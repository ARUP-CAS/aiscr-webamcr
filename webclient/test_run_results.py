"""Váže výsledky testů na jeden pokus bez spouštění stažených dat."""

import hashlib
import json
import os
import re
import shutil
import stat
import uuid
from pathlib import Path

FILES = {"test_summary.env", "results.xlsx", "test_output.log"}
FIELDS = {
    "version",
    "attempt_id",
    "mode",
    "number",
    "state",
    "exit_code",
    "spreadsheet_required",
    "files",
    "message",
    "counts",
}
COUNT_FIELDS = {"total", "passed", "failed", "skipped", "expected_failures"}
OUTCOME_LIMIT = 16384


def validate_identity(identity):
    """Ověří identifikátor bez cest a shellové syntaxe.

    :param identity: Identifikátor pokusu.
    :return: Ověřený identifikátor.
    :raises ValueError: Při nepovoleném tvaru.
    """
    if not isinstance(identity, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}", identity, re.ASCII):
        raise ValueError("Neplatný identifikátor pokusu")
    return identity


def selection(mode, number):
    """Normalizuje očekávaný výběr bez vyhodnocování obsahu.

    :param mode: Název režimu.
    :param number: Číslo testu nebo prázdný řetězec.
    :return: Normalizovaná dvojice režimu a čísla.
    :raises ValueError: Při neplatném výběru.
    """
    if mode not in ("vsechny", "neuspesne", "konkretni") or not isinstance(number, str):
        raise ValueError("Neplatný režim")
    if number and not re.fullmatch(r"[0-9]+", number):
        raise ValueError("Neplatné číslo testu")
    if mode == "konkretni" and not number:
        raise ValueError("Chybí číslo testu")
    return mode, str(int(number)) if mode == "konkretni" else ""


def attempt_identity(identity=None):
    """Ověří zadanou identitu nebo vytvoří novou pro samostatný běh.

    :param identity: Volitelná identita pokusu z CI.
    :return: Ověřená identita, případně ``local-<uuid>`` pro ruční spuštění.
    """
    return validate_identity(identity or f"local-{uuid.uuid4().hex}")


def prepare_current(root):
    """Přesune poslední běh do ``previous/`` a připraví prázdný ``current/``.

    Starší obsah ``previous/`` se smaže. Kořenová tabulka výběru a ostatní
    soubory v kořeni zůstávají beze změny.

    :param root: Kořen výsledků.
    :return: Absolutní cesta prázdného adresáře ``current/``.
    :raises ValueError: Pokud je ``current/`` nebo ``previous/`` odkaz či junction.
    """
    current, previous = Path(root) / "current", Path(root) / "previous"
    for path in (current, previous):
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError("Adresář výsledků nesmí být odkaz")
    if previous.exists():
        shutil.rmtree(previous)
    if current.exists():
        current.rename(previous)
    current.mkdir(parents=True)
    return current.resolve()


def digest(path):
    """Spočítá otisk běžného souboru bez následování odkazu.

    :param path: Soubor patřící k pokusu.
    :return: Hexadecimální SHA-256.
    :raises ValueError: Při odkazu nebo chybějícím souboru.
    """
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Chybí běžný soubor {path.name}")
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            value.update(chunk)
    return value.hexdigest()


def atomic_write(path, content):
    """Zveřejní úplný soubor jediným přejmenováním.

    :param path: Cílová cesta.
    :param content: Bajty hotového obsahu.
    """
    temporary = path.with_name(f".{path.name}-{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_summary(directory, passed, failed):
    """Zapíše dva číselné záznamy aktuálního pokusu.

    :param directory: Adresář pokusu.
    :param passed: Počet úspěšných testů.
    :param failed: Počet neúspěšných testů.
    """
    atomic_write(directory / "test_summary.env", f"PASSED={passed}\nFAILED={failed}\n".encode("ascii"))


def read_summary(path):
    """Přečte celý číselný souhrn včetně CRLF a posledního řádku bez LF.

    :param path: Soubor se dvěma záznamy.
    :return: Počty testů.
    :raises ValueError: Při neplatném nebo neúplném obsahu.
    """
    with path.open("rb") as stream:
        raw = stream.read(4097)
    if len(raw) > 4096:
        raise ValueError("Příliš dlouhý souhrn")
    lines = raw.split(b"\n")
    if lines[-1] == b"":
        lines.pop()
    counts = {}
    for line in lines:
        match = re.fullmatch(rb"(PASSED|FAILED)=([0-9]+)", line.removesuffix(b"\r"))
        if not match or match[1] in counts:
            raise ValueError("Neplatný číselný souhrn")
        counts[match[1]] = int(match[2])
    if set(counts) != {b"PASSED", b"FAILED"}:
        raise ValueError("Neúplný číselný souhrn")
    return counts[b"PASSED"], counts[b"FAILED"]


def validate_record(record, identity, mode, number):
    """Ověří schéma a identitu před použitím názvů souborů.

    :param record: Deserializovaný záznam.
    :param identity: Očekávaný pokus.
    :param mode: Očekávaný režim.
    :param number: Očekávané číslo.
    :return: Ověřený záznam.
    :raises ValueError: Při nesouladu nebo nepovoleném obsahu.
    """
    validate_identity(identity)
    mode, number = selection(mode, number)
    if not isinstance(record, dict):
        raise ValueError("Neplatné schéma výsledku")
    version = record.get("version")
    if type(version) is not int or version != 2:
        raise ValueError("Neznámá verze výsledku")
    if set(record) != FIELDS:
        raise ValueError("Neplatné schéma výsledku")
    if (record["attempt_id"], record["mode"], record["number"]) != (identity, mode, number):
        raise ValueError("Výsledek patří jinému pokusu nebo výběru")
    if record["state"] not in ("completed", "no-tests", "error"):
        raise ValueError("Neplatný stav výsledku")
    if type(record["exit_code"]) is not int or not 0 <= record["exit_code"] <= 255:
        raise ValueError("Neplatný návratový kód")
    if type(record["spreadsheet_required"]) is not bool or not isinstance(record["message"], str):
        raise ValueError("Neplatná metadata výsledku")
    files = record["files"]
    if not isinstance(files, dict) or not set(files) <= FILES:
        raise ValueError("Nepovolená cesta artefaktu")
    if any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value) for value in files.values()):
        raise ValueError("Neplatný otisk artefaktu")
    if record["state"] == "error":
        if record["exit_code"] == 0 or record["spreadsheet_required"] or set(files) - {"test_output.log"}:
            raise ValueError("Chyba nesmí vypadat jako dokončené testy")
    else:
        if "test_summary.env" not in files:
            raise ValueError("Chybí aktuální souhrn")
        if record["spreadsheet_required"] and "results.xlsx" not in files:
            raise ValueError("Chybí aktuální tabulka")
        if record["state"] == "no-tests" and (
            mode != "neuspesne" or record["exit_code"] or record["spreadsheet_required"] or "results.xlsx" in files
        ):
            raise ValueError("Neplatný výsledek bez testů")
    counts = record["counts"]
    if record["state"] == "error":
        if counts is not None:
            raise ValueError("Chyba nesmí vymýšlet počty testů")
    else:
        if not isinstance(counts, dict) or set(counts) != COUNT_FIELDS:
            raise ValueError("Chybí úplné počty testů")
        if any(type(value) is not int or value < 0 for value in counts.values()):
            raise ValueError("Neplatné počty testů")
        if counts["total"] != sum(counts[key] for key in COUNT_FIELDS - {"total"}):
            raise ValueError("Rozporné kategorie testů")
        if record["state"] == "no-tests":
            if any(counts.values()):
                raise ValueError("No-op nesmí vykazovat testy")
        elif (
            counts["total"] - counts["skipped"] <= 0
            or record["exit_code"] not in (0, 1)
            or (record["exit_code"] == 0) != (counts["failed"] == 0)
        ):
            raise ValueError("Rozpor provedených testů a procesu")
    return record


def read_outcome(directory):
    """Načte jediný omezený objekt JSON bez duplicitních klíčů.

    :param directory: Adresář pokusu.
    :return: Načtený objekt k ověření proti očekávanému pokusu.
    """

    def unique(pairs):
        """Odmítne duplicitní klíč v každém objektu JSON.

        :param pairs: Dvojice ze čteného objektu.
        :return: Slovník s jedinečnými klíči.
        """
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicitní klíč výsledku")
            result[key] = value
        return result

    path = directory / "outcome.json"
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > OUTCOME_LIMIT:
        raise ValueError("Neplatný soubor výsledku")
    with path.open("rb") as stream:
        raw = stream.read(OUTCOME_LIMIT + 1)
    if len(raw) > OUTCOME_LIMIT:
        raise ValueError("Neplatný soubor výsledku")
    try:
        record = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    except RecursionError as exc:
        raise ValueError("Příliš hluboký objekt výsledku") from exc
    if not isinstance(record, dict):
        raise ValueError("Neplatné schéma výsledku")
    return record


def load_record(directory, identity, mode, number):
    """Načte a ověří výsledek proti očekávané identitě a výběru.

    :param directory: Adresář staženého pokusu.
    :param identity: Očekávaný pokus.
    :param mode: Očekávaný režim.
    :param number: Očekávané číslo.
    :return: Ověřená metadata.
    """
    return validate_record(read_outcome(directory), identity, mode, number)


def validate_bundle(directory, record):
    """Ověří otisky a soulad čísel s výsledkem procesu před publikací.

    :param directory: Adresář aktuálního pokusu.
    :param record: Již ověřená metadata.
    :return: Počty testů, pro chybu None.
    """
    validate_record(record, record["attempt_id"], record["mode"], record["number"])
    for filename, expected in record["files"].items():
        if digest(directory / filename) != expected:
            raise ValueError("Artefakt neodpovídá aktuálnímu výsledku")
    if record["state"] == "error":
        return None
    passed, failed = read_summary(directory / "test_summary.env")
    if (passed, failed) != (record["counts"]["passed"], record["counts"]["failed"]):
        raise ValueError("Rozpor souhrnu a kategorií testů")
    return passed, failed


def publish_outcome(
    directory,
    identity,
    mode,
    number,
    state,
    exit_code,
    spreadsheet_required=False,
    message="",
    selection_data=None,
    counts=None,
):
    """Zveřejní ověřený záznam poslední; stará tabulka se použije jen jako vstup.

    Po dokončeném běhu nahradí sloučená tabulka kořenovou tabulku výběru
    v nadřazeném adresáři ``current/``.

    :param directory: Adresář ``current/`` aktuálního běhu.
    :param identity: Identita pokusu.
    :param mode: Režim výběru.
    :param number: Číslo testu.
    :param state: completed, no-tests nebo error.
    :param exit_code: Výsledek procesu nebo chyba přípravy.
    :param spreadsheet_required: Vyžaduje výběr novou tabulku Selenium testů.
    :param message: Diagnostika chyby.
    :param selection_data: Ověřená tabulka pro příští výběr, zveřejněná před záznamem dokončení.
    :param counts: Úplné kategorie provedených testů; povinné pro completed.
    """
    mode, number = selection(mode, number)
    names = {"test_output.log"} if state == "error" else FILES
    record = dict(
        version=2,
        attempt_id=identity,
        mode=mode,
        number=number,
        state=state,
        exit_code=exit_code,
        spreadsheet_required=spreadsheet_required,
        message=message,
        counts={key: 0 for key in COUNT_FIELDS} if state == "no-tests" and counts is None else counts,
        files={name: digest(directory / name) for name in sorted(names) if (directory / name).exists()},
    )
    validate_record(record, identity, mode, number)
    validate_bundle(directory, record)
    if state == "completed" and "results.xlsx" in record["files"] and selection_data is not None:
        atomic_write(directory.parent / "results.xlsx", selection_data)
    atomic_write(directory / "outcome.json", json.dumps(record, ensure_ascii=True, sort_keys=True).encode("utf-8"))
