from django.contrib import admin


class HistorieAdmin(admin.ModelAdmin):
    list_display = ("uzivatel", "datum_zmeny", "typ_zmeny", "poznamka", "vazba")
