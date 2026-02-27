from django.contrib import admin


class OznamovatelAdmin(admin.ModelAdmin):
    """Implementuje komponentu ``OznamovatelAdmin`` v rámci aplikace."""

    list_display = ("email", "adresa", "odpovedna_osoba", "oznamovatel", "telefon")
