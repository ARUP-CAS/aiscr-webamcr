import django_tables2 as tables
from django_tables2_column_shifter.tables import ColumnShiftTableBootstrap4
from django_tables2.utils import A
from django.utils.translation import gettext as _
from django.utils.html import conditional_escape, mark_safe
from django.utils.encoding import force_str
from django.db import models

from heslar.models import RuianKatastr

from .models import Lokalita


class DalsiKatastryColumn(tables.Column):
    def render(self, value):
        if value:
            items = []
            for item in value:
                content = conditional_escape(force_str(item))
                items.append(content)

            return mark_safe(conditional_escape("; ").join(items))
        else:
            return ""

    def order(self, queryset, is_descending):
        comments = (
            RuianKatastr.objects.filter(
                archeologickyzaznamkatastr__archeologicky_zaznam_id=models.OuterRef(
                    "pk"
                )
            )
            .order_by("nazev")
            .values("nazev")
        )
        queryset = queryset.annotate(length=models.Subquery(comments[:1])).order_by(
            ("-" if is_descending else "") + "length"
        )
        return (queryset, True)


class LokalitaTable(ColumnShiftTableBootstrap4):

    ident_cely = tables.Column(linkify=True, accessor="archeologicky_zaznam.ident_cely")
    katastr = tables.Column(
        verbose_name=_("Katastrální území"),
        default="",
        accessor="archeologicky_zaznam.hlavni_katastr",
    )
    stav = tables.columns.Column(default="", accessor="archeologicky_zaznam.stav")
    druh = tables.columns.Column(default="", order_by="druh__nazev_zkraceny")
    nazev = tables.columns.Column(default="")
    typ_lokality = tables.columns.Column(
        default="", order_by="typ_lokality__nazev_zkraceny"
    )
    zachovalost = tables.columns.Column(
        default="", order_by="zachovalost__nazev_zkraceny"
    )
    jistota = tables.columns.Column(default="", order_by="jistota__nazev_zkraceny")
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
    pristupnost = tables.Column(
        verbose_name=_("Pristupnost"),
        default="",
        accessor="archeologicky_zaznam.pristupnost",
    )

    columns_to_hide = None
    first_columns = None

    def get_column_default_show(self):
        self.column_default_show = list(self.columns.columns.keys())
        if "lokalita_vychozi_skryte_sloupce" in self.request.session:
            columns_to_hide = set(
                self.request.session["lokalita_vychozi_skryte_sloupce"]
            )
        else:
            columns_to_hide = ("uzivatelske_oznaceni", "dalsi_katastry")
        for column in columns_to_hide:
            if column is not None and column in self.column_default_show:
                self.column_default_show.remove(column)
        return super(LokalitaTable, self).get_column_default_show()

    class Meta:
        model = Lokalita
        # template_name = "projekt/bootstrap4.html"
        fields = (
            "druh",
            "nazev",
            "typ_lokality",
            "zachovalost",
            "jistota",
        )
        sequence = (
            "ident_cely",
            "stav",
            "pristupnost",
            "katastr",
            "typ_lokality",
            "druh",
            "nazev",
            "zachovalost",
            "jistota",
            "uzivatelske_oznaceni",
            "dalsi_katastry",
        )

        def __init__(self, *args, **kwargs):
            super(LokalitaTable, self).__init__(*args, **kwargs)
