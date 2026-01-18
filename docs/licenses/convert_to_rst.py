import json
import subprocess

LICENSES_MANUAL_FIXES = {
    "wrapt": "Copyright (c) 2013-2025, Graham Dumpleton",
}


def csv_to_rst_table():
    output = subprocess.run(
        ["pip-licenses", "--format=json", "--with-urls", "--from=mixed", "--with-system"],
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
    print(f"{len(data_to_write)} libraries written to file 'docs/source/12_zavislosti/python_knihovny.rst'.")


csv_to_rst_table()
