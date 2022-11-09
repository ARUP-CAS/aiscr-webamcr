from django.contrib import admin
from heslar.models import Heslar

@admin.register(Heslar)
class HeslarAdmin(admin.ModelAdmin):
    list_display = ("ident_cely", "nazev_heslare")
    readonly_fields = ("ident_cely", "nazev_heslare")
    fields = ("ident_cely", "nazev_heslare", "heslo", "popis", "zkratka", "heslo_en", "popis_en", "zkratka_en", "razeni")

