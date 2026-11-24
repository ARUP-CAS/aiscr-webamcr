"""Váže výsledky testů na jeden pokus bez spouštění stažených dat."""

import hashlib
import json
import os
import re
import uuid
from pathlib import Path

FILES = {"test_summary.env", "results.xlsx", "test_output.log"}
FIELDS = {"version", "attempt_id", "mode", "number", "state", "exit_code", "spreadsheet_required", "files", "message"}


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


def create_attempt(root, identity=None):
    """Vytvoří nový adresář a odmítne přepsání existujícího pokusu.

    :param root: Kořen výsledků.
    :param identity: Identita z CI nebo None pro samostatné spuštění.
    :return: Cesta nového pokusu a jeho identita.
    """
    identity = validate_identity(identity or f"local-{uuid.uuid4().hex}")
    runs = Path(root) / "runs"
    if runs.is_symlink():
        raise ValueError("Adresář pokusů nesmí být odkaz")
    runs.mkdir(parents=True, exist_ok=True)
    directory = runs / identity
    directory.mkdir()
    return directory.resolve(), identity


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
    raw = path.read_bytes()
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
    if not isinstance(record, dict) or set(record) != FIELDS:
        raise ValueError("Neplatné schéma výsledku")
    if type(record["version"]) is not int or record["version"] != 1:
        raise ValueError("Neznámá verze výsledku")
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
    return record


def load_record(directory, identity, mode, number):
    """Načte JSON s odmítnutím duplicitních klíčů a bez vyhodnocování dat.

    :param directory: Adresář staženého pokusu.
    :param identity: Očekávaný pokus.
    :param mode: Očekávaný režim.
    :param number: Očekávané číslo.
    :return: Ověřená metadata.
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
    if path.is_symlink() or path.stat().st_size > 16384:
        raise ValueError("Neplatný soubor výsledku")
    record = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    return validate_record(record, identity, mode, number)


def validate_bundle(directory, record):
    """Ověří otisky a soulad čísel s výsledkem procesu před publikací.

    :param directory: Adresář aktuálního pokusu.
    :param record: Již ověřená metadata.
    :return: Počty testů, pro chybu None.
    """
    for filename, expected in record["files"].items():
        if digest(directory / filename) != expected:
            raise ValueError("Artefakt neodpovídá aktuálnímu výsledku")
    if record["state"] == "error":
        return None
    passed, failed = read_summary(directory / "test_summary.env")
    if record["state"] == "no-tests":
        if passed or failed:
            raise ValueError("No-op nesmí obsahovat provedené testy")
    elif passed + failed <= 0 or (record["exit_code"] == 0) != (failed == 0):
        raise ValueError("Rozpor výsledku procesu a čísel testů")
    return passed, failed


def publish_outcome(
    directory, identity, mode, number, state, exit_code, spreadsheet_required=False, message="", selection_data=None
):
    """Zveřejní ověřený záznam poslední; stará tabulka se použije jen jako vstup.

    :param directory: Nový adresář pokusu.
    :param identity: Identita pokusu.
    :param mode: Režim výběru.
    :param number: Číslo testu.
    :param state: completed, no-tests nebo error.
    :param exit_code: Výsledek procesu nebo chyba přípravy.
    :param spreadsheet_required: Vyžaduje výběr novou tabulku Selenium testů.
    :param message: Diagnostika chyby.
    :param selection_data: Ověřená tabulka pro příští výběr, zveřejněná před záznamem dokončení.
    """
    mode, number = selection(mode, number)
    names = {"test_output.log"} if state == "error" else FILES
    record = dict(
        version=1,
        attempt_id=identity,
        mode=mode,
        number=number,
        state=state,
        exit_code=exit_code,
        spreadsheet_required=spreadsheet_required,
        message=message,
        files={name: digest(directory / name) for name in sorted(names) if (directory / name).exists()},
    )
    validate_record(record, identity, mode, number)
    validate_bundle(directory, record)
    if state == "completed" and "results.xlsx" in record["files"] and selection_data is not None:
        atomic_write(directory.parent.parent / "results.xlsx", selection_data)
    atomic_write(directory / "outcome.json", json.dumps(record, ensure_ascii=True, sort_keys=True).encode("utf-8"))
