#!/usr/bin/env python3
"""
Kontrola souladu manifestu ``webclient/static_vendor.json`` s knihovnami třetích stran vloženými
do ``webclient/static/``.

Ověřuje, že:

* každá položka manifestu má vyplněný název, verzi, licenci, zdroj a seznam cest,
* každá cesta z manifestu existuje a patří jen jedné položce,
* každý soubor pod ``webclient/static/vendor/`` je v manifestu,
* žádný adresář pod ``webclient/static/vendor/`` se nejmenuje jako balíček z ``dependencies``
  v ``package.json`` (knihovna nesmí být zároveň z npm i vendorovaná),
* relativní ``url(...)`` v CSS souborech z manifestu míří na existující soubor,
* každý odkaz ``{% static 'vendor/...' %}`` v šablonách míří na soubor z manifestu.

Výstup pro uživatele a CI: řádky na stderr s prefixem ``[static-vendor]`` (grep v GitHub Actions).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional, Set

LOG_PREFIX = "[static-vendor]"

# Relativní cesty od kořene repozitáře (pre-commit spouští z rootu).
MANIFEST = "webclient/static_vendor.json"
STATIC_DIR = "webclient/static"
VENDOR_SUBDIR = "vendor"
PACKAGE_JSON = "package.json"
TEMPLATES_ROOT = "webclient"

REQUIRED_TEXT_FIELDS = ("name", "version", "license", "source")
STATIC_VENDOR_REF_RE = re.compile(r"""\{%\s*static\s+['"](vendor/[^'"]+)['"]""")
CSS_URL_RE = re.compile(r"url\(([^)]*)\)")


def log_msg(message: str) -> None:
    """
    Vypíše jeden řádek na stderr s prefixem pro přehled v CI a PR komentářích.

    :param message: Text bez prefixu (typicky ``ERROR:`` nebo ``INFO:``).
    """
    print(f"{LOG_PREFIX} {message}", file=sys.stderr)


def repo_root() -> Path:
    """
    Vrátí kořen repozitáře (nadřazený adresář ``scripts/``).

    :return: Cesta ke kořeni.
    """
    return Path(__file__).resolve().parent.parent


def load_manifest(root: Path) -> List[dict]:
    """
    Načte seznam knihoven z manifestu ``webclient/static_vendor.json``.

    :param root: Kořen repozitáře.
    :return: Položky pole ``libraries``.
    :raises FileNotFoundError: Vyvolá se, pokud manifest neexistuje.
    :raises json.JSONDecodeError: Vyvolá se při neplatném JSON.
    :raises ValueError: Vyvolá se, pokud kořen není objekt nebo ``libraries`` není pole objektů.
    """
    path = root / MANIFEST
    if not path.is_file():
        raise FileNotFoundError(f"Chybí soubor {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get("libraries"), list):
        raise ValueError(f"{path}: očekáván objekt s polem 'libraries'")
    if not all(isinstance(item, dict) for item in data["libraries"]):
        raise ValueError(f"{path}: položky 'libraries' musí být objekty")
    return data["libraries"]


def load_npm_dependencies(root: Path) -> Set[str]:
    """
    Načte jména přímých závislostí z kořenového ``package.json``.

    :param root: Kořen repozitáře.
    :return: Klíče sekce ``dependencies``; prázdná množina, pokud soubor chybí.
    """
    path = root / PACKAGE_JSON
    if not path.is_file():
        return set()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    deps = data.get("dependencies") if isinstance(data, dict) else None
    return set(deps) if isinstance(deps, dict) else set()


def is_static_relative(rel: str) -> bool:
    """
    Ověří, že cesta z manifestu je POSIX cesta relativní k ``webclient/static/`` a nevede mimo něj.

    :param rel: Cesta z pole ``paths`` (např. ``vendor/leaflet-search/leaflet-search.js``).
    :return: ``False`` pro absolutní cestu, cestu s diskem, zpětným lomítkem nebo komponentou ``..``.
    """
    path = PurePosixPath(rel)
    return not ("\\" in rel or path.is_absolute() or ":" in path.parts[0] or ".." in path.parts)


def check_entries(libraries: List[dict], static_dir: Path) -> tuple[List[str], Dict[str, str]]:
    """
    Zkontroluje povinná pole položek a existenci jejich cest.

    :param libraries: Položky manifestu.
    :param static_dir: Adresář ``webclient/static``.
    :return: ``(chyby, mapa cesta → název knihovny)`` pro všechny cesty z manifestu.
    """
    errors: List[str] = []
    owners: Dict[str, str] = {}
    for index, lib in enumerate(libraries):
        label = lib.get("name") or f"#{index}"
        for field in REQUIRED_TEXT_FIELDS:
            value = lib.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"knihovna '{label}': chybí nebo je prázdné pole '{field}'")
        if not isinstance(lib.get("modified"), bool):
            errors.append(f"knihovna '{label}': pole 'modified' musí být true/false")
        paths = lib.get("paths")
        if not isinstance(paths, list) or not paths:
            errors.append(f"knihovna '{label}': pole 'paths' musí být neprázdný seznam")
            continue
        for rel in paths:
            if not isinstance(rel, str) or not rel:
                errors.append(f"knihovna '{label}': neplatná cesta {rel!r}")
                continue
            if not is_static_relative(rel):
                errors.append(
                    f"knihovna '{label}': cesta '{rel}' musí být relativní k {STATIC_DIR}/ "
                    "(bez '..', '\\' a absolutní cesty)"
                )
                continue
            if rel in owners:
                errors.append(f"cesta '{rel}' je uvedena u '{owners[rel]}' i u '{label}'")
                continue
            owners[rel] = label
            if not (static_dir / rel).is_file():
                errors.append(f"knihovna '{label}': soubor '{rel}' neexistuje ve {STATIC_DIR}/")
    return errors, owners


def check_vendor_dir(static_dir: Path, owners: Dict[str, str], npm_deps: Set[str]) -> List[str]:
    """
    Zkontroluje, že každý soubor pod ``static/vendor/`` je v manifestu a že žádný podadresář
    nenese jméno npm závislosti.

    :param static_dir: Adresář ``webclient/static``.
    :param owners: Mapa cesta → název knihovny z :func:`check_entries`.
    :param npm_deps: Jména závislostí z ``package.json``.
    :return: Seznam chyb.
    """
    errors: List[str] = []
    vendor_dir = static_dir / VENDOR_SUBDIR
    if not vendor_dir.is_dir():
        return errors
    for child in sorted(vendor_dir.iterdir()):
        if child.is_dir() and child.name in npm_deps:
            errors.append(
                f"'{VENDOR_SUBDIR}/{child.name}' je zároveň v package.json dependencies; "
                "odstraň vendorovanou kopii, nebo závislost z package.json"
            )
    for path in sorted(p for p in vendor_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(static_dir).as_posix()
        if rel not in owners:
            errors.append(f"soubor '{rel}' není v {MANIFEST}; doplň verzi, licenci a zdroj")
    return errors


def check_css_urls(static_dir: Path, owners: Dict[str, str]) -> List[str]:
    """
    Zkontroluje, že relativní ``url(...)`` v CSS souborech z manifestu míří na existující soubor.

    Absolutní URL (``http:``, ``//``, ``/``), ``data:`` URI a odkazy na fragment se přeskakují.

    :param static_dir: Adresář ``webclient/static``.
    :param owners: Mapa cesta → název knihovny z :func:`check_entries`.
    :return: Seznam chyb.
    """
    errors: List[str] = []
    for rel in sorted(owners):
        path = static_dir / rel
        if path.suffix != ".css" or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in CSS_URL_RE.finditer(text):
            target = match.group(1).strip().strip("'\"").split("?")[0].split("#")[0]
            if not target or re.match(r"^([a-z]+:|/|#)", target, re.IGNORECASE):
                continue
            if not (path.parent / target).resolve().is_file():
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{rel}:{line}: url('{target}') míří na neexistující soubor")
    return errors


def check_template_references(templates_root: Path, owners: Dict[str, str]) -> List[str]:
    """
    Zkontroluje, že odkazy ``{% static 'vendor/...' %}`` v šablonách míří na soubory z manifestu.

    :param templates_root: Adresář, pod kterým se hledají šablony ``*.html``.
    :param owners: Mapa cesta → název knihovny z :func:`check_entries`.
    :return: Seznam chyb.
    """
    errors: List[str] = []
    for template in sorted(templates_root.rglob("*.html")):
        if "node_modules" in template.parts:
            continue
        text = template.read_text(encoding="utf-8", errors="replace")
        for match in STATIC_VENDOR_REF_RE.finditer(text):
            if match.group(1) not in owners:
                line = text.count("\n", 0, match.start()) + 1
                rel = template.relative_to(templates_root.parent).as_posix()
                errors.append(f"{rel}:{line}: odkaz na '{match.group(1)}', který není v {MANIFEST}")
    return errors


def collect_errors(root: Path) -> List[str]:
    """
    Provede všechny kontroly nad repozitářem.

    :param root: Kořen repozitáře.
    :return: Seznam chyb; prázdný seznam znamená soulad.
    :raises FileNotFoundError: Vyvolá se, pokud manifest neexistuje.
    :raises json.JSONDecodeError: Vyvolá se při neplatném JSON manifestu nebo ``package.json``.
    :raises ValueError: Vyvolá se při neplatné struktuře manifestu.
    """
    static_dir = root / STATIC_DIR
    libraries = load_manifest(root)
    errors, owners = check_entries(libraries, static_dir)
    errors += check_vendor_dir(static_dir, owners, load_npm_dependencies(root))
    errors += check_css_urls(static_dir, owners)
    errors += check_template_references(root / TEMPLATES_ROOT, owners)
    return errors


def main(argv: Optional[List[str]] = None) -> int:
    """
    Vstupní bod CLI.

    :param argv: Argumenty bez ``sys.argv[0]``; ``None`` = ``sys.argv[1:]``.
    :return: ``0`` při souladu, ``1`` při chybě.
    """
    parser = argparse.ArgumentParser(
        description="Kontrola manifestu vendorovaných statických knihoven (webclient/static_vendor.json).",
    )
    parser.parse_args(argv)

    try:
        errors = collect_errors(repo_root())
    except (OSError, ValueError, json.JSONDecodeError) as e:
        log_msg(f"ERROR: čtení manifestu: {e}")
        return 1

    for error in errors:
        log_msg(f"ERROR: {error}")
    if errors:
        log_msg(f"INFO: pravidla viz {MANIFEST} a docs/source/12_zavislosti/javascript_knihovny.rst")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
