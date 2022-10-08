import datetime
from decimal import Decimal

from arch_z.models import Akce, ArcheologickyZaznam
from core.constants import (
    AZ_STAV_ZAPSANY,
    D_STAV_ZAPSANY,
    DOKUMENT_RELATION_TYPE,
    DOKUMENTACNI_JEDNOTKA_RELATION_TYPE,
    KLADYZM10,
    KLADYZM50,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    ROLE_ADMIN_ID,
    ROLE_ARCHEOLOG_ID,
    ROLE_ARCHIVAR_ID,
    ROLE_BADATEL_ID,
    ROLE_NEAKTIVNI_UZIVATEL_ID,
    PIAN_RELATION_TYPE,
)
from core.models import ProjektSekvence, Soubor, SouborVazby
from dj.models import DokumentacniJednotka
from django.contrib.auth.models import Group
from django.contrib.gis.geos import GEOSGeometry
from django.test.runner import DiscoverRunner as BaseRunner
from dokument.models import Dokument, DokumentCast, DokumentExtraData, DokumentJazyk
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
    PRISTUPNOST_ANONYM_ID,
    PRISTUPNOST_ARCHEOLOG_ID,
    SPECIFIKACE_DATA_PRESNE,
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
from komponenta.models import KomponentaVazby
from oznameni.models import Oznamovatel
from pian.models import Kladyzm, Pian
from projekt.models import Projekt
from uzivatel.models import Organizace, Osoba, User

import logging

from lokalita.models import Lokalita

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
EXISTING_EVENT_IDENT = "C-202000001A"
EXISTING_LOKALITA_IDENT = "X-C-L0000004"
EXISTING_EVENT_IDENT_INCOMPLETE = "C-202000001B"
EXISTING_DOCUMENT_ID = 123654
DOCUMENT_NALEZOVA_ZPRAVA_ID = 12347
DOKUMENT_CAST_IDENT = "M-TX-202100115-D001"
USER_ARCHEOLOG_EMAIL = "indiana.jones@uchicago.edu"
USER_ARCHEOLOG_ID = 47

PIAN_POTVRZEN = 2

PREDMET_ID = 200
PREDMET_SPECIFIKACE_ID = 999

LOKALITA_TYP = 1021
LOKALITA_TYP_NEW = 1020
LOKALITA_DRUH = 1031


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

        # Sekvence pro identifikatory
        # Projekt
        sekvence_roku = [2020, 2021, 2022, 2023, 2024, 2025]
        projektove_sekvence = []
        for rok in sekvence_roku:
            projektove_sekvence.append(ProjektSekvence(rada="C", rok=rok, sekvence=1))
            projektove_sekvence.append(ProjektSekvence(rada="M", rok=rok, sekvence=1))
        ProjektSekvence.objects.bulk_create(projektove_sekvence)

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
            id=KATASTR_PRAHA_ID,
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
        logger.debug(praha.id)
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
        ]
        for n in nazvy_heslaru:
            n.save()

        Heslar(
            id=hesla.TYP_PROJEKTU_ZACHRANNY_ID, nazev_heslare=hn, heslo="zachranny"
        ).save()
        Heslar(id=PRESNOST_DESITKY_METRU_ID, nazev_heslare=hp, zkratka=1).save()
        Heslar(id=GEOMETRY_PLOCHA, nazev_heslare=ha).save()
        Heslar(id=GEOMETRY_BOD, nazev_heslare=ha).save()
        Heslar(id=1120, heslo="ostatní", nazev_heslare=hto).save()
        Heslar(id=SPECIFIKACE_DATA_PRESNE, heslo="presne", nazev_heslare=hsd).save()
        Heslar(id=HLAVNI_TYP_SONDA_ID, heslo="sonda", nazev_heslare=hta).save()
        Heslar(id=ZACHOVALOST_30_80_ID, heslo="30 % az 80 %", nazev_heslare=hza).save()
        Heslar(id=ARCHIV_ARUB, heslo="archiv ARÚB", nazev_heslare=hdu).save()
        typ_dokumentu_plan = Heslar(
            id=TYP_DOKUMENTU_PLAN_SONDY_ID, heslo="plan sondy", nazev_heslare=htd
        )
        typ_dokumentu_nalezova_zprava = Heslar(
            id=TYP_DOKUMENTU_NALEZOVA_ZPRAVA, heslo="nalezova_zprava", nazev_heslare=htd
        )
        typ_dokumentu_nalezova_zprava.save()
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
        Heslar(
            id=JAZYK_DOKUMENTU_CESTINA_ID,
            heslo="cesky",
            nazev_heslare=hjd,
            heslo_en="cesky",
        ).save()
        Heslar(id=ULOZENI_ORIGINALU_ID, heslo="uloz+orig", nazev_heslare=hjd).save()
        Heslar(id=TYP_DJ_CELEK_AKCE_ID, heslo="celek akce", nazev_heslare=hdj).save()
        Heslar(
            id=ARCHEOLOGICKY_POSUDEK_ID, heslo="archeologicky", nazev_heslare=hpd
        ).save()
        typ_muzeum = Heslar(
            id=TYP_ORGANIZACE_MUZEUM_ID, heslo="Muzemum", nazev_heslare=hto
        )
        zp = Heslar(
            id=PRISTUPNOST_ANONYM_ID, heslo="anonym pristupnost", nazev_heslare=hpr
        )
        Heslar(
            id=PRISTUPNOST_ARCHEOLOG_ID,
            heslo="archeolog pristupnost",
            nazev_heslare=hpr,
        ).save()
        zp.save()
        typ_muzeum.save()
        hok_podrizene = Heslar(
            id=OBDOBI_STREDNI_PALEOLIT_ID, heslo="Stredni paleolit", nazev_heslare=hok
        )
        hok_podrizene.save()
        hok_nadrizene = Heslar(
            id=OBDOBI_NADRIZENE_ID, heslo="Stredni paleolit", nazev_heslare=hokkat
        )
        hok_nadrizene.save()
        HeslarHierarchie(
            heslo_podrazene=hok_podrizene,
            heslo_nadrazene=hok_nadrizene,
            typ="podřízenost",
        ).save()
        Heslar(id=AREAL_HRADISTE_ID, heslo="Hradiste", nazev_heslare=hak).save()
        predmet = Heslar(id=PREDMET_ID, heslo="luk", nazev_heslare=hpdr)
        predmet.save()
        specifikace = Heslar(
            id=PREDMET_SPECIFIKACE_ID, heslo="drevo", nazev_heslare=hps
        )
        specifikace.save()
        HeslarHierarchie(
            heslo_podrazene=specifikace, heslo_nadrazene=predmet, typ="výchozí hodnota"
        ).save()
        Heslar(id=LOKALITA_DRUH, nazev_heslare=hld, zkratka=1).save()
        Heslar(id=LOKALITA_TYP, nazev_heslare=hlt, zkratka="L").save()
        Heslar(id=LOKALITA_TYP_NEW, nazev_heslare=hlt, zkratka="M").save()

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
                "0106000020B38E01000100000001030000000100000005000000C0C9ED"
                "A718E828C180504AA34C7E2EC1808369E65D0726C1003986AD3FE42EC1E00477941C5426C1C0FA78"
                "B3849830C140CFBDB2203E29C1D04EA8B0E66430C1C0C9EDA718E828C180504AA34C7E2EC1",
                srid=102067,
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
                "0106000020B38E01000100000001030000000100000005000000C0C9ED"
                "A718E828C180504AA34C7E2EC1808369E65D0726C1003986AD3FE42EC1E00477941C5426C1C0FA78"
                "B3849830C140CFBDB2203E29C1D04EA8B0E66430C1C0C9EDA718E828C180504AA34C7E2EC1"
            ),
        )
        kl50.save()

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
        archeolog_group = Group(id=ROLE_ARCHEOLOG_ID, name="Archeolog")
        archeolog_group.save()
        archivar_group = Group(id=ROLE_ARCHIVAR_ID, name="Archivar")
        archivar_group.save()
        badatel_group = Group(id=ROLE_BADATEL_ID, name="Badatel")
        badatel_group.save()
        neaktivni = Group(id=ROLE_NEAKTIVNI_UZIVATEL_ID, name="Neaktivni uzivatel")
        neaktivni.save()

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
            is_active=True,
        )
        user.save()

        user_archeolog = User.objects.create_user(
            email=USER_ARCHEOLOG_EMAIL,
            password="test123!",
            organizace=o,
            hlavni_role=archeolog_group,
            is_active=True,
            id=USER_ARCHEOLOG_ID,
        )
        user_archeolog.save()

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
        dc.save()

        vazba = HistorieVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        vazba.save()
        vazba_pian = HistorieVazby(typ_vazby=PIAN_RELATION_TYPE, id=47)
        vazba_pian.save()
        vazba_soubory = SouborVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        vazba_soubory.save()
        soubor = Soubor(
            nazev_zkraceny="x",
            nazev_puvodni="x",
            vlastnik=User.objects.first(),
            nazev="x",
            mimetype="x",
            size_bytes=1,
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
