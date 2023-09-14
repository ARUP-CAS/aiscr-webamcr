import django_tables2 as tables
from django.db import models
from django.utils.encoding import force_str
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from lokalita.tables import DalsiKatastryColumn
from core.utils import SearchTable

from .models import Akce, AkceVedouci


class AkceVedouciColumn(tables.Column):
    """
    Třída pro sloupec další katastry lokality.
    """
    def render(self, value):
        if value:
            items = []
            for item in value:
                content = conditional_escape(force_str(item.vedouci))
                items.append(content)

            return mark_safe(conditional_escape("; ").join(items))
        else:
            return ""

    def order(self, queryset, is_descending):
        vedouci_vypis_cely = (
            AkceVedouci.objects.filter(
                akce=models.OuterRef(
                    "pk"
                )
            )
            .values("vedouci__vypis_cely")
            .order_by("vedouci__vypis_cely")
        )
        queryset = queryset.annotate(vedouci_vypis_cely=models.Subquery(vedouci_vypis_cely[:1])).order_by(
            ("-" if is_descending else "") + "vedouci_vypis_cely"
        )
        return queryset, True


class AkceVedouciOrganizaceColumn(tables.Column):
    """
    Třída pro sloupec další katastry lokality.
    """
    def render(self, value):
        if value:
            items = []
            for item in value:
                content = conditional_escape(force_str(item.organizace))
                items.append(content)

            return mark_safe(conditional_escape("; ").join(items))
        else:
            return ""

    def order(self, queryset, is_descending):
        organizace_nazev_zkraceny = (
            AkceVedouci.objects.filter(
                akce=models.OuterRef(
                    "pk"
                )
            )
            .values("organizace__nazev_zkraceny")
            .order_by("organizace__nazev_zkraceny")
        )
        queryset = queryset.annotate(organizace_nazev_zkraceny=models.Subquery(organizace_nazev_zkraceny[:1])).order_by(
            ("-" if is_descending else "") + "organizace_nazev_zkraceny"
        )
        return queryset, True


class AkceTable(SearchTable):
    """
        Class pro definování tabulky pro akci použitých pro zobrazení přehledu akcií a exportu.
    """
    ident_cely = tables.Column(
        linkify=True, accessor="archeologicky_zaznam__ident_cely"
    )
    stav = tables.columns.Column(default="", accessor="archeologicky_zaznam__stav")
    organizace = tables.columns.Column(
        default="", order_by="organizace__nazev_zkraceny"
    )
    hlavni_vedouci = tables.columns.Column(default="")
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
    akce_vedouci_organizace = AkceVedouciOrganizaceColumn(
        verbose_name=_("arch_z.tables.AkceTable.akce_vedouci_organizace.label"),
        default="",
        accessor="akcevedouci_set__all",
    )
    akce_vedouci_vedouci = AkceVedouciColumn(
        verbose_name=_("arch_z.tables.AkceTable.akce_vedouci_vedouci.label"),
        default="",
        accessor="akcevedouci_set__all",
    )
    hlavni_katastr = tables.Column(
        verbose_name=_("arch_z.tables.AkceTable.hlavni_katastr.label"),
        default="",
        accessor="archeologicky_zaznam__hlavni_katastr",
    )

    app = "akce"
    columns_to_hide = ("uzivatelske_oznaceni", "dalsi_katastry")
    first_columns = None

    class Meta:
        model = Akce
        fields = (
            "pristupnost",
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
            "dalsi_katastry",
            "specifikace_data",
            "datum_zahajeni",
            "datum_ukonceni",
            "organizace",
            "akce_vedouci_organizace",
            "hlavni_vedouci",
            "akce_vedouci_vedouci",
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
