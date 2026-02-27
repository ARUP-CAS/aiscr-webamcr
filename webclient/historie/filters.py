import django_filters
from uzivatel.models import Organizace


class HistorieOrganizaceMultipleChoiceFilter(django_filters.ModelMultipleChoiceFilter):
    """Zapouzdřuje chování třídy ``HistorieOrganizaceMultipleChoiceFilter`` pro modul ``webclient.historie.filters``."""
    def get_queryset(self, request):
        """Zajišťuje logiku funkce ``get_queryset``.
        
        :param request: HTTP požadavek zpracovávaný view funkcí nebo metodou.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return Organizace.objects.all()

    def filter(self, qs, value):
        """Zajišťuje logiku funkce ``filter``.
        
        :param qs: Vstupní hodnota parametru ``qs`` použitého při zpracování.
        :param value: Vstupní hodnota parametru ``value`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return qs
