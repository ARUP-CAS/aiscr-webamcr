"""Propojené CSV recepty, stabilní ZIP a bezpečné doplnění skutečných klíčů."""

from __future__ import annotations

import csv
import io
import re
import zipfile

from .catalog import RECIPES
from .common import namespace


def ident(name, ns, index, refs=None):
    """Složí platný syntetický identifikátor; neodvozuje DB primární klíč."""
    number = int(namespace(ns)) + index
    if number > 999999:
        raise ValueError("Namespace range exhausted")
    project = f"C-{209000000 + number}"
    document = f"C-TX-{209000000 + number}"
    sheet50 = str((refs or {}).get("zm50") or "0001").replace("-", "").zfill(4)
    names = {
        "heslar": f"HES-{number:06}",
        "organizace": f"ORG-{number:06}",
        "osoby": f"OS-{number:06}",
        "uzivatele": f"U-{number:06}",
        "projekty": project,
        "az_akce": project + "A01",
        "az_lokality": f"C-N{number:07}",
        "samostatne_nalezy": project + "-N00001",
        # 9xxxxx is reserved for cadastral precision; ordinary fixtures use the
        # corresponding 8xxxxx range and the actual ZM50 sheet prefix.
        "az_pian": f"P-{sheet50}-{number - 100000:06}",
        "az_dokumentacni_jednotky": project + "A01-D01",
        "az_adb": f"ADB-{(refs or {}).get('sm5', 'PRAH43')}-{number:06}",
        "az_adb_vyskove_body": f"ADB-{(refs or {}).get('sm5', 'PRAH43')}-{number:06}-V0001",
        "dokumenty_lety": f"LET-{number:06}",
        "dokumenty": document,
        "dokumenty_casti": document + "-D001",
        "komponenty": project + "A01-K001",
        "externi_zdroje": f"BIB-{number:09}",
    }
    return names.get(name)


def missing_tokens(rows):
    """Najde všechny nevyřešené reference před označením vstupu za spustitelný."""
    return sorted({v for row in rows for v in row.values() if isinstance(v, str) and v.startswith("$")})


def resolve(value, name, index, ns, refs, bindings):
    """Doplní pouze explicitní slovníkové reference bez eval nebo shellu."""
    if not isinstance(value, str):
        return value
    if value.startswith("$ref:"):
        key = value[5:]
        synthetic = {
            "synthetic_period": 1001,
            "synthetic_period_child": 1002,
            "synthetic_document_type": 1003,
            "synthetic_document_material": 1004,
            "synthetic_document_material_2": 1005,
        }
        if key in synthetic:
            return ident("heslar", ns, synthetic[key], refs)
        return refs[key] if refs.get(key) not in (None, "") else value
    if value.startswith("$bind:"):
        return bindings.get(value[6:], value)
    if value.startswith("$row:"):
        parts = value.split(":")
        return ident(parts[1], ns, int(parts[2]) if len(parts) > 2 else index, refs) or value
    return value.format(tag=f"{ns}-{index}", n=int(ns) + index)


def row_for(mapper, ns, index, refs, bindings=None):
    """Sestaví úplnou hlavičku a vyplní explicitně recenzovaný recept."""
    name = mapper["csv"]
    row = {column: "" for column in mapper["columns"]}
    row.update({key: resolve(value, name, index, ns, refs, bindings or {}) for key, value in RECIPES[name].items()})
    if "ident_cely" in row:
        row["ident_cely"] = ident(name, ns, index, refs)
    if mapper["key"] == "id" and name not in ("distribution",):
        row["id"] = f"{mapper['prefix']}-{int(ns) + index}"
    if set(row) - set(mapper["columns"]):
        raise ValueError(f"Recipe/source column drift: {name}: {set(row) - set(mapper['columns'])}")
    return row


def graph(source, ns, refs, bindings=None):
    """Vytvoří základní graf včetně samostatných cílů vztahů."""
    tables = {}
    for mapper in source["mappers"]:
        name = mapper["csv"]
        count = 3 if ident(name, ns, 1, refs) and name != "heslar" else 1
        tables[name] = [row_for(mapper, ns, i, refs, bindings) for i in range(1, count + 1)]
    # The second document part deliberately has no fieldwork/project link: unidentified route.
    tables["dokumenty_casti"][1]["archeologicky_zaznam"] = ""
    tables["dokumenty_casti"][2]["archeologicky_zaznam"] = ""
    tables["dokumenty_casti"][2]["projekt"] = ident("projekty", ns, 1, refs)
    for slot, offset, family in [
        ("period", 1001, "HESLAR_OBDOBI"),
        ("period-child", 1002, "HESLAR_OBDOBI"),
        ("doc-type", 1003, "HESLAR_DOKUMENT_TYP"),
        ("doc-material", 1004, "HESLAR_DOKUMENT_MATERIAL"),
        ("doc-material-2", 1005, "HESLAR_DOKUMENT_MATERIAL"),
    ]:
        mapper = next(x for x in source["mappers"] if x["csv"] == "heslar")
        row = row_for(mapper, ns, offset, refs)
        row["nazev_heslare"] = refs.get("vocabulary_names", {}).get(family) or "$ref:vocabulary_names." + family
        tables["heslar"].append(row)
    return tables


def csv_bytes(rows, columns=None):
    """Zapíše CSV s čárkou, UTF-8, CRLF a uvozovkami všech polí."""
    columns = columns or list(rows[0])
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def zip_bytes(tables):
    """Vytvoří deterministický archiv; bez rozbalování cizích vstupů."""
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(tables.items()):
            if not re.fullmatch(r"[a-z0-9_]+\.csv", name):
                raise ValueError("Unsafe archive member name")
            info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    return stream.getvalue()


def late_bind(tables, bindings):
    """Doplní skutečné prefixed PK a cesty; nepovolí SQL nebo odhad čísel."""
    bound = {}
    for name, rows in tables.items():
        bound[name] = []
        for row in rows:
            result = {}
            for column, value in row.items():
                if isinstance(value, str) and value.startswith("$bind:"):
                    key = value[6:]
                    if key not in bindings:
                        raise ValueError(f"Missing verified binding: {key}")
                    value = bindings[key]
                    if column == "id" and not re.fullmatch(r"[a-z]+-\d+", str(value)):
                        raise ValueError("Invalid prefixed DB key binding")
                    if column == "path" and not re.fullmatch(
                        r"/?rest/AMCR/record/[A-Za-z0-9-]+/file/[a-fA-F0-9-]{36}", str(value)
                    ):
                        raise ValueError("Invalid repository path binding")
                result[column] = value
            bound[name].append(result)
    return bound
