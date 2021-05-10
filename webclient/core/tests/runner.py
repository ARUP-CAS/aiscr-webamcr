from arch_z.models import Akce, ArcheologickyZaznam
from core.constants import (
    AZ_STAV_ZAPSANY,
    D_STAV_ZAPSANY,
    DOKUMENT_RELATION_TYPE,
    DOKUMENTACNI_JEDNOTKA_RELATION_TYPE,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    ROLE_ADMIN_ID,
)
from core.models import SouborVazby
from dj.models import DokumentacniJednotka
from django.contrib.auth.models import Group
from django.contrib.gis.geos import GEOSGeometry
from django.test.runner import DiscoverRunner as BaseRunner
from dokument.models import Dokument, DokumentExtraData
from heslar import hesla
from heslar.hesla import (
    HESLAR_AKCE_TYP,
    HESLAR_AREAL,
    HESLAR_DATUM_SPECIFIKACE,
    HESLAR_DJ_TYP,
    HESLAR_DOKUMENT_MATERIAL,
    HESLAR_DOKUMENT_RADA,
    HESLAR_DOKUMENT_TYP,
    HESLAR_DOKUMENT_ZACHOVALOST,
    HESLAR_JAZYK,
    HESLAR_OBDOBI,
    HESLAR_ORGANIZACE_TYP,
    HESLAR_PIAN_PRESNOST,
    HESLAR_PIAN_TYP,
    HESLAR_POSUDEK_TYP,
    HESLAR_PRISTUPNOST,
    HESLAR_PROJEKT_TYP,
    PRISTUPNOST_ANONYM_ID,
    TYP_PROJEKTU_ZACHRANNY_ID,
)
from heslar.models import (
    Heslar,
    HeslarDokumentTypMaterialRada,
    HeslarNazev,
    RuianKatastr,
    RuianKraj,
    RuianOkres,
)
from historie.models import HistorieVazby
from komponenta.models import KomponentaVazby
from oznameni.models import Oznamovatel
from projekt.models import Projekt
from uzivatel.models import Organizace, Osoba, User

# Konstanty pouzite v testech
PRESNOST_DESITKY_METRU_ID = 56
PRESNOST_JEDNOTKY_METRU_ID = 567
PRESNOST_POLOHA_PODLE_KATASTRU_ID = 1150
PRESNOST_STOVKY_METRU_ID = 1213

SPECIFIKACE_DATA_PRESNE_ID = 881
HLAVNI_TYP_SONDA_ID = 1234
TYP_DOKUMENTU_PLAN_SONDY_ID = 1096
MATERIAL_DOKUMENTU_DIGI_SOUBOR_ID = 229
JAZYK_DOKUMENTU_CESTINA_ID = 1256
TYP_DJ_CELEK_AKCE_ID = 321
OBDOBI_STREDNI_PALEOLIT_ID = 336
AREAL_HRADISTE_ID = 337
RADA_DOKUMENTU_TEXT_ID = 547
ZACHOVALOST_30_80_ID = 658

TYP_ORGANIZACE_USTAV_PAMATKOVE_PECE_ID = 852
TYP_ORGANIZACE_MUZEUM_ID = 342
TYP_ORGANIZACE_TERENNI_PRACOVISTE_ID = 710
TYP_ORGANIZACE_UNIVERZITA_ID = 487
TYP_ORGANIZACE_VYZKUMNA_INSTITUCE_ID = 581
TYP_ORGANIZACE_OSTATNI_ID = 110

TYP_PIAN_PLOCHA_ID = 476
TYP_PIAN_LINIE_ID = 1206
TYP_PIAN_BOD_ID = 58

EL_CHEFE_ID = 666
KATASTR_ODROVICE_ID = 150
TESTOVACI_DOKUMENT_IDENT = "C-TX-201501985"
AMCR_TESTOVACI_ORGANIZACE_ID = 769066
ARCHEOLOGICKY_POSUDEK_ID = 1111
EXISTING_PROJECT_IDENT = "C-202000001"
EXISTING_EVENT_IDENT = "C-202000001A"
EXISTING_DOCUMENT_ID = 123654


def add_middleware_to_request(request, middleware_class):
    middleware = middleware_class()
    middleware.process_request(request)
    return request


def add_middleware_to_response(request, middleware_class):
    middleware = middleware_class()
    middleware.process_response(request)
    return request


class AMCRTestRunner(BaseRunner):
    def setup_databases(self, *args, **kwargs):
        temp_return = super(AMCRTestRunner, self).setup_databases(*args, **kwargs)
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
            id=KATASTR_ODROVICE_ID,
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

        hn = HeslarNazev(id=HESLAR_PROJEKT_TYP, nazev="heslar_typ_projektu")
        hp = HeslarNazev(id=HESLAR_PIAN_PRESNOST, nazev="heslar_presnost")
        ha = HeslarNazev(id=HESLAR_PIAN_TYP, nazev="heslar_typ_pian")
        hto = HeslarNazev(id=HESLAR_ORGANIZACE_TYP, nazev="heslar_typ_organizace")
        hpr = HeslarNazev(id=HESLAR_PRISTUPNOST, nazev="heslar_pristupnost")
        hsd = HeslarNazev(id=HESLAR_DATUM_SPECIFIKACE, nazev="heslar_specifikace_data")
        hta = HeslarNazev(id=HESLAR_AKCE_TYP, nazev="heslar_typ_akce_druha")
        htd = HeslarNazev(id=HESLAR_DOKUMENT_TYP, nazev="heslar_typ_dokumentu")
        hmd = HeslarNazev(
            id=HESLAR_DOKUMENT_MATERIAL, nazev="heslar_material_dokumentu"
        )
        hdr = HeslarNazev(id=HESLAR_DOKUMENT_RADA, nazev="heslar_rada_dokumentu")
        hdj = HeslarNazev(id=HESLAR_DJ_TYP, nazev="heslar_dj_typ")
        hjd = HeslarNazev(id=HESLAR_JAZYK, nazev="heslar_jazyk_dokumentu")
        hpd = HeslarNazev(id=HESLAR_POSUDEK_TYP, nazev="heslar_posudek")
        hok = HeslarNazev(id=HESLAR_OBDOBI, nazev="heslar_obdobi")
        hak = HeslarNazev(id=HESLAR_AREAL, nazev="heslar_areal")
        hza = HeslarNazev(id=HESLAR_DOKUMENT_ZACHOVALOST, nazev="heslar_zachovalost")
        nazvy_heslaru = [
            hn,
            hp,
            ha,
            hto,
            hpr,
            hsd,
            hta,
            htd,
            hmd,
            hjd,
            hpd,
            hdj,
            hok,
            hak,
            hdr,
            hza,
        ]
        for n in nazvy_heslaru:
            n.save()

        Heslar(
            id=hesla.TYP_PROJEKTU_ZACHRANNY_ID, nazev_heslare=hn, heslo="zachranny"
        ).save()
        Heslar(id=PRESNOST_DESITKY_METRU_ID, nazev_heslare=hp).save()
        Heslar(id=TYP_PIAN_PLOCHA_ID, nazev_heslare=ha).save()
        Heslar(id=1120, heslo="ostatní", nazev_heslare=hto).save()
        Heslar(id=SPECIFIKACE_DATA_PRESNE_ID, heslo="presne", nazev_heslare=hsd).save()
        Heslar(id=HLAVNI_TYP_SONDA_ID, heslo="sonda", nazev_heslare=hta).save()
        Heslar(id=ZACHOVALOST_30_80_ID, heslo="30 % az 80 %", nazev_heslare=hza).save()
        typ_dokumentu_plan = Heslar(
            id=TYP_DOKUMENTU_PLAN_SONDY_ID, heslo="plan sondy", nazev_heslare=htd
        )
        material_dokumentu_digi = Heslar(
            id=MATERIAL_DOKUMENTU_DIGI_SOUBOR_ID,
            heslo="digitalni soubor",
            nazev_heslare=hmd,
        )
        rada_dokumentu_text = Heslar(
            id=RADA_DOKUMENTU_TEXT_ID, heslo="textovy soubor", nazev_heslare=hdr
        )
        typ_dokumentu_plan.save()
        material_dokumentu_digi.save()
        rada_dokumentu_text.save()
        Heslar(id=JAZYK_DOKUMENTU_CESTINA_ID, heslo="cesky", nazev_heslare=hjd).save()
        Heslar(id=TYP_DJ_CELEK_AKCE_ID, heslo="celek akce", nazev_heslare=hdj).save()
        Heslar(
            id=ARCHEOLOGICKY_POSUDEK_ID, heslo="archeologicky", nazev_heslare=hpd
        ).save()
        typ_muzeum = Heslar(
            id=TYP_ORGANIZACE_MUZEUM_ID, heslo="Muzemum", nazev_heslare=hto
        )
        zp = Heslar(id=PRISTUPNOST_ANONYM_ID, nazev_heslare=hpr)
        zp.save()
        typ_muzeum.save()
        Heslar(
            id=OBDOBI_STREDNI_PALEOLIT_ID, heslo="Stredni paleolit", nazev_heslare=hok
        ).save()
        Heslar(id=AREAL_HRADISTE_ID, heslo="Hradiste", nazev_heslare=hak).save()

        # Zaznamy v HeslarDokumentMaterialRada
        HeslarDokumentTypMaterialRada(
            dokument_rada=rada_dokumentu_text,
            dokument_material=material_dokumentu_digi,
            dokument_typ=typ_dokumentu_plan,
            validated=True,
        ).save()

        # Vlozit role do auth_user
        admin_group = Group(id=ROLE_ADMIN_ID, name="Admin")
        admin_group.save()

        o = Organizace(
            id=AMCR_TESTOVACI_ORGANIZACE_ID,
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
            hlavni_role=admin_group,
        )
        user.save()
        # PROJEKT
        p = Projekt(
            typ_projektu=Heslar.objects.get(id=TYP_PROJEKTU_ZACHRANNY_ID),
            ident_cely=EXISTING_PROJECT_IDENT,
            stav=PROJEKT_STAV_ZAHAJENY_V_TERENU,
            hlavni_katastr=praha,
        )
        p.save()
        oznamovatel = Oznamovatel(
            email="tester_juraj@example.com",
            adresa="Nekde 123456",
            odpovedna_osoba="Juraj Skvarla",
            oznamovatel="Juraj Skvarla",
            telefon="+420874521325",
            projekt=p,
        )
        oznamovatel.save()

        # PROJEKT EVENT
        az = ArcheologickyZaznam(
            typ_zaznamu="A",
            ident_cely=EXISTING_EVENT_IDENT,
            stav=AZ_STAV_ZAPSANY,
        )
        az.save()
        a = Akce(
            archeologicky_zaznam=az,
            specifikace_data=Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE_ID),
        )
        a.projekt = p
        a.save()

        # Dokumentacni jednotka akce
        kv = KomponentaVazby(typ_vazby=DOKUMENTACNI_JEDNOTKA_RELATION_TYPE)
        kv.save()
        dj = DokumentacniJednotka(
            typ=Heslar.objects.get(id=TYP_DJ_CELEK_AKCE_ID),
            negativni_jednotka=True,
            ident_cely="C-202000001A-D01",
        )
        dj.archeologicky_zaznam = az
        dj.komponenty = kv
        dj.save()

        # Osoba
        osoba = Osoba(
            id=EL_CHEFE_ID,
            jmeno="Jakub",
            prijmeni="Škvarla",
            vypis="J. Škvarla",
            vypis_cely="Jakub El Chefe Škvarla",
        )
        osoba.save()
        vazba = HistorieVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        vazba.save()
        vazba_soubory = SouborVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        vazba_soubory.save()
        d = Dokument(
            id=EXISTING_DOCUMENT_ID,
            rada=Heslar.objects.get(id=RADA_DOKUMENTU_TEXT_ID),
            typ_dokumentu=Heslar.objects.get(id=TYP_DOKUMENTU_PLAN_SONDY_ID),
            organizace=o,
            pristupnost=zp,
            ident_cely=TESTOVACI_DOKUMENT_IDENT,
            stav=D_STAV_ZAPSANY,
            material_originalu=Heslar.objects.get(id=MATERIAL_DOKUMENTU_DIGI_SOUBOR_ID),
            historie=vazba,
            soubory=vazba_soubory,
        )
        d.save()
        DokumentExtraData(dokument=d).save()

        return temp_return

    def teardown_databases(self, *args, **kwargs):
        # do somthing
        return super(AMCRTestRunner, self).teardown_databases(*args, **kwargs)
