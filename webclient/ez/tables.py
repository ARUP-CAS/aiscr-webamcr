import django_tables2 as tables
from django_tables2_column_shifter.tables import ColumnShiftTableBootstrap4
from django_tables2.utils import A
from django.utils.translation import gettext as _
from django.utils.html import conditional_escape, mark_safe
from django.utils.encoding import force_str
from django.db.models import OuterRef, Subquery

from uzivatel.models import Osoba

from .models import ExterniZdroj


class ExtZdrojAutoriColumn(tables.Column):
    def render(self, record, value):
        if value:
            osoby = Osoba.objects.filter(
                externizdrojautor__externi_zdroj__ident_cely=record
            ).order_by("externizdrojautor__poradi")
            items = []
            for autor in osoby:
                content = conditional_escape(force_str(autor))
                items.append(content)

            return mark_safe(conditional_escape("; ").join(items))
        else:
            return ""

    def order(self, queryset, is_descending):
        comments = (
            Osoba.objects.filter(externizdrojautor__externi_zdroj=OuterRef("pk"))
            .order_by("externizdrojautor__poradi")
            .values("vypis_cely")
        )
        queryset = queryset.annotate(length=Subquery(comments[:1])).order_by(
            ("-" if is_descending else "") + "length"
        )
        return (queryset, True)


class ExtZdrojEditoriColumn(ExtZdrojAutoriColumn):
    def render(self, record, value):
        if value:
            osoby = Osoba.objects.filter(
                externizdrojeditor__externi_zdroj__ident_cely=record
            ).order_by("externizdrojeditor__poradi")
            items = []
            for autor in osoby:
                content = conditional_escape(force_str(autor))
                items.append(content)

            return mark_safe(conditional_escape("; ").join(items))
        else:
            return ""

    def order(self, queryset, is_descending):
        comments = (
            Osoba.objects.filter(externizdrojeditor__externi_zdroj=OuterRef("pk"))
            .order_by("externizdrojeditor__poradi")
            .values("vypis_cely")
        )
        queryset = queryset.annotate(length=Subquery(comments[:1])).order_by(
            ("-" if is_descending else "") + "length"
        )
        return (queryset, True)


class ExterniZdrojTable(ColumnShiftTableBootstrap4):

    ident_cely = tables.Column(linkify=True)
    autor = ExtZdrojAutoriColumn(default="", accessor="autori.all")
    editor = ExtZdrojEditoriColumn(default="", accessor="editori.all")
    casopis_denik_nazev = tables.columns.Column(default="")
    casopis_rocnik = tables.columns.Column(default="")
    sbornik_nazev = tables.columns.Column(default="")
    sysno = tables.columns.Column(default="")
    columns_to_hide = None
    first_columns = None

    def get_column_default_show(self):
        self.column_default_show = list(self.columns.columns.keys())
        if "extzdroj_vychozi_skryte_sloupce" in self.request.session:
            columns_to_hide = set(
                self.request.session["extzdroj_vychozi_skryte_sloupce"]
            )
        else:
            columns_to_hide = (
                "editor",
                "casopis_denik_nazev",
                "casopis_rocnik",
                "sbornik_nazev",
                "sysno",
            )
        for column in columns_to_hide:
            if column is not None and column in self.column_default_show:
                self.column_default_show.remove(column)
        return super(ExterniZdrojTable, self).get_column_default_show()

    class Meta:
        model = ExterniZdroj
        # template_name = "projekt/bootstrap4.html"
        fields = (
            "stav",
            "typ",
            "rok_vydani_vzniku",
            "nazev",
            "casopis_denik_nazev",
            "casopis_rocnik",
            "sbornik_nazev",
            "sysno",
        )
        sequence = (
            "ident_cely",
            "stav",
            "typ",
            "autor",
            "rok_vydani_vzniku",
            "nazev",
            "editor",
            "casopis_denik_nazev",
            "casopis_rocnik",
            "sbornik_nazev",
            "sysno",
        )

        def __init__(self, *args, **kwargs):
            super(ExterniZdrojTable, self).__init__(*args, **kwargs)
