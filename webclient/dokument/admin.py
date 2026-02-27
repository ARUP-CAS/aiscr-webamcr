from django.contrib import admin
from dokument.models import Let
from heslar.admin import ObjectWithMetadataAdmin


class DokumentWithMetadataAdmin(ObjectWithMetadataAdmin):
    """Třída `DokumentWithMetadataAdmin` v modulu `webclient.dokument.admin`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
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

    def get_readonly_fields(self, request, obj=None):
        """Funkce `LetAdmin.get_readonly_fields` v modulu `webclient.dokument.admin`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :param obj: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if obj:  # editace existujícího objektu
            return self.readonly_fields + ("ident_cely",)
        return self.readonly_fields
