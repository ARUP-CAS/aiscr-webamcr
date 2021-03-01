import django_filters as filters
from django_filters import MultipleChoiceFilter
from projekt.models import Projekt


class ProjektFilter(filters.FilterSet):

    stav = MultipleChoiceFilter(choices=Projekt.CHOICES)

    class Meta:
        model = Projekt
        fields = {
            "ident_cely": ["icontains"],
            "typ_projektu": ["exact"],
            "organizace": ["exact"],
            # "vedouci_projektu": [""],
            # "kulturni_pamatka": [""],
            # "planovane_zahajeni",
            # "hlavni_katastr": [""],
        }
