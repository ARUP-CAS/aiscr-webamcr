from django.utils.translation import gettext_lazy as _
from django_tables2 import columns
from django_tables2_column_shifter.tables import ColumnShiftTableBootstrap4
from historie.models import Historie


class HistorieTable(ColumnShiftTableBootstrap4):
    """
    Class pro definování tabulky pro zobrazení historie.
    """

    datum_zmeny = columns.DateTimeColumn(
        format="Y-m-d, H:i", default="", verbose_name=_("core.tables.HistorieTable.datum_zmeny")
    )
    typ_zmeny = columns.Column(default="", verbose_name=_("core.tables.HistorieTable.typ_zmeny"))
    poznamka = columns.Column(default="", verbose_name=_("core.tables.HistorieTable.poznamka"))
    uzivatel_custom = columns.Column(default="", verbose_name=_("core.tables.HistorieTable.uzivatel_custom"))

    class Meta:
        model = Historie
        fields = (
            "typ_zmeny",
            "datum_zmeny",
            "uzivatel_custom",
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
    history_date = columns.DateTimeColumn(format="Y-m-d, H:i", default="")

    class Meta:
        fields = ("history_date",)
