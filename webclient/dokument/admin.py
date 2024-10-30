from django.contrib import admin
from dokument.models import Let
from heslar.admin import ObjectWithMetadataAdmin


class DokumentWithMetadataAdmin(ObjectWithMetadataAdmin):
    pass


@admin.register(Let)
class LetAdmin(DokumentWithMetadataAdmin):
    """
    Admin část pro správu modelu Let.
    """

    list_display = (
        "ident_cely",
        "datum",
        "letiste_start",
        "letiste_cil",
        "organizace",
        "pilot",
        "pozorovatel",
        "uzivatelske_oznaceni",
    )
    list_filter = ("letiste_start", "letiste_cil", "organizace")
    fields = (
        "ident_cely",
        "uzivatelske_oznaceni",
        "datum",
        "pilot",
        "pozorovatel",
        "ucel_letu",
        "typ_letounu",
        "letiste_start",
        "letiste_cil",
        "hodina_zacatek",
        "hodina_konec",
        "pocasi",
        "dohlednost",
        "fotoaparat",
        "organizace",
    )
    search_fields = ("ident_cely", "uzivatelske_oznaceni")
