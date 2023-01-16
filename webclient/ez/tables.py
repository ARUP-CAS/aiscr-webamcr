import django_tables2 as tables
from django_tables2.utils import A
from django.utils.translation import gettext as _
from django.utils.html import conditional_escape, mark_safe
from django.utils.encoding import force_str
from django.db.models import OuterRef, Subquery

from uzivatel.models import Osoba
from core.utils import SearchTable

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


class ExterniZdrojTable(SearchTable):

    ident_cely = tables.Column(linkify=True)
    autor = ExtZdrojAutoriColumn(default="", accessor="autori.all")
    editor = ExtZdrojEditoriColumn(default="", accessor="editori.all")
    casopis_denik_nazev = tables.columns.Column(default="")
    casopis_rocnik = tables.columns.Column(default="")
    sbornik_nazev = tables.columns.Column(default="")
    sysno = tables.columns.Column(default="")
    columns_to_hide = (
        "editor",
        "casopis_denik_nazev",
        "casopis_rocnik",
        "sbornik_nazev",
        "sysno",
    )
    app = "ext_zdroj"
    first_columns = None

    class Meta:
        model = ExterniZdroj
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
