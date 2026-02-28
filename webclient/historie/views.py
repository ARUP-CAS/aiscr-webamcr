import logging

from adb.models import Adb
from arch_z.models import ArcheologickyZaznam
from core.models import Permissions as p
from core.models import Soubor, check_permissions
from core.views import ExportMixinDate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import ListView
from django_tables2 import RequestConfig, SingleTableMixin
from django_tables2.export.export import TableExport
from dokument.models import Dokument
from ez.models import ExterniZdroj
from historie.models import Historie
from historie.tables import FedoraHistorieTable, HistorieTable
from pas.models import SamostatnyNalez
from pian.models import Pian
from projekt.models import Projekt
from uzivatel.models import User

logger = logging.getLogger(__name__)


class HistorieListView(ExportMixinDate, LoginRequiredMixin, SingleTableMixin, ListView):
    """
    Třída pohledu pro zobrazení historie záznamu.

    Třída se dědí pro jednotlivá historie.
    """

    paginate_by = None
    use_history_table = True
    table_class = HistorieTable
    model = Historie
    template_name = "historie/historie_list.html"
    export_name = "export_historie_"
    table_pagination = {"per_page": 25}  # Výchozí počet záznamů v tabulce historie.

    context_typ = None  # např. "samostatny_nalez"
    lookup_kwarg = "ident_cely"  # URL parametr obsahující identifikátor
    queryset_filter = None  # např. "vazba__sn_historie__ident_cely"
    context_entity = None
    fedora_lookup = "ident_cely"

    def get_lookup_value(self):
        """Vrátí hodnotu z URL podle lookup_kwarg."""
        return self.kwargs[self.lookup_kwarg]

    def prepare_queryset(self, qs):
        """
        Potomek může přepsat pro vlastní řazení nebo dodatečné filtry.

        :param qs: Hodnota parametru ``qs`` použitého touto operací.
        """
        return qs.order_by("datum_zmeny")

    def add_extra_context(self, context):
        """
        Potomek může přepsat a doplnit další hodnoty do contextu.

        :param context: Hodnota parametru ``context`` použitého touto operací.
        """
        pass

    def get_queryset(self):
        """Vrací queryset historie po aplikaci výchozího řazení a filtrů."""
        if not self.use_history_table:
            return self.model.objects.none()
        if not self.queryset_filter:
            raise ValueError(f"{self.__class__.__name__} must define queryset_filter")

        lookup = self.get_lookup_value()
        qs = self.model.objects.filter(**{self.queryset_filter: lookup})
        qs = self.prepare_queryset(qs)
        return qs

    def get_header_config(self, context):
        """
        Potomek musí vrátit {'url': ..., 'icon': ..., 'text': ...}

        :param context: Hodnota parametru ``context`` použitého touto operací.
        """
        return None

    def add_fedora_history(self, context):
        """
        Pokud potomek definuje fedora_model, automaticky se načte

        metadata historie z Fedory a přidá se druhá tabulka fedora_table.

        :param context: Hodnota parametru ``context`` použitého touto operací.
        """
        if not hasattr(self, "fedora_model") or self.fedora_model is None:
            return

        ident = context.get("ident_cely") or context.get("pk") or context.get("soubor_id")
        if not ident:
            return

        lookup_field = getattr(self, "fedora_lookup", "ident_cely")
        lookup = {lookup_field: ident}

        try:
            record = self.fedora_model.objects.get(**lookup)
        except Exception:
            return
        fedora_data = record.get_historicke_verze()
        if not fedora_data:
            return
        fedora_table = FedoraHistorieTable(fedora_data, prefix="fed-")
        per_page = int(self.request.GET.get("fed-per_page", 25))  # Výchozí počet záznamů v tabulce Fedora historie.
        RequestConfig(self.request, paginate={"per_page": per_page}).configure(fedora_table)

        context["fedora_table"] = fedora_table

    def get_table(self, **kwargs):
        """
        Vrací tabulku historie naplněnou připraveným querysetem.

        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        if not self.use_history_table:
            return None
        return super().get_table(**kwargs)

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        if not self.use_history_table:
            self.table_class = None
        context = super().get_context_data(**kwargs)
        context["export_formats"] = ["csv", "json", "xlsx"]
        if self.context_typ:
            context["typ"] = self.context_typ
            context["entity"] = self.context_typ
        if self.context_entity:
            context["entity"] = self.context_entity
        try:
            context["ident_cely"] = self.get_lookup_value()
        except KeyError:
            pass
        self.add_extra_context(context)
        if check_permissions(p.actionChoices.historie_fedora, self.request.user, context["ident_cely"]):
            self.add_fedora_history(context)
        context["header"] = self.get_header_config(context)
        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Vyrenderuje to response.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        :param response_kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        export_format = self.request.GET.get("_export")
        export_table = self.request.GET.get("export_table")
        if export_format and export_table == "fedora":
            fedora_table = context.get("fedora_table")
            if fedora_table is None:
                return super().render_to_response(context, **response_kwargs)
            # Export tabulky Fedora historie.
            exporter = TableExport(export_format, fedora_table)
            return exporter.response(filename=self.get_export_filename(export_format, "export_fedora_historie_"))
        return super().render_to_response(context, **response_kwargs)


class ProjektHistorieListView(HistorieListView):
    """Třída pohledu pro zobrazení historie projektu."""

    context_typ = "projekt"
    queryset_filter = "vazba__projekt_historie__ident_cely"
    fedora_model = Projekt

    def get_header_config(self, context):
        """
        Vrací header config.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        """
        return {
            "url": reverse("projekt:detail", args=[context["ident_cely"]]),
            "icon": "dynamic_feed",
            "text": _("historie.templates.historieList.projekt.cardHeader"),
        }


class AkceHistorieListView(HistorieListView):
    """Třída pohledu pro zobrazení historie akcí."""

    context_typ = "akce"
    queryset_filter = "vazba__archeologickyzaznam__ident_cely"
    fedora_model = ArcheologickyZaznam

    def get_header_config(self, context):
        """
        Vrací header config.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        """
        return {
            "url": reverse("arch_z:detail", args=[context["ident_cely"]]),
            "icon": "brush",
            "text": _("historie.templates.historieList.akce.cardHeader"),
        }


class DokumentHistorieListView(HistorieListView):
    """Třida pohledu pro zobrazení historie dokumentů."""

    queryset_filter = "vazba__dokument_historie__ident_cely"
    fedora_model = Dokument

    def get_header_config(self, context):
        """
        Vrací header config.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        """
        ident = context["ident_cely"]
        if "3D" in ident:
            return {
                "url": reverse("dokument:detail-model-3D", args=[ident]),
                "icon": "3d_rotation",
                "text": _("historie.templates.historieList.model3D.cardHeader"),
            }
        return {
            "url": reverse("dokument:detail", args=[ident]),
            "icon": "description",
            "text": _("historie.templates.historieList.dokument.cardHeader"),
        }

    def add_extra_context(self, context):
        """
        Provádí operaci add extra context.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        """
        ident = self.get_lookup_value()
        typ = "knihovna_3d" if "3D" in ident else "dokument"
        context["typ"] = typ
        context["entity"] = typ


class SamostatnyNalezHistorieListView(HistorieListView):
    """Třida pohledu pro zobrazení historie samostatných nálezů."""

    context_typ = "samostatny_nalez"
    queryset_filter = "vazba__sn_historie__ident_cely"
    fedora_model = SamostatnyNalez

    def get_header_config(self, context):
        """
        Vrací header config.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        """
        return {
            "url": reverse("pas:detail", args=[context["ident_cely"]]),
            "icon": "location_on",
            "text": _("historie.templates.historieList.sn.cardHeader"),
        }


class SpolupraceHistorieListView(HistorieListView):
    """Třida pohledu pro zobrazení historie spolupráce."""

    context_typ = "spoluprace"
    context_entity = "samostatny_nalez"
    lookup_kwarg = "pk"
    queryset_filter = "vazba__spoluprace_historie__pk"

    def get_header_config(self, context):
        """
        Vrací header config.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        """
        return {
            "url": reverse("pas:spoluprace_list"),
            "icon": "location_on",
            "text": _("historie.templates.historieList.spoluprace.cardHeader"),
        }


class SouborHistorieListView(HistorieListView):
    """Třida pohledu pro zobrazení historie souborů."""

    context_typ = "soubor"
    lookup_kwarg = "soubor_id"
    queryset_filter = "vazba__soubor_historie"
    fedora_model = Soubor
    fedora_lookup = "pk"

    def prepare_queryset(self, qs):
        """
        Provádí operaci prepare queryset.

        :param qs: Vstupní hodnota ``qs`` pro danou operaci.
        """
        return qs.order_by("-datum_zmeny")

    def add_extra_context(self, context):
        """
        Provádí operaci add extra context.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        """
        soubor_id = self.get_lookup_value()
        soubor = get_object_or_404(Soubor, pk=soubor_id)
        context["projekt"] = getattr(soubor.vazba, "projekt_souboru", None)
        nav = getattr(soubor.vazba, "navazany_objekt", None)
        if nav:
            context["back_ident"] = getattr(nav, "ident_cely", None)
            if isinstance(nav, Projekt):
                context["back_model"] = "Projekt"
            elif isinstance(nav, Dokument):
                context["back_model"] = "DokumentModel3D" if "3D" in nav.ident_cely else "Dokument"
            elif isinstance(nav, SamostatnyNalez):
                context["back_model"] = "SamostatnyNalez"

    def get_header_config(self, context):
        """
        Vrací header config.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        """
        nav = context["back_model"]
        if nav == "Projekt":
            return {
                "url": reverse("projekt:detail", args=[context["back_ident"]]),
                "icon": "save",
                "text": _("historie.templates.historieList.soubor.cardHeader"),
            }
        if nav == "DokumentModel3D":
            return {
                "url": reverse("dokument:detail-model-3D", args=[context["back_ident"]]),
                "icon": "save",
                "text": _("historie.templates.historieList.soubor.cardHeader"),
            }
        if nav == "Dokument":
            return {
                "url": reverse("dokument:detail", args=[context["back_ident"]]),
                "icon": "save",
                "text": _("historie.templates.historieList.soubor.cardHeader"),
            }
        if nav == "SamostatnyNalez":
            return {
                "url": reverse("pas:detail", args=[context["back_ident"]]),
                "icon": "save",
                "text": _("historie.templates.historieList.soubor.cardHeader"),
            }

        return None


class LokalitaHistorieListView(HistorieListView):
    """Třida pohledu pro zobrazení historie lokalit."""

    context_typ = "lokalita"
    queryset_filter = "vazba__archeologickyzaznam__ident_cely"
    fedora_model = ArcheologickyZaznam

    def get_header_config(self, context):
        """
        Vrací header config.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        """
        return {
            "url": reverse("lokalita:detail", args=[context["ident_cely"]]),
            "icon": "tour",
            "text": _("historie.templates.historieList.lokalita.cardHeader"),
        }


class UzivatelHistorieListView(HistorieListView):
    """Třida pohledu pro zobrazení historie uživatele."""

    context_typ = "uzivatel"
    queryset_filter = "vazba__uzivatelhistorievazba__ident_cely"
    fedora_model = User

    def get_header_config(self, context):
        """
        Vrací header config.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        """
        next_url = self.request.GET.get("next", reverse("uzivatel:update-uzivatel"))
        return {
            "url": next_url,
            "icon": "person",
            "text": _("historie.templates.historieList.uzivatele.cardHeader"),
        }


class ExterniZdrojHistorieListView(HistorieListView):
    """Třida pohledu pro zobrazení historie externích zdrojů."""

    context_typ = "ext_zdroj"
    queryset_filter = "vazba__externizdroj__ident_cely"
    fedora_model = ExterniZdroj

    def get_header_config(self, context):
        """
        Vrací header config.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        """
        return {
            "url": reverse("ez:detail", args=[context["ident_cely"]]),
            "icon": "menu_book",
            "text": _("historie.templates.historieList.ext_zdroj.cardHeader"),
        }


class PianHistorieListView(HistorieListView):
    """Třida pohledu pro zobrazení historie Pianu."""

    use_history_table = False
    fedora_model = Pian
    context_typ = "akce"

    def get_header_config(self, context):
        """
        Vrací header config.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        """
        return {
            "url": reverse("arch_z:detail-dj", args=[self.kwargs["akce_ident_cely"], self.kwargs["dj_ident_cely"]]),
            "icon": "brush",
            "text": _("historie.templates.historieList.pian.cardHeader"),
        }


class PianLokalitaHistorieListView(HistorieListView):
    """Třida pohledu pro zobrazení historie Pianu."""

    use_history_table = False
    fedora_model = Pian
    context_typ = "lokalita"

    def get_header_config(self, context):
        """
        Vrací header config.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        """
        return {
            "url": reverse(
                "lokalita:detail-dj", args=[self.kwargs["lokalita_ident_cely"], self.kwargs["dj_ident_cely"]]
            ),
            "icon": "tour",
            "text": _("historie.templates.historieList.pian.cardHeader"),
        }


class AdbHistorieListView(HistorieListView):
    """Třida pohledu pro zobrazení historie ADB."""

    use_history_table = False
    fedora_model = Adb
    context_typ = "akce"

    def get_header_config(self, context):
        """
        Vrací header config.

        :param context: Vstupní hodnota ``context`` pro danou operaci.
        """
        return {
            "url": reverse("arch_z:detail-dj", args=[self.kwargs["akce_ident_cely"], self.kwargs["dj_ident_cely"]]),
            "icon": "brush",
            "text": _("historie.templates.historieList.adb.cardHeader"),
        }
