from django.contrib import admin


class OznamovatelAdmin(admin.ModelAdmin):
    list_display = ("email", "adresa", "odpovedna_osoba", "oznamovatel", "telefon")
