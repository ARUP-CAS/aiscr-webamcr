import logging
from django.urls import reverse

import django_tables2 as tables
from django.utils.translation import gettext as _
from django.utils.html import conditional_escape, mark_safe
from django.utils.encoding import force_str
from django.utils.html import format_html

from uzivatel.models import Osoba
from core.utils import SearchTable

from .models import Dokument

logger = logging.getLogger('python-logstash-logger')


class Model3DTable(SearchTable):

    ident_cely = tables.Column(linkify=True)
    typ_dokumentu = tables.columns.Column(default="")
    organizace__nazev_zkraceny = tables.columns.Column(default="")
    popis = tables.columns.Column(default="")
    rok_vzniku = tables.columns.Column(default="")
    extra_data__format = tables.columns.Column(default="")
    extra_data__odkaz = tables.columns.Column(default="")
    extra_data__duveryhodnost = tables.columns.Column(default="")
    app = "knihovna_3d"
    first_columns = None

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


class DokumentTable(SearchTable):

    ident_cely = tables.Column(linkify=True)
    typ_dokumentu = tables.columns.Column(default="")
    organizace__nazev_zkraceny = tables.columns.Column(
        default="", verbose_name=_("Organizace")
    )
    popis = tables.columns.Column(default="")
    rok_vzniku = tables.columns.Column(default="")
    autori = AutorColumn(order_by="hlavni_autor")
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
        accessor="soubory__soubory",
        attrs={
            "th": {"class": "white"},
        },
        orderable=False,
        verbose_name=_("dokument.list.soubory.label"),
    )
    columns_to_hide = (
        "rada",
        "let",
        "material_originalu",
        "poznamka",
        "ulozeni_originalu",
        "oznamceni_originalu",
        "datum_zverejneni",
        "licence",
    )
    app = "dokument"
    first_columns = None

    def render_nahled(self, value, record):
        soubor = record.soubory.soubory.filter(mimetype__startswith="image").first()
        if soubor is not None:
            soubor_url = reverse("core:download_file", args=(soubor.id,))
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
            "oznamceni_originalu",
            "datum_zverejneni",
            "licence",
        )

    def __init__(self, *args, **kwargs):
        super(DokumentTable, self).__init__(*args, **kwargs)
