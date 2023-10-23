import logging

import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html
from django_tables2.utils import A
from django.utils.translation import gettext as _
from django.template import Context, Template
from django.template.loader import get_template

from core.utils import SearchTable
from core.models import Permissions as p, check_permissions

from .models import SamostatnyNalez, UzivatelSpoluprace

logger = logging.getLogger(__name__)


class SamostatnyNalezTable(SearchTable):
    """
    Class pro definování tabulky pro samostatný nález použitých pro zobrazení přehledu nálezu a exportu.
    """
    ident_cely = tables.Column(linkify=True)
    katastr = tables.Column(verbose_name=_("pas.tables.samostatnyNalezTable.katastr.label"), default="")
    datum_nalezu = tables.columns.DateTimeColumn(format="Y-m-d", default="")
    lokalizace = tables.columns.Column(default="")
    obdobi = tables.columns.Column(default="")
    druh_nalezu = tables.columns.Column(default="")
    specifikace = tables.columns.Column(default="")
    nalezce = tables.columns.Column(default="")
    evidencni_cislo = tables.columns.Column(default="")
    predano = tables.columns.Column(default="")
    predano_organizace = tables.columns.Column(
        default="", order_by="predano_organizace__nazev_zkraceny"
    )
    app = "samostatny_nalez"
    nahled = tables.columns.Column(
        default="",
        accessor="soubory",
        attrs={
            "th": {"class": "white"},
        },
        orderable=False,
        verbose_name=_("dokument.tables.dokumentTable.soubory.label"),
    )
    columns_to_hide = (
        "predano",
        "pristupnost",
        "evidencni_cislo",
        "presna_datace",
        "pocet",
        "poznamka",
        "okolnosti",
        "hloubka"
    )

    class Meta:
        model = SamostatnyNalez
        fields = (
            "nahled",
            "ident_cely",
            "stav",
            "lokalizace",
            "katastr",
            "obdobi",
            "druh_nalezu",
            "specifikace",
            "nalezce",
            "datum_nalezu",
            "evidencni_cislo",
            "predano",
            "predano_organizace",
            "pristupnost",
            "presna_datace",
            "pocet",
            "poznamka",
            "okolnosti",
            "hloubka"
        )
        sequence = (
            "nahled",
            "ident_cely",
            "stav",
            "predano",
            "pristupnost",
            "evidencni_cislo",
            "katastr",
            "lokalizace",
            "datum_nalezu",
            "nalezce",
            "predano_organizace",
            "obdobi",
            "presna_datace",
            "druh_nalezu",
            "specifikace",
            "pocet",
            "poznamka",
            "okolnosti",
            "hloubka"
        )

    def render_nahled(self, value, record):
        """
        Metóda pro správne zobrazení náhledu souboru.
        """
        soubor = record.nahled_soubor
        if soubor is not None:
            soubor_url = reverse("core:download_thumbnail", args=('pas', record.ident_cely ,soubor.id,))
            return format_html(
                '<img src="{}" class="image-nahled" data-toggle="modal" data-target="#soubor-modal">',
                soubor_url,
            )
        return ""

    def __init__(self, *args, **kwargs):
        super(SamostatnyNalezTable, self).__init__(*args, **kwargs)

class AktivaceDeaktivaceColumn(tables.TemplateColumn):
    def render(self, record, table, value, bound_column, **kwargs):
        if record.aktivni:
            perm_check = check_permissions(p.actionChoices.spoluprace_deaktivovat, table.request.user,record.id)
        else:
            perm_check = check_permissions(p.actionChoices.spoluprace_aktivovat, table.request.user,record.id)
        if perm_check:
            return super().render(record, table, value, bound_column, **kwargs)
        else:
            return format_html("")
        
class smazatColumn(tables.TemplateColumn):
    def render(self, record, table, value, bound_column, **kwargs):
        if check_permissions(p.actionChoices.spoluprace_smazat, table.request.user,record.id):
            return super().render(record, table, value, bound_column, **kwargs)
        else:
            return format_html("")
        
class UzivatelSpolupraceTable(SearchTable):
    """
    Class pro definování tabulky pro uživatelskou spolupráci použitých pro zobrazení přehledu spoluprác a exportu.
    """
    stav = tables.Column(
        verbose_name="Stav", default=""
    )
    vedouci = tables.Column(
        accessor="vedouci__name_and_id",
        verbose_name="Vedoucí",
        order_by=("vedouci__last_name", "vedouci__first_name", "vedouci__ident_cely"),
        default="",
    )
    organizace_vedouci = tables.Column(
        accessor=("vedouci__organizace"),
        verbose_name="Organizace (Vedoucí)",
        default="",
        order_by="vedouci__organizace__nazev_zkraceny",
    )
    spolupracovnik = tables.Column(
        accessor="spolupracovnik__name_and_id",
        verbose_name="Spolupracovník",
        order_by=("vedouci__last_name", "vedouci__first_name", "vedouci__ident_cely"),
        default="",
    )
    organizace_spolupracovnik = tables.Column(
        accessor=("spolupracovnik__organizace"),
        verbose_name="Organizace (Spolupracovník)",
        default="",
        order_by="spolupracovnik__organizace__nazev_zkraceny",
    )

    historie = tables.LinkColumn(
        "historie:spoluprace",
        text="Historie",
        args=[A("pk")],
        attrs={"th": {"style": "color:white"}},
        orderable=False,
    )
    aktivace = AktivaceDeaktivaceColumn(
        attrs={
            "th": {"class": "orderable ", "style": "color:#fff"},
        },
        template_name="pas/aktivace_deaktivace_cell.html",
        orderable=False,
    )
    smazani = smazatColumn(
        attrs={
            "th": {"class": "orderable ", "style": "color:#fff"},
        },
        template_name="pas/smazat_cell.html",
        exclude_from_export=True,
        orderable=False,
    )
    app = "spoluprace"

    class Meta:
        model = UzivatelSpoluprace
        fields = (
            "stav",
            "vedouci",
            "organizace_vedouci",
            "spolupracovnik",
            "organizace_spolupracovnik",
        )
        sequence = (
            "stav",
            "vedouci",
            "organizace_vedouci",
            "spolupracovnik",
            "organizace_spolupracovnik",
            "historie",
            "aktivace",
            "smazani",
        )

    def __init__(self, *args, **kwargs):
        super(UzivatelSpolupraceTable, self).__init__(*args, **kwargs)



