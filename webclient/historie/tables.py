from django_tables2 import columns

from historie.models import Historie
from django_tables2_column_shifter.tables import (
    ColumnShiftTableBootstrap4,
)


class HistorieTable(ColumnShiftTableBootstrap4):
    """
    Class pro definování tabulky pro zobrazení historie.
    """
    datum_zmeny = columns.DateTimeColumn(format ='Y-m-d, H:i',default="")
    typ_zmeny = columns.Column(default="")
    poznamka = columns.Column(default="")
    uzivatel = columns.Column(default="")
    class Meta:
        model = Historie
        fields = (
            "typ_zmeny",
            "datum_zmeny",
            "uzivatel",
            "poznamka",
        )

    # TODO: This form of printing does not respect django timezone
    # @staticmethod
    # def render_datum_zmeny(value):
    #     if value:
    #         return value.strftime("%Y-%m-%d, %H:%M:%S")
    #     else:
    #         return "—"


class SimpleHistoryTable(ColumnShiftTableBootstrap4):
    history_date = columns.DateTimeColumn(format='Y-m-d, H:i', default="")

    class Meta:
        fields = (
            "history_date",
        )
