from django.contrib import admin
from dokument.models import Let
from heslar.admin import ObjectWithMetadataAdmin


class DokumentWithMetadataAdmin(ObjectWithMetadataAdmin):
    """Implementuje komponentu ``DokumentWithMetadataAdmin`` v rámci aplikace."""

    pass


@admin.register(Let)
class LetAdmin(DokumentWithMetadataAdmin):
    """Admin část pro správu modelu Let."""

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

    def get_readonly_fields(self, request, obj=None):
        """
        Vrací readonly fields.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_readonly_fields``.
        :param obj: Parametr ``obj`` ovlivňuje větvení podmínek.

            :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, atribut objektu.
        """
        if obj:  # editace existujícího objektu
            return self.readonly_fields + ("ident_cely",)
        return self.readonly_fields
