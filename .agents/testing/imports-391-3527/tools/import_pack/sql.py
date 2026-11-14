"""Úplné read-only SQL exporty reference, schématu a vlastněného grafu."""

import ast
import re


def quote(value):
    """Escapuje SQL literál; identifikátory nevytváří ze vstupních dat."""
    return "'" + str(value).replace("'", "''") + "'"


def reference_sql(repo):
    """Sestaví jeden JSON výsledek s referencemi známého testovacího schématu."""
    if isinstance(repo, dict):
        constants = repo["vocabulary_constants"]
    else:
        tree = ast.parse((repo / "webclient/heslar/hesla.py").read_text(encoding="utf-8"))
        constants = {
            n.target.id: ast.literal_eval(n.value)
            for n in tree.body
            if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id.startswith("HESLAR_")
        }
    fields = []
    point = "ST_SetSRID(ST_Point(14.5,50.0),4326)"
    extent = "ST_MakeEnvelope(14.5,50.0,14.50002,50.00002,4326)"

    def covers(column):
        return f"ST_Covers({column},ST_Transform({extent},ST_SRID({column})))"

    for key, family in sorted(constants.items()):
        # Stable, domain-sensitive preferences; each selected reference is returned with its family.
        preference = {
            "HESLAR_PIAN_TYP": "CASE WHEN lower(heslo)='bod' THEN 0 ELSE 1 END,",
            "HESLAR_DJ_TYP": "CASE WHEN lower(heslo) LIKE '%katastr%' THEN 1 ELSE 0 END,",
            "HESLAR_PRISTUPNOST": "CASE WHEN zkratka='A' THEN 0 ELSE 1 END,",
            "HESLAR_DOKUMENT_RADA": "CASE WHEN zkratka='TX' THEN 0 ELSE 1 END,",
        }.get(key, "")
        extra = " AND zkratka<'4'" if key == "HESLAR_PIAN_PRESNOST" else ""
        fields += [
            quote(key),
            f"(SELECT ident_cely FROM heslar WHERE nazev_heslare={family}{extra} ORDER BY {preference} ident_cely LIMIT 1)",
        ]
    fields += [
        quote("vocabulary_name"),
        "(SELECT nazev FROM heslar_nazev WHERE povolit_zmeny ORDER BY id LIMIT 1)",
        quote("vocabulary_names"),
        "(SELECT jsonb_object_agg(k,v) FROM (VALUES "
        + ",".join(f"({quote(k)},(SELECT nazev FROM heslar_nazev WHERE id={v}))" for k, v in sorted(constants.items()))
        + ") names(k,v))",
        quote("katastr"),
        f"(SELECT 'ruian-'||kod FROM ruian_katastr WHERE {covers('hranice')} ORDER BY kod LIMIT 1)",
        quote("secondary_katastr"),
        "(SELECT 'ruian-'||kod FROM ruian_katastr ORDER BY kod OFFSET 1 LIMIT 1)",
        quote("cadastral_existing_katastr"),
        "(SELECT 'ruian-'||kod FROM ruian_katastr WHERE pian_id IS NOT NULL ORDER BY kod LIMIT 1)",
        quote("cadastral_missing_katastr"),
        "(SELECT 'ruian-'||kod FROM ruian_katastr WHERE pian_id IS NULL ORDER BY kod LIMIT 1)",
        quote("district"),
        "(SELECT 'ruian-'||kod FROM ruian_okres ORDER BY kod LIMIT 1)",
        quote("region"),
        "(SELECT 'ruian-'||kod FROM ruian_kraj ORDER BY kod LIMIT 1)",
        quote("zm10"),
        f"(SELECT cislo FROM kladyzm WHERE kategorie=10 AND {covers('the_geom')} ORDER BY cislo LIMIT 1)",
        quote("zm50"),
        f"(SELECT cislo FROM kladyzm WHERE kategorie=50 AND {covers('the_geom')} ORDER BY cislo LIMIT 1)",
        quote("sm5"),
        f"(SELECT mapno FROM kladysm5 WHERE {covers('geom')} ORDER BY mapno LIMIT 1)",
        quote("group_name"),
        "(SELECT name FROM auth_group ORDER BY name LIMIT 1)",
        quote("notification_type"),
        "(SELECT ident_cely FROM notifikace_typ ORDER BY ident_cely LIMIT 1)",
    ]
    fields += [
        quote("pian_line_type"),
        "(SELECT ident_cely FROM heslar WHERE nazev_heslare=40 AND lower(heslo) LIKE 'lini%' ORDER BY ident_cely LIMIT 1)",
        quote("pian_polygon_type"),
        "(SELECT ident_cely FROM heslar WHERE nazev_heslare=40 AND lower(heslo) LIKE 'ploch%' ORDER BY ident_cely LIMIT 1)",
        quote("cadastral_dj_type"),
        "(SELECT ident_cely FROM heslar WHERE nazev_heslare=34 AND lower(heslo) LIKE '%katastr%' ORDER BY ident_cely LIMIT 1)",
        quote("cadastre_content_type"),
        "(SELECT app_label||'.'||model FROM django_content_type WHERE app_label='heslar' AND model='ruiankatastr')",
        quote("cadastre_db_id"),
        f"(SELECT id FROM ruian_katastr WHERE {covers('hranice')} ORDER BY kod LIMIT 1)",
        quote("cadastre_code"),
        f"(SELECT kod FROM ruian_katastr WHERE {covers('hranice')} ORDER BY kod LIMIT 1)",
        quote("wrong_content_type"),
        "(SELECT app_label||'.'||model FROM django_content_type WHERE app_label='auth' AND model='group')",
    ]
    fields += [
        quote("unused_file_key"),
        "(SELECT 'soub-'||candidate FROM generate_series(2000000000,2000000010) candidate WHERE NOT EXISTS (SELECT 1 FROM soubor WHERE id=candidate) LIMIT 1)",
    ]
    projected = f"ST_Transform({point},5514)"
    fields += [
        quote("point_5514_offset"),
        "ST_AsText(ST_Transform(ST_SetSRID(ST_Point(14.50001,50.00001),4326),5514))",
        quote("elevation_point_5514"),
        f"(SELECT 'POINT Z('||ST_X(p)||' '||ST_Y(p)||' 250.5)' FROM (SELECT {projected} AS p) point)",
        quote("elevation_point_5514_updated"),
        f"(SELECT 'POINT Z('||ST_X(p)||' '||ST_Y(p)||' 251.5)' FROM (SELECT {projected} AS p) point)",
    ]
    reference_queries = {
        "heslar": "SELECT id,ident_cely,nazev_heslare FROM heslar",
        "heslar_nazev": "SELECT id,nazev FROM heslar_nazev",
        "ruian_katastr": f"SELECT id,kod,pian_id FROM ruian_katastr WHERE {covers('hranice')} OR kod IN (SELECT kod FROM ruian_katastr ORDER BY kod LIMIT 2) OR id IN ((SELECT id FROM ruian_katastr WHERE pian_id IS NULL ORDER BY kod LIMIT 1) UNION (SELECT id FROM ruian_katastr WHERE pian_id IS NOT NULL ORDER BY kod LIMIT 1))",
        "ruian_okres": "SELECT id,kod FROM ruian_okres ORDER BY kod LIMIT 2",
        "ruian_kraj": "SELECT id,kod FROM ruian_kraj ORDER BY kod LIMIT 2",
        "kladyzm": f"SELECT gid,cislo,kategorie FROM kladyzm WHERE {covers('the_geom')}",
        "kladysm5": f"SELECT gid,mapno FROM kladysm5 WHERE {covers('geom')}",
        "auth_group": "SELECT id,name FROM auth_group",
        "notifikace_typ": "SELECT id,ident_cely FROM notifikace_typ",
        "django_content_type": "SELECT id,app_label,model FROM django_content_type WHERE model IN ('ruiankatastr','ruianokres','ruiankraj','group')",
    }
    fields += [
        quote("reference_rows"),
        "jsonb_build_object("
        + ",".join(
            quote(table) + ", (SELECT COALESCE(jsonb_agg(to_jsonb(r)),'[]'::jsonb) FROM (" + query + ") r)"
            for table, query in reference_queries.items()
        )
        + ")",
    ]
    # PostgreSQL functions accept at most 100 arguments; keep each object below that.
    objects = ["jsonb_build_object(\n" + ",\n".join(fields[i : i + 80]) + ")" for i in range(0, len(fields), 80)]
    return (
        "-- Export the single JSON value unchanged as references.json (UTF-8).\nBEGIN TRANSACTION READ ONLY;\nSELECT "
        + " || ".join(objects)
        + ";\nCOMMIT;\n"
    )


def schema_sql():
    """Vrátí read-only dotaz na tabulky, sloupce a DB omezení."""
    return """BEGIN TRANSACTION READ ONLY;
SELECT jsonb_build_object(
 'database', current_database(), 'server_version', current_setting('server_version'),
 'columns', (SELECT jsonb_agg(to_jsonb(c)) FROM
   (SELECT table_name,column_name,data_type,is_nullable FROM information_schema.columns
    WHERE table_schema='public' ORDER BY table_name,ordinal_position) c),
 'constraints', (SELECT jsonb_agg(jsonb_build_object('table',conrelid::regclass::text,
   'name',conname,'definition',pg_get_constraintdef(oid))) FROM pg_constraint
   WHERE connamespace='public'::regnamespace)
);
COMMIT;
"""


def operator_sql(identity):
    """Resolve an observed operator's numeric key and role without personal fields."""
    if not re.fullmatch(r"U-\d{6}", identity):
        raise ValueError("Expected the actual U-xxxxxx operator identity")
    return (
        "BEGIN TRANSACTION READ ONLY;\nSELECT jsonb_build_object('captured_at',clock_timestamp(),'operator',"
        + "(SELECT to_jsonb(u) FROM (SELECT id,ident_cely,is_active,is_staff,is_superuser FROM auth_user WHERE ident_cely="
        + quote(identity)
        + ") u));\nCOMMIT;\n"
    )


ROOT_TABLES = {
    "heslar",
    "organizace",
    "osoba",
    "projekt",
    "samostatny_nalez",
    "archeologicky_zaznam",
    "pian",
    "dokumentacni_jednotka",
    "adb",
    "vyskovy_bod",
    "let",
    "dokument",
    "dokument_cast",
    "komponenta",
    "externi_zdroj",
    "auth_user",
}
LINK_OWNERS = {
    "soubor_vazby": [(table, "soubory") for table in ("dokument", "projekt", "samostatny_nalez")],
    "komponenta_vazby": [(table, "komponenty") for table in ("dokumentacni_jednotka", "dokument_cast")],
    "historie_vazby": [
        (table, "historie")
        for table in (
            "dokument",
            "projekt",
            "samostatny_nalez",
            "archeologicky_zaznam",
            "pian",
            "externi_zdroj",
            "auth_user",
            "soubor",
            "uzivatel_spoluprace",
        )
    ],
}
SCOPES = {
    "heslar_datace": "obdobi IN (SELECT id FROM heslar WHERE ident_cely IN ({ids}))",
    "heslar_dokument_typ_material": "dokument_typ IN (SELECT id FROM heslar WHERE ident_cely IN ({ids}))",
    "heslar_hierarchie": "heslo_nadrazene IN (SELECT id FROM heslar WHERE ident_cely IN ({ids})) OR heslo_podrazene IN (SELECT id FROM heslar WHERE ident_cely IN ({ids}))",
    "heslar_odkaz": "heslo IN (SELECT id FROM heslar WHERE ident_cely IN ({ids}))",
    "projekt_katastr": "projekt_id IN (SELECT id FROM projekt WHERE ident_cely IN ({ids}))",
    "oznamovatel": "projekt IN (SELECT id FROM projekt WHERE ident_cely IN ({ids}))",
    "akce": "archeologicky_zaznam IN (SELECT id FROM archeologicky_zaznam WHERE ident_cely IN ({ids}))",
    "lokalita": "archeologicky_zaznam IN (SELECT id FROM archeologicky_zaznam WHERE ident_cely IN ({ids}))",
    "akce_vedouci": "akce IN (SELECT id FROM archeologicky_zaznam WHERE ident_cely IN ({ids}))",
    "archeologicky_zaznam_katastr": "archeologicky_zaznam_id IN (SELECT id FROM archeologicky_zaznam WHERE ident_cely IN ({ids}))",
    "dokument_extra_data": "dokument IN (SELECT id FROM dokument WHERE ident_cely IN ({ids}))",
    "dokument_autor": "dokument IN (SELECT id FROM dokument WHERE ident_cely IN ({ids}))",
    "dokument_jazyk": "dokument IN (SELECT id FROM dokument WHERE ident_cely IN ({ids}))",
    "dokument_osoba": "dokument IN (SELECT id FROM dokument WHERE ident_cely IN ({ids}))",
    "dokument_posudek": "dokument IN (SELECT id FROM dokument WHERE ident_cely IN ({ids}))",
    "tvar": "dokument IN (SELECT id FROM dokument WHERE ident_cely IN ({ids}))",
    "neident_akce": "dokument_cast IN (SELECT id FROM dokument_cast WHERE ident_cely IN ({ids}))",
    "neident_akce_vedouci": "neident_akce IN (SELECT id FROM dokument_cast WHERE ident_cely IN ({ids}))",
    "komponenta_aktivita": "komponenta IN (SELECT id FROM komponenta WHERE ident_cely IN ({ids}))",
    "nalez_objekt": "komponenta IN (SELECT id FROM komponenta WHERE ident_cely IN ({ids}))",
    "nalez_predmet": "komponenta IN (SELECT id FROM komponenta WHERE ident_cely IN ({ids}))",
    "externi_zdroj_autor": "externi_zdroj IN (SELECT id FROM externi_zdroj WHERE ident_cely IN ({ids}))",
    "externi_zdroj_editor": "externi_zdroj IN (SELECT id FROM externi_zdroj WHERE ident_cely IN ({ids}))",
    "externi_odkaz": "externi_zdroj IN (SELECT id FROM externi_zdroj WHERE ident_cely IN ({ids}))",
    "notifikace_projekty_pes": "user_id IN (SELECT id FROM auth_user WHERE ident_cely IN ({ids}))",
    "uzivatel_spoluprace": "vedouci IN (SELECT id FROM auth_user WHERE ident_cely IN ({ids})) OR spolupracovnik IN (SELECT id FROM auth_user WHERE ident_cely IN ({ids}))",
    "auth_user_groups": "user_id IN (SELECT id FROM auth_user WHERE ident_cely IN ({ids}))",
    "auth_user_notifikace_typ": "user_id IN (SELECT id FROM auth_user WHERE ident_cely IN ({ids}))",
}


def snapshot_sql(source, identifiers, baseline=None):
    """Omezí export výhradně na explicitní identifikátory a jejich potomky."""
    values = ",".join("(" + quote(x) + ")" for x in sorted(set(identifiers)))
    requested = (
        "WITH requested(ident_cely) AS (" + ("VALUES " + values if values else "SELECT NULL::text WHERE false") + ")\n"
    )
    ids = "SELECT ident_cely FROM requested"
    file_scope = (
        "vazba IN ("
        + " UNION ".join(
            f"SELECT soubory FROM {table} WHERE ident_cely IN ({{ids}})"
            for table in ["dokument", "projekt", "samostatny_nalez"]
        )
        + ")"
    )
    scopes = dict(SCOPES, soubor=file_scope)
    scopes["ruian_katastr"] = (
        "id IN ("
        + " UNION ".join(
            f"SELECT {column} FROM {table} WHERE ident_cely IN ({{ids}})"
            for table, column in (
                ("projekt", "hlavni_katastr"),
                ("archeologicky_zaznam", "hlavni_katastr"),
                ("samostatny_nalez", "katastr"),
            )
        )
        + ")"
    )
    history_owners = [
        "dokument",
        "projekt",
        "samostatny_nalez",
        "archeologicky_zaznam",
        "pian",
        "externi_zdroj",
        "auth_user",
    ]
    scopes["historie"] = (
        "vazba IN ("
        + " UNION ".join(f"SELECT historie FROM {table} WHERE ident_cely IN ({{ids}})" for table in history_owners)
        + " UNION SELECT historie FROM soubor WHERE "
        + file_scope
        + " UNION SELECT historie FROM uzivatel_spoluprace WHERE "
        + SCOPES["uzivatel_spoluprace"]
        + " UNION SELECT p.historie FROM pian p JOIN dokumentacni_jednotka dj ON dj.pian=p.id WHERE dj.ident_cely IN ({ids}))"
    )
    scopes["historie_vazby"] = scopes["historie"].replace("vazba IN (", "id IN (", 1)
    scopes["soubor_vazby"] = (
        "id IN ("
        + " UNION ".join(
            f"SELECT soubory FROM {table} WHERE ident_cely IN ({{ids}})"
            for table in ("dokument", "projekt", "samostatny_nalez")
        )
        + ")"
    )
    scopes["komponenta_vazby"] = (
        "id IN ("
        + " UNION ".join(
            f"SELECT komponenty FROM {table} WHERE ident_cely IN ({{ids}})"
            for table in ("dokumentacni_jednotka", "dokument_cast")
        )
        + ")"
    )
    tables = {source["models"][m["model"]]["table"] for m in source["mappers"] if m["model"] in source["models"]}
    tables |= set(ROOT_TABLES) | {
        "akce",
        "lokalita",
        "dokument_extra_data",
        "auth_user_groups",
        "auth_user_notifikace_typ",
        "ruian_katastr",
    }
    tables |= set(LINK_OWNERS)
    fields = []
    for table in sorted(tables):
        if not isinstance(table, str) or not re.fullmatch(r"[a-z_]+", table):
            raise ValueError("Unreviewed DB table")
        scope = "ident_cely IN ({ids})" if table in ROOT_TABLES else scopes.get(table)
        if table == "pian":
            scope += " OR id IN (SELECT pian FROM dokumentacni_jednotka WHERE ident_cely IN ({ids}))"
            scope += " OR id IN (SELECT pian_id FROM ruian_katastr WHERE " + scopes["ruian_katastr"] + ")"
        if scope is None:
            raise ValueError(f"No independently authored DB scope for {table}")
        model = next((m for m in source["models"].values() if m["table"] == table), {"fields": {}})
        from .oracle import pk

        key = pk(model)
        frozen = [r[key] for r in (baseline or {}).get(table, []) if isinstance(r.get(key), int)]
        if frozen:
            scope = "(" + scope + ") OR " + key + " IN (" + ",".join(map(str, sorted(set(frozen)))) + ")"
        watermark = (baseline or {}).get("_link_watermarks", {}).get(table)
        if table in LINK_OWNERS and isinstance(watermark, int) and watermark >= 0:
            scope = "(" + scope + ") OR id>" + str(watermark)
        projection = "to_jsonb(t)-'password'-'sha_1'"
        if table in LINK_OWNERS:
            owners = "+".join(
                f"(SELECT count(*) FROM {owner} o WHERE o.{field}=t.id)" for owner, field in LINK_OWNERS[table]
            )
            projection += " || jsonb_build_object('_owner_count'," + owners + ")"
        geometry = {
            name: f
            for name, f in model["fields"].items()
            if f["type"]
            in (
                "GeometryField",
                "PointField",
                "PolygonField",
                "LineStringField",
                "MultiPolygonField",
                "MultiPointField",
                "MultiLineStringField",
            )
        }
        if geometry:
            geo = ",".join(
                quote(name)
                + ",jsonb_build_object('wkt',ST_AsText("
                + name
                + "),'srid',ST_SRID("
                + name
                + "),'valid',ST_IsValid("
                + name
                + "))"
                for name in geometry
            )
            condition = " AND ".join(
                f"({name} IS NULL OR (ST_IsValid({name}) AND ST_SRID({name})={f['srid']}))"
                for name, f in geometry.items()
            )
            if "geom" in geometry and "geom_sjtsk" in geometry:
                condition += " AND ((geom IS NULL AND geom_sjtsk IS NULL) OR (geom IS NOT NULL AND geom_sjtsk IS NOT NULL AND ST_HausdorffDistance(geom,ST_Transform(geom_sjtsk,4326))<0.00001))"
            projection += (
                " || jsonb_build_object('_geometry',jsonb_build_object("
                + geo
                + "),'_geometry_consistent',("
                + condition
                + "))"
            )
        fields.append(
            quote(table) + ", (SELECT COALESCE(jsonb_agg((" + projection + ") ORDER BY to_jsonb(t)::text),'[]'::jsonb) "
            f"FROM {table} t WHERE " + scope.format(ids=ids) + ")"
        )
    fields += [
        "'_provenance',jsonb_build_object('captured_at',clock_timestamp(),'database',current_database(),'snapshot',txid_current_snapshot()::text)"
    ]
    fields += [
        "'_link_watermarks',jsonb_build_object("
        + ",".join(quote(table) + f",(SELECT COALESCE(max(id),0) FROM {table})" for table in LINK_OWNERS)
        + ")"
    ]
    objects = ["jsonb_build_object(\n" + ",\n".join(fields[i : i + 40]) + ")" for i in range(0, len(fields), 40)]
    return (
        "-- Export the single JSON value as db-before.json or db-after.json.\nBEGIN TRANSACTION READ ONLY;\n"
        + requested
        + "SELECT "
        + " || ".join(objects)
        + ";\nCOMMIT;\n"
    )
