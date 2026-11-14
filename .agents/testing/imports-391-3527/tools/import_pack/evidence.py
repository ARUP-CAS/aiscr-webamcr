"""Read-only čtení reportů a samostatné důkazy o přidělených klíčích."""

import re
import zipfile

from .common import digest


def report_rows(path):
    """Načte data XLSX bez vykonávání vzorců a externích odkazů."""
    from openpyxl import load_workbook

    with zipfile.ZipFile(path) as archive:
        if sum(info.file_size for info in archive.infolist()) > 150_000_000:
            raise ValueError("XLSX exceeds evidence expansion budget")
    workbook = load_workbook(path, read_only=True, data_only=True, keep_links=False)
    try:
        if not {"Import", "Fedora"}.issubset(workbook.sheetnames):
            raise ValueError("Expected Import and Fedora report sheets")
        result = {}
        for name in ("Import", "Fedora"):
            rows = iter(workbook[name].iter_rows(values_only=True))
            headers = next(rows, None)
            if not headers:
                raise ValueError("Empty report sheet")
            result[name] = [dict(zip(headers, row)) for row in rows]
        return result
    finally:
        workbook.close()


def bind_keys(manifest, snapshot, report):
    """Vyžaduje shodu reportovaného PK se samostatným DB exportem."""
    mapping = {}
    for row in report["Import"]:
        name = row.get("CSV")
        import_id = row.get("ID v CSV", row.get("ID in CSV"))
        database_id = row.get("ID v DB", row.get("ID in DB"))
        if not name or not import_id or not database_id:
            continue
        name = str(name).removesuffix(".csv")
        candidates = [
            batch for batch in manifest["batches"] if batch["operation"] == "insert" and name in batch["tables"]
        ]
        if not candidates:
            continue
        originals = [source for batch in candidates for source in batch["tables"][name]]
        for ordinal, source in enumerate(originals, 1):
            if str(source.get("id", source.get("ident_cely"))) != str(import_id):
                continue
            match = re.fullmatch(r"(?:([a-z]+)-)?(\d+)", str(database_id))
            if not match:
                continue
            pk = int(match.group(2))
            logical = re.fullmatch(r"([a-z]+)-(\d+)", str(import_id))
            index = (
                int(logical.group(2)) - int(manifest["namespace"]) if logical and manifest.get("namespace") else ordinal
            )
            if index < 1:
                raise ValueError("Import identity is outside this namespace")
            # Narrow by class table: PK equality across unrelated tables is not identity.
            model_table = manifest.get("class_tables", {}).get(name)
            matches = [record for record in snapshot.get(model_table, []) if record.get("id") == pk]
            if len(matches) != 1:
                raise ValueError(f"DB/report identity disagreement for {name}:{index}")
            if source.get("ident_cely") and matches[0].get("ident_cely") != source["ident_cely"]:
                raise ValueError("DB natural key disagrees with report")
            prefix = str(import_id).split("-", 1)[0]
            if match.group(1) and match.group(1) != prefix:
                raise ValueError("DB key prefix disagrees with CSV key")
            mapping[f"{name}:{index}.id"] = f"{prefix}-{pk}"
            if name == "soubory":
                if not matches[0].get("path"):
                    raise ValueError("File has no repository path")
                if "nazev" in source and matches[0].get("nazev") != source["nazev"]:
                    raise ValueError("File name disagrees with creation evidence")
                if "vazba" in source:
                    owners = [
                        owner
                        for table in ("dokument", "projekt", "samostatny_nalez")
                        for owner in snapshot.get(table, [])
                        if owner.get("ident_cely") == source["vazba"]
                    ]
                    if len(owners) != 1 or owners[0].get("soubory") != matches[0].get("vazba"):
                        raise ValueError("File owner disagrees with creation evidence")
                mapping[f"file:{index}.id"] = f"soub-{pk}"
                mapping[f"file:{index}.path"] = matches[0]["path"]
                if index == 1:
                    mapping["file.id"], mapping["file.path"] = f"soub-{pk}", matches[0]["path"]
            break
    return mapping


def file_evidence(path):
    """Vrátí cestu a otisk existujícího lokálního důkazu."""
    return {"path": str(path.resolve()), "sha256": digest(path.read_bytes()), "bytes": path.stat().st_size}
