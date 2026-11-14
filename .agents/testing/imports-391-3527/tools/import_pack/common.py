"""Deterministické soubory, kontrolní součty a hranice testovacího balíčku."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

PACK = Path(__file__).resolve().parents[2]
STATES = {"prepared", "passed", "failed", "blocked", "unexecuted", "inapplicable"}
# Identity of the source/generator hashing rule; a pack pinned under another rule is stale.
SOURCE_HASH_MODE = "sha256-lf-text-v1"


def repo_root(start: Path = PACK) -> Path:
    """Najde repozitář bez čtení lokálního nastavení aplikace."""
    for path in (start, *start.parents):
        if (path / "webclient/core/import_data_mappers.py").is_file():
            return path
    raise ValueError("Source checkout unavailable; supply a repository for inventory refresh.")


def digest(data: bytes) -> str:
    """Vrátí SHA-256 vstupních bajtů."""
    return hashlib.sha256(data).hexdigest()


def source_digest(data: bytes) -> str:
    """
    Vrátí SHA-256 textového zdroje s konci řádků sjednocenými na LF.

    Stejný obsah v Gitu tak dává stejný otisk v CRLF i LF checkoutu, v ``git show`` i v nasazeném
    zdroji. Binární vstupy se otiskují funkcí :func:`digest` ze surových bajtů.

    :param data: Bajty textového souboru v libovolném kódování konců řádků.
    :return: Hexadecimální SHA-256 obsahu po převodu CRLF na LF.
    """
    return digest(data.replace(b"\r\n", b"\n"))


def generator_hashes():
    """Pin executable generator code and the frozen functional input definitions."""
    paths = list((PACK / "tools").rglob("*.py"))
    paths += [
        PACK / name
        for name in (
            "definitions/inventory.json",
            "definitions/coverage.json",
            "definitions/datasets.json",
            "definitions/expectations.json",
            "definitions/import-messages.json",
            "definitions/known-defects.json",
            "operator/terminology.json",
        )
    ]
    paths = [path for path in paths if path.exists()]
    if any(path.is_symlink() or not path.resolve().is_relative_to(PACK.resolve()) for path in paths):
        raise ValueError("Generator identity cannot follow external links")
    return {path.relative_to(PACK).as_posix(): source_digest(path.read_bytes()) for path in sorted(paths)}


def read_json(path: Path):
    """Read JSON or a single-cell/header CSV export of the SQL JSON value."""
    text = path.read_text(encoding="utf-8-sig")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import csv
        import io

        csv.field_size_limit(256 * 1024 * 1024)
        candidates = []
        for row in csv.reader(io.StringIO(text)):
            if len(row) == 1:
                try:
                    candidates.append(json.loads(row[0]))
                except json.JSONDecodeError:
                    pass
        if len(candidates) != 1:
            raise ValueError("Expected one JSON value or one JSON cell exported as CSV") from None
        return candidates[0]


def json_bytes(value) -> bytes:
    """Vrátí stabilní UTF-8 reprezentaci JSON."""
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_new(path: Path, data: bytes) -> None:
    """Vytvoří soubor; existující odlišný obsah nepřepíše."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Refusing to overwrite different content: {path}")
        return
    with path.open("xb") as stream:
        stream.write(data)


def save_json(path: Path, value) -> None:
    """Uloží nový nebo obsahově totožný JSON."""
    write_new(path, json_bytes(value))


def inside(root: Path, relative: str) -> Path:
    """Ověří výstupní cestu včetně symlinků před zápisem."""
    root = root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError("Path leaves the selected output root")
    return path


def namespace(value: str) -> str:
    """Povolí pouze číselný rozsah pro syntetické identifikátory."""
    if not re.fullmatch(r"9[0-9]{5}", value):
        raise ValueError("Namespace must be six digits starting with 9, e.g. 950000")
    return value


def assert_owned(repo: Path) -> None:
    """Odmítne překryv balíčku s doručenými soubory governance."""
    assets = read_json(repo / ".agents/delivery-manifest.json")["assets"]
    prefix = PACK.relative_to(repo).as_posix() + "/"
    if any(str(name).startswith(prefix) for name in assets):
        raise ValueError("Pack overlaps a delivered asset")
