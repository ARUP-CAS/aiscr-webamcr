"""Ověří požadované služby a skutečné zdraví kontejnerů cílového stacku.

Nasazovací wrappery spouštějí skript systémovým ``python3`` nasazovacího
serveru, který má Python 3.6. Skript proto smí používat jen moduly
standardní knihovny a parametry ``subprocess.run`` dostupné v Pythonu 3.6;
tuto spodní hranici hlídá ``scripts/test_pre_commit_stack_ready.py``.
"""

import argparse
import json
import re
import subprocess
import sys
import time


def docker(*args, deadline=None):
    """Spustí pouze čtecí Docker CLI a odmítne neúplné inspekce.

    :param args: Argumenty čtecího příkazu.
    :param deadline: Hodnota ``time.monotonic()``, do které musí inspekce
        skončit; ``None`` omezí příkaz jen vlastním limitem 30 sekund.
    :return: Úplný standardní výstup.
    :raises TimeoutError: Pokud termín inspekce již uplynul.
    """
    remaining = 30 if deadline is None else min(30, deadline - time.monotonic())
    if remaining <= 0:
        raise TimeoutError("Vypršel limit inspekce stacku")
    result = subprocess.run(
        ["docker", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=True,
        timeout=remaining,
    )
    return result.stdout


def expected_services(compose_files, deadline=None):
    """Vybere názvy služeb z kanonického sloučeného výstupu Docker CLI.

    :param compose_files: Compose soubory skutečně použité k nasazení.
    :param deadline: Termín inspekce předaný příkazu Docker CLI.
    :return: Neprázdná množina názvů služeb.
    :raises ValueError: Při chybějící nebo nerozpoznatelné sekci služeb.
    """
    command = ["stack", "config", "--skip-interpolation"]
    for path in compose_files:
        command.extend(["--compose-file", path])
    config = docker(*command, deadline=deadline)
    services = set()
    inside = False
    indent = None
    for line in config.splitlines():
        if line == "services:":
            inside = True
        elif inside and line and not line.startswith(" "):
            break
        elif inside:
            match = re.fullmatch(r"( +)[\"']?([A-Za-z0-9_.-]+)[\"']?:", line)
            if match and (indent is None or len(match[1]) == indent):
                indent = len(match[1])
                services.add(match[2])
    if not services:
        raise ValueError("Chybí rozpoznatelné požadované služby")
    return services


def inspect_json(kind, names, deadline=None):
    """Ověří úplnost strukturované inspekce konkrétních objektů.

    :param kind: Typ objektu Docker.
    :param names: Jednoznačně vybrané názvy nebo ID.
    :param deadline: Termín inspekce předaný příkazu Docker CLI.
    :return: Seznam inspektovaných objektů.
    :raises ValueError: Pokud inspekce nevrátí právě jeden objekt pro každý název.
    """
    values = json.loads(docker("inspect", "--type", kind, *names, deadline=deadline))
    if not isinstance(values, list) or len(values) != len(names):
        raise ValueError("Neúplná inspekce Docker")
    return values


def readiness(stack, services, deadline=None):
    """Zkontroluje aktivní úlohy a zdraví pouze požadovaných služeb.

    :param stack: Přesný název cílového stacku.
    :param services: Požadované služby z Compose konfigurace.
    :param deadline: Termín inspekce předaný každému příkazu Docker CLI.
    :return: Dvojice připravenosti a diagnostiky.
    """
    rows = docker(
        "service",
        "ls",
        "--filter",
        f"label=com.docker.stack.namespace={stack}",
        "--format",
        "{{json .}}",
        deadline=deadline,
    )
    replicas = {}
    for line in rows.splitlines():
        row = json.loads(line)
        if row["Name"] in replicas:
            raise ValueError("Duplicitní služba v inspekci")
        replicas[row["Name"]] = row["Replicas"]
    required = {f"{stack}_{name}" for name in services}
    if not required <= replicas.keys():
        return False, "Chybí požadované služby: " + ", ".join(sorted(required - replicas.keys()))
    specs = inspect_json("service", sorted(required), deadline)
    if {item["Spec"]["Name"] for item in specs} != required:
        raise ValueError("Inspekce neodpovídá požadovaným službám")
    for service in specs:
        name = service["Spec"]["Name"]
        mode = service["Spec"]["Mode"]
        update = service.get("UpdateStatus", {}).get("State")
        if update in ("paused", "updating") or (update and update.startswith("rollback")):
            return False, f"{name}: rollout {update}"
        counts = re.fullmatch(r"([0-9]+)/([0-9]+)(?: \(([0-9]+)/([0-9]+) completed\))?", replicas[name])
        if not counts:
            raise ValueError(f"Neplatný počet replik: {name}")
        running, desired = int(counts[1]), int(counts[2])
        if any(key in mode for key in ("ReplicatedJob", "GlobalJob")):
            expected = mode.get("ReplicatedJob", {}).get("TotalCompletions", int(counts[4] or 0))
            if counts[3] is not None and int(counts[3]) == int(counts[4]) == expected:
                continue
            return False, f"{name}: jednorázová úloha není dokončena"
        if "Replicated" in mode and mode["Replicated"].get("Replicas", 1) == 0:
            if desired != 0 or running != 0:
                return False, f"{name}: neodpovídá záměrnému škálování na nulu"
            continue
        if desired <= 0 or running != desired:
            return False, f"{name}: repliky {running}/{desired}"
        if "Replicated" in mode and desired != mode["Replicated"].get("Replicas", 1):
            return False, f"{name}: neodpovídá požadovanému počtu replik"
        ids = docker(
            "service", "ps", "--no-trunc", "-q", "--filter", "desired-state=running", name, deadline=deadline
        ).split()
        if len(ids) != desired or len(set(ids)) != desired:
            return False, f"{name}: chybí aktivní úlohy"
        tasks = inspect_json("task", ids, deadline)
        for task in tasks:
            if task["ServiceID"] != service["ID"]:
                raise ValueError("Úloha patří jiné službě")
            if task["DesiredState"] != "running" or task["Status"]["State"] != "running":
                return False, f"{name}: úloha není running"
            container = task["Status"].get("ContainerStatus", {}).get("ContainerID")
            if not container:
                return False, f"{name}: chybí kontejner"
            state = inspect_json("container", [container], deadline)[0]["State"]
            if state["Status"] != "running" or state.get("Health", {}).get("Status", "healthy") != "healthy":
                return False, f"{name}: kontejner není zdravý"
    return True, "Požadované služby stacku jsou připraveny"


def wait_ready(stack, compose_files, timeout=600, interval=20):
    """Počká nejvýše do stanoveného termínu; chybu inspekce neinterpretuje jako zdraví.

    :param stack: Název stacku.
    :param compose_files: Použité Compose soubory.
    :param timeout: Maximální délka čekání v sekundách.
    :param interval: Interval dalších kontrol.
    :return: Nula při připravenosti, jinak jedna.
    """
    if timeout < 0 or interval <= 0:
        raise ValueError("Neplatný limit čekání")
    deadline = time.monotonic() + timeout
    services = expected_services(compose_files, deadline)
    while True:
        ready, message = readiness(stack, services, deadline)
        print(message, flush=True)
        if ready:
            return 0
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return 1
        time.sleep(min(interval, remaining))


def main(argv=None):
    """Vrátí stav použitelnosti stacku pro volající nasazovací skript.

    :param argv: Volitelné argumenty CLI.
    :return: Nula při připravenosti, jinak jedna.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("stack")
    parser.add_argument("--compose-file", action="append", required=True)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--interval", type=int, default=20)
    args = parser.parse_args(argv)
    try:
        return wait_ready(args.stack, args.compose_file, args.timeout, args.interval)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as exc:
        print(f"Readiness inspection failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
