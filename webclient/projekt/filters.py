import django_filters as filters
from projekt.models import Projekt


class ProjektFilter(filters.FilterSet):
    class Meta:
        model = Projekt
        fields = {
            "ident_cely": ["icontains"],
            # "typ_projektu": [""],
            # "stav": [""],
            # "organizace": [""],
            # "vedouci_projektu": [""],
            # "kulturni_pamatka": [""],
            # "planovane_zahajeni",
            # "hlavni_katastr": [""],
        }
