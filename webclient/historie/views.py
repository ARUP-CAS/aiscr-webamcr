from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django_tables2 import SingleTableMixin
from historie.models import Historie
from historie.tables import HistorieTable


class HistorieListView(LoginRequiredMixin, SingleTableMixin, ListView):
    table_class = HistorieTable
    model = Historie
    template_name = "historie/historie_list.html"


class ProjektHistorieListView(HistorieListView):
    def get_queryset(self):
        projekt_ident = self.kwargs["ident_cely"]
        return self.model.objects.filter(
            vazba__projekt_historie__ident_cely=projekt_ident
        ).order_by("-datum_zmeny")


class AkceHistorieListView(HistorieListView):
    def get_queryset(self):
        akce_ident = self.kwargs["ident_cely"]
        return self.model.objects.filter(
            vazba__archeologickyzaznam__ident_cely=akce_ident
        ).order_by("-datum_zmeny")


class DokumentHistorieListView(HistorieListView):
    def get_queryset(self):
        dokument_ident = self.kwargs["ident_cely"]
        return self.model.objects.filter(
            vazba__dokument_historie__ident_cely=dokument_ident
        ).order_by("-datum_zmeny")


class SamostatnyNalezHistorieListView(HistorieListView):
    def get_queryset(self):
        sn_ident = self.kwargs["ident_cely"]
        return self.model.objects.filter(
            vazba__sn_historie__ident_cely=sn_ident
        ).order_by("-datum_zmeny")
