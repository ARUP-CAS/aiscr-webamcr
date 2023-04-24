import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django_tables2 import SingleTableMixin
from simple_history.models import HistoricalRecords

from historie.models import Historie
from historie.tables import HistorieTable, SimpleHistoryTable
from core.forms import SouborMetadataForm
from core.models import Soubor

from projekt.models import Projekt
from core.views import ExportMixinDate
from uzivatel.models import User

logger = logging.getLogger('python-logstash-logger')


class HistorieListView(ExportMixinDate, LoginRequiredMixin, SingleTableMixin, ListView):
    table_class = HistorieTable
    model = Historie
    template_name = "historie/historie_list.html"
    export_name = "export_historie_"

    def get_context_data(self, typ=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["export_formats"] = ["csv", "json", "xlsx"]
        return context


class ProjektHistorieListView(HistorieListView):
    def get_queryset(self):
        projekt_ident = self.kwargs["ident_cely"]
        return self.model.objects.filter(
            vazba__projekt_historie__ident_cely=projekt_ident
        ).order_by("-datum_zmeny")

    def get_context_data(self, **kwargs):
        context = super(ProjektHistorieListView, self).get_context_data(**kwargs)
        context["typ"] = "projekt"
        context["ident_cely"] = self.kwargs["ident_cely"]
        context["entity"] = context["typ"]
        return context


class AkceHistorieListView(HistorieListView):
    def get_queryset(self):
        akce_ident = self.kwargs["ident_cely"]
        return self.model.objects.filter(
            vazba__archeologickyzaznam__ident_cely=akce_ident
        ).order_by("-datum_zmeny")

    def get_context_data(self, **kwargs):
        context = super(AkceHistorieListView, self).get_context_data(**kwargs)
        context["typ"] = "akce"
        context["ident_cely"] = self.kwargs["ident_cely"]
        context["entity"] = context["typ"]
        return context


class DokumentHistorieListView(HistorieListView):
    def get_queryset(self):
        dokument_ident = self.kwargs["ident_cely"]
        return self.model.objects.filter(
            vazba__dokument_historie__ident_cely=dokument_ident
        ).order_by("-datum_zmeny")

    def get_context_data(self, **kwargs):
        context = super(DokumentHistorieListView, self).get_context_data(**kwargs)
        if "3D" in self.kwargs["ident_cely"]:
            context["typ"] = "knihovna_3d"
        else:
            context["typ"] = "dokument"
        context["ident_cely"] = self.kwargs["ident_cely"]
        context["entity"] = context["typ"]
        return context


class SamostatnyNalezHistorieListView(HistorieListView):
    def get_queryset(self):
        sn_ident = self.kwargs["ident_cely"]
        return self.model.objects.filter(
            vazba__sn_historie__ident_cely=sn_ident
        ).order_by("-datum_zmeny")

    def get_context_data(self, **kwargs):
        context = super(SamostatnyNalezHistorieListView, self).get_context_data(
            **kwargs
        )
        context["typ"] = "samostatny_nalez"
        context["entity"] = context["typ"]
        context["ident_cely"] = self.kwargs["ident_cely"]
        return context


class SpolupraceHistorieListView(HistorieListView):
    def get_queryset(self):
        spoluprace_ident = self.kwargs["pk"]
        return self.model.objects.filter(
            vazba__spoluprace_historie__pk=spoluprace_ident
        ).order_by("-datum_zmeny")

    def get_context_data(self, **kwargs):
        context = super(SpolupraceHistorieListView, self).get_context_data(**kwargs)
        context["typ"] = "spoluprace"
        context["entity"] = "samostatny_nalez"
        return context


class SouborHistorieListView(HistorieListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        soubor_id = self.kwargs["soubor_id"]
        context["typ"] = "soubor"
        context["entity"] = context["typ"]
        soubor = Soubor.objects.get(pk=soubor_id)
        context["metadata_form"] = SouborMetadataForm(instance=soubor)
        try:
            context["projekt"] = soubor.vazba.projekt_souboru
        except Projekt.DoesNotExist:
            context["projekt"] = None
        return context

    def get_queryset(self):
        soubor_id = self.kwargs["soubor_id"]
        return self.model.objects.filter(vazba__soubor_historie=soubor_id).order_by(
            "-datum_zmeny"
        )


class LokalitaHistorieListView(HistorieListView):
    def get_queryset(self):
        lokalita_ident = self.kwargs["ident_cely"]
        return self.model.objects.filter(
            vazba__archeologickyzaznam__ident_cely=lokalita_ident
        ).order_by("-datum_zmeny")

    def get_context_data(self, **kwargs):
        context = super(LokalitaHistorieListView, self).get_context_data(**kwargs)
        context["typ"] = "lokalita"
        context["entity"] = context["typ"]
        context["ident_cely"] = self.kwargs["ident_cely"]
        return context


class UzivatelHistorieListView(HistorieListView):
    def get_queryset(self):
        user_ident = self.kwargs["ident_cely"]
        return self.model.objects.filter(
            vazba__uzivatelhistorievazba__ident_cely=user_ident
        ).order_by("-datum_zmeny")

    def get_context_data(self, **kwargs):
        context = super(UzivatelHistorieListView, self).get_context_data(**kwargs)
        context["typ"] = "uzivatel"
        context["entity"] = context["typ"]
        context["ident_cely"] = self.kwargs["ident_cely"]
        return context


class ExterniZdrojHistorieListView(HistorieListView):
    def get_queryset(self):
        ez_ident = self.kwargs["ident_cely"]
        return self.model.objects.filter(
            vazba__externizdroj__ident_cely=ez_ident
        ).order_by("-datum_zmeny")

    def get_context_data(self, **kwargs):
        context = super(ExterniZdrojHistorieListView, self).get_context_data(**kwargs)
        context["typ"] = "ext_zdroj"
        context["entity"] = context["typ"]
        context["ident_cely"] = self.kwargs["ident_cely"]
        return context
