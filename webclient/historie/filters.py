import django_filters
from uzivatel.models import Organizace


class HistorieOrganizaceMultipleChoiceFilter(django_filters.ModelMultipleChoiceFilter):
    def get_queryset(self, request):
        return Organizace.objects.all()

    def filter(self, qs, value):
        return qs
