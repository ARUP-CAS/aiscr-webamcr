import logging

import django_tables2 as tables
from django_tables2_column_shifter.tables import ColumnShiftTableBootstrap4

from .models import SamostatnyNalez, UzivatelSpoluprace

logger = logging.getLogger(__name__)


class SamostatnyNalezTable(ColumnShiftTableBootstrap4):

    ident_cely = tables.Column(linkify=True)

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

    vedouci = tables.Column(accessor="vedouci__email", verbose_name="Vedoucí")
    spolupracovnik = tables.Column(
        accessor="spolupracovnik__email", verbose_name="Spolupracovník"
    )
    aktivace = tables.TemplateColumn(template_name="pas/aktivace_deaktivace_cell.html")

    class Meta:
        model = UzivatelSpoluprace
        # template_name = "projekt/bootstrap4.html"
        fields = ("stav",)

    def __init__(self, *args, **kwargs):
        super(UzivatelSpolupraceTable, self).__init__(*args, **kwargs)
