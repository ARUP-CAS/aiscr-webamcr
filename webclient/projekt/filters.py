import django_filters
from projekt.models import Projekt


class ProjektFilter(django_filters.FilterSet):
    class Meta:
        model = Projekt
        fields = ("ident_cely",)
