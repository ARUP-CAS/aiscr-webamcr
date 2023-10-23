import logging
from django.urls import reverse

import django_tables2 as tables
from django.utils.translation import gettext as _
from django.utils.html import conditional_escape, mark_safe
from django.utils.encoding import force_str
from django.utils.html import format_html

from uzivatel.models import Osoba
from core.utils import SearchTable
from django.db.models import OuterRef, Subquery

from .models import Dokument

logger = logging.getLogger(__name__)


class AutorColumn(tables.Column):
    """
    Class pro definování sloupce autor a toho jak se zobrazuje aby bylo dodrženo pořadí.
    """

    def render(self, record, value):
        osoby = record.ordered_autors
        items = []
        for autor in osoby:
            content = conditional_escape(force_str(autor))
            items.append(content)

        return mark_safe(conditional_escape("; ").join(items))

    def order(self, queryset, is_descending):
        osoby = (
            Osoba.objects.filter(dokumentautor__dokument=OuterRef("pk"))
            .order_by("dokumentautor__poradi")
            .values("vypis_cely")
        )
        queryset = queryset.annotate(main=Subquery(osoby[:1])).order_by(
            ("-" if is_descending else "") + "main"
        )
        return queryset, True


class OsobyColumn(tables.Column):
    """
    Class pro definování sloupce autor a toho jak se zobrazuje aby bylo dodrženo pořadí.
    """

    def render(self, record, value):
        osoby = record.osoby.all()
        items = []
        for autor in osoby:
            content = conditional_escape(force_str(autor))
            items.append(content)

        return mark_safe(conditional_escape("; ").join(items))

    def order(self, queryset, is_descending):
        osoby = (
            Osoba.objects.filter(dokumentosoba__dokument=OuterRef("pk"))
            .values("vypis_cely")
        )
        queryset = queryset.annotate(main=Subquery(osoby[:1])).order_by(
            ("-" if is_descending else "") + "main"
        )
        return queryset, True


class Model3DTable(SearchTable):
    """
    Class pro definování tabulky pro modelu 3D použitých pro zobrazení přehledu modelu 3D a exportu.
    """
    ident_cely = tables.Column(linkify=True)
    typ_dokumentu = tables.columns.Column(default="")
    organizace__nazev_zkraceny = tables.columns.Column(default="")
    popis = tables.columns.Column(default="")
    rok_vzniku = tables.columns.Column(default="")
    extra_data__format = tables.columns.Column(default="")
    extra_data__odkaz = tables.columns.Column(default="")
    extra_data__duveryhodnost = tables.columns.Column(default="")
    autori = AutorColumn()
    app = "knihovna_3d"
    first_columns = None
    nahled = tables.columns.Column(
        default="",
        accessor="soubory",
        attrs={
            "th": {"class": "white"},
        },
        orderable=False,
        verbose_name=_("dokument.tables.dokumentTable.soubory.label"),
    )

    class Meta:
        model = Dokument
        fields = (
            "ident_cely",
            "stav",
            "typ_dokumentu",
            "organizace__nazev_zkraceny",
            "popis",
            "rok_vzniku",
            "extra_data__format",
            "extra_data__odkaz",
            "extra_data__duveryhodnost",
        )
        sequence = (
            "nahled",
            "ident_cely",
            "stav",
            "typ_dokumentu",
            "autori",
            "organizace__nazev_zkraceny",
            "rok_vzniku",
            "popis",
            "extra_data__format",
            "extra_data__odkaz",
            "extra_data__duveryhodnost"
        )

    def __init__(self, *args, **kwargs):
        super(Model3DTable, self).__init__(*args, **kwargs)

    def render_nahled(self, value, record):
        """
        Metóda pro správne zobrazení náhledu souboru.
        """
        if len(record.soubory.soubory.all()) > 0:
            soubor = record.soubory.soubory.first()
        else:
            soubor = None
        if soubor is not None:
            soubor_url = reverse("core:download_thumbnail", args=(soubor.id,))
            return format_html(
                '<img src="{}" class="image-nahled" data-toggle="modal" data-target="#soubor-modal">',
                soubor_url,
            )
        return ""


class DokumentTable(SearchTable):
    """
    Class pro definování tabulky pro dokumenty použitých pro zobrazení přehledu dokumentů a exportu.
    """
    ident_cely = tables.Column(linkify=True)
    typ_dokumentu = tables.columns.Column(default="")
    organizace__nazev_zkraceny = tables.columns.Column(
        default="", verbose_name=_("dokument.tables.dokumentTable.organizace.label")
    )
    popis = tables.columns.Column(default="")
    rok_vzniku = tables.columns.Column(default="")
    autori = AutorColumn()
    osoby = OsobyColumn()
    popis = tables.columns.Column(default="")
    pristupnost = tables.columns.Column(default="")
    rada = tables.columns.Column(default="")
    let = tables.columns.Column(default="")
    material_originalu = tables.columns.Column(default="")
    poznamka = tables.columns.Column(default="")
    ulozeni_originalu = tables.columns.Column(default="")
    oznamceni_originalu = tables.columns.Column(default="")
    datum_zverejneni = tables.columns.Column(default="")
    licence = tables.columns.Column(default="")
    nahled = tables.columns.Column(
        default="",
        accessor="soubory",
        attrs={
            "th": {"class": "white"},
        },
        orderable=False,
        verbose_name=_("dokument.tables.dokumentTable.soubory.label"),
    )
    columns_to_hide = (
        "pristupnost",
        "datum_zverejneni",
        "oznamceni_originalu",
        "extra_data__datum_vzniku",
        "poznamka",
        "extra_data__cislo_objektu",
        "rada",

        "material_originalu",
        "extra_data__format",
        "ulozeni_originalu",
        "licence",
        "let",
        "extra_data__zachovalost",
        "extra_data__nahrada",
        "extra_data__pocet_variant_originalu",
        "extra_data__meritko",
        "extra_data__vyska",
        "extra_data__sirka",
        "extra_data__zeme",
        "extra_data__region",
        "extra_data__udalost_typ",
        "extra_data__udalost",
        "extra_data__rok_od",
        "extra_data__rok_do",
        "osoby",
        "extra_data__odkaz",
        "extra_data__duveryhodnost",
    )
    app = "dokument"
    first_columns = None

    def render_nahled(self, value, record):
        """
        Metóda pro správne zobrazení náhledu souboru.
        """
        if len(record.soubory.first_soubor)>0:
            soubor = record.soubory.first_soubor[0]
        else: 
            soubor = None
        if soubor is not None:
            soubor_url = reverse("core:download_thumbnail", args=(soubor.id,))
            return format_html(
                '<img src="{}" class="image-nahled" data-toggle="modal" data-target="#soubor-modal">',
                soubor_url,
            )
        return ""

    class Meta:
        model = Dokument
        fields = (
            "nahled",
            "ident_cely",
            "stav",
            "organizace__nazev_zkraceny",
            "autori",
            "rok_vzniku",
            "typ_dokumentu",
            "popis",
            "pristupnost",
            "rada",
            "let",
            "material_originalu",
            "poznamka",
            "ulozeni_originalu",
            "oznaceni_originalu",
            "datum_zverejneni",
            "licence",
            "extra_data__format",
            "extra_data__datum_vzniku",
            "extra_data__cislo_objektu",
            "extra_data__zachovalost",
            "extra_data__nahrada",
            "extra_data__pocet_variant_originalu",
            "extra_data__meritko",
            "extra_data__vyska",
            "extra_data__sirka",
            "extra_data__zeme",
            "extra_data__region",
            "extra_data__udalost_typ",
            "extra_data__udalost",
            "extra_data__rok_od",
            "extra_data__rok_do",
            "extra_data__odkaz",
            "extra_data__duveryhodnost",
        )
        sequence = (
            "nahled",
            "ident_cely",
            "stav",
            "pristupnost",
            "datum_zverejneni",
            "oznaceni_originalu",
            "autori",
            "organizace__nazev_zkraceny",
            "rok_vzniku",
            "extra_data__datum_vzniku",
            "popis",
            "poznamka",
            "extra_data__cislo_objektu",
            "rada",
            "typ_dokumentu",
            "material_originalu",
            "extra_data__format",
            "ulozeni_originalu",
            "licence",
            "let",
            "extra_data__zachovalost",
            "extra_data__nahrada",
            "extra_data__pocet_variant_originalu",
            "extra_data__meritko",
            "extra_data__vyska",
            "extra_data__sirka",
            "extra_data__zeme",
            "extra_data__region",
            "extra_data__udalost_typ",
            "extra_data__udalost",
            "extra_data__rok_od",
            "extra_data__rok_do",
            "osoby",
            "extra_data__odkaz",
            "extra_data__duveryhodnost",
        )

    def __init__(self, *args, **kwargs):
        super(DokumentTable, self).__init__(*args, **kwargs)
