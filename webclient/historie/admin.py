from django.contrib import admin
from historie.models import Historie, HistorieVazby


class HistorieAdmin(admin.ModelAdmin):
    list_display = ("uzivatel", "datum_zmeny", "typ_zmeny", "poznamka", "vazba")


admin.site.register(Historie, HistorieAdmin)
admin.site.register(HistorieVazby)
