import django_filters
from uzivatel.models import Organizace


class HistorieOrganizaceMultipleChoiceFilter(django_filters.ModelMultipleChoiceFilter):
    """Třída `HistorieOrganizaceMultipleChoiceFilter` v modulu `webclient.historie.filters`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_queryset(self, request):
        """Funkce `HistorieOrganizaceMultipleChoiceFilter.get_queryset` v modulu `webclient.historie.filters`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return Organizace.objects.all()

    def filter(self, qs, value):
        """Funkce `HistorieOrganizaceMultipleChoiceFilter.filter` v modulu `webclient.historie.filters`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param qs: Vstupní hodnota používaná při zpracování.
        :param value: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return qs
