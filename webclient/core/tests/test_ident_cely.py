import datetime
from decimal import Decimal

from core.ident_cely import (
    get_ident_consecutive_number,
    get_permanent_project_ident,
    get_region_from_cadastre,
    get_temporary_project_ident,
)
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase
from heslar.hesla import (
    PRESNOST_DESITKY_METRU_ID,
    TYP_PIAN_PLOCHA_ID,
    TYP_PROJEKTU_ZACHRANNY_ID,
)
from heslar.models import Heslar, RuianKatastr
from pian.models import Kladyzm, Pian
from projekt.models import Projekt


class IdentTests(TestCase):
    def setUp(self):
        kl = Kladyzm(
            gid=1,
            objectid=1,
            kategorie=1,
            cislo="01",
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
            buffer=GEOSGeometry(
                "0106000020E610000001000000010300000001000000130000006E6F8E0B8E84304091B2E4D544"
                "8248401F1E93480586304064D23AA54D814840D3819AAF5E863040D2583431DC804840A294390E6"
                "F843040DAE2ADDC72804840862715C5D883304025CEA19C628048400FD982CE3D833040E868346F"
                "5E80484040B173420C7E304018B719A61B8048402B66119F397830409FD10A33C97F484092BAF06"
                "2A4783040827C4FCB55804840FA5C963DC87A3040C3E02EA9E18048408C9A8056D17A3040B9BFA4"
                "1AE6804840BD35778B877C304027BB3E2B83814840B088D6301E813040901D47D7218248409E2B3"
                "B911E813040566325BF258248401ED53C6D73813040739AD6F82F8248400816E571C0813040542C"
                "604C13824840178B9F59228230409A127179028248409D0CB7BE598230403D43D4B3EF8148406E6"
                "F8E0B8E84304091B2E4D544824840"
            ),
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

        ident = get_permanent_project_ident(p)
        self.assertEqual(ident, "C-202100001")

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
        region = get_region_from_cadastre(RuianKatastr.objects.get(id=150))
        self.assertEqual(region, "C")

    def test_get_ident_consecutive_number(self):
        # Insert some projects to the database
        zachranny_typ_projektu = Heslar.objects.get(pk=TYP_PROJEKTU_ZACHRANNY_ID)
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
