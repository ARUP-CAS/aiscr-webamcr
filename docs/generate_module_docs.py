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

# Directories to skip (not Django apps)
SKIP_DIRS = {"static", "templates", "locale", "__pycache__", "services"}

# Track if any files have changed
changes_detected = False

# Common file type descriptions
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
    """
    Check if content differs from existing file.

    Args:
        content (str): New content to compare
        output_file (Path): Path to existing file

    Returns:
        bool: True if content has changed or file doesn't exist
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
    """
    Extract URL patterns from a urls.py file.

    Args:
        urls_file (Path): Path to urls.py file

    Returns:
        tuple: (app_name, list of url_patterns)
            Each url_pattern is a dict with keys: 'pattern', 'view', 'name'
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
    """
    Parse a path() or re_path() call to extract URL pattern info.

    Args:
        node: AST node representing a path() call

    Returns:
        dict: {'pattern': str, 'view': str, 'name': str} or None
    """
    if not isinstance(node, ast.Call):
        return None

    # Check if it's a path() or re_path() call
    if isinstance(node.func, ast.Name) and node.func.id not in ["path", "re_path"]:
        return None

    if len(node.args) < 2:
        return None

    # Extract pattern (first argument)
    pattern = None
    if isinstance(node.args[0], ast.Constant):
        pattern = node.args[0].value

    # Extract view (second argument)
    view = None
    if isinstance(node.args[1], ast.Attribute):
        # e.g., views.zapsat or views.MyView.as_view()
        if isinstance(node.args[1].value, ast.Name):
            view = f"{node.args[1].value.id}.{node.args[1].attr}"
    elif isinstance(node.args[1], ast.Name):
        # e.g., post_upload
        view = node.args[1].id
    elif isinstance(node.args[1], ast.Call):
        # e.g., MyView.as_view()
        if isinstance(node.args[1].func, ast.Attribute):
            if isinstance(node.args[1].func.value, ast.Name):
                view = f"{node.args[1].func.value.id}.as_view()"
            elif isinstance(node.args[1].func.value, ast.Attribute):
                # Nested attribute like views.MyView.as_view()
                if isinstance(node.args[1].func.value.value, ast.Name):
                    view = f"{node.args[1].func.value.value.id}.{node.args[1].func.value.attr}.as_view()"

    # Extract name from keyword arguments
    name = None
    for keyword in node.keywords:
        if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
            name = keyword.value.value

    if pattern is not None:
        return {"pattern": pattern, "view": view or "N/A", "name": name or "N/A"}

    return None


def generate_url_routing_rst() -> bool:
    """
    Generate URL routing documentation for all modules.

    Creates docs/source/04_django_aplikace/04_01_core/url_routing.rst
    with tables of all URL patterns from each module's urls.py

    Returns:
        bool: True if successful, False otherwise
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
            # Skip the main webclient/urls.py (project-level URLs)
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

    # Write the file
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        new_content = "\n".join(rst_lines).rstrip() + "\n"
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
    """
    Extract signal receivers from a signals.py file.

    Args:
        signals_file (Path): Path to signals.py file

    Returns:
        list: List of signal info dicts with keys: 'function', 'signal_type', 'sender', 'weak'
    """
    try:
        with open(signals_file, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        signals = []

        for node in tree.body:
            # Look for functions decorated with @receiver
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        # Check if decorator is receiver()
                        if isinstance(decorator.func, ast.Name) and decorator.func.id == "receiver":
                            signal_info = parse_receiver_decorator(decorator, node.name)
                            if signal_info:
                                signals.append(signal_info)

        return signals

    except Exception as e:
        print(f"  ⚠ Warning: Could not parse {signals_file}: {e}")
        return []


def parse_receiver_decorator(decorator: ast.Call, function_name: str) -> Optional[Dict[str, str]]:
    """
    Parse a @receiver() decorator to extract signal information.

    Args:
        decorator: AST Call node representing @receiver()
        function_name: Name of the decorated function

    Returns:
        dict: {'function': str, 'signal_type': str, 'sender': str, 'weak': str} or None
    """
    if len(decorator.args) == 0:
        return None

    # Extract signal type (first argument)
    signal_type = None
    if isinstance(decorator.args[0], ast.Attribute):
        signal_type = decorator.args[0].attr
    elif isinstance(decorator.args[0], ast.Name):
        signal_type = decorator.args[0].id

    # Extract sender and weak from keyword arguments
    sender = "N/A"
    weak = "True"  # Default value in Django

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
    """
    Generate signals documentation for all modules.

    Creates docs/source/04_django_aplikace/04_01_core/signals.rst
    with tables of all signal receivers from each module's signals.py

    Returns:
        bool: True if successful, False otherwise
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
            # Skip the main webclient module
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

    # Write the file
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        new_content = "\n".join(rst_lines).rstrip() + "\n"
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
    """
    Extract action choices from Permissions class in models.py.

    Args:
        models_file (Path): Path to models.py file

    Returns:
        list: List of action names (e.g., 'adb_smazat', 'vb_smazat')
    """
    try:
        with open(models_file, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        actions = []

        # Find Permissions class
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "Permissions":
                # Find actionChoices nested class
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
    """
    Generate permissions documentation.

    Updates docs/source/04_django_aplikace/04_01_core/permissions.rst
    by appending the list of all defined actions from Permissions.actionChoices
    after the "Uživatelské akce řízené pomocí oprávnění" heading.

    Returns:
        bool: True if successful, False otherwise
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

    # Read existing content if file exists
    existing_content = []
    marker_heading = "Uživatelské akce řízené pomocí oprávnění"
    marker_found = False

    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Find the marker heading and keep everything before it (including the heading and separator)
        for i, line in enumerate(lines):
            existing_content.append(line.rstrip())
            if line.strip() == marker_heading:
                marker_found = True
                # Also include the separator line (dashes) after the heading
                if i + 1 < len(lines) and lines[i + 1].strip().startswith("-"):
                    existing_content.append(lines[i + 1].rstrip())
                break

    # If marker not found, create default structure
    if not marker_found:
        existing_content.extend(
            [
                marker_heading,
                "-" * len(marker_heading),
            ]
        )

    # Build the new content to append
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

    # Combine existing and new content
    final_content = existing_content + new_content

    # Write the file
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        final_text = "\n".join(final_content).rstrip() + "\n"
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
    """Strip wrapping quotes/braces from a comment value."""
    cleaned = value.strip()
    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1].strip()
    if cleaned.startswith("{") and cleaned.endswith("}"):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def parse_comment_values(comment_text: str) -> Tuple[str, str]:
    """Return mapping values parsed from an inline XSD comment."""
    if not comment_text:
        return "", ""

    parts = [clean_comment_value(part) for part in comment_text.split("|")]
    value = parts[0] if parts else ""
    description = parts[1] if len(parts) > 1 else ""

    if value.lower() == "self":
        return "", ""

    return value, description


def get_following_comment(parent: ET.Element, element: ET.Element) -> str:
    """Find the first comment node immediately following the given element."""
    siblings = list(parent)
    for index, node in enumerate(siblings):
        if node is element and index + 1 < len(siblings):
            next_node = siblings[index + 1]
            if next_node.tag is ET.Comment:
                return (next_node.text or "").strip()
    return ""


def collect_choice_element_names(choice_element: ET.Element) -> List[str]:
    """Collect names of all xs:element nodes inside a choice block."""
    names: List[str] = []
    for child in choice_element:
        if child.tag == f"{XS_NS}element":
            names.append(child.attrib.get("name", ""))
        elif child.tag in {f"{XS_NS}sequence", f"{XS_NS}choice"}:
            names.extend(collect_choice_element_names(child))
    return names


def format_choice_note(names: List[str]) -> str:
    """Format a note describing the options inside a choice element."""
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
    """Recursively extract element definitions, noting choice context when present."""
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
    """Extract element rows from a complexType definition."""
    rows: List[Dict[str, str]] = []
    for child in complex_type:
        if child.tag in {f"{XS_NS}sequence", f"{XS_NS}choice"}:
            rows.extend(extract_elements_from_parent(child))
    return rows


def extract_model_mappings(schema_root: ET.Element) -> List[Dict[str, str]]:
    """Read mappings from the amcr element choice into Model -> ComplexType rows."""
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
    """
    Extract version attribute from XSD schema root element.

    Args:
        schema_root (ET.Element): Root element of the XSD schema

    Returns:
        str: Version string (e.g., "2.2") or "neznámá" if not found
    """
    return schema_root.attrib.get("version", "neznámá")


def generate_export_structure_rst() -> bool:
    """Generate docs/source/05_integrace/export_structure.rst from amcr.xsd."""
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

    # Respect the position of the "generic-types" comment to split processing
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
        new_content = "\n".join(rst_lines).rstrip() + "\n"
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
    """
    Check if a Python file has meaningful code (not just comments).

    Args:
        source_file (Path): Path to the Python file

    Returns:
        bool: True if file has meaningful code, False otherwise
    """
    try:
        with open(source_file, "r", encoding="utf-8") as f:
            source_code = f.read()

        # Try to parse the file
        tree = ast.parse(source_code)

        # Check if there are any meaningful nodes (classes, functions, imports, etc.)
        has_code = False
        for node in ast.walk(tree):
            # Check for any meaningful statement
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)):
                has_code = True
                break

        return has_code
    except Exception as e:
        print(f"  ⚠ Warning: Could not parse {source_file}: {e}")
        return False


def extract_docstrings(source_file: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extract docstrings from the Python module using AST parsing.

    Args:
        source_file (Path): Path to the Python source file

    Returns:
        tuple: (classes, functions) where each is a list of dictionaries
    """
    with open(source_file, "r", encoding="utf-8") as f:
        source_code = f.read()

    tree = ast.parse(source_code)

    classes = []
    functions = []

    # Only iterate through top-level nodes (not nested classes like Meta)
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
            # Only top-level functions (not methods)
            docstring = ast.get_docstring(node) or "Popis není k dispozici."
            # Get function signature
            args = [arg.arg for arg in node.args.args]
            functions.append({"name": node.name, "docstring": docstring, "args": args, "lineno": node.lineno})

    return classes, functions


def generate_rst_explicit(source_file: Path, module_name: str, module_title: str, module_description: str) -> str:
    """
    Generate RST file with explicit docstring content.

    Args:
        source_file (Path): Path to the Python source file
        module_name (str): Fully qualified module name
        module_title (str): Title for the RST file
        module_description (str): Description for the module

    Returns:
        str: Generated RST content
    """
    classes, functions = extract_docstrings(source_file)

    rst_lines = [module_title, "=" * len(module_title), "", module_description, ""]

    if classes:
        rst_lines.extend(["Třídy", "------", ""])

        for cls in classes:
            rst_lines.append(f".. py:class:: {cls['name']}")
            rst_lines.append("")
            rst_lines.append(f"   {cls['docstring']}")
            rst_lines.append("")

            if cls["methods"]:
                rst_lines.append("   **Metody:**")
                rst_lines.append("")
                for method in cls["methods"]:
                    if method["name"].startswith("_") and method["name"] != "__init__":
                        continue  # Skip private methods except __init__
                    rst_lines.append(f"   .. py:method:: {method['name']}()")
                    rst_lines.append("")
                    if method["docstring"]:
                        for line in method["docstring"].split("\n"):
                            rst_lines.append(f"      {line}")
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
            for line in func["docstring"].split("\n"):
                rst_lines.append(f"   {line}")
            rst_lines.append("")

    return "\n".join(rst_lines).rstrip() + "\n"


def generate_rst_autodoc(module_name: str, module_title: str, module_description: str) -> str:
    """
    Generate RST file with Sphinx autodoc directives.

    Args:
        module_name (str): Fully qualified module name
        module_title (str): Title for the RST file
        module_description (str): Description for the module

    Returns:
        str: Generated RST content
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
    """
    Get appropriate title and description for a module file.

    Args:
        module_dir_name (str): Name of the module directory (e.g., 'adb', 'core')
        filename (str): Name of the Python file (e.g., 'models.py')

    Returns:
        tuple: (title, description)
    """
    file_info = FILE_TYPE_INFO.get(
        filename, {"suffix": filename.replace(".py", ""), "description": f'Modul {filename.replace(".py", "")}.'}
    )

    # Capitalize module name for title
    module_display = module_dir_name.upper()

    title = f"{module_display} {file_info['suffix']}"
    description = file_info["description"]

    return title, description


def generate_rst_for_file(source_file: Path, module_dir_name: str, output_dir: Path, mode: str = "autodoc") -> bool:
    """
    Generate RST documentation for a single Python file.

    Args:
        source_file (Path): Path to the source Python file
        module_dir_name (str): Name of the module directory
        output_dir (Path): Output directory for RST files
        mode (str): Generation mode ('autodoc' or 'explicit')

    Returns:
        bool: True if successful, False otherwise
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
    """
    Generate index.rst file with toctree of all generated modules.

    Args:
        module_dir_name (str): Name of the module directory
        generated_files (list): List of generated Python filenames
        output_dir (Path): Output directory

    Returns:
        bool: True if successful, False otherwise
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

    # Create toctree entries (without .py extension)
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

    # Write the index file
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
    """
    Process a single module directory.

    Args:
        module_dir_name (str): Name of the module directory
        mode (str): Generation mode

    Returns:
        bool: True if any files were generated
    """
    source_dir = webclient_dir / module_dir_name
    output_dir = output_base_dir / module_dir_name

    # Check if source directory exists
    if not source_dir.exists() or not source_dir.is_dir():
        print(f"  ⊝ Skipping {module_dir_name}: source directory not found")
        return False

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  Processing module: {module_dir_name}")
    print(f"  Source: {source_dir}")
    print(f"  Output: {output_dir}")

    generated_files = []
    skipped_files = []

    # Get all Python files in the module directory
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

        # Check if file has meaningful code
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
    """
    Get all Django module directories from webclient.

    Returns:
        list: List of module directory names
    """
    modules = []
    for item in sorted(webclient_dir.iterdir()):
        if item.is_dir() and item.name not in SKIP_DIRS and not item.name.startswith("."):
            # Check if it looks like a Django app (has __init__.py or Python files)
            if (item / "__init__.py").exists() or list(item.glob("*.py")):
                modules.append(item.name)
    return modules


def generate_all_modules(mode: str = "autodoc", specific_module: Optional[str] = None) -> bool:
    """
    Generate RST files for all modules or a specific module.

    Args:
        mode (str): Generation mode
        specific_module (str): Specific module to process, or None for all

    Returns:
        bool: True if any documentation was generated
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
    """
    Build the HTML documentation using Sphinx.

    Returns:
        bool: True if build succeeded, False otherwise
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
    """Main function to run the documentation generator."""
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

    # Generate export structure documentation
    generate_export_structure_rst()

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

    # Exit with code 1 if changes were detected
    if changes_detected:
        print("\n⚠ Documentation changes detected!")
        print("The documentation files have been updated.")
        print("Please review and commit these changes.")
        sys.exit(1)


if __name__ == "__main__":
    main()
