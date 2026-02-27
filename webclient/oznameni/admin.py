from django.contrib import admin


class OznamovatelAdmin(admin.ModelAdmin):
    """Třída `OznamovatelAdmin` v modulu `webclient.oznameni.admin`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    list_display = ("email", "adresa", "odpovedna_osoba", "oznamovatel", "telefon")
