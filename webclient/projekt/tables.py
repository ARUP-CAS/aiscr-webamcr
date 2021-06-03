import logging
import django_tables2 as tables

from .models import Projekt
from django_tables2_column_shifter.tables import (
    ColumnShiftTableBootstrap4,
)

logger = logging.getLogger(__name__)

class ProjektTable(ColumnShiftTableBootstrap4):

    ident_cely = tables.Column(linkify=True)

    def get_column_default_show(self):
        self.column_default_show = list(self.columns.columns.keys())
        if "projekt_vychozi_skryte_sloupce" in self.request.session:
            columns_to_hide = set(self.request.session["projekt_vychozi_skryte_sloupce"])
            for column in columns_to_hide:
                if column is not None and column in self.column_default_show:
                    self.column_default_show.remove(column)
        return super(ProjektTable, self).get_column_default_show()

    class Meta:
        model = Projekt
        template_name = "projekt/bootstrap4.html"
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
        )

    def __init__(self, *args, **kwargs):
        super(ProjektTable, self).__init__(*args, **kwargs)
        # self.set_hideable_columns(['ident_cely', 'stav']) Uncomment when will be supported

    @staticmethod
    def render_datum_zahajeni(value):
        if value:
            return value.strftime("%Y/%m/%d")
        else:
            return "—"

    @staticmethod
    def render_datum_ukonceni(value):
        if value:
            return value.strftime("%Y/%m/%d")
        else:
            return "—"
