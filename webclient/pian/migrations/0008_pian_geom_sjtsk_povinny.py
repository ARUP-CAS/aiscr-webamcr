# Schémová migrace: ``Pian.geom_sjtsk`` se stává povinným (``NOT NULL``),
# stejně jako ``Pian.geom``.
#
# PIAN z principu leží na území ČR, takže JTSK protějšek dává smysl vždy.
# Dokud byl sloupec nullable, procházely DB záznamy bez JTSK a spatial
# dotazy určující katastr (``core.utils.get_all_pians_with_akce`` →
# ``ST_Intersects`` proti ``ruian_katastr.hranice``, od migrace
# ``heslar.0013`` v EPSG:5514) na nich vracely ``NULL``. Katastr se
# nedohledal a připojení pianu k archeologickému záznamu jeho
# ``hlavni_katastr`` tiše neaktualizovalo.
#
# Zároveň se zjednodušuje ``CheckConstraint`` ``pian_geom_check``: původní
# podmínka explicitně povolovala chybějící JTSK u ``geom_system='4326'``,
# což si s novým ``NOT NULL`` odporuje. Její třetí větev (obojí ``NULL``)
# je nadále nesplnitelná a zbylé dvě vždy pravdivé, takže zůstává jen to,
# co má reálnou vypovídací hodnotu – výčet povolených hodnot
# ``geom_system``.

#
# Před zpřísněním sloupce běží dávkový backfill: dokud byl nullable, mohly
# vzniknout řádky s ``geom_sjtsk IS NULL`` (starý ``pian_geom_check`` je
# u ``geom_system='4326'`` výslovně povoloval). ``AlterField`` by na takové
# databázi skončil ``IntegrityError`` – ověřeno na kopii produkční DB, kde
# bylo 213 123 z 213 129 řádků bez JTSK.

import django.contrib.gis.db.models.fields
from django.db import migrations, models


#: Velikost jedné dávky backfillu. Každá dávka je samostatná transakce, po
#: které je práce zapsaná natrvalo – vyšší číslo znamená míň režie, ale delší
#: transakci a víc práce ztracené při případném pádu. 1000 je kompromis
#: ověřený na 258 tisících pianech.
_DAVKA = 1000


def _prepni_trigger(connection, *, zapnout):
    """
    Zapne nebo vypne ``trg_validate_geometries`` v krátké vlastní transakci.

    ``ALTER TABLE`` bere na ``pian`` zámek ``ACCESS EXCLUSIVE``. Držet ho po
    celou dobu backfillu nelze: běh přes stovky tisíc řádků trvá minuty,
    zatímco aplikace má ``statement_timeout=90000`` (viz ``settings.base``)
    a do toho limitu se počítá i čekání na zámek – každý dotaz nad ``pian``
    by po celou dobu nasazení skončil chybou. Přepnutí proto běží samostatně
    a zámek se drží jen na okamžik.

    :param connection: Databázové spojení ze ``schema_editor``.
    :param zapnout: ``True`` zapne trigger, ``False`` ho vypne.
    """
    from django.db import transaction

    smer = "ENABLE" if zapnout else "DISABLE"
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(f"ALTER TABLE pian {smer} TRIGGER trg_validate_geometries")


def _doplnit_geom_sjtsk(apps, schema_editor):
    """
    Dopočítá chybějící ``Pian.geom_sjtsk`` z ``Pian.geom`` (EPSG:4326).

    Používá výhradně ``core.coordTransform.transform_geom_to_sjtsk`` – projekt
    zakazuje ``ST_Transform`` i ``GEOSGeometry.transform()``, aby všechny
    převody procházely jednou aplikační implementací.

    Zapisuje se **raw SQL UPDATE**, ne přes ORM: ``Pian.save()`` spouští
    signály, které zapisují metadata do Fedory. Při migraci je to nežádoucí
    (a nad statisíci řádky neprůchodné).

    Řádky, u kterých transformace selže nebo které nemají ani ``geom``,
    zůstanou prázdné – ``AlterField`` pak skončí chybou a nasazení se zastaví,
    což je správně: tichý default by do dat vnesl nesmyslnou geometrii.

    **Trigger.** Po dobu backfillu je vypnutý ``trg_validate_geometries``.
    Ten je ``BEFORE INSERT OR UPDATE OF geom, geom_sjtsk`` a jeho funkce
    validuje **obě** kolony včetně ``NEW.geom``, kterou tahle migrace vůbec
    nemění. V datech přitom existují starší piany, jejichž ``geom`` dnešní
    ``validategeom`` neuznává (``geometryNotSimple``, ``segmentsTooShort``,
    ``BBox``) – vznikly dřív než ten trigger. Bez vypnutí by první takový
    řádek shodil celou migraci, a tím i nasazení, přestože o zápis nevalidní
    geometrie vůbec nejde.

    Vypnutí, backfill i zapnutí jsou **tři oddělené transakce**, ne jedna.
    Zámek ``ACCESS EXCLUSIVE`` z ``ALTER TABLE`` se tak drží jen na okamžik
    (viz :func:`_prepni_trigger`) a jednotlivé dávky se průběžně commitují,
    takže neúspěch nezahodí celou dosud odvedenou práci. Zapnutí zpět je ve
    ``finally``, takže trigger nezůstane vypnutý ani při chybě uprostřed.
    """
    from core.coordTransform import transform_geom_to_sjtsk

    Pian = apps.get_model("pian", "Pian")
    connection = schema_editor.connection

    _prepni_trigger(connection, zapnout=False)
    try:
        zpracovano, preskoceno = _projed_davky(Pian, connection, transform_geom_to_sjtsk)
    finally:
        _prepni_trigger(connection, zapnout=True)

    if zpracovano or preskoceno:
        print(f"  pian.geom_sjtsk doplnen: {zpracovano}, nepodarilo se: {preskoceno}", flush=True)


def _projed_davky(Pian, connection, transform_geom_to_sjtsk):
    """
    Projde piany bez ``geom_sjtsk`` po dávkách a dopočítá jim hodnotu.

    Každá dávka běží ve vlastní transakci a po jejím konci je zapsaná
    natrvalo. Migrace má proto ``atomic = False`` – jedna společná transakce
    by držela zámky a nevyřízené trigger eventy po celou dobu běhu.

    :param Pian: Historický model ``pian.Pian`` z ``apps.get_model``.
    :param connection: Databázové spojení ze ``schema_editor``.
    :param transform_geom_to_sjtsk: Funkce převodu WKT do EPSG:5514.
    :return: Dvojice ``(zpracovano, preskoceno)``.
    """
    from django.db import transaction

    zpracovano = preskoceno = 0
    while True:
        davka = list(
            Pian.objects.filter(geom_sjtsk__isnull=True, geom__isnull=False)
            .exclude(pk__in=_preskocene)
            .values_list("pk", "geom")[:_DAVKA]
        )
        if not davka:
            break
        with transaction.atomic():
            for pk, geom in davka:
                wkt, stav = transform_geom_to_sjtsk(geom.wkt)
                if stav != "OK" or not wkt:
                    _preskocene.add(pk)
                    preskoceno += 1
                    continue
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE pian SET geom_sjtsk = ST_GeomFromText(%s, 5514) WHERE id = %s",
                        [wkt, pk],
                    )
                zpracovano += 1

    return zpracovano, preskoceno


#: PK řádků, u kterých transformace selhala. Bez nich by se smyčka výš točila
#: donekonečna, protože takový řádek zůstane ``geom_sjtsk IS NULL``.
_preskocene = set()


def _zpet(apps, schema_editor):
    """Zpětný krok backfillu neexistuje – dopočtené hodnoty se nemažou."""


class Migration(migrations.Migration):

    # Backfill (RunPython) a zpřísnění sloupce (AlterField) nesmí běžet
    # v jedné transakci: PostgreSQL by ``ALTER TABLE`` odmítl chybou
    # "cannot ALTER TABLE because it has pending trigger events", protože
    # předchozí hromadné UPDATE nechá ve stejné transakci nevyřízené
    # trigger eventy. S ``atomic = False`` má každá operace transakci vlastní.
    #
    # Backfill je idempotentní (doplňuje jen řádky s ``geom_sjtsk IS NULL``),
    # takže opakované spuštění po případném selhání je bezpečné.
    atomic = False

    dependencies = [
        ("pian", "0007_remove_pian_geom_sjtsk_updated_at_and_more"),
    ]

    operations = [
        migrations.RunPython(_doplnit_geom_sjtsk, _zpet),
        migrations.AlterField(
            model_name="pian",
            name="geom_sjtsk",
            field=django.contrib.gis.db.models.fields.GeometryField(db_index=True, srid=5514),
        ),
        migrations.RemoveConstraint(
            model_name="pian",
            name="pian_geom_check",
        ),
        migrations.AddConstraint(
            model_name="pian",
            constraint=models.CheckConstraint(
                condition=models.Q(("geom_system__in", ["4326", "5514"])),
                name="pian_geom_check",
            ),
        ),
    ]
