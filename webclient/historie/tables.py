import django_tables2 as tables
from django.conf import settings
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_tables2 import columns
from django_tables2_column_shifter.tables import ColumnShiftTableBootstrap4
from historie.models import Historie
from uzivatel.models import User


class HistorieTable(ColumnShiftTableBootstrap4):
    """
    Class pro definování tabulky pro zobrazení historie.
    """

    datum_zmeny = columns.DateTimeColumn(
        format="Y-m-d, H:i", default="", verbose_name=_("core.tables.HistorieTable.datum_zmeny")
    )
    typ_zmeny = columns.Column(default="", verbose_name=_("core.tables.HistorieTable.typ_zmeny"))
    poznamka = columns.Column(default="", verbose_name=_("core.tables.HistorieTable.poznamka"))
    uzivatel_custom = columns.Column(
        accessor="uzivatel", default="", verbose_name=_("core.tables.HistorieTable.uzivatel_custom")
    )

    def render_uzivatel_custom(self, record):
        if not record.uzivatel:
            return ""
        return record.uzivatel.display_name(viewer=self.request.user if hasattr(self, "request") else None)

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

    column_excluded = ["url"]
    datum = tables.DateTimeColumn(
        verbose_name=_("historie.templates.historieList.fedora.datum"),
        format="Y-m-d, H:i:s",
        orderable=True,
    )
    url = tables.Column(
        verbose_name=_("historie.templates.historieList.fedora.stahnout"),
        attrs={
            "td": {
                "rel": "",
                "title": "",
            },
            "th": {"class": "col-stahnout"},
        },
        orderable=False,
    )
    uzivatel = columns.Column(
        default="",
        verbose_name=_("historie.templates.historieList.fedora.uzivatel"),
        orderable=True,
    )

    def render_uzivatel(self, record):
        uzivatel = User.objects.filter(ident_cely=record["uzivatel"]).first()
        if uzivatel is None:
            return record["uzivatel"]
        return uzivatel.display_name(viewer=self.request.user if hasattr(self, "request") else None)

    def render_url(self, value, record):
        return format_html(
            '<a href="{}" class="btn-sm" target="_blank">'
            '<span class="material-icons" style="vertical-align:middle;">download</span>'
            "</a>",
            record["url"],
        )

    def value_url(self, value, record):
        return f"{settings.SITE_URL}{record['url']}"

    class Meta:
        attrs = {"class": "table-shifter table fedora-table"}
        fields = ("url", "datum", "uzivatel")
        order_by = ("-datum",)
