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

        :param qs: Vstupní hodnota ``qs`` pro danou operaci.
        :param value: Vstupní hodnota ``value`` pro danou operaci.
        """
        return qs
