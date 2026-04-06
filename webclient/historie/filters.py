import django_filters
from uzivatel.models import Organizace


class HistorieOrganizaceMultipleChoiceFilter(django_filters.ModelMultipleChoiceFilter):
    """Implementuje komponentu ``HistorieOrganizaceMultipleChoiceFilter`` v rámci aplikace."""

    def get_queryset(self, request):
        """
        Vrací queryset. v aplikaci.

        :param request: HTTP požadavek.

        :return: Výsledek volání ``all()``.
        """
        return Organizace.objects.all()

    def filter(self, qs, value):
        """
        Filtruje hodnotu. v aplikaci.

        :param qs: Queryset, který má být filtrován.
        :param value: Vybrané hodnoty filtru (v této implementaci se queryset vrací beze změny).

        :return: Proměnná ``qs``.
        """
        return qs
