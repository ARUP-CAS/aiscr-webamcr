#!/usr/bin/env python3
"""
Kontrola a úprava shody pinů (tag/digest) u stejného container image v Dockerfileech a docker-compose.

- V jednom souboru: stejný image repozitář nesmí mít různé tagy/digesty (FROM nebo image:).
- docker-compose.yml je zdroj pravdy pro literály; spotřebitelské compose soubory se při --fix srovnají na prod.

Výstup pro CI: řádky na stderr s prefixem ``[image-ref-parity]``.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, DefaultDict, Dict, Iterable, List, Optional, Set, Tuple

from packaging.version import InvalidVersion, Version
from ruamel.yaml import YAML

LOG_PREFIX = "[image-ref-parity]"

# Relativní cesty od kořene repozitáře (pre-commit spouští z rootu).
DOCKERFILE_PATHS = [
    "Dockerfile",
    "Dockerfile-DEV",
    "Dockerfile-DB",
    "fedora/Dockerfile",
    "redis/Dockerfile",
    "proxy/Dockerfile",
]

COMPOSE_PRODUCTION = ["docker-compose.yml"]
COMPOSE_CONSUMERS = [
    "docker-compose-dev-local-db-all-containers.yml",
    "docker-compose-dev-local-db.yml",
    "docker-compose-test.yml",
    "git_docker-compose.yml",
]

FROM_LINE = re.compile(r"^FROM\s+(?P<rest>.+?)\s*(?:#.*)?$", re.IGNORECASE)
AS_SUFFIX = re.compile(r"\s+AS\s+(\S+)\s*$", re.IGNORECASE)
# FROM s nahraditelným image tokenem (image bez komentáře na konci řádku zvlášť).
FROM_IMG_RE = re.compile(
    r"^(FROM\s+)((?:--platform=\S+\s+)+)?(\S+)((\s+AS\s+\S+)?)(\s*(?:#.*)?)$",
    re.IGNORECASE,
)


def log_msg(message: str, *, verbose_only: bool = False, verbose: bool = False) -> None:
    """
    Vypíše jeden řádek na stderr s prefixem pro grep v CI.

    :param message: Text bez prefixu.
    :param verbose_only: Pokud True, vypíše jen při verbose režimu.
    :param verbose: Aktuální verbose příznak.
    """
    if verbose_only and not verbose:
        return
    print(f"{LOG_PREFIX} {message}", file=sys.stderr)


def is_literal_image_ref(value: str) -> bool:
    """
    Určí, zda hodnota ``image:`` v compose lze použít pro porovnání pinů (bez rozšíření proměnných).

    :param value: Řetězec z pole ``image`` u služby.
    :return: False pro prázdný řetězec, obsah ``${`` / ``$$``; jinak True.
    """
    s = value.strip()
    if not s:
        return False
    if "${" in s or "$$" in s:
        return False
    return True


def _strip_platform_flags(rest: str) -> str:
    """
    Odstraní z řetězce za ``FROM`` všechny úvodní příznaky ``--platform=...``.

    :param rest: Část řádku za ``FROM`` před případným ``AS``.
    :return: Zbytek začínající odkazem na image, nebo prázdný řetězec při neplatném tvaru.
    """
    current = rest.strip()
    while current.startswith("--"):
        space_idx = current.find(" ")
        if space_idx == -1:
            return ""
        current = current[space_idx + 1 :].strip()
    return current


def parse_from_instruction(line: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    Parsuje řádek Dockerfile začínající ``FROM`` na odkaz na image a volitelné jméno stage.

    :param line: Jeden řádek souboru (může obsahovat koncový komentář ``#``).
    :return: ``(image_ref, as_name)`` nebo None, pokud řádek není platný ``FROM``.
    """
    stripped = line.strip()
    m = FROM_LINE.match(stripped)
    if not m:
        return None
    rest = m.group("rest").strip()
    as_name: Optional[str] = None
    as_m = AS_SUFFIX.search(rest)
    if as_m:
        as_name = as_m.group(1)
        rest = rest[: as_m.start()].strip()
    rest = _strip_platform_flags(rest)
    if not rest:
        return None
    return rest, as_name


def repository_and_pin(image_ref: str) -> Tuple[str, str]:
    """
    Rozdělí odkaz na container image na klíč repozitáře a normalizovaný pin (tag a/nebo digest).

    :param image_ref: Řetězec image bez části ``AS`` (např. ``ghcr.io/foo:1.0``).
    :return: ``(repo_key, pin_key)`` — obě části malými písmeny pro porovnání.
    """
    ref = image_ref.strip()
    lower = ref.lower()
    digest_idx = lower.find("@sha256:")
    digest_suffix = ""
    if digest_idx != -1:
        digest_suffix = ref[digest_idx:]
        ref = ref[:digest_idx]

    last_slash = ref.rfind("/")
    tail = ref[last_slash + 1 :]
    if ":" in tail:
        repo, _, tag = ref.rpartition(":")
    else:
        repo, tag = ref, ""

    pin = (tag + digest_suffix).lower()
    return repo.lower(), pin


def choose_canonical_pin(pins: Set[str]) -> str:
    """
    Vybere jeden kanonický pin z množiny normalizovaných pinů (malá písmena).

    :param pins: Množina pin_key.
    :return: Vítězný pin_key.
    """
    if len(pins) == 1:
        return next(iter(pins))
    pins_list = list(pins)

    def sort_key(pin: str) -> Tuple[int, Any]:
        tag_part = pin.split("@sha256:", 1)[0]
        try:
            return (0, Version(tag_part))
        except InvalidVersion:
            return (1, pin)

    if all(sort_key(p)[0] == 0 for p in pins_list):
        return max(pins_list, key=lambda p: Version(p.split("@sha256:", 1)[0]))
    return max(pins_list)


def pick_display_ref_for_pin(refs_by_pin: Dict[str, List[str]], pin_key: str) -> str:
    """
    Vrátí reprezentaci image pro zápis (zachovává casing z jednoho výskytu).

    :param refs_by_pin: Mapa pin_key -> původní řetězce image.
    :param pin_key: Normalizovaný pin.
    :return: Původní řetězec image.
    """
    candidates = refs_by_pin.get(pin_key, [])
    if not candidates:
        return pin_key
    return candidates[0]


def build_yaml() -> YAML:
    """
    Vytvoří nakonfigurovanou instanci ``ruamel.yaml.YAML`` pro čtení/zápis compose se zachováním uvozovek.

    :return: YAML loader/dumper vhodný pro úpravy compose souborů.
    """
    y = YAML()
    y.preserve_quotes = True
    y.indent(mapping=2, sequence=4, offset=2)
    return y


@dataclass
class DockerfileScan:
    """
    Výsledek průchodu Dockerfile: agregace pinů podle repozitáře a metadata řádků pro přepis ``FROM``.
    """

    pins_by_repo: DefaultDict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    refs_by_repo_pin: DefaultDict[str, DefaultDict[str, List[str]]] = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(list))
    )
    line_info: List[Dict[str, Any]] = field(default_factory=list)


def scan_dockerfile(text: str) -> DockerfileScan:
    """
    Projde text Dockerfile a sejme externí base image (mimo ``scratch`` a odkazy na již definované stage).

    :param text: Celý obsah Dockerfile.
    :return: Struktura s množinami pinů, mapou původních řetězců a ``line_info`` pro ``FROM_IMG_RE``.
    """
    scan = DockerfileScan()
    stages: Set[str] = set()
    for lineno, line in enumerate(text.splitlines(), start=1):
        parsed = parse_from_instruction(line)
        if parsed is None:
            continue
        image_ref, as_name = parsed
        if image_ref.lower() == "scratch":
            if as_name:
                stages.add(as_name)
            continue
        if image_ref in stages:
            if as_name:
                stages.add(as_name)
            continue
        repo_key, pin_key = repository_and_pin(image_ref)
        scan.pins_by_repo[repo_key].add(pin_key)
        scan.refs_by_repo_pin[repo_key][pin_key].append(image_ref)
        m = FROM_IMG_RE.match(line.rstrip("\n"))
        if m:
            scan.line_info.append(
                {
                    "lineno": lineno,
                    "line": line,
                    "repo_key": repo_key,
                    "pin_key": pin_key,
                    "prefix": m.group(1) + (m.group(2) or ""),
                    "as_part": m.group(4) or "",
                    "suffix": m.group(6) or "",
                }
            )
        if as_name:
            stages.add(as_name)
    return scan


def fix_dockerfile_text(text: str, fix: bool, path: Path, _verbose: bool) -> Tuple[str, List[str], bool]:
    """
    Zkontroluje nebo opraví konflikty pinů u stejného ``repo_key`` v jednom Dockerfile.

    :param text: Původní obsah souboru.
    :param fix: Pokud True, přepíše ``FROM`` řádky na kanonický pin; pokud False, jen hlásí chyby.
    :param path: Cesta pro hlášky v chybách.
    :param _verbose: Rezervováno (aktuálně nepoužito).
    :return: Trojice ``(nový_text, seznam_chyb, byl_upraven)``.
    """
    errors: List[str] = []
    scan = scan_dockerfile(text)
    for repo_key, pins in scan.pins_by_repo.items():
        if len(pins) <= 1:
            continue
        if not fix:
            detail_parts = []
            for pin in sorted(pins):
                detail_parts.append(f"  - {repr(pin) if pin else '(bez explicitního tagu)'}")
            errors.append(
                f"{path}: stejný image {repo_key!r} má v jednom Dockerfile různé tagy/digesty:\n"
                + "\n".join(detail_parts)
            )
            log_msg(f"ERROR: {path}: konflikt pinů pro {repo_key!r}: {', '.join(sorted(pins))}")
            continue
        win = choose_canonical_pin(set(pins))
        new_ref = pick_display_ref_for_pin({k: list(v) for k, v in scan.refs_by_repo_pin[repo_key].items()}, win)
        log_msg(f"FIX: {path}: sjednocuji {repo_key!r} na pin {win!r} (→ {new_ref!r})")

    if errors and not fix:
        return text, errors, False

    if not fix:
        return text, [], False

    lines = text.splitlines(keepends=True)
    modified = False
    for info in scan.line_info:
        repo_key = info["repo_key"]
        pins = scan.pins_by_repo[repo_key]
        if len(pins) <= 1:
            continue
        win = choose_canonical_pin(set(pins))
        if info["pin_key"] == win:
            continue
        new_ref = pick_display_ref_for_pin({k: list(v) for k, v in scan.refs_by_repo_pin[repo_key].items()}, win)
        lineno = info["lineno"]
        idx = lineno - 1
        old = lines[idx]
        m = FROM_IMG_RE.match(old.rstrip("\r\n"))
        if not m:
            continue
        nl = "\n" if old.endswith("\n") else ""
        if old.endswith("\r\n"):
            nl = "\r\n"
        new_line = m.group(1) + (m.group(2) or "") + new_ref + (m.group(4) or "") + (m.group(6) or "") + nl
        if new_line != old:
            lines[idx] = new_line
            modified = True
    return "".join(lines), [], modified


def iter_compose_service_images(data: Any) -> Iterable[Tuple[str, str, Any]]:
    """
    Projde ``services`` v načteném compose a vrátí služby s řetězcovým ``image``.

    :param data: Kořenový dict compose (např. z ``yaml.load``), očekává se klíč ``services``.
    :yield: ``(název_služby, hodnota_image, spec_dict)`` — ``spec_dict`` umožní při ``--fix`` změnit ``image`` na místě.
    :return: Iterátor trojic (viz ``:yield:``); při neplatném ``data`` nebo ``services`` nic nevygeneruje.
    """
    if not isinstance(data, dict):
        return
    services = data.get("services")
    if not isinstance(services, dict):
        return
    for svc_name, spec in services.items():
        if not isinstance(spec, dict):
            continue
        img = spec.get("image")
        if isinstance(img, str):
            yield svc_name, img, spec


def scan_compose_intra(
    data: Any, _path: Path
) -> Tuple[DefaultDict[str, Set[str]], DefaultDict[str, DefaultDict[str, List[str]]], int]:
    """
    Shromáždí literální ``image`` z jednoho compose souboru pro intra-file kontrolu shody pinů.

    :param data: Parsovaný obsah compose.
    :param _path: Cesta k souboru (pro rozhraní; aktuálně se nepoužívá).
    :return: ``(pins_by_repo, refs_by_repo_pin, počet_přeskočených_neliterálních_image)``.
    """
    pins_by_repo: DefaultDict[str, Set[str]] = defaultdict(set)
    refs_by_repo_pin: DefaultDict[str, DefaultDict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
    skipped_nonliteral = 0
    for _svc_name, img, _spec in iter_compose_service_images(data):
        if not is_literal_image_ref(img):
            skipped_nonliteral += 1
            continue
        repo_key, pin_key = repository_and_pin(img)
        pins_by_repo[repo_key].add(pin_key)
        refs_by_repo_pin[repo_key][pin_key].append(img)
    return pins_by_repo, refs_by_repo_pin, skipped_nonliteral


def apply_compose_intra_fix(
    data: Any,
    path: Path,
    pins_by_repo: DefaultDict[str, Set[str]],
    refs_by_repo_pin: DefaultDict[str, DefaultDict[str, List[str]]],
    fix: bool,
    _verbose: bool,
) -> Tuple[List[str], bool]:
    """
    U jednoho compose sjednotí literální ``image`` se stejným ``repo_key`` na jeden kanonický pin.

    :param data: Parsovaný strom compose (mění se in-place při ``fix=True``).
    :param path: Cesta k souboru pro chybové hlášky.
    :param pins_by_repo: Agregace pinů ze :func:`scan_compose_intra`.
    :param refs_by_repo_pin: Mapa původních řetězců image podle pinu.
    :param fix: Zapnout zápis oprav do ``data``.
    :param _verbose: Rezervováno (nepoužito).
    :return: ``(seznam_chyb, byl_proveden_zápis_do_dat)``.
    """
    errors: List[str] = []
    modified = False
    for repo_key, pins in pins_by_repo.items():
        if len(pins) <= 1:
            continue
        if not fix:
            errors.append(f"{path}: stejný image {repo_key!r} má v compose různé tagy/digesty: {sorted(pins)}")
            log_msg(f"ERROR: {path}: konflikt pinů pro {repo_key!r}: {', '.join(sorted(pins))}")
            continue
        win = choose_canonical_pin(set(pins))
        new_ref = pick_display_ref_for_pin({k: list(v) for k, v in refs_by_repo_pin[repo_key].items()}, win)
        log_msg(f"FIX: {path}: sjednocuji {repo_key!r} na {new_ref!r}")
        for _svc_name, img, spec in iter_compose_service_images(data):
            if not is_literal_image_ref(img):
                continue
            rk, pk = repository_and_pin(img)
            if rk != repo_key:
                continue
            if pk != win:
                spec["image"] = new_ref
                modified = True
    return errors, modified


def extract_prod_literal_map(data: Any) -> Dict[str, str]:
    """
    Z produkčního compose vytvoří mapu ``repo_key`` → literální řetězec ``image`` (první výskyt).

    :param data: Parsovaný ``docker-compose.yml`` (nebo ekvivalent).
    :return: Slovník pro cross-file srovnání se spotřebitelskými compose.
    """
    out: Dict[str, str] = {}
    for _svc, img, _spec in iter_compose_service_images(data):
        if not is_literal_image_ref(img):
            continue
        repo_key, _pin = repository_and_pin(img)
        if repo_key not in out:
            out[repo_key] = img.strip()
    return out


def apply_compose_cross_fix(
    consumer_data: Any,
    consumer_path: Path,
    prod_map: Dict[str, str],
    fix: bool,
    verbose: bool,
) -> Tuple[List[str], bool]:
    """
    Porovná literální image ve spotřebitelském compose s mapou z produkce a případně je srovná.

    :param consumer_data: Parsovaný compose spotřebitele (mění se in-place při ``fix=True``).
    :param consumer_path: Cesta k souboru spotřebitele (logy a chyby).
    :param prod_map: Výstup :func:`extract_prod_literal_map` z ``docker-compose.yml``.
    :param fix: Pokud True, přepíše ``image`` na hodnotu z prod při nesouladu pinu.
    :param verbose: Zapíná podrobné SKIP logy u neliterálních image (přes ``log_msg``).
    :return: ``(seznam_chyb při fix=False, byl_proveden_zápis)``.
    """
    errors: List[str] = []
    modified = False
    seen_deferred: Set[Tuple[str, str]] = set()

    for svc_name, img, spec in iter_compose_service_images(consumer_data):
        if not is_literal_image_ref(img):
            if verbose:
                log_msg(
                    f"SKIP: {consumer_path} služba {svc_name!r}: neliterální image (přeskočeno)",
                    verbose_only=True,
                    verbose=verbose,
                )
            continue
        repo_key, pin_key = repository_and_pin(img)
        if repo_key in prod_map:
            prod_ref = prod_map[repo_key]
            _, prod_pin = repository_and_pin(prod_ref)
            if pin_key != prod_pin:
                msg = f"{consumer_path}: služba {svc_name!r}: {img!r} ≠ prod {prod_ref!r} " f"(repo {repo_key!r})"
                if not fix:
                    errors.append(msg)
                    log_msg(f"ERROR: {msg}")
                else:
                    log_msg(f"FIX: {consumer_path} {svc_name!r}: {img!r} → {prod_ref!r} (prod)")
                    spec["image"] = prod_ref
                    modified = True
        else:
            key = (repo_key, str(consumer_path))
            if key not in seen_deferred:
                seen_deferred.add(key)
                log_msg(
                    f"NOTE: {consumer_path}: repo {repo_key!r} má literál {img!r}, "
                    f"ale {COMPOSE_PRODUCTION[0]} neobsahuje srovnatelný literál pro stejný repozitář — "
                    f"cross-file srovnání přeskočeno (zkontroluj ručně / proměnné v prod).",
                    verbose_only=True,
                    verbose=verbose,
                )
    return errors, modified


def process_dockerfiles(root: Path, fix: bool, verbose: bool) -> Tuple[List[str], List[Path]]:
    """
    Zpracuje všechny Dockerfile z konstanty ``DOCKERFILE_PATHS`` pod kořenem ``root``.

    :param root: Kořen repozitáře (aktuální pracovní adresář při běhu z pre-commit).
    :param fix: Předáno do :func:`fix_dockerfile_text`; při True zapíše změny na disk.
    :param verbose: Předáno dál pro případné budoucí logování (část volání zachována kvůli API).
    :return: ``(souhrnné_chyby, seznam_cest_upravených_souborů)``.
    """
    errors: List[str] = []
    modified_paths: List[Path] = []
    for rel in DOCKERFILE_PATHS:
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        new_text, errs, mod = fix_dockerfile_text(text, fix, path, verbose)
        errors.extend(errs)
        if mod and fix:
            path.write_text(new_text, encoding="utf-8")
            modified_paths.append(path)
            log_msg(f"Upraven soubor {path}")
    return errors, modified_paths


def process_compose_files(root: Path, fix: bool, verbose: bool) -> Tuple[List[str], List[Path]]:
    """
    Načte prod a spotřebitelské compose, provede intra-file a cross-file kontrolu nebo opravu.

    Zapisuje pouze soubory, u kterých došlo ke změně dat (ne přeformátovává prod zbytečně).

    :param root: Kořen repozitáře.
    :param fix: Zapne zápis YAML a cross-file úpravy spotřebitelů.
    :param verbose: Statistiky přeskočených neliterálních referencí a SKIP u cross-file.
    :return: ``(souhrnné_chyby, seznam_cest_upravených_souborů)``.
    """
    yaml = build_yaml()
    errors: List[str] = []
    modified_paths: List[Path] = []
    loaded: Dict[Path, Any] = {}
    originals: Dict[Path, str] = {}

    all_compose = [root / p for p in COMPOSE_PRODUCTION + COMPOSE_CONSUMERS if (root / p).is_file()]

    for path in all_compose:
        raw = path.read_text(encoding="utf-8")
        originals[path] = raw
        loaded[path] = yaml.load(raw) or {}

    compose_dirty: Set[Path] = set()

    for path in all_compose:
        data = loaded[path]
        pins_by_repo, refs_by_repo, skipped = scan_compose_intra(data, path)
        if verbose and skipped:
            log_msg(
                f"INFO: {path}: přeskočeno {skipped} neliterálních image referencí",
                verbose_only=True,
                verbose=verbose,
            )
        errs, intra_mod = apply_compose_intra_fix(data, path, pins_by_repo, refs_by_repo, fix, verbose)
        errors.extend(errs)
        if intra_mod:
            compose_dirty.add(path)

    prod_path = root / COMPOSE_PRODUCTION[0]
    prod_map: Dict[str, str] = {}
    if prod_path in loaded:
        prod_map = extract_prod_literal_map(loaded[prod_path])

    for rel in COMPOSE_CONSUMERS:
        path = root / rel
        if path not in loaded:
            continue
        errs, cross_mod = apply_compose_cross_fix(loaded[path], path, prod_map, fix, verbose)
        errors.extend(errs)
        if cross_mod:
            compose_dirty.add(path)

    if fix:
        for path in sorted(compose_dirty, key=str):
            out = io.StringIO()
            yaml.dump(loaded[path], out)
            path.write_text(out.getvalue(), encoding="utf-8")
            modified_paths.append(path)
            log_msg(f"Upraven soubor {path}")

    return errors, modified_paths


def main(argv: Optional[List[str]] = None) -> int:
    """
    Vstupní bod CLI: spustí kontrolu Dockerfile a compose, volitelně s opravami.

    :param argv: Argumenty příkazové řádky (bez ``sys.argv[0]``); None znamená ``sys.argv[1:]``.
    :return: 0 při úspěchu; 1 při nalezených chybách (bez ``--fix``) nebo po úpravě souborů (s ``--fix``, aby pre-commit znovu zstageoval).
    """
    parser = argparse.ArgumentParser(description="Kontrola shody container image pinů (Dockerfile + compose).")
    parser.add_argument("files", nargs="*", help="Ignorováno — vždy se kontrolují pevné cesty v repozitáři.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Opravit soubory na místě (intra + cross na spotřebitele).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Podrobnější výstup.",
    )
    args = parser.parse_args(argv)

    verbose = bool(args.verbose)
    root = Path.cwd()

    all_errors: List[str] = []
    modified: List[Path] = []

    de, md = process_dockerfiles(root, args.fix, verbose)
    all_errors.extend(de)
    modified.extend(md)

    ce, mc = process_compose_files(root, args.fix, verbose)
    all_errors.extend(ce)
    modified.extend(mc)

    for err in all_errors:
        if not err.startswith(LOG_PREFIX):
            print(err, file=sys.stderr)

    if all_errors:
        return 1

    if args.fix and modified:
        log_msg(f"HOTOVÁ ÚPRAVA: {len(modified)} soubor(ů); znovu přidej do commitu.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
