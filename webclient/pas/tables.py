import logging

import django_tables2 as tables
from django_tables2.utils import A
from django.utils.translation import gettext as _

from core.utils import SearchTable

from .models import SamostatnyNalez, UzivatelSpoluprace

logger = logging.getLogger(__name__)


class SamostatnyNalezTable(SearchTable):

    ident_cely = tables.Column(linkify=True)
    katastr = tables.Column(verbose_name=_("Katastrální území"), default="")
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

    class Meta:
        model = SamostatnyNalez
        fields = (
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
        )

    def __init__(self, *args, **kwargs):
        super(SamostatnyNalezTable, self).__init__(*args, **kwargs)


class UzivatelSpolupraceTable(SearchTable):

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
    aktivace = tables.TemplateColumn(
        attrs={
            "th": {"class": "orderable ", "style": "color:#fff"},
        },
        template_name="pas/aktivace_deaktivace_cell.html",
        orderable=False,
    )
    smazani = tables.TemplateColumn(
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

    def __init__(self, *args, **kwargs):
        super(UzivatelSpolupraceTable, self).__init__(*args, **kwargs)
