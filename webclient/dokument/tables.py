import logging

import django_tables2 as tables
from core.models import Soubor
from core.utils import SearchTable
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Dokument

logger = logging.getLogger(__name__)


class Model3DTable(SearchTable):
    """
    Class pro definování tabulky pro modelu 3D použitých pro zobrazení přehledu modelu 3D a exportu.
    """

    ident_cely = tables.Column(linkify=True, verbose_name=_("dokument.tables.modelTable.ident_cely.label"))
    typ_dokumentu = tables.columns.Column(default="", verbose_name=_("dokument.tables.modelTable.typ_dokumentu.label"))
    organizace = tables.columns.Column(
        default="", verbose_name=_("dokument.tables.modelTable.organizace.label"), order_by="organizace__nazev_zkraceny"
    )
    popis = tables.columns.Column(default="", verbose_name=_("dokument.tables.modelTable.popis.label"))
    rok_vzniku = tables.columns.Column(default="", verbose_name=_("dokument.tables.modelTable.rok_vzniku.label"))
    extra_data__format = tables.columns.Column(
        default="", verbose_name=_("dokument.tables.modelTable.extra_data__format.label")
    )
    extra_data__odkaz = tables.columns.Column(
        default="", verbose_name=_("dokument.tables.modelTable.extra_data__odkaz.label")
    )
    extra_data__duveryhodnost = tables.columns.Column(
        default="", verbose_name=_("dokument.tables.modelTable.extra_data__duveryhodnost.label")
    )
    extra_data__zeme = tables.Column(verbose_name=_("dokument.tables.dokumentTable.extra_data__zeme.label"))
    extra_data__region_extra = tables.Column(verbose_name=_("dokument.tables.dokumentTable.extra_data__region.label"))
    autori = tables.Column(
        default="", accessor="autori_snapshot", verbose_name=_("dokument.tables.modelTable.autori.label")
    )
    stav = tables.columns.Column(default="", verbose_name=_("dokument.tables.modelTable.stav.label"))
    app = "knihovna_3d"
    first_columns = None
    nahled = tables.columns.Column(
        default="",
        accessor="soubory",
        attrs={
            "th": {"class": "white"},
        },
        orderable=False,
        verbose_name=_("dokument.tables.modelTable.nahled.label"),
    )
    columns_to_hide = (
        "extra_data__zeme",
        "extra_data__region_extra",
    )

    class Meta:
        model = Dokument
        fields = (
            "ident_cely",
            "stav",
            "typ_dokumentu",
            "organizace",
            "popis",
            "rok_vzniku",
            "extra_data__format",
            "extra_data__odkaz",
            "extra_data__duveryhodnost",
            "extra_data__zeme",
            "extra_data__region_extra",
        )
        sequence = (
            "nahled",
            "ident_cely",
            "stav",
            "typ_dokumentu",
            "autori",
            "organizace",
            "rok_vzniku",
            "popis",
            "extra_data__format",
            "extra_data__odkaz",
            "extra_data__duveryhodnost",
            "extra_data__zeme",
            "extra_data__region_extra",
        )

    def __init__(self, *args, **kwargs):
        super(Model3DTable, self).__init__(*args, **kwargs)

    def render_nahled(self, value, record):
        """
        Metóda pro správne zobrazení náhledu souboru.
        """
        if len(record.soubory.soubory.all()) > 0:
            soubor = record.soubory.soubory.first()
        else:
            soubor = None
        if soubor is not None:
            soubor: Soubor
            thumbnail_url = reverse(
                "core:download_thumbnail",
                args=(
                    "model3d",
                    record.ident_cely,
                    soubor.id,
                ),
            )
            soubor_url = reverse(
                "core:download_file",
                args=(
                    "model3d",
                    record.ident_cely,
                    soubor.id,
                ),
            )
            return format_html(
                '<img src="{}" class="image-nahled" data-toggle="modal" data-target="#soubor-modal" loading="lazy" data-fullsrc="{}" '
                'style="opacity:0" onload="this.style.opacity=100">',
                thumbnail_url,
                soubor_url,
            )
        return ""


class DokumentTable(SearchTable):
    """
    Class pro definování tabulky pro dokumenty použitých pro zobrazení přehledu dokumentů a exportu.
    """

    ident_cely = tables.Column(linkify=True, verbose_name=_("dokument.tables.dokumentTable.ident_cely.label"))
    typ_dokumentu = tables.columns.Column(
        default="", verbose_name=_("dokument.tables.dokumentTable.typ_dokumentu.label")
    )
    organizace = tables.columns.Column(
        default="",
        verbose_name=_("dokument.tables.dokumentTable.organizace.label"),
        order_by="organizace__nazev_zkraceny",
    )
    rok_vzniku = tables.columns.Column(default="", verbose_name=_("dokument.tables.dokumentTable.rok_vzniku.label"))
    autori = tables.Column(
        default="", accessor="autori_snapshot", verbose_name=_("dokument.tables.dokumentTable.autori.label")
    )
    osoby = tables.Column(
        default="", accessor="osoby_snapshot", verbose_name=_("dokument.tables.dokumentTable.osoby.label")
    )
    popis = tables.columns.Column(default="", verbose_name=_("dokument.tables.dokumentTable.popis.label"))
    pristupnost = tables.columns.Column(default="", verbose_name=_("dokument.tables.dokumentTable.pristupnost.label"))
    rada = tables.columns.Column(default="", verbose_name=_("dokument.tables.dokumentTable.rada.label"))
    material_originalu = tables.columns.Column(
        default="", verbose_name=_("dokument.tables.dokumentTable.material_originalu.label")
    )
    poznamka = tables.columns.Column(default="", verbose_name=_("dokument.tables.dokumentTable.poznamka.label"))
    ulozeni_originalu = tables.columns.Column(
        default="", verbose_name=_("dokument.tables.dokumentTable.ulozeni_originalu.label")
    )
    oznaceni_originalu = tables.columns.Column(
        default="", verbose_name=_("dokument.tables.dokumentTable.oznaceni_originalu.label")
    )
    datum_zverejneni = tables.columns.DateColumn(
        default="",
        verbose_name=_("dokument.tables.dokumentTable.datum_zverejneni.label"),
        format="Y-m-d",
    )
    licence = tables.columns.Column(default="", verbose_name=_("dokument.tables.dokumentTable.licence.label"))
    nahled = tables.columns.Column(
        default="",
        accessor="soubory",
        attrs={
            "th": {"class": "white"},
        },
        orderable=False,
        verbose_name=_("dokument.tables.dokumentTable.nahled.label"),
    )
    stav = tables.Column(verbose_name=_("dokument.tables.dokumentTable.stav.label"))
    let = tables.Column(verbose_name=_("dokument.tables.dokumentTable.let.label"))
    extra_data__datum_vzniku = tables.Column(
        verbose_name=_("dokument.tables.dokumentTable.extra_data__datum_vzniku.label")
    )
    extra_data__cislo_objektu = tables.Column(
        verbose_name=_("dokument.tables.dokumentTable.extra_data__cislo_objektu.label")
    )
    extra_data__format = tables.Column(verbose_name=_("dokument.tables.dokumentTable.extra_data__format.label"))
    extra_data__zachovalost = tables.Column(
        verbose_name=_("dokument.tables.dokumentTable.extra_data__zachovalost.label")
    )
    extra_data__nahrada = tables.Column(verbose_name=_("dokument.tables.dokumentTable.extra_data__nahrada.label"))
    extra_data__pocet_variant_originalu = tables.Column(
        verbose_name=_("dokument.tables.dokumentTable.extra_data__pocet_variant_originalu.label")
    )
    extra_data__meritko = tables.Column(verbose_name=_("dokument.tables.dokumentTable.extra_data__meritko.label"))
    extra_data__vyska = tables.Column(verbose_name=_("dokument.tables.dokumentTable.extra_data__vyska.label"))
    extra_data__sirka = tables.Column(verbose_name=_("dokument.tables.dokumentTable.extra_data__sirka.label"))
    extra_data__zeme = tables.Column(verbose_name=_("dokument.tables.dokumentTable.extra_data__zeme.label"))
    extra_data__region_extra = tables.Column(verbose_name=_("dokument.tables.dokumentTable.extra_data__region.label"))
    extra_data__udalost_typ = tables.Column(
        verbose_name=_("dokument.tables.dokumentTable.extra_data__udalost_typ.label")
    )
    extra_data__udalost = tables.Column(verbose_name=_("dokument.tables.dokumentTable.extra_data__udalost.label"))
    extra_data__rok_od = tables.Column(verbose_name=_("dokument.tables.dokumentTable.extra_data__rok_od.label"))
    extra_data__rok_do = tables.Column(verbose_name=_("dokument.tables.dokumentTable.extra_data__rok_do.label"))
    extra_data__odkaz = tables.Column(verbose_name=_("dokument.tables.dokumentTable.extra_data__odkaz.label"))
    extra_data__duveryhodnost = tables.Column(
        verbose_name=_("dokument.tables.dokumentTable.extra_data__duveryhodnost.label")
    )
    columns_to_hide = (
        "pristupnost",
        "datum_zverejneni",
        "oznaceni_originalu",
        "extra_data__datum_vzniku",
        "poznamka",
        "extra_data__cislo_objektu",
        "rada",
        "material_originalu",
        "extra_data__format",
        "ulozeni_originalu",
        "licence",
        "let",
        "extra_data__zachovalost",
        "extra_data__nahrada",
        "extra_data__pocet_variant_originalu",
        "extra_data__meritko",
        "extra_data__vyska",
        "extra_data__sirka",
        "extra_data__zeme",
        "extra_data__region_extra",
        "extra_data__udalost_typ",
        "extra_data__udalost",
        "extra_data__rok_od",
        "extra_data__rok_do",
        "osoby",
        "extra_data__odkaz",
        "extra_data__duveryhodnost",
    )
    app = "dokument"
    first_columns = None

    def render_nahled(self, value, record):
        """
        Metóda pro správne zobrazení náhledu souboru.
        """
        if hasattr(record.soubory, "first_soubor") and len(record.soubory.first_soubor) > 0:
            soubor = record.soubory.first_soubor[0]
        else:
            soubor = None
        if soubor is not None:
            soubor: Soubor
            thumbnail_url = reverse(
                "core:download_thumbnail",
                args=(
                    "model3d",
                    record.ident_cely,
                    soubor.id,
                ),
            )
            thumbnail_large_url = reverse(
                "core:download_thumbnail_large",
                args=(
                    "model3d",
                    record.ident_cely,
                    soubor.id,
                ),
            )
            return format_html(
                '<img src="{}" class="image-nahled" data-toggle="modal" data-target="#soubor-modal" '
                'loading="lazy" data-fullsrc="{}" style="opacity:0" onload="this.style.opacity=100">',
                thumbnail_url,
                thumbnail_large_url,
            )
        return ""

    class Meta:
        model = Dokument
        fields = (
            "nahled",
            "ident_cely",
            "stav",
            "organizace",
            "autori",
            "rok_vzniku",
            "typ_dokumentu",
            "popis",
            "pristupnost",
            "rada",
            "let",
            "material_originalu",
            "poznamka",
            "ulozeni_originalu",
            "oznaceni_originalu",
            "datum_zverejneni",
            "licence",
            "extra_data__format",
            "extra_data__datum_vzniku",
            "extra_data__cislo_objektu",
            "extra_data__zachovalost",
            "extra_data__nahrada",
            "extra_data__pocet_variant_originalu",
            "extra_data__meritko",
            "extra_data__vyska",
            "extra_data__sirka",
            "extra_data__zeme",
            "extra_data__region_extra",
            "extra_data__udalost_typ",
            "extra_data__udalost",
            "extra_data__rok_od",
            "extra_data__rok_do",
            "extra_data__odkaz",
            "extra_data__duveryhodnost",
        )
        sequence = (
            "nahled",
            "ident_cely",
            "stav",
            "pristupnost",
            "datum_zverejneni",
            "oznaceni_originalu",
            "autori",
            "organizace",
            "rok_vzniku",
            "extra_data__datum_vzniku",
            "popis",
            "poznamka",
            "extra_data__cislo_objektu",
            "rada",
            "typ_dokumentu",
            "material_originalu",
            "extra_data__format",
            "ulozeni_originalu",
            "licence",
            "let",
            "extra_data__zachovalost",
            "extra_data__nahrada",
            "extra_data__pocet_variant_originalu",
            "extra_data__meritko",
            "extra_data__vyska",
            "extra_data__sirka",
            "extra_data__zeme",
            "extra_data__region_extra",
            "extra_data__udalost_typ",
            "extra_data__udalost",
            "extra_data__rok_od",
            "extra_data__rok_do",
            "osoby",
            "extra_data__odkaz",
            "extra_data__duveryhodnost",
        )

    def __init__(self, *args, **kwargs):
        super(DokumentTable, self).__init__(*args, **kwargs)
