import logging

import django_tables2 as tables
from django_tables2_column_shifter.tables import ColumnShiftTableBootstrap4

from .models import Dokument

logger = logging.getLogger(__name__)


class DokumentTable(ColumnShiftTableBootstrap4):

    ident_cely = tables.Column(linkify=True)

    # def get_column_default_show(self):
    #     self.column_default_show = list(self.columns.columns.keys())
    #     if "projekt_vychozi_skryte_sloupce" in self.request.session:
    #         columns_to_hide = set(self.request.session["projekt_vychozi_skryte_sloupce"])
    #         for column in columns_to_hide:
    #             if column is not None and column in self.column_default_show:
    #                 self.column_default_show.remove(column)
    #     return super(ProjektTable, self).get_column_default_show()

    class Meta:
        model = Dokument
        # template_name = "projekt/bootstrap4.html"
        fields = (
            "ident_cely",
            "stav",
            "typ_dokumentu",
            "organizace",
            "popis",
            "extra_data__datum_vzniku",
            "extra_data__format",
            "extra_data__odkaz",
            "extra_data__duveryhodnost",
        )

    def __init__(self, *args, **kwargs):
        super(DokumentTable, self).__init__(*args, **kwargs)
