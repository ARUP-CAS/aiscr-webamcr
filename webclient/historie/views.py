from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django_tables2 import SingleTableMixin
from historie.models import Historie
from historie.tables import HistorieTable
from core.forms import SouborMetadataForm
from core.models import Soubor

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


class SpolupraceHistorieListView(HistorieListView):
    def get_queryset(self):
        spoluprace_ident = self.kwargs["pk"]
        return self.model.objects.filter(
            vazba__spoluprace_historie__pk=spoluprace_ident
        ).order_by("-datum_zmeny")

class SouborHistorieListView(HistorieListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        soubor_id = self.kwargs["soubor_id"]
        soubor = Soubor.objects.get(pk=soubor_id)
        context["metadata_form"] = SouborMetadataForm(instance=soubor)
        return context

    def get_queryset(self):
        soubor_id = self.kwargs["soubor_id"]
        return self.model.objects.filter(
            vazba__soubor_historie=soubor_id
        ).order_by("-datum_zmeny")
