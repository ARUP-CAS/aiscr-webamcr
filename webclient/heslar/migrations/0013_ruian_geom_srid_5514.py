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
#   1. Po dávkách číst 4326 WKT z DB, transformovat v Pythonu na 5514 WKT
#      a odkládat do dočasné tabulky (viz ``_PRACOVNI_TABULKA``).
#   2. ALTER COLUMN ... TYPE geometry(_, 5514) USING NULL – dočasně
#      vyprázdní typ (data drží dočasná tabulka).
#   3. UPDATE ... ST_GeomFromText(<wkt_5514>, 5514) po dávkách z dočasné
#      tabulky.
#   4. Restore NOT NULL na ``ruian_katastr`` (na kraj/okres je null=True).
#
# Celý krok zůstává v **jedné transakci**: mezi body 2 a 3 nemají tabulky
# geometrii, takže commit uprostřed by při pádu nechal hesláře prázdné.
# Dočasná tabulka je proto ``ON COMMIT DROP`` a data drží databáze, ne
# paměť procesu – původní verze držela WKT všech 13 tisíc katastrů plus
# sjednocené polygony okresů a krajů v Pythonu naráz.
#
# ``backwards`` je symetrický pro downgrade zpět na 4326.

from django.db import migrations
import django.contrib.gis.db.models.fields
from django.utils.translation import gettext_lazy as _


_TABLES = ("ruian_katastr", "ruian_okres", "ruian_kraj")

#: Po kolika řádcích se čte a zapisuje. Jeden ``SELECT`` přes všechny katastry
#: s ``ST_AsText(hranice)`` překračoval ``statement_timeout=90000`` (viz
#: ``settings.base``) – ze stejného důvodu čte po dávkách i samotný syncer,
#: viz komentáře v ``heslar.ruian_sync.syncer``.
_DAVKA = 500

#: Dočasná tabulka, do které se odkládají transformované WKT. Existuje jen
#: uvnitř transakce migrace (``ON COMMIT DROP``).
_PRACOVNI_TABULKA = "_ruian_geom_prevod"

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


def _preved_do_pracovni_tabulky(cursor, table, transform_fn):
    """
    Po dávkách přečte a transformuje geometrie jedné tabulky.

    Výsledné WKT ukládá do :data:`_PRACOVNI_TABULKA`, ne do paměti procesu.
    Čte se keysetem přes ``id``, takže každý ``SELECT`` sáhne jen na dávku
    a nenarazí na ``statement_timeout``.

    :param cursor: Otevřený databázový kurzor.
    :param table: Název zdrojové tabulky.
    :param transform_fn: Funkce převodu WKT mezi soustavami.
    :raises RuntimeError: Když transformace kterékoli geometrie selže –
        pokračovat by znamenalo zapsat do heslářů prázdnou geometrii.
    """
    posledni_id = 0
    while True:
        cursor.execute(
            f"SELECT id, ST_AsText(hranice), ST_AsText(definicni_bod) FROM {table} "
            f"WHERE id > %s ORDER BY id LIMIT %s",
            [posledni_id, _DAVKA],
        )
        rows = cursor.fetchall()
        if not rows:
            return

        prevedene = []
        for row_id, hranice_wkt, def_bod_wkt in rows:
            new_hranice = None
            if hranice_wkt:
                new_hranice, status = transform_fn(hranice_wkt)
                if status != "OK":
                    raise RuntimeError(f"{table}#{row_id} hranice transform failed: {status}")
            new_def_bod = None
            if def_bod_wkt:
                new_def_bod, status = transform_fn(def_bod_wkt)
                if status != "OK":
                    raise RuntimeError(f"{table}#{row_id} definicni_bod transform failed: {status}")
            prevedene.append((table, row_id, new_hranice, new_def_bod))

        cursor.executemany(
            f"INSERT INTO {_PRACOVNI_TABULKA} (tabulka, id, hranice, definicni_bod) VALUES (%s, %s, %s, %s)",
            prevedene,
        )
        posledni_id = rows[-1][0]


def _napln_z_pracovni_tabulky(cursor, table, target_srid):
    """
    Zapíše transformované geometrie zpět po dávkách.

    Aktualizuje se ``UPDATE ... FROM`` proti :data:`_PRACOVNI_TABULKA`, tedy
    množinově po dávkách řádků, ne jedním příkazem na řádek.

    :param cursor: Otevřený databázový kurzor.
    :param table: Název cílové tabulky.
    :param target_srid: Cílový SRID zapisovaných geometrií.
    """
    posledni_id = 0
    while True:
        cursor.execute(
            f"SELECT id FROM {_PRACOVNI_TABULKA} WHERE tabulka = %s AND id > %s ORDER BY id LIMIT %s",
            [table, posledni_id, _DAVKA],
        )
        ids = [r[0] for r in cursor.fetchall()]
        if not ids:
            return

        cursor.execute(
            f"UPDATE {table} t SET "
            f"  hranice = CASE WHEN c.hranice IS NOT NULL "
            f"                 THEN ST_GeomFromText(c.hranice, {target_srid}) ELSE NULL END, "
            f"  definicni_bod = CASE WHEN c.definicni_bod IS NOT NULL "
            f"                       THEN ST_GeomFromText(c.definicni_bod, {target_srid}) ELSE NULL END "
            f"FROM {_PRACOVNI_TABULKA} c "
            f"WHERE c.tabulka = %s AND c.id = t.id AND t.id = ANY(%s)",
            [table, ids],
        )
        posledni_id = ids[-1]


def _transform_all(apps, schema_editor, transform_fn, target_srid):
    """
    Sdílená implementace forwards/backwards migrace RÚIAN geometrií.

    Přečte ``hranice``/``definicni_bod`` z ``ruian_*`` tabulek, transformuje
    v Pythonu přes ``transform_fn``, vypustí a naplní zpět v novém SRID.
    Na konci obnoví GiST indexy zahozené při ``ALTER COLUMN TYPE`` (viz
    :func:`_recreate_spatial_indexes`).

    Čtení i zápis běží po dávkách přes dočasnou tabulku – zdůvodnění viz
    :data:`_DAVKA` a komentář v hlavičce modulu.

    :param apps: Historický app registry (pro :func:`_recreate_spatial_indexes`).
    :param schema_editor: Django schema editor s aktivním connection.
    :param transform_fn: ``core.coordTransform.transform_geom_to_sjtsk`` nebo
        ``transform_geom_to_wgs84``.
    :param target_srid: Cílový SRID (5514 pro forwards, 4326 pro backwards).
    """
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE TEMPORARY TABLE {_PRACOVNI_TABULKA} ("
            f"  tabulka text NOT NULL, id integer NOT NULL,"
            f"  hranice text, definicni_bod text,"
            f"  PRIMARY KEY (tabulka, id)"
            f") ON COMMIT DROP"
        )
        for table in _TABLES:
            _preved_do_pracovni_tabulky(cursor, table, transform_fn)

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

        for table in _TABLES:
            _napln_z_pracovni_tabulky(cursor, table, target_srid)

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
