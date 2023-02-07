import datetime
from decimal import Decimal

from core.ident_cely import get_dokument_rada, get_temporary_project_ident
from core.models import ProjektSekvence
from core.tests.runner import (
    GEOMETRY_PLOCHA,
    KATASTR_ODROVICE_ID,
    MATERIAL_DOKUMENTU_DIGI_SOUBOR_ID,
    PRESNOST_DESITKY_METRU_ID,
    RADA_DOKUMENTU_TEXT_ID,
    TYP_DOKUMENTU_PLAN_SONDY_ID,
)
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase
from heslar.hesla import TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar, RuianKatastr
from historie.models import HistorieVazby
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
                "01030000208A150000010000000500000040A0C822AEE122C100008294A0F02CC1A03A26F06B0720C100F28414463E2DC180C07FD6894120C1E03D48F6308D2FC1E03A07951E2523C12067B4B38D3E2FC140A0C822AEE122C100008294A0F02CC1"
            ),
        )
        kl.save()
        vazba_pian = HistorieVazby.objects.get(pk=47)
        pian = Pian(
            id=1,
            presnost=Heslar.objects.get(pk=PRESNOST_DESITKY_METRU_ID),
            typ=Heslar.objects.get(pk=GEOMETRY_PLOCHA),
            geom=GEOSGeometry("0101000020E610000042D35729E77F3040234F91EAF9804840"),
            zm10=kl,
            zm50=kl,
            ident_cely="P-3412-900002",
            stav=2,
            historie=vazba_pian,
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
        self.assertEqual(p.ident_cely, f"C-{datetime.datetime.now().year}00001")

    def test_get_temporary_project_ident(self):
        year = datetime.datetime.now().year
        p = Projekt(
            id=1,
        )
        region = "M"
        ident = get_temporary_project_ident(p, region)
        self.assertEqual(ident, f"X-M-{'0' * 8}1")
        p.id = 100000
        ident = get_temporary_project_ident(p, region)
        self.assertEqual(ident, f"X-M-{str(p.id).zfill(9)}")

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
