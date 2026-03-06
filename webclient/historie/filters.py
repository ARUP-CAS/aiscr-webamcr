import django_filters
from uzivatel.models import Organizace


class HistorieOrganizaceMultipleChoiceFilter(django_filters.ModelMultipleChoiceFilter):
    """Implementuje komponentu ``HistorieOrganizaceMultipleChoiceFilter`` v rámci aplikace."""

    def get_queryset(self, request):
        """
        Vrací queryset. v aplikaci.

        :param request: Django HTTP požadavek použitý při zpracování.
        """
        return Organizace.objects.all()

    def filter(self, qs, value):
        """
        Filtruje hodnotu. v aplikaci.

        :param qs: Vstupní queryset, který má být dále zpracován.
        :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
        """
        return qs
