"""Konkrétní izolované kontexty složitých větví a kompatibilní dávky."""

from __future__ import annotations

from collections import defaultdict

from .catalog import RECIPES, VARIANTS
from .datasets import ident, resolve, row_for

REJECT = {
    "unique-term",
    "unique-abbreviation",
    "wrong-vocabulary",
    "forward-reference",
    "month-limit",
    "duplicate-name",
    "protected-reference-delete",
    "type-project-constraint",
    "wrong-subtype",
    "composite-duplicate",
    "invalid-geometry",
    "mutual-exclusion",
    "unique-email",
    "existing-relation",
    "missing-relation",
    "reserved-orig",
    "reserved-paradata",
    "reserved-page-thumb",
    "unsafe-path",
    "prefix-collision",
}
REJECT |= {
    "duplicate-in-batch",
    "existing-distribution",
    "missing-update",
    "missing-delete",
    "empty-name",
    "unsafe-filename",
    "missing-file-id",
    "missing-file-uuid",
    "missing-file-owner",
    "existing-ancestor-conflict",
    "existing-descendant-conflict",
    "missing-distribution",
    "empty-path",
    "unknown-path",
}
REJECT |= {"date-trailing-junk", "datetime-trailing-junk"}
UNRESOLVED = {"cycle", "self-reference", "count-boundary", "duplicate-relation"}
RUNTIME = {
    "cadastral-missing-pian",
    "active-user-delete",
    "missing-companion",
    "missing-extra-data",
    "thumb-backfill",
    "backfill-idempotence",
}
RUNTIME |= {"missing-file-uuid", "missing-file-owner"}
LIFECYCLES = {"tombstone-reinsert", "recreate", "relation-add-remove"}
FILE_LIFECYCLES = {"soubory.branch." + value for value in ("document-owner", "project-owner", "individual-find-owner")}


def variant_row(mapper, variant, index, ns, refs):
    """Převede pojmenovanou větev na konkrétní změnu a kontrolní smlouvu."""
    name = mapper["csv"]
    row = row_for(mapper, ns, index, refs)
    # Fixed second identities refer to the same isolated context, never another case.
    for field, raw in RECIPES[name].items():
        if isinstance(raw, str) and raw.startswith("$row:") and raw.endswith(":2"):
            row[field] = ident(raw.split(":")[1], ns, index + 1, refs)
    if name in ("dokumenty_neident_akce", "dokumenty_neident_akce_vedouci"):
        row["dokument_cast" if name == "dokumenty_neident_akce" else "neident_akce"] = ident(
            "dokumenty_casti", ns, index, refs
        )
    if name == "heslar_datace":
        row["obdobi"] = ident("heslar", ns, index, refs)
    if name == "heslar_hierarchie":
        row.update(
            heslo_nadrazene=ident("heslar", ns, index, refs), heslo_podrazene=ident("heslar", ns, index + 1, refs)
        )
    operation = "update" if mapper["allow_update"] else "insert"
    outcome = "reject" if variant in REJECT else "apply"
    notes = []
    if variant in UNRESOLVED:
        outcome = "acceptance-unresolved"
        notes.append(
            "No acceptance rule for this combination was established by the issue; record current behaviour and integrity, then resolve the rule before a pass."
        )
    if variant in RUNTIME:
        notes.append(
            "Requires the named controlled setup before this input; retain before/after evidence and do not run setup without target-specific authorization."
        )
    if variant == "missing-companion":
        outcome = "reject"
        notes.append(
            "Remove only the companion of this run-owned isolated root after retaining its full row and an approved restoration recipe; expected clean row rejection and unchanged surviving root."
        )
    if variant == "active-user-delete":
        operation, outcome = "delete", "reject"
        row["ident_cely"] = "$ref:current_operator_ident"
        notes.append(
            "Use a disposable approved operator currently logged in as import owner; never substitute a shared administrator. The key must be bound explicitly at session preflight."
        )
    if "geometry-4326" == variant:
        row.update(geom_system="4326", geom="POINT(14.50001 50.00001)", geom_sjtsk="")
    elif "geometry-5514" == variant:
        row.update(geom_system="5514", geom="", geom_sjtsk="$ref:point_5514_offset")
    elif variant in ("geometry-clear", "omitted-versus-clear"):
        row.update(geom_system="4326", geom="", geom_sjtsk="")
        if name == "az_pian":
            outcome = "reject"
        notes.append(
            "Compare an update omitting geometry headers against this explicit-clear input; preserve both reports and verify source/derived geometry and required-field rules separately."
        )
    elif variant == "invalid-geometry":
        row["geom"] = "NOT A GEOMETRY"
    elif variant == "line":
        row.update(geom="LINESTRING(14.5 50,14.50001 50.00001)", geom_system="4326", typ="$ref:pian_line_type")
    elif variant == "polygon":
        row.update(
            geom="POLYGON((14.5 50,14.50001 50,14.50001 50.00001,14.5 50))",
            geom_system="4326",
            typ="$ref:pian_polygon_type",
        )
    elif variant in ("partial-update", "partial-range-update"):
        key = list(mapper["key"]) if isinstance(mapper["key"], (list, tuple)) else [mapper["key"]]
        field = next(
            (x for x in ("poznamka", "lokalizace", "nazev", "rok_do_max", "uzivatelske_oznaceni") if x in row), None
        )
        if variant == "partial-range-update":
            field = "rok_do_max"
        if field:
            row = {k: row[k] for k in [*key, field]}
            row[field] = 300 if field == "rok_do_max" else f"TEST PARTIAL {ns}-{index}"
    elif variant == "independent-fieldwork":
        row.update(typ="N", projekt="")
    elif variant == "type-project-constraint":
        row.update(typ="N", projekt=ident("projekty", ns, index, refs))
    elif variant == "wrong-subtype":
        row["ident_cely"] = ident("az_lokality" if name == "az_akce" else "az_akce", ns, index, refs)
    elif variant == "mutual-exclusion":
        row.update(archeologicky_zaznam=ident("az_akce", ns, index, refs), projekt=ident("projekty", ns, index, refs))
    elif variant in ("project-link", "unidentified-link"):
        row["archeologicky_zaznam"] = ""
        row["projekt"] = ident("projekty", ns, index, refs) if variant == "project-link" else ""
    elif variant in (
        "documentation-unit-owner",
        "document-part-fieldwork-owner",
        "document-part-document-owner",
        "both-component-owners",
    ):
        if "vazba" in row:
            row["vazba"] = ident(
                "az_dokumentacni_jednotky" if variant == "documentation-unit-owner" else "dokumenty_casti",
                ns,
                index,
                refs,
            )
        if name == "komponenty" and variant.startswith("document-part-"):
            row["ident_cely"] = ident("dokumenty", ns, index, refs) + "-K001"
        notes.append(
            "Assert the correct parent history/XML route; the document-only part must have both optional external links empty."
        )
    elif variant == "site-owner":
        row["archeologicky_zaznam"] = ident("az_lokality", ns, index, refs)
    elif variant.startswith("cadastral-"):
        row.update(typ="$ref:cadastral_dj_type", pian="")
        notes.append(
            "Use a verified cadastral area with the required existing/missing spatial-unit state; check reuse or one new spatial unit and rollback/orphan behaviour."
        )
    elif variant in ("district", "region", "cadastre"):
        row["ruian"] = refs.get({"cadastre": "katastr"}.get(variant, variant), "$ref:" + variant)
    elif variant in ("serialized-content-type", "wrong-content-type"):
        row = {
            "uzivatel": row["uzivatel"],
            "content_type": (
                "$ref:cadastre_content_type" if variant == "serialized-content-type" else "$ref:wrong_content_type"
            ),
            "object_id": "$ref:cadastre_code",
        }
    elif variant == "reparent-old-new":
        candidates = [field for field, raw in RECIPES[name].items() if isinstance(raw, str) and raw.startswith("$row:")]
        if candidates:
            field = candidates[0]
            target = RECIPES[name][field].split(":")[1]
            row[field] = ident(target, ns, index + 1, refs)
        else:
            field = next((key for key, value in mapper["columns"].items() if value.get("kind") == "lookup"), None)
            if field:
                row[field] = "$ref:replacement_" + name + "_" + field
        notes.append(
            "Capture both previous and new owners/peers. Old links must disappear and new links appear in their respective metadata, with untouched sibling controls."
        )
    elif variant == "wrong-vocabulary":
        field = next((key for key, info in mapper["columns"].items() if "Heslar" in info.get("definition", "")), None)
        if field:
            target = (
                "HESLAR_PRISTUPNOST"
                if "HESLAR_LICENCE" in mapper["columns"][field].get("definition", "")
                else "HESLAR_LICENCE"
            )
            row[field] = refs.get(target, "$ref:" + target)
    elif variant == "month-limit":
        row["mesicu_do_zverejneni"] = 2147483647
    elif variant == "confidence-bounds":
        row["duveryhodnost"] = 101
        outcome = "reject"
    elif variant == "count-boundary":
        row["pocet"] = -1
    elif variant == "unique-email":
        row["email"] = f"user-{ns}-{index + 1}@example.invalid"
    elif variant == "duplicate-name":
        row.update(jmeno=f"Test{ns}-{index + 1}", prijmeni=f"Synthetic{ns}-{index + 1}")
    elif variant == "unique-term":
        row.update(heslo=f"TEST {ns}-1", heslo_en=f"TEST {ns}-1")
    elif variant == "unique-abbreviation":
        row["zkratka"] = "T" + str(int(ns) + 1)
    elif variant == "booleans-access":
        for field in (
            "oao",
            "zanikla",
            "cteni_dokumentu",
            "predano",
            "is_active",
            "is_staff",
            "is_superuser",
            "jistota",
        ):
            if field in row:
                row[field] = "-1" if field not in ("is_staff", "is_superuser") else "0"
    elif variant in ("date-time-legacy", "date-boundaries", "legacy-date", "legacy-datetime"):
        for field in ("datum", "datum_rd", "date_joined", "rok_zahajeni"):
            if field in row:
                row[field] = "2011.1.1 0:00:00" if field != "rok_zahajeni" else -100
    elif variant == "mapping-relation-choice":
        row["skos_mapping_relation"] = "invalid-choice"
        outcome = "reject"
    elif variant == "nullable-lookups":
        for key, info in mapper["columns"].items():
            if info.get("kind") == "lookup" and info.get("nullable"):
                row[key] = ""
    elif variant in ("csv-null-string", "unicode-quotes-newline"):
        row["poznamka" if "poznamka" in row else "popis"] = (
            "NA" if variant == "csv-null-string" else 'NA, NULL, "None"\nPříliš žluťoučký kůň'
        )
    elif variant in ("reserved-orig", "reserved-paradata", "reserved-page-thumb", "unsafe-path"):
        row["distribution"] = {
            "reserved-orig": "orig",
            "reserved-paradata": "paradata/x",
            "reserved-page-thumb": "thumb/page/1",
            "unsafe-path": "atr/../orig",
        }[variant]
    elif variant in ("orig-paradata", "thumb-paradata"):
        row["distribution"] = "orig" if variant == "orig-paradata" else "thumb"
    elif variant in ("document-owner", "project-owner", "individual-find-owner") and name == "soubory":
        owner = {
            "document-owner": "dokumenty",
            "project-owner": "projekty",
            "individual-find-owner": "samostatne_nalezy",
        }[variant]
        row["vazba"] = ident(owner, ns, index, refs)
        row["nazev"] = (
            f"replacement-{ns}-{index}.jpg" if variant == "individual-find-owner" else f"replacement-{ns}-{index}.pdf"
        )
    elif variant == "gps-removal":
        row.update(vazba=ident("samostatne_nalezy", ns, index, refs), nazev=f"gps-{ns}-{index}.jpg")
    elif variant == "missing-binary":
        row["nazev"] = f"deliberately-absent-{ns}-{index}.pdf"
        outcome = "runtime-failure"
    elif variant == "mime-extension":
        row["nazev"] = f"pdf-disguised-{ns}-{index}.jpg"
        outcome = "acceptance-unresolved"
        notes.append(
            "Agree whether a detected MIME/extension mismatch is rejected or retained with the detected MIME before assigning a pass."
        )
    elif variant in ("child-delete-history", "delete-parent-history", "protected-reference-delete", "missing-relation"):
        operation = "delete"
    elif variant == "recreate" or variant == "tombstone-reinsert":
        notes.append(
            "Run INSERT, UPDATE, DELETE, then INSERT with the same distribution key; retain each phase report and direct status/version/content evidence."
        )
    elif variant == "missing-extra-data":
        notes.append(
            "Prepare the document without optional extra-data fields, prove the companion row is absent, then apply this geometry/extra-data update."
        )
    elif variant in ("forward-reference", "backward-reference", "hierarchy", "cycle", "self-reference"):
        field = (
            "soucast"
            if name == "organizace"
            else (
                "heslo_nadrazene"
                if name == "heslar_hierarchie"
                else "posudek" if name == "dokumenty_posudky" else "spolupracovnik"
            )
        )
        row[field] = (
            row.get("ident_cely", row.get("dokument", row.get("vedouci", "$ref:self_target")))
            if variant == "self-reference"
            else "$ref:" + variant + "_target"
        )
        notes.append(
            "The forward target must be absent before this batch; reverse-order/cycle pairs are isolated and require explicit acceptance before verdict."
        )
    if name == "historie" and variant.endswith("-owner"):
        owner = {
            "project-owner": "projekty",
            "fieldwork-owner": "az_akce",
            "site-owner": "az_lokality",
            "document-owner": "dokumenty",
            "individual-find-owner": "samostatne_nalezy",
            "spatial-unit-owner": "az_pian",
            "external-source-owner": "externi_zdroje",
            "user-owner": "uzivatele",
        }.get(variant)
        row["vazba"] = (
            ident(owner, ns, index, refs)
            if owner
            else (f"$bind:file:{index}.id" if variant == "file-owner" else f"$bind:uzivatele_spoluprace:{index}.id")
        )
        notes.append(
            "The attached historie.sql defines this owner key. A resolver rejection is a failed positive test, not evidence that the owner is out of scope."
        )
    if variant == "uri-null":
        row["uri"] = ""
    if variant in ("localized-date", "timezone-date-shift", "date-trailing-junk"):
        row["datum"] = {
            "localized-date": "2. 1. 2020 10:20:30",
            "timezone-date-shift": "2020-01-01T23:30:00Z",
            "date-trailing-junk": "2020-01-02junk",
        }[variant]
    if variant in ("localized-datetime", "datetime-trailing-junk"):
        row["date_joined"] = "02.01.2020 10:20:30" if variant == "localized-datetime" else "2020-01-02 10:20:30junk"
    if variant == "nullable-years":
        row["rok_narozeni"] = ""
    if variant == "required-map-sheet":
        row["sm5"], outcome = "", "reject"
    if variant == "constraints" and name == "samostatne_nalezy":
        row["geom_system"], outcome = "9999", "reject"
    if variant == "both-endpoints-update":
        for field, target in (
            ("heslo_nadrazene", "heslar"),
            ("heslo_podrazene", "heslar"),
            ("archeologicky_zaznam", "az_akce"),
            ("externi_zdroj", "externi_zdroje"),
        ):
            if field in row:
                row[field] = ident(target, ns, index + 1 if field != "heslo_podrazene" else index, refs)
    if variant == "all-optional-fields":
        row.update(
            sbornik_nazev=f"TEST collection {ns}-{index}",
            edice_rada="TEST series",
            casopis_denik_nazev="TEST journal",
            casopis_rocnik="2020/1",
            isbn="9780000000002",
            issn="0000-0000",
            datum_rd="2020-01-02",
            link="https://example.invalid/test",
        )
    if variant == "optional-pian-text":
        row["pian"] = ""
    if variant == "reparent-old-new" and name == "heslar_odkazy":
        row["heslo"] = ident("heslar", ns, 1002, refs)
    if variant == "nested-name":
        row["distribution"] = "deep/ocr/alto-xml"
    if variant == "download-permissions":
        notes.append(
            "Human opens the bound original/distribution/paradata download links with the approved operator, authorized reader and unauthorized/anonymous sessions; agent supplies exact URLs and the agreed access matrix. Keep observed HTTP/download outcome and filename/MIME; a Fedora service-account read is not this permissions test."
        )
    if name == "heslar_hierarchie" and variant == "self-reference":
        row["heslo_nadrazene"] = row["heslo_podrazene"] = ident("heslar", ns, index, refs)
    if variant == "replace-preserves-path":
        row["nazev"] = f"replacement-{ns}-{index}.pdf"
    if mapper["key"] == "id":
        row["id"] = "$bind:" + name + ":" + str(index) + ".id"
    if name == "distribution":
        row["id"] = f"$bind:file:{index}.id"
    if name == "paradata":
        row["path"] = f"$bind:file:{index}.path"
    rows = [row]
    if variant in (
        "duplicate-in-batch",
        "existing-distribution",
        "existing-ancestor-conflict",
        "existing-descendant-conflict",
    ):
        operation = "insert"
    if variant == "duplicate-in-batch":
        rows.append(dict(row))
    if variant == "missing-delete":
        operation = "delete"
    if variant == "empty-name":
        row["distribution"] = ""
    if variant == "unsafe-filename":
        row["nazev"] = "../not-allowed.xml"
    if variant == "missing-file-id":
        row["id"] = "$ref:unused_file_key"
    if variant in ("existing-ancestor-conflict", "existing-descendant-conflict"):
        row["distribution"] = "ocr/alto-xml" if variant == "existing-ancestor-conflict" else "ocr"
    if variant == "missing-distribution":
        row["distribution"] = "absent/alto-xml"
    if variant == "empty-path":
        row["path"] = ""
    if variant == "unknown-path":
        row["path"] = (
            "rest/AMCR/record/" + ident("dokumenty", ns, index, refs) + "/file/00000000-0000-0000-0000-000000000000"
        )
    if name == "heslar_hierarchie" and variant == "cycle":
        operation = "insert"
        row.update(
            id=f"hier-{int(ns) + index}",
            heslo_nadrazene=ident("heslar", ns, index, refs),
            heslo_podrazene=ident("heslar", ns, index + 1, refs),
        )
        rows.append(
            {
                **row,
                "id": f"hier-{int(ns) + index + 1}",
                "heslo_nadrazene": row["heslo_podrazene"],
                "heslo_podrazene": row["heslo_nadrazene"],
            }
        )
    if variant == "prefix-collision":
        operation = "insert"
        rows = [{**row, "distribution": "ocr"}, {**row, "distribution": "ocr/alto-xml"}]
    if variant == "same-record-multiple-files":
        rows.append({**row, "id": f"$bind:file:{index + 1}.id"})
    if variant in ("existing-relation", "composite-duplicate"):
        operation = "insert"
        if variant == "composite-duplicate":
            rows.append(dict(row))
    if variant == "both-component-owners":
        second = dict(row)
        second["komponenta"] = ident("dokumenty", ns, index + 1, refs) + "-K001"
        if mapper["key"] == "id":
            second["id"] = f"$bind:{name}:{index + 1}.id"
        if "pocet" in row:
            row["pocet"], second["pocet"] = 5, 6
        rows.append(second)
    if variant == "cascade":
        operation = "delete"
        # Project-linked fieldwork is RESTRICT; document parts are CASCADE.
        outcome = "reject" if name == "projekty" else "apply"
    extra_tables = {}
    if name == "paradata" and variant == "same-batch-distribution":
        operation = "insert"
        rows[0]["distribution"] = "new/alto-xml"
        extra_tables["distribution"] = [
            {
                "id": f"$bind:file:{index}.id",
                "nazev": f"alto-{ns}-{index}.xml",
                "mimetype": "application/xml",
                "distribution": "new/alto-xml",
            }
        ]
    if name == "paradata" and variant == "delete-with-distribution":
        operation = "delete"
        rows = [{"path": row["path"], "distribution": row["distribution"]}]
        extra_tables["distribution"] = [{"id": f"$bind:file:{index}.id", "distribution": row["distribution"]}]
    if name == "organizace" and variant in ("hierarchy", "cycle"):
        rows[0]["soucast"] = ident("organizace", ns, index + 1, refs)
        if variant == "cycle":
            parent = row_for(mapper, ns, index + 1, refs)
            parent["soucast"] = rows[0]["ident_cely"]
            rows.append(parent)
    if name == "heslar_hierarchie" and variant in ("forward-reference", "backward-reference"):
        rows[0]["heslo_nadrazene"] = ident("heslar", ns, index + 2 if variant == "forward-reference" else index, refs)
    if name == "organizace" and variant in ("forward-reference", "backward-reference"):
        parent = row_for(mapper, ns, index + 2, refs)
        child = row_for(mapper, ns, index + 3, refs)
        child["soucast"] = parent["ident_cely"]
        operation = "insert"
        rows = [child, parent] if variant == "forward-reference" else [parent, child]
    rows = [{key: resolve(value, name, index, ns, refs, {}) for key, value in item.items()} for item in rows]
    extra_tables = {
        table: [{key: resolve(value, table, index, ns, refs, {}) for key, value in item.items()} for item in items]
        for table, items in extra_tables.items()
    }
    return {
        "operation": operation,
        "outcome": outcome,
        "row": rows[0],
        "rows": rows,
        "extra_tables": extra_tables,
        "notes": notes,
        "setup": "isolated-context",
        "index": index,
    }


def branch_contexts(source, ns, refs):
    """Oddělí kontexty větví a seskupí po nejvýše jedné třídě na dávku."""
    by_name = {m["csv"]: m for m in source["mappers"]}
    roots = [name for name in by_name if ident(name, ns, 1, refs) and name != "heslar"]
    setup = defaultdict(list)
    cases = []
    index = 100
    for name, variants in VARIANTS.items():
        mapper = by_name[name]
        for variant in variants:
            spec = variant_row(mapper, variant, index, ns, refs)
            case_id = f"{name}.branch.{variant}"
            # Each branch owns its full root graph; two identities allow old/new-owner checks.
            for root in roots:
                for i in (index, index + 1):
                    row = row_for(by_name[root], ns, i, refs)
                    for field, raw in RECIPES[root].items():
                        if isinstance(raw, str) and raw.startswith("$row:") and raw.endswith(":2"):
                            row[field] = ident(raw.split(":")[1], ns, index + 1, refs)
                    if root == "dokumenty_casti" and (
                        name.startswith("dokumenty_neident") or variant == "document-part-document-owner"
                    ):
                        row["archeologicky_zaznam"] = ""
                    if root == "az_akce" and variant.startswith("cadastral-") and i == index:
                        reference = (
                            "cadastral_missing_katastr"
                            if variant == "cadastral-missing-pian"
                            else "cadastral_existing_katastr"
                        )
                        row["hlavni_katastr"] = refs.get(reference) or refs.get("katastr") or "$ref:katastr"
                    if variant == "both-component-owners" and i == index + 1:
                        if root == "dokumenty_casti":
                            row["archeologicky_zaznam"] = ""
                        if root == "komponenty":
                            row["vazba"] = ident("dokumenty_casti", ns, i, refs)
                            row["ident_cely"] = ident("dokumenty", ns, i, refs) + "-K001"
                    if name == "komponenty" and variant.startswith("document-part-") and root == "komponenty":
                        row["vazba"] = ident("dokumenty_casti", ns, i, refs)
                        row["ident_cely"] = ident("dokumenty", ns, i, refs) + "-K001"
                    setup[root].append(row)
            if (
                name not in roots
                and name not in ("distribution", "paradata")
                and (
                    spec["operation"] in ("update", "delete") or variant in ("existing-relation", "composite-duplicate")
                )
                and variant != "missing-relation"
            ):
                row = row_for(mapper, ns, index, refs)
                for field, raw in RECIPES[name].items():
                    if isinstance(raw, str) and raw.startswith("$row:") and raw.endswith(":2"):
                        row[field] = ident(raw.split(":")[1], ns, index + 1, refs)
                if name in ("dokumenty_neident_akce", "dokumenty_neident_akce_vedouci"):
                    row["dokument_cast" if name == "dokumenty_neident_akce" else "neident_akce"] = ident(
                        "dokumenty_casti", ns, index, refs
                    )
                if name == "heslar_datace":
                    row["obdobi"] = ident("heslar", ns, index, refs)
                if name == "soubory" and variant in (
                    "document-owner",
                    "project-owner",
                    "individual-find-owner",
                    "gps-removal",
                ):
                    owner = {
                        "document-owner": "dokumenty",
                        "project-owner": "projekty",
                        "individual-find-owner": "samostatne_nalezy",
                        "gps-removal": "samostatne_nalezy",
                    }[variant]
                    row["vazba"] = ident(owner, ns, index, refs)
                    if variant in ("individual-find-owner", "gps-removal"):
                        row["nazev"] = f"gps-{ns}-{index}.jpg"
                setup[name].append(row)
                if variant == "both-component-owners" and mapper["key"] == "id":
                    second = row_for(mapper, ns, index + 1, refs)
                    second["komponenta"] = ident("dokumenty", ns, index + 1, refs) + "-K001"
                    setup[name].append(second)
            if name == "dokumenty_neident_akce_vedouci":
                parent = row_for(by_name["dokumenty_neident_akce"], ns, index, refs)
                parent["dokument_cast"] = ident("dokumenty_casti", ns, index, refs)
                setup["dokumenty_neident_akce"].append(parent)
            if name in ("heslar_datace", "heslar_hierarchie"):
                for number in (index, index + 1) if name == "heslar_hierarchie" else (index,):
                    term = row_for(by_name["heslar"], ns, number, refs)
                    term["nazev_heslare"] = (
                        refs.get("vocabulary_names", {}).get("HESLAR_OBDOBI") or "$ref:vocabulary_names.HESLAR_OBDOBI"
                    )
                    setup["heslar"].append(term)
            if name in ("distribution", "paradata") or (name == "historie" and variant == "file-owner"):
                file_mapper = by_name["soubory"]
                for number in (index, index + 1) if variant == "same-record-multiple-files" else (index,):
                    file_row = row_for(file_mapper, ns, number, refs)
                    file_row["vazba"] = ident("dokumenty", ns, index, refs)
                    setup["soubory"].append(file_row)
            if name == "historie" and variant == "cooperation-owner":
                cooperation = row_for(by_name["uzivatele_spoluprace"], ns, index, refs)
                cooperation["spolupracovnik"] = ident("uzivatele", ns, index + 1, refs)
                setup["uzivatele_spoluprace"].append(cooperation)
            cases.append({"id": case_id, "class": name, "variant": variant, **spec})
            index += 10
    groups = []
    for case in cases:
        if (
            case["variant"] in RUNTIME
            or case["variant"] in LIFECYCLES
            or case["id"] in FILE_LIFECYCLES
            or case["outcome"] == "acceptance-unresolved"
        ):
            continue
        combined = {case["class"]: case["rows"], **case["extra_tables"]}
        isolated = (
            case["variant"] in ("forward-reference", "prefix-collision")
            or case["outcome"] == "runtime-failure"
            or (case["class"] == "historie" and case["variant"] in ("file-owner", "cooperation-owner", "user-owner"))
        )
        group = next(
            (
                g
                for g in groups
                if not isolated
                and not g.get("isolated")
                and g["operation"] == case["operation"]
                and g["outcome"] == case["outcome"]
                and all(
                    name not in g["tables"] or set(g["tables"][name][0]) == set(items[0])
                    for name, items in combined.items()
                )
            ),
            None,
        )
        if group is None:
            group = {
                "operation": case["operation"],
                "outcome": case["outcome"],
                "tables": {},
                "cases": [],
                "isolated": isolated,
            }
            groups.append(group)
        for table, items in combined.items():
            group["tables"].setdefault(table, []).extend(items)
        group["cases"].append(case["id"])
    return dict(setup), cases, groups
