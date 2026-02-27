from django.contrib import admin


class ProjektAdmin(admin.ModelAdmin):
    """Třída `ProjektAdmin` v modulu `webclient.projekt.admin`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    list_display = (
        "ident_cely",
        "typ_projektu",
        "stav",
        "lokalizace",
        "parcelni_cislo",
        "podnet",
        "uzivatelske_oznaceni",
        "oznamovatel",
        "planovane_zahajeni",
        "soubory",
        "historie",
    )
