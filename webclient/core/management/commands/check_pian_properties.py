import logging

from core.repository_connector import FedoraTransaction
from django.contrib.gis.db.models.functions import Centroid
from django.contrib.gis.geos import GeometryCollection, LineString, MultiPolygon, Point, Polygon
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro kontrolu a opravu vlastností PIANů.

    Tento příkaz kontroluje a případně opravuje:

    - Typ geometrie (typ) - musí odpovídat skutečnému typu geometrie (bod/linie/plocha)
    - Základní mapy ZM10 a ZM50 - určí se podle pozice geometrie

    Pro každý PIAN:

    - Ověří, zda typ geometrie odpovídá skutečnosti
    - Vypočítá reprezentativní bod geometrie (střed u linie, centroid u plochy)
    - Určí příslušnost k základním mapám ZM10 a ZM50
    - Pokud se některá hodnota liší, provede aktualizaci

    Poznámka:
        - Aktualizace jsou prováděny včetně Fedora transakcí a metadat
        - Proces může trvat delší dobu v závislosti na počtu PIANů

    Příklady použití::

        python manage.py check_pian_properties
    """

    help = _("core.management.commands.check_pian_properties.Command.help")

    def handle(self, *args, **options):
        """Zpracuje argumenty příkazu a zkontroluje konzistenci vlastností PIAN.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param options: Dodatečné pojmenované argumenty předané voláním.
        :return: Vrací výsledek provedené operace.
        """
        from heslar.hesla_dynamicka import GEOMETRY_BOD, GEOMETRY_LINIE, GEOMETRY_PLOCHA
        from heslar.models import Heslar
        from pian.models import Pian, get_ZM_from_point

        logger.debug("core.management.commands.check_pian_properties.start")

        # Připraví mapování tříd geometrií na odpovídající heslářové hodnoty typu.
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

        self.stdout.write(_("core.management.commands.check_pian_properties.total_pian") + " " + str(pocet_pians))
        self.stdout.write(_("core.management.commands.check_pian_properties.processing_pian"))
        self.stdout.write("")

        for item in query.iterator(chunk_size=1000):
            save = False
            changes = []
            geom = item.geom

            # Ověří, zda uložený typ odpovídá skutečnému typu geometrie.
            if item.typ.pk != geom_type[str(type(geom))].pk:
                old_typ = str(item.typ)
                item.typ = geom_type[str(type(geom))]
                save = True
                changes.append(
                    _("core.management.commands.check_pian_properties.change_typ")
                    + " "
                    + old_typ
                    + " -> "
                    + str(item.typ)
                )

            # Calculate representative point based on geometry type
            if isinstance(geom, Point):
                point = geom
            elif isinstance(geom, LineString):
                point = geom.interpolate_normalized(0.5)
            else:
                point = Centroid(geom)

            # Zkontroluje ZM10 a ZM50.
            zm10, zm50 = get_ZM_from_point(point)
            if zm10 is not None and zm50 is not None:
                if item.zm10.pk != zm10.pk:
                    old_zm10 = str(item.zm10)
                    item.zm10 = zm10
                    save = True
                    changes.append(
                        _("core.management.commands.check_pian_properties.change_zm10")
                        + " "
                        + old_zm10
                        + " -> "
                        + str(zm10)
                    )
                if item.zm50.pk != zm50.pk:
                    old_zm50 = str(item.zm50)
                    item.zm50 = zm50
                    save = True
                    changes.append(
                        _("core.management.commands.check_pian_properties.change_zm50")
                        + " "
                        + old_zm50
                        + " -> "
                        + str(zm50)
                    )

            # Uloží pouze pokud došlo ke změnám.
            if save is True:
                pocet_zmenenych += 1
                self.stdout.write(
                    "\r"
                    + _("core.management.commands.check_pian_properties.changed")
                    + " "
                    + str(pocet_zmenenych)
                    + " | "
                    + _("core.management.commands.check_pian_properties.processed")
                    + " "
                    + str(index)
                    + "/"
                    + str(pocet_pians)
                    + " | "
                    + _("core.management.commands.check_pian_properties.pian")
                    + " "
                    + str(item.pk)
                    + ": "
                    + ", ".join(changes),
                    ending="",
                )

                fedora_transaction = FedoraTransaction()
                item.active_transaction = fedora_transaction
                item.update_all_azs = False
                item.close_active_transaction_when_finished = True
                item.save()

            index += 1

            # Pravidelně vypisuje průběh i bez změn.
            if index % 100 == 0:
                self.stdout.write(
                    "\r"
                    + _("core.management.commands.check_pian_properties.changed")
                    + " "
                    + str(pocet_zmenenych)
                    + " | "
                    + _("core.management.commands.check_pian_properties.processed")
                    + " "
                    + str(index)
                    + "/"
                    + str(pocet_pians),
                    ending="",
                )

        self.stdout.write("")
        self.stdout.write("")

        logger.debug(
            "core.management.commands.check_pian_properties.end",
            extra={"total": pocet_pians, "changed": pocet_zmenenych},
        )

        self.stdout.write("=" * 50)
        self.stdout.write(_("core.management.commands.check_pian_properties.total_processed") + " " + str(pocet_pians))
        self.stdout.write(
            _("core.management.commands.check_pian_properties.changed_count") + " " + str(pocet_zmenenych)
        )
        self.stdout.write("=" * 50)
        self.stdout.write("")

        if pocet_zmenenych > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    _("core.management.commands.check_pian_properties.finished_fixed")
                    + " "
                    + str(pocet_zmenenych)
                    + " "
                    + _("core.management.commands.check_pian_properties.of_total")
                    + " "
                    + str(pocet_pians)
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(_("core.management.commands.check_pian_properties.finished_no_changes"))
            )
