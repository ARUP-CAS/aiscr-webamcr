import django_tables2 as tables
from core.utils import SearchTable
from django.utils.translation import gettext_lazy as _

from .models import ExterniZdroj


class ExterniZdrojTable(SearchTable):
    """
    Class pro definování tabulky pro externí zdroj použitých pro zobrazení přehledu zdrojů a exportu.
    """

    ident_cely = tables.Column(linkify=True, verbose_name=_("ez.tables.ezTable.ident_cely.label"))
    autori = tables.Column(default="", accessor="autori_snapshot", verbose_name=_("ez.tables.ezTable.autori.label"))
    editori = tables.Column(default="", accessor="editori_snapshot", verbose_name=_("ez.tables.ezTable.editori.label"))
    casopis_denik_nazev = tables.columns.Column(
        default="", verbose_name=_("ez.tables.ezTable.casopis_denik_nazev.label")
    )
    casopis_rocnik = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.casopis_rocnik.label"))
    sbornik_nazev = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.sbornik_nazev.label"))
    stav = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.stav.label"))
    typ = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.typ.label"))
    rok_vydani_vzniku = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.rok_vydani_vzniku.label"))
    datum_rd = tables.columns.DateColumn(default="", verbose_name=_("ez.tables.ezTable.datum_rd.label"), format="Y-m-d")
    edice_rada = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.edice_rada.label"))
    vydavatel = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.vydavatel.label"))
    typ_dokumentu = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.typ_dokumentu.label"))
    organizace = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.organizace.label"))
    paginace_titulu = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.paginace_titulu.label"))
    isbn = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.isbn.label"))
    issn = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.issn.label"))
    link = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.link.label"))
    poznamka = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.poznamka.label"))
    misto = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.misto.label"))
    nazev = tables.columns.Column(default="", verbose_name=_("ez.tables.ezTable.nazev.label"))
    columns_to_hide = (
        "datum_rd",
        "edice_rada",
        "misto",
        "vydavatel",
        "typ_dokumentu",
        "organizace",
        "paginace_titulu",
        "isbn",
        "issn",
        "link",
        "poznamka",
    )
    app = "ext_zdroj"
    first_columns = None

    class Meta:
        model = ExterniZdroj
        fields = (
            "stav",
            "typ",
            "rok_vydani_vzniku",
            "nazev",
            "casopis_denik_nazev",
            "casopis_rocnik",
            "sbornik_nazev",
            "datum_rd",
            "edice_rada",
            "misto",
            "vydavatel",
            "typ_dokumentu",
            "organizace",
            "paginace_titulu",
            "isbn",
            "issn",
            "link",
            "poznamka",
        )
        sequence = (
            "ident_cely",
            "stav",
            "typ",
            "autori",
            "rok_vydani_vzniku",
            "datum_rd",
            "nazev",
            "editori",
            "casopis_denik_nazev",
            "casopis_rocnik",
            "sbornik_nazev",
            "edice_rada",
            "misto",
            "vydavatel",
            "typ_dokumentu",
            "organizace",
            "paginace_titulu",
            "isbn",
            "issn",
            "link",
            "poznamka",
        )
