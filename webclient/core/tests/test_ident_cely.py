import datetime

from core.ident_cely import (
    get_ident_consecutive_number,
    get_region_from_cadastre,
    get_temporary_project_ident,
)
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase
from heslar import hesla
from heslar.models import Heslar, HeslarNazev, RuianKatastr, RuianKraj, RuianOkres

# from pian.models import Pian
from projekt.models import Projekt


class IdentTests(TestCase):
    def setUp(self):
        hn = HeslarNazev(nazev="Typy projektu")
        hn.save()
        h = Heslar(id=hesla.PROJEKT_ZACHRANNY_ID, nazev_heslare=hn)
        h.save()

    def test_get_permanent_project_ident(self):
        # TODO
        pass

    def test_get_temporary_project_ident(self):
        year = datetime.datetime.now().year
        p = Projekt(
            id=1,
        )
        region = "M"
        ident = get_temporary_project_ident(p, region)
        self.assertEqual(ident, "X-M-" + str(year) + "00001")
        p.id = 100000
        ident = get_temporary_project_ident(p, region)
        self.assertEqual(ident, "X-M-" + str(year) + "00000")

    def test_get_region_from_cadastre(self):
        # TODO insert valid PIAN record and move all of the inserts to the setup method
        # pian = Pian(
        #
        # )
        kraj = RuianKraj(nazev="Hlavní město Praha", rada_id="C", kod=1)
        okres = RuianOkres(nazev="Testovy okres", kraj=kraj, spz="spz", kod=2)
        katastr = RuianKatastr(
            nazev="Testovaci katastr",
            okres=okres,
            kod=3,
            aktualni=True,
            definicni_bod=GEOSGeometry(
                "0101000020E610000042D35729E77F3040234F91EAF9804840"
            ),
        )
        kraj.save()
        okres.save()
        katastr.save()
        region = get_region_from_cadastre(katastr)
        self.assertEqual(region, "C")

    def test_get_ident_consecutive_number(self):
        # Insert some projects to the database
        zachranny_typ_projektu = Heslar.objects.get(id=hesla.PROJEKT_ZACHRANNY_ID)
        Projekt(
            stav=0, typ_projektu=zachranny_typ_projektu, ident_cely="M-202000003"
        ).save()
        Projekt(
            stav=0, typ_projektu=zachranny_typ_projektu, ident_cely="M-202000002"
        ).save()
        number = get_ident_consecutive_number("M", 2020)
        self.assertEqual(number, 4)
        Projekt(
            stav=0, typ_projektu=zachranny_typ_projektu, ident_cely="M-202000006"
        ).save()
        number = get_ident_consecutive_number("M", 2020)
        self.assertEqual(number, 7)
