import django_tables2 as tables
from django_tables2_column_shifter.tables import ColumnShiftTableBootstrap4
from django.utils.translation import gettext as _

from lokalita.tables import DalsiKatastryColumn

from .models import Akce


class AkceTable(ColumnShiftTableBootstrap4):

    ident_cely = tables.Column(linkify=True, accessor="archeologicky_zaznam.ident_cely")
    katastr = tables.Column(
        verbose_name=_("Katastrální území"),
        default="",
        accessor="archeologicky_zaznam.hlavni_katastr",
    )
    stav = tables.columns.Column(default="", accessor="archeologicky_zaznam.stav")
    organizace = tables.columns.Column(
        default="", order_by="organizace__nazev_zkraceny"
    )
    hlavni_vedouci = tables.columns.Column(default="")
    uzivatelske_oznaceni = tables.Column(
        verbose_name=_("Uživatelské označení"),
        default="",
        accessor="archeologicky_zaznam.uzivatelske_oznaceni",
    )
    dalsi_katastry = DalsiKatastryColumn(
        verbose_name=_("Další katastry"),
        default="",
        accessor="archeologicky_zaznam.katastry.all",
    )

    columns_to_hide = None
    first_columns = None

    def get_column_default_show(self):
        self.column_default_show = list(self.columns.columns.keys())
        if "akce_vychozi_skryte_sloupce" in self.request.session:
            columns_to_hide = set(self.request.session["akce_vychozi_skryte_sloupce"])
        else:
            columns_to_hide = ("uzivatelske_oznaceni", "dalsi_katastry")
        for column in columns_to_hide:
            if column is not None and column in self.column_default_show:
                self.column_default_show.remove(column)
        return super(AkceTable, self).get_column_default_show()

    class Meta:
        model = Akce
        # template_name = "projekt/bootstrap4.html"
        fields = (
            "hlavni_vedouci",
            "organizace",
        )
        sequence = (
            "ident_cely",
            "stav",
            "katastr",
            "organizace",
            "hlavni_vedouci",
            "uzivatelske_oznaceni",
            "dalsi_katastry",
        )

        def __init__(self, *args, **kwargs):
            super(AkceTable, self).__init__(*args, **kwargs)
