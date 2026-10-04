"""Sdílené pomocné funkce pro vytváření testovacích dat v mapper testech."""

from core.constants import DOKUMENT_RELATION_TYPE
from core.models import Soubor, SouborVazby
from django.conf import settings
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

    # Organizace is shared by every fixture dokument — its nazev_zkraceny is unique, so a second
    # call must reuse the existing row instead of inserting a duplicate.
    organizace = Organizace.objects.filter(ident_cely="ORG-T-001").first()
    if organizace is None:
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


def create_soubor_fixture(
    dokument,
    nazev="dokument.pdf",
    uuid="11111111-2222-3333-4444-555555555555",
    with_path=True,
    with_navazany_objekt=True,
):
    """Vytvoří uložený ``Soubor`` navázaný na dokument, včetně vazby na historii.

    :param dokument: Dokument, ke kterému se soubor naváže.
    :param nazev: Název souboru.
    :param uuid: UUID kontejneru souboru ve Fedoře, ze kterého se skládá ``path``.
    :param with_path: Pokud ``False``, soubor zůstane bez ``path`` (nemá tedy ``repository_uuid``).
    :param with_navazany_objekt: Pokud ``False``, vazba se k dokumentu nepřipojí, takže
        ``vazba.navazany_objekt`` je ``None`` (soubor nemá nadřazený záznam).
    :return: Uloženou instanci ``Soubor`` s vyplněnou vazbou na historii.
    """
    vazba = SouborVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
    vazba.suppress_signal = True
    vazba.save()
    if with_navazany_objekt:
        dokument.soubory = vazba
        dokument.suppress_signal = True
        dokument.save()
    soubor = Soubor(
        nazev=nazev,
        mimetype="application/pdf",
        vazba=vazba,
        size_mb=1,
        path=(f"rest/{settings.FEDORA_SERVER_NAME}/record/{dokument.ident_cely}/file/{uuid}" if with_path else None),
    )
    soubor.suppress_signal = True
    soubor.save()
    soubor.create_soubor_vazby()
    return soubor
