import django_tables2 as tables
from django.utils.translation import gettext as _

from lokalita.tables import DalsiKatastryColumn
from core.utils import SearchTable

from .models import Akce


class AkceTable(SearchTable):
    """
        Class pro definování tabulky pro akci použitých pro zobrazení přehledu akcií a exportu.
    """
    ident_cely = tables.Column(
        linkify=True, accessor="archeologicky_zaznam__ident_cely"
    )
    katastr = tables.Column(
        verbose_name=_("arch_z.tables.AkceTable.katastr.label"),
        default="",
        accessor="archeologicky_zaznam__hlavni_katastr",
    )
    pristupnost = tables.Column(
        verbose_name=_("arch_z.tables.AkceTable.pristupnost.label"),
        default="",
        accessor="archeologicky_zaznam__pristupnost",
    )
    hlavni_katastr = tables.Column(
        verbose_name=_("arch_z.tables.AkceTable.hlavni_katastr.label"),
        default="",
        accessor="archeologicky_zaznam__hlavni_katastr",
    )
    katastry = tables.Column(
        verbose_name=_("arch_z.tables.AkceTable.katastry.label"),
        default="",
        accessor="archeologicky_zaznam__katastry",
    )
    stav = tables.columns.Column(default="", accessor="archeologicky_zaznam__stav")
    organizace = tables.columns.Column(
        default="", order_by="organizace__nazev_zkraceny"
    )
    vedouci_organizace = tables.Column(
        verbose_name=_("arch_z.tables.AkceTable.vedouci_organizace.label"),
        default="",
        accessor="vedouci_organizace",
    )
    hlavni_vedouci = tables.columns.Column(default="")
    vedouci = tables.Column(
        verbose_name=_("arch_z.tables.AkceTable.vedouci.label"),
        default="",
        accessor="vedouci",
    )
    uzivatelske_oznaceni = tables.Column(
        verbose_name=_("arch_z.tables.AkceTable.uzivatelske_oznaceni.label"),
        default="",
        accessor="archeologicky_zaznam__uzivatelske_oznaceni",
    )
    dalsi_katastry = DalsiKatastryColumn(
        verbose_name=_("arch_z.tables.AkceTable.dalsi_katastry.label"),
        default="",
        accessor="archeologicky_zaznam__katastry__all",
    )
    app = "akce"
    columns_to_hide = \
        ("pristupnost",
         "uzivatelske_oznaceni",
         "katastry",
         "specifikace_data",
         "organizace_vedouci",
         "ulozeni_nalezu",
         "ulozeni_dokumentace",
         "je_nz",
         "odlozena_nz",
         )
    first_columns = None

    class Meta:
        model = Akce
        fields = (
            "hlavni_vedouci",
            "organizace",
            "specifikace_data",
            "datum_zahajeni",
            "datum_ukonceni",
            "hlavni_typ",
            "vedlejsi_typ",
            "lokalizace_okolnosti",
            "ulozeni_nalezu",
            "ulozeni_dokumentace",
            "je_nz",
            "odlozena_nz",
        )
        sequence = (
            "ident_cely",
            "stav",
            "pristupnost",
            "uzivatelske_oznaceni",
            "hlavni_katastr",
            "katastry",
            "specifikace_data",
            "datum_zahajeni",
            "datum_ukonceni",
            "organizace",
            "vedouci_organizace",
            "hlavni_vedouci",
            "vedouci",
            "hlavni_typ",
            "vedlejsi_typ",
            "lokalizace_okolnosti",
            "ulozeni_nalezu",
            "ulozeni_dokumentace",
            "je_nz",
            "odlozena_nz",
        )

        def __init__(self, *args, **kwargs):
            super(AkceTable, self).__init__(*args, **kwargs)
