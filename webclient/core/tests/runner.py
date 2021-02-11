from arch_z.models import Akce, ArcheologickyZaznam
from core.constants import AZ_STAV_ZAPSANY
from django.contrib.gis.geos import GEOSGeometry
from django.test.runner import DiscoverRunner as BaseRunner
from heslar import hesla
from heslar.hesla import PRISTUPNOST_ANONYM_ID
from heslar.models import Heslar, HeslarNazev, RuianKatastr, RuianKraj, RuianOkres
from uzivatel.models import Organizace, User

# Konstanty pouzite v testech
PRESNOST_DESITKY_METRU_ID = 56
PRESNOST_JEDNOTKY_METRU_ID = 567
PRESNOST_POLOHA_PODLE_KATASTRU_ID = 1150
PRESNOST_STOVKY_METRU_ID = 1213

TYP_ORGANIZACE_USTAV_PAMATKOVE_PECE_ID = 852
TYP_ORGANIZACE_MUZEUM_ID = 342
TYP_ORGANIZACE_TERENNI_PRACOVISTE_ID = 710
TYP_ORGANIZACE_UNIVERZITA_ID = 487
TYP_ORGANIZACE_VYZKUMNA_INSTITUCE_ID = 581
TYP_ORGANIZACE_OSTATNI_ID = 110

TYP_PIAN_PLOCHA_ID = 476
TYP_PIAN_LINIE_ID = 1206
TYP_PIAN_BOD_ID = 58


def add_middleware_to_request(request, middleware_class):
    middleware = middleware_class()
    middleware.process_request(request)
    return request


def add_middleware_to_response(request, middleware_class):
    middleware = middleware_class()
    middleware.process_response(request)
    return request


class AMCRMixinRunner(object):
    def setup_databases(self, *args, **kwargs):
        temp_return = super(AMCRMixinRunner, self).setup_databases(*args, **kwargs)
        print("Setting up my database content ...")

        kraj_praha = RuianKraj(id=84, nazev="Hlavní město Praha", rada_id="C", kod=1)
        kraj_brno = RuianKraj(id=85, nazev="Jihomoravský kraj", rada_id="C", kod=2)
        okres_praha = RuianOkres(
            id=162, nazev="Praha", kraj=kraj_brno, spz="spz", kod=3
        )
        okres_brno_venkov = RuianOkres(
            id=163, nazev="Brno-venkov", kraj=kraj_brno, spz="spz", kod=4
        )
        odrovice = RuianKatastr(
            id=150,
            nazev="ODROVICE",
            okres=okres_brno_venkov,
            kod=3,
            aktualni=True,
            definicni_bod=GEOSGeometry(
                "0101000020E610000042D35729E77F3040234F91EAF9804840"
            ),
            hranice=GEOSGeometry(
                "0106000020E610000001000000010300000001000000130000006E6F8E0B8E84304091B2E4D54"
                "48248401F1E93480586304064D23AA54D814840D3819AAF5E863040D2583431DC804840A29439"
                "0E6F843040DAE2ADDC72804840862715C5D883304025CEA19C628048400FD982CE3D833040E86"
                "8346F5E80484040B173420C7E304018B719A61B8048402B66119F397830409FD10A33C97F4840"
                "92BAF062A4783040827C4FCB55804840FA5C963DC87A3040C3E02EA9E18048408C9A8056D17A3"
                "040B9BFA41AE6804840BD35778B877C304027BB3E2B83814840B088D6301E813040901D47D721"
                "8248409E2B3B911E813040566325BF258248401ED53C6D73813040739AD6F82F8248400816E571"
                "C0813040542C604C13824840178B9F59228230409A127179028248409D0CB7BE598230403D43D"
                "4B3EF8148406E6F8E0B8E84304091B2E4D544824840"
            ),
            pian=1,
        )
        praha = RuianKatastr(
            id=149,
            nazev="JOSEFOV",
            okres=okres_praha,
            kod=3,
            aktualni=True,
            definicni_bod=GEOSGeometry(
                "0101000020E61000006690F8F089D62C40957C231E2F0B4940"
            ),
            hranice=GEOSGeometry(
                "0106000020E61000000100000001030000000100000013000000ED2BF5120ED62C40E95C8F63"
                "BA0B4940A88DBA2A20D62C40D963192CBC0B49401E0BE95D66D62C40BB04E9FBA20B4940A704"
                "40B545D72C408828418EAA0B49408247C41C53D72C400A133A839B0B49408AF95C4B9CD72C40"
                "D57BA3289D0B494099ABFAC0BBD72C406D51FEF38D0B49403722D2C681D72C40EB2E0074880B"
                "4940755B0FEA61D72C40FA0200188F0B4940ACB20F8D08D72C403F7747528D0B49404F3900CC"
                "2BD72C4096DA754B7E0B49407CBCE723C3D62C4032CA4717750B49400CF2773FFAD62C407ADA"
                "B87E5E0B4940119C9C7068D62C40DD0B0A73530B494072CED04595D62C401AEDAE41410B4940"
                "543910F6CCD42C40791DBCDD5B0B49401050ED8531D52C40B711E7EC920B49406E87F5C48AD5"
                "2C40899F4641A90B4940ED2BF5120ED62C40E95C8F63BA0B4940"
            ),
            pian=1,
        )
        kraj_praha.save()
        kraj_brno.save()
        okres_praha.save()
        okres_brno_venkov.save()
        odrovice.save()
        praha.save()

        hn = HeslarNazev(nazev="heslar_typ_projektu")
        hp = HeslarNazev(nazev="heslar_presnost")
        ha = HeslarNazev(nazev="heslar_typ_pian")
        hto = HeslarNazev(nazev="heslar_typ_organizace")
        hpr = HeslarNazev(nazev="heslar_pristupnost")
        hsd = HeslarNazev(nazev="heslar_specifikace_data")
        nazvy_heslaru = [hn, hp, ha, hto, hpr, hsd]
        for n in nazvy_heslaru:
            n.save()

        Heslar(id=hesla.TYP_PROJEKTU_ZACHRANNY_ID, nazev_heslare=hn).save()
        Heslar(id=PRESNOST_DESITKY_METRU_ID, nazev_heslare=hp).save()
        Heslar(id=TYP_PIAN_PLOCHA_ID, nazev_heslare=ha).save()
        Heslar(id=1120, heslo="ostatní", nazev_heslare=hto).save()
        Heslar(id=881, heslo="presne", nazev_heslare=hsd).save()
        typ_muzeum = Heslar(
            id=TYP_ORGANIZACE_MUZEUM_ID, heslo="Muzemum", nazev_heslare=hto
        )
        zp = Heslar(id=PRISTUPNOST_ANONYM_ID, nazev_heslare=hpr)

        zp.save()
        typ_muzeum.save()

        o = Organizace(
            id=769066,
            nazev="AMCR Testovaci organizace",
            nazev_zkraceny="AMCR",
            typ_organizace=typ_muzeum,
            zverejneni_pristupnost=zp,
        )
        o.save()

        user = User.objects.create_user(
            email="amcr@arup.cas.cz",
            password="foo1234!!!",
            organizace=o,
        )
        user.save()

        az = ArcheologickyZaznam(
            typ_zaznamu="A",
            ident_cely="C-202000001A",
            stav=AZ_STAV_ZAPSANY,
        )
        az.save()
        a = Akce(archeologicky_zaznam=az, specifikace_data=Heslar.objects.get(id=881))
        a.save()

        return temp_return

    def teardown_databases(self, *args, **kwargs):
        # do somthing
        return super(AMCRMixinRunner, self).teardown_databases(*args, **kwargs)


class AMCRTestRunner(AMCRMixinRunner, BaseRunner):
    pass
