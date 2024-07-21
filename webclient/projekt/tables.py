import logging
import django_tables2 as tables

from django.utils.translation import gettext_lazy as _

from core.utils import SearchTable
from .models import Projekt

logger = logging.getLogger(__name__)


class ProjektTable(SearchTable):
    """
    Třída pro definování tabulky pro projekt použitých pro zobrazení přehledu projektů a exportu.
    """
    ident_cely = tables.Column(verbose_name=_("projekt.tables.ProjektTable.ident_cely.label"),linkify=True)
    datum_zahajeni = tables.columns.DateTimeColumn(verbose_name=_("projekt.tables.ProjektTable.datum_zahajeni.label"),format ='Y-m-d',default="")
    datum_ukonceni = tables.columns.DateTimeColumn(verbose_name=_("projekt.tables.ProjektTable.datum_ukonceni.label"),format ='Y-m-d',default="")
    organizace = tables.columns.Column(verbose_name=_("projekt.tables.ProjektTable.organizace.label"),default="", order_by="organizace__nazev_zkraceny")
    vedouci_projektu = tables.columns.Column(verbose_name=_("projekt.tables.ProjektTable.vedouci_projektu.label"),default="")
    kulturni_pamatka = tables.columns.Column(verbose_name=_("projekt.tables.ProjektTable.kulturni_pamatka.label"),default="")
    uzivatelske_oznaceni = tables.columns.Column(verbose_name=_("projekt.tables.ProjektTable.uzivatelske_oznaceni.label"),default="")
    planovane_zahajeni = tables.columns.Column(verbose_name=_("projekt.tables.ProjektTable.planovane_zahajeni.label"),default="")
    katastry = tables.ManyToManyColumn(verbose_name=_("projekt.tables.ProjektTable.katastry.label"), default="",
                                       accessor="katastry", order_by="katastry", orderable=True, separator="; ")
    termin_odevzdani_nz = tables.columns.Column(verbose_name=_("projekt.tables.ProjektTable.termin_odevzdani_nz.label"),default="")
    lokalizace = tables.columns.Column(verbose_name=_("projekt.tables.ProjektTable.lokalizace.label"),default="")
    parcelni_cislo = tables.columns.Column(verbose_name=_("projekt.tables.ProjektTable.parcelni_cislo.label"),default="")
    oznaceni_stavby = tables.columns.Column(verbose_name=_("projekt.tables.ProjektTable.oznaceni_stavby.label"),default="")
    columns_to_hide = (
        "uzivatelske_oznaceni",
        "katastry",
        "termin_odevzdani_nz",
        "lokalizace",
        "parcelni_cislo",
        "vedouci_projektu",
        "kulturni_pamatka",
    )
    app = "projekt"

    class Meta:
        model = Projekt
        fields = (
            "ident_cely",
            "stav",
            "typ_projektu",
            "hlavni_katastr",
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
            'termin_odevzdani_nz',
            'oznaceni_stavby',
            'parcelni_cislo',
        )
        sequence = (
            "ident_cely",
            "stav",
            "typ_projektu",
            "hlavni_katastr",
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
            "kulturni_pamatka"
        )

    def __init__(self, *args, **kwargs):
        super(ProjektTable, self).__init__(*args, **kwargs)
        # self.set_hideable_columns(['ident_cely', 'stav']) Uncomment when will be supported

