import datetime
from decimal import Decimal

import psycopg2

from arch_z.models import Akce, ArcheologickyZaznam, ExterniOdkaz
from core.constants import (
    AZ_STAV_ZAPSANY,
    D_STAV_ZAPSANY,
    DOKUMENT_CAST_RELATION_TYPE,
    DOKUMENT_RELATION_TYPE,
    DOKUMENTACNI_JEDNOTKA_RELATION_TYPE,
    EZ_STAV_ODESLANY,
    EZ_STAV_ZAPSANY,
    KLADYZM10,
    KLADYZM50,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    ROLE_ADMIN_ID,
    ROLE_ARCHEOLOG_ID,
    ROLE_ARCHIVAR_ID,
    ROLE_BADATEL_ID,
    PIAN_RELATION_TYPE,
)
from core.models import ProjektSekvence, Soubor, SouborVazby
from dj.models import DokumentacniJednotka
from django.contrib.auth.models import Group
from django.contrib.gis.geos import GEOSGeometry
from webclient.settings.base import get_secret
from django.test.runner import DiscoverRunner as BaseRunner
from dokument.models import (
    Dokument,
    DokumentCast,
    DokumentExtraData,
    DokumentJazyk,
    Tvar,
)
from heslar import hesla
from heslar.hesla import (
    GEOMETRY_BOD,
    GEOMETRY_PLOCHA,
    HESLAR_AKCE_TYP,
    HESLAR_AREAL,
    HESLAR_DATUM_SPECIFIKACE,
    HESLAR_DJ_TYP,
    HESLAR_DOKUMENT_MATERIAL,
    HESLAR_DOKUMENT_RADA,
    HESLAR_DOKUMENT_TYP,
    HESLAR_DOKUMENT_ZACHOVALOST,
    HESLAR_EXTERNI_ZDROJ_TYP,
    HESLAR_JAZYK,
    HESLAR_LOKALITA_DRUH,
    HESLAR_LOKALITA_TYP,
    HESLAR_OBDOBI,
    HESLAR_ORGANIZACE_TYP,
    HESLAR_PIAN_PRESNOST,
    HESLAR_PIAN_TYP,
    HESLAR_POSUDEK_TYP,
    HESLAR_PRISTUPNOST,
    HESLAR_PROJEKT_TYP,
    HESLAR_LETFOTO_TVAR,
    PRISTUPNOST_ANONYM_ID,
    PRISTUPNOST_ARCHEOLOG_ID,
    SPECIFIKACE_DATA_PRESNE,
    TYP_PROJEKTU_PRUZKUM_ID,
    TYP_PROJEKTU_ZACHRANNY_ID,
    HESLAR_DOKUMENT_ULOZENI,
    HESLAR_PREDMET_SPECIFIKACE,
    HESLAR_PREDMET_DRUH,
    HESLAR_OBDOBI_KAT,
)
from heslar.models import (
    Heslar,
    HeslarDokumentTypMaterialRada,
    HeslarHierarchie,
    HeslarNazev,
    RuianKatastr,
    RuianKraj,
    RuianOkres,
)
from historie.models import HistorieVazby
from komponenta.models import Komponenta, KomponentaVazby
from oznameni.models import Oznamovatel
from pian.models import Kladyzm, Pian
from projekt.models import Projekt
from uzivatel.models import Organizace, Osoba, User, UserNotificationType

import logging

from lokalita.models import Lokalita
from ez.models import ExterniZdroj
from neidentakce.models import NeidentAkce

logger = logging.getLogger(__name__)

# Konstanty pouzite v testech
PRESNOST_DESITKY_METRU_ID = 56
PRESNOST_JEDNOTKY_METRU_ID = 567
PRESNOST_POLOHA_PODLE_KATASTRU_ID = 1150
PRESNOST_STOVKY_METRU_ID = 1213

HLAVNI_TYP_SONDA_ID = 1234
TYP_DOKUMENTU_PLAN_SONDY_ID = 1096
TYP_DOKUMENTU_NALEZOVA_ZPRAVA = 1073
MATERIAL_DOKUMENTU_DIGI_SOUBOR_ID = 229
JAZYK_DOKUMENTU_CESTINA_ID = 1256
ULOZENI_ORIGINALU_ID = 5588
TYP_DJ_CELEK_AKCE_ID = 321
TYP_DJ_KATASTR_ID = 1071
OBDOBI_STREDNI_PALEOLIT_ID = 336
OBDOBI_NADRIZENE_ID = 330
AREAL_HRADISTE_ID = 337
RADA_DOKUMENTU_TEXT_ID = 547
ZACHOVALOST_30_80_ID = 658
ARCHIV_ARUB = 1165

TYP_ORGANIZACE_USTAV_PAMATKOVE_PECE_ID = 852
TYP_ORGANIZACE_MUZEUM_ID = 342
TYP_ORGANIZACE_TERENNI_PRACOVISTE_ID = 710
TYP_ORGANIZACE_UNIVERZITA_ID = 487
TYP_ORGANIZACE_VYZKUMNA_INSTITUCE_ID = 581
TYP_ORGANIZACE_OSTATNI_ID = 110

EL_CHEFE_ID = 666
KATASTR_ODROVICE_ID = 150
KATASTR_PRAHA_ID = 149
TESTOVACI_DOKUMENT_IDENT = "C-TX-201501985"
TESTOVACI_SOUBOR_ID = 123
DOCUMENT_NALEZOVA_ZPRAVA_IDENT = "C-TX-201501986"
AMCR_TESTOVACI_ORGANIZACE_ID = 769066
ARCHEOLOGICKY_POSUDEK_ID = 1111
EXISTING_PROJECT_IDENT = "C-202000001"
EXISTING_PROJECT_IDENT_ZACHRANNY = "C-202000002"
EXISTING_PROJECT_IDENT_PRUZKUMNY = "C-202000003"
EXISTING_EVENT_IDENT = "C-202000001A"
EXISTING_EVENT_IDENT2 = "C-202000001C"
EXISTING_LOKALITA_IDENT = "X-C-L0000004"
EXISTING_EVENT_IDENT_INCOMPLETE = "C-202000001B"
EXISTING_SAM_EVENT_IDENT = "X-M-9123456A"
EXISTING_DOCUMENT_ID = 123654
EXISTING_EZ_IDENT = "BIB-0000001"
EXISTING_EZ_ODESLANY = "BIB-0000002"
EXISTIN_EO_ID = 22
EXISTIN_NEIDENT_AKCE_IDENT = "M-TX-202100115-D01"
DOCUMENT_NALEZOVA_ZPRAVA_ID = 12347
DOKUMENT_CAST_IDENT = "M-TX-202100115-D001"
DOKUMENT_CAST_IDENT2 = "M-TX-202100115-D002"
DOKUMENT_KOMPONENTA_IDENT = "M-TX-202100115-K001"
USER_ARCHEOLOG_EMAIL = "indiana.jones@uchicago.edu"
USER_ARCHEOLOG_ID = 47

PIAN_POTVRZEN = 2

PREDMET_ID = 200
PREDMET_SPECIFIKACE_ID = 999

LOKALITA_TYP = 1021
LOKALITA_TYP_NEW = 1020
LOKALITA_DRUH = 1031

EZ_TYP = 2035
EZ_TYP_NEW = 2036

LETFOTO_TVAR_ID = 3036

TEST_USER_USERNAME = "amcr@arup.cas.cz"
TEST_USER_PASSWORD = "foo1234!!!"


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

        # Connections are established to duplicate Ruian data
        database_name = get_secret("DB_NAME")
        prod_conn = psycopg2.connect(
            host=get_secret("DB_HOST"),
            database=database_name,
            user=get_secret('DB_USER'),
            password=get_secret('DB_PASS')
        )

        # establish connection to test_prod_zaloha database
        test_conn = psycopg2.connect(
            host=get_secret("DB_HOST"),
            database=f"test_{database_name}",
            user=get_secret('DB_USER'),
            password=get_secret('DB_PASS')
        )

        # create cursor objects for both connections
        prod_cursor = prod_conn.cursor()
        test_cursor = test_conn.cursor()

        def item_to_str(item):
            if item is None:
                return "null"
            if isinstance(item, str):
                return f"'{item}'"
            return str(item)

        # execute SQL query to copy data from prod_zaloha.ruian_katastr to test_prod_zaloha.ruian_katastr
        tables = (
            ("id, nazev, kod, rada_id, definicni_bod, hranice, nazev_en", "public.ruian_kraj"),
            ("id, nazev, kraj, spz, kod, nazev_en, hranice, definicni_bod", "ruian_okres"),
            ("id, okres, aktualni, nazev, kod, definicni_bod, hranice, nazev_stary, soucasny", "ruian_katastr"),
        )
        for table in tables:
            prod_cursor.execute(f"SELECT {table[0]} FROM {table[1]}")
            for row in prod_cursor:
                row = ", ".join([item_to_str(item) for item in row])
                if table[1] == "ruian_katastr":
                    row = row[:7] + row[8:]
                test_cursor.execute(f"INSERT INTO {table[1]} ({table[0]}) VALUES ({row});")
            test_conn.commit()

        prod_cursor.close()
        test_cursor.close()
        prod_conn.close()
        test_conn.close()

        print("Setting up my database content ...")

        # Sekvence pro identifikatory
        # Projekt
        sekvence_roku = [2020, 2021, 2022, 2023, 2024, 2025]
        projektove_sekvence = []
        for rok in sekvence_roku:
            projektove_sekvence.append(ProjektSekvence(rada="C", rok=rok, sekvence=1))
            projektove_sekvence.append(ProjektSekvence(rada="M", rok=rok, sekvence=1))
        ProjektSekvence.objects.bulk_create(projektove_sekvence)

        UserNotificationType(ident_cely="E-U-04", zasilat_neaktivnim=False,
                             predmet="AMČR: uživatelský účet čeká na aktivaci",
                             cesta_sablony="emails/E-U-04.html").save()

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
        hokkat = HeslarNazev(id=HESLAR_OBDOBI_KAT, nazev="heslat_odbobi_kat")
        hak = HeslarNazev(id=HESLAR_AREAL, nazev="heslar_areal")
        hza = HeslarNazev(id=HESLAR_DOKUMENT_ZACHOVALOST, nazev="heslar_zachovalost")
        hdu = HeslarNazev(id=HESLAR_DOKUMENT_ULOZENI, nazev="heslar_dokument_ulozeni")
        hps = HeslarNazev(
            id=HESLAR_PREDMET_SPECIFIKACE, nazev="heslar_predmet_specifikace"
        )
        hpdr = HeslarNazev(id=HESLAR_PREDMET_DRUH, nazev="heslar_predmet_druh")
        hld = HeslarNazev(id=HESLAR_LOKALITA_DRUH, nazev="heslar_lokalita_druh")
        hlt = HeslarNazev(id=HESLAR_LOKALITA_TYP, nazev="heslar_lokalita_typ")
        hezt = HeslarNazev(id=HESLAR_EXTERNI_ZDROJ_TYP, nazev="heslar_ez_typ")
        hlft = HeslarNazev(id=HESLAR_LETFOTO_TVAR, nazev="heslar_letfoto_tvar")
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
            hokkat,
            hak,
            hdr,
            hza,
            hdu,
            hps,
            hpdr,
            hld,
            hlt,
            hezt,
            hlft,
        ]
        for n in nazvy_heslaru:
            n.save()

        Heslar(
            id=hesla.TYP_PROJEKTU_ZACHRANNY_ID, nazev_heslare=hn, heslo="záchranný", ident_cely="XXX1"
        ).save()
        Heslar(
            id=hesla.TYP_PROJEKTU_PRUZKUM_ID, nazev_heslare=hn, heslo="průzkumný", ident_cely="XXX2"
        ).save()
        Heslar(id=PRESNOST_DESITKY_METRU_ID, nazev_heslare=hp, zkratka=1, ident_cely="XXX3").save()
        Heslar(id=GEOMETRY_PLOCHA, nazev_heslare=ha, ident_cely="XXX4").save()
        Heslar(id=GEOMETRY_BOD, nazev_heslare=ha, ident_cely="XXX5").save()
        Heslar(id=1120, heslo="ostatní", nazev_heslare=hto, ident_cely="XXX6").save()
        Heslar(id=SPECIFIKACE_DATA_PRESNE, heslo="presne", nazev_heslare=hsd, ident_cely="XXX7").save()
        Heslar(id=HLAVNI_TYP_SONDA_ID, heslo="sonda", nazev_heslare=hta, ident_cely="XXX8").save()
        Heslar(id=ZACHOVALOST_30_80_ID, heslo="30 % az 80 %", nazev_heslare=hza, ident_cely="XXX9").save()
        Heslar(id=ARCHIV_ARUB, heslo="archiv ARÚB", nazev_heslare=hdu, ident_cely="XXX10").save()
        typ_dokumentu_plan = Heslar(
            id=TYP_DOKUMENTU_PLAN_SONDY_ID, heslo="plan sondy", nazev_heslare=htd, ident_cely="XXX11"
        )
        typ_dokumentu_nalezova_zprava = Heslar(
            id=TYP_DOKUMENTU_NALEZOVA_ZPRAVA, heslo="nalezova_zprava", nazev_heslare=htd, ident_cely="XXX12"
        )
        typ_dokumentu_nalezova_zprava.save()
        material_dokumentu_digi = Heslar(
            id=MATERIAL_DOKUMENTU_DIGI_SOUBOR_ID,
            heslo="digitalni soubor",
            nazev_heslare=hmd,
            ident_cely = "XXX13"
        )
        rada_dokumentu_text = Heslar(
            id=RADA_DOKUMENTU_TEXT_ID, heslo="textovy soubor", nazev_heslare=hdr, ident_cely="XXX14"
        )
        typ_dokumentu_plan.save()
        material_dokumentu_digi.save()
        rada_dokumentu_text.save()
        Heslar(
            id=JAZYK_DOKUMENTU_CESTINA_ID,
            heslo="cesky",
            nazev_heslare=hjd,
            heslo_en="cesky",
            ident_cely="XXX15",
        ).save()
        Heslar(id=ULOZENI_ORIGINALU_ID, heslo="uloz+orig", nazev_heslare=hjd, ident_cely="XXX16").save()
        Heslar(id=TYP_DJ_CELEK_AKCE_ID, heslo="celek akce", nazev_heslare=hdj, ident_cely="XXX17").save()
        Heslar(id=TYP_DJ_KATASTR_ID, heslo="katastr", nazev_heslare=hdj, ident_cely="XXX18").save()
        Heslar(
            id=ARCHEOLOGICKY_POSUDEK_ID, heslo="archeologicky", nazev_heslare=hpd, ident_cely="XXX19"
        ).save()
        typ_muzeum = Heslar(
            id=TYP_ORGANIZACE_MUZEUM_ID, heslo="Muzemum", nazev_heslare=hto, ident_cely="XXX20"
        )
        zp = Heslar(
            id=PRISTUPNOST_ANONYM_ID, heslo="anonym pristupnost", nazev_heslare=hpr, ident_cely="XXX21"
        )
        Heslar(
            id=PRISTUPNOST_ARCHEOLOG_ID,
            heslo="archeolog pristupnost",
            nazev_heslare=hpr,
            ident_cely="XXX22"
        ).save()
        Heslar(
            id=LETFOTO_TVAR_ID,
            heslo="tvar fotky 1",
            nazev_heslare=hlft,
            ident_cely="XXX23"
        ).save()
        zp.save()
        typ_muzeum.save()
        hok_podrizene = Heslar(
            id=OBDOBI_STREDNI_PALEOLIT_ID, heslo="Stredni paleolit", nazev_heslare=hok, ident_cely="XXX24"
        )
        hok_podrizene.save()
        hok_nadrizene = Heslar(
            id=OBDOBI_NADRIZENE_ID, heslo="Stredni paleolit", nazev_heslare=hokkat, ident_cely="XXX99"
        )
        hok_nadrizene.save()
        HeslarHierarchie(
            heslo_podrazene=hok_podrizene,
            heslo_nadrazene=hok_nadrizene,
            typ="podřízenost",
        ).save()
        Heslar(id=AREAL_HRADISTE_ID, heslo="Hradiste", nazev_heslare=hak, ident_cely="XXX25").save()
        predmet = Heslar(id=PREDMET_ID, heslo="luk", nazev_heslare=hpdr, ident_cely="XXX26")
        predmet.save()
        specifikace = Heslar(
            id=PREDMET_SPECIFIKACE_ID, heslo="drevo", nazev_heslare=hps, ident_cely="XXX27"
        )
        specifikace.save()
        HeslarHierarchie(
            heslo_podrazene=specifikace, heslo_nadrazene=predmet, typ="výchozí hodnota"
        ).save()
        Heslar(id=LOKALITA_DRUH, nazev_heslare=hld, zkratka=1, ident_cely="XXX28").save()
        Heslar(id=LOKALITA_TYP, nazev_heslare=hlt, zkratka="L", ident_cely="XXX29").save()
        Heslar(id=LOKALITA_TYP_NEW, nazev_heslare=hlt, zkratka="M", ident_cely="XXX30").save()
        Heslar(id=EZ_TYP, nazev_heslare=hezt, zkratka="K", heslo="kniha", ident_cely="XXX31").save()
        Heslar(id=EZ_TYP_NEW, nazev_heslare=hezt, zkratka="C", heslo="casopis", ident_cely="XXX32").save()

        kl10 = Kladyzm(
            gid=2,
            objectid=2,
            kategorie=KLADYZM10,
            cislo="01",
            nazev="Praha",
            natoceni=Decimal(8.78330000000),
            shape_leng=Decimal(341204.736390),
            shape_area=Decimal(7189599966.71),
            the_geom=GEOSGeometry(
                "01030000208A150000010000000500000040822DB0C55929C1E0569730EF022FC100F6C19EDF4E29C1A03D6ED284B92EC1C0F5F1A8D9F228C100806CBDBCC72EC1C05CFAA89AFD28C160EA92D62C112FC140822DB0C55929C1E0569730EF022FC1",
                srid=5514,
            ),
        )
        kl10.save()
        kl50 = Kladyzm(
            gid=3,
            objectid=3,
            kategorie=KLADYZM50,
            cislo="02",
            nazev="Praha",
            natoceni=Decimal(8.78330000000),
            shape_leng=Decimal(341204.736390),
            shape_area=Decimal(7189599966.71),
            the_geom=GEOSGeometry(
                "01030000208A150000010000000500000040822DB0C55929C1E0569730EF022FC100F6C19EDF4E29C1A03D6ED284B92EC1C0F5F1A8D9F228C100806CBDBCC72EC1C05CFAA89AFD28C160EA92D62C112FC140822DB0C55929C1E0569730EF022FC1",
                srid=5514,
            ),
        )
        kl50.save()

        # Zaznamy v HeslarDokumentMaterialRada
        HeslarDokumentTypMaterialRada(
            dokument_rada=rada_dokumentu_text,
            dokument_material=material_dokumentu_digi,
            dokument_typ=typ_dokumentu_plan,
        ).save()

        # Vlozit role do auth_user
        admin_group = Group(id=ROLE_ADMIN_ID, name="Admin")
        admin_group.save()
        archeolog_group = Group(id=ROLE_ARCHEOLOG_ID, name="Archeolog")
        archeolog_group.save()
        archivar_group = Group(id=ROLE_ARCHIVAR_ID, name="Archivar")
        archivar_group.save()
        badatel_group = Group(id=ROLE_BADATEL_ID, name="Badatel")
        badatel_group.save()

        o = Organizace(
            id=AMCR_TESTOVACI_ORGANIZACE_ID,
            nazev="AMCR Testovaci organizace",
            nazev_zkraceny="AMCR",
            typ_organizace=typ_muzeum,
            zverejneni_pristupnost=zp,
        )
        o.save()

        user = User.objects.create_user(
            email=TEST_USER_USERNAME,
            password=TEST_USER_PASSWORD,
            organizace=o,
            is_active=True,
        )
        user.created_from_admin_panel = True
        user.save()
        user.groups.add(admin_group)

        user_archeolog = User.objects.create_user(
            email=USER_ARCHEOLOG_EMAIL,
            password="test123!",
            organizace=o,
            is_active=True,
            id=USER_ARCHEOLOG_ID,
        )
        user_archeolog.created_from_admin_panel = True
        user_archeolog.save()
        user_archeolog.groups.add(archeolog_group)

        praha = RuianKatastr.objects.get(pk=316655)
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

        Projekt(
            typ_projektu=Heslar.objects.get(id=TYP_PROJEKTU_PRUZKUM_ID),
            ident_cely=EXISTING_PROJECT_IDENT_PRUZKUMNY,
            stav=PROJEKT_STAV_ZAHAJENY_V_TERENU,
            hlavni_katastr=praha,
        ).save()

        # PROJEKT ZACHRANNY
        p = Projekt(
            typ_projektu=Heslar.objects.get(id=TYP_PROJEKTU_ZACHRANNY_ID),
            ident_cely=EXISTING_PROJECT_IDENT_ZACHRANNY,
            stav=PROJEKT_STAV_ZAHAJENY_V_TERENU,
            hlavni_katastr=praha,
        )
        p.save()

        # Osoba
        osoba = Osoba(
            id=EL_CHEFE_ID,
            jmeno="Jakub",
            prijmeni="Škvarla",
            vypis="J. Škvarla",
            vypis_cely="Jakub El Chefe Škvarla",
        )
        osoba.save()

        # INCOMPLETE EVENT
        az_incoplete = ArcheologickyZaznam(
            typ_zaznamu="A",
            hlavni_katastr=praha,
            ident_cely=EXISTING_EVENT_IDENT_INCOMPLETE,
            stav=AZ_STAV_ZAPSANY,
        )
        az_incoplete.save()
        a_incomplete = Akce(
            archeologicky_zaznam=az_incoplete,
            specifikace_data=Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE),
        )
        a_incomplete.projekt = p
        a_incomplete.save()

        # PROJEKT EVENT
        az = ArcheologickyZaznam(
            typ_zaznamu="A",
            hlavni_katastr=praha,
            ident_cely=EXISTING_EVENT_IDENT,
            stav=AZ_STAV_ZAPSANY,
            pristupnost=Heslar.objects.get(pk=PRISTUPNOST_ANONYM_ID),
        )
        az.save()
        a = Akce(
            typ=Akce.TYP_AKCE_PROJEKTOVA,
            archeologicky_zaznam=az,
            specifikace_data=Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE),
            datum_zahajeni=datetime.datetime.today(),
            datum_ukonceni=datetime.datetime.today() + datetime.timedelta(days=1),
            lokalizace_okolnosti="test",
            hlavni_typ=Heslar.objects.get(pk=HLAVNI_TYP_SONDA_ID),
            hlavni_vedouci=Osoba.objects.first(),
            organizace=o,
        )
        a.projekt = p
        a.save()

        az3 = ArcheologickyZaznam(
            typ_zaznamu="A",
            hlavni_katastr=praha,
            ident_cely=EXISTING_EVENT_IDENT2,
            stav=AZ_STAV_ZAPSANY,
            pristupnost=Heslar.objects.get(pk=PRISTUPNOST_ANONYM_ID),
        )
        az3.save()
        a3 = Akce(
            typ=Akce.TYP_AKCE_PROJEKTOVA,
            archeologicky_zaznam=az3,
            specifikace_data=Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE),
            datum_zahajeni=datetime.datetime.today(),
            datum_ukonceni=datetime.datetime.today() + datetime.timedelta(days=1),
            lokalizace_okolnosti="test",
            hlavni_typ=Heslar.objects.get(pk=HLAVNI_TYP_SONDA_ID),
            hlavni_vedouci=Osoba.objects.first(),
            organizace=o,
        )
        a3.projekt = p
        a3.save()

        # LOKALITA
        az_lokalita = ArcheologickyZaznam(
            typ_zaznamu="L",
            hlavni_katastr=praha,
            ident_cely=EXISTING_LOKALITA_IDENT,
            stav=AZ_STAV_ZAPSANY,
            pristupnost=Heslar.objects.get(pk=PRISTUPNOST_ANONYM_ID),
        )
        az_lokalita.save()
        lokalita = Lokalita(
            archeologicky_zaznam=az_lokalita,
            typ_lokality=Heslar.objects.get(id=LOKALITA_TYP),
            druh=Heslar.objects.get(id=LOKALITA_DRUH),
            nazev="nazev lokality",
        )
        lokalita.save()

        # EVENT
        az2 = ArcheologickyZaznam(
            typ_zaznamu="A",
            hlavni_katastr=praha,
            ident_cely=EXISTING_SAM_EVENT_IDENT,
            stav=AZ_STAV_ZAPSANY,
            pristupnost=Heslar.objects.get(pk=PRISTUPNOST_ANONYM_ID),
        )
        az2.save()
        a2 = Akce(
            typ=Akce.TYP_AKCE_SAMOSTATNA,
            archeologicky_zaznam=az2,
            specifikace_data=Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE),
            datum_zahajeni=datetime.datetime.today(),
            datum_ukonceni=datetime.datetime.today() + datetime.timedelta(days=1),
            lokalizace_okolnosti="test",
            hlavni_typ=Heslar.objects.get(pk=HLAVNI_TYP_SONDA_ID),
            hlavni_vedouci=Osoba.objects.first(),
            organizace=o,
        )
        a2.save()

        # Externi Zdroj
        ez = ExterniZdroj(
            typ=Heslar.objects.get(pk=EZ_TYP),
            ident_cely=EXISTING_EZ_IDENT,
            stav=EZ_STAV_ZAPSANY,
            rok_vydani_vzniku="1991",
            nazev="Taka pekna kniha",
        )
        ez.save()
        ez2 = ExterniZdroj(
            typ=Heslar.objects.get(pk=EZ_TYP),
            ident_cely=EXISTING_EZ_ODESLANY,
            stav=EZ_STAV_ODESLANY,
            rok_vydani_vzniku="1991",
            nazev="Taka pekna kniha",
        )
        ez2.save()

        eo = ExterniOdkaz(
            externi_zdroj=ez,
            archeologicky_zaznam=az,
            id=EXISTIN_EO_ID,
        )
        eo.save()

        vazba_pian = HistorieVazby(typ_vazby=PIAN_RELATION_TYPE, id=47)
        vazba_pian.save()

        pian = Pian(
            presnost=Heslar.objects.first(),
            typ=Heslar.objects.first(),
            geom=GEOSGeometry("POINT(5 23)"),
            zm10=kl10,
            zm50=kl50,
            ident_cely="x",
            historie=vazba_pian,
            stav=PIAN_POTVRZEN,
        )
        pian.save()

        # Dokumentacni jednotka akce
        kv = KomponentaVazby(typ_vazby=DOKUMENTACNI_JEDNOTKA_RELATION_TYPE)
        kv.save()
        dj = DokumentacniJednotka(
            typ=Heslar.objects.get(id=TYP_DJ_CELEK_AKCE_ID),
            negativni_jednotka=True,
            ident_cely="C-202000001A-D01",
            pian=pian,
        )
        dj.archeologicky_zaznam = az
        dj.komponenty = kv
        dj.save()

        vazba = HistorieVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        vazba.save()
        vazba_pian = HistorieVazby(typ_vazby=PIAN_RELATION_TYPE, id=47)
        vazba_pian.save()
        vazba_soubory = SouborVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        vazba_soubory.save()
        # Dokument d bez souboru
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
            popis="popis",
            ulozeni_originalu=Heslar.objects.get(id=ULOZENI_ORIGINALU_ID),
        )
        d.save()
        DokumentJazyk(
            id=1,
            dokument=d,
            jazyk=Heslar.objects.get(id=JAZYK_DOKUMENTU_CESTINA_ID),
        ).save()
        DokumentExtraData(dokument=d).save()
        dc = DokumentCast(
            dokument=d,
            archeologicky_zaznam=az_incoplete,
            ident_cely=DOKUMENT_CAST_IDENT,
        )
        kv2 = KomponentaVazby(typ_vazby=DOKUMENT_CAST_RELATION_TYPE)
        kv2.save()
        dc.komponenty = kv2
        dc.save()

        dc2 = DokumentCast(
            dokument=d,
            ident_cely=DOKUMENT_CAST_IDENT2,
        )
        kv3 = KomponentaVazby(typ_vazby=DOKUMENT_CAST_RELATION_TYPE)
        kv3.save()
        dc2.komponenty = kv3
        dc2.save()

        komp = Komponenta(
            obdobi=Heslar.objects.get(id=OBDOBI_STREDNI_PALEOLIT_ID),
            areal=Heslar.objects.get(id=AREAL_HRADISTE_ID),
            ident_cely=DOKUMENT_KOMPONENTA_IDENT,
            komponenta_vazby=kv2,
        )
        komp.save()

        Tvar(dokument=d, tvar=Heslar.objects.get(id=AREAL_HRADISTE_ID)).save()

        NeidentAkce(dokument_cast=dc2).save()

        vazba = HistorieVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        vazba.save()
        vazba_pian = HistorieVazby(typ_vazby=PIAN_RELATION_TYPE, id=47)
        vazba_pian.save()
        vazba_soubory = SouborVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        vazba_soubory.save()
        soubor = Soubor(
            nazev_zkraceny="x",
            nazev_puvodni="x",
            nazev="x",
            mimetype="x",
            size_mb=1,
            vazba=vazba_soubory,
            path="x",
            id=TESTOVACI_SOUBOR_ID,
        )
        soubor.save()
        dokument_nalezova_zprava = Dokument(
            id=DOCUMENT_NALEZOVA_ZPRAVA_ID,
            rada=Heslar.objects.get(id=RADA_DOKUMENTU_TEXT_ID),
            typ_dokumentu=Heslar.objects.get(id=TYP_DOKUMENTU_NALEZOVA_ZPRAVA),
            organizace=o,
            pristupnost=zp,
            ident_cely=DOCUMENT_NALEZOVA_ZPRAVA_IDENT,
            stav=D_STAV_ZAPSANY,
            material_originalu=Heslar.objects.get(id=MATERIAL_DOKUMENTU_DIGI_SOUBOR_ID),
            historie=vazba,
            soubory=vazba_soubory,
            popis="popis",
            ulozeni_originalu=Heslar.objects.get(id=ULOZENI_ORIGINALU_ID),
        )
        dokument_nalezova_zprava.save()
        DokumentJazyk(
            id=2,
            dokument=dokument_nalezova_zprava,
            jazyk=Heslar.objects.get(id=JAZYK_DOKUMENTU_CESTINA_ID),
        ).save()
        DokumentExtraData(dokument=dokument_nalezova_zprava).save()
        dc = DokumentCast(dokument=dokument_nalezova_zprava, archeologicky_zaznam=az)
        dc.save()
        return temp_return

    def teardown_databases(self, *args, **kwargs):
        # do somthing
        return super(AMCRTestRunner, self).teardown_databases(*args, **kwargs)
