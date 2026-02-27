import django_filters
from uzivatel.models import Organizace


class HistorieOrganizaceMultipleChoiceFilter(django_filters.ModelMultipleChoiceFilter):
    """Zapouzdřuje chování třídy ``HistorieOrganizaceMultipleChoiceFilter`` pro modul ``webclient.historie.filters``."""
    def get_queryset(self, request):
        """Zpracuje volání ``HistorieOrganizaceMultipleChoiceFilter.get_queryset`` v rámci modulu ``webclient.historie.filters``."""
        return Organizace.objects.all()

    def filter(self, qs, value):
        """Provádí funkci ``HistorieOrganizaceMultipleChoiceFilter.filter`` v rámci modulu ``webclient.historie.filters``."""
        return qs
