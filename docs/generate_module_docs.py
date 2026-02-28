#!/usr/bin/env python3
"""
Script to generate Sphinx documentation for all Django modules in webclient/
and save them to docs/source/04_django_aplikace/04_02_moduly/

This script extracts docstrings from modules and generates detailed
reStructuredText documentation for each module directory.

Usage:
    python3 generate_module_docs.py [--build] [--mode MODE] [--module MODULE]

    Options:
        --build         Also build the HTML documentation (requires sphinx-build)
        --mode MODE     Generation mode: 'autodoc' (default) or 'explicit'
                       - autodoc: Uses Sphinx autodoc directives
                       - explicit: Writes docstrings directly to RST
        --module MODULE Specific module to process (e.g., 'adb', 'core')
                       If not specified, processes all modules

    Example with virtual environment:
        source .venv/bin/activate && python3 generate_module_docs.py --build
        source .venv/bin/activate && python3 generate_module_docs.py --module core
"""

import argparse
import ast
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Define paths
docs_dir = Path(__file__).parent
project_root = docs_dir.parent
webclient_dir = project_root / "webclient"
output_base_dir = docs_dir / "source/04_django_aplikace/04_02_moduly"
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
    """Check if content differs from existing file.

    :param content: Hodnota parametru ``content``.
    :param output_file: Hodnota parametru ``output_file``.
    :return: Návratová hodnota funkce.
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
    """Extract URL patterns from a urls.py file.

    :param urls_file: Hodnota parametru ``urls_file``.
    :return: Návratová hodnota funkce.
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
    """Parse a path() or re_path() call to extract URL pattern info.

    :param node: Hodnota parametru ``node``.
    :return: Návratová hodnota funkce.
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
    """Generate URL routing documentation for all modules.

    :return: Návratová hodnota funkce.
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
    """Extract signal receivers from a signals.py file.

    :param signals_file: Hodnota parametru ``signals_file``.
    :return: Návratová hodnota funkce.
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
    """Parse a @receiver() decorator to extract signal information.

    :param decorator: Hodnota parametru ``decorator``.
    :param function_name: Hodnota parametru ``function_name``.
    :return: Návratová hodnota funkce.
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
    """Generate signals documentation for all modules.

    :return: Návratová hodnota funkce.
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
    """Extract action choices from Permissions class in models.py.

    :param models_file: Hodnota parametru ``models_file``.
    :return: Návratová hodnota funkce.
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
    """Generate permissions documentation.

    :return: Návratová hodnota funkce.
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

    :param value: Hodnota parametru ``value``.
    :return: Návratová hodnota funkce.
    """
    cleaned = value.strip()
    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1].strip()
    if cleaned.startswith("{") and cleaned.endswith("}"):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def parse_comment_values(comment_text: str) -> Tuple[str, str]:
    """Vrátí mapované hodnoty získané z inline komentáře XSD.

    :param comment_text: Hodnota parametru ``comment_text``.
    :return: Návratová hodnota funkce.
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

    :param parent: Hodnota parametru ``parent``.
    :param element: Hodnota parametru ``element``.
    :return: Návratová hodnota funkce.
    """
    siblings = list(parent)
    for index, node in enumerate(siblings):
        if node is element and index + 1 < len(siblings):
            next_node = siblings[index + 1]
            if next_node.tag is ET.Comment:
                return (next_node.text or "").strip()
    return ""


def collect_choice_element_names(choice_element: ET.Element) -> List[str]:
    """Collect names of all xs:element nodes inside a choice block.

    :param choice_element: Hodnota parametru ``choice_element``.
    :return: Návratová hodnota funkce.
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

    :param names: Hodnota parametru ``names``.
    :return: Návratová hodnota funkce.
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

    :param parent: Hodnota parametru ``parent``.
    :param choice_context: Hodnota parametru ``choice_context``.
    :return: Návratová hodnota funkce.
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

    :param complex_type: Hodnota parametru ``complex_type``.
    :return: Návratová hodnota funkce.
    """
    rows: List[Dict[str, str]] = []
    for child in complex_type:
        if child.tag in {f"{XS_NS}sequence", f"{XS_NS}choice"}:
            rows.extend(extract_elements_from_parent(child))
    return rows


def extract_model_mappings(schema_root: ET.Element) -> List[Dict[str, str]]:
    """Načte mapování z volby elementu amcr do řádků Model -> ComplexType.

    :param schema_root: Hodnota parametru ``schema_root``.
    :return: Návratová hodnota funkce.
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
    """Extract version attribute from XSD schema root element.

    :param schema_root: Hodnota parametru ``schema_root``.
    :return: Návratová hodnota funkce.
    """
    return schema_root.attrib.get("version", "neznámá")


def extract_django_command_info(command_file: Path) -> Dict[str, str]:
    """Extract documentation information from a Django management command file.

    :param command_file: Hodnota parametru ``command_file``.
    :return: Návratová hodnota funkce.
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
    """Extract argument definitions from add_arguments method.

    :param add_arguments_node: Hodnota parametru ``add_arguments_node``.
    :return: Návratová hodnota funkce.
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
    """Generate management commands documentation.

    :return: Návratová hodnota funkce.
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

    :return: Návratová hodnota funkce.
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
    """Check if a Python file has meaningful code (not just comments).

    :param source_file: Hodnota parametru ``source_file``.
    :return: Návratová hodnota funkce.
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


def extract_docstrings(source_file: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Extract docstrings from the Python module using AST parsing.

    :param source_file: Hodnota parametru ``source_file``.
    :return: Návratová hodnota funkce.
    """
    with open(source_file, "r", encoding="utf-8") as f:
        source_code = f.read()

    tree = ast.parse(source_code)

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

    return classes, functions


def format_docstring_for_rst(docstring: str, indent: str = "") -> List[str]:
    """Format a Google-style docstring for RST output.

    :param docstring: Hodnota parametru ``docstring``.
    :param indent: Hodnota parametru ``indent``.
    :return: Návratová hodnota funkce.
    """
    if not docstring:
        return []

    lines = docstring.split("\n")
    result = []
    in_args_section = False
    in_returns_section = False
    in_status_codes_section = False
    in_process_section = False
    in_custom_section = False
    in_other_section = False

    # Klíčová slova sekcí, která formátují položky jako seznamy se zpětnými apostrofy kolem názvů.
    args_like_sections = {"Args:", "Attributes:", "Response Data Keys:", "URL Parameters:"}
    # Klíčová slova sekcí, která formátují položky kurzívou.
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
        """Ověří, zda text odpovídá klíčovému slovu sekce."""
        return text in all_section_keywords

    def is_custom_section(text: str, line_index: int) -> bool:
        """Ověří, zda text vypadá jako vlastní hlavička sekce (končí dvojtečkou a má obsah níže)."""
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
        """Translate section name to Czech."""
        name_without_colon = section_name.rstrip(":")
        return section_translations.get(name_without_colon, name_without_colon)

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Ověří, zda vstupujeme do nové sekce.
        if is_section_keyword(stripped):
            in_args_section = stripped in args_like_sections
            in_returns_section = stripped in returns_like_sections
            in_status_codes_section = stripped in status_codes_sections
            in_process_section = stripped in process_sections
            in_custom_section = False
            in_other_section = stripped in other_sections

            translated_name = translate_section(stripped)
            result.append("")
            result.append(f"{indent}**{translated_name}:**")
            result.append("")
            i += 1
            continue

        # Ověří, zda vstupujeme do vlastní sekce (např. „Rozdíly oproti NewFileUploadView:“).
        # Vlastní sekce detekuje jen tehdy, když už nejsme uvnitř známé sekce.
        in_any_section = (
            in_args_section or in_returns_section or in_status_codes_section or in_process_section or in_custom_section
        )
        if not in_any_section and is_custom_section(stripped, i):
            in_args_section = False
            in_returns_section = False
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

        # Zpracuje sekce typu Args – formátuje je jako seznam se zpětnými apostrofy.
        if in_args_section and stripped:
            # Ověří, zda jde o řádek argumentu (název (typ): popis).
            # or (name: description) format
            # Supports: name, *args, **kwargs
            arg_match = re.match(r"^(\*{0,2}\w+)\s*(?:\(([^)]+)\))?\s*:\s*(.*)$", stripped)
            if arg_match:
                arg_name = arg_match.group(1)
                arg_type = arg_match.group(2)
                arg_desc = arg_match.group(3)

                if arg_type:
                    result.append(f"{indent}- ``{arg_name}`` (*{arg_type}*): {arg_desc}")
                else:
                    result.append(f"{indent}- ``{arg_name}``: {arg_desc}")

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
                        result.append(f"{indent}  {next_stripped}")
                    else:
                        break
                    i += 1
                continue
            elif not stripped:
                in_args_section = False

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

        # Handle Returns/Raises section
        if in_returns_section and stripped:
            # Ověří, zda to odpovídá formátu typ: popis.
            # Supports: Type, Type[inner], Type | Type2, Optional[Type], etc.
            ret_match = re.match(r"^([\w\[\], |]+)\s*:\s*(.*)$", stripped)
            if ret_match:
                ret_type = ret_match.group(1).strip()
                ret_desc = ret_match.group(2)
                result.append(f"{indent}*{ret_type}*: {ret_desc}")

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
                        result.append(f"{indent}{next_stripped}")
                    else:
                        break
                    i += 1
                continue
            elif not stripped:
                in_returns_section = False

        # Handle other sections or regular text
        if in_other_section and stripped:
            result.append(f"{indent}{stripped}")
        elif (
            not in_args_section
            and not in_returns_section
            and not in_status_codes_section
            and not in_process_section
            and not in_custom_section
        ):
            result.append(f"{indent}{stripped}" if stripped else "")

        i += 1

    return result


def generate_rst_explicit(source_file: Path, module_name: str, module_title: str, module_description: str) -> str:
    """Generate RST file with explicit docstring content.

    :param source_file: Hodnota parametru ``source_file``.
    :param module_name: Hodnota parametru ``module_name``.
    :param module_title: Hodnota parametru ``module_title``.
    :param module_description: Hodnota parametru ``module_description``.
    :return: Návratová hodnota funkce.
    """
    classes, functions = extract_docstrings(source_file)

    rst_lines = [module_title, "=" * len(module_title), "", module_description, ""]

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
    """Generate RST file with Sphinx autodoc directives.

    :param module_name: Hodnota parametru ``module_name``.
    :param module_title: Hodnota parametru ``module_title``.
    :param module_description: Hodnota parametru ``module_description``.
    :return: Návratová hodnota funkce.
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
    """Get appropriate title and description for a module file.

    :param module_dir_name: Hodnota parametru ``module_dir_name``.
    :param filename: Hodnota parametru ``filename``.
    :return: Návratová hodnota funkce.
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
    """Generate RST documentation for a single Python file.

    :param source_file: Hodnota parametru ``source_file``.
    :param module_dir_name: Hodnota parametru ``module_dir_name``.
    :param output_dir: Hodnota parametru ``output_dir``.
    :param mode: Hodnota parametru ``mode``.
    :return: Návratová hodnota funkce.
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
        import traceback

        traceback.print_exc()
        return False


def generate_index_rst(module_dir_name: str, generated_files: List[str], output_dir: Path) -> bool:
    """Generate index.rst file with toctree of all generated modules.

    :param module_dir_name: Hodnota parametru ``module_dir_name``.
    :param generated_files: Hodnota parametru ``generated_files``.
    :param output_dir: Hodnota parametru ``output_dir``.
    :return: Návratová hodnota funkce.
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
    """Process a single module directory.

    :param module_dir_name: Hodnota parametru ``module_dir_name``.
    :param mode: Hodnota parametru ``mode``.
    :return: Návratová hodnota funkce.
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
    """Get all Django module directories from webclient.

    :return: Návratová hodnota funkce.
    """
    modules = []
    for item in sorted(webclient_dir.iterdir()):
        if item.is_dir() and item.name not in SKIP_DIRS and not item.name.startswith("."):
            # Ověří, zda to vypadá jako Django aplikace (má `__init__.py` nebo Python soubory).
            if (item / "__init__.py").exists() or list(item.glob("*.py")):
                modules.append(item.name)
    return modules


def generate_all_modules(mode: str = "autodoc", specific_module: Optional[str] = None) -> bool:
    """Generate RST files for all modules or a specific module.

    :param mode: Hodnota parametru ``mode``.
    :param specific_module: Hodnota parametru ``specific_module``.
    :return: Návratová hodnota funkce.
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


def build_docs() -> bool:
    """Build the HTML documentation using Sphinx.

    :return: Návratová hodnota funkce.
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
    args = parser.parse_args()

    # Generate RST files
    if not generate_all_modules(mode=args.mode, specific_module=args.module):
        print("\n✗ No documentation files were generated")
        sys.exit(1)

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

    # Vytvoří dokumentaci, pokud je to požadováno.
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
