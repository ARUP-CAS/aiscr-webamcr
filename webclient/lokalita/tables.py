import django_tables2 as tables
from django_tables2.utils import A
from django.utils.translation import gettext as _
from django.utils.html import conditional_escape, mark_safe
from django.utils.encoding import force_str
from django.db import models

from heslar.models import RuianKatastr
from core.utils import SearchTable

from .models import Lokalita


class DalsiKatastryColumn(tables.Column):
    """
    Třída pro sloupec další katastry lokality.
    """
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


class LokalitaTable(SearchTable):
    """
    Class pro definování tabulky pro lokaity použitých pro zobrazení přehledu lokalit a exportu.
    """
    ident_cely = tables.Column(
        linkify=True, accessor="archeologicky_zaznam__ident_cely"
    )
    katastr = tables.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.katastr.label"),
        default="",
        accessor="archeologicky_zaznam__hlavni_katastr",
    )
    stav = tables.columns.Column(default="", accessor="archeologicky_zaznam__stav")
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
        verbose_name=_("lokalita.tables.lokalitaTable.uzivatelskeOznaceni.label"),
        default="",
        accessor="archeologicky_zaznam__uzivatelske_oznaceni",
    )
    dalsi_katastry = DalsiKatastryColumn(
        verbose_name=_("lokalita.tables.lokalitaTable.dalsiKatastry.label"),
        default="",
        accessor="archeologicky_zaznam__katastry__all",
    )
    pristupnost = tables.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.pristupnost.label"),
        default="",
        accessor="archeologicky_zaznam__pristupnost",
    )

    columns_to_hide = ("pristupnost", "uzivatelske_oznaceni", "dalsi_katastry")
    app = "lokalita"
    first_columns = None

    class Meta:
        model = Lokalita
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
            "uzivatelske_oznaceni",
            "katastr",
            "dalsi_katastry",
            "nazev",
            "typ_lokality",
            "druh",
            "zachovalost",
            "jistota",
        )

        def __init__(self, *args, **kwargs):
            super(LokalitaTable, self).__init__(*args, **kwargs)
