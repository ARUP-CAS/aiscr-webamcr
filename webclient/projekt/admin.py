from django.contrib import admin


class ProjektAdmin(admin.ModelAdmin):
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
