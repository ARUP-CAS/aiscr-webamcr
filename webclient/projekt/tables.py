import logging
import django_tables2 as tables

from core.utils import SearchTable

from .models import Projekt

logger = logging.getLogger('python-logstash-logger')

class ProjektTable(SearchTable):

    ident_cely = tables.Column(linkify=True)
    datum_zahajeni = tables.columns.DateTimeColumn(format ='Y-m-d',default="")
    datum_ukonceni = tables.columns.DateTimeColumn(format ='Y-m-d',default="")
    organizace = tables.columns.Column(default="", order_by="organizace__nazev_zkraceny")
    vedouci_projektu = tables.columns.Column(default="")
    kulturni_pamatka = tables.columns.Column(default="")
    uzivatelske_oznaceni = tables.columns.Column(default="")
    planovane_zahajeni = tables.columns.Column(default="")
    columns_to_hide = (
                "kulturni_pamatka",
                "typ_projektu",
            )
    app = "projekt"

    class Meta:
        model = Projekt
        fields = (
            "ident_cely",
            "stav",
            "hlavni_katastr",
            "podnet",
            "lokalizace",
            "datum_zahajeni",
            "datum_ukonceni",
            "organizace",
            "vedouci_projektu",
            "kulturni_pamatka",
            "typ_projektu",
            "uzivatelske_oznaceni",
            "planovane_zahajeni",
        )

    def __init__(self, *args, **kwargs):
        super(ProjektTable, self).__init__(*args, **kwargs)
        # self.set_hideable_columns(['ident_cely', 'stav']) Uncomment when will be supported

