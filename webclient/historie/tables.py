from django_tables2 import tables, columns
from simple_history.models import HistoricalRecords

from historie.models import Historie
from django_tables2_column_shifter.tables import (
    ColumnShiftTableBootstrap4,
)


class HistorieTable(ColumnShiftTableBootstrap4):
    datum_zmeny = columns.DateTimeColumn(format ='Y-m-d, H:i',default="")
    typ_zmeny = columns.Column(default="")
    poznamka = columns.Column(default="")
    uzivatel = columns.Column(default="")
    class Meta:
        model = Historie
        template_name = "projekt/bootstrap4.html"
        # template_name = "django_tables2/bootstrap4.html"
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
        template_name = "projekt/bootstrap4.html"
        # template_name = "django_tables2/bootstrap4.html"
        fields = (
            "history_date",
        )
