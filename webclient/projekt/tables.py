import logging
from datetime import timedelta

import django_tables2 as tables
from core.utils import SearchTable
from django.utils.translation import gettext_lazy as _
from psycopg2._range import DateRange

from .models import Projekt

logger = logging.getLogger(__name__)


class ProjektTable(SearchTable):
    """
    Třída pro definování tabulky pro projekt použitých pro zobrazení přehledu projektů a exportu.
    """

    ident_cely = tables.Column(verbose_name=_("projekt.tables.ProjektTable.ident_cely.label"), linkify=True)
    datum_zahajeni = tables.columns.DateTimeColumn(
        verbose_name=_("projekt.tables.ProjektTable.datum_zahajeni.label"), format="Y-m-d", default=""
    )
    datum_ukonceni = tables.columns.DateTimeColumn(
        verbose_name=_("projekt.tables.ProjektTable.datum_ukonceni.label"), format="Y-m-d", default=""
    )
    organizace = tables.columns.Column(
        verbose_name=_("projekt.tables.ProjektTable.organizace.label"),
        default="",
        order_by="organizace__nazev_zkraceny",
    )
    vedouci_projektu = tables.columns.Column(
        verbose_name=_("projekt.tables.ProjektTable.vedouci_projektu.label"), default=""
    )
    kulturni_pamatka = tables.columns.Column(
        verbose_name=_("projekt.tables.ProjektTable.kulturni_pamatka.label"), default=""
    )
    uzivatelske_oznaceni = tables.columns.Column(
        verbose_name=_("projekt.tables.ProjektTable.uzivatelske_oznaceni.label"), default=""
    )
    planovane_zahajeni = tables.columns.Column(
        verbose_name=_("projekt.tables.ProjektTable.planovane_zahajeni.label"), default=""
    )
    katastry = tables.ManyToManyColumn(
        verbose_name=_("projekt.tables.ProjektTable.katastry.label"),
        default="",
        accessor="katastry",
        order_by="katastry",
        orderable=True,
        separator="; ",
    )
    termin_odevzdani_nz = tables.columns.Column(
        verbose_name=_("projekt.tables.ProjektTable.termin_odevzdani_nz.label"), default=""
    )
    lokalizace = tables.columns.Column(verbose_name=_("projekt.tables.ProjektTable.lokalizace.label"), default="")
    parcelni_cislo = tables.columns.Column(
        verbose_name=_("projekt.tables.ProjektTable.parcelni_cislo.label"), default=""
    )
    oznaceni_stavby = tables.columns.Column(
        verbose_name=_("projekt.tables.ProjektTable.oznaceni_stavby.label"), default=""
    )
    columns_to_hide = (
        "uzivatelske_oznaceni",
        "hlavni_katastr__okres",
        "hlavni_katastr__okres__kraj",
        "katastry",
        "termin_odevzdani_nz",
        "lokalizace",
        "parcelni_cislo",
        "vedouci_projektu",
        "kulturni_pamatka",
    )
    app = "projekt"

    class Meta:
        """Třída `ProjektTable.Meta` v modulu `webclient.projekt.tables`.
        
        Zapouzdřuje související data a chování v rámci dané části aplikace.
        """
        model = Projekt
        fields = (
            "ident_cely",
            "stav",
            "typ_projektu",
            "hlavni_katastr",
            "hlavni_katastr__okres",
            "hlavni_katastr__okres__kraj",
            "katastry",
            "lokalizace",
            "parcelni_cislo",
            "podnet",
            "oznaceni_stavby",
            "planovane_zahajeni",
            "organizace",
            "vedouci_projektu",
            "uzivatelske_oznaceni",
            "datum_zahajeni",
            "datum_ukonceni",
            "termin_odevzdani_nz",
            "kulturni_pamatka",
            "typ_projektu",
            "uzivatelske_oznaceni",
            "planovane_zahajeni",
            "katastry",
            "termin_odevzdani_nz",
            "oznaceni_stavby",
            "parcelni_cislo",
        )
        sequence = (
            "ident_cely",
            "stav",
            "typ_projektu",
            "hlavni_katastr",
            "hlavni_katastr__okres",
            "hlavni_katastr__okres__kraj",
            "katastry",
            "lokalizace",
            "parcelni_cislo",
            "podnet",
            "oznaceni_stavby",
            "planovane_zahajeni",
            "organizace",
            "vedouci_projektu",
            "uzivatelske_oznaceni",
            "datum_zahajeni",
            "datum_ukonceni",
            "termin_odevzdani_nz",
            "kulturni_pamatka",
        )

    def render_planovane_zahajeni(self, value):
        """Funkce `ProjektTable.render_planovane_zahajeni` v modulu `webclient.projekt.tables`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param value: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if value == "" or value is None:
            return None
        if isinstance(value, DateRange):
            if value.lower and value.upper:
                format_str = "%Y-%m-%d"
                return f"{value.lower.strftime(format_str)} - {(value.upper - timedelta(days=1)).strftime(format_str)}"
        return str(value)

    def __init__(self, *args, **kwargs):
        """Funkce `ProjektTable.__init__` v modulu `webclient.projekt.tables`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param args: Vstupní hodnota používaná při zpracování.
        :param kwargs: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        super(ProjektTable, self).__init__(*args, **kwargs)
        # self.set_hideable_columns(['ident_cely', 'stav']) Odkomentovat, až bude podpora dostupná.
