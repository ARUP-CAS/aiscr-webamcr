from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django_tables2 import SingleTableMixin
from historie.models import Historie
from historie.tables import HistorieTable
from projekt.models import Projekt
from arch_z.models import ArcheologickyZaznam
from dokument.models import Dokument
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from django.shortcuts import get_object_or_404
from core.models import over_opravneni_with_exception


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

    def get(self, request, ident_cely, *args, **kwargs):
        zaznam = get_object_or_404(Projekt, ident_cely=ident_cely)
        over_opravneni_with_exception(zaznam, request)
        super().get(request, *args, **kwargs)


class AkceHistorieListView(HistorieListView):
    def get_queryset(self):
        akce_ident = self.kwargs["ident_cely"]
        return self.model.objects.filter(
            vazba__archeologickyzaznam__ident_cely=akce_ident
        ).order_by("-datum_zmeny")

    def get(self, request, ident_cely, *args, **kwargs):
        zaznam = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
        over_opravneni_with_exception(zaznam, request)
        super().get(request, *args, **kwargs)


class DokumentHistorieListView(HistorieListView):
    def get_queryset(self):
        dokument_ident = self.kwargs["ident_cely"]
        return self.model.objects.filter(
            vazba__dokument_historie__ident_cely=dokument_ident
        ).order_by("-datum_zmeny")

    def get(self, request, ident_cely, *args, **kwargs):
        zaznam = get_object_or_404(Dokument, ident_cely=ident_cely)
        over_opravneni_with_exception(zaznam, request)
        super().get(request, *args, **kwargs)


class SamostatnyNalezHistorieListView(HistorieListView):
    def get_queryset(self):
        sn_ident = self.kwargs["ident_cely"]
        return self.model.objects.filter(
            vazba__sn_historie__ident_cely=sn_ident
        ).order_by("-datum_zmeny")

    def get(self, request, ident_cely, *args, **kwargs):
        zaznam = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
        over_opravneni_with_exception(zaznam, request)
        super().get(request, *args, **kwargs)


class SpolupraceHistorieListView(HistorieListView):
    def get_queryset(self):
        spoluprace_ident = self.kwargs["pk"]
        return self.model.objects.filter(
            vazba__spoluprace_historie__pk=spoluprace_ident
        ).order_by("-datum_zmeny")

    def get(self, request, pk, *args, **kwargs):
        zaznam = get_object_or_404(UzivatelSpoluprace, ident_cely=pk)
        over_opravneni_with_exception(zaznam, request)
        super().get(request, *args, **kwargs)
