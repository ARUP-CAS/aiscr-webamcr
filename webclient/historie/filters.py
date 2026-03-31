import django_filters
from uzivatel.models import Organizace


class HistorieOrganizaceMultipleChoiceFilter(django_filters.ModelMultipleChoiceFilter):
    """Implementuje komponentu ``HistorieOrganizaceMultipleChoiceFilter`` v rámci aplikace."""

    def get_queryset(self, request):
        """
        Vrací queryset. v aplikaci.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_queryset``.

            :return: Vrací výsledek volání ``all()``.
        """
        return Organizace.objects.all()

    def filter(self, qs, value):
        """
        Filtruje hodnotu. v aplikaci.

        :param qs: Parametr ``qs`` vstupuje do návratové hodnoty.
        :param value: Parametr ``value`` slouží jako vstup pro logiku funkce ``filter``.

            :return: Vrací proměnná ``qs``.
        """
        return qs
