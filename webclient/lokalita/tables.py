import django_tables2 as tables
from django_tables2.utils import A
from django.utils.translation import gettext_lazy as _
from django.utils.html import conditional_escape, mark_safe
from django.utils.encoding import force_str
from django.db import models

from heslar.models import RuianKatastr
from core.utils import SearchTable

from .models import Lokalita


class LokalitaTable(SearchTable):
    """
    Class pro definování tabulky pro lokaity použitých pro zobrazení přehledu lokalit a exportu.
    """
    ident_cely = tables.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.ident_cely.label"),
        linkify=True,
        accessor="archeologicky_zaznam__ident_cely"
    )
    katastr = tables.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.katastr.label"),
        default="",
        accessor="archeologicky_zaznam__hlavni_katastr",
    )
    stav = tables.columns.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.stav.label"),
        default="",
        accessor="archeologicky_zaznam__stav"
    )
    druh = tables.columns.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.druh.label"),
        default="",
        order_by="druh__nazev_zkraceny"
    )
    nazev = tables.columns.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.nazev.label"),
        default=""
    )
    typ_lokality = tables.columns.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.typ_lokality.label"),
        default="",
        order_by="typ_lokality__nazev_zkraceny"
    )
    zachovalost = tables.columns.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.zachovalost.label"),
        default="",
        order_by="zachovalost__nazev_zkraceny"
    )
    jistota = tables.columns.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.jistota.label"),
        default="",
        order_by="jistota__nazev_zkraceny"
    )
    uzivatelske_oznaceni = tables.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.uzivatelskeOznaceni.label"),
        default="",
        accessor="archeologicky_zaznam__uzivatelske_oznaceni",
    )
    dalsi_katastry = tables.columns.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.dalsi_katastry.label"),
        default="",
        accessor="dalsi_katastry_snapshot"
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
