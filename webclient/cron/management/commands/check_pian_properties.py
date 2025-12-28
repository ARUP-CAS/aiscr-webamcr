import logging

from core.repository_connector import FedoraTransaction
from django.contrib.gis.db.models.functions import Centroid
from django.contrib.gis.geos import GeometryCollection, LineString, MultiPolygon, Point, Polygon
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro kontrolu a opravu vlastností PIANů.

    Tento příkaz kontroluje a případně opravuje:
    1. Typ geometrie (typ) - musí odpovídat skutečnému typu geometrie (bod/linie/plocha)
    2. Základní mapy ZM10 a ZM50 - určí se podle pozice geometrie

    Pro každý PIAN:
    - Ověří, zda typ geometrie odpovídá skutečnosti
    - Vypočítá reprezentativní bod geometrie (střed u linie, centroid u plochy)
    - Určí příslušnost k základním mapám ZM10 a ZM50
    - Pokud se některá hodnota liší, provede aktualizaci

    Poznámka:
        Aktualizace jsou prováděny včetně Fedora transakcí a metadat.
        Proces může trvat delší dobu v závislosti na počtu PIANů.

    Příklad použití:
        python manage.py check_pian_properties
    """

    help = "Kontrola a oprava vlastností PIANů (typ geometrie, ZM10, ZM50)"

    def handle(self, *args, **options):
        from heslar.hesla_dynamicka import GEOMETRY_BOD, GEOMETRY_LINIE, GEOMETRY_PLOCHA
        from heslar.models import Heslar
        from pian.models import Pian, get_ZM_from_point

        logger.debug("cron.management.commands.check_pian_properties.start")

        # Prepare geometry type mapping
        geom_type = {}
        geom_type[str(Point)] = Heslar.objects.get(id=GEOMETRY_BOD)
        geom_type[str(LineString)] = Heslar.objects.get(id=GEOMETRY_LINIE)
        geom_type[str(Polygon)] = Heslar.objects.get(id=GEOMETRY_PLOCHA)
        geom_type[str(MultiPolygon)] = Heslar.objects.get(id=GEOMETRY_PLOCHA)
        geom_type[str(GeometryCollection)] = Heslar.objects.get(id=GEOMETRY_PLOCHA)

        query = Pian.objects.all()
        pocet_zmenenych = 0
        pocet_pians = query.count()
        index = 0

        self.stdout.write(f"Celkový počet PIANů: {pocet_pians}")
        self.stdout.write("Zpracovávám PIANy...")
        self.stdout.write("")

        for item in query.iterator(chunk_size=1000):
            save = False
            changes = []
            geom = item.geom

            # Check geometry type
            if item.typ.pk != geom_type[str(type(geom))].pk:
                old_typ = item.typ.nazev
                item.typ = geom_type[str(type(geom))]
                save = True
                changes.append(f"typ: {old_typ} -> {item.typ.nazev}")

            # Calculate representative point based on geometry type
            if isinstance(geom, Point):
                point = geom
            elif isinstance(geom, LineString):
                point = geom.interpolate_normalized(0.5)
            else:
                point = Centroid(geom)

            # Check ZM10 and ZM50
            zm10, zm50 = get_ZM_from_point(point)
            if zm10 is not None and zm50 is not None:
                if item.zm10.pk != zm10.pk:
                    old_zm10 = item.zm10.nazev
                    item.zm10 = zm10
                    save = True
                    changes.append(f"ZM10: {old_zm10} -> {zm10.nazev}")
                if item.zm50.pk != zm50.pk:
                    old_zm50 = item.zm50.nazev
                    item.zm50 = zm50
                    save = True
                    changes.append(f"ZM50: {old_zm50} -> {zm50.nazev}")

            # Save if there were changes
            if save is True:
                pocet_zmenenych += 1
                self.stdout.write(
                    f"\rZměněno: {pocet_zmenenych} | Zpracováno: {index}/{pocet_pians} | "
                    f"PIAN {item.pk}: {', '.join(changes)}",
                    ending="",
                )

                fedora_transaction = FedoraTransaction()
                item.active_transaction = fedora_transaction
                item.update_all_azs = False
                item.close_active_transaction_when_finished = True
                item.save()

            index += 1

            # Show periodic progress even when no changes
            if index % 100 == 0:
                self.stdout.write(
                    f"\rZměněno: {pocet_zmenenych} | Zpracováno: {index}/{pocet_pians}",
                    ending="",
                )

        self.stdout.write("")
        self.stdout.write("")

        logger.debug(
            "cron.management.commands.check_pian_properties.end",
            extra={"total": pocet_pians, "changed": pocet_zmenenych},
        )

        self.stdout.write("=" * 50)
        self.stdout.write(f"Celkem zpracováno PIANů: {pocet_pians}")
        self.stdout.write(f"Počet PIANů se změnami:  {pocet_zmenenych}")
        self.stdout.write("=" * 50)
        self.stdout.write("")

        if pocet_zmenenych > 0:
            self.stdout.write(self.style.SUCCESS(f"Dokončeno. Opraveno {pocet_zmenenych} PIANů z {pocet_pians}"))
        else:
            self.stdout.write(self.style.SUCCESS("Dokončeno. Žádné změny nebyly nutné"))
