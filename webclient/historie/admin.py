from django.contrib import admin


class HistorieAdmin(admin.ModelAdmin):
    """Třída `HistorieAdmin` v modulu `webclient.historie.admin`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    list_display = ("uzivatel", "datum_zmeny", "typ_zmeny", "poznamka", "vazba")
