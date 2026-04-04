#!/usr/bin/env python3
"""
Kontrola souladu záložní n-tice ``_NPM_VENDOR_PACKAGE_NAMES`` v Django ``base.py`` s klíči
``dependencies`` v kořenovém ``package.json``.

Při ``--fix`` přepíše n-tici tak, aby přesně odpovídala (abecedně seřazené) klíčům z ``dependencies``.

Výstup pro uživatele a CI: řádky na stderr s prefixem ``[npm-vendor-names]`` (grep v GitHub Actions).
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import List, Optional, Set, Tuple

CONST_NAME = "_NPM_VENDOR_PACKAGE_NAMES"
ASSIGN_PREFIX_RE = re.compile(rf"^({CONST_NAME}\s*=\s*\()", re.MULTILINE)
LOG_PREFIX = "[npm-vendor-names]"

# Relativní cesty od kořene repozitáře (pre-commit spouští z rootu).
PACKAGE_JSON = "package.json"
BASE_PY = "webclient/webclient/settings/base.py"


def log_msg(message: str) -> None:
    """
    Vypíše jeden řádek na stderr s prefixem pro přehled v CI a PR komentářích.

    :param message: Text bez prefixu (typicky ``ERROR:``, ``FIX:`` nebo ``INFO:``).
    """
    print(f"{LOG_PREFIX} {message}", file=sys.stderr)


def repo_root() -> Path:
    """
    Vrátí kořen repozitáře (nadřazený adresář ``scripts/``).

    :return: Cesta ke kořeni.
    """
    return Path(__file__).resolve().parent.parent


def load_dependency_keys(root: Path) -> Set[str]:
    """
    Načte množinu jmen přímých závislostí z kořenového ``package.json``.

    :param root: Kořen repozitáře.
    :return: Klíče sekce ``dependencies``.
    :raises: ``FileNotFoundError``, ``json.JSONDecodeError``, ``ValueError`` při neplatném obsahu.
    """
    path = root / PACKAGE_JSON
    if not path.is_file():
        raise FileNotFoundError(f"Chybí soubor {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: očekáván JSON objekt na kořeni")
    deps = data.get("dependencies")
    if deps is None:
        return set()
    if not isinstance(deps, dict):
        raise ValueError(f"{path}: pole 'dependencies' musí být objekt")
    keys = [k for k in deps if isinstance(k, str)]
    if len(keys) != len(deps):
        raise ValueError(f"{path}: všechny klíče v 'dependencies' musí být řetězce")
    return set(keys)


def _tuple_inner_span(text: str, open_paren_index: int) -> Optional[Tuple[int, int]]:
    """
    Najde indexy obsahu n-tice: ``text[inner_start:inner_end]`` je tělo mezi závorkami (bez ``(`` a ``)``).

    Respektuje řetězce a escape sekvence; mimo řetězec ignoruje obsah po ``#`` do konce řádku.

    :param text: Celý obsah souboru.
    :param open_paren_index: Index otevírací závorky ``(`` přiřazení n-tice.
    :return: ``(inner_start, inner_end)`` nebo ``None`` při neuzavřené závorce.
    """
    i = open_paren_index + 1
    depth = 1
    in_str = False
    str_delim: Optional[str] = None
    escape = False
    n = len(text)
    while i < n and depth > 0:
        c = text[i]
        if escape:
            escape = False
            i += 1
            continue
        if in_str:
            if c == "\\":
                escape = True
            elif c == str_delim:
                in_str = False
                str_delim = None
            i += 1
            continue
        if c in "\"'":
            in_str = True
            str_delim = c
            i += 1
            continue
        if c == "#":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return open_paren_index + 1, i
        i += 1
    return None


def locate_vendor_tuple_assignment(text: str) -> Optional[Tuple[int, int, int, int]]:
    """
    Najde v ``base.py`` span přiřazení ``_NPM_VENDOR_PACKAGE_NAMES = (...)``.

    :param text: Obsah ``base.py``.
    :return: ``(assign_start, assign_end, inner_start, inner_end)`` — celý blok k nahrazení
        je ``text[assign_start:assign_end]``; ``inner_*`` je tělo n-tice pro ``ast``.
    """
    m = ASSIGN_PREFIX_RE.search(text)
    if not m:
        return None
    assign_start = m.start(1)
    open_paren = m.end(1) - 1
    inner = _tuple_inner_span(text, open_paren)
    if inner is None:
        return None
    inner_start, inner_end = inner
    close_paren = inner_end
    assign_end = close_paren + 1
    return assign_start, assign_end, inner_start, inner_end


def parse_tuple_string_literals(inner: str) -> List[str]:
    """
    Parsuje tělo n-tice a vrátí seznam řetězcových literálů v pořadí výskytu.

    :param inner: Obsah mezi ``(`` a ``)`` včetně komentářů a řádkových zalomení.
    :return: Seznam hodnot řetězců.
    :raises ValueError: při neplatné syntaxi nebo nečistě řetězcových prvcích.
    """
    snippet = f"{CONST_NAME} = ({inner})"
    try:
        tree = ast.parse(snippet)
    except SyntaxError as e:
        raise ValueError(f"Neplatná syntaxe n-tice {CONST_NAME}: {e}") from e
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        t = node.targets[0]
        if isinstance(t, ast.Name) and t.id == CONST_NAME:
            return _elts_as_str_list(node.value)
    raise ValueError(f"V úryvku chybí přiřazení {CONST_NAME}")


def _elts_as_str_list(value: ast.AST) -> List[str]:
    """Vrátí řetězce z ``ast.Tuple`` nebo jednoprvkové n-tice."""
    if isinstance(value, ast.Tuple):
        out: List[str] = []
        for elt in value.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                out.append(elt.value)
            else:
                raise ValueError(f"Očekávány pouze řetězcové literály v {CONST_NAME}, dostal {type(elt).__name__}")
        return out
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return [value.value]
    raise ValueError(f"Očekána n-tice řetězců pro {CONST_NAME}, dostal {type(value).__name__}")


def build_tuple_assignment(sorted_names: List[str]) -> str:
    """
    Sestaví text přiřazení ``_NPM_VENDOR_PACKAGE_NAMES = (...)`` ve stylu Black (odsazení 4 mezery).

    :param sorted_names: Již seřazené názvy balíčků.
    :return: Text včetně koncového ``\\n\\n`` před následující definici.
    """
    if not sorted_names:
        return f"{CONST_NAME} = ()\n\n"
    lines = [f'    "{name}",' for name in sorted_names]
    body = "\n".join(lines)
    return f"{CONST_NAME} = (\n{body}\n)\n\n"


def read_tuple_names(base_path: Path) -> Tuple[str, Set[str]]:
    """
    Načte ``base.py`` a extrahuje množinu jmen z ``_NPM_VENDOR_PACKAGE_NAMES``.

    :param base_path: Cesta k ``base.py``.
    :return: ``(celý_text, množina_jmen)``.
    """
    text = base_path.read_text(encoding="utf-8")
    loc = locate_vendor_tuple_assignment(text)
    if loc is None:
        raise ValueError(f"V {base_path} se nepodařilo najít {CONST_NAME} = (...)")
    _a, _b, inner_start, inner_end = loc
    inner = text[inner_start:inner_end]
    names = parse_tuple_string_literals(inner)
    return text, set(names)


def main(argv: Optional[List[str]] = None) -> int:
    """
    Vstupní bod CLI.

    :param argv: Argumenty bez ``sys.argv[0]``; ``None`` = ``sys.argv[1:]``.
    :return: ``0`` při OK; ``1`` při chybě nebo po úspěšném ``--fix`` se změnou souboru (pre-commit).
    """
    parser = argparse.ArgumentParser(
        description="Kontrola souladu _NPM_VENDOR_PACKAGE_NAMES s package.json dependencies.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Přepsat n-tici v base.py podle package.json (abecedně).",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    base_path = root / BASE_PY
    if not base_path.is_file():
        log_msg(f"ERROR: chybí soubor {base_path}")
        return 1

    try:
        dep_keys = load_dependency_keys(root)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        log_msg(f"ERROR: čtení package.json: {e}")
        return 1

    try:
        text, tuple_names = read_tuple_names(base_path)
    except (OSError, ValueError) as e:
        log_msg(f"ERROR: čtení {CONST_NAME}: {e}")
        return 1

    missing = sorted(dep_keys - tuple_names)
    extra = sorted(tuple_names - dep_keys)

    if not missing and not extra:
        return 0

    if not args.fix:
        if missing:
            log_msg(
                f"ERROR: v {CONST_NAME} chybí oproti package.json dependencies: {', '.join(missing)}",
            )
        if extra:
            log_msg(
                f"ERROR: v {CONST_NAME} jsou navíc oproti package.json dependencies: {', '.join(extra)}",
            )
        log_msg("INFO: spusť s --fix pro úpravu base.py (nebo doplň n-tici ručně).")
        return 1

    loc = locate_vendor_tuple_assignment(text)
    if loc is None:
        log_msg(f"ERROR: interní chyba — nenalezen span pro {CONST_NAME}")
        return 1
    assign_start, assign_end, _is, _ie = loc
    new_assign = build_tuple_assignment(sorted(dep_keys))
    new_text = text[:assign_start] + new_assign + text[assign_end:]
    base_path.write_text(new_text, encoding="utf-8", newline="\n")
    log_msg(
        f"FIX: upraven {base_path} — n-tice sjednocena s package.json ({len(dep_keys)} balíčků); "
        "znovu přidej do commitu.",
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
