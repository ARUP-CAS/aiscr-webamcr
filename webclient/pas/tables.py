import logging

import django_tables2 as tables
from core.constants import ROLE_BADATEL_ID
from core.models import Permissions as p
from core.models import Soubor, check_permissions
from core.utils import SearchTable
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_tables2.utils import A

from .models import SamostatnyNalez, UzivatelSpoluprace

logger = logging.getLogger(__name__)


class SamostatnyNalezTable(SearchTable):
    """Definuje tabulku samostatných nálezů pro přehled i export."""

    ident_cely = tables.Column(verbose_name=_("pas.tables.samostatnyNalezTable.ident_cely.label"), linkify=True)
    igsn = tables.Column(verbose_name=_("pas.tables.samostatnyNalezTable.igsn.label"), default="")
    katastr = tables.Column(verbose_name=_("pas.tables.samostatnyNalezTable.katastr.label"), default="")
    kraj = tables.Column(
        verbose_name=_("pas.tables.samostatnyNalezTable.kraj.label"), default="", accessor="katastr__okres__kraj"
    )
    okres = tables.Column(
        verbose_name=_("pas.tables.samostatnyNalezTable.okres.label"), default="", accessor="katastr__okres"
    )
    datum_nalezu = tables.columns.DateTimeColumn(
        verbose_name=_("pas.tables.samostatnyNalezTable.datum_nalezu.label"), format="Y-m-d", default=""
    )
    lokalizace = tables.columns.Column(verbose_name=_("pas.tables.samostatnyNalezTable.lokalizace.label"), default="")
    obdobi = tables.columns.Column(verbose_name=_("pas.tables.samostatnyNalezTable.obdobi.label"), default="")
    druh_nalezu = tables.columns.Column(verbose_name=_("pas.tables.samostatnyNalezTable.druh_nalezu.label"), default="")
    specifikace = tables.columns.Column(verbose_name=_("pas.tables.samostatnyNalezTable.specifikace.label"), default="")
    nalezce = tables.columns.Column(verbose_name=_("pas.tables.samostatnyNalezTable.nalezce.label"), default="")
    evidencni_cislo = tables.columns.Column(
        verbose_name=_("pas.tables.samostatnyNalezTable.evidencni_cislo.label"), default=""
    )
    predano = tables.columns.Column(verbose_name=_("pas.tables.samostatnyNalezTable.predano.label"), default="")
    predano_organizace = tables.columns.Column(
        verbose_name=_("pas.tables.samostatnyNalezTable.predano_organizace.label"),
        default="",
        order_by="predano_organizace__nazev_zkraceny",
    )
    stav = tables.columns.Column(verbose_name=_("pas.tables.samostatnyNalezTable.stav.label"), default="")
    pristupnost = tables.columns.Column(verbose_name=_("pas.tables.samostatnyNalezTable.pristupnost.label"), default="")
    presna_datace = tables.columns.Column(
        verbose_name=_("pas.tables.samostatnyNalezTable.presna_datace.label"), default=""
    )
    pocet = tables.columns.Column(verbose_name=_("pas.tables.samostatnyNalezTable.pocet.label"), default="")
    poznamka = tables.columns.Column(verbose_name=_("pas.tables.samostatnyNalezTable.poznamka.label"), default="")
    okolnosti = tables.columns.Column(verbose_name=_("pas.tables.samostatnyNalezTable.okolnosti.label"), default="")
    hloubka = tables.columns.Column(verbose_name=_("pas.tables.samostatnyNalezTable.hloubka.label"), default="")
    app = "samostatny_nalez"
    nahled = tables.columns.Column(
        default="",
        accessor="soubory",
        attrs={
            "th": {"class": "white"},
        },
        orderable=False,
        verbose_name=_("pas.tables.samostatnyNalezTable.nahled.label"),
    )
    columns_to_hide = (
        "igsn",
        "predano",
        "pristupnost",
        "evidencni_cislo",
        "presna_datace",
        "pocet",
        "poznamka",
        "okolnosti",
        "hloubka",
        "okres",
        "kraj",
    )

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = SamostatnyNalez
        fields = (
            "nahled",
            "ident_cely",
            "stav",
            "lokalizace",
            "katastr",
            "okres",
            "kraj",
            "obdobi",
            "druh_nalezu",
            "specifikace",
            "nalezce",
            "datum_nalezu",
            "evidencni_cislo",
            "predano",
            "predano_organizace",
            "pristupnost",
            "presna_datace",
            "pocet",
            "poznamka",
            "okolnosti",
            "hloubka",
        )
        sequence = (
            "nahled",
            "ident_cely",
            "igsn",
            "stav",
            "predano",
            "pristupnost",
            "evidencni_cislo",
            "katastr",
            "okres",
            "kraj",
            "lokalizace",
            "datum_nalezu",
            "nalezce",
            "predano_organizace",
            "obdobi",
            "presna_datace",
            "druh_nalezu",
            "specifikace",
            "pocet",
            "poznamka",
            "okolnosti",
            "hloubka",
        )

    def render_nahled(self, value, record):
        """
        Metoda pro správně zobrazení náhledu souboru.

        :param value: Parametr ``value`` slouží jako vstup pro logiku funkce ``render_nahled``.
        :param record: Parametr ``record`` předává se do volání ``reverse()``, pracuje se s atributy ``nahled_soubor``, ``ident_cely``.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``format_html()``, str.
        """
        soubor = record.nahled_soubor
        if soubor is not None:
            soubor: Soubor
            thumbnail_url = reverse(
                "core:download_thumbnail",
                args=(
                    "pas",
                    record.ident_cely,
                    soubor.id,
                ),
            )
            thumbnail_large_url = reverse(
                "core:download_thumbnail_large",
                args=(
                    "pas",
                    record.ident_cely,
                    soubor.id,
                ),
            )
            return format_html(
                '<img src="{}" class="image-nahled" data-bs-toggle="modal" data-bs-target="#soubor-modal" '
                'loading="lazy" data-fullsrc="{}" style="opacity:0" onload="this.style.opacity=100">',
                thumbnail_url,
                thumbnail_large_url,
            )
        return ""

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super(SamostatnyNalezTable, self).__init__(*args, **kwargs)


class AktivaceDeaktivaceColumn(tables.TemplateColumn):
    """Implementuje komponentu ``AktivaceDeaktivaceColumn`` v rámci aplikace."""

    def render(self, record, table, value, bound_column, **kwargs):
        """
        Vyrenderuje hodnotu. v aplikaci.

        :param record: Parametr ``record`` předává se do volání ``check_permissions()``, ``render()``, pracuje se s atributy ``aktivni``, ``id``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param table: Parametr ``table`` předává se do volání ``hasattr()``, ``check_permissions()``, pracuje se s atributy ``request``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param value: Parametr ``value`` předává se do volání ``render()``, vstupuje do návratové hodnoty.
        :param bound_column: Parametr ``bound_column`` se předává do volání ``render()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``render()``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: str, výsledek volání ``render()``, výsledek volání ``format_html()``.
        """
        if not hasattr(table, "request"):
            return ""
        if record.aktivni:
            perm_check = check_permissions(p.actionChoices.spoluprace_deaktivovat, table.request.user, record.id)
        else:
            perm_check = check_permissions(p.actionChoices.spoluprace_aktivovat, table.request.user, record.id)
        if perm_check:
            return super().render(record, table, value, bound_column, **kwargs)
        else:
            return format_html("")


class smazatColumn(tables.TemplateColumn):
    """Implementuje komponentu ``smazatColumn`` v rámci aplikace."""

    def render(self, record, table, value, bound_column, **kwargs):
        """
        Vyrenderuje hodnotu. v aplikaci.

        :param record: Parametr ``record`` předává se do volání ``check_permissions()``, ``render()``, pracuje se s atributy ``id``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param table: Parametr ``table`` předává se do volání ``hasattr()``, ``check_permissions()``, pracuje se s atributy ``request``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param value: Parametr ``value`` předává se do volání ``render()``, vstupuje do návratové hodnoty.
        :param bound_column: Parametr ``bound_column`` se předává do volání ``render()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``render()``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: str, výsledek volání ``render()``, výsledek volání ``format_html()``.
        """
        if not hasattr(table, "request"):
            return ""
        if check_permissions(p.actionChoices.spoluprace_smazat, table.request.user, record.id):
            return super().render(record, table, value, bound_column, **kwargs)
        else:
            return format_html("")


class EditProjektyColumn(tables.TemplateColumn):
    """Implementuje komponentu ``EditProjektyColumn`` pro editaci projektů spolupráce."""

    def render(self, record, table, value, bound_column, **kwargs):
        """
        Vyrenderuje hodnotu v aplikaci.

        :param record: Parametr ``record`` předává se do volání ``check_permissions()``, ``render()``, pracuje se s atributy ``id``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param table: Parametr ``table`` předává se do volání ``hasattr()``, ``check_permissions()``, pracuje se s atributy ``request``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param value: Parametr ``value`` předává se do volání ``render()``, vstupuje do návratové hodnoty.
        :param bound_column: Parametr ``bound_column`` se předává do volání ``render()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``render()``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: str, výsledek volání ``render()``, výsledek volání ``format_html()``.
        """
        if not hasattr(table, "request"):
            return ""
        if check_permissions(p.actionChoices.spoluprace_edit_projekty, table.request.user, record.id):
            return super().render(record, table, value, bound_column, **kwargs)
        return ""


class UzivatelSpolupraceTable(SearchTable):
    """Definuje tabulku uživatelských spoluprací pro přehled i export."""

    stav = tables.Column(verbose_name="Stav", default="")
    vedouci = tables.Column(
        accessor="vedouci__name_and_id",
        verbose_name=_("pas.tables.spolupraceTable.vedouci.label"),
        order_by=("vedouci__last_name", "vedouci__first_name", "vedouci__ident_cely"),
        default="",
    )
    organizace_vedouci = tables.Column(
        accessor=("vedouci__organizace"),
        verbose_name=_("pas.tables.spolupraceTable.organizace_vedouci.label"),
        default="",
        order_by="vedouci__organizace__nazev_zkraceny",
    )
    spolupracovnik = tables.Column(
        accessor="spolupracovnik__name_and_id",
        verbose_name=_("pas.tables.spolupraceTable.spolupracovnik.label"),
        order_by=("spolupracovnik__last_name", "spolupracovnik__first_name", "spolupracovnik__ident_cely"),
        default="",
    )
    organizace_spolupracovnik = tables.Column(
        accessor=("spolupracovnik__organizace"),
        verbose_name=_("pas.tables.spolupraceTable.organizace_spolupracovnik.label"),
        default="",
        order_by="spolupracovnik__organizace__nazev_zkraceny",
    )

    historie = tables.LinkColumn(
        "historie:spoluprace",
        text=_("pas.tables.spolupraceTable.historie.cell"),
        args=[A("pk")],
        attrs={"th": {"style": "color:white"}},
        orderable=False,
        verbose_name=_("pas.tables.spolupraceTable.historie.label"),
    )
    projekty = tables.Column(
        verbose_name=_("pas.tables.spolupraceTable.projekty.label"),
        orderable=False,
        default="",
        attrs={"th": {"style": "color:white"}, "td": {"data-no-tooltip": "true"}},
        exclude_from_export=True,
    )
    aktivace = AktivaceDeaktivaceColumn(
        attrs={
            "th": {"class": "orderable ", "style": "color:#fff"},
        },
        template_name="pas/aktivace_deaktivace_cell.html",
        orderable=False,
        verbose_name=_("pas.tables.spolupraceTable.aktivace.label"),
    )
    edit_projekty = EditProjektyColumn(
        attrs={
            "th": {"class": "orderable ", "style": "color:#fff"},
            "td": {"data-no-tooltip": "true"},
        },
        template_name="pas/edit_projekty_cell.html",
        exclude_from_export=True,
        orderable=False,
        verbose_name=_("pas.tables.spolupraceTable.editProjeky.label"),
    )
    smazani = smazatColumn(
        attrs={
            "th": {"class": "orderable ", "style": "color:#fff"},
        },
        template_name="pas/smazat_cell.html",
        exclude_from_export=True,
        orderable=False,
        verbose_name=_("pas.tables.spolupraceTable.smazani.label"),
    )
    app = "spoluprace"

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = UzivatelSpoluprace
        fields = (
            "stav",
            "vedouci",
            "organizace_vedouci",
            "spolupracovnik",
            "organizace_spolupracovnik",
            "projekty",
        )
        sequence = (
            "stav",
            "vedouci",
            "organizace_vedouci",
            "spolupracovnik",
            "organizace_spolupracovnik",
            "projekty",
            "historie",
            "aktivace",
            "edit_projekty",
            "smazani",
        )

    def __init__(self, *args, user=None, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param user: Přihlášený uživatel; pro roli Badatel se sloupec ``edit_projekty`` z tabulky odstraní.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        if user is not None and user.is_authenticated and user.hlavni_role.pk == ROLE_BADATEL_ID:
            kwargs["exclude"] = (*kwargs.get("exclude", ()), "edit_projekty")
        super(UzivatelSpolupraceTable, self).__init__(*args, **kwargs)

    def render_projekty(self, value, record):
        """
        Vyrenderuje seznam projektů přiřazených ke spolupráci jako klikatelné odkazy.

        :param value: Parametr ``value`` slouží jako vstup pro logiku funkce ``render_projekty``.
        :param record: Parametr ``record`` předává se do volání ``record.projekty.all()``.

            :return: Vrací výsledek volání ``format_html()``.
        """
        projekt_list = record.projekty.all()
        if not projekt_list:
            return format_html('<span class="text-muted">&mdash;</span>')
        tooltip = ", ".join(proj.ident_cely for proj in projekt_list)
        links = [
            format_html('<a href="{}">{}</a>', reverse("projekt:detail", args=[proj.ident_cely]), proj.ident_cely)
            for proj in projekt_list
        ]
        return format_html(
            '<div rel="tooltip" title="{}" style="overflow:hidden;white-space:nowrap;text-overflow:ellipsis">{}</div>',
            tooltip,
            mark_safe(", ".join(str(link) for link in links)),
        )

    def get_all_idents(self):
        """
        Vrátí prázdnu hodnotu. Metoda je zde kvůli kompatibilitě s ostatními tabulkami.

        :return: Vrací str.
        """
        return ""
