"""Independent row/value and graph checks against exported database evidence.

No import report is used as an expected value. Schema descriptors supply column
types; the explicit relationship rules below supply special ownership semantics.
Unknown contracts block their check instead of accepting an aggregate count.
"""

import re
from datetime import datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from .verify import selected

ALIASES = {"komponenty": {"vazba": "komponenta_vazby"}, "uzivatele_notifikace_projekty": {"uzivatel": "user"}}
OWNER_FIELDS = {
    "komponenty": ("komponenta_vazby", ("dokumentacni_jednotka", "dokument_cast"), "komponenty"),
    "soubory": ("vazba", ("dokument", "projekt", "samostatny_nalez"), "soubory"),
    "historie": (
        "vazba",
        (
            "dokument",
            "projekt",
            "samostatny_nalez",
            "archeologicky_zaznam",
            "pian",
            "externi_zdroj",
            "auth_user",
            "soubor",
            "uzivatel_spoluprace",
        ),
        "historie",
    ),
}
NATURAL = {
    "HeslarNazev": "nazev",
    "RuianKatastr": "kod",
    "RuianOkres": "kod",
    "RuianKraj": "kod",
    "Kladyzm": "cislo",
    "Kladysm5": "mapno",
    "Group": "name",
}


def rows(snapshot, refs, table):
    """Combine scoped owned rows with sanitized, frozen reference identities."""
    if table not in snapshot and table not in refs.get("reference_rows", {}):
        raise ValueError(f"Missing table evidence: {table}")
    result = list(snapshot.get(table, []))
    for item in refs.get("reference_rows", {}).get(table, []):
        if item not in result:
            result.append(item)
    return result


def pk(model):
    """Respect one-to-one primary keys, including ADB and dating rows."""
    for field, info in model["fields"].items():
        if info.get("primary_key"):
            return info.get("db_column", field + "_id" if info["type"] in ("ForeignKey", "OneToOneField") else field)
    return "id"


def find_owner(snapshot, value, tables, link):
    candidates = []
    for table in tables:
        for row in snapshot.get(table, []):
            matches = row.get("ident_cely") == value
            if table in ("soubor", "uzivatel_spoluprace"):
                matches = value == ("soub-" if table == "soubor" else "spol-") + str(row.get("id"))
            if matches:
                candidates.append(row)
    if len(candidates) != 1 or candidates[0].get(link) is None:
        raise ValueError(f"Owner/link is absent or ambiguous: {value}:{link}")
    return candidates[0][link]


def scalar(value, info):
    """Normalize CSV values to persisted types using an explicit timezone."""
    if value is None or value == "":
        return None
    kind = info["type"]
    if kind == "BooleanField":
        text = str(value).lower()
        if text not in ("true", "false", "1", "0", "-1"):
            raise ValueError("Unknown boolean contract")
        return text in ("true", "1", "-1")
    if "Integer" in kind or kind == "AutoField":
        return int(value)
    if kind in ("FloatField", "DecimalField"):
        return Decimal(str(value))
    if kind in ("DateField", "TimeField", "DateTimeField"):
        text = str(value)
        if kind == "TimeField":
            return time.fromisoformat(text).isoformat()
        if re.match(r"\d{4}\.\d{1,2}\.\d{1,2}", text):
            text = datetime.strptime(text, "%Y.%m.%d %H:%M:%S").isoformat(sep=" ")
        if kind == "DateField":
            localized = re.fullmatch(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})(?: .*)?", text)
            if localized:
                return datetime(int(localized[3]), int(localized[2]), int(localized[1])).date().isoformat()
            if "T" in text or " " in text:
                parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
                if parsed.tzinfo is not None:
                    return parsed.astimezone(ZoneInfo("Europe/Prague")).date().isoformat()
            return text[:10]
        if kind == "DateTimeField":
            value = (
                datetime.strptime(text, "%d.%m.%Y %H:%M:%S")
                if re.match(r"\d{1,2}\.\d{1,2}\.\d{4}", text)
                else datetime.fromisoformat(text)
            )
            if value.tzinfo is None:
                value = value.replace(tzinfo=ZoneInfo("Europe/Prague"))
            return value.timestamp()
        return text
    return str(value)


def expected_field(source, mapper, field, value, snapshot, refs):
    """Resolve expected FK identities without trusting mapper output or a report."""
    name = mapper["csv"]
    model_name = mapper["columns"].get(field, {}).get("model", mapper["model"])
    model = source["models"].get(model_name, {})
    field_name = ALIASES.get(name, {}).get(field, mapper["columns"].get(field, {}).get("model_field", field))
    if field == "vazba" and name in OWNER_FIELDS:
        column, tables, link = OWNER_FIELDS[name]
        return model["table"], column, find_owner(snapshot, value, tables, link), None
    info = model.get("fields", {}).get(field_name)
    if info is None and field_name == "id":
        return model.get("table"), "id", int(str(value).rsplit("-", 1)[-1]), {"type": "IntegerField"}
    if info is None:
        raise ValueError(f"No explicit field contract: {name}.{field}")
    column = info.get(
        "db_column", field_name + "_id" if info["type"] in ("ForeignKey", "OneToOneField") else field_name
    )
    if "GeometryField" in info["type"] or info["type"] in ("PointField", "PolygonField", "LineStringField"):
        return model["table"], column, value or None, info
    if info["type"] not in ("ForeignKey", "OneToOneField"):
        return model["table"], column, scalar(value, info), info
    if not value:
        return model["table"], column, None, info
    target = info["args"][0] if info.get("args") else info.get("to")
    target = target.get("expression") if isinstance(target, dict) else target
    target = target.split(".")[-1]
    target_model = source["models"].get(target)
    if not target_model:
        target_model = {
            "table": {"Group": "auth_group", "ContentType": "django_content_type"}.get(target),
            "fields": {},
        }
    table = target_model["table"]
    key = NATURAL.get(target, "ident_cely")
    if key == "kod":
        value = int(str(value).removeprefix("ruian-"))
    if target == "Adb":
        key = "ident_cely"
    if target == "Akce":
        owner = [r for r in snapshot.get("archeologicky_zaznam", []) if r.get("ident_cely") == value]
        if len(owner) != 1:
            raise ValueError("Missing fieldwork root")
        key, value = "archeologicky_zaznam", owner[0]["id"]
    if target == "NeidentAkce":
        owner = [r for r in snapshot.get("dokument_cast", []) if r.get("ident_cely") == value]
        if len(owner) != 1:
            raise ValueError("Missing unidentified-fieldwork document part")
        key, value = "dokument_cast", owner[0]["id"]
    matches = [r for r in rows(snapshot, refs, table) if r.get(key) == value]
    if len(matches) != 1:
        raise ValueError(f"Missing/ambiguous reference: {table}.{key}={value}")
    return model["table"], column, matches[0][pk(target_model)], info


def equal(actual, expected, info):
    if info and info["type"] == "DateTimeField" and actual:
        actual = datetime.fromisoformat(str(actual)).timestamp()
    if isinstance(expected, Decimal) and actual is not None:
        actual = Decimal(str(actual))
    return actual == expected


def check_batch(source, batch, before, after, refs=None):
    """Check complete persisted row values and preserve omitted UPDATE columns.

    Geometry and repository evidence are separate mandatory checks. A missing
    special contract becomes blocked, never a successful row assertion.
    """
    refs = refs or {}
    results = []
    if (
        batch["expected"].startswith("reject")
        or batch["expected"] == "runtime-failure"
        or batch["expected"] not in ("apply", "acceptance-unresolved")
    ):
        for table in sorted(set(before) | set(after)):
            if table.startswith("_"):
                continue
            results.append(
                {
                    "id": batch["id"] + ".unchanged." + table,
                    "state": "passed" if before.get(table) == after.get(table) else "failed",
                }
            )
        return results
    mappers = {m["csv"]: m for m in source["mappers"]}
    for name, inputs in batch["tables"].items():
        if name in ("distribution", "paradata"):
            # Checked by direct repository resources, plus the separate history contract.
            results.append(
                {
                    "id": batch["id"] + "." + name,
                    "state": "blocked",
                    "reason": "Direct status/bytes/MIME/version and side-effect evidence required",
                }
            )
            continue
        if name in ("uzivatele_opravneni", "uzivatele_notifikace", "uzivatele_notifikace_projekty"):
            results.extend(check_user_relation(name, batch, inputs, before, after, refs))
            continue
        mapper = mappers[name]
        for i, data in enumerate(inputs, 1):
            result = {"id": f"{batch['id']}.{name}.{i}", "state": "blocked"}
            try:
                if any(isinstance(v, str) and v.startswith("$") for v in data.values()):
                    raise ValueError("Input still has unbound references")
                values, geometry = {}, []
                context = after if batch["operation"] != "delete" else before
                for field, value in data.items():
                    if field == "id" and batch["operation"] == "insert":
                        continue  # import pseudo-key is not the allocated DB key
                    table, column, expected, info = expected_field(source, mapper, field, value, context, refs)
                    if (
                        name == "az_dokumentacni_jednotky"
                        and field == "pian"
                        and data.get("typ") == refs.get("cadastral_dj_type")
                    ):
                        variant = next(
                            (
                                c["variant"]
                                for c in batch.get("case_details", [])
                                if c.get("target") == data.get("ident_cely") and c["variant"].startswith("cadastral-")
                            ),
                            None,
                        )
                        expected = cadastral_pian(data, before, after, variant)
                    if info and (
                        "GeometryField" in info["type"]
                        or info["type"] in ("PointField", "PolygonField", "LineStringField")
                    ):
                        geometry.append((table, column, expected))
                        continue
                    values.setdefault(table, {})[column] = (expected, info)
                primary = source["models"][mapper["model"]]["table"]
                key_fields = list(mapper["key"]) if isinstance(mapper["key"], (list, tuple)) else [mapper["key"]]
                selector = {}
                for key in key_fields:
                    if key == "id" and batch["operation"] == "insert":
                        continue
                    table, column, value, _ = expected_field(source, mapper, key, data[key], context, refs)
                    selector[column] = value
                if not selector:
                    selector = {k: v for k, (v, _) in values[primary].items()}
                old = selected(before, primary, selector)
                new = selected(after, primary, selector)
                if batch["operation"] == "delete":
                    passed = len(old) == 1 and len(new) == 0
                else:
                    passed = len(new) == 1 and (len(old) == 0 if batch["operation"] == "insert" else len(old) == 1)
                    for table, fields in values.items():
                        if table == primary:
                            targets = new
                        else:
                            targets = (
                                selected(
                                    after,
                                    table,
                                    {"archeologicky_zaznam" if name.startswith("az_") else "dokument": new[0]["id"]},
                                )
                                if len(new) == 1
                                else []
                            )
                        passed &= len(targets) == 1 and all(
                            equal(targets[0].get(k), v, info) for k, (v, info) in fields.items()
                        )
                        if batch["operation"] == "update" and targets:
                            previous = selected(before, table, {"id": targets[0]["id"]}) if "id" in targets[0] else old
                            derived = {column for owner_table, column, _ in geometry if owner_table == table}
                            if derived and "geom_sjtsk" in targets[0]:
                                derived |= {"geom", "geom_sjtsk"}
                            if name == "soubory":
                                derived |= {"mimetype", "size_mb", "sha_512", "rozsah"}
                                if old and targets[0].get("vazba") != old[0].get("vazba"):
                                    derived.add("path")
                            omitted = set(targets[0]) - set(fields) - derived - {"_geometry", "_geometry_consistent"}
                            passed &= len(previous) == 1 and all(
                                previous[0].get(k) == targets[0].get(k) for k in omitted
                            )
                    for table, column, expected in geometry:
                        # The SQL adds exact EWKT and independent SRID/pair consistency.
                        targets = (
                            new
                            if table == primary
                            else selected(after, table, {"dokument": new[0]["id"]}) if new else []
                        )
                        if not targets or "_geometry_consistent" not in targets[0]:
                            raise ValueError("Missing normalized geometry/SRID evidence")
                        passed &= targets[0]["_geometry_consistent"] is True
                        source_column = "geom_sjtsk" if str(data.get("geom_system")) == "5514" else "geom"
                        if column == source_column or not data.get(source_column):
                            actual = targets[0]["_geometry"][column]["wkt"]
                            passed &= geometry_equal(actual, expected)
                    if name == "soubory" and len(new) == 1:
                        owners = [
                            r
                            for table in ("dokument", "projekt", "samostatny_nalez")
                            for r in after.get(table, [])
                            if r.get("soubory") == new[0].get("vazba")
                        ]
                        passed &= len(owners) == 1
                        if owners:
                            expected_path = (
                                r"rest/AMCR/record/" + re.escape(owners[0]["ident_cely"]) + r"/file/[a-fA-F0-9-]{36}"
                            )
                            passed &= re.fullmatch(expected_path, str(new[0].get("path") or "").lstrip("/")) is not None
                result.update(state="passed" if passed else "failed", selector=selector, geometry_columns=geometry)
            except (ValueError, KeyError, TypeError) as error:
                result["reason"] = str(error)
            results.append(result)
    return results


def geometry_equal(actual, expected):
    """Compare simple generated WKT types and every coordinate, including Z."""
    if not actual or not expected:
        return not actual and not expected
    numeric = r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?"
    types = [re.sub(r"\s+", "", str(v).split("(", 1)[0]).upper() for v in (actual, expected)]
    left, right = [[float(n) for n in re.findall(numeric, str(v))] for v in (actual, expected)]
    return types[0] == types[1] and len(left) == len(right) and all(abs(a - b) < 1e-8 for a, b in zip(left, right))


def cadastral_pian(data, before, after, variant=None):
    """Reuse exact prior reference, or check the unique derived cadastral geometry."""
    parents = [
        r for r in before.get("archeologicky_zaznam", []) if r.get("ident_cely") == data.get("archeologicky_zaznam")
    ]
    if len(parents) != 1:
        raise ValueError("Missing cadastral Fieldwork event/Site parent")
    old = selected(before, "ruian_katastr", {"id": parents[0]["hlavni_katastr"]})
    new = selected(after, "ruian_katastr", {"id": parents[0]["hlavni_katastr"]})
    if len(old) != 1 or len(new) != 1:
        raise ValueError("Missing cadastral reference evidence")
    if variant == "cadastral-existing-pian" and not old[0].get("pian_id"):
        raise ValueError("Expected a cadastre with an existing spatial unit")
    if variant == "cadastral-missing-pian" and old[0].get("pian_id"):
        raise ValueError("Expected a cadastre without a spatial unit; controlled setup is incomplete")
    if old[0].get("pian_id"):
        if new[0].get("pian_id") != old[0]["pian_id"]:
            raise ValueError("Existing cadastral spatial unit was replaced")
        return old[0]["pian_id"]
    candidates = selected(after, "pian", {"id": new[0].get("pian_id")})
    prior_ids = {r["id"] for r in before.get("pian", [])}
    created = [r for r in after.get("pian", []) if r["id"] not in prior_ids]
    if len(candidates) != 1 or len(created) != 1 or candidates[0]["id"] != created[0]["id"]:
        raise ValueError("Expected exactly one new cadastral spatial unit")
    spatial = candidates[0]
    boundary = old[0].get("_geometry", {}).get("hranice", {}).get("wkt")
    actual = spatial.get("_geometry", {}).get("geom_sjtsk", {}).get("wkt")
    if (
        not boundary
        or not geometry_equal(actual, boundary)
        or spatial.get("geom_system") != "5514"
        or not spatial.get("_geometry_consistent")
    ):
        raise ValueError("Derived spatial unit differs from the cadastral boundary/SRID")
    return spatial["id"]


def check_user_relation(name, batch, inputs, before, after, refs):
    table = {
        "uzivatele_opravneni": "auth_user_groups",
        "uzivatele_notifikace": "auth_user_notifikace_typ",
        "uzivatele_notifikace_projekty": "notifikace_projekty_pes",
    }[name]
    result = []
    for i, data in enumerate(inputs, 1):
        item = {"id": f"{batch['id']}.{name}.{i}", "state": "blocked"}
        try:
            users = [u for u in rows(after, refs, "auth_user") if u.get("ident_cely") == data["uzivatel"]]
            if len(users) != 1:
                raise ValueError("Missing relation user")
            selector = {"user_id": users[0]["id"]}
            if name == "uzivatele_notifikace_projekty":
                if "ruian" in data:
                    code = int(str(data["ruian"]).removeprefix("ruian-"))
                    peers = [
                        (t, r)
                        for t in ("ruian_katastr", "ruian_okres", "ruian_kraj")
                        for r in rows(after, refs, t)
                        if r["kod"] == code
                    ]
                    if len(peers) != 1:
                        raise ValueError("Ambiguous RUIAN code")
                    model = peers[0][0].replace("_", "")
                    object_pk = peers[0][1]["id"]
                else:
                    code, model = int(data["object_id"]), data["content_type"].split(".")[-1]
                    ruian_table = {
                        "ruiankatastr": "ruian_katastr",
                        "ruianokres": "ruian_okres",
                        "ruiankraj": "ruian_kraj",
                    }.get(model)
                    peers = [r for r in rows(after, refs, ruian_table) if r["kod"] == code] if ruian_table else []
                    if len(peers) != 1:
                        raise ValueError("Missing serialized RUIAN code")
                    object_pk = peers[0]["id"]
                types = [r for r in rows(after, refs, "django_content_type") if r["model"] == model]
                if len(types) != 1:
                    raise ValueError("Missing RUIAN content type")
                selector.update(content_type_id=types[0]["id"], object_id=object_pk)
            else:
                other_table, input_field, natural, db_field = (
                    ("auth_group", "skupina", "name", "group_id")
                    if name == "uzivatele_opravneni"
                    else ("notifikace_typ", "notifikace", "ident_cely", "usernotificationtype_id")
                )
                peer = [r for r in rows(after, refs, other_table) if r[natural] == data[input_field]]
                if len(peer) != 1:
                    raise ValueError("Missing relation endpoint")
                selector[db_field] = peer[0]["id"]
            old, new = selected(before, table, selector), selected(after, table, selector)
            passed = (len(old), len(new)) == ((0, 1) if batch["operation"] == "insert" else (1, 0))
            item.update(state="passed" if passed else "failed", selector=selector)
        except (ValueError, KeyError) as error:
            item["reason"] = str(error)
        result.append(item)
    return result
