import django_tables2 as tables
from core.utils import SearchTable
from django.utils.translation import gettext_lazy as _

from .models import Lokalita


class LokalitaTable(SearchTable):
    """
    Class pro definování tabulky pro lokaity použitých pro zobrazení přehledu lokalit a exportu.
    """

    ident_cely = tables.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.ident_cely.label"),
        linkify=True,
        accessor="archeologicky_zaznam__ident_cely",
    )
    igsn = tables.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.igsn.label"),
        default="",
    )
    katastr = tables.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.katastr.label"),
        default="",
        accessor="archeologicky_zaznam__hlavni_katastr",
    )
    okres = tables.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.okres.label"),
        default="",
        accessor="archeologicky_zaznam__hlavni_katastr__okres",
    )
    kraj = tables.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.kraj.label"),
        default="",
        accessor="archeologicky_zaznam__hlavni_katastr__okres__kraj",
    )
    stav = tables.columns.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.stav.label"), default="", accessor="archeologicky_zaznam__stav"
    )
    druh = tables.columns.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.druh.label"), default="", order_by="druh__heslo"
    )
    nazev = tables.columns.Column(verbose_name=_("lokalita.tables.lokalitaTable.nazev.label"), default="")
    typ_lokality = tables.columns.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.typ_lokality.label"), default="", order_by="typ_lokality__heslo"
    )
    zachovalost = tables.columns.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.zachovalost.label"), default="", order_by="zachovalost__heslo"
    )
    jistota = tables.columns.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.jistota.label"), default="", order_by="jistota__heslo"
    )
    uzivatelske_oznaceni = tables.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.uzivatelskeOznaceni.label"),
        default="",
        accessor="archeologicky_zaznam__uzivatelske_oznaceni",
    )
    dalsi_katastry = tables.columns.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.dalsi_katastry.label"),
        default="",
        accessor="dalsi_katastry_snapshot",
    )
    pristupnost = tables.Column(
        verbose_name=_("lokalita.tables.lokalitaTable.pristupnost.label"),
        default="",
        accessor="archeologicky_zaznam__pristupnost",
    )

    columns_to_hide = ("igsn", "pristupnost", "uzivatelske_oznaceni", "dalsi_katastry", "okres", "kraj")
    app = "lokalita"
    first_columns = None

    class Meta:
        """Třída `LokalitaTable.Meta` v modulu `webclient.lokalita.tables`.
        
        Zapouzdřuje související data a chování v rámci dané části aplikace.
        """
        model = Lokalita
        fields = (
            "druh",
            "nazev",
            "typ_lokality",
            "zachovalost",
            "jistota",
        )
        sequence = (
            "ident_cely",
            "igsn",
            "stav",
            "pristupnost",
            "uzivatelske_oznaceni",
            "katastr",
            "okres",
            "kraj",
            "dalsi_katastry",
            "nazev",
            "typ_lokality",
            "druh",
            "zachovalost",
            "jistota",
        )

    def get_all_idents(self):
        """
        Vrátí seznam identifikátorů archeologických záznamů pro lokalitu.
        """
        return ",".join([record.record.archeologicky_zaznam.ident_cely for record in self.paginated_rows])
