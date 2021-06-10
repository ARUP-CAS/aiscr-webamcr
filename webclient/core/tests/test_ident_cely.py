import datetime
from decimal import Decimal

from core.ident_cely import get_dokument_rada, get_temporary_project_ident
from core.models import ProjektSekvence
from core.tests.runner import (
    KATASTR_ODROVICE_ID,
    MATERIAL_DOKUMENTU_DIGI_SOUBOR_ID,
    PRESNOST_DESITKY_METRU_ID,
    RADA_DOKUMENTU_TEXT_ID,
    TYP_DOKUMENTU_PLAN_SONDY_ID,
    TYP_PIAN_PLOCHA_ID,
)
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase
from heslar.hesla import TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar, RuianKatastr
from pian.models import Kladyzm, Pian
from projekt.models import Projekt


class IdentTests(TestCase):
    def setUp(self):
        kl = Kladyzm(
            gid=1,
            objectid=1,
            kategorie=1,
            cislo="03",
            nazev="Vejprty",
            natoceni=Decimal(8.78330000000),
            shape_leng=Decimal(341204.736390),
            shape_area=Decimal(7189599966.71),
            the_geom=GEOSGeometry(
                "0106000020B38E01000100000001030000000100000005000000A0103FF6D3672BC1A08E29DB"
                "A8C22BC1E06C309E109228C1408F6DE6CB322CC1C0C9EDA718E828C180504AA34C7E2EC10037"
                "0FD61FC72BC1C0252A1EBB0C2EC1A0103FF6D3672BC1A08E29DBA8C22BC1"
            ),
        )
        kl.save()
        pian = Pian(
            id=1,
            presnost=Heslar.objects.get(pk=PRESNOST_DESITKY_METRU_ID),
            typ=Heslar.objects.get(pk=TYP_PIAN_PLOCHA_ID),
            geom=GEOSGeometry("0101000020E610000042D35729E77F3040234F91EAF9804840"),
            zm10=kl,
            zm50=kl,
            ident_cely="P-3412-900002",
            stav=2,
        )
        pian.save()

    def test_get_permanent_project_ident(self):
        p = Projekt(
            stav=0,
            typ_projektu=Heslar.objects.get(pk=TYP_PROJEKTU_ZACHRANNY_ID),
            hlavni_katastr=RuianKatastr.objects.get(id=150),
        )
        p.save()

        p.set_permanent_ident_cely()
        p.save()
        self.assertEqual(p.ident_cely, "C-202100001")

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

    def test_get_permanent_ident(self):
        # Insert some projects to the database
        year = datetime.datetime.now().year
        zachranny_typ_projektu = Heslar.objects.get(pk=TYP_PROJEKTU_ZACHRANNY_ID)
        katastr_odrovice = RuianKatastr.objects.get(id=KATASTR_ODROVICE_ID)
        Projekt(
            stav=0,
            typ_projektu=zachranny_typ_projektu,
            ident_cely="C-X-202000003",
            hlavni_katastr=katastr_odrovice,
        ).save()
        p = Projekt(
            stav=0,
            typ_projektu=zachranny_typ_projektu,
            ident_cely="C-X-202000002",
            hlavni_katastr=katastr_odrovice,
        )
        p.save()
        p.set_permanent_ident_cely()
        self.assertEqual(p.ident_cely, "C-" + str(year) + "00001")
        s = ProjektSekvence.objects.filter(rok=year).filter(rada="C")[0]
        # Over ze se sekvence inkrementla
        self.assertEqual(s.sekvence, 2)

    def test_get_dokument_rada(self):
        material = Heslar.objects.get(id=MATERIAL_DOKUMENTU_DIGI_SOUBOR_ID)
        typ = Heslar.objects.get(id=TYP_DOKUMENTU_PLAN_SONDY_ID)
        rada = get_dokument_rada(typ, material)
        self.assertEqual(rada.id, RADA_DOKUMENTU_TEXT_ID)
