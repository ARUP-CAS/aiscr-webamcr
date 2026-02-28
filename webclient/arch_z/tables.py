import django_tables2 as tables
from core.utils import SearchTable
from django.contrib.postgres.aggregates import StringAgg
from django.utils.translation import gettext_lazy as _

from .models import Akce


class BooleanValueColumn(tables.columns.Column):
    """Implementuje komponentu ``BooleanValueColumn`` v rámci aplikace."""

    def __init__(self, *args, **kwargs):
        """Inicializuje instanci třídy.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Funkce nevrací hodnotu (``None``)."""
        self.value_labels = kwargs.pop("value_labels", None)
        super(BooleanValueColumn, self).__init__(*args, **kwargs)

    def render(self, value):
        """Vyrenderuje booleovskou hodnotu do textové reprezentace pro tabulku.
        """
        value = [x for x in self.value_labels if x[0] == bool(value)]
        if len(value) > 0:
            return value[0][1]
        return ""


class AkceTable(SearchTable):
    """
    Definuje tabulku akcí pro přehled i export.
    """

    ident_cely = tables.Column(
        verbose_name=_("arch_z.tables.AkceTable.ident_cely.label"),
        linkify=True,
        accessor="archeologicky_zaznam__ident_cely",
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
    okres = tables.Column(
        verbose_name=_("arch_z.tables.AkceTable.okres.label"),
        default="",
        accessor="archeologicky_zaznam__hlavni_katastr__okres",
    )
    kraj = tables.Column(
        verbose_name=_("arch_z.tables.AkceTable.kraj.label"),
        default="",
        accessor="archeologicky_zaznam__hlavni_katastr__okres__kraj",
    )
    katastry = tables.ManyToManyColumn(
        verbose_name=_("arch_z.tables.AkceTable.katastry.label"),
        default="",
        accessor="archeologicky_zaznam__katastry",
        order_by="archeologicky_zaznam__katastry",
        orderable=True,
        separator="; ",
    )
    stav = tables.columns.Column(
        verbose_name=_("arch_z.tables.AkceTable.stav.label"), default="", accessor="archeologicky_zaznam__stav"
    )
    organizace = tables.columns.Column(
        verbose_name=_("arch_z.tables.AkceTable.organizace.label"), default="", order_by="organizace__nazev_zkraceny"
    )
    vedouci_organizace = tables.Column(
        verbose_name=_("arch_z.tables.AkceTable.vedouci_organizace.label"),
        default="",
        accessor="vedouci_organizace",
        orderable=False,
        attrs={
            "th": {"class": "white"},
        },
    )
    hlavni_vedouci = tables.columns.Column(verbose_name=_("arch_z.tables.AkceTable.hlavni_vedouci.label"), default="")
    vedouci = tables.Column(
        default="", accessor="vedouci_snapshot", verbose_name=_("arch_z.tables.AkceTable.vedouci.label")
    )
    uzivatelske_oznaceni = tables.columns.Column(
        verbose_name=_("arch_z.tables.AkceTable.uzivatelske_oznaceni.label"),
        default="",
        accessor="archeologicky_zaznam__uzivatelske_oznaceni",
    )
    datum_zahajeni = tables.columns.DateColumn(
        verbose_name=_("arch_z.tables.AkceTable.datum_zahajeni.label"),
        default="",
        format="Y-m-d",
    )
    datum_ukonceni = tables.columns.DateColumn(
        verbose_name=_("arch_z.tables.AkceTable.datum_ukonceni.label"),
        default="",
        format="Y-m-d",
    )
    hlavni_typ = tables.columns.Column(
        verbose_name=_("arch_z.tables.AkceTable.hlavni_typ.label"),
        default="",
    )
    vedlejsi_typ = tables.columns.Column(
        verbose_name=_("arch_z.tables.AkceTable.vedlejsi_typ.label"),
        default="",
    )
    lokalizace_okolnosti = tables.columns.Column(
        verbose_name=_("arch_z.tables.AkceTable.lokalizace_okolnosti.label"),
        default="",
    )
    specifikace_data = tables.columns.Column(
        verbose_name=_("arch_z.tables.AkceTable.specifikace_data.label"),
        default="",
    )
    ulozeni_nalezu = tables.columns.Column(
        verbose_name=_("arch_z.tables.AkceTable.ulozeni_nalezu.label"),
        default="",
    )
    ulozeni_dokumentace = tables.columns.Column(
        verbose_name=_("arch_z.tables.AkceTable.ulozeni_dokumentace.label"),
        default="",
    )
    je_nz = BooleanValueColumn(
        verbose_name=_("arch_z.tables.AkceTable.je_nz.label"),
        default="",
        value_labels=[(False, _("arch_z.tables.AkceTable.je_nz.ne")), (True, _("arch_z.tables.AkceTable.je_nz.ano"))],
    )
    odlozena_nz = BooleanValueColumn(
        verbose_name=_("arch_z.tables.AkceTable.odlozena_nz.label"),
        default="",
        value_labels=[
            (False, _("arch_z.tables.AkceTable.odlozena_nz.ne")),
            (True, _("arch_z.tables.AkceTable.odlozena_nz.ano")),
        ],
    )

    def order_vedouci_organizace(self, queryset, is_descending):
        """Provádí operaci order vedouci organizace.

        :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.
        :param is_descending: Vstupní hodnota ``is_descending`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        queryset = queryset.annotate(
            vedouci_organizace__nazev_zkraceny=StringAgg(
                "akcevedouci__organizace__nazev_zkraceny",
                delimiter=", ",
            )
        ).order_by(f"{'-' * (-1 * is_descending)}vedouci_organizace__nazev_zkraceny")
        return queryset, True

    app = "akce"
    columns_to_hide = (
        "pristupnost",
        "uzivatelske_oznaceni",
        "okres",
        "kraj",
        "katastry",
        "specifikace_data",
        "organizace_vedouci",
        "ulozeni_nalezu",
        "ulozeni_dokumentace",
        "je_nz",
        "odlozena_nz",
        "vedouci",
        "vedouci_organizace",
    )
    first_columns = None

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

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
            "okres",
            "kraj",
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
        """Inicializuje instanci třídy.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Funkce nevrací hodnotu (``None``)."""
        super(AkceTable, self).__init__(*args, **kwargs)

    def get_all_idents(self):
        """
        Vrátí seznam identifikátorů archeologických záznamů pro akci.
        """
        return ",".join([record.record.archeologicky_zaznam.ident_cely for record in self.paginated_rows])
