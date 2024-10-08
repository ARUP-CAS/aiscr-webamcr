import logging

from core.constants import ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID
from core.models import Soubor
from core.views import ExportMixinDate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import CharField, F, Value
from django.db.models.functions import Concat
from django.utils.translation import get_language
from django.views.generic import ListView
from django_tables2 import SingleTableMixin
from dokument.models import Dokument
from historie.models import Historie
from historie.tables import HistorieTable
from pas.models import SamostatnyNalez
from projekt.models import Projekt

logger = logging.getLogger(__name__)


class HistorieListView(ExportMixinDate, LoginRequiredMixin, SingleTableMixin, ListView):
    """
    Třida pohledu pro zobrazení historie záznamu.
    Třída se dedí pro jednotlivá historie.
    """

    table_class = HistorieTable
    model = Historie
    template_name = "historie/historie_list.html"
    export_name = "export_historie_"

    def _annotate_queryset(self, queryset):
        user = self.request.user
        if user.hlavni_role.pk in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID):
            return queryset.annotate(
                uzivatel_custom=Concat(
                    F("uzivatel__last_name"),
                    Value(", "),
                    F("uzivatel__first_name"),
                    Value(" ("),
                    F("uzivatel__ident_cely"),
                    Value(", "),
                    F("uzivatel__organizace__nazev_zkraceny_en")
                    if get_language() == "en"
                    else F("uzivatel__organizace__nazev_zkraceny"),
                    Value(")"),
                    output_field=CharField(),
                )
            )
        else:
            return queryset.annotate(
                uzivatel_custom=Concat(
                    F("uzivatel__ident_cely"),
                    Value(" ("),
                    F("uzivatel__organizace__nazev_zkraceny_en")
                    if get_language() == "en"
                    else F("uzivatel__organizace__nazev_zkraceny"),
                    Value(")"),
                    output_field=CharField(),
                )
            )

    def get_context_data(self, typ=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["export_formats"] = ["csv", "json", "xlsx"]
        return context


class ProjektHistorieListView(HistorieListView):
    """
    Třida pohledu pro zobrazení historie projektu.
    """

    def get_queryset(self):
        projekt_ident = self.kwargs["ident_cely"]
        queryset = self.model.objects.filter(vazba__projekt_historie__ident_cely=projekt_ident).order_by("datum_zmeny")
        queryset = self._annotate_queryset(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProjektHistorieListView, self).get_context_data(**kwargs)
        context["typ"] = "projekt"
        context["ident_cely"] = self.kwargs["ident_cely"]
        context["entity"] = context["typ"]
        return context


class AkceHistorieListView(HistorieListView):
    """
    Třida pohledu pro zobrazení historie akcií.
    """

    def get_queryset(self):
        akce_ident = self.kwargs["ident_cely"]
        queryset = self.model.objects.filter(vazba__archeologickyzaznam__ident_cely=akce_ident).order_by("datum_zmeny")
        queryset = self._annotate_queryset(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(AkceHistorieListView, self).get_context_data(**kwargs)
        context["typ"] = "akce"
        context["ident_cely"] = self.kwargs["ident_cely"]
        context["entity"] = context["typ"]
        return context


class DokumentHistorieListView(HistorieListView):
    """
    Třida pohledu pro zobrazení historie dokumentů.
    """

    def get_queryset(self):
        dokument_ident = self.kwargs["ident_cely"]
        queryset = self.model.objects.filter(vazba__dokument_historie__ident_cely=dokument_ident).order_by(
            "datum_zmeny"
        )
        queryset = self._annotate_queryset(queryset)
        return queryset

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
    """
    Třida pohledu pro zobrazení historie samostatných nálezů.
    """

    def get_queryset(self):
        sn_ident = self.kwargs["ident_cely"]
        queryset = self.model.objects.filter(vazba__sn_historie__ident_cely=sn_ident).order_by("datum_zmeny")
        queryset = self._annotate_queryset(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(SamostatnyNalezHistorieListView, self).get_context_data(**kwargs)
        context["typ"] = "samostatny_nalez"
        context["entity"] = context["typ"]
        context["ident_cely"] = self.kwargs["ident_cely"]
        return context


class SpolupraceHistorieListView(HistorieListView):
    """
    Třida pohledu pro zobrazení historie spolupráce.
    """

    def get_queryset(self):
        spoluprace_ident = self.kwargs["pk"]
        queryset = self.model.objects.filter(vazba__spoluprace_historie__pk=spoluprace_ident).order_by("datum_zmeny")
        queryset = self._annotate_queryset(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(SpolupraceHistorieListView, self).get_context_data(**kwargs)
        context["typ"] = "spoluprace"
        context["entity"] = "samostatny_nalez"
        return context


class SouborHistorieListView(HistorieListView):
    """
    Třida pohledu pro zobrazení historie souborů.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        soubor_id = self.kwargs["soubor_id"]
        context["typ"] = "soubor"
        context["entity"] = context["typ"]
        soubor = Soubor.objects.get(pk=soubor_id)
        try:
            context["projekt"] = soubor.vazba.projekt_souboru
        except Projekt.DoesNotExist:
            context["projekt"] = None
        back_ident = None
        back_model = None
        if soubor.vazba and soubor.vazba.navazany_objekt:
            navazany_objekt = soubor.vazba.navazany_objekt
            back_ident = navazany_objekt.ident_cely
            if isinstance(navazany_objekt, Projekt):
                back_model = "Projekt"
            elif isinstance(navazany_objekt, Dokument):
                if "3D" in navazany_objekt.ident_cely:
                    back_model = "DokumentModel3D"
                else:
                    back_model = "Dokument"
            elif isinstance(navazany_objekt, SamostatnyNalez):
                back_model = "SamostatnyNalez"
        context["back_ident"] = back_ident
        context["back_model"] = back_model
        return context

    def get_queryset(self):
        soubor_id = self.kwargs["soubor_id"]
        queryset = self.model.objects.filter(vazba__soubor_historie=soubor_id).order_by("-datum_zmeny")
        queryset = self._annotate_queryset(queryset)
        return queryset


class LokalitaHistorieListView(HistorieListView):
    """
    Třida pohledu pro zobrazení historie lokalit.
    """

    def get_queryset(self):
        lokalita_ident = self.kwargs["ident_cely"]
        queryset = self.model.objects.filter(vazba__archeologickyzaznam__ident_cely=lokalita_ident).order_by(
            "datum_zmeny"
        )
        queryset = self._annotate_queryset(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(LokalitaHistorieListView, self).get_context_data(**kwargs)
        context["typ"] = "lokalita"
        context["entity"] = context["typ"]
        context["ident_cely"] = self.kwargs["ident_cely"]
        return context


class UzivatelHistorieListView(HistorieListView):
    """
    Třida pohledu pro zobrazení historie uživatele.
    """

    def get_queryset(self):
        user_ident = self.kwargs["ident_cely"]
        queryset = self.model.objects.filter(vazba__uzivatelhistorievazba__ident_cely=user_ident).order_by(
            "datum_zmeny"
        )
        queryset = self._annotate_queryset(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(UzivatelHistorieListView, self).get_context_data(**kwargs)
        context["typ"] = "uzivatel"
        context["entity"] = context["typ"]
        context["ident_cely"] = self.kwargs["ident_cely"]
        return context


class ExterniZdrojHistorieListView(HistorieListView):
    """
    Třida pohledu pro zobrazení historie externích zdrojů.
    """

    def get_queryset(self):
        ez_ident = self.kwargs["ident_cely"]
        queryset = self.model.objects.filter(vazba__externizdroj__ident_cely=ez_ident).order_by("datum_zmeny")
        queryset = self._annotate_queryset(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ExterniZdrojHistorieListView, self).get_context_data(**kwargs)
        context["typ"] = "ext_zdroj"
        context["entity"] = context["typ"]
        context["ident_cely"] = self.kwargs["ident_cely"]
        return context
