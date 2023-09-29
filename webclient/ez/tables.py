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
    """
    Třída pro sloupec autori externího zdroje, kvůli zohlednení pořadí zadání.
    """
    def render(self, record, value):
        if value:
            osoby = record.ordered_autors
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
    """
    Třída pro sloupec editori externího zdroje, kvůli zohlednení pořadí zadání.
    """
    def render(self, record, value):
        if value:
            osoby = record.ordered_editors
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
    """
    Class pro definování tabulky pro externí zdroj použitých pro zobrazení přehledu zdrojů a exportu.
    """
    ident_cely = tables.Column(linkify=True)
    autori = ExtZdrojAutoriColumn(default="", accessor="autori__all")
    editori = ExtZdrojEditoriColumn(default="", accessor="editori__all")
    casopis_denik_nazev = tables.columns.Column(default="")
    casopis_rocnik = tables.columns.Column(default="")
    sbornik_nazev = tables.columns.Column(default="")
    sysno = tables.columns.Column(default="")
    columns_to_hide = (
        "sysno",
        "datum_rd",
        "edice_rada",
        "misto",
        "vydavatel",
        "typ_dokumentu",
        "organizace",
        "paginace_titulu",
        "isbn",
        "issn",
        "link",
        "poznamka"
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
            "datum_rd",
            "edice_rada",
            "misto",
            "vydavatel",
            "typ_dokumentu",
            "organizace",
            "paginace_titulu",
            "isbn",
            "issn",
            "link",
            "poznamka",
        )
        sequence = (
            "ident_cely",
            "sysno",
            "stav",
            "typ",
            "autori",
            "rok_vydani_vzniku",
            "datum_rd",
            "nazev",
            "editori",
            "casopis_denik_nazev",
            "casopis_rocnik",
            "sbornik_nazev",
            "edice_rada",
            "misto",
            "vydavatel",
            "typ_dokumentu",
            "organizace",
            "paginace_titulu",
            "isbn",
            "issn",
            "link",
            "poznamka",
        )
