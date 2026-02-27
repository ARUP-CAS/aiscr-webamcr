from django.contrib import admin


class HistorieAdmin(admin.ModelAdmin):
    """Zapouzdřuje chování třídy ``HistorieAdmin`` pro modul ``webclient.historie.admin``."""
    list_display = ("uzivatel", "datum_zmeny", "typ_zmeny", "poznamka", "vazba")
