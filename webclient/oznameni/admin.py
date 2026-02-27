from django.contrib import admin


class OznamovatelAdmin(admin.ModelAdmin):
    """Zapouzdřuje chování třídy ``OznamovatelAdmin`` pro modul ``webclient.oznameni.admin``."""
    list_display = ("email", "adresa", "odpovedna_osoba", "oznamovatel", "telefon")
