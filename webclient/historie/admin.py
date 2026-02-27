from django.contrib import admin


class HistorieAdmin(admin.ModelAdmin):
    """Implementuje komponentu ``HistorieAdmin`` v rámci aplikace."""
    list_display = ("uzivatel", "datum_zmeny", "typ_zmeny", "poznamka", "vazba")
