import django_tables2 as tables

from .models import Projekt


class ProjektTable(tables.Table):

    ident_cely = tables.Column(linkify=True)

    class Meta:
        model = Projekt
        template_name = "django_tables2/bootstrap4.html"
        fields = (
            "ident_cely",
            "stav",
            "hlavni_katastr",
            "podnet",
            "lokalizace",
            "datum_zahajeni",
            "datum_ukonceni",
            "organizace",
            "vedouci_projektu",
            "kulturni_pamatka",
            "typ_projektu",
            "uzivatelske_oznaceni",
        )

    @staticmethod
    def render_datum_zahajeni(value):
        if value:
            return value.strftime("%Y/%m/%d")
        else:
            return "—"

    @staticmethod
    def render_datum_ukonceni(value):
        if value:
            return value.strftime("%Y/%m/%d")
        else:
            return "—"
