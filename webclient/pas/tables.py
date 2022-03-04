import logging

import django_tables2 as tables
from django_tables2_column_shifter.tables import ColumnShiftTableBootstrap4
from django_tables2.utils import A
from django.utils.translation import gettext as _

from .models import SamostatnyNalez, UzivatelSpoluprace

logger = logging.getLogger(__name__)


class SamostatnyNalezTable(ColumnShiftTableBootstrap4):

    ident_cely = tables.Column(linkify=True)
    katastr = tables.Column(verbose_name=_("Katastrální území"))
    datum_nalezu = tables.columns.DateTimeColumn(format ='Y-m-d')

    def get_column_default_show(self):
        self.column_default_show = list(self.columns.columns.keys())
        if "projekt_vychozi_skryte_sloupce" in self.request.session:
            columns_to_hide = set(
                self.request.session["projekt_vychozi_skryte_sloupce"]
            )
            for column in columns_to_hide:
                if column is not None and column in self.column_default_show:
                    self.column_default_show.remove(column)
        return super(SamostatnyNalezTable, self).get_column_default_show()

    class Meta:
        model = SamostatnyNalez
        # template_name = "projekt/bootstrap4.html"
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


class UzivatelSpolupraceTable(ColumnShiftTableBootstrap4):

    stav = tables.Column(verbose_name="Stav", attrs={"td": {"class": "spoluprace"}},)
    vedouci = tables.Column(
        accessor=("vedouci__name_and_id"),
        verbose_name="Vedoucí",
        attrs={"td": {"class": "spoluprace"}},
    )
    organizace_vedouci = tables.Column(
        accessor=("vedouci__organizace"),
        verbose_name="Organizace (Vedoucí)",
        attrs={"td": {"class": "spoluprace"}},
    )
    spolupracovnik = tables.Column(
        accessor="spolupracovnik__name_and_id",
        verbose_name="Spolupracovník",
        attrs={"td": {"class": "spoluprace"}},
    )
    organizace_spolupracovnik = tables.Column(
        accessor=("spolupracovnik__organizace"),
        verbose_name="Organizace (Spolupracovník)",
        attrs={"td": {"class": "spoluprace"}},
    )

    historie = tables.LinkColumn(
        "historie:spoluprace",
        text="Historie",
        args=[A("pk")],
        attrs={"a": {"class": "btn btn-sm"}},
    )
    aktivace = tables.TemplateColumn(
        attrs={
            "td": {"class": "spoluprace"},
            "th": {"class": "orderable ", "style": "color:#fff"},
        },
        template_name="pas/aktivace_deaktivace_cell.html",
        orderable=False,
    )
    smazani = tables.LinkColumn(
        "pas:spoluprace_smazani",
        text="Smazat",
        args=[A("pk")],
        attrs={
            "a": {"class": "btn btn-sm"},
            "th": {"class": "orderable ", "style": "color:#fff"},
        },
        exclude_from_export=True,
        orderable=False,
    )

    class Meta:
        model = UzivatelSpoluprace
        # template_name = "projekt/bootstrap4.html"
        fields = ("stav",)

    def __init__(self, *args, **kwargs):
        super(UzivatelSpolupraceTable, self).__init__(*args, **kwargs)
