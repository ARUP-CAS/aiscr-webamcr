import logging
from django.urls import reverse

import django_tables2 as tables
from django_tables2_column_shifter.tables import ColumnShiftTableBootstrap4
from django.utils.translation import gettext as _
from django.utils.html import conditional_escape, mark_safe
from django.utils.encoding import force_str
from django.utils.html import format_html

from uzivatel.models import Osoba

from .models import Dokument

logger = logging.getLogger(__name__)


class Model3DTable(ColumnShiftTableBootstrap4):

    ident_cely = tables.Column(linkify=True)
    typ_dokumentu = tables.columns.Column(default="")
    organizace__nazev_zkraceny = tables.columns.Column(default="")
    popis = tables.columns.Column(default="")
    rok_vzniku = tables.columns.Column(default="")
    extra_data__format = tables.columns.Column(default="")
    extra_data__odkaz = tables.columns.Column(default="")
    extra_data__duveryhodnost = tables.columns.Column(default="")

    def get_column_default_show(self):
        self.column_default_show = list(self.columns.columns.keys())
        if "projekt_vychozi_skryte_sloupce" in self.request.session:
            columns_to_hide = set(
                self.request.session["projekt_vychozi_skryte_sloupce"]
            )
            for column in columns_to_hide:
                if column is not None and column in self.column_default_show:
                    self.column_default_show.remove(column)
        return super(Model3DTable, self).get_column_default_show()

    class Meta:
        model = Dokument
        # template_name = "projekt/bootstrap4.html"
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

    def __init__(self, *args, **kwargs):
        super(Model3DTable, self).__init__(*args, **kwargs)


class AutorColumn(tables.Column):
    def render(self, record, value):
        osoby = Osoba.objects.filter(
            dokumentautor__dokument__ident_cely=record
        ).order_by("dokumentautor__poradi")
        items = []
        for autor in osoby:
            content = conditional_escape(force_str(autor))
            items.append(content)

        return mark_safe(conditional_escape("; ").join(items))

    def order(self, queryset, is_descending):
        queryset = queryset.order_by(("-" if is_descending else "") + "main_autor")
        return (queryset, True)


class DokumentTable(ColumnShiftTableBootstrap4):

    ident_cely = tables.Column(linkify=True)
    typ_dokumentu = tables.columns.Column(default="")
    organizace__nazev_zkraceny = tables.columns.Column(
        default="", verbose_name=_("Organizace")
    )
    popis = tables.columns.Column(default="")
    rok_vzniku = tables.columns.Column(default="")
    autori = AutorColumn()
    popis = tables.columns.Column(default="")
    pristupnost = tables.columns.Column(default="")
    rada = tables.columns.Column(default="")
    let = tables.columns.Column(default="")
    material_original = tables.columns.Column(default="")
    poznamka = tables.columns.Column(default="")
    ulozeni_originalu = tables.columns.Column(default="")
    oznamceni_originalu = tables.columns.Column(default="")
    datum_zverejneni = tables.columns.Column(default="")
    licence = tables.columns.Column(default="")
    nahled = tables.columns.Column(
        default="",
        accessor="soubory__soubory",
        attrs={
            "th": {"class": "white"},
            # "td": {"class": "no-tooltip"},
        },
        orderable=False,
        verbose_name=_("dokument.list.soubory.label"),
    )

    def render_nahled(self, value, record):
        soubor = record.soubory.soubory.filter(mimetype__startswith="image").first()
        if soubor is not None:
            soubor_url = reverse("core:download_file", args=(soubor.id,))
            return format_html(
                '<img src="{}" class="image-nahled" >',
                soubor_url,
            )
        return ""

    def get_column_default_show(self):
        self.column_default_show = list(self.columns.columns.keys())
        if "dokument_vychozi_skryte_sloupce" in self.request.session:
            columns_to_hide = set(
                self.request.session["dokument_vychozi_skryte_sloupce"]
            )
        else:
            columns_to_hide = (
                "rada",
                "let",
                "material_original",
                "poznamka",
                "ulozeni_originalu",
                "oznamceni_originalu",
                "datum_zverejneni",
                "licence",
                "nahled",
            )
        for column in columns_to_hide:
            if column is not None and column in self.column_default_show:
                self.column_default_show.remove(column)
        return super(DokumentTable, self).get_column_default_show()

    class Meta:
        model = Dokument
        # template_name = "projekt/bootstrap4.html"
        fields = (
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
            "material_original",
            "poznamka",
            "ulozeni_originalu",
            "oznamceni_originalu",
            "datum_zverejneni",
            "licence",
            "nahled",
        )

    def __init__(self, *args, **kwargs):
        super(DokumentTable, self).__init__(*args, **kwargs)
