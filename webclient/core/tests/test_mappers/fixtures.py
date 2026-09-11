"""Sdílené pomocné funkce pro vytváření testovacích dat v mapper testech."""

from dokument.models import Dokument
from ez.models import ExterniZdroj
from heslar.hesla import (
    HESLAR_DOKUMENT_MATERIAL,
    HESLAR_DOKUMENT_RADA,
    HESLAR_DOKUMENT_TYP,
    HESLAR_EXTERNI_ZDROJ_TYP,
    HESLAR_LICENCE,
    HESLAR_ORGANIZACE_TYP,
    HESLAR_PRISTUPNOST,
)
from heslar.models import Heslar, HeslarNazev
from uzivatel.models import Organizace


def create_dokument_fixture(ident_cely="C-TX-000001", stav=1):
    """Vytvoří instanci Dokument se všemi povinnými FK závislostmi.

    :param ident_cely: Unikátní identifikátor dokumentu.
    :param stav: Stav dokumentu (výchozí 1 = zapsaný).
    :return: Uloženou instanci Dokument.
    """
    hn_rada = HeslarNazev.objects.get_or_create(pk=HESLAR_DOKUMENT_RADA, defaults={"nazev": "Dokument rada"})[0]
    hn_typ = HeslarNazev.objects.get_or_create(pk=HESLAR_DOKUMENT_TYP, defaults={"nazev": "Dokument typ"})[0]
    hn_material = HeslarNazev.objects.get_or_create(
        pk=HESLAR_DOKUMENT_MATERIAL, defaults={"nazev": "Dokument material"}
    )[0]
    hn_pristupnost = HeslarNazev.objects.get_or_create(pk=HESLAR_PRISTUPNOST, defaults={"nazev": "Přístupnost"})[0]
    hn_licence = HeslarNazev.objects.get_or_create(pk=HESLAR_LICENCE, defaults={"nazev": "Licence"})[0]
    hn_org_typ = HeslarNazev.objects.get_or_create(pk=HESLAR_ORGANIZACE_TYP, defaults={"nazev": "Typ organizace"})[0]

    heslar_rada = Heslar.objects.get_or_create(
        ident_cely="HES-RADA-001",
        defaults={"heslo": "Fotografie", "heslo_en": "Photography", "nazev_heslare": hn_rada},
    )[0]
    heslar_typ = Heslar.objects.get_or_create(
        ident_cely="HES-DOCTYP-001",
        defaults={"heslo": "Fotodokumentace", "heslo_en": "Photodocumentation", "nazev_heslare": hn_typ},
    )[0]
    heslar_material = Heslar.objects.get_or_create(
        ident_cely="HES-MAT-001",
        defaults={"heslo": "Digitální", "heslo_en": "Digital", "nazev_heslare": hn_material},
    )[0]
    heslar_pristupnost = Heslar.objects.get_or_create(
        ident_cely="HES-PRIST-001",
        defaults={"heslo": "Veřejná", "heslo_en": "Public", "nazev_heslare": hn_pristupnost},
    )[0]
    heslar_licence = Heslar.objects.get_or_create(
        ident_cely="HES-LIC-001",
        defaults={"heslo": "CC BY", "heslo_en": "CC BY", "nazev_heslare": hn_licence},
    )[0]
    heslar_org_typ = Heslar.objects.get_or_create(
        ident_cely="HES-ORGTYP-001",
        defaults={"heslo": "Veřejná", "heslo_en": "Public", "nazev_heslare": hn_org_typ},
    )[0]

    organizace = Organizace(
        ident_cely="ORG-T-001",
        nazev="Testovací ústav",
        nazev_zkraceny="TU",
        nazev_zkraceny_en="TI",
        typ_organizace=heslar_org_typ,
        zverejneni_pristupnost=heslar_pristupnost,
        licence=heslar_licence,
    )
    organizace.suppress_signal = True
    organizace.save()

    dokument = Dokument(
        ident_cely=ident_cely,
        stav=stav,
        rada=heslar_rada,
        typ_dokumentu=heslar_typ,
        organizace=organizace,
        pristupnost=heslar_pristupnost,
        material_originalu=heslar_material,
    )
    dokument.suppress_signal = True
    dokument.save()
    return dokument


def create_externi_zdroj_fixture(ident_cely="BIB-C-EZ-000001", stav=1):
    """Vytvoří instanci ExterniZdroj se všemi povinnými FK závislostmi.

    :param ident_cely: Unikátní identifikátor externího zdroje.
    :param stav: Stav externího zdroje (výchozí 1 = zapsaný).
    :return: Uloženou instanci ExterniZdroj.
    """
    hn_ez_typ = HeslarNazev.objects.get_or_create(pk=HESLAR_EXTERNI_ZDROJ_TYP, defaults={"nazev": "Externi zdroj typ"})[
        0
    ]
    heslar_ez_typ = Heslar.objects.get_or_create(
        ident_cely="HES-EZTYP-001",
        defaults={"heslo": "Článek", "heslo_en": "Article", "nazev_heslare": hn_ez_typ},
    )[0]
    externi_zdroj = ExterniZdroj(ident_cely=ident_cely, stav=stav, typ=heslar_ez_typ)
    externi_zdroj.suppress_signal = True
    externi_zdroj.save()
    return externi_zdroj
