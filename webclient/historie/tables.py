import django_tables2 as tables
from django.utils.html import format_html
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


class FedoraHistorieTable(ColumnShiftTableBootstrap4):
    """
    Class pro definování tabulky pro zobrazení fedora verzí metadat nebo souborů na stránce pod historií.
    """

    datum = tables.DateTimeColumn(
        verbose_name=_("historie.templates.historieList.fedora.datum"),
        format="Y-m-d, H:i",
        attrs={"td": {"class": "col_datum"}},
        orderable=True,
    )
    url = tables.Column(
        verbose_name="Stáhnout",
        attrs={
            "td": {
                "class": "col_stahnout",
                "rel": "",
                "title": "",
            }
        },
        orderable=False,
    )

    def render_url(self, value, record):
        return format_html(
            '<a href="{}" class="btn btn-sm btn-outline-primary" target="_blank">'
            '<span class="material-icons" style="vertical-align:middle;">download</span>'
            "</a>",
            record["url"],
        )

    class Meta:
        attrs = {"class": "table-shifter table"}
        fields = ("datum", "url")
        order_by = ("-datum",)
