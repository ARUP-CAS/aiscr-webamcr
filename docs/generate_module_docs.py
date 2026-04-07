#!/usr/bin/env python3
"""
Skript pro generování Sphinx dokumentace pro všechny Django moduly v webclient/
a jejich uložení do docs/source/04_django_aplikace/04_02_moduly/

Skript extrahuje docstringy z modulů a generuje podrobnou
reStructuredText dokumentaci pro každý adresář modulu.

Použití:
    python3 generate_module_docs.py [--build] [--mode MODE] [--module MODULE]

    Volby:
        --build         Také sestaví HTML dokumentaci (vyžaduje sphinx-build)
        --mode MODE     Režim generování: 'autodoc' (výchozí) nebo 'explicit'
                       - autodoc: Používá direktivy Sphinx autodoc
                       - explicit: Zapisuje docstringy přímo do RST
        --module MODULE Konkrétní modul ke zpracování (např. 'adb', 'core')
                       Pokud není zadáno, zpracuje všechny moduly

    Příklad s virtuálním prostředím:
        source .venv/bin/activate && python3 generate_module_docs.py --build
        source .venv/bin/activate && python3 generate_module_docs.py --module core
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import traceback
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import yaml

sys.stdout.reconfigure(encoding="utf-8")

# Define paths
docs_dir = Path(__file__).parent
project_root = docs_dir.parent
webclient_dir = project_root / "webclient"
output_base_dir = docs_dir / "source/04_django_aplikace/04_02_moduly"
docs_scripts_output_dir = docs_dir / "source/03_vyvoj/dokumentacni_skripty"
project_scripts_dir = project_root / "scripts"
project_scripts_output_dir = docs_dir / "source/03_vyvoj/projektove_skripty"
XS_NS = "{http://www.w3.org/2001/XMLSchema}"

# Files to skip
SKIP_FILES = {"urls.py", "__init__.py", "apps.py"}

# Adresáře k přeskočení (nejsou to Django aplikace).
SKIP_DIRS = {"static", "templates", "locale", "__pycache__", "services"}

# Sleduje, zda došlo ke změně souborů.
changes_detected = False

# Běžné popisy typů souborů
FILE_TYPE_INFO = {
    "models.py": {"suffix": "modely", "description": "Definice modelů."},
    "forms.py": {"suffix": "formuláře", "description": "Definice formulářů."},
    "views.py": {"suffix": "views", "description": "Definice views."},
    "signals.py": {"suffix": "signály", "description": "Definice signálů."},
    "admin.py": {"suffix": "admin", "description": "Konfigurace Django admin."},
    "managers.py": {"suffix": "managers", "description": "Definice manažerů."},
    "serializers.py": {"suffix": "serializers", "description": "Definice serializérů."},
    "permissions.py": {"suffix": "permissions", "description": "Definice oprávnění."},
    "filters.py": {"suffix": "filtry", "description": "Definice filtrů."},
    "widgets.py": {"suffix": "widgety", "description": "Definice widgetů."},
}


def check_content_changed(content: str, output_file: Path) -> bool:
    """Zkontroluje, zda se obsah liší od existujícího souboru.

    :param content: Nový obsah k porovnání.
    :param output_file: Cesta k existujícímu souboru.
    :return: True, pokud se obsah změnil nebo soubor neexistuje
    """
    if not output_file.exists():
        return True

    try:
        with open(output_file, "r", encoding="utf-8") as f:
            existing_content = f.read()
        return existing_content != content
    except Exception:
        return True


def extract_url_patterns(urls_file: Path) -> Tuple[Optional[str], List[Dict[str, str]]]:
    """Extrahujte vzory URL ze souboru urls.py.

    :param urls_file: Cesta k souboru urls.py.
    :return: Každý url_pattern je slovník s klíči: ``pattern``, ``view``, ```name```
    """
    try:
        with open(urls_file, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        app_name = None
        url_patterns = []

        # Find app_name
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "app_name":
                        if isinstance(node.value, ast.Constant):
                            app_name = node.value.value

        # Find urlpatterns list
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "urlpatterns":
                        if isinstance(node.value, ast.List):
                            for item in node.value.elts:
                                url_info = parse_path_call(item)
                                if url_info:
                                    url_patterns.append(url_info)

        return app_name, url_patterns

    except Exception as e:
        print(f"  ⚠ Warning: Could not parse {urls_file}: {e}")
        return None, []


def parse_path_call(node: ast.AST) -> Optional[Dict[str, str]]:
    """Analyzuje volání path() nebo re_path() a extrahuje informace o vzoru URL.

    :param node: uzel AST představující volání path().
    :return: ```dict: {'pattern': str, 'view': str, 'name': str} or None```
    """
    if not isinstance(node, ast.Call):
        return None

    # Ověří, zda jde o některou z funkcí pro definici URL tras.
    if isinstance(node.func, ast.Name) and node.func.id not in ["path", "re_path"]:
        return None

    if len(node.args) < 2:
        return None

    # Získá pattern (první argument).
    pattern = None
    if isinstance(node.args[0], ast.Constant):
        pattern = node.args[0].value

    # Získá pohled (druhý argument).
    view = None
    if isinstance(node.args[1], ast.Attribute):
        # např. views.zapsat nebo views.MyView.as_view()
        if isinstance(node.args[1].value, ast.Name):
            view = f"{node.args[1].value.id}.{node.args[1].attr}"
    elif isinstance(node.args[1], ast.Name):
        # např. post_upload
        view = node.args[1].id
    elif isinstance(node.args[1], ast.Call):
        # např. MyView.as_view()
        if isinstance(node.args[1].func, ast.Attribute):
            if isinstance(node.args[1].func.value, ast.Name):
                view = f"{node.args[1].func.value.id}.as_view()"
            elif isinstance(node.args[1].func.value, ast.Attribute):
                # Nested attribute like views.MyView.as_view()
                if isinstance(node.args[1].func.value.value, ast.Name):
                    view = f"{node.args[1].func.value.value.id}.{node.args[1].func.value.attr}.as_view()"

    # Získá název z pojmenovaných argumentů.
    name = None
    for keyword in node.keywords:
        if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
            name = keyword.value.value

    if pattern is not None:
        return {"pattern": pattern, "view": view or "N/A", "name": name or "N/A"}

    return None


def generate_url_routing_rst() -> bool:
    """Vygeneruje dokumentaci k směrování URL pro všechny moduly.

    Vytvoří docs/source/04_django_aplikace/04_01_core/url_routing.rst
    s tabulkami všech vzorů URL z urls.py každého modulu.

    :return: True, pokud úspěšné, jinak false
    """
    global changes_detected
    output_file = docs_dir / "source/04_django_aplikace/04_01_core/url_routing.rst"

    print("\n  Generating URL routing documentation")
    print(f"  Output: {output_file}")

    rst_lines = ["URL Routing", "===========", "", "Dokumentace všech URL adres v aplikaci.", ""]

    # Get all modules
    modules = []
    for item in sorted(webclient_dir.iterdir()):
        if item.is_dir() and not item.name.startswith(".") and item.name not in SKIP_DIRS:
            # Přeskočí hlavní `webclient/urls.py` (URL na úrovni projektu).
            if item.name == "webclient":
                continue
            urls_file = item / "urls.py"
            if urls_file.exists():
                modules.append((item.name, urls_file))

    if not modules:
        print("  ⊝ No urls.py files found")
        return False

    # Process each module
    for module_name, urls_file in modules:
        app_name, url_patterns = extract_url_patterns(urls_file)

        if not url_patterns:
            continue

        # Add module section
        module_display = app_name.upper() if app_name else module_name.upper()
        rst_lines.extend(
            [
                "",
                module_display,
                "-" * len(module_display),
                "",
                ".. list-table::",
                "   :header-rows: 1",
                "   :widths: 30 40 30",
                "",
                "   * - Název",
                "     - URL",
                "     - Cíl",
            ]
        )

        # Add URL patterns
        for url_info in url_patterns:
            rst_lines.extend(
                [
                    f"   * - ``{url_info['name']}``",
                    f"     - ``{url_info['pattern']}``",
                    f"     - ``{url_info['view']}``",
                ]
            )

        print(f"    ✓ {module_name}: {len(url_patterns)} URLs")

    # Zapíše soubor.
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        new_content = "\n".join(rst_lines)
        if check_content_changed(new_content, output_file):
            changes_detected = True
            print("    ⚠ URL routing documentation needs update")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("    ✓ URL routing documentation generated")
        return True
    except Exception as e:
        print(f"    ✗ Error writing URL routing documentation: {e}")
        return False


def extract_signals(signals_file: Path) -> List[Dict[str, str]]:
    """Extrahuje přijímače signálu ze souboru signals.py.

    :param signals_file: Cesta k souboru signals.py.
    :return: Seznam slovníků informací o signálech s klíči: ``function``, ``signal_type``, ``sender``, ```weak```
    """
    try:
        with open(signals_file, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        signals = []

        for node in tree.body:
            # Hledá funkce dekorované `@receiver`.
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        # Ověří, zda je dekorátor `receiver()`.
                        if isinstance(decorator.func, ast.Name) and decorator.func.id == "receiver":
                            signal_info = parse_receiver_decorator(decorator, node.name)
                            if signal_info:
                                signals.append(signal_info)

        return signals

    except Exception as e:
        print(f"  ⚠ Warning: Could not parse {signals_file}: {e}")
        return []


def parse_receiver_decorator(decorator: ast.Call, function_name: str) -> Optional[Dict[str, str]]:
    """Analyzuje dekorátor @receiver() pro extrakci informací o signálu.

    :param decorator: AST Volací uzel představující @receiver()
    :param function_name: Název dekorované funkce
    :return: ```dict: {'function': str, 'signal_type': str, 'sender': str, 'weak': str} or None```
    """
    if len(decorator.args) == 0:
        return None

    # Extract signal type (first argument)
    signal_type = None
    if isinstance(decorator.args[0], ast.Attribute):
        signal_type = decorator.args[0].attr
    elif isinstance(decorator.args[0], ast.Name):
        signal_type = decorator.args[0].id

    # Získá `sender` a `weak` z pojmenovaných argumentů.
    sender = "N/A"
    weak = "True"  # Výchozí hodnota v Django.

    for keyword in decorator.keywords:
        if keyword.arg == "sender":
            if isinstance(keyword.value, ast.Attribute):
                sender = keyword.value.attr
            elif isinstance(keyword.value, ast.Name):
                sender = keyword.value.id
        elif keyword.arg == "weak":
            if isinstance(keyword.value, ast.Constant):
                weak = str(keyword.value.value)

    return {"function": function_name, "signal_type": signal_type or "N/A", "sender": sender, "weak": weak}


def generate_signals_rst() -> bool:
    """Vygeneruje dokumentaci signálů pro všechny moduly.

    Vytvoří docs/source/04_django_aplikace/04_01_core/signals.rst
    s tabulkami všech přijímačů signálů z každého modulu signals.py

    :return: True v případě úspěchu, False v opačném případě.
    """
    global changes_detected
    output_file = docs_dir / "source/04_django_aplikace/04_01_core/signals.rst"

    print("\n  Generating signals documentation")
    print(f"  Output: {output_file}")

    rst_lines = ["Signály", "=======", "", "Dokumentace všech signálů v aplikaci.", ""]

    # Get all modules
    modules = []
    for item in sorted(webclient_dir.iterdir()):
        if item.is_dir() and not item.name.startswith(".") and item.name not in SKIP_DIRS:
            # Přeskočí hlavní modul `webclient`.
            if item.name == "webclient":
                continue
            signals_file = item / "signals.py"
            if signals_file.exists():
                modules.append((item.name, signals_file))

    if not modules:
        print("  ⊝ No signals.py files found")
        return False

    # Process each module
    for module_name, signals_file in modules:
        signals_list = extract_signals(signals_file)

        if not signals_list:
            continue

        # Add module section
        module_display = module_name.upper()
        rst_lines.extend(
            [
                "",
                module_display,
                "-" * len(module_display),
                "",
                ".. list-table::",
                "   :header-rows: 1",
                "   :widths: 30 30 40",
                "",
                "   * - Model",
                "     - Typ signálu",
                "     - Název funkce",
            ]
        )

        # Add signals
        for signal_info in signals_list:
            rst_lines.extend(
                [
                    f"   * - ``{signal_info['sender']}``",
                    f"     - ``{signal_info['signal_type']}``",
                    f"     - ``{signal_info['function']}``",
                ]
            )

        print(f"    ✓ {module_name}: {len(signals_list)} signals")

    # Zapíše soubor.
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        new_content = "\n".join(rst_lines)
        if check_content_changed(new_content, output_file):
            changes_detected = True
            print("    ⚠ Signals documentation needs update")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("    ✓ Signals documentation generated")
        return True
    except Exception as e:
        print(f"    ✗ Error writing signals documentation: {e}")
        return False


def extract_permissions(models_file: Path) -> List[str]:
    """Extrahuje možnosti akcí z třídy Permissions v models.py.

    :param models_file: Cesta k souboru models.py.
    :return: Seznam názvů akcí (např. ``adb_smazat``, ```vb_smazat```)
    """
    try:
        with open(models_file, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        actions = []

        # Najde třídu Permissions.
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "Permissions":
                # Najde vnořenou třídu actionChoices.
                for item in node.body:
                    if isinstance(item, ast.ClassDef) and item.name == "actionChoices":
                        # Extract all assignments in actionChoices
                        for choice_node in item.body:
                            if isinstance(choice_node, ast.AnnAssign) and isinstance(choice_node.target, ast.Name):
                                # Skip special attributes
                                if not choice_node.target.id.startswith("_"):
                                    actions.append(choice_node.target.id)
                            elif isinstance(choice_node, ast.Assign):
                                for target in choice_node.targets:
                                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                                        actions.append(target.id)
                        break
                break

        return actions

    except Exception as e:
        print(f"  ⚠ Warning: Could not parse {models_file}: {e}")
        return []


def generate_permissions_rst() -> bool:
    """Vygeneruje dokumentaci oprávnění.

    Aktualizuje docs/source/04_django_aplikace/04_01_core/permissions.rst
    připojením seznamu všech definovaných akcí z Permissions.actionChoices
    za nadpis „Uživatelské akce řízené pomocí oprávnění”.

    :return: True, pokud úspěšné, jinak False.
    """
    global changes_detected
    output_file = docs_dir / "source/04_django_aplikace/04_01_core/permissions.rst"

    print("\n  Generating permissions documentation")
    print(f"  Output: {output_file}")

    # Find core/models.py
    models_file = webclient_dir / "core" / "models.py"
    if not models_file.exists():
        print("  ⊝ core/models.py not found")
        return False

    # Extract actions
    actions = extract_permissions(models_file)

    if not actions:
        print("  ⊝ No actions found in Permissions.actionChoices")
        return False

    # Načte existující obsah, pokud soubor existuje.
    existing_content = []
    marker_heading = "Uživatelské akce řízené pomocí oprávnění"
    marker_found = False

    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Najde značkový nadpis a ponechá vše před ním (včetně nadpisu a oddělovače).
        for i, line in enumerate(lines):
            existing_content.append(line.rstrip())
            if line.strip() == marker_heading:
                marker_found = True
                # Zahrne i řádek oddělovače (pomlčky) za nadpisem.
                if i + 1 < len(lines) and lines[i + 1].strip().startswith("-"):
                    existing_content.append(lines[i + 1].rstrip())
                break

    # Pokud značka není nalezena, vytvoří výchozí strukturu.
    if not marker_found:
        existing_content.extend(
            [
                marker_heading,
                "-" * len(marker_heading),
            ]
        )

    # Sestaví nový obsah k připojení.
    new_content = [
        "",
        "Používá se pro bližší specifikaci akce či součásti view, pro které se oprávnění uplatňuje. Seznam všech akcí definovaných ve třídě ``Permissions.actionChoices``:",
        "",
    ]

    # Add actions as bullet list
    for action in actions:
        new_content.append(f"- ``{action}``")

    new_content.append("")
    new_content.append(f"**Celkem:** {len(actions)} akcí")

    # Spojí existující a nový obsah.
    final_content = existing_content + new_content

    # Zapíše soubor.
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        final_text = "\n".join(final_content)
        if check_content_changed(final_text, output_file):
            changes_detected = True
            print("    ⚠ Permissions documentation needs update")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_text)
        print(f"    ✓ Found {len(actions)} actions")
        print("    ✓ Permissions documentation updated (preserved existing content)")
        return True
    except Exception as e:
        print(f"    ✗ Error writing permissions documentation: {e}")
        return False


def clean_comment_value(value: str) -> str:
    """Odstraní obalové uvozovky/závorky z hodnoty komentáře.

    :param value: Parametr ``value`` pracuje se s atributy ``strip``.
    :return: Hodnota vrácená funkcí podle aktuální logiky implementace.
    """
    cleaned = value.strip()
    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1].strip()
    if cleaned.startswith("{") and cleaned.endswith("}"):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def parse_comment_values(comment_text: str) -> Tuple[str, str]:
    """Vrátí mapované hodnoty získané z inline komentáře XSD.

    :param comment_text: Číselná hodnota ``comment_text`` použitá při výpočtu nebo transformaci.
    :return: Hodnota vrácená funkcí podle aktuální logiky implementace.
    """
    if not comment_text:
        return "", ""

    parts = [clean_comment_value(part) for part in comment_text.split("|")]
    value = parts[0] if parts else ""
    description = parts[1] if len(parts) > 1 else ""

    if value.lower() == "self":
        return "", ""

    return value, description


def get_following_comment(parent: ET.Element, element: ET.Element) -> str:
    """Najde první uzel komentáře bezprostředně za daným elementem.

    :param parent: Parametr ``parent`` se předává do volání ``list()``.
    :param element: Parametr ``element`` ovlivňuje větvení podmínek.
    :return: Hodnota vrácená funkcí podle aktuální logiky implementace.
    """
    siblings = list(parent)
    for index, node in enumerate(siblings):
        if node is element and index + 1 < len(siblings):
            next_node = siblings[index + 1]
            if next_node.tag is ET.Comment:
                return (next_node.text or "").strip()
    return ""


def collect_choice_element_names(choice_element: ET.Element) -> List[str]:
    """Shromáždí názvy všech uzlů xs:element uvnitř bloku choice.

    :param choice_element: Parametr ``choice_element`` slouží jako vstup pro logiku funkce ``collect_choice_element_names``.
    :return: Hodnota vrácená funkcí podle aktuální logiky implementace.
    """
    names: List[str] = []
    for child in choice_element:
        if child.tag == f"{XS_NS}element":
            names.append(child.attrib.get("name", ""))
        elif child.tag in {f"{XS_NS}sequence", f"{XS_NS}choice"}:
            names.extend(collect_choice_element_names(child))
    return names


def format_choice_note(names: List[str]) -> str:
    """Naformátuje poznámku popisující možnosti uvnitř elementu choice.

    :param names: Kolekce ``names`` zpracovávaná touto funkcí.
    :return: Hodnota vrácená funkcí podle aktuální logiky implementace.
    """
    options = [name for name in names if name]
    if len(options) < 2:
        return ""
    if len(options) == 2:
        readable = " a ".join(options)
    else:
        readable = ", ".join(options[:-1]) + f" a {options[-1]}"
    return f"Volba mezi {readable}"


def extract_elements_from_parent(
    parent: ET.Element, choice_context: Optional[List[str]] = None
) -> List[Dict[str, str]]:
    """Rekurzivně extrahuje definice elementů a zaznamená kontext choice, pokud existuje.

    :param parent: Parametr ``parent`` se předává do volání ``get_following_comment()``.
    :param choice_context: Kolekce ``choice_context`` zpracovávaná touto funkcí.
    :return: Hodnota vrácená funkcí podle aktuální logiky implementace.
    """
    rows: List[Dict[str, str]] = []

    for child in parent:
        if child.tag == f"{XS_NS}element":
            comment = get_following_comment(parent, child)
            value_map, description_map = parse_comment_values(comment)
            rows.append(
                {
                    "name": child.attrib.get("name", ""),
                    "min": child.attrib.get("minOccurs", "1"),
                    "max": child.attrib.get("maxOccurs", "1"),
                    "type": child.attrib.get("type", ""),
                    "value_map": value_map,
                    "description_map": description_map,
                    "note": format_choice_note(choice_context or []),
                }
            )
        elif child.tag == f"{XS_NS}sequence":
            rows.extend(extract_elements_from_parent(child, choice_context=choice_context))
        elif child.tag == f"{XS_NS}choice":
            choice_names = collect_choice_element_names(child)
            rows.extend(extract_elements_from_parent(child, choice_context=choice_names))

    return rows


def extract_elements_from_complex_type(complex_type: ET.Element) -> List[Dict[str, str]]:
    """Extrahuje řádky elementů z definice complexType.

    :param complex_type: Parametr ``complex_type`` slouží jako vstup pro logiku funkce ``extract_elements_from_complex_type``.
    :return: Hodnota vrácená funkcí podle aktuální logiky implementace.
    """
    rows: List[Dict[str, str]] = []
    for child in complex_type:
        if child.tag in {f"{XS_NS}sequence", f"{XS_NS}choice"}:
            rows.extend(extract_elements_from_parent(child))
    return rows


def extract_model_mappings(schema_root: ET.Element) -> List[Dict[str, str]]:
    """Načte mapování z volby elementu amcr do řádků Model -> ComplexType.

    :param schema_root: Parametr ``schema_root`` pracuje se s atributy ``find``.
    :return: Hodnota vrácená funkcí podle aktuální logiky implementace.
    """
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
    mappings: List[Dict[str, str]] = []

    amcr_element = schema_root.find("xs:element[@name='amcr']", ns)
    if amcr_element is None:
        return mappings

    choice = amcr_element.find(".//xs:choice", ns)
    if choice is None:
        return mappings

    for element in choice:
        if element.tag != f"{XS_NS}element":
            continue
        comment = get_following_comment(choice, element)
        value_map, _ = parse_comment_values(comment)
        model_name = value_map or element.attrib.get("name", "")
        mappings.append({"model": model_name, "type": element.attrib.get("type", "")})

    return mappings


def extract_xsd_version(schema_root: ET.Element) -> str:
    """Extrahuje atribut verze z kořenového prvku schématu XSD.

    :param schema_root: Kořenový prvek schématu XSD.
    :return: Verze (např. „2.2“) nebo „neznámá“, pokud nebyla nalezena
    """
    return schema_root.attrib.get("version", "neznámá")


def extract_django_command_info(command_file: Path) -> Dict[str, str]:
    """Extrahuje informace o dokumentaci ze souboru příkazů pro správu Django.

    :param command_file: Cesta k příkazovému souboru.
    :return: ```dict: {'name': str, 'help': str, 'docstring': str, 'arguments': list}```
    """
    try:
        with open(command_file, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        command_name = command_file.stem
        command_help = ""
        command_docstring = ""
        arguments = []

        # Najde třídu Command.
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "Command":
                # Získá docstring třídy.
                command_docstring = ast.get_docstring(node) or "Popis není k dispozici."

                # Find help attribute
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "help":
                                if isinstance(item.value, ast.Constant):
                                    command_help = item.value.value
                                elif isinstance(item.value, ast.Call):
                                    # Help uses gettext(_())
                                    if item.value.args and isinstance(item.value.args[0], ast.Constant):
                                        command_help = item.value.args[0].value

                    # Najde metodu add_arguments a získá informace o argumentech.
                    elif isinstance(item, ast.FunctionDef) and item.name == "add_arguments":
                        arguments = extract_command_arguments(item)
                break

        return {
            "name": command_name,
            "help": command_help,
            "docstring": command_docstring,
            "arguments": arguments,
        }

    except Exception as e:
        print(f"  ⚠ Warning: Could not parse {command_file}: {e}")
        return {
            "name": command_file.stem,
            "help": "",
            "docstring": "Popis není k dispozici.",
            "arguments": [],
        }


def extract_command_arguments(add_arguments_node: ast.FunctionDef) -> List[Dict[str, str]]:
    """Extrahuje definice argumentů z metody add_arguments.

    :param add_arguments_node: AST uzel metody add_arguments.
    :return: Seznam slovníků s informacemi o argumentech s klíči: ``name``, ``type``, ``help``, ```default```
    """
    arguments = []

    for item in add_arguments_node.body:
        if isinstance(item, ast.Expr) and isinstance(item.value, ast.Call):
            call = item.value
            # Ověří, zda jde o `parser.add_argument()`.
            if isinstance(call.func, ast.Attribute) and call.func.attr == "add_argument":
                if call.args and isinstance(call.args[0], ast.Constant):
                    arg_name = call.args[0].value

                    # Extract keyword arguments
                    arg_type = ""
                    arg_help = ""
                    arg_default = ""

                    for keyword in call.keywords:
                        if keyword.arg == "type":
                            if isinstance(keyword.value, ast.Name):
                                arg_type = keyword.value.id
                        elif keyword.arg == "help":
                            if isinstance(keyword.value, ast.Constant):
                                arg_help = keyword.value.value
                            elif isinstance(keyword.value, ast.Call):
                                # Help uses gettext(_())
                                if keyword.value.args and isinstance(keyword.value.args[0], ast.Constant):
                                    arg_help = keyword.value.args[0].value
                        elif keyword.arg == "default":
                            if isinstance(keyword.value, ast.Constant):
                                arg_default = str(keyword.value.value)

                    arguments.append(
                        {
                            "name": arg_name,
                            "type": arg_type,
                            "help": arg_help,
                            "default": arg_default,
                        }
                    )

    return arguments


def generate_management_commands_rst() -> bool:
    """Vygeneruje dokumentaci k příkazům pro správu.

    Vytvoří docs/source/04_django_aplikace/04_01_core/management_commands.rst
    s dokumentací ke všem příkazům pro správu Django v core/management/commands.

    :return: True, pokud úspěšné, jinak False.
    """
    global changes_detected
    output_file = docs_dir / "source/04_django_aplikace/04_01_core/management_commands.rst"
    commands_dir = webclient_dir / "core" / "management" / "commands"

    print("\n  Generating management commands documentation")
    print(f"  Source: {commands_dir}")
    print(f"  Output: {output_file}")

    if not commands_dir.exists():
        print("  ⊝ Commands directory not found")
        return False

    # Get all command files
    command_files = []
    for item in sorted(commands_dir.iterdir()):
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            command_files.append(item)

    if not command_files:
        print("  ⊝ No command files found")
        return False

    rst_lines = [
        "Management příkazy",
        "==================",
        "",
        "Dokumentace všech Django management příkazů v aplikaci.",
        "",
        "Spuštění v Docker kontejneru",
        "----------------------------",
        "",
        "Pokud aplikace běží v kontejneru, je možné buď nejprve spustit terminál v kontejneru a následně zadat příkaz,",
        "případně spustit příkaz přímo bez otevření interaktivního shellu.",
        "",
        "**Bez swarm módu (vývoj):**",
        "",
        "Tento postup se využívá pro vývojové prostředí, proto se příkazy spouští s vývojovým nastavením ``--settings=webclient.settings.dev``.",
        "",
        "1. Zjistěte ID běžícího kontejneru:",
        "",
        "   .. code-block:: bash",
        "",
        "      docker ps",
        "",
        "2. Spusťte shell v kontejneru (například s ID ``fdd99a0b6c90``):",
        "",
        "   .. code-block:: bash",
        "",
        "      docker exec -it aiscr-webamcr-web /bin/sh",
        "",
        "3. Poté spusťte požadovaný příkaz:",
        "",
        "   .. code-block:: bash",
        "",
        "      python manage.py <název_příkazu> [parametry] --settings=webclient.settings.dev",
        "",
        "Alternativně je možné vše zapsat do jednoho příkazu (bez otevření interaktivního shellu):",
        "",
        ".. code-block:: bash",
        "",
        "   docker exec -it $(docker ps -q -f name=aiscr-webamcr-web) python manage.py <název_příkazu> [parametry] --settings=webclient.settings.dev",
        "",
        "**Se swarm módem (produkce):**",
        "",
        "Swarm mód se používá pro produkční nasazení, proto se příkazy spouští s produkčním nastavením ``--settings=webclient.settings.production``.",
        "",
        "1. Zjistěte ID běžícího kontejneru:",
        "",
        "   .. code-block:: bash",
        "",
        "      sudo docker ps",
        "",
        "2. Spusťte shell v kontejneru:",
        "",
        "   .. code-block:: bash",
        "",
        "      sudo docker exec -it <ID_kontejneru> /bin/sh",
        "",
        "3. Poté spusťte požadovaný příkaz:",
        "",
        "   .. code-block:: bash",
        "",
        "      python3 manage.py <název_příkazu> [parametry] --settings=webclient.settings.production",
        "",
        "Alternativně je možné vše zapsat do jednoho příkazu (bez otevření interaktivního shellu):",
        "",
        ".. code-block:: bash",
        "",
        "   docker exec -it $(sudo docker ps -q -f name=swarm_webamcr_web) python3 manage.py <název_příkazu> [parametry] --settings=webclient.settings.production",
        "",
    ]

    # Process each command
    for command_file in command_files:
        command_info = extract_django_command_info(command_file)

        # Add command section
        command_title = f"``{command_info['name']}``"
        rst_lines.extend(
            [
                "",
                command_title,
                "-" * len(command_title),
                "",
            ]
        )

        # Přidá odkaz na modul pro autodoc.
        rst_lines.extend(
            [
                f".. automodule:: core.management.commands.{command_info['name']}",
                "   :members: Command",
                "   :undoc-members:",
                "",
            ]
        )

        # Přidá tabulku argumentů, pokud existují.
        if command_info["arguments"]:
            rst_lines.extend(
                [
                    "**Parametry:**",
                    "",
                    ".. list-table::",
                    "   :header-rows: 1",
                    "   :widths: 30 20 20 30",
                    "",
                    "   * - Název",
                    "     - Typ",
                    "     - Výchozí hodnota",
                    "     - Popis",
                ]
            )

            for arg in command_info["arguments"]:
                rst_lines.extend(
                    [
                        f"   * - ``{arg['name']}``",
                        f"     - ``{arg['type']}``" if arg["type"] else "     - ",
                        f"     - ``{arg['default']}``" if arg["default"] else "     - ",
                        f"     - {arg['help']}" if arg["help"] else "     - ",
                    ]
                )

            rst_lines.append("")

        print(f"    ✓ {command_info['name']}")

    # Zapíše soubor.
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        new_content = "\n".join(rst_lines)
        if check_content_changed(new_content, output_file):
            changes_detected = True
            print("    ⚠ Management commands documentation needs update")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"    ✓ Found {len(command_files)} commands")
        print("    ✓ Management commands documentation generated")
        return True
    except Exception as e:
        print(f"    ✗ Error writing management commands documentation: {e}")
        return False


def generate_export_structure_rst() -> bool:
    """Vygeneruje docs/source/05_integrace/export_structure.rst ze souboru amcr.xsd.

    :return: Hodnota vrácená funkcí podle aktuální logiky implementace.
    """
    global changes_detected
    xsd_file = project_root / "webclient/xml_generator/definitions/amcr.xsd"
    output_file = docs_dir / "source/05_integrace/export_structure.rst"

    print("\n  Generating export structure documentation")
    print(f"  Source: {xsd_file}")
    print(f"  Output: {output_file}")

    if not xsd_file.exists():
        print("  ⊝ XSD schema not found")
        return False

    try:
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        tree = ET.parse(xsd_file, parser=parser)
    except Exception as exc:
        print(f"  ✗ Failed to parse XSD: {exc}")
        return False

    schema_root = tree.getroot()
    xsd_version = extract_xsd_version(schema_root)
    print(f"    XSD schema version: {xsd_version}")
    model_mappings = extract_model_mappings(schema_root)

    documented_complex_types: List[ET.Element] = []
    generic_type_names: List[str] = []
    generic_boundary_reached = False

    # Respektuje pozici komentáře „generic-types“ pro rozdělení zpracování.
    for child in list(schema_root):
        if child.tag is ET.Comment and (child.text or "").strip() == "generic-types":
            generic_boundary_reached = True
            continue

        if child.tag == f"{XS_NS}complexType":
            if generic_boundary_reached:
                name = child.attrib.get("name", "")
                if name:
                    generic_type_names.append(name)
            else:
                documented_complex_types.append(child)

    rst_lines = [
        "Struktura XML exportu",
        "=====================",
        "",
        f"Tento dokument popisuje strukturu XML exportu z databáze AMCR podle XML schématu verze {xsd_version}.",
        "",
    ]

    if model_mappings:
        rst_lines.extend(
            [
                "Mapování modelů na komplexní typy",
                "---------------------------------",
                "",
                ".. list-table::",
                "   :header-rows: 1",
                "   :widths: 50 50",
                "",
                "   * - Model",
                "     - Komplexní typ",
            ]
        )

        for mapping in model_mappings:
            rst_lines.extend(
                [
                    f"   * - ``{mapping['model']}``",
                    f"     - ``{mapping['type']}``",
                ]
            )

        rst_lines.append("")

    for complex_type in documented_complex_types:
        type_name = complex_type.attrib.get("name", "")
        rows = extract_elements_from_complex_type(complex_type)

        rst_lines.extend(
            [
                type_name,
                "-" * len(type_name),
                "",
                ".. list-table::",
                "   :header-rows: 1",
                "   :widths: 18 10 10 18 18 18 18",
                "",
                "   * - Název elementu",
                "     - Min. počet",
                "     - Max. počet",
                "     - Typ",
                "     - Mapování hodnoty",
                "     - Mapování popisu",
                "     - Poznámka",
            ]
        )

        if rows:
            for row in rows:
                rst_lines.extend(
                    [
                        f"   * - ``{row['name']}``",
                        f"     - ``{row['min']}``",
                        f"     - ``{row['max']}``",
                        f"     - ``{row['type']}``",
                        f"     - ``{row['value_map']}``" if row["value_map"] else "     - ",
                        f"     - ``{row['description_map']}``" if row["description_map"] else "     - ",
                        f"     - {row['note']}" if row["note"] else "     - ",
                    ]
                )
        else:
            rst_lines.extend(
                [
                    "   * - (bez elementů)",
                    "     - ",
                    "     - ",
                    "     - ",
                    "     - ",
                    "     - ",
                    "     - ",
                ]
            )

        rst_lines.append("")

    if generic_type_names:
        rst_lines.extend(
            [
                "Generické typy",
                "---------------",
                "",
            ]
        )
        for name in generic_type_names:
            rst_lines.append(f"- ``{name}``")
        rst_lines.append("")

    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        new_content = "\n".join(rst_lines)
        if check_content_changed(new_content, output_file):
            changes_detected = True
            print("    ⚠ Export structure documentation needs update")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("    ✓ Export structure documentation generated")
        return True
    except Exception as exc:
        print(f"    ✗ Error writing export structure documentation: {exc}")
        return False


def has_meaningful_code(source_file: Path) -> bool:
    """Zkontroluje, zda soubor Python obsahuje smysluplný kód (nejen komentáře).

    :param source_file: Cesta k souboru.
    :return: rue, pokud soubor obsahuje smysluplný kód, False v opačném případě.
    """
    try:
        with open(source_file, "r", encoding="utf-8") as f:
            source_code = f.read()

        # Pokusí se soubor naparsovat.
        tree = ast.parse(source_code)

        # Ověří, zda existují smysluplné uzly (třídy, funkce, importy apod.).
        has_code = False
        for node in ast.walk(tree):
            # Ověří přítomnost smysluplného příkazu.
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)):
                has_code = True
                break

        return has_code
    except Exception as e:
        print(f"  ⚠ Warning: Could not parse {source_file}: {e}")
        return False


def extract_docstrings(source_file: Path) -> Tuple[Optional[str], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Extrahuje docstrings z modulu Python pomocí AST parsování.

    :param source_file: Cesta ke zdrojovému souboru.
    :return: tuple: (docstring modulu nebo None, třídy, funkce); třídy a funkce jsou seznamy slovníků.
    """
    with open(source_file, "r", encoding="utf-8") as f:
        source_code = f.read()

    tree = ast.parse(source_code)
    module_doc = ast.get_docstring(tree, clean=False)

    classes = []
    functions = []

    # Iteruje jen přes uzly nejvyšší úrovně (ne přes vnořené třídy typu Meta).
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            docstring = ast.get_docstring(node) or "Popis není k dispozici."
            methods = []

            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_doc = ast.get_docstring(item) or ""
                    methods.append({"name": item.name, "docstring": method_doc, "lineno": item.lineno})

            classes.append({"name": node.name, "docstring": docstring, "methods": methods, "lineno": node.lineno})

        elif isinstance(node, ast.FunctionDef):
            # Pouze funkce nejvyšší úrovně (ne metody).
            docstring = ast.get_docstring(node) or "Popis není k dispozici."
            # Získá signaturu funkce.
            args = [arg.arg for arg in node.args.args]
            functions.append({"name": node.name, "docstring": docstring, "args": args, "lineno": node.lineno})

    return module_doc, classes, functions


def _looks_like_sphinx_fieldlist(docstring: str) -> bool:
    """Vrátí True, pokud text vypadá jako Sphinx info pole (:param:, :return: atd.)."""
    return bool(
        re.search(r"^\s*:(?:param|type|return|returns|raises|raise|yield|yields|rtype)\b", docstring, re.I | re.M)
    )


# Řádky začínající Sphinx info polem — po ast.get_docstring() mohou mít zbytečné odsazení
# (např. „:return:“ vnořené pod „:param:“), což dříve vedlo k cyklickým změnám v generovaném RST.
_RST_INFO_FIELD_LINE = re.compile(
    r"^\s*:(?:param|type|return|returns|raises|raise|yield|yields|rtype)\b",
    re.I,
)


def _indent_docstring_lines(docstring: str, indent: str) -> List[str]:
    """Přidá ``indent`` k neprázdným řádkům; prázdné řádky ponechá prázdné."""
    out: List[str] = []
    for line in docstring.splitlines():
        if line.strip():
            if _RST_INFO_FIELD_LINE.match(line):
                line = line.lstrip()
            out.append(f"{indent}{line}")
        else:
            out.append("")
    return out


def format_docstring_for_rst(docstring: str, indent: str = "") -> List[str]:
    """Formátuje docstring pro výstup RST v režimu explicit.

    Docstringy se Sphinx poli (:param:, :return:, …) se předají beze změny obsahu (jen odsazení).
    Google sekce (Args:, Returns:, …) se převedou na stejná Sphinx info pole.

    :param docstring: Docstring, který se má formátovat
    :param indent: Prefix odsazení pro každý řádek.
    :return: Seznam formátovaných řádků RST.
    """
    if not docstring:
        return []

    if _looks_like_sphinx_fieldlist(docstring):
        return _indent_docstring_lines(docstring, indent)

    lines = docstring.split("\n")
    result = []
    in_args_section = False
    args_variant = ""
    in_returns_like = False
    returns_variant = ""
    in_status_codes_section = False
    in_process_section = False
    in_custom_section = False
    in_other_section = False

    field_cont = indent + "   "

    # Sekce převáděné na Sphinx info pole: :param / :ivar (+ volitelně :type).
    args_like_sections = {"Args:", "Attributes:", "Response Data Keys:", "URL Parameters:"}
    # Sekce převáděné na :return / :rtype, :raises resp. :yields.
    returns_like_sections = {"Returns:", "Raises:", "Yields:"}
    # Klíčová slova sekcí, která formátují položky jako seznamy se zpětnými apostrofy kolem kódů.
    status_codes_sections = {"Response Status Codes:"}
    # Klíčová slova sekcí, která formátují položky jako číslované seznamy (kroky procesu).
    process_sections = {"Process Description:"}
    # Klíčová slova sekcí, která pouze předávají text.
    other_sections = {"Examples:", "Note:", "Notes:"}

    all_section_keywords = (
        args_like_sections | returns_like_sections | status_codes_sections | process_sections | other_sections
    )

    # Translation of section names to Czech
    section_translations = {
        "Args": "Argumenty",
        "Attributes": "Atributy",
        "Response Data Keys": "Klíče odpovědi",
        "URL Parameters": "URL parametry",
        "Returns": "Návratová hodnota",
        "Raises": "Výjimky",
        "Yields": "Generuje",
        "Response Status Codes": "Stavové kódy odpovědi",
        "Process Description": "Popis procesu",
        "Examples": "Příklady",
        "Note": "Poznámka",
        "Notes": "Poznámky",
    }

    def is_section_keyword(text: str) -> bool:
        """Ověří, zda text odpovídá klíčovému slovu sekce.

        :param text: Parametr ``text`` vstupuje do návratové hodnoty.
        :return: Vrací hodnotu typu ``bool`` podle vyhodnocení podmínek.
        """
        return text in all_section_keywords

    def is_custom_section(text: str, line_index: int) -> bool:
        """Ověří, zda text vypadá jako vlastní hlavička sekce (končí dvojtečkou a má obsah níže).

        :param text: Parametr ``text`` pracuje se s atributy ``endswith``, ovlivňuje větvení podmínek.
        :param line_index: Parametr ``line_index`` ovlivňuje větvení podmínek.
        :return: Vrací hodnotu typu ``bool`` podle vyhodnocení podmínek.
        """
        if not text.endswith(":"):
            return False
        # Nesmí to být známá sekce.
        if text in all_section_keywords:
            return False
        # Ověří, zda existuje další řádek a je odsazený (značí obsah sekce).
        if line_index + 1 < len(lines):
            next_line = lines[line_index + 1]
            if next_line.startswith("    ") or next_line.startswith("\t"):
                return True
        return False

    def translate_section(section_name: str) -> str:
        """Překládá název sekce do češtiny.

        :param section_name: Parametr ``section_name`` pracuje se s atributy ``rstrip``.
        :return: Vrací hodnotu typu ``str`` (výsledek volání ``get()``).
        """
        name_without_colon = section_name.rstrip(":")
        return section_translations.get(name_without_colon, name_without_colon)

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Ověří, zda vstupujeme do nové sekce.
        if is_section_keyword(stripped):
            in_args_section = stripped in args_like_sections
            args_variant = stripped if in_args_section else ""
            in_returns_like = stripped in returns_like_sections
            returns_variant = stripped if in_returns_like else ""
            in_status_codes_section = stripped in status_codes_sections
            in_process_section = stripped in process_sections
            in_custom_section = False
            in_other_section = stripped in other_sections

            use_translated_header = bool(in_status_codes_section or in_process_section or in_other_section)
            if use_translated_header:
                translated_name = translate_section(stripped)
                result.append("")
                result.append(f"{indent}**{translated_name}:**")
                result.append("")
            elif in_args_section or in_returns_like:
                if result and result[-1].strip():
                    result.append("")
            i += 1
            continue

        # Ověří, zda vstupujeme do vlastní sekce (např. „Rozdíly oproti NewFileUploadView:“).
        # Vlastní sekce detekuje jen tehdy, když už nejsme uvnitř známé sekce.
        in_any_section = (
            in_args_section or in_returns_like or in_status_codes_section or in_process_section or in_custom_section
        )
        if not in_any_section and is_custom_section(stripped, i):
            in_args_section = False
            args_variant = ""
            in_returns_like = False
            returns_variant = ""
            in_status_codes_section = False
            in_process_section = False
            in_custom_section = True
            in_other_section = False

            # Název sekce použije beze změny (u vlastních sekcí není třeba překlad).
            section_name = stripped.rstrip(":")
            result.append("")
            result.append(f"{indent}**{section_name}:**")
            result.append("")
            i += 1
            continue

        # Zpracuje sekce typu Args – převod na Sphinx :param / :ivar (+ :type).
        if in_args_section and stripped:
            # Ověří, zda jde o řádek argumentu (název (typ): popis).
            # nebo formát (name: description)
            # Podporuje: name, *args, **kwargs
            arg_match = re.match(r"^(\*{0,2}\w+)\s*(?:\(([^)]+)\))?\s*:\s*(.*)$", stripped)
            if arg_match:
                arg_name = arg_match.group(1)
                arg_type = arg_match.group(2)
                arg_desc = arg_match.group(3)
                field = ":ivar" if args_variant == "Attributes:" else ":param"

                result.append(f"{indent}{field} {arg_name}: {arg_desc}")
                if arg_type:
                    result.append(f"{indent}:type {arg_name}: {arg_type}")

                # Ověří navazující řádky (více odsazené než argument).
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()
                    # Pokud je další řádek prázdný nebo jde o novou sekci, ukončí zpracování.
                    if not next_stripped or is_section_keyword(next_stripped):
                        break
                    # Ověří, zda jde o pokračování (v originálu začíná mezerou).
                    if next_line.startswith("    ") or next_line.startswith("\t"):
                        # Ověří, zda jde o nový argument (podporuje *args, **kwargs).
                        if re.match(r"^\s+\*{0,2}\w+\s*(?:\([^)]+\))?\s*:", next_line):
                            break
                        result.append(f"{field_cont}{next_stripped}")
                    else:
                        break
                    i += 1
                continue
            elif not stripped:
                in_args_section = False
                args_variant = ""

        # Zpracuje sekci Response Status Codes – formátuje ji jako seznam se zpětnými apostrofy kolem kódů.
        if in_status_codes_section and stripped:
            # Ověří, zda jde o řádek stavového kódu (kód: popis).
            status_match = re.match(r"^(\d{3})\s*:\s*(.*)$", stripped)
            if status_match:
                status_code = status_match.group(1)
                status_desc = status_match.group(2)
                result.append(f"{indent}- ``{status_code}``: {status_desc}")

                # Ověří navazující řádky.
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()
                    if not next_stripped or is_section_keyword(next_stripped):
                        break
                    if next_line.startswith("    ") or next_line.startswith("\t"):
                        # Ověří, zda jde o nový stavový kód.
                        if re.match(r"^\s+\d{3}\s*:", next_line):
                            break
                        result.append(f"{indent}  {next_stripped}")
                    else:
                        break
                    i += 1
                continue
            elif not stripped:
                in_status_codes_section = False

        # Handle Process Description section - format as numbered list
        if in_process_section and stripped:
            # Ověří, zda jde o číslovaný krok (např. „1. Popis kroku“).
            step_match = re.match(r"^(\d+)\.\s+(.*)$", stripped)
            if step_match:
                step_num = step_match.group(1)
                step_desc = step_match.group(2)
                result.append(f"{indent}{step_num}. {step_desc}")

                # Ověří navazující řádky.
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()
                    if not next_stripped or is_section_keyword(next_stripped):
                        break
                    if next_line.startswith("    ") or next_line.startswith("\t"):
                        # Ověří, zda jde o nový číslovaný krok.
                        if re.match(r"^\s+\d+\.\s+", next_line):
                            break
                        result.append(f"{indent}   {next_stripped}")
                    else:
                        break
                    i += 1
                continue
            elif not stripped:
                in_process_section = False

        # Zpracuje vlastní sekce – formátuje odrážky a číslované seznamy.
        if in_custom_section and stripped:
            # Ověří, zda jde o odrážku (začíná znakem -).
            bullet_match = re.match(r"^-\s+(.*)$", stripped)
            # Ověří, zda jde o číslovanou položku (např. „1. popis“).
            number_match = re.match(r"^(\d+)\.\s+(.*)$", stripped)

            if bullet_match:
                bullet_desc = bullet_match.group(1)
                result.append(f"{indent}- {bullet_desc}")

                # Ověří navazující řádky.
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()
                    if not next_stripped or is_section_keyword(next_stripped) or is_custom_section(next_stripped, i):
                        break
                    if next_line.startswith("    ") or next_line.startswith("\t"):
                        # Ověří, zda jde o novou odrážku nebo číslovanou položku.
                        if re.match(r"^\s+-\s+", next_line) or re.match(r"^\s+\d+\.\s+", next_line):
                            break
                        result.append(f"{indent}  {next_stripped}")
                    else:
                        break
                    i += 1
                continue
            elif number_match:
                num = number_match.group(1)
                num_desc = number_match.group(2)
                result.append(f"{indent}{num}. {num_desc}")

                # Ověří navazující řádky.
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()
                    if not next_stripped or is_section_keyword(next_stripped) or is_custom_section(next_stripped, i):
                        break
                    if next_line.startswith("    ") or next_line.startswith("\t"):
                        # Ověří, zda jde o novou odrážku nebo číslovanou položku.
                        if re.match(r"^\s+-\s+", next_line) or re.match(r"^\s+\d+\.\s+", next_line):
                            break
                        result.append(f"{indent}   {next_stripped}")
                    else:
                        break
                    i += 1
                continue
            elif not stripped:
                in_custom_section = False

        # Returns / Raises / Yields → Sphinx :return, :raises, :yields
        if in_returns_like:
            if not stripped:
                in_returns_like = False
                returns_variant = ""
            else:
                # Ověří, zda to odpovídá formátu typ: popis.
                # Supports: Type, Type[inner], Type | Type2, Optional[Type], etc.
                ret_match = re.match(r"^([\w\[\], |]+)\s*:\s*(.*)$", stripped)
                if ret_match:
                    ret_type = ret_match.group(1).strip()
                    ret_desc = ret_match.group(2)
                    if returns_variant == "Returns:":
                        result.append(f"{indent}:return: {ret_desc}")
                        result.append(f"{indent}:rtype: {ret_type}")
                    elif returns_variant == "Raises:":
                        result.append(f"{indent}:raises {ret_type}: {ret_desc}")
                    elif returns_variant == "Yields:":
                        body = f"*{ret_type}*: {ret_desc}" if ret_desc else f"``{ret_type}``"
                        result.append(f"{indent}:yields: {body}")

                    # Ověří navazující řádky.
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        next_stripped = next_line.strip()
                        if not next_stripped or is_section_keyword(next_stripped):
                            break
                        if next_line.startswith("    ") or next_line.startswith("\t"):
                            # Ověří, zda jde o novou položku typu.
                            if re.match(r"^\s+[\w\[\], |]+\s*:", next_line):
                                break
                            result.append(f"{field_cont}{next_stripped}")
                        else:
                            break
                        i += 1
                    continue
                if returns_variant == "Returns:":
                    result.append(f"{indent}:return: {stripped}")
                elif returns_variant == "Raises:":
                    result.append(f"{indent}{stripped}")
                elif returns_variant == "Yields:":
                    result.append(f"{indent}:yields: {stripped}")
                i += 1
                continue

        # Handle other sections or regular text
        if in_other_section and stripped:
            result.append(f"{indent}{stripped}")
        elif (
            not in_args_section
            and not in_returns_like
            and not in_status_codes_section
            and not in_process_section
            and not in_custom_section
        ):
            result.append(f"{indent}{stripped}" if stripped else "")

        i += 1

    return result


def generate_rst_explicit(source_file: Path, module_name: str, module_title: str, module_description: str) -> str:
    """Vygeneruje soubor RST s explicitním obsahem docstringu.

    :param source_file: Cesta k zdrojovému souboru.
    :param module_name: Plně kvalifikovaný název modulu.
    :param module_title: Název souboru RST.
    :param module_description: Popis modulu.
    :return: Vygenerovaný obsah RST.
    """
    module_doc, classes, functions = extract_docstrings(source_file)

    rst_lines = [module_title, "=" * len(module_title), "", module_description, ""]

    if module_doc and module_doc.strip():
        overview = "Přehled modulu"
        rst_lines.extend([overview, "-" * len(overview), ""])
        rst_lines.extend(format_docstring_for_rst(module_doc.strip(), ""))
        rst_lines.append("")

    if classes:
        rst_lines.extend(["Třídy", "------", ""])

        for cls in classes:
            rst_lines.append(f".. py:class:: {cls['name']}")
            rst_lines.append("")
            # Naformátuje docstring třídy.
            formatted_class_doc = format_docstring_for_rst(cls["docstring"], "   ")
            rst_lines.extend(formatted_class_doc)
            rst_lines.append("")

            if cls["methods"]:
                rst_lines.append("   **Metody:**")
                rst_lines.append("")
                for method in cls["methods"]:
                    rst_lines.append(f"   .. py:method:: {method['name']}()")
                    rst_lines.append("")
                    if method["docstring"]:
                        formatted_method_doc = format_docstring_for_rst(method["docstring"], "      ")
                        rst_lines.extend(formatted_method_doc)
                        rst_lines.append("")
            rst_lines.append("")

    if functions:
        rst_lines.append("Funkce")
        rst_lines.append("------")
        rst_lines.append("")

        for func in functions:
            args_str = ", ".join(func["args"])
            rst_lines.append(f".. py:function:: {func['name']}({args_str})")
            rst_lines.append("")
            formatted_func_doc = format_docstring_for_rst(func["docstring"], "   ")
            rst_lines.extend(formatted_func_doc)
            rst_lines.append("")

    return "\n".join(rst_lines)


def generate_rst_autodoc(module_name: str, module_title: str, module_description: str) -> str:
    """Vygeneruje soubor RST pomocí direktiv Sphinx autodoc.

    :param module_name: Plně kvalifikovaný název modulu.
    :param module_title: Název souboru RST`.
    :param module_description: HPopis modulu.
    :return: Vygenerovaný obsah RST.
    """
    return f"""{module_title}
{"=" * len(module_title)}

{module_description}

.. automodule:: {module_name}
    :members:
    :undoc-members:
    :show-inheritance:
    :member-order: bysource
"""


def get_module_title_and_description(module_dir_name: str, filename: str) -> Tuple[str, str]:
    """Předá příslušný název a popis souboru modulu.

    :param module_dir_name: Název adresáře modulu (např. ``adb``, ``core``).
    :param filename: Název souboru Python (např. ``models.py``).
    :return: tuple: (title, description)
    """
    file_info = FILE_TYPE_INFO.get(
        filename, {"suffix": filename.replace(".py", ""), "description": f'Modul {filename.replace(".py", "")}.'}
    )

    # Použije název modulu s velkým počátečním písmenem do titulku.
    module_display = module_dir_name.upper()

    title = f"{module_display} {file_info['suffix']}"
    description = file_info["description"]

    return title, description


def generate_rst_for_file(source_file: Path, module_dir_name: str, output_dir: Path, mode: str = "autodoc") -> bool:
    """Vygeneruje dokumentaci RST pro jeden soubor Python.

    :param source_file: Cesta ke zdrojovému souboru Python.
    :param module_dir_name: Název adresáře modulu.
    :param output_dir: Výstupní adresář pro soubory RST.
    :param mode: Režim generování (``autodoc`` nebo ``explicit``).
    :return: True v případě úspěchu, False v opačném případě.
    """
    global changes_detected
    filename = source_file.name
    module_name = f"{module_dir_name}.{source_file.stem}"
    output_file = output_dir / f"{source_file.stem}.rst"

    # Get module info
    module_title, module_description = get_module_title_and_description(module_dir_name, filename)

    try:
        if mode == "explicit":
            rst_content = generate_rst_explicit(source_file, module_name, module_title, module_description)
        else:
            rst_content = generate_rst_autodoc(module_name, module_title, module_description)

        if check_content_changed(rst_content, output_file):
            changes_detected = True

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rst_content)

        print(f"    ✓ {output_file.name}")
        return True

    except Exception as e:
        print(f"    ✗ Error generating RST for {filename}: {e}")

        traceback.print_exc()
        return False


def generate_index_rst(module_dir_name: str, generated_files: List[str], output_dir: Path) -> bool:
    """Vygeneruje soubor index.rst s toctree všech vygenerovaných modulů.

    :param module_dir_name: Název adresáře modulu.
    :param generated_files: Seznam vygenerovaných názvů souborů Python.
    :param output_dir: Výstupní adresář.
    :return: True v případě úspěchu, False v opačném případě
    """
    global changes_detected
    index_file = output_dir / "index.rst"

    # Sort files in a logical order: models, forms, views, signals, admin, others
    order = [
        "models.py",
        "forms.py",
        "views.py",
        "signals.py",
        "admin.py",
        "managers.py",
        "serializers.py",
        "permissions.py",
        "filters.py",
        "widgets.py",
    ]
    sorted_files = []

    # Add files in preferred order
    for preferred in order:
        if preferred in generated_files:
            sorted_files.append(preferred)

    # Add any remaining files
    for f in sorted(generated_files):
        if f not in sorted_files:
            sorted_files.append(f)

    # Vytvoří položky toctree (bez přípony .py)
    toctree_entries = [f.replace(".py", "") for f in sorted_files]

    # Module display name
    module_display = module_dir_name.upper()

    index_content = f"""{module_display}
{"=" * len(module_display)}

Dokumentace modulu {module_dir_name}.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

"""

    # Add each entry
    for entry in toctree_entries:
        index_content += f"   {entry}\n"

    # Zapíše indexový soubor.
    try:
        if check_content_changed(index_content, index_file):
            changes_detected = True
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(index_content)
        print("    ✓ index.rst")
        return True
    except Exception as e:
        print(f"    ✗ Error updating index.rst: {e}")
        return False


def process_module(module_dir_name: str, mode: str = "autodoc") -> bool:
    """Zpracuje jeden adresář modulu.

    :param module_dir_name: Název adresáře modulu.
    :param mode: Režim generování (``autodoc`` nebo ``explicit``).
    :return: True, pokud byly vygenerovány nějaké soubory.
    """
    source_dir = webclient_dir / module_dir_name
    output_dir = output_base_dir / module_dir_name

    # Ověří, zda existuje zdrojový adresář.
    if not source_dir.exists() or not source_dir.is_dir():
        print(f"  ⊝ Skipping {module_dir_name}: source directory not found")
        return False

    # Vytvoří výstupní adresář, pokud neexistuje.
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  Processing module: {module_dir_name}")
    print(f"  Source: {source_dir}")
    print(f"  Output: {output_dir}")

    generated_files = []
    skipped_files = []

    # Získá všechny Python soubory v adresáři modulu.
    py_files = sorted(source_dir.glob("*.py"))

    if not py_files:
        print("    ⊝ No Python files found")
        return False

    for source_file in py_files:
        filename = source_file.name

        # Skip certain files
        if filename in SKIP_FILES:
            skipped_files.append(filename)
            continue

        # Ověří, zda soubor obsahuje smysluplný kód.
        if not has_meaningful_code(source_file):
            skipped_files.append(filename)
            continue

        # Generate RST
        if generate_rst_for_file(source_file, module_dir_name, output_dir, mode):
            generated_files.append(filename)

    # Generate index.rst
    if generated_files:
        generate_index_rst(module_dir_name, generated_files, output_dir)

    print(f"    Generated: {len(generated_files)}, Skipped: {len(skipped_files)}")

    return len(generated_files) > 0


def get_all_modules() -> List[str]:
    """Získá všechny adresáře modulů Django z webového klienta.

    :return: Seznam názvů adresářů modulů.
    """
    modules = []
    for item in sorted(webclient_dir.iterdir()):
        if item.is_dir() and item.name not in SKIP_DIRS and not item.name.startswith("."):
            # Ověří, zda to vypadá jako Django aplikace (má `__init__.py` nebo Python soubory).
            if (item / "__init__.py").exists() or list(item.glob("*.py")):
                modules.append(item.name)
    return modules


def generate_all_modules(mode: str = "autodoc", specific_module: Optional[str] = None) -> bool:
    """Vygeneruje soubory RST pro všechny moduly nebo konkrétní modul.

    :param mode: Režim generování (``autodoc`` nebo ``explicit``).
    :param specific_module: Konkrétní modul, který se má zpracovat, nebo None pro všechny.
    :return: True, pokud byla vygenerována nějaká dokumentace.
    """
    print("Generating documentation for webclient modules")
    print(f"Mode: {mode}")
    print(f"Output base directory: {output_base_dir}")
    print("=" * 60)

    if specific_module:
        modules = [specific_module]
        print(f"Processing specific module: {specific_module}")
    else:
        modules = get_all_modules()
        print(f"Found {len(modules)} modules to process")

    total_generated = 0
    successful_modules = []
    failed_modules = []

    for module_name in modules:
        try:
            if process_module(module_name, mode):
                successful_modules.append(module_name)
                total_generated += 1
        except Exception as e:
            print(f"  ✗ Error processing module {module_name}: {e}")
            failed_modules.append(module_name)

    print("\n" + "=" * 60)
    print("\nSummary:")
    print(f"  Modules processed successfully: {len(successful_modules)}")
    if failed_modules:
        print(f"  Modules with errors: {len(failed_modules)}")
        for m in failed_modules:
            print(f"    - {m}")

    if successful_modules:
        print("\n  Successfully processed modules:")
        for m in successful_modules:
            print(f"    - {m}")

    return total_generated > 0


def generate_rst_for_docs_script(source_file: Path, output_dir: Path, mode: str = "autodoc") -> bool:
    """Vygeneruje dokumentaci RST pro jeden Python skript v adresáři docs/.

    :param source_file: Cesta ke zdrojovému souboru Python v docs/.
    :param output_dir: Výstupní adresář pro soubory RST.
    :param mode: Režim generování (``autodoc`` nebo ``explicit``).
    :return: True v případě úspěchu, False v opačném případě.
    """
    global changes_detected
    module_name = f"docs.{source_file.stem}"
    output_file = output_dir / f"{source_file.stem}.rst"
    module_title = f"Skript {source_file.stem}"
    module_description = f"Dokumentace skriptu ``docs/{source_file.name}``."

    try:
        if mode == "explicit":
            rst_content = generate_rst_explicit(source_file, module_name, module_title, module_description)
        else:
            rst_content = generate_rst_autodoc(module_name, module_title, module_description)

        if check_content_changed(rst_content, output_file):
            changes_detected = True

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rst_content)

        print(f"    ✓ {output_file.name}")
        return True

    except Exception as e:
        print(f"    ✗ Error generating RST for docs script {source_file.name}: {e}")
        import traceback

        traceback.print_exc()
        return False


def generate_docs_scripts_index_rst(generated_files: List[str], output_dir: Path) -> bool:
    """Vygeneruje index.rst pro dokumentační skripty v docs/.

    :param generated_files: Seznam vygenerovaných názvů souborů Python.
    :param output_dir: Výstupní adresář.
    :return: True v případě úspěchu, False v opačném případě.
    """
    global changes_detected
    index_file = output_dir / "index.rst"
    toctree_entries = [f.replace(".py", "") for f in sorted(generated_files)]

    index_content = """Dokumentační skripty
====================

Tato sekce obsahuje technickou dokumentaci Python skriptů v adresáři ``docs/``.

.. toctree::
   :maxdepth: 2
   :caption: Obsah:

"""

    for entry in toctree_entries:
        index_content += f"   {entry}\n"

    try:
        if check_content_changed(index_content, index_file):
            changes_detected = True
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(index_content)
        print("    ✓ index.rst")
        return True
    except Exception as e:
        print(f"    ✗ Error updating docs scripts index.rst: {e}")
        return False


def generate_docs_scripts_docs(mode: str = "autodoc") -> bool:
    """Vygeneruje RST dokumentaci pro všechny ``*.py`` skripty v ``docs/``.

    :param mode: Režim generování (``autodoc`` nebo ``explicit``).
    :return: True, pokud byl vygenerován alespoň jeden soubor.
    """
    output_dir = docs_scripts_output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\nGenerating documentation for docs/*.py scripts")
    print(f"Mode: {mode}")
    print(f"Source: {docs_dir}")
    print(f"Output: {output_dir}")

    generated_files = []
    skipped_files = []

    py_files = sorted(docs_dir.glob("*.py"))
    if not py_files:
        print("  ⊝ No Python scripts found in docs/")
        return False

    for source_file in py_files:
        if source_file.name == "__init__.py":
            skipped_files.append(source_file.name)
            continue

        if not has_meaningful_code(source_file):
            skipped_files.append(source_file.name)
            continue

        if generate_rst_for_docs_script(source_file, output_dir, mode):
            generated_files.append(source_file.name)

    if generated_files:
        generate_docs_scripts_index_rst(generated_files, output_dir)

    print(f"  Generated: {len(generated_files)}, Skipped: {len(skipped_files)}")
    return len(generated_files) > 0


def get_script_language(script_name: str) -> str:
    """Vrátí jazyk pro zvýraznění syntaxe podle přípony souboru.

    :param script_name: Parametr ``script_name`` předává se do volání ``Path()``.
    :return: Vrací hodnotu typu ``str`` (str).
    """
    suffix = Path(script_name).suffix.lower()
    if suffix == ".sh":
        return "bash"
    if suffix == ".py":
        return "python"
    if suffix == ".ini":
        return "ini"
    if suffix == ".txt":
        return "text"
    return "text"


def get_script_doc_name(script_name: str) -> str:
    """Vrátí bezpečný název RST souboru pro skript.

    :param script_name: Parametr ``script_name`` předává se do volání ``sub()``, vstupuje do návratové hodnoty.
    :return: Vrací hodnotu typu ``str`` (výsledek volání ``lower()``).
    """
    return re.sub(r"[^a-zA-Z0-9]+", "_", script_name).strip("_").lower()


def generate_rst_for_project_script(source_file: Path, output_dir: Path) -> bool:
    """Vygeneruje RST dokumentaci pro jeden soubor v adresáři scripts/.

    :param source_file: Parametr ``source_file`` předává se do volání ``get_script_doc_name()``, ``get_script_language()``, pracuje se s atributy ``name``.
    :param output_dir: Parametr ``output_dir`` slouží jako vstup pro logiku funkce ``generate_rst_for_project_script``.
    :return: Vrací hodnotu typu ``bool`` podle vyhodnocení podmínek.
    """
    global changes_detected
    doc_name = get_script_doc_name(source_file.name)
    output_file = output_dir / f"{doc_name}.rst"
    language = get_script_language(source_file.name)

    if source_file.suffix.lower() == ".py":
        module_title = f"Skript {source_file.name}"
        module_description = f"Automaticky generovaná dokumentace skriptu ``scripts/{source_file.name}``."
        module_name = f"scripts.{source_file.stem}"
        try:
            body = generate_rst_explicit(source_file, module_name, module_title, module_description)
            src_href = f"../../../../scripts/{source_file.name}"
            code_heading = "Zdrojový kód"
            rst_content = (
                body.rstrip()
                + "\n\n"
                + f"{code_heading}\n"
                + "-" * len(code_heading)
                + "\n\n"
                + f".. literalinclude:: {src_href}\n"
                + f"   :language: {language}\n"
                + "   :linenos:\n"
            )
        except Exception as e:
            print(f"    ⚠ Falling back to literalinclude-only for {source_file.name}: {e}")
            rst_content = f"""Skript {source_file.name}
================{'=' * len(source_file.name)}

Automaticky generovaná dokumentace skriptu ``scripts/{source_file.name}``.

.. literalinclude:: ../../../../scripts/{source_file.name}
   :language: {language}
   :linenos:
"""
    else:
        rst_content = f"""Skript {source_file.name}
================{'=' * len(source_file.name)}

Automaticky generovaná dokumentace skriptu ``scripts/{source_file.name}``.

.. literalinclude:: ../../../../scripts/{source_file.name}
   :language: {language}
   :linenos:
"""

    try:
        if check_content_changed(rst_content, output_file):
            changes_detected = True

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rst_content)

        print(f"    ✓ {output_file.name}")
        return True
    except Exception as e:
        print(f"    ✗ Error generating RST for project script {source_file.name}: {e}")
        return False


def generate_project_scripts_index_rst(toctree_entries: List[str], output_dir: Path) -> bool:
    """Vygeneruje index.rst pro skripty v adresáři scripts/.

    :param toctree_entries: Parametr ``toctree_entries`` předává se do volání ``sorted()``.
    :param output_dir: Parametr ``output_dir`` slouží jako vstup pro logiku funkce ``generate_project_scripts_index_rst``.
    :return: Vrací hodnotu typu ``bool`` podle vyhodnocení podmínek.
    """
    global changes_detected
    index_file = output_dir / "index.rst"

    index_content = """Projektové skripty
=================

Tato sekce obsahuje automaticky generovanou dokumentaci souborů v adresáři ``scripts/``.

.. toctree::
   :maxdepth: 2
   :caption: Obsah:

"""

    for entry in sorted(toctree_entries):
        index_content += f"   {entry}\n"

    try:
        if check_content_changed(index_content, index_file):
            changes_detected = True
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(index_content)
        print("    ✓ index.rst")
        return True
    except Exception as e:
        print(f"    ✗ Error updating project scripts index.rst: {e}")
        return False


def generate_project_scripts_docs() -> bool:
    """Vygeneruje RST dokumentaci pro soubory v ``scripts/``.

    :return: Vrací hodnotu typu ``bool`` podle vyhodnocení podmínek.
    """
    output_dir = project_scripts_output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\nGenerating documentation for scripts/* files")
    print(f"Source: {project_scripts_dir}")
    print(f"Output: {output_dir}")

    if not project_scripts_dir.exists() or not project_scripts_dir.is_dir():
        print("  ⊝ scripts/ directory not found")
        return False

    generated_entries = []
    script_files = sorted([f for f in project_scripts_dir.iterdir() if f.is_file() and not f.name.startswith(".")])
    if not script_files:
        print("  ⊝ No files found in scripts/")
        return False

    for source_file in script_files:
        doc_name = get_script_doc_name(source_file.name)
        if generate_rst_for_project_script(source_file, output_dir):
            generated_entries.append(doc_name)

    if generated_entries:
        generate_project_scripts_index_rst(generated_entries, output_dir)

    print(f"  Generated: {len(generated_entries)}, Skipped: {len(script_files) - len(generated_entries)}")
    return len(generated_entries) > 0


def build_docs() -> bool:
    """Vytvoří HTML dokumentaci pomocí Sphinx.

    :return: True, pokud se sestavení podařilo, False v opačném případě.
    """
    print("\nBuilding HTML documentation...")
    try:
        result = subprocess.run(["make", "html"], cwd=docs_dir, capture_output=True, text=True)

        if result.returncode == 0:
            print("✓ Documentation built successfully!")
            html_dir = Path(docs_dir) / "build/html/04_django_aplikace/04_02_moduly"
            if html_dir.exists():
                print(f"✓ Generated HTML files in: {html_dir}")
            return True
        else:
            print(f"✗ Build failed with return code {result.returncode}")
            if result.stderr:
                print(f"Error output: {result.stderr[-1000:]}")  # Last 1000 chars
            return False

    except FileNotFoundError:
        print("✗ sphinx-build not found. Please activate the virtual environment:")
        print("  source .venv/bin/activate")
        return False
    except Exception as e:
        print(f"✗ Error building documentation: {e}")
        return False


def _fetch_dockerhub_odkaz(image: str) -> str:
    """Načte zdrojovou URL pro Docker Hub image (best-effort, bez autentizace).

    :param image: Základní název image, např. ``grafana/grafana-enterprise``.
    :type image: str
    :return: Řetězec zdrojové URL, nebo prázdný řetězec při chybě nebo nepodporovaném registru.
    :rtype: str
    """
    if image.startswith(("gcr.io/", "docker.elastic.co/", "ghcr.io/")):
        return ""

    if "/" not in image:
        image = f"library/{image}"

    parts = image.split("/")
    if len(parts) != 2:
        return ""

    namespace, name = parts
    url = f"https://hub.docker.com/v2/repositories/{namespace}/{name}/"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.load(resp)

        if data.get("source"):
            return data["source"]

        desc = data.get("full_description", "")
        m = re.search(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", desc)
        return m.group(0) if m else ""

    except (urllib.error.URLError, json.JSONDecodeError):
        return ""


class DockerImageScanner:
    """Prohledává soubory projektu a sbírá tagy Docker image.

    Prochází všechny soubory ``docker-compose*.yml`` v kořenovém adresáři projektu
    a soubor ``Dockerfile-DB``. Výsledkem je slovník mapující základní název image
    (bez tagu) na jeho plný tag.

    :param project_root: Kořenový adresář projektu.
    :type project_root: Path
    """

    def __init__(self, project_root: Path):
        """Inicializuje scanner s kořenovým adresářem projektu.

        :param project_root: Kořenový adresář projektu.
        :type project_root: Path
        """
        self.project_root = project_root

    def collect_versions(self) -> Dict[str, str]:
        """Shromáždí verze image ze souborů docker-compose a Dockerfile-DB.

        Prochází nejprve compose soubory, poté ``Dockerfile-DB``. Pro každý
        základní název image je uložen první nalezený plný tag (produkční soubory
        mají přednost díky pořadí vrácenému metodou :meth:`_ordered_compose_files`).

        :return: Slovník ``{základní název image: plný tag}``.
        :rtype: Dict[str, str]
        """
        versions: Dict[str, str] = {}

        for image in self._compose_images():
            base = self._base_image(image)
            versions.setdefault(base, image)

        for image in self._dockerfile_images():
            base = self._base_image(image)
            versions.setdefault(base, image)

        return versions

    def _compose_images(self) -> List[str]:
        """Extrahuje plné tagy image ze souborů docker-compose.

        Přeskočí proměnné (``${...}``) a testovací image
        (``docker.io/library/test_*``).

        :return: Seznam plných tagů image (např. ``redis:8.4.0``).
        :rtype: List[str]
        """
        images: List[str] = []
        image_re = re.compile(r"^\s+image:\s*(.+)")

        for compose_file in self._ordered_compose_files():
            try:
                text = compose_file.read_text(encoding="utf-8")
            except OSError:
                continue

            for line in text.splitlines():
                m = image_re.match(line)
                if not m:
                    continue

                full_tag = m.group(1).strip()

                if full_tag.startswith("${") or full_tag.startswith("docker.io/library/test_"):
                    continue

                images.append(full_tag)

        return images

    def _dockerfile_images(self) -> List[str]:
        """Extrahuje image z direktiv FROM v souboru Dockerfile-DB.

        Pokud soubor ``Dockerfile-DB`` neexistuje, vrátí prázdný seznam.

        :return: Seznam plných tagů image z direktiv FROM.
        :rtype: List[str]
        """
        dockerfile_db = self.project_root / "Dockerfile-DB"
        if not dockerfile_db.exists():
            return []

        from_re = re.compile(r"^FROM\s+(\S+)")
        images: List[str] = []

        for line in dockerfile_db.read_text(encoding="utf-8").splitlines():
            m = from_re.match(line)
            if m:
                images.append(m.group(1).strip())

        return images

    def _ordered_compose_files(self) -> List[Path]:
        """Vrátí seznam souborů docker-compose seřazených podle priority.

        Produkční soubory (``docker-compose.yml``, ``docker-compose-proxy.yml``)
        jsou řazeny jako první, aby jejich verze image měly přednost při volání
        :meth:`collect_versions`.

        :return: Seřazený seznam cest k souborům docker-compose.
        :rtype: List[Path]
        """
        priority_files = ["docker-compose.yml", "docker-compose-proxy.yml"]

        all_compose = sorted(self.project_root.glob("docker-compose*.yml"))
        ordered: List[Path] = []

        for name in priority_files:
            p = self.project_root / name
            if p in all_compose:
                ordered.append(p)

        for p in all_compose:
            if p not in ordered:
                ordered.append(p)

        return ordered

    @staticmethod
    def _base_image(full_tag: str) -> str:
        """Vrátí základní název image bez tagu.

        :param full_tag: Plný tag image (např. ``redis:8.4.0``).
        :type full_tag: str
        :return: Název image bez tagu (např. ``redis``).
        :rtype: str
        """
        return full_tag.rsplit(":", 1)[0] if ":" in full_tag else full_tag


def _parse_compose_versions(project_root: Path) -> Dict[str, str]:
    """Parsuje všechny soubory docker-compose*.yml a Dockerfile-DB v project_root
    a hledá direktivy image:. Vrátí slovník mapující základní název image na plný tag.

    Priorita: docker-compose.yml / docker-compose-proxy.yml (produkce) jako první,
    poté ostatní soubory.

    :param project_root: Kořenový adresář projektu.
    :type project_root: Path
    :return: Slovník ``{základní název image: plný tag}``.
    :rtype: Dict[str, str]
    """
    return DockerImageScanner(project_root).collect_versions()


def _check_missing_meta_images(
    versions: Dict[str, str],
    images_meta: List[Dict[str, str]],
) -> List[str]:
    """Vrátí seznam základních názvů image nalezených v docker-compose / Dockerfile-DB,
    které nejsou pokryty žádným záznamem v docker_images_meta.yaml.

    Proměnné reference na image (``${...}``) v compose souborech jsou již filtrovány
    třídou DockerImageScanner, takže jsou kontrolovány pouze konkrétní názvy image.

    :param versions: Slovník ``{základní název image: plný tag}`` z docker-compose souborů.
    :type versions: Dict[str, str]
    :param images_meta: Seznam metadatových záznamů z docker_images_meta.yaml.
    :type images_meta: List[Dict[str, str]]
    :return: Seřazený seznam základních názvů image chybějících v metadatech.
    :rtype: List[str]
    """
    meta_keys = {e.get("image", "") for e in images_meta}
    return sorted(image for image in versions if image not in meta_keys)


ODKAZ_CACHE_FILE = docs_dir / "docker_images_odkaz_cache.yaml"


def _load_odkaz_cache() -> Dict[str, str]:
    """Načte mezipaměť odkazů DockerHub ze souboru ``docker_images_odkaz_cache.yaml``.

    Pokud soubor neexistuje, vrátí prázdný slovník.

    :return: Slovník ``{název image: URL}`` s dříve uloženými odkazy.
    :rtype: Dict[str, str]
    """
    if ODKAZ_CACHE_FILE.exists():
        return yaml.safe_load(ODKAZ_CACHE_FILE.read_text(encoding="utf-8")) or {}
    return {}


def _save_odkaz_cache(cache: Dict[str, str]) -> None:
    """Uloží mezipaměť odkazů DockerHub do souboru ``docker_images_odkaz_cache.yaml``.

    :param cache: Slovník ``{název image: URL}`` k uložení.
    :type cache: Dict[str, str]
    """
    ODKAZ_CACHE_FILE.write_text(yaml.dump(cache, allow_unicode=True), encoding="utf-8")


def _fetch_missing_links(image_keys: List[str], cache: Dict[str, str]) -> Dict[str, str]:
    """Načte DockerHub odkazy pouze pro image, které ještě nejsou v mezipaměti, paralelně.

    :param image_keys: Seznam základních názvů image, pro které se mají načíst odkazy.
    :type image_keys: List[str]
    :param cache: Existující mezipaměť odkazů ``{název image: URL}``.
    :type cache: Dict[str, str]
    :return: Aktualizovaná mezipaměť včetně nově načtených odkazů.
    :rtype: Dict[str, str]
    """
    missing = [img for img in image_keys if img not in cache and not img.startswith("${")]

    if not missing:
        return cache

    print(f"  Fetching DockerHub links for {len(missing)} new images...")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_fetch_dockerhub_odkaz, img): img for img in missing}
        for future in as_completed(futures):
            img = futures[future]
            try:
                cache[img] = future.result()
            except Exception as e:
                print(f"  ⚠ Failed to fetch link for {img}: {e}")
                cache[img] = ""

    return cache


def generate_docker_images_rst() -> bool:
    """Vygeneruje dokumentaci Docker image.

    :return: True v případě úspěchu, False v opačném případě.
    :rtype: bool
    """
    global changes_detected

    output_file = docs_dir / "source/12_zavislosti/docker_images.rst"
    meta_file = docs_dir / "docker_images_meta.yaml"

    print("\n  Generating Docker images documentation")
    print(f"  Output: {output_file}")

    if not meta_file.exists():
        print(f"  ⊝ {meta_file} not found, skipping")
        return False

    meta_data = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    images_meta: List[Dict[str, str]] = meta_data.get("images", [])

    if not images_meta:
        print("  ⊝ No image entries found in docker_images_meta.yaml")
        return False

    versions = _parse_compose_versions(project_root)

    # Ověří, zda jsou všechny image z docker-compose souborů zahrnuty v metadatech.
    missing = _check_missing_meta_images(versions, images_meta)
    if missing:
        print("  ✗ Následující Docker image chybí v docker_images_meta.yaml:")
        for img in missing:
            print(f"      - {img}")
        print("  Přidejte chybějící záznamy do docs/docker_images_meta.yaml.")
        global changes_detected
        changes_detected = True
        return False

    # Load cache, fetch only what's missing (in parallel), save back
    hub_cache = _load_odkaz_cache()
    image_keys = [e.get("image", "") for e in images_meta if not e.get("odkaz")]
    hub_cache = _fetch_missing_links(image_keys, hub_cache)
    _save_odkaz_cache(hub_cache)

    content_lines: List[str] = []
    content_lines += _build_section_header(
        "Vlastní image",
        "Tyto image jsou vyvíjeny vývojovým týmem aplikace a jsou specifické pro provoz AMCR.",
    )
    for entry in images_meta:
        if entry.get("image", "").startswith("${"):
            content_lines += _build_image_block(entry, versions, hub_cache)

    content_lines += _build_section_header(
        "Generické image",
        "Tyto image jsou standardní open-source image používané pro provoz podpůrných služeb.",
    )
    for entry in images_meta:
        if not entry.get("image", "").startswith("${"):
            content_lines += _build_image_block(entry, versions, hub_cache)

    banner_lines = [
        "..",
        "   Tento soubor je automaticky generován. Neupravujte ručně.",
        "   Změny tagů: ``docker-compose*.yml``, ``Dockerfile-DB``; popis a licence:",
        "   ``docs/docker_images_meta.yaml``. Obnovení: ``python docs/generate_module_docs.py``",
        "   nebo ``python docs/licenses/convert_to_rst.py``.",
        "",
    ]
    new_content = "\n".join(banner_lines) + "Docker images\n=============\n\n" + "\n".join(content_lines) + "\n"

    if check_content_changed(new_content, output_file):
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(new_content, encoding="utf-8")
        print(f"  ✓ Updated {output_file.name} with {len(images_meta)} Docker images")
        changes_detected = True
    else:
        print(f"  ⊝ {output_file.name} unchanged")

    return True


def _build_section_header(title: str, description: str) -> List[str]:
    """Vytvoří záhlaví sekce RST.

    :param title: Název sekce.
    :type title: str
    :param description: Popis sekce.
    :type description: str
    :return: Seznam řádků RST záhlaví sekce.
    :rtype: List[str]
    """
    return [
        title,
        "-" * len(title),
        "",
        description,
        "",
    ]


def _build_image_block(
    entry: Dict[str, str],
    versions: Dict[str, str],
    hub_cache: Dict[str, str],
) -> List[str]:
    """Sestaví RST blok pro jeden Docker image.

    :param entry: Metadatový záznam image z docker_images_meta.yaml.
    :type entry: Dict[str, str]
    :param versions: Slovník ``{základní název image: plný tag}`` z docker-compose souborů.
    :type versions: Dict[str, str]
    :param hub_cache: Mezipaměť odkazů DockerHub ``{název image: URL}``.
    :type hub_cache: Dict[str, str]
    :return: Seznam řádků RST bloku pro daný image.
    :rtype: List[str]
    """

    image_key = entry.get("image", "")
    display_name = entry.get("display_name", image_key)

    verze = entry.get("verze_override", "")
    if not verze:
        full_tag = versions.get(image_key, "")
        verze = _extract_version(full_tag)

    licence = entry.get("licence", "")
    odkaz_raw = entry.get("odkaz") or hub_cache.get(image_key, "")
    if isinstance(odkaz_raw, list):
        odkaz = ", ".join(odkaz_raw)
    else:
        odkaz = odkaz_raw
    popis = entry.get("popis", "")
    base_image = entry.get("base_image")

    lines = [
        display_name,
        "~" * len(display_name),
        "",
        f"- **Verze:** {verze}" if verze else "- **Verze:**",
        f"- **Licence:** {licence}" if licence else "- **Licence:**",
        f"- **Odkaz:** {odkaz}" if odkaz else "- **Odkaz:**",
    ]

    if base_image:
        base_name = base_image.get("image", "")
        base_licence = base_image.get("licence", "")
        base_odkaz = base_image.get("odkaz", "")
        lines += [
            "",
            f"- **Bázový image:** {base_name}" if base_name else "- **Bázový image:**",
            f"- **Licence bázového image:** {base_licence}" if base_licence else "- **Licence bázového image:**",
            f"- **Odkaz na bázový image:** {base_odkaz}" if base_odkaz else "- **Odkaz na bázový image:**",
        ]

    if popis:
        lines += ["", popis]

    lines.append("")
    return lines


def _extract_version(full_tag: str) -> str:
    """Extrahuje verzi tagu z plného tagu Docker image.

    :param full_tag: Plný tag image (např. ``redis:8.4.0``).
    :type full_tag: str
    :return: Verze tagu (např. ``8.4.0``), nebo ``latest`` pokud tag není přítomen.
    :rtype: str
    """
    if not full_tag:
        return ""
    return full_tag.rsplit(":", 1)[-1] if ":" in full_tag else "latest"


BEGIN_MARKER = ".. BEGIN GENERATED NODEJS LIBRARIES"
END_MARKER = ".. END GENERATED NODEJS LIBRARIES"


@dataclass
class JsLibrary:
    """Datová třída reprezentující jednu Node.js knihovnu.

    :param name: Název balíčku (např. ``bootstrap``).
    :type name: str
    :param version: Verze balíčku (např. ``5.3.8``).
    :type version: str
    :param license: Identifikátor licence (např. ``MIT``).
    :type license: str
    :param homepage: URL domovské stránky nebo repozitáře knihovny.
    :type homepage: str
    """

    name: str
    version: str
    license: str
    homepage: str


def load_json(path: Path) -> dict:
    """Načte a vrátí obsah JSON souboru.

    :param path: Cesta k JSON souboru.
    :type path: Path
    :return: Deserializovaný obsah JSON souboru.
    :rtype: dict
    """
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def normalize_repo_url(url: str) -> str:
    """Normalizuje URL repozitáře pro zobrazení v dokumentaci.

    Odstraní prefix ``git+``, převede ``git://host/…`` na ``https://host/…``
    (prohlížeče ``git://`` nepodporují spolehlivě) a ořízne příponu ``.git``.

    :param url: Surová URL repozitáře (např. ``git+https://github.com/foo/bar.git``).
    :type url: str
    :return: Normalizovaná URL (např. ``https://github.com/foo/bar``).
    :rtype: str
    """
    if not url:
        return url
    if url.startswith("git+"):
        url = url[4:]
    if url.startswith("git://"):
        url = "https://" + url[6:]
    if url.endswith(".git"):
        url = url[:-4]
    return url


def npm_package_page_url(package_name: str) -> str:
    """Vrátí kanonickou URL stránky balíčku na https://www.npmjs.com/.

    Používá se jako záložní odkaz, když v ``node_modules`` není k dispozici
    ``homepage`` ani ``repository`` (např. při běhu generátoru bez ``npm install``).
    Scoped balíčky (``@scope/name``) se kódují s ``%2F`` místo lomítka v cestě.

    :param package_name: Název balíčku z ``package.json`` (např. ``leaflet`` nebo ``@types/node``).
    :type package_name: str
    :return: URL ve tvaru ``https://www.npmjs.com/package/...``.
    :rtype: str
    """
    encoded = quote(package_name, safe="@")
    return f"https://www.npmjs.com/package/{encoded}"


def parse_preserved_js_library_links(rst_content: str) -> Dict[str, str]:
    """Z existujícího RST vytáhne mapu ``název balíčku → odkaz`` z generovaného bloku.

    Parsuje řádky ``list-table`` mezi značkami ``.. BEGIN GENERATED NODEJS LIBRARIES``
    a ``.. END GENERATED NODEJS LIBRARIES``. Řádek záhlaví tabulky
    (``Název knihovny``) se přeskočí. Slouží k zachování odkazů při běhu bez
    ``node_modules`` (např. CI), aby se nepřepisovaly platné URL hodnotami
    z :func:`npm_package_page_url`.

    Očekává stejný čtyřřádkový tvar řádků tabulky jako :func:`build_rst_table`;
    ruční zalamování buněk může parsování rozhodit.

    :param rst_content: Obsah souboru ``javascript_knihovny.rst`` (nebo ekvivalent).
    :type rst_content: str
    :return: Slovník ``{název balíčku: URL}`` pro neprázdné odkazy.
    :rtype: Dict[str, str]
    """
    if BEGIN_MARKER not in rst_content or END_MARKER not in rst_content:
        return {}

    start = rst_content.index(BEGIN_MARKER)
    end = rst_content.index(END_MARKER)
    section = rst_content[start:end]
    preserved: Dict[str, str] = {}
    lines = section.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("   * - "):
            name = line[7:].strip()
            if (
                i + 3 < len(lines)
                and lines[i + 1].startswith("     - ")
                and lines[i + 2].startswith("     - ")
                and lines[i + 3].startswith("     - ")
            ):
                url = lines[i + 3][len("     - ") :].strip()
                if name != "Název knihovny" and url:
                    preserved[name] = url
                i += 4
                continue
        i += 1
    return preserved


def load_dependencies(package_json: dict) -> Dict[str, str]:
    """Načte produkční závislosti ze slovníku ``package.json``.

    :param package_json: Deserializovaný obsah souboru ``package.json``.
    :type package_json: dict
    :return: Slovník ``{název balíčku: verze}`` z pole ``dependencies``.
    :rtype: Dict[str, str]
    """
    return package_json.get("dependencies", {})


def load_lock_licenses(lock_file: Path) -> Dict[str, str]:
    """Načte licence balíčků ze souboru ``package-lock.json``.

    Prochází sekci ``packages`` lock souboru a extrahuje pole ``license``
    pro každý záznam pod klíčem ``node_modules/<název>``.

    :param lock_file: Cesta k souboru ``package-lock.json``.
    :type lock_file: Path
    :return: Slovník ``{název balíčku: licence}``.
    :rtype: Dict[str, str]
    """
    licenses: Dict[str, str] = {}

    if not lock_file.exists():
        return licenses

    lock = load_json(lock_file)

    for key, info in lock.get("packages", {}).items():
        if key.startswith("node_modules/"):
            name = key[len("node_modules/") :]
            license_val = info.get("license")
            if isinstance(license_val, dict):
                license_val = (license_val.get("type") or "").strip()

            if license_val:
                licenses[name] = license_val

    return licenses


def read_node_module_metadata(project_root: Path, name: str) -> tuple[str, str]:
    """Načte licenci a URL domovské stránky balíčku z adresáře ``node_modules``.

    Pokud soubor ``package.json`` daného balíčku neexistuje, vrátí dvojici
    prázdných řetězců. Pole ``license`` může být řetězec nebo objekt s klíčem
    ``type`` (starší formát npm). URL repozitáře je normalizována pomocí
    :func:`normalize_repo_url`.

    :param project_root: Kořenový adresář projektu obsahující ``node_modules``.
    :type project_root: Path
    :param name: Název balíčku (např. ``bootstrap``).
    :type name: str
    :return: Dvojice ``(licence, homepage_url)``.
    :rtype: tuple[str, str]
    """

    nm_pkg = project_root / "node_modules" / name / "package.json"

    if not nm_pkg.exists():
        return "", ""

    data = load_json(nm_pkg)

    license_val = data.get("license", "")
    if isinstance(license_val, dict):
        license_val = (license_val.get("type") or "").strip()

    homepage = data.get("homepage", "")

    if not homepage:
        repo = data.get("repository", {})
        if isinstance(repo, dict):
            homepage = repo.get("url", "")
        elif isinstance(repo, str):
            homepage = repo

    homepage = normalize_repo_url(homepage)

    return license_val, homepage


def collect_libraries(
    project_root: Path,
    dependencies: Dict[str, str],
    lock_licenses: Dict[str, str],
    preserved_links: Optional[Dict[str, str]] = None,
) -> List[JsLibrary]:
    """Sestaví seznam Node.js knihoven obohacený o licence a URL.

    Pro každou závislost z ``dependencies`` nejprve hledá licenci v ``lock_licenses``
    (ze souboru ``package-lock.json``), a pokud ji nenajde, čte ji přímo
    ze souboru ``package.json`` v ``node_modules``. Homepage se čte z
    ``node_modules``; chybí-li, použije se dříve uložený odkaz z ``preserved_links``
    (poslední generovaný blok v RST — stabilizuje CI bez ``npm ci``), jinak URL
    stránky balíčku na npm (:func:`npm_package_page_url`). Nový balíček bez
    uloženého odkazu tedy dostane vždy npm URL. Záznamy jsou seřazeny abecedně
    podle názvu balíčku.

    :param project_root: Kořenový adresář projektu obsahující ``node_modules``.
    :type project_root: Path
    :param dependencies: Slovník ``{název balíčku: verze}`` z ``package.json``.
    :type dependencies: Dict[str, str]
    :param lock_licenses: Slovník ``{název balíčku: licence}`` z ``package-lock.json``.
    :type lock_licenses: Dict[str, str]
    :param preserved_links: Volitelně odkazy z existujícího generovaného bloku RST.
    :type preserved_links: Optional[Dict[str, str]]
    :return: Seřazený seznam objektů :class:`JsLibrary`.
    :rtype: List[JsLibrary]
    """

    rows: List[JsLibrary] = []

    for name, version in sorted(dependencies.items()):

        license_val = lock_licenses.get(name, "")
        homepage = ""

        nm_license, nm_homepage = read_node_module_metadata(project_root, name)

        if not license_val:
            license_val = nm_license

        homepage = nm_homepage
        if not homepage and preserved_links:
            homepage = preserved_links.get(name, "")
        if not homepage:
            homepage = npm_package_page_url(name)

        rows.append(JsLibrary(name, version, license_val, homepage))

    return rows


def build_rst_table(rows: List[JsLibrary]) -> str:
    """Sestaví RST blok s tabulkou Node.js knihoven.

    Vygeneruje sekci dokumentace ve formátu ``list-table`` ohraničenou
    značkami ``BEGIN_MARKER`` a ``END_MARKER``, která obsahuje sloupce
    Název knihovny, Verze, Licence a Odkaz.

    :param rows: Seznam záznamů Node.js knihoven k zobrazení v tabulce.
    :type rows: List[JsLibrary]
    :return: Řetězec s RST obsahem tabulky včetně ohraničujících značek.
    :rtype: str
    """

    lines = [
        BEGIN_MARKER,
        "",
        "Knihovny instalované pomocí Node.js",
        "------------------------------------",
        "",
        ".. list-table:: Knihovny v jazyce Javascript instalované pomocí Node.js",
        "   :widths: 25 25 25 25",
        "   :header-rows: 1",
        "",
        "   * - Název knihovny",
        "     - Verze",
        "     - Licence",
        "     - Odkaz",
    ]

    for row in rows:
        lines.append(f"   * - {row.name}")
        lines.append(f"     - {row.version}")
        lines.append(f"     - {row.license}")
        lines.append(f"     - {row.homepage}")

    lines.append("")
    lines.append(END_MARKER)

    return "\n".join(lines) + "\n"


def insert_generated_block(content: str, block: str) -> str:
    """Vloží nebo nahradí generovaný blok mezi značkami v RST obsahu.

    :param content: Původní text souboru (např. ``.rst``).
    :param block: Nový generovaný úsek včetně značek začátku a konce.
    :return: Obsah po vložení bloku, jinak ``block`` předřazený před ``content``.
    """
    if BEGIN_MARKER in content and END_MARKER in content:
        start = content.index(BEGIN_MARKER)
        end = content.index(END_MARKER) + len(END_MARKER)
        # Consume the trailing newline after END_MARKER to prevent
        # accumulation on each run
        if end < len(content) and content[end] == "\n":
            end += 1
        return content[:start] + block + content[end:]
    return block + "\n" + content


def generate_js_libraries_rst() -> bool:
    """Vygeneruje tabulku Node.js JavaScript knihoven pro javascript_knihovny.rst.

    Licences berou z ``package-lock.json``; odkazy nejprve z ``node_modules``,
    při jejich absenci z existujícího generovaného bloku v souboru, jinak z
    :func:`npm_package_page_url`. Pro aktualizaci odkazů z metadat balíčků
    (homepage, repository) je potřeba mít nainstalované závislosti (``npm ci``).

    :return: True v případě úspěchu, False v opačném případě.
    :rtype: bool
    """

    global changes_detected

    output_file = docs_dir / "source/12_zavislosti/javascript_knihovny.rst"
    package_json_file = project_root / "package.json"
    package_lock_file = project_root / "package-lock.json"

    print("\n  Generating Node.js JavaScript libraries documentation")
    print(f"  Output: {output_file}")

    if not package_json_file.exists():
        print(f"  ⊝ {package_json_file} not found, skipping")
        return False

    package_json = load_json(package_json_file)

    dependencies = load_dependencies(package_json)

    if not dependencies:
        print("  ⊝ No dependencies found in package.json")
        return False

    lock_licenses = load_lock_licenses(package_lock_file)

    existing_content = ""
    if output_file.exists():
        existing_content = output_file.read_text(encoding="utf-8")

    preserved_links = parse_preserved_js_library_links(existing_content)
    rows = collect_libraries(project_root, dependencies, lock_licenses, preserved_links)

    table_block = build_rst_table(rows)

    new_content = insert_generated_block(existing_content, table_block)

    if check_content_changed(new_content, output_file):

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(new_content, encoding="utf-8")

        print(f"  ✓ Updated {output_file.name} with {len(rows)} Node.js packages")

        changes_detected = True

    else:
        print(f"  ⊝ {output_file.name} unchanged")

    return True


def main() -> None:
    """Hlavní funkce pro spuštění generátoru dokumentace."""
    parser = argparse.ArgumentParser(description="Generate Sphinx documentation for Django modules in webclient/")
    parser.add_argument("--build", action="store_true", help="Also build the HTML documentation")
    parser.add_argument(
        "--mode", choices=["autodoc", "explicit"], default="explicit", help="Generation mode (default: explicit)"
    )
    parser.add_argument(
        "--module",
        type=str,
        help="Specific module to process (e.g., 'adb', 'core'). If not specified, processes all modules.",
    )
    parser.add_argument(
        "--docker-images-only",
        action="store_true",
        help="Only regenerate docs/source/12_zavislosti/docker_images.rst (compose + docker_images_meta.yaml).",
    )
    args = parser.parse_args()

    if args.docker_images_only:
        generate_docker_images_rst()
        if changes_detected:
            print("\n⚠ Documentation changes detected!")
            print("The documentation files have been updated.")
            print("Please review and commit these changes.")
            sys.exit(1)
        return

    # Generate RST files
    if not generate_all_modules(mode=args.mode, specific_module=args.module):
        print("\n✗ No documentation files were generated")
        sys.exit(1)

    # Generate RST files for docs/*.py scripts
    generate_docs_scripts_docs(mode=args.mode)

    # Generate RST files for scripts/* files
    generate_project_scripts_docs()

    # Generate URL routing documentation
    generate_url_routing_rst()

    # Generate signals documentation
    generate_signals_rst()

    # Generate permissions documentation
    generate_permissions_rst()

    # Generate management commands documentation
    generate_management_commands_rst()

    # Generate export structure documentation
    generate_export_structure_rst()

    # Generate Docker images documentation
    generate_docker_images_rst()

    # Generate Node.js JavaScript libraries documentation
    generate_js_libraries_rst()

    # Build documentation if requested
    if args.build:
        if not build_docs():
            sys.exit(1)
    else:
        print("\nNext steps:")
        print("1. To build the HTML documentation, run:")
        print("   source .venv/bin/activate")
        print("   cd docs && make html")
        print("\n2. Or run this script with --build flag:")
        print("   cd docs && source ../.venv/bin/activate && python3 generate_module_docs.py --build")
        print("\n3. To view the generated documentation:")
        print("   open build/html/04_django_aplikace/04_02_moduly/")

    # Ukončí se s kódem 1, pokud byly detekovány změny.
    if changes_detected:
        print("\n⚠ Documentation changes detected!")
        print("The documentation files have been updated.")
        print("Please review and commit these changes.")
        sys.exit(1)


if __name__ == "__main__":
    main()
