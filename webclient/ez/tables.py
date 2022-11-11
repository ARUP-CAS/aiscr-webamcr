import django_tables2 as tables
from django_tables2_column_shifter.tables import ColumnShiftTableBootstrap4
from django_tables2.utils import A
from django.utils.translation import gettext as _

from .models import ExterniZdroj


class ExterniZdrojTable(ColumnShiftTableBootstrap4):

    ident_cely = tables.Column(linkify=True)
    autor = tables.Column(accessor="externizdrojautor.autor", default="")
    editor = tables.Column(accessor="externizdrojeditor.editor", default="")
    casopis_denik_nazev = tables.columns.Column(default="")
    casopis_rocnik = tables.columns.Column(default="")
    sbornik_nazev = tables.columns.Column(default="")
    sysno = tables.columns.Column(default="")
    columns_to_hide = None
    first_columns = None

    def get_column_default_show(self):
        self.column_default_show = list(self.columns.columns.keys())
        if "extzdroj_vychozi_skryte_sloupce" in self.request.session:
            columns_to_hide = set(
                self.request.session["extzdroj_vychozi_skryte_sloupce"]
            )
        else:
            columns_to_hide = (
                "editor",
                "casopis_denik_nazev",
                "casopis_rocnik",
                "sbornik_nazev",
                "sysno",
            )
        for column in columns_to_hide:
            if column is not None and column in self.column_default_show:
                self.column_default_show.remove(column)
        return super(ExterniZdrojTable, self).get_column_default_show()

    class Meta:
        model = ExterniZdroj
        # template_name = "projekt/bootstrap4.html"
        fields = (
            "stav",
            "typ",
            "rok_vydani_vzniku",
            "nazev",
            "casopis_denik_nazev",
            "casopis_rocnik",
            "sbornik_nazev",
            "sysno",
        )
        sequence = (
            "ident_cely",
            "stav",
            "typ",
            "autor",
            "rok_vydani_vzniku",
            "nazev",
            "editor",
            "casopis_denik_nazev",
            "casopis_rocnik",
            "sbornik_nazev",
            "sysno",
        )

        def __init__(self, *args, **kwargs):
            super(ExterniZdrojTable, self).__init__(*args, **kwargs)
