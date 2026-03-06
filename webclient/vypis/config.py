from django.utils.translation import gettext_lazy as _

from .fields import (
    ChooseField,
    DoubleField,
    DoubleFieldNum,
    Field,
    ForeignDoubleField,
    ForeignDoubleFieldNum,
    ForeignField,
    ForeignGeomGmlField,
    ForeignGeomWktField,
    ForeignManyToManyField,
    GeomGmlField,
    GeomWktField,
    HistorieRepeatableField,
    HistorieSubSectionField,
    KomponentaRepeatableSectionNameWithAccessor,
    ManyToManyField,
    Model3dKomponentaAktivityField,
    Model3dKomponentaField,
    NeidentAkceSubSectionField,
    OznamovatelSectionNameWithAccessor,
    PianSectionNameWithAccessor,
    RepeatableField,
    RepeatableSectionNameWithAccessor,
    SectionNameWithAccessor,
    SimpleSectionTemplateName,
    SouborDownloadField,
    SouborField,
    SouboryRepeatableSectionNameWithAccessor,
    StatusField,
    SubSectionField,
    VbRepeatableField,
    ZjisteniField,
)


def get_config(name):
    """
    Vrací config. v aplikaci.

    :param name: Parametr ``name`` předává se do volání ``get()``, vstupuje do návratové hodnoty.

        :return: Vrací výsledek volání ``get()``.
    """
    configs = {
        "dokument": DOKUMENTY_CONFIG,
        "projekt": PROJEKTY_CONFIG,
        "akce": AKCE_CONFIG,
        "lokalita": LOKALITA_CONFIG,
        "pas": PAS_CONFIG,
        "model": MODEL_CONFIG,
        "ez": EZ_CONFIG,
    }
    return configs.get(name)


NEIDENT_AKCE_CONFIG = {
    "section_name": SimpleSectionTemplateName(_("vypis.dokumenty.neidentifikovane_akce.section_name")),
    "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
    "katastr": Field(_("vypis.dokumenty.neidentifikovane_akce.katastr.label"), "katastr"),
    "vedouci": ManyToManyField(_("vypis.dokumenty.neidentifikovane_akce.vedouci.label"), "vedouci"),
    "rok": DoubleFieldNum(
        _("vypis.dokumenty.neidentifikovane_akce.rok.label"),
        ["rok_zahajeni", "rok_ukonceni"],
    ),
    "lokalizace": Field(
        _("vypis.dokumenty.neidentifikovane_akce.lokalizace.label"),
        "lokalizace",
    ),
    "popis": Field(
        _("vypis.dokumenty.neidentifikovane_akce.popis.label"),
        "popis",
    ),
    "poznamka": Field(
        _("vypis.dokumenty.neidentifikovane_akce.poznamka.label"),
        "poznamka",
    ),
    "pian": Field(
        _("vypis.dokumenty.neidentifikovane_akce.pian.label"),
        "pian",
    ),
}

NALEZY_CONFIG = {
    "section_name": SimpleSectionTemplateName(_("vypis.nalezy.section_name")),
    "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
    "objekty": RepeatableField(
        _("vypis.nalezy.objekty.label"),
        ["druh", "specifikace", "pocet", "poznamka"],
        "objekty",
        "vypis/dokumenty/nalezy.html",
    ),
    "predmety": RepeatableField(
        _("vypis.nalezy.predmety.label"),
        ["druh", "specifikace", "pocet", "poznamka"],
        "predmety",
        "vypis/dokumenty/nalezy.html",
    ),
}

KOMPONENTY_DOKU_CONFIG = {
    "section_name": KomponentaRepeatableSectionNameWithAccessor(
        _("vypis.dokumenty.komponenty.section_name"),
        ["get_ident_cely_link", "obdobi", "jistota", "presna_datace", "areal", "aktivity"],
        "komponenty",
        "komponenta_vazby__casti_dokumentu",
    ),
    "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
    "poznamka": Field(_("vypis.dokumenty.komponenty.poznamka.label"), "poznamka"),
    "nalezy": SubSectionField(NALEZY_CONFIG),
}

KOMPONENTY_DJ_CONFIG = {
    "section_name": KomponentaRepeatableSectionNameWithAccessor(
        _("vypis.dj.komponenty.section_name"),
        ["get_ident_cely_link", "obdobi", "jistota", "presna_datace", "areal", "aktivity"],
        "komponenty",
        "komponenta_vazby__dokumentacni_jednotka",
    ),
    "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
    "poznamka": Field(_("vypis.dj.komponenty.poznamka.label"), "poznamka"),
    "nalezy": SubSectionField(NALEZY_CONFIG),
}

PIAN_CONFIG = {
    "section_name": PianSectionNameWithAccessor(
        _("vypis.pian.pian.section_name"), ["get_ident_cely_link", "get_stav_display", "typ", "presnost"], "pian"
    ),
    "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
    "zakladni_mapa": ForeignField(_("vypis.pian.zakladni_mapa.label"), "zm10__cislo", "pian"),
    "primarni_epsg": ForeignField(_("vypis.pian.primarni_epsg.label"), "geom_system", "pian"),
    "geometrie_gml": ForeignGeomGmlField(_("vypis.pian.geometrie_gml.label"), "geom", "pian"),
    "geometrie_gml_sjtsk": ForeignGeomGmlField(_("vypis.pian.geometrie_gml_sjtsk.label"), "geom_sjtsk", "pian"),
    "geometrie_wkt": ForeignGeomWktField(_("vypis.pian.geometrie_wkt.label"), "geom", "pian"),
    "geometrie_wkt_sjtsk": ForeignGeomWktField(_("vypis.pian.geometrie_wkt_sjtsk.label"), "geom_sjtsk", "pian"),
    "historie": HistorieSubSectionField("pian", _("vypis.pian.historie.section_name")),
}

ADB_CONFIG = {
    "section_name": SectionNameWithAccessor(_("vypis.adb.adb.section_name"), "get_ident_cely_link"),
    "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
    "typ_sondy": Field(_("vypis.adb.typ_sondy.label"), "typ_sondy"),
    "uzivatelske_oznaceni_sondy": Field(_("vypis.adb.uzivatelske_oznaceni_sondy.label"), "uzivatelske_oznaceni_sondy"),
    "trat": Field(_("vypis.adb.trat.label"), "trat"),
    "cislo_popisne": Field(_("vypis.adb.cislo_popisne.label"), "cislo_popisne"),
    "parcelni_cislo": Field(_("vypis.adb.parcelni_cislo.label"), "parcelni_cislo"),
    "podnet": Field(_("vypis.adb.podnet.label"), "podnet"),
    "stratigraficke_jednotky": Field(_("vypis.adb.stratigraficke_jednotky.label"), "stratigraficke_jednotky"),
    "autor_popisu": Field(_("vypis.adb.autor_popisu.label"), "autor_popisu"),
    "rok_popisu": Field(_("vypis.adb.rok_popisu.label"), "rok_popisu"),
    "autor_revize": Field(_("vypis.adb.autor_revize.label"), "autor_revize"),
    "rok_revize": Field(_("vypis.adb.rok_revize.label"), "rok_revize"),
    "poznamka": Field(_("vypis.adb.poznamka.label"), "poznamka"),
    "vb": VbRepeatableField(
        _("vypis.adb.vb.label"), ["ident_cely", "typ", "poloha_gml", "poloha_wkt"], "vb", "vypis/akce/vb.html", "adb"
    ),
}

DOKUMENTY_CONFIG = {
    "title": _("vypis.dokumenty.title"),
    "main_sections": {
        "header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/dokumenty/header.html"),
            "ident_cely": Field(_("vypis.dokumenty.ident_cely.label"), "ident_cely"),
            "stav": StatusField(_("vypis.dokumenty.stav.label"), "get_stav_display"),
            "autor": ManyToManyField(_("vypis.dokumenty.autor.label"), "autori"),
            "rok_vzniku": Field(_("vypis.dokumenty.rok_vzniku.label"), "rok_vzniku"),
        },
        "sub_header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/sub_header.html"),
            "typ": Field(_("vypis.dokumenty.typ.label"), "typ_dokumentu"),
            "material": Field(_("vypis.dokumenty.material.label"), "material_originalu"),
            "rada": Field(_("vypis.dokumenty.rada.label"), "rada"),
            "pristupnost": Field(_("vypis.dokumenty.pristupnost.label"), "pristupnost"),
        },
        "under_header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/simple_section_without_name.html"),
            "doi": Field(_("vypis.dokumenty.doi.label"), "doi"),
            "organizace": ForeignField(_("vypis.dokumenty.organizace.label"), "get_nazev", "organizace"),
            "popis": Field(_("vypis.dokumenty.popis.label"), "popis"),
        },
    },
    "sections": {
        "popis_dokumentu": {
            "section_name": SimpleSectionTemplateName(_("vypis.dokumenty.popis_dokumentu.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "jazyk": ManyToManyField(_("vypis.dokumenty.popis_dokumentu.jazyk.label"), "jazyky"),
            "poznamka": Field(_("vypis.dokumenty.popis_dokumentu.poznamka.label"), "poznamka"),
            "posudky": ManyToManyField(_("vypis.dokumenty.popis_dokumentu.posudky.label"), "posudky"),
            "ulozeni_originalu": Field(
                _("vypis.dokumenty.popis_dokumentu.ulozeni_originalu.label"), "ulozeni_originalu"
            ),
            "oznaceni_originalu": Field(
                _("vypis.dokumenty.popis_dokumentu.oznaceni_originalu.label"), "oznaceni_originalu"
            ),
            "datum_zverejneni": Field(_("vypis.dokumenty.popis_dokumentu.datum_zverejneni.label"), "datum_zverejneni"),
            "objekt_kontext": ForeignField(
                _("vypis.dokumenty.popis_dokumentu.objekt_kontext.label"), "cislo_objektu", "extra_data"
            ),
            "primarni_epsg": ForeignField(
                _("vypis.dokumenty.popis_dokumentu.primarni_epsg.label"), "geom_system", "extra_data"
            ),
            "poloha_gml": ForeignGeomGmlField(
                _("vypis.dokumenty.popis_dokumentu.poloha_gml.label"), "geom", "extra_data"
            ),
            "poloha_gml_sjtsk": ForeignGeomGmlField(
                _("vypis.dokumenty.popis_dokumentu.poloha_gml_sjtsk.label"), "geom_sjtsk", "extra_data"
            ),
            "poloha_wkt": ForeignGeomWktField(
                _("vypis.dokumenty.popis_dokumentu.poloha_wkt.label"), "geom", "extra_data"
            ),
            "poloha_wkt_sjtsk": ForeignGeomWktField(
                _("vypis.dokumenty.popis_dokumentu.poloha_wkt_sjtsk.label"), "geom_sjtsk", "extra_data"
            ),
            "format": ForeignField(_("vypis.dokumenty.popis_dokumentu.format.label"), "format", "extra_data"),
            "vyska": ForeignField(_("vypis.dokumenty.popis_dokumentu.vyska.label"), "vyska", "extra_data"),
            "sirka": ForeignField(_("vypis.dokumenty.popis_dokumentu.sirka.label"), "sirka", "extra_data"),
            "meritko": ForeignField(_("vypis.dokumenty.popis_dokumentu.meritko.label"), "meritko", "extra_data"),
            "zachovalost": ForeignField(
                _("vypis.dokumenty.popis_dokumentu.zachovalost.label"), "zachovalost", "extra_data"
            ),
            "nahrada": ForeignField(_("vypis.dokumenty.popis_dokumentu.nahrada.label"), "nahrada", "extra_data"),
            "pocet_variant_originalu": ForeignField(
                _("vypis.dokumenty.popis_dokumentu.pocet_variant_originalu.label"),
                "pocet_variant_originalu",
                "extra_data",
            ),
            "odkaz": ForeignField(_("vypis.dokumenty.popis_dokumentu.odkaz.label"), "odkaz", "extra_data"),
            "datum_vzniku": ForeignField(
                _("vypis.dokumenty.popis_dokumentu.datum_vzniku.label"), "datum_vzniku", "extra_data"
            ),
            "zeme": ForeignField(_("vypis.dokumenty.popis_dokumentu.zeme.label"), "zeme", "extra_data"),
            "region": ForeignField(_("vypis.dokumenty.popis_dokumentu.region.label"), "region_extra", "extra_data"),
            "typ_udalosti": ForeignField(
                _("vypis.dokumenty.popis_dokumentu.typ_udalosti.label"), "udalost_typ", "extra_data"
            ),
            "udalost": ForeignField(_("vypis.dokumenty.popis_dokumentu.udalost.label"), "udalost", "extra_data"),
            "roky": ForeignDoubleFieldNum(
                _("vypis.dokumenty.popis_dokumentu.roky.label"), ["rok_od", "rok_do"], "extra_data"
            ),
            "osoba": ManyToManyField(_("vypis.dokumenty.popis_dokumentu.osoba.label"), "osoby"),
            "duveryhodnost": ForeignField(
                _("vypis.dokumenty.popis_dokumentu.duveryhodnost.label"), "duveryhodnost", "extra_data"
            ),
            "licence": Field(_("vypis.dokumenty.popis_dokumentu.licence.label"), "licence"),
        },
        "let": {
            "section_name": SectionNameWithAccessor(_("vypis.dokumenty.let.section_name"), "ident_cely", "let"),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "datum": ForeignField(_("vypis.dokumenty.let.datum.label"), "datum", "let"),
            "cas": ForeignDoubleFieldNum(_("vypis.dokumenty.let.cas.label"), ["hodina_zacatek", "hodina_konec"], "let"),
            "trasa": ForeignDoubleField(_("vypis.dokumenty.let.trasa.label"), ["letiste_start", "letiste_cil"], "let"),
            "ucel_letu": ForeignField(_("vypis.dokumenty.let.ucel_letu.label"), "ucel_letu", "let"),
            "pozorovatel": ForeignField(_("vypis.dokumenty.let.pozorovatel.label"), "pozorovatel", "let"),
            "pilot": ForeignField(_("vypis.dokumenty.let.pilot.label"), "pilot", "let"),
            "organizace": ForeignField(_("vypis.dokumenty.let.organizace.label"), "organizace__get_nazev", "let"),
            "uzivatelske_oznaceni": ForeignField(
                _("vypis.dokumenty.let.uzivatelske_oznaceni.label"), "uzivatelske_oznaceni", "let"
            ),
            "fotoaparat": ForeignField(_("vypis.dokumenty.let.fotoaparat.label"), "fotoaparat", "let"),
            "typ_letounu": ForeignField(_("vypis.dokumenty.let.typ_letounu.label"), "typ_letounu", "let"),
            "pocasi": ForeignField(_("vypis.dokumenty.let.pocasi.label"), "pocasi", "let"),
            "dohlednost": ForeignField(_("vypis.dokumenty.let.dohlednost.label"), "dohlednost", "let"),
        },
        "dokumentove_tvary": {
            "section_name": SimpleSectionTemplateName(_("vypis.dokumenty.dokumentove_tvary.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "tvary": RepeatableField(
                _("vypis.dokumenty.dokumentove_tvary.tvary.label"),
                ["tvar", "poznamka"],
                "tvary",
                "vypis/dokumenty/tvar.html",
            ),
        },
        "dokument_casti": {
            "section_name": RepeatableSectionNameWithAccessor(
                _("vypis.dokumenty.dokument_casti.section_name"),
                ["get_ident_cely_link", "poznamka"],
                "dokument_casti",
                "dokument",
            ),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "dok_zaznam": ChooseField(
                _("vypis.dokumenty.dokument_casti.dok_zaznam.label"), ["archeologicky_zaznam", "projekt"]
            ),
            "komponenty": SubSectionField(KOMPONENTY_DOKU_CONFIG),
            "neident_akce": NeidentAkceSubSectionField(NEIDENT_AKCE_CONFIG),
        },
        "historie": {
            "section_name": SimpleSectionTemplateName(_("vypis.dokumenty.historie.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "historie": HistorieRepeatableField(
                _("vypis.dokumenty.historie.label"),
                ["datum_zmeny", "uzivatel_protected", "get_typ_zmeny_display", "poznamka"],
                "historie",
                "vypis/historie.html",
            ),
        },
        "soubory": {
            "section_name": SouboryRepeatableSectionNameWithAccessor(
                _("vypis.dokumenty.soubory.section_name"), ["nazev", "mimetype"], "soubory"
            ),
            "template": SimpleSectionTemplateName("vypis/soubory.html"),
            "small_thumbnail": SouborField(
                _("vypis.dokumenty.dokument_casti.small_thumbnail.label"), "small_thumbnail", "dokument"
            ),
            "path": SouborDownloadField(_("vypis.dokumenty.dokument_casti.path.label"), "path", "dokument"),
            "rozsah": Field(_("vypis.dokumenty.dokument_casti.rozsah.label"), "rozsah"),
            "size_mb": Field(_("vypis.dokumenty.dokument_casti.size_mb.label"), "size_mb"),
            "sha_512": Field(_("vypis.dokumenty.dokument_casti.sha_512.label"), "sha_512"),
            "historie": HistorieSubSectionField(None, _("vypis.dokumenty.soubory.historie.label")),
        },
    },
}

PROJEKTY_CONFIG = {
    "title": _("vypis.projekt.title"),
    "main_sections": {
        "header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/projekty/header.html"),
            "ident_cely": Field(_("vypis.projekty.ident_cely.label"), "ident_cely"),
            "stav": StatusField(_("vypis.projekty.stav.label"), "get_stav_display"),
            "hlavni_katastr": Field(_("vypis.projekty.hlavni_katastr.label"), "hlavni_katastr"),
            "vedouci_projektu": Field(_("vypis.projekty.vedouci_projektu.label"), "vedouci_projektu"),
        },
        "sub_header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/sub_header.html"),
            "typ_projektu": Field(_("vypis.projekty.typ.label"), "typ_projektu"),
            "datum_provedeni": DoubleField(
                _("vypis.projekty.datum_provedeni.label"), ["datum_zahajeni", "datum_ukonceni"]
            ),
            "pristupnost": Field(_("vypis.projekty.pristupnost.label"), "pristupnost"),
        },
        "under_header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/simple_section_without_name.html"),
            "organizace": ForeignField(_("vypis.projekty.organizace.label"), "get_nazev", "organizace"),
            "dalsi_katastry": ManyToManyField(_("vypis.projekty.dalsi_katastry.label"), "katastry"),
            "podnet": Field(_("vypis.projekty.podnet.label"), "podnet"),
        },
    },
    "sections": {
        "popis_projektu": {
            "section_name": SimpleSectionTemplateName(_("vypis.projekty.popis_projektu.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "lokalizace": Field(_("vypis.projekty.popis_projektu.lokalizace.label"), "lokalizace"),
            "parcelni_cislo": Field(_("vypis.projekty.popis_projektu.parcelni_cislo.label"), "parcelni_cislo"),
            "primarni_epsg": Field(_("vypis.projekty.primarni_epsg.label"), "geom_system"),
            "poloha_gml": GeomGmlField(_("vypis.projekty.popis_projektu.poloha_gml.label"), "geom"),
            "poloha_gml_sjtsk": GeomGmlField(_("vypis.projekty.popis_projektu.poloha_gml_sjtsk.label"), "geom_sjtsk"),
            "poloha_wkt": GeomWktField(_("vypis.projekty.popis_projektu.poloha_wkt.label"), "geom"),
            "poloha_wkt_sjtsk": GeomWktField(_("vypis.projekty.popis_projektu.poloha_wkt_sjtsk.label"), "geom_sjtsk"),
            "planovane_zahajeni": Field(
                _("vypis.projekty.popis_projektu.planovane_zahajeni.label"), "planovane_zahajeni_vypis"
            ),
            "uzivatelske_oznaceni": Field(
                _("vypis.projekty.popis_projektu.uzivatelske_oznaceni.label"), "uzivatelske_oznaceni"
            ),
            "pamatkova_ochrana": Field(_("vypis.projekty.popis_projektu.pamatkova_ochrana.label"), "kulturni_pamatka"),
            "rejstrikove_cislo": Field(
                _("vypis.projekty.popis_projektu.rejstrikove_cislo.label"), "kulturni_pamatka_cislo"
            ),
            "nazev_pamatky": Field(_("vypis.projekty.popis_projektu.nazev_pamatky.label"), "kulturni_pamatka_popis"),
            "oznaceni_stavby": Field(_("vypis.projekty.popis_projektu.oznaceni_stavby.label"), "oznaceni_stavby"),
            "termin_odevzdani_nz": Field(
                _("vypis.projekty.popis_projektu.termin_odevzdani_nz.label"), "termin_odevzdani_nz"
            ),
        },
        "oznamovatel": {
            "section_name": OznamovatelSectionNameWithAccessor(
                _("vypis.projekty.oznamovatel.section_name"), "oznamovatel", "oznamovatel"
            ),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "odpovedna_osoba": ForeignField(
                _("vypis.projekty.oznamovatel.odpovedna_osoba.label"), "odpovedna_osoba", "oznamovatel"
            ),
            "adresa": ForeignField(_("vypis.projekty.oznamovatel.adresa.label"), "adresa", "oznamovatel"),
            "telefon": ForeignField(_("vypis.projekty.oznamovatel.telefon.label"), "telefon", "oznamovatel"),
            "email": ForeignField(_("vypis.projekty.oznamovatel.email.label"), "email", "oznamovatel"),
            "poznamka": ForeignField(_("vypis.projekty.oznamovatel.poznamka.label"), "poznamka", "oznamovatel"),
        },
        "historie": {
            "section_name": SimpleSectionTemplateName(_("vypis.projekty.historie.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "historie": HistorieRepeatableField(
                _("vypis.projekty.historie.label"),
                ["datum_zmeny", "uzivatel_protected", "get_typ_zmeny_display", "poznamka"],
                "historie",
                "vypis/historie.html",
            ),
        },
        "soubory": {
            "section_name": SouboryRepeatableSectionNameWithAccessor(
                _("vypis.projekty.soubory.section_name"), ["nazev", "mimetype"], "soubory"
            ),
            "template": SimpleSectionTemplateName("vypis/soubory.html"),
            "small_thumbnail": SouborField(
                _("vypis.projekty.soubory.small_thumbnail.label"), "small_thumbnail", "projekt"
            ),
            "path": SouborDownloadField(_("vypis.projekty.soubory.path.label"), "path", "projekt"),
            "rozsah": Field(_("vypis.projekty.soubory.rozsah.label"), "rozsah"),
            "size_mb": Field(_("vypis.projekty.soubory.size_mb.label"), "size_mb"),
            "sha_512": Field(_("vypis.projekty.soubory.sha_512.label"), "sha_512"),
            "historie": HistorieSubSectionField(None, _("vypis.projekty.soubory.historie.label")),
        },
        "archeologicke_zaznamy": {
            "section_name": SimpleSectionTemplateName(_("vypis.projekty.archeologicke_zaznamy.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "akce": RepeatableField(
                _("vypis.projekty.archeologicke_zaznamy.label"),
                ["ident_cely"],
                "archeologicky_zaznam",
                "vypis/souvisejici_zaznam.html",
                "akce__projekt",
            ),
        },
        "samostante_nalezy": {
            "section_name": SimpleSectionTemplateName(_("vypis.projekty.samostante_nalezy.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "sn": RepeatableField(
                _("vypis.projekty.samostante_nalezy.label"),
                ["ident_cely", "druh_nalezu", "specifikace"],
                "samostatny_nalez",
                "vypis/souvisejici_zaznam_pas.html",
            ),
        },
        "dokumenty": {
            "section_name": SimpleSectionTemplateName(_("vypis.projekty.dokumenty.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "dokumenty": RepeatableField(
                _("vypis.projekty.dokumenty.label"),
                ["dokument__ident_cely", "dokument__autori_snapshot", "dokument__rok_vzniku"],
                "dokument_casti",
                "vypis/souvisejici_zaznam_dok.html",
            ),
        },
    },
}

AKCE_CONFIG = {
    "title": _("vypis.akce.title"),
    "main_sections": {
        "header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/akce/header.html"),
            "ident_cely": Field(_("vypis.akce.ident_cely.label"), "ident_cely"),
            "stav": StatusField(_("vypis.akce.stav.label"), "get_stav_display"),
            "hlavni_katastr": Field(_("vypis.akce.hlavni_katastr.label"), "hlavni_katastr"),
            "hlavni_vedouci": ForeignField(_("vypis.akce.hlavni_vedouci.label"), "hlavni_vedouci", "akce"),
        },
        "sub_header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/akce/sub_header.html"),
            "specifikace_data": ForeignField(_("vypis.akce.specifikace_data.label"), "specifikace_data", "akce"),
            "datum_zahajeni": ForeignField(_("vypis.akce.datum_zahajeni.label"), "datum_zahajeni", "akce"),
            "datum_ukonceni": ForeignField(_("vypis.akce.datum_ukonceni.label"), "datum_ukonceni", "akce"),
            "je_nz": ForeignField(_("vypis.akce.je_nz.label"), "je_nz", "akce"),
            "odlozena_nz": ForeignField(_("vypis.akce.odlozena_nz.label"), "odlozena_nz", "akce"),
            "pristupnost": Field(_("vypis.akce.pristupnost.label"), "pristupnost"),
        },
        "under_header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/simple_section_without_name.html"),
            "organizace": ForeignField(_("vypis.akce.organizace.label"), "organizace__get_nazev", "akce"),
            "katastry": ManyToManyField(_("vypis.akce.katastry.label"), "katastry"),
            "lokalizace_okolnosti": ForeignField(
                _("vypis.akce.lokalizace_okolnosti.label"), "lokalizace_okolnosti", "akce"
            ),
        },
    },
    "sections": {
        "popis_akce": {
            "section_name": SimpleSectionTemplateName(_("vypis.akce.popis_akce.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "projekt": ForeignField(_("vypis.akce.projekt.label"), "projekt__get_ident_cely_link", "akce"),
            "hlavni_typ": ForeignField(_("vypis.akce.hlavni_typ.label"), "hlavni_typ", "akce"),
            "vedlejsi_typ": ForeignField(_("vypis.akce.vedlejsi_typ.label"), "vedlejsi_typ", "akce"),
            "ostatni_vedouci": ForeignManyToManyField(_("vypis.akce.ostatni_vedouci.label"), "akcevedouci_set", "akce"),
            "uzivatelske_oznaceni": Field(_("vypis.akce.uzivatelske_oznaceni.label"), "uzivatelske_oznaceni"),
            "ulozeni_nalezu": ForeignField(_("vypis.akce.ulozeni_nalezu.label"), "ulozeni_nalezu", "akce"),
            "ulozeni_dokumentace": ForeignField(
                _("vypis.akce.ulozeni_dokumentace.label"), "ulozeni_dokumentace", "akce"
            ),
            "souhrn_upresneni": ForeignField(_("vypis.akce.souhrn_upresneni.label"), "souhrn_upresneni", "akce"),
        },
        "dokumentacni_jednotka": {
            "section_name": RepeatableSectionNameWithAccessor(
                _("vypis.akce.dokumentacni_jednotka.section_name"),
                ["get_ident_cely_link", "typ", "nazev"],
                "dokumentacni_jednotka",
                "archeologicky_zaznam",
            ),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "typ_zjisteni": ZjisteniField(
                _("vypis.akce.dokumentacni_jednotka.typ_zjisteni.label"), "negativni_jednotka"
            ),
            "pian": SubSectionField(PIAN_CONFIG),
            "adb": SubSectionField(ADB_CONFIG, "adb"),
            "komponenty": SubSectionField(KOMPONENTY_DJ_CONFIG),
        },
        "historie": {
            "section_name": SimpleSectionTemplateName(_("vypis.akce.historie.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "historie": HistorieRepeatableField(
                _("vypis.akce.historie.label"),
                ["datum_zmeny", "uzivatel_protected", "get_typ_zmeny_display", "poznamka"],
                "historie",
                "vypis/historie.html",
            ),
        },
        "ext_zdroje": {
            "section_name": SimpleSectionTemplateName(_("vypis.akce.ext_zdroje.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "ext_zdroje": RepeatableField(
                _("vypis.akce.ext_zdroje.label"),
                [
                    "externi_zdroj__ident_cely",
                    "externi_zdroj__autori_snapshot",
                    "externi_zdroj__rok_vydani_vzniku",
                    "paginace",
                ],
                "ext_odkaz",
                "vypis/akce/ext_odkazy.html",
                "archeologicky_zaznam",
            ),
        },
        "dokumenty": {
            "section_name": SimpleSectionTemplateName(_("vypis.akce.dokumenty.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "dokumenty": RepeatableField(
                _("vypis.akce.dokumenty.label"),
                ["dokument__ident_cely", "dokument__autori_snapshot", "dokument__rok_vzniku"],
                "dokument_casti",
                "vypis/souvisejici_zaznam_dok.html",
                "archeologicky_zaznam",
            ),
        },
    },
}

LOKALITA_CONFIG = {
    "title": _("vypis.lokalita.title"),
    "main_sections": {
        "header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/lokalita/header.html"),
            "ident_cely": Field(_("vypis.lokalita.ident_cely.label"), "ident_cely"),
            "stav": StatusField(_("vypis.lokalita.stav.label"), "get_stav_display"),
            "hlavni_katastr": Field(_("vypis.lokalita.hlavni_katastr.label"), "hlavni_katastr"),
            "nazev": ForeignField(_("vypis.lokalita.hlavni_vedouci.label"), "nazev", "lokalita"),
        },
        "sub_header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/sub_header.html"),
            "typ_lokality": ForeignField(_("vypis.lokalita.typ_lokality.label"), "typ_lokality", "lokalita"),
            "druh": ForeignField(_("vypis.lokalita.druh.label"), "druh", "lokalita"),
            "zachovalost": ForeignField(_("vypis.lokalita.zachovalost.label"), "zachovalost", "lokalita"),
            "jistota": ForeignField(_("vypis.lokalita.jistota.label"), "jistota", "lokalita"),
            "pristupnost": Field(_("vypis.lokalita.pristupnost.label"), "pristupnost"),
        },
        "under_header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/simple_section_without_name.html"),
            "igsn": ForeignField(_("vypis.lokalita.igsn.label"), "igsn", "lokalita"),
            "katastry": ManyToManyField(_("vypis.lokalita.katastry.label"), "katastry"),
        },
    },
    "sections": {
        "popis_lokality": {
            "section_name": SimpleSectionTemplateName(_("vypis.lokalita.popis_lokality.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "uzivatelske_oznaceni": Field(_("vypis.lokalita.uzivatelske_oznaceni.label"), "uzivatelske_oznaceni"),
            "popis": ForeignField(_("vypis.lokalita.popis.label"), "popis", "lokalita"),
            "poznamka": ForeignField(_("vypis.lokalita.poznamka.label"), "poznamka", "lokalita"),
        },
        "dokumentacni_jednotka": {
            "section_name": RepeatableSectionNameWithAccessor(
                _("vypis.akce.dokumentacni_jednotka.section_name"),
                ["get_ident_cely_link", "typ", "nazev"],
                "dokumentacni_jednotka",
                "archeologicky_zaznam",
            ),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "typ_zjisteni": ZjisteniField(
                _("vypis.lokalita.dokumentacni_jednotka.typ_zjisteni.label"), "negativni_jednotka"
            ),
            "pian": SubSectionField(PIAN_CONFIG),
            "komponenty": SubSectionField(KOMPONENTY_DJ_CONFIG),
        },
        "historie": {
            "section_name": SimpleSectionTemplateName(_("vypis.lokalita.historie.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "historie": HistorieRepeatableField(
                _("vypis.lokalita.historie.label"),
                ["datum_zmeny", "uzivatel_protected", "get_typ_zmeny_display", "poznamka"],
                "historie",
                "vypis/historie.html",
            ),
        },
        "ext_zdroje": {
            "section_name": SimpleSectionTemplateName(_("vypis.lokalita.ext_zdroje.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "ext_zdroje": RepeatableField(
                _("vypis.lokalita.ext_zdroje.label"),
                [
                    "externi_zdroj__ident_cely",
                    "externi_zdroj__autori_snapshot",
                    "externi_zdroj__rok_vydani_vzniku",
                    "paginace",
                ],
                "ext_odkaz",
                "vypis/akce/ext_odkazy.html",
                "archeologicky_zaznam",
            ),
        },
        "dokumenty": {
            "section_name": SimpleSectionTemplateName(_("vypis.lokalita.dokumenty.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "dokumenty": RepeatableField(
                _("vypis.lokalita.dokumenty.label"),
                ["dokument__ident_cely", "dokument__autori_snapshot", "dokument__rok_vzniku"],
                "dokument_casti",
                "vypis/souvisejici_zaznam_dok.html",
                "archeologicky_zaznam",
            ),
        },
    },
}

PAS_CONFIG = {
    "title": _("vypis.pas.title"),
    "main_sections": {
        "header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/pas/header.html"),
            "ident_cely": Field(_("vypis.pas.ident_cely.label"), "ident_cely"),
            "stav": StatusField(_("vypis.pas.stav.label"), "get_stav_display"),
            "nalezce": Field(_("vypis.pas.nalezce.label"), "nalezce"),
            "datum_nalezu": Field(_("vypis.pas.datum_nalezu.label"), "datum_nalezu"),
        },
        "sub_header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/sub_header.html"),
            "predano": Field(_("vypis.pas.predano.label"), "get_predano_display"),
            "predano_organizace": ForeignField(
                _("vypis.pas.predano_organizace.label"), "get_nazev", "predano_organizace"
            ),
            "evidencni_cislo": Field(_("vypis.pas.evidencni_cislo.label"), "evidencni_cislo"),
            "pristupnost": Field(_("vypis.pas.pristupnost.label"), "pristupnost"),
        },
        "under_header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/pas/under_header.html"),
            "igsn": Field(_("vypis.pas.igsn.label"), "igsn"),
            "obdobi": Field(_("vypis.pas.obdobi.label"), "obdobi"),
            "presna_datace": Field(_("vypis.pas.presna_datace.label"), "presna_datace"),
            "druh_nalezu": Field(_("vypis.pas.druh_nalezu.label"), "druh_nalezu"),
            "specifikace": Field(_("vypis.pas.specifikace.label"), "specifikace"),
            "katastr": Field(_("vypis.pas.katastr.label"), "katastr"),
        },
    },
    "sections": {
        "popis_pas": {
            "section_name": SimpleSectionTemplateName(_("vypis.pas.popis_nalezu.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "projekt": ForeignField(_("vypis.pas.popis_pas.projekt.label"), "get_ident_cely_link", "projekt"),
            "lokalizace": Field(_("vypis.pas.popis_pas.lokalizace.label"), "lokalizace"),
            "okolnosti": Field(_("vypis.pas.popis_pas.okolnosti.label"), "okolnosti"),
            "hloubka": Field(_("vypis.pas.popis_pas.hloubka.label"), "hloubka"),
            "pocet": Field(_("vypis.pas.popis_pas.pocet.label"), "pocet"),
            "poznamka": Field(_("vypis.pas.popis_pas.poznamka.label"), "poznamka"),
            "geom_system": Field(_("vypis.pas.popis_pas.geom_system.label"), "geom_system"),
            "geom": GeomGmlField(_("vypis.pas.popis_pas.geom_gml.label"), "geom"),
            "geom_sjtsk": GeomGmlField(_("vypis.pas.popis_pas.geom_sjtsk_gml.label"), "geom_sjtsk"),
            "geom_wkt": GeomWktField(_("vypis.pas.popis_pas.geom_wkt.label"), "geom"),
            "geom_sjtsk_wkt": GeomWktField(_("vypis.pas.popis_pas.geom_sjtsk_wkt.label"), "geom_sjtsk"),
        },
        "historie": {
            "section_name": SimpleSectionTemplateName(_("vypis.pas.historie.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "historie": HistorieRepeatableField(
                _("vypis.pas.historie.label"),
                ["datum_zmeny", "uzivatel_protected", "get_typ_zmeny_display", "poznamka"],
                "historie",
                "vypis/historie.html",
            ),
        },
        "soubory": {
            "section_name": SouboryRepeatableSectionNameWithAccessor(
                _("vypis.pas.soubory.section_name"), ["nazev", "mimetype"], "soubory"
            ),
            "template": SimpleSectionTemplateName("vypis/soubory.html"),
            "small_thumbnail": SouborField(_("vypis.pas.soubory.small_thumbnail.label"), "small_thumbnail", "pas"),
            "path": SouborDownloadField(_("vypis.pas.soubory.path.label"), "path", "pas"),
            "rozsah": Field(_("vypis.pas.soubory.rozsah.label"), "rozsah"),
            "size_mb": Field(_("vypis.pas.soubory.size_mb.label"), "size_mb"),
            "sha_512": Field(_("vypis.pas.soubory.sha_512.label"), "sha_512"),
            "historie": HistorieSubSectionField(None, _("vypis.pas.soubory.historie.label")),
        },
    },
}

MODEL_CONFIG = {
    "title": _("vypis.model3d.title"),
    "main_sections": {
        "header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/dokumenty/header.html"),
            "ident_cely": Field(_("vypis.model3d.ident_cely.label"), "ident_cely"),
            "stav": StatusField(_("vypis.model3d.stav.label"), "get_stav_display"),
            "autor": ManyToManyField(_("vypis.model3d.autor.label"), "autori"),
            "rok_vzniku": Field(_("vypis.model3d.rok_vzniku.label"), "rok_vzniku"),
        },
        "sub_header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/sub_header.html"),
            "typ": Field(_("vypis.model3d.typ.label"), "typ_dokumentu"),
            "material": Field(_("vypis.model3d.material.label"), "material_originalu"),
            "rada": Field(_("vypis.model3d.rada.label"), "rada"),
            "pristupnost": Field(_("vypis.model3d.pristupnost.label"), "pristupnost"),
        },
        "under_header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/model/under_header.html"),
            "doi": Field(_("vypis.model3d.doi.label"), "doi"),
            "organizace": ForeignField(_("vypis.model3d.organizace.label"), "get_nazev", "organizace"),
            "obdobi": Model3dKomponentaField(_("vypis.model3d.obdobi.label"), "obdobi"),
            "presna_datace": Model3dKomponentaField(_("vypis.model3d.presna_datace.label"), "presna_datace"),
            "areal": Model3dKomponentaField(_("vypis.model3d.areal.label"), "areal"),
            "aktivity": Model3dKomponentaAktivityField(_("vypis.model3d.aktivita.label"), "aktivity"),
            "odkaz": ForeignField(_("vypis.model3d.odkaz.label"), "odkaz", "extra_data"),
            "popis": Field(_("vypis.model3d.popis.label"), "popis"),
        },
    },
    "sections": {
        "popis_model3d": {
            "section_name": SimpleSectionTemplateName(_("vypis.model3d.popis_model3d.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "poznamka": Field(_("vypis.model3d.popis_model3d.poznamka.label"), "poznamka"),
            "ulozeni_originalu": Field(_("vypis.model3d.popis_model3d.ulozeni_originalu.label"), "ulozeni_originalu"),
            "oznaceni_originalu": Field(
                _("vypis.model3d.popis_model3d.oznaceni_originalu.label"), "oznaceni_originalu"
            ),
            "primarni_epsg": ForeignField(
                _("vypis.model3d.popis_dokumentu.primarni_epsg.label"), "geom_system", "extra_data"
            ),
            "poloha_gml": ForeignGeomGmlField(
                _("vypis.model3d.popis_dokumentu.poloha_gml.label"), "geom", "extra_data"
            ),
            "poloha_gml_sjtsk": ForeignGeomGmlField(
                _("vypis.model3d.popis_dokumentu.poloha_gml_sjtsk.label"), "geom_sjtsk", "extra_data"
            ),
            "poloha_wkt": ForeignGeomWktField(
                _("vypis.model3d.popis_dokumentu.poloha_wkt.label"), "geom", "extra_data"
            ),
            "poloha_wkt_sjtsk": ForeignGeomWktField(
                _("vypis.model3d.popis_dokumentu.poloha_wkt_sjtsk.label"), "geom_sjtsk", "extra_data"
            ),
            "format": ForeignField(_("vypis.model3d.popis_model3d.format.label"), "format", "extra_data"),
            "zeme": ForeignField(_("vypis.model3d.popis_model3d.zeme.label"), "zeme", "extra_data"),
            "region": ForeignField(_("vypis.model3d.popis_model3d.region.label"), "region_extra", "extra_data"),
            "duveryhodnost": ForeignField(
                _("vypis.model3d.popis_model3d.duveryhodnost.label"), "duveryhodnost", "extra_data"
            ),
            "licence": Field(_("vypis.model3d.popis_model3d.licence.label"), "licence"),
        },
        "dokument_casti": {
            "section_name": RepeatableSectionNameWithAccessor(
                _("vypis.model3d.dokument_casti.section_name"),
                ["get_ident_cely_link", "poznamka"],
                "dokument_casti",
                "dokument",
            ),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "dok_zaznam": ChooseField(
                _("vypis.model3d.dokument_casti.dok_zaznam.label"), ["archeologicky_zaznam", "projekt"]
            ),
            "komponenty": SubSectionField(KOMPONENTY_DOKU_CONFIG),
        },
        "historie": {
            "section_name": SimpleSectionTemplateName(_("vypis.model3d.historie.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "historie": HistorieRepeatableField(
                _("vypis.model3d.historie.label"),
                ["datum_zmeny", "uzivatel_protected", "get_typ_zmeny_display", "poznamka"],
                "historie",
                "vypis/historie.html",
            ),
        },
        "soubory": {
            "section_name": SouboryRepeatableSectionNameWithAccessor(
                _("vypis.model3d.soubory.section_name"), ["nazev", "mimetype"], "soubory"
            ),
            "template": SimpleSectionTemplateName("vypis/soubory.html"),
            "small_thumbnail": SouborField(
                _("vypis.model3d.soubory.small_thumbnail.label"), "small_thumbnail", "model3d"
            ),
            "path": SouborDownloadField(_("vypis.model3d.soubory.path.label"), "path", "model3d"),
            "rozsah": Field(_("vypis.model3d.soubory.rozsah.label"), "rozsah"),
            "size_mb": Field(_("vypis.model3d.soubory.size_mb.label"), "size_mb"),
            "sha_512": Field(_("vypis.model3d.soubory.sha_512.label"), "sha_512"),
            "historie": HistorieSubSectionField(None, _("vypis.model3d.soubory.historie.label")),
        },
    },
}

EZ_CONFIG = {
    "title": _("vypis.ez.title"),
    "main_sections": {
        "header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/ez/header.html"),
            "ident_cely": Field(_("vypis.ez.ident_cely.label"), "ident_cely"),
            "stav": StatusField(_("vypis.ez.stav.label"), "get_stav_display"),
            "typ": Field(_("vypis.ez.typ.label"), "typ"),
            "autor": ManyToManyField(_("vypis.ez.autor.label"), "autori"),
            "rok_vydani_vzniku": Field(_("vypis.ez.rok_vydani_vzniku.label"), "rok_vydani_vzniku"),
        },
        "under_header": {
            "section_name": SimpleSectionTemplateName(None),
            "template": SimpleSectionTemplateName("vypis/simple_section_without_name.html"),
            "nazev": Field(_("vypis.ez.nazev.label"), "nazev"),
            "doi": Field(_("vypis.ez.doi.label"), "doi"),
        },
    },
    "sections": {
        "popis_zdroje": {
            "section_name": SimpleSectionTemplateName(_("vypis.ez.popis_ez.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "editor": ManyToManyField(_("vypis.ez.popis_ez.editor.label"), "editori"),
            "nazev_sborniku": Field(_("vypis.ez.popis_ez.nazev_sborniku.label"), "sbornik_nazev"),
            "casopis_denik_nazev": Field(_("vypis.ez.popis_ez.casopis_denik_nazev.label"), "casopis_denik_nazev"),
            "casopis_rocnik": Field(_("vypis.ez.popis_ez.casopis_rocnik.label"), "casopis_rocnik"),
            "datum_rd": Field(_("vypis.ez.popis_ez.datum_rd.label"), "datum_rd"),
            "edice_rada": Field(_("vypis.ez.popis_ez.edice_rada.label"), "edice_rada"),
            "typ_dokumentu": Field(_("vypis.ez.popis_ez.typ_dokumentu.label"), "typ_dokumentu"),
            "organizace": Field(_("vypis.ez.popis_ez.organizace.label"), "organizace"),
            "misto": Field(_("vypis.ez.popis_ez.misto.label"), "misto"),
            "vydavatel": Field(_("vypis.ez.popis_ez.vydavatel.label"), "vydavatel"),
            "paginace_titulu": Field(_("vypis.ez.popis_ez.paginace_titulu.label"), "paginace_titulu"),
            "isbn": Field(_("vypis.ez.popis_ez.isbn.label"), "isbn"),
            "issn": Field(_("vypis.ez.popis_ez.issn.label"), "issn"),
            "poznamka": Field(_("vypis.ez.popis_ez.poznamka.label"), "poznamka"),
            "odkaz": Field(_("vypis.ez.popis_ez.odkaz.label"), "link"),
        },
        "historie": {
            "section_name": SimpleSectionTemplateName(_("vypis.ez.historie.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "historie": HistorieRepeatableField(
                _("vypis.ez.historie.label"),
                ["datum_zmeny", "uzivatel_protected", "get_typ_zmeny_display", "poznamka"],
                "historie",
                "vypis/historie.html",
            ),
        },
        "ext_odkaz": {
            "section_name": SimpleSectionTemplateName(_("vypis.ez.ext_odkazy.section_name")),
            "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
            "archz": RepeatableField(
                _("vypis.ez.ext_odkazy.label"),
                ["archeologicky_zaznam__ident_cely", "paginace"],
                "ext_odkaz",
                "vypis/ez/ext_odkazy.html",
                "externi_zdroj",
            ),
        },
    },
}
