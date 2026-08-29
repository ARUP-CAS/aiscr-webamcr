# Generated for issue #372 (přechod katastrů na primární JTSK / EPSG:5514)
#
# Migrace transformuje geometrické sloupce ``hranice`` a ``definicni_bod``
# u ``RuianKatastr``, ``RuianOkres`` a ``RuianKraj`` z EPSG:4326 (WGS84)
# na EPSG:5514 (S-JTSK Krovak East-North).
#
# CRS transformace probíhá **aplikačně** přes ``core.coordTransform``
# (`transform_geom_to_sjtsk` / `transform_geom_to_wgs84`). PostGIS
# ``ST_Transform`` se v projektu záměrně nepoužívá – projekt má vlastní
# implementaci pro Python i JavaScript a je nutná konzistence.
#
# Postup:
#   1. Cache 4326 WKT z DB → transform v Pythonu na 5514 WKT.
#   2. ALTER COLUMN ... TYPE geometry(_, 5514) USING NULL – dočasně
#      vyprázdní typ (data drží cache).
#   3. UPDATE ... ST_GeomFromText(<wkt_5514>, 5514) – naplní z cache.
#   4. Restore NOT NULL na ``ruian_katastr`` (na kraj/okres je null=True).
#
# ``backwards`` je symetrický pro downgrade zpět na 4326.

from django.db import migrations
import django.contrib.gis.db.models.fields
from django.utils.translation import gettext_lazy as _


_TABLES = ("ruian_katastr", "ruian_okres", "ruian_kraj")

#: Modely odpovídající tabulkám v ``_TABLES``. Potřebné pro znovuvytvoření
#: GiST indexů po ALTER COLUMN TYPE (viz :func:`_recreate_spatial_indexes`).
_MODEL_NAMES = ("RuianKatastr", "RuianOkres", "RuianKraj")
_SPATIAL_COLUMNS = ("hranice", "definicni_bod")


def _recreate_spatial_indexes(apps, schema_editor):
    """
    Znovu vytvoří GiST indexy na ``hranice``/``definicni_bod``.

    ``ALTER COLUMN ... TYPE geometry(...) USING ...`` (viz :func:`_transform_all`)
    přetypuje typmod geometrického sloupce a při tom v PostGIS zahodí
    existující GiST index, aniž by ho sám obnovil. Django's
    ``PostGISSchemaEditor._alter_field`` index řeší jen při změně
    booleovského ``spatial_index`` flagu (viz jeho zdrojový kód) – ten se
    v této migraci nemění (zůstává ``True``), takže se o obnovu indexu
    nepostará. 

    :param apps: Historický app registry (poskytuje ``RunPython``).
    :param schema_editor: Aktivní schema editor (poskytuje ``RunPython``).
    """
    for model_name in _MODEL_NAMES:
        model = apps.get_model("heslar", model_name)
        for column in _SPATIAL_COLUMNS:
            try:
                field = model._meta.get_field(column)
            except Exception:
                continue
            if not getattr(field, "spatial_index", False):
                continue
            index_name = schema_editor._create_spatial_index_name(model, field)
            schema_editor.execute(f"DROP INDEX IF EXISTS {index_name}")
            schema_editor.execute(schema_editor._create_spatial_index_sql(model, field))


def _transform_all(apps, schema_editor, transform_fn, target_srid):
    """
    Sdílená implementace forwards/backwards migrace RÚIAN geometrií.

    Přečte ``hranice``/``definicni_bod`` z ``ruian_*`` tabulek, transformuje
    v Pythonu přes ``transform_fn``, vypustí a naplní zpět v novém SRID.
    Na konci obnoví GiST indexy zahozené při ``ALTER COLUMN TYPE`` (viz
    :func:`_recreate_spatial_indexes`).

    :param apps: Historický app registry (pro :func:`_recreate_spatial_indexes`).
    :param schema_editor: Django schema editor s aktivním connection.
    :param transform_fn: ``core.coordTransform.transform_geom_to_sjtsk`` nebo
        ``transform_geom_to_wgs84``.
    :param target_srid: Cílový SRID (5514 pro forwards, 4326 pro backwards).
    """
    connection = schema_editor.connection

    cache = {}
    for table in _TABLES:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT id, ST_AsText(hranice), ST_AsText(definicni_bod) FROM {table}"
            )
            rows = cursor.fetchall()

        transformed = []
        for row_id, hranice_wkt, def_bod_wkt in rows:
            new_hranice = None
            if hranice_wkt:
                new_hranice, status = transform_fn(hranice_wkt)
                if status != "OK":
                    raise RuntimeError(
                        f"{table}#{row_id} hranice transform failed: {status}"
                    )
            new_def_bod = None
            if def_bod_wkt:
                new_def_bod, status = transform_fn(def_bod_wkt)
                if status != "OK":
                    raise RuntimeError(
                        f"{table}#{row_id} definicni_bod transform failed: {status}"
                    )
            transformed.append((row_id, new_hranice, new_def_bod))
        cache[table] = transformed

    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE ruian_katastr "
            "ALTER COLUMN hranice DROP NOT NULL, "
            "ALTER COLUMN definicni_bod DROP NOT NULL;"
        )
        for table in _TABLES:
            cursor.execute(
                f"ALTER TABLE {table} "
                f"ALTER COLUMN hranice TYPE geometry(MultiPolygon, {target_srid}) USING NULL, "
                f"ALTER COLUMN definicni_bod TYPE geometry(Point, {target_srid}) USING NULL;"
            )

        for table, rows in cache.items():
            for row_id, new_hranice_wkt, new_def_bod_wkt in rows:
                cursor.execute(
                    f"UPDATE {table} SET "
                    f"  hranice = CASE WHEN %s IS NOT NULL "
                    f"                 THEN ST_GeomFromText(%s, {target_srid}) ELSE NULL END, "
                    f"  definicni_bod = CASE WHEN %s IS NOT NULL "
                    f"                       THEN ST_GeomFromText(%s, {target_srid}) ELSE NULL END "
                    f"WHERE id = %s",
                    [
                        new_hranice_wkt, new_hranice_wkt,
                        new_def_bod_wkt, new_def_bod_wkt,
                        row_id,
                    ],
                )

        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE;")
        cursor.execute(
            "ALTER TABLE ruian_katastr "
            "ALTER COLUMN hranice SET NOT NULL, "
            "ALTER COLUMN definicni_bod SET NOT NULL;"
        )

    _recreate_spatial_indexes(apps, schema_editor)


def forwards(apps, schema_editor):
    """
    Přetransformuje RÚIAN geometrie z EPSG:4326 na EPSG:5514.
    """
    from core.coordTransform import transform_geom_to_sjtsk

    _transform_all(apps, schema_editor, transform_geom_to_sjtsk, 5514)


def backwards(apps, schema_editor):
    """
    Downgrade – přetransformuje RÚIAN geometrie z EPSG:5514 zpět na EPSG:4326.
    """
    from core.coordTransform import transform_geom_to_wgs84

    _transform_all(apps, schema_editor, transform_geom_to_wgs84, 4326)


class Migration(migrations.Migration):

    dependencies = [
        ("heslar", "0012_ruiansyncrun"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name="ruiankatastr",
            name="definicni_bod",
            field=django.contrib.gis.db.models.fields.PointField(
                srid=5514,
                verbose_name=_("heslar.models.RuianKatastr.definicni_bod"),
            ),
        ),
        migrations.AlterField(
            model_name="ruiankatastr",
            name="hranice",
            field=django.contrib.gis.db.models.fields.MultiPolygonField(
                srid=5514,
                verbose_name=_("heslar.models.RuianKatastr.hranice"),
            ),
        ),
        migrations.AlterField(
            model_name="ruiankraj",
            name="definicni_bod",
            field=django.contrib.gis.db.models.fields.PointField(
                null=True,
                srid=5514,
                verbose_name=_("heslar.models.RuianKatastr.definicni_bod"),
            ),
        ),
        migrations.AlterField(
            model_name="ruiankraj",
            name="hranice",
            field=django.contrib.gis.db.models.fields.MultiPolygonField(
                null=True,
                srid=5514,
                verbose_name=_("heslar.models.RuianKatastr.hranice"),
            ),
        ),
        migrations.AlterField(
            model_name="ruianokres",
            name="definicni_bod",
            field=django.contrib.gis.db.models.fields.PointField(
                null=True,
                srid=5514,
                verbose_name=_("heslar.models.RuianKatastr.definicni_bod"),
            ),
        ),
        migrations.AlterField(
            model_name="ruianokres",
            name="hranice",
            field=django.contrib.gis.db.models.fields.MultiPolygonField(
                null=True,
                srid=5514,
                verbose_name=_("heslar.models.RuianKatastr.hranice"),
            ),
        ),
    ]
