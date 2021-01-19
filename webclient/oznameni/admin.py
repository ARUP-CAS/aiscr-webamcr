from django.contrib import admin
from oznameni.models import Oznamovatel


class OznamovatelAdmin(admin.ModelAdmin):
    list_display = ("email", "adresa", "odpovedna_osoba", "oznamovatel", "telefon")


admin.site.register(Oznamovatel, OznamovatelAdmin)
