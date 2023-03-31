import django_tables2 as tables
from django.utils.translation import gettext as _

from lokalita.tables import DalsiKatastryColumn
from core.utils import SearchTable

from .models import Akce


class AkceTable(SearchTable):
    ident_cely = tables.Column(
        linkify=True, accessor="archeologicky_zaznam__ident_cely"
    )
    katastr = tables.Column(
        verbose_name=_("Katastrální území"),
        default="",
        accessor="archeologicky_zaznam__hlavni_katastr",
    )
    stav = tables.columns.Column(default="", accessor="archeologicky_zaznam__stav")
    organizace = tables.columns.Column(
        default="", order_by="organizace__nazev_zkraceny"
    )
    hlavni_vedouci = tables.columns.Column(default="")
    uzivatelske_oznaceni = tables.Column(
        verbose_name=_("Uživatelské označení"),
        default="",
        accessor="archeologicky_zaznam__uzivatelske_oznaceni",
    )
    dalsi_katastry = DalsiKatastryColumn(
        verbose_name=_("Další katastry"),
        default="",
        accessor="archeologicky_zaznam__katastry__all",
    )
    app = "akce"
    columns_to_hide = ("uzivatelske_oznaceni", "dalsi_katastry")
    first_columns = None

    class Meta:
        model = Akce
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
