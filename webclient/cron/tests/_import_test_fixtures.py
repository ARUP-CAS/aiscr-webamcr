"""Sdílené fixtures pro ``run_data_import`` testy modelů ADB / DJ / VyskovyBod / AZ.

Tyto modely tvoří propojený graf vyžadující kompletní RUIAN hierarchii, PIAN
napojený do hlavního katastru a Akce-typ ArcheologickyZaznam. Fixture stavebnice
existuje pouze pro snížení duplicity v testech ``cron/tests/test_run_data_import_*``.
"""

from unittest.mock import patch

from arch_z.models import Akce, ArcheologickyZaznam
from core.constants import AZ_STAV_ZAPSANY
from dj.models import DokumentacniJednotka
from heslar.hesla import (
    HESLAR_AKCE_TYP,
    HESLAR_DATUM_SPECIFIKACE,
    HESLAR_DJ_TYP,
    HESLAR_LICENCE,
    HESLAR_ORGANIZACE_TYP,
    HESLAR_PIAN_PRESNOST,
    HESLAR_PIAN_TYP,
    HESLAR_PRISTUPNOST,
    HESLAR_PROJEKT_TYP,
)
from heslar.models import Heslar, HeslarNazev, RuianKatastr, RuianKraj, RuianOkres
from pian.models import Kladyzm, Pian
from projekt.models import Projekt
from uzivatel.models import Organizace


def fedora_silence():
    """Kontext manager-trojice patches pro vytváření fixture záznamů bez Fedora HTTP volání."""
    return (
        patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ),
        patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None),
    )


def create_heslar_fixtures(suffix: str):
    """Vytvoří nutné heslářové entry pro importní fixtures.

    :param suffix: Přípona použitá pro unikátní identifikátory testovacích hesel.
    """
    pristupnost_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_PRISTUPNOST, defaults={"nazev": "pristupnost"})
    pristupnost, _ = Heslar.objects.get_or_create(
        nazev_heslare=pristupnost_nazev,
        zkratka="A",
        defaults={"ident_cely": "HES-IMP-PRST-001", "heslo": "Veřejný", "heslo_en": "Public"},
    )
    licence_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_LICENCE, defaults={"nazev": "licence"})
    licence, _ = Heslar.objects.get_or_create(
        nazev_heslare=licence_nazev,
        zkratka="L",
        defaults={"ident_cely": "HES-IMP-LIC-001", "heslo": "L", "heslo_en": "L"},
    )
    typ_org_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_ORGANIZACE_TYP, defaults={"nazev": "typ_organizace"})
    typ_org, _ = Heslar.objects.get_or_create(
        nazev_heslare=typ_org_nazev,
        zkratka="T",
        defaults={"ident_cely": "HES-IMP-TYPORG-001", "heslo": "T", "heslo_en": "T"},
    )
    dj_typ_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_DJ_TYP, defaults={"nazev": "dj_typ"})
    dj_typ, _ = Heslar.objects.get_or_create(
        ident_cely=f"HES-DJTYP-{suffix}",
        defaults={
            "nazev_heslare": dj_typ_nazev,
            "heslo": "Sonda",
            "heslo_en": "Trench",
            "zkratka": f"S{suffix[:1]}",
            "razeni": 99,
        },
    )
    pian_typ_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_PIAN_TYP, defaults={"nazev": "pian_typ"})
    pian_typ, _ = Heslar.objects.get_or_create(
        ident_cely=f"HES-PIANTYP-{suffix}",
        defaults={
            "nazev_heslare": pian_typ_nazev,
            "heslo": "Bod",
            "heslo_en": "Point",
            "zkratka": f"B{suffix[:1]}",
            "razeni": 1,
        },
    )
    presnost_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_PIAN_PRESNOST, defaults={"nazev": "pian_presnost"})
    presnost, _ = Heslar.objects.get_or_create(
        ident_cely=f"HES-PIANPR-{suffix}",
        defaults={
            "nazev_heslare": presnost_nazev,
            "heslo": "Přesný",
            "heslo_en": "Accurate",
            "zkratka": "1",
            "razeni": 1,
        },
    )
    return {
        "pristupnost": pristupnost,
        "licence": licence,
        "typ_org": typ_org,
        "dj_typ": dj_typ,
        "pian_typ": pian_typ,
        "presnost": presnost,
    }


def create_ruian_with_pian(suffix: str, pian_ident: str, heslars: dict) -> tuple:
    """Vytvoří RuianKraj/Okres/Katastr + Pian a naváže Pian do katastru.

    :param suffix: Přípona použitá pro unikátní názvy a kódy RUIAN fixtures.
    :param pian_ident: Identifikátor PIAN záznamu vytvořeného pro katastr.
    :param heslars: Slovník heslářových fixtures potřebných pro PIAN.
    :return: (katastr, pian)
    """
    point_wkt = "SRID=4326;POINT(14.5 50.0)"
    multipoly_wkt = "SRID=4326;MULTIPOLYGON(((14.4 49.9, 14.6 49.9, 14.6 50.1, 14.4 50.1, 14.4 49.9)))"
    base_kod = abs(hash(suffix)) % 800 + 100
    kraj = RuianKraj(
        nazev=f"Kraj-{suffix}",
        kod=base_kod,
        rada_id="X",
        nazev_en=f"Kraj-{suffix}-EN",
        definicni_bod=point_wkt,
        hranice=multipoly_wkt,
    )
    kraj.suppress_signal = True
    kraj.save()
    okres = RuianOkres(
        nazev=f"Okres-{suffix}",
        kraj=kraj,
        spz=f"{suffix[:2].upper()}X",
        kod=base_kod * 100,
        nazev_en=f"Okres-{suffix}-EN",
        definicni_bod=point_wkt,
        hranice=multipoly_wkt,
    )
    okres.suppress_signal = True
    okres.save()
    katastr = RuianKatastr(
        nazev=f"Katastr-{suffix}",
        kod=base_kod * 1000,
        okres=okres,
        definicni_bod=point_wkt,
        hranice=multipoly_wkt,
    )
    katastr.suppress_signal = True
    katastr.save()

    polygon_5514_wkt = (
        "SRID=5514;POLYGON((-700000 -1000000, -700000 -1100000, -800000 -1100000,"
        " -800000 -1000000, -700000 -1000000))"
    )
    # Kladyzm.cislo má max_length=8 → musíme suffix zkrátit.
    zm10 = Kladyzm.objects.create(cislo=f"Z10{suffix[:5]}", kategorie=10, the_geom=polygon_5514_wkt)
    zm50 = Kladyzm.objects.create(cislo=f"Z50{suffix[:5]}", kategorie=50, the_geom=polygon_5514_wkt)
    pian = Pian(
        ident_cely=pian_ident,
        stav=1,
        geom_system="5514",
        geom="SRID=4326;POINT(14.5 50.0)",
        geom_sjtsk="SRID=5514;POINT(-700000 -1050000)",
        typ=heslars["pian_typ"],
        presnost=heslars["presnost"],
        zm10=zm10,
        zm50=zm50,
    )
    pian.suppress_signal = True
    pian.save()
    katastr.pian = pian
    katastr.suppress_signal = True
    katastr.save()
    return katastr, pian


def create_organizace(suffix: str, heslars: dict) -> Organizace:
    """Vytvoří testovací fixture pro importní scénář.

    :param suffix: Hodnota použitá v testovacím importním scénáři.
    :param heslars: Hodnota použitá v testovacím importním scénáři.
    :return: Výsledek použitý navazujícími asercemi testu."""
    org, _ = Organizace.objects.get_or_create(
        ident_cely=f"ORG-IMP-{suffix}-001",
        defaults={
            "nazev": f"Org {suffix}",
            "nazev_zkraceny": f"ORG{suffix[:5].upper()}",
            "typ_organizace": heslars["typ_org"],
            "zverejneni_pristupnost": heslars["pristupnost"],
            "licence": heslars["licence"],
        },
    )
    return org


def create_archeologicky_zaznam(ident_cely: str, katastr, pristupnost) -> ArcheologickyZaznam:
    """Vytvoří testovací fixture pro importní scénář.

    :param ident_cely: Hodnota použitá v testovacím importním scénáři.
    :param katastr: Hodnota použitá v testovacím importním scénáři.
    :param pristupnost: Hodnota použitá v testovacím importním scénáři.
    :return: Výsledek použitý navazujícími asercemi testu."""
    az = ArcheologickyZaznam(
        ident_cely=ident_cely,
        typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_AKCE,
        pristupnost=pristupnost,
        stav=AZ_STAV_ZAPSANY,
        hlavni_katastr=katastr,
    )
    az.suppress_signal = True
    az.save()
    return az


def create_projekt_typ(suffix: str) -> Heslar:
    """Vytvoří Heslar pro typ projektu (HESLAR_PROJEKT_TYP).

    :param suffix: Přípona použitá pro unikátní identifikátor hesla.
    :return: Heslářový záznam typu projektu.
    """
    nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_PROJEKT_TYP, defaults={"nazev": "projekt_typ"})
    heslar, _ = Heslar.objects.get_or_create(
        ident_cely=f"HES-PROJTYP-{suffix}",
        defaults={
            "nazev_heslare": nazev,
            "heslo": "Projektová",
            "heslo_en": "Project-based",
            "zkratka": "P",
            "razeni": 1,
        },
    )
    return heslar


def create_projekt(ident_cely: str, katastr, typ_projektu, stav: int = 1) -> Projekt:
    """Vytvoří Projekt s minimem povinných FK (typ_projektu, hlavni_katastr).

    :param ident_cely: Celý identifikátor testovacího projektu.
    :param katastr: Hlavní katastr přiřazený projektu.
    :param typ_projektu: Heslářový typ projektu.
    :param stav: Stav projektu uložený do fixture.
    :return: Uložený projekt připravený pro importní test.
    """
    projekt = Projekt(
        ident_cely=ident_cely,
        stav=stav,
        typ_projektu=typ_projektu,
        hlavni_katastr=katastr,
    )
    projekt.suppress_signal = True
    projekt.save()
    return projekt


def create_akce_typ(suffix: str) -> Heslar:
    """Vytvoří Heslar pro hlavní/vedlejší typ akce (HESLAR_AKCE_TYP).

    :param suffix: Přípona použitá pro unikátní identifikátor hesla.
    :return: Heslářový záznam typu akce.
    """
    nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_AKCE_TYP, defaults={"nazev": "akce_typ"})
    heslar, _ = Heslar.objects.get_or_create(
        ident_cely=f"HES-AKTYP-{suffix}",
        defaults={
            "nazev_heslare": nazev,
            "heslo": "Výzkum",
            "heslo_en": "Research",
            "zkratka": "V",
            "razeni": 1,
        },
    )
    return heslar


def create_specifikace_data(suffix: str) -> Heslar:
    """Vytvoří Heslar pro specifikaci data (HESLAR_DATUM_SPECIFIKACE).

    :param suffix: Přípona použitá pro unikátní identifikátor hesla.
    :return: Heslářový záznam specifikace data.
    """
    nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_DATUM_SPECIFIKACE, defaults={"nazev": "datum_specifikace"})
    heslar, _ = Heslar.objects.get_or_create(
        ident_cely=f"HES-DATSP-{suffix}",
        defaults={
            "nazev_heslare": nazev,
            "heslo": "Den",
            "heslo_en": "Day",
            "zkratka": "D",
            "razeni": 1,
        },
    )
    return heslar


def create_akce(az, projekt=None, specifikace_data=None, hlavni_typ=None) -> Akce:
    """Vytvoří Akce navázanou na AZ. Pokud není projekt, akce je samostatná (typ 'N').

    :param az: Archeologický záznam, ke kterému akce patří.
    :param projekt: Volitelný projekt pro projektovou akci.
    :param specifikace_data: Volitelná specifikace data akce.
    :param hlavni_typ: Volitelný hlavní typ akce.
    :return: Uložená akce připravená pro importní test.
    """
    akce = Akce(
        archeologicky_zaznam=az,
        typ=Akce.TYP_AKCE_PROJEKTOVA if projekt else Akce.TYP_AKCE_SAMOSTATNA,
        projekt=projekt,
        specifikace_data=specifikace_data,
        hlavni_typ=hlavni_typ,
    )
    akce.suppress_signal = True
    akce.save()
    return akce


def create_dokumentacni_jednotka(ident_cely: str, az, pian, dj_typ) -> DokumentacniJednotka:
    """Vytvoří testovací fixture pro importní scénář.

    :param ident_cely: Hodnota použitá v testovacím importním scénáři.
    :param az: Hodnota použitá v testovacím importním scénáři.
    :param pian: Hodnota použitá v testovacím importním scénáři.
    :param dj_typ: Hodnota použitá v testovacím importním scénáři.
    :return: Výsledek použitý navazujícími asercemi testu."""
    dj = DokumentacniJednotka(
        ident_cely=ident_cely,
        negativni_jednotka=False,
        nazev=f"DJ {ident_cely}",
        archeologicky_zaznam=az,
        pian=pian,
        typ=dj_typ,
    )
    dj.suppress_signal = True
    dj.save()
    return dj
