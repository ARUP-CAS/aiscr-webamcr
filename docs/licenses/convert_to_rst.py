"""Generuje RST dokumentaci závislostí pro Python i Docker image.

- Tabulku Python knihoven z výstupu ``pip-licenses`` zapisuje do
  ``docs/source/12_zavislosti/python_knihovny.rst``.
- Soubor ``docs/source/12_zavislosti/docker_images.rst`` obnoví voláním
  ``docs/generate_module_docs.py --docker-images-only`` (verze z compose a
  ``docs/docker_images_meta.yaml``).
"""

import json
import subprocess
import sys
from pathlib import Path

LICENSES_MANUAL_FIXES = {
    "wrapt": "Copyright (c) 2013-2025, Graham Dumpleton",
}


def csv_to_rst_table():
    """Načte licence knihoven a zapíše je do dokumentace ve formátu RST."""
    output = subprocess.run(
        [sys.executable, "-m", "piplicenses", "--format=json", "--with-urls", "--from=mixed", "--with-system"],
        capture_output=True,
        text=True,
    )
    packages = json.loads(output.stdout)
    data_to_write = []

    for package in packages:
        package_name = package["Name"]
        license_value = LICENSES_MANUAL_FIXES.get(package_name, package["License"])
        row = {
            "Název knihovny": package_name,
            "Verze": package["Version"],
            "Licence": license_value,
            "Odkaz": package.get("URL", ""),
        }
        data_to_write.append(row)

    rest_table_data = ""
    for row_index, row in enumerate(data_to_write):
        for key, value in row.items():
            rest_table_data += f"   * - {value}\n" if key == "Název knihovny" else f"     - {value}\n"  # noqa: E221
    with open("docs/source/knihovny_for_edit.rst", encoding="utf-8") as rst_file:
        content = rst_file.read()
    content = content.replace("@licence_table", rest_table_data)
    with open("docs/source/12_zavislosti/python_knihovny.rst", "w", encoding="utf-8") as rst_file:
        rst_file.write(content)
    print(f"Do souboru 'docs/source/12_zavislosti/python_knihovny.rst' bylo zapsáno {len(data_to_write)} knihoven.")


def main() -> None:
    """Vygeneruje RST pro Python knihovny a Docker image."""
    csv_to_rst_table()
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "docs" / "generate_module_docs.py"),
            "--docker-images-only",
        ],
        cwd=str(repo_root),
        text=True,
    )
    if result.returncode == 1:
        # generate_module_docs.py používá návratový kód 1 jako signál „soubory změněny“ (pre-commit).
        print(
            "Soubor docs/source/12_zavislosti/docker_images.rst byl aktualizován "
            "(generate_module_docs.py skončil kódem 1 — očekávané při změnách).",
        )
    elif result.returncode != 0:
        print(
            f"generate_module_docs.py --docker-images-only selhal s návratovým kódem {result.returncode}.",
            file=sys.stderr,
        )
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
