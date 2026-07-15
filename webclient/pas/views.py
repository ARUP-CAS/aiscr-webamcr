import logging
from enum import Enum

import requests
import simplejson as json
from core.constants import (
    ARCHIVACE_SN,
    ODESLANI_SN,
    POTVRZENI_SN,
    ROLE_ADMIN_ID,
    ROLE_ARCHIVAR_ID,
    SN_ARCHIVOVANY,
    SN_ODESLANY,
    SN_POTVRZENY,
    SN_ZAPSANY,
    SPOLUPRACE_NEAKTIVNI,
    SPOLUPRACE_ZADOST,
    UZIVATEL_SPOLUPRACE_RELATION_TYPE,
    VRACENI_SN,
    ZAPSANI_SN,
)
from core.exceptions import MaximalIdentNumberError
from core.forms import CheckStavNotChangedForm, VratitForm
from core.ident_cely import get_sn_ident
from core.message_constants import (
    FORM_NOT_VALID,
    MAXIMUM_IDENT_DOSAZEN,
    PRISTUP_ZAKAZAN,
    PROJEKT_NENI_TYP_PRUZKUMNY,
    SAMOSTATNY_NALEZ_ARCHIVOVAN,
    SAMOSTATNY_NALEZ_NELZE_ARCHIVOVAT,
    SAMOSTATNY_NALEZ_NELZE_ODESLAT,
    SAMOSTATNY_NALEZ_NELZE_POTVRDIT,
    SAMOSTATNY_NALEZ_ODESLAN,
    SAMOSTATNY_NALEZ_POTVRZEN,
    SAMOSTATNY_NALEZ_VRACEN,
    SPOLUPRACE_BYLA_AKTIVOVANA,
    SPOLUPRACE_BYLA_DEAKTIVOVANA,
    SPOLUPRACE_NEBYLA_DEAKTIVOVANA,
    SPOLUPRACI_NELZE_AKTIVOVAT,
    SPOLUPRACI_NELZE_DEAKTIVOVAT,
    ZADOST_O_SPOLUPRACI_VYTVORENA,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from core.models import Permissions as p
from core.models import check_permissions
from core.repository_connector import FedoraError, FedoraRepositoryConnector, FedoraTransaction
from core.utils import TwoQueryPaginator, get_cadastre_from_point, get_cadastre_from_point_with_geometry
from core.views import PermissionFilterMixin, SearchListView, check_stav_changed
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, TemplateView, View
from dokument.forms import CoordinatesDokumentForm
from fedora_management.decorators import handle_fedora_error
from heslar.hesla_dynamicka import PRISTUPNOST_ARCHEOLOG_ID, TYP_PROJEKTU_PRUZKUM_ID
from heslar.models import Heslar
from historie.models import Historie, HistorieVazby
from pas.filters import SamostatnyNalezFilter, UzivatelSpolupraceFilter
from pas.forms import (
    CreateSamostatnyNalezForm,
    CreateZadostForm,
    DeaktivovatSpolupraciForm,
    EditSpolupraceProjektyForm,
    PotvrditNalezForm,
)
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from pas.tables import SamostatnyNalezTable, UzivatelSpolupraceTable
from pid.exceptions import DoiConnectionError, DoiWriteError
from projekt.models import Projekt
from services.mailer import Mailer
from uzivatel.models import User

logger = logging.getLogger(__name__)


def get_detail_context(sn, request):
    """
    Funkce pro získaní potřebného kontextu pro samostatný nález.

    :param sn: Parametr ``sn`` se předává do volání ``CreateSamostatnyNalezForm()``, ``PotvrditNalezForm()``, pracuje se s atributy ``historie``, ``soubory``, ovlivňuje větvení podmínek.
    :param request: Parametr ``request`` se předává do volání ``CreateSamostatnyNalezForm()``, ``get_history_dates()``, pracuje se s atributy ``user``.

        :return: Vrací proměnná ``context``.
    """
    context = {"sn": sn}
    context["form"] = CreateSamostatnyNalezForm(instance=sn, readonly=True, user=request.user)
    context["ulozeni_form"] = PotvrditNalezForm(instance=sn, readonly=True)
    context["history_dates"] = get_history_dates(sn.historie, request.user)
    context["show"] = get_detail_template_shows(sn, request.user)
    if sn.soubory:
        context["soubory"] = sorted(sn.soubory.soubory.all(), key=lambda x: (x.nazev.replace(".", "0"), x.nazev))
    else:
        context["soubory"] = None
    context["app"] = "pas"
    return context


@login_required
@require_http_methods(["GET"])
def index(request):
    """
    Funkce pohledu pro zobrazení domovské stránky samostatného nálezu s navigačními možnostmi.

    :param request: Parametr ``request`` se předává do volání ``render()``, vstupuje do návratové hodnoty.

        :return: Vrací výsledek volání ``render()``.
    """
    return render(request, "pas/index.html")


class SamostatnyNalezCreateView(LoginRequiredMixin, CreateView):
    """Implementuje komponentu ``SamostatnyNalezCreateView`` v rámci aplikace."""

    model = SamostatnyNalez
    form_class = CreateSamostatnyNalezForm
    template_name = "pas/create.html"

    class ActionType(Enum):
        """Implementuje komponentu ``ActionType`` v rámci aplikace."""

        CREATE = 1
        CREATE_FROM_PROJECT = 2
        CREATE_AS_COPY = 3

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        self.get_action_type = None
        self.copy_source = None
        super().__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        """
        Provádí operaci dispatch.

        :param request: Parametr ``request`` předává se do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``dispatch()``.
        """
        if "kopie" in self.request.path:
            get_action_type = self.ActionType.CREATE_AS_COPY.value
            self._set_copy_source()
        elif "ident_cely" in kwargs:
            get_action_type = self.ActionType.CREATE_FROM_PROJECT.value
        else:
            get_action_type = self.ActionType.CREATE.value
        self.get_action_type = get_action_type
        return super().dispatch(request, *args, **kwargs)

    def _set_copy_source(self):
        """
               Nastaví copy source.

        :return: Výstup funkce odpovídající implementované logice.
        """
        copy_source = get_object_or_404(SamostatnyNalez, ident_cely=self.kwargs["ident_cely"])
        copy_source.id = None
        copy_source.soubory = None
        copy_source.historie = None
        copy_source.evidencni_cislo = None
        copy_source.predano_organizace = None
        copy_source.predano = False
        copy_source.pristupnost = None
        copy_source.igsn = None
        self.copy_source = copy_source

    def get_form_kwargs(self):
        """
        Vrací form kwargs.

        :return: Vrací proměnná ``kwargs``.
        """
        kwargs = super().get_form_kwargs()
        if self.get_action_type == self.ActionType.CREATE_AS_COPY.value:
            kwargs["instance"] = self.copy_source
        kwargs["user"] = self.request.user
        kwargs["required"] = get_required_fields()
        kwargs["required_next"] = get_required_fields(next=1)
        kwargs["project_ident"] = (
            self.kwargs["ident_cely"] if self.get_action_type == self.ActionType.CREATE_FROM_PROJECT.value else None
        )
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        if self.get_action_type in (self.ActionType.CREATE.value, self.ActionType.CREATE_FROM_PROJECT.value):
            context["formCoor"] = CoordinatesDokumentForm()
        else:
            context["formCoor"] = CoordinatesDokumentForm(initial=self.copy_source.generate_coord_forms_initial())
        context["title"] = _("pas.views.create.title")
        context["header"] = _("pas.views.create.header")
        context["button"] = _("pas.views.create.submitButton.text")
        context["global_map_can_edit"] = True
        return context

    def form_valid(self, form):
        """
        Provádí operaci form valid.

        :param form: Parametr ``form`` se předává do volání ``form_invalid()``, pracuje se s atributy ``save``, ``save_m2m``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``form_invalid()``, výsledek volání ``HttpResponseRedirect()``.
        """
        form_coor = CoordinatesDokumentForm(self.request.POST)
        sn = form.save(commit=False)
        geom, geom_sjtsk = self.handle_geometry(form_coor)

        try:
            sn.ident_cely = get_sn_ident(sn.projekt)
        except MaximalIdentNumberError:
            messages.error(self.request, MAXIMUM_IDENT_DOSAZEN)
            return self.form_invalid(form)

        repository_connector = FedoraRepositoryConnector(sn)
        if not repository_connector.check_container_deleted_or_not_exists(sn.ident_cely, "samostatny_nalez"):
            logger.info(
                "pas.views.create.check_container_deleted_or_not_exists.incorrect",
                extra={"ident_cely": sn.ident_cely},
            )
            messages.error(self.request, _("pas.views.zapsat.create.check_container_deleted_or_not_exists_error"))
            return self.form_invalid(form)

        # Pokračuje uložením a další logikou.
        sn.create_transaction(self.request.user, ZAZNAM_USPESNE_VYTVOREN)
        sn.stav = SN_ZAPSANY
        sn.pristupnost = Heslar.objects.get(id=PRISTUPNOST_ARCHEOLOG_ID)
        sn.predano_organizace = None
        sn.geom_system = form_coor.data.get("coordinate_system")

        if geom is not None:
            sn.katastr = get_cadastre_from_point(geom)
            sn.geom = geom
        if geom_sjtsk is not None:
            sn.geom_sjtsk = geom_sjtsk

        sn.save()
        form.save_m2m()
        sn.set_zapsany(self.request.user)
        sn.close_active_transaction_when_finished = True
        sn.save()

        return HttpResponseRedirect(reverse("pas:detail", kwargs={"ident_cely": sn.ident_cely}))

    def form_invalid(self, form):
        """
        Zaloguje chyby neplatného formuláře a zobrazí uživateli zprávu.

        :param form: Parametr ``form`` se předává do volání ``info()``, ``form_invalid()``, pracuje se s atributy ``errors``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``form_invalid()``.
        """
        logger.info("pas.views.create.form_invalid", extra={"error": form.errors})
        messages.error(self.request, FORM_NOT_VALID)
        return super().form_invalid(form)

    def handle_geometry(self, form_coor):
        """
        Zpracuje geometry. v aplikaci.

        :param form_coor: Parametr ``form_coor`` předává se do volání ``float()``, pracuje se s atributy ``data``.

            :return: Vrací n-tici.
        """
        geom = None
        geom_sjtsk = None
        try:
            # Parsování souřadnic WGS84
            wgs84_x1 = float(form_coor.data.get("coordinate_wgs84_x1"))
            wgs84_x2 = float(form_coor.data.get("coordinate_wgs84_x2"))
            if wgs84_x1 > 0 and wgs84_x2 > 0:
                geom = Point(wgs84_x1, wgs84_x2)

            # Parsování souřadnic SJTSK
            sjtsk_x1 = float(form_coor.data.get("coordinate_sjtsk_x1"))
            sjtsk_x2 = float(form_coor.data.get("coordinate_sjtsk_x2"))
            if sjtsk_x1 < 0 and sjtsk_x2 < 0:
                geom_sjtsk = Point(sjtsk_x1, sjtsk_x2)
        except Exception:
            logger.info(
                "pas.views.create.corrd_format_error",
                extra={"geom": geom, "geom_sjtsk": geom_sjtsk},
            )
        return geom, geom_sjtsk

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` předává se do volání ``success()``, ``get()``, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, pracuje se s atributy ``get``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``HttpResponseRedirect()``, výsledek volání ``get()``.
        """
        ident_cely = kwargs.get("ident_cely")
        if self.get_action_type == self.ActionType.CREATE_FROM_PROJECT.value:
            proj = get_object_or_404(Projekt, ident_cely=ident_cely)
            if proj.typ_projektu.id != TYP_PROJEKTU_PRUZKUM_ID:
                logger.debug("Projekt neni typu pruzkumny")
                messages.success(request, PROJEKT_NENI_TYP_PRUZKUMNY)
                return HttpResponseRedirect(proj.get_absolute_url())
        return super().get(request, *args, **kwargs)


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    """
    Funkce pohledu pro zobrazení detailu samostatného nálezu.

    :param request: Parametr ``request`` se předává do volání ``update()``, ``get_detail_context()``, pracuje se s atributy ``session``, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``.

        :return: Vrací výsledek volání ``render()``.
    """
    context = {"warnings": request.session.pop("temp_data", None)}
    sn = get_object_or_404(
        SamostatnyNalez.objects.select_related(
            "soubory",
            "okolnosti",
            "obdobi",
            "druh_nalezu",
            "specifikace",
            "predano_organizace",
            "historie",
        ),
        ident_cely=ident_cely,
    )
    sn: SamostatnyNalez
    context.update(get_detail_context(sn=sn, request=request))
    if sn.geom:
        logger.debug(
            "pas.views.create.detail",
            extra={"geom_system": sn.geom_system, "ident_cely": sn.ident_cely},
        )
        context["formCoor"] = CoordinatesDokumentForm(
            initial=sn.generate_coord_forms_initial()
        )  # Zmen musis poslat data do formulare
        context["global_map_can_edit"] = False
    else:
        context["formCoor"] = CoordinatesDokumentForm()
    return render(request, "pas/detail.html", context)


@never_cache
@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    """
    Funkce pohledu pro editaci samostatného nálezu.

    :param request: Parametr ``request`` se předává do volání ``CreateSamostatnyNalezForm()``, ``CoordinatesDokumentForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``redirect()``, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
        :raises PermissionDenied: Vyvolá se při splnění podmínky ``sn.stav == SN_ARCHIVOVANY``.
    """
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if sn.stav == SN_ARCHIVOVANY:
        raise PermissionDenied()
    kwargs = {"projekt_disabled": "disabled"}
    required_fields = get_required_fields(sn)
    required_fields_next = get_required_fields(sn, 1)
    if request.method == "POST":
        request_post = request.POST.copy()
        request_post["projekt"] = sn.projekt
        form = CreateSamostatnyNalezForm(
            request_post,
            instance=sn,
            user=request.user,
            required=required_fields,
            required_next=required_fields_next,
            **kwargs,
        )
        form_coor = CoordinatesDokumentForm(request.POST)
        geom = None
        geom_sjtsk = None
        try:
            wgs84_x1 = float(form_coor.data.get("coordinate_wgs84_x1"))
            wgs84_x2 = float(form_coor.data.get("coordinate_wgs84_x2"))
            sjtsk_x1 = float(form_coor.data.get("coordinate_sjtsk_x1"))
            sjtsk_x2 = float(form_coor.data.get("coordinate_sjtsk_x2"))
            if wgs84_x1 > 0 and wgs84_x2 > 0:
                geom = Point(wgs84_x1, wgs84_x2)
            if sjtsk_x1 < 0 and sjtsk_x2 < 0:
                geom_sjtsk = Point(sjtsk_x1, sjtsk_x2)
        except Exception:
            logger.info(
                "pas.views.edit.corrd_format_error",
                extra={"geom": geom, "geom_sjtsk": geom_sjtsk},
            )
        if form.is_valid():
            logger.debug("pas.views.edit.form_valid")
            conflicting_fields = form.get_conflicting_fields()
            if conflicting_fields:
                geom_label = str(_("pas.forms.createSamostatnyNalezForm.souradnice.label"))
                conflicting_labels = [
                    geom_label if f == "geom" else str(form.fields[f].label)
                    for f in conflicting_fields
                    if f == "geom" or f in form.fields
                ]
                return render(
                    request,
                    "pas/edit.html",
                    {
                        "sn": sn,
                        "global_map_can_edit": True,
                        "formCoor": form_coor,
                        "form": form,
                        "concurrent_changes": conflicting_labels,
                        "fresh_form_url": reverse("pas:edit", kwargs={"ident_cely": ident_cely}),
                    },
                )
            sn.geom_system = form_coor.data.get("coordinate_system")
            if geom is not None:
                sn.katastr = get_cadastre_from_point(geom)
                sn.geom = geom
            if geom_sjtsk is not None:
                sn.geom_sjtsk = geom_sjtsk
            sn: SamostatnyNalez = form.save(commit=False)
            sn.create_transaction(request.user)
            sn.close_active_transaction_when_finished = True
            sn.save()
            if form.changed_data:
                logger.debug(
                    "pas.views.edit.form_changed_data",
                    extra={"data": str(form.changed_data)},
                )
            return redirect("pas:detail", ident_cely=ident_cely)
        else:
            logger.info("pas.views.edit.form_invalid", extra={"error": form.errors})
            return redirect("pas:detail", ident_cely=ident_cely)
    else:
        form = CreateSamostatnyNalezForm(
            instance=sn,
            user=request.user,
            required=required_fields,
            required_next=required_fields_next,
            **kwargs,
        )
        if sn.geom:
            form_coor = CoordinatesDokumentForm(initial=sn.generate_coord_forms_initial())
        else:
            form_coor = CoordinatesDokumentForm()
    return render(
        request,
        "pas/edit.html",
        {
            "sn": sn,
            "global_map_can_edit": True,
            "formCoor": form_coor,
            "form": form,
        },
    )


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def edit_ulozeni(request, ident_cely):
    """
    Funkce pohledu pro editaci uložení samostatného nálezu pomocí modalu.

    Pole ``predano_organizace`` je zobrazeno jako editovatelné; archeolog může zvolit cílovou organizaci (muzeum) nezávisle na organizaci projektu.

    :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``PotvrditNalezForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
    """
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    predano_required = True if sn.stav == SN_POTVRZENY else False
    if check_stav_changed(request, sn, prefix="edit-ulozeni"):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = PotvrditNalezForm(request.POST, instance=sn, predano_required=predano_required, prefix="edit-ulozeni")
        if form.is_valid():
            logger.debug("pas.views.edit_ulozeni.form_valid")
            sn: SamostatnyNalez = form.save(commit=False)
            sn.create_transaction(request.user)
            sn.close_active_transaction_when_finished = True
            sn.save()
            if form.changed_data:
                logger.debug(
                    "pas.views.edit_ulozeni.form_changed_data",
                    extra={"data": str(form.changed_data)},
                )
            return JsonResponse({"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})})
        else:
            logger.info(
                "pas.views.edit_ulozeni.form_invalid",
                extra={"error": form.errors},
            )
    else:
        form = PotvrditNalezForm(
            instance=sn,
            predano_required=predano_required,
            initial={"old_stav": sn.stav},
            predano_hidden=False,
            prefix="edit-ulozeni",
        )
    context = {
        "object": sn,
        "form": form,
        "title": _("pas.views.editUlozeni.title.text"),
        "id_tag": "edit-ulozeni-pas-form",
        "button": _("pas.views.editUlozeni.submitButton.text"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    """
    Funkce pohledu pro vrácení stavu samostatného nálezu pomocí modalu.

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
    """
    sn: SamostatnyNalez = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if not SN_ARCHIVOVANY >= sn.stav > SN_ZAPSANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentálně zbytečné, případná chyba se propaguje výše.
    if check_stav_changed(request, sn):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = VratitForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            fedora_transaction = sn.create_transaction(request.user, SAMOSTATNY_NALEZ_VRACEN)
            try:
                if sn.stav == SN_ARCHIVOVANY:
                    sn.igsn_hide()
                sn.set_vracen(request.user, sn.stav - 1, duvod)
                sn.close_active_transaction_when_finished = True
                sn.save()
                Mailer.send_en03_en04(samostatny_nalez=sn, reason=duvod)
                return JsonResponse({"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})})
            except (DoiWriteError, FedoraError) as err:
                logger.info("pas.views.vratit.error", extra={"error": err})
                transaction.set_rollback(True)
                fedora_transaction.rollback_transaction()
                if isinstance(err, FedoraError):
                    sn.igsn_publish(False)
            return JsonResponse({"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})})
        else:
            logger.info("pas.views.vratit.form_invalid", extra={"error": form.errors})
    else:
        form = VratitForm(initial={"old_stav": sn.stav})
    context = {
        "object": sn,
        "form": form,
        "title": _("pas.views.vratit.title.text"),
        "id_tag": "vratit-pas-form",
        "button": _("pas.views.vratit.submitButton.text"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def odeslat(request, ident_cely):
    """
    Funkce pohledu pro odeslání samostatného nálezu pomocí modalu.

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
    """
    sn: SamostatnyNalez = get_object_or_404(
        SamostatnyNalez.objects.select_related(
            "soubory",
            "okolnosti",
            "obdobi",
            "druh_nalezu",
            "specifikace",
            "predano_organizace",
            "historie",
        ),
        ident_cely=ident_cely,
    )
    if sn.stav != SN_ZAPSANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentálně zbytečné, případná chyba se propaguje výše.
    if check_stav_changed(request, sn):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        sn.create_transaction(request.user, SAMOSTATNY_NALEZ_ODESLAN)
        sn.set_odeslany(request.user)
        sn.close_active_transaction_when_finished = True
        sn.save()
        return JsonResponse({"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})})

    warnings = sn.check_pred_odeslanim()
    logger.info("pas.views.odeslat.warnings", extra={"warning": warnings})
    if warnings:
        request.session["temp_data"] = warnings
        messages.add_message(request, messages.ERROR, SAMOSTATNY_NALEZ_NELZE_ODESLAT)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    form_check = CheckStavNotChangedForm(initial={"old_stav": sn.stav})
    context = {
        "object": sn,
        "title": _("pas.views.odeslat.title.text"),
        "id_tag": "odeslat-pas-form",
        "button": _("pas.views.odeslat.submitButton.text"),
        "form_check": form_check,
    }

    return render(request, "core/transakce_modal.html", context)


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def potvrdit(request, ident_cely):
    """
    Funkce pohledu pro potvrzení samostatného nálezu pomocí modalu.

    Při potvrzení zobrazí formulář včetně pole ``predano_organizace``, které archeolog může vyplnit výběrem cílové organizace. Hodnota není odvozena od organizace projektu, ale uložena přímo z formuláře.

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``session``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
    """
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if sn.stav != SN_ODESLANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if check_stav_changed(request, sn, prefix="potvrdit"):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    warnings = sn.check_pred_odeslanim()
    logger.info("pas.views.potvrdit.warnings", extra={"warning": warnings})
    if warnings:
        request.session["temp_data"] = warnings
        messages.add_message(request, messages.ERROR, SAMOSTATNY_NALEZ_NELZE_POTVRDIT)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = PotvrditNalezForm(request.POST, instance=sn, predano_required=True, prefix="potvrdit")
        if form.is_valid():
            form_obj: SamostatnyNalez = form.save(commit=False)
            form_obj.create_transaction(request.user, SAMOSTATNY_NALEZ_POTVRZEN)
            form_obj.set_potvrzeny(request.user)
            form_obj.close_active_transaction_when_finished = True
            form_obj.save()
            return JsonResponse({"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})})
        else:
            logger.info("pas.views.potvrdit.form_invalid", extra={"error": form.errors})
    else:
        form = PotvrditNalezForm(
            instance=sn,
            initial={"old_stav": sn.stav},
            predano_hidden=False,
            predano_required=True,
            prefix="potvrdit",
        )
    context = {
        "object": sn,
        "form": form,
        "title": _("pas.views.potvrdit.title.text"),
        "id_tag": "potvrdit-pas-form",
        "button": _("pas.views.potvrdit.submitButton.text"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
def archivovat(request, ident_cely):
    """
    Funkce pohledu pro archivaci samostatného nálezu pomocí modalu.

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``session``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
    """
    sn: SamostatnyNalez = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if sn.stav != SN_POTVRZENY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentálně zbytečné, případná chyba se propaguje výše.
    if check_stav_changed(request, sn):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    warnings = sn.check_pred_odeslanim()
    logger.info("pas.views.archivovat.warnings", extra={"warning": warnings})
    if warnings:
        request.session["temp_data"] = warnings
        messages.add_message(request, messages.ERROR, SAMOSTATNY_NALEZ_NELZE_ARCHIVOVAT)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        fedora_transaction = sn.create_transaction(request.user, SAMOSTATNY_NALEZ_ARCHIVOVAN)
        try:
            sn.set_archivovany(request.user)
            sn.igsn_publish()
            sn.set_igsn()
            sn.close_active_transaction_when_finished = True
            sn.save()
            return JsonResponse({"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})})
        except (DoiWriteError, FedoraError) as err:
            logger.info("pas.views.archivovat.error", extra={"error": err, "ident_cely": ident_cely})
            transaction.set_rollback(True)
            fedora_transaction.rollback_transaction()
            if isinstance(err, FedoraError):
                sn.igsn_hide(False)
        return JsonResponse({"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})})
    else:
        # TODO: doplnit případné kontroly (warnings = sn.check_pred_archivaci()).
        try:
            igsn_confirmation = sn.igsn_exists() and sn.igsn is None
        except (DoiConnectionError, requests.RequestException) as err:
            logger.warning(
                "pas.views.archivovat.igsn_exists_check_failed",
                extra={"ident_cely": sn.ident_cely, "error": err},
                exc_info=True,
            )
            igsn_confirmation = False
        form_check = CheckStavNotChangedForm(require_confirmation=igsn_confirmation, initial={"old_stav": sn.stav})
        context = {
            "object": sn,
            "title": _("pas.views.archivovat.title.text"),
            "id_tag": "archivovat-pas-form",
            "pid_confirmation": igsn_confirmation,
            "button": _("pas.views.archivovat.submitButton.text"),
            "form_check": form_check,
        }
    return render(request, "core/transakce_modal.html", context)


class PasPermissionFilterMixin(PermissionFilterMixin):
    """Implementuje komponentu ``PasPermissionFilterMixin`` v rámci aplikace."""

    def add_ownership_lookup(self, ownership, qs):
        """
        Provádí operaci add ownership lookup.

        Pro vlastnictví ``ours`` vrací podmínku pokrývající jak organizaci projektu (``projekt__organizace``), tak cílovou organizaci nálezu (``predano_organizace``).

        :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
        :param qs: Parametr ``qs`` slouží jako vstup pro logiku funkce ``add_ownership_lookup``.

            :return: Vrací výsledek volání ``Q()``.
        """
        filter_historie = {"uzivatel": self.request.user}
        filtered_my = Historie.objects.filter(**filter_historie)
        if ownership == p.ownershipChoices.our:
            return Q(projekt__organizace=self.request.user.organizace) | Q(
                predano_organizace=self.request.user.organizace
            )
        else:
            return Q(**{"historie_zapsat__in": filtered_my})


class SamostatnyNalezListView(SearchListView, PasPermissionFilterMixin):
    """Třída pohledu pro zobrazení přehledu samostatných nálezu s filtrem v podobe tabulky."""

    table_class = SamostatnyNalezTable
    model = SamostatnyNalez
    template_name = "pas/samostatny_nalez_list.html"
    filterset_class = SamostatnyNalezFilter
    export_name = "export_samostatny-nalez_"
    app = "samostatny_nalez"
    redis_snapshot_prefix = "samostatny_nalez"
    redis_value_list_field = "ident_cely"
    toolbar = "toolbar_pas.html"
    typ_zmeny_lookup = ZAPSANI_SN
    vypis_app = "pas"
    map_enabled = True
    map_layer = "pas"
    table_pagination = {"per_page": 100, "paginator_class": TwoQueryPaginator}

    def init_translations(self):
        """
        Inicializuje překlady pro zobrazení seznamu.
        """
        super().init_translations()
        self.page_title = _("pas.views.samostatnyNalezListView.pageTitle")
        self.search_sum = _("pas.views.samostatnyNalezListView.pocetVyhledanych")
        self.pick_text = _("pas.views.samostatnyNalezListView.pickText")
        self.hasOnlyVybrat_header = _("pas.views.samostatnyNalezListView.header.hasOnlyVybrat")
        self.hasOnlyVlastnik_header = _("pas.views.samostatnyNalezListView.header.hasOnlyVlastnik")
        self.hasOnlyArchive_header = _("pas.views.samostatnyNalezListView.header.hasOnlyArchive")
        self.hasOnlyPotvrdit_header = _("pas.views.samostatnyNalezListView.header.hasOnlyPotvrdit")
        self.hasOnlyNase_header = _("pas.views.samostatnyNalezListView.hasOnlyNase_header.text")
        self.default_header = _("pas.views.samostatnyNalezListView.header.default")

    @staticmethod
    def rename_field_for_ordering(field: str):
        """
        Provádí operaci rename field for ordering.

        :param field: Parametr ``field`` předává se do volání ``get()``, pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``get()``.
        """
        field = field.replace("-", "")
        return {
            "katastr": "katastr__nazev",
            "okres": "katastr__okres__nazev",
            "kraj": "katastr__okres__kraj__nazev",
            "nalezce": "nalezce__vypis_cely",
            "predano_organizace": "predano_organizace__nazev_zkraceny",
            "obdobi": "obdobi__razeni",
            "druh_nalezu": "druh_nalezu__razeni",
            "specifikace": "specifikace__razeni",
            "pristupnost": "pristupnost__razeni",
            "okolnosti": "okolnosti__razeni",
        }.get(field, field)

    def get_queryset(self):
        """
        Vrací queryset. v aplikaci.

        :return: Vrací výsledek volání ``check_filter_permission()``.
        """
        sort_params = self._get_sort_params()
        sort_params = [self.rename_field_for_ordering(x) for x in sort_params]
        qs = super().get_queryset()
        qs = qs.order_by(*sort_params)
        qs = qs.distinct("pk", *sort_params)
        qs = (
            qs.select_related(
                "nalezce",
                "predano_organizace",
                "katastr",
                "katastr__okres__kraj",
                "soubory",
            )
            .prefetch_related(
                "specifikace",
                "okolnosti",
                "pristupnost",
                "soubory__soubory",
                "obdobi",
                "druh_nalezu",
            )
            .defer(
                "geom",
                "geom_sjtsk",
                # nalezce (Osoba.__str__ = vypis_cely)
                "nalezce__jmeno",
                "nalezce__prijmeni",
                "nalezce__vypis",
                "nalezce__rok_narozeni",
                "nalezce__rok_umrti",
                "nalezce__rodne_prijmeni",
                "nalezce__ident_cely",
                "nalezce__orcid",
                "nalezce__wikidata",
                # predano_organizace (Organizace.__str__ = nazev_zkraceny / nazev_zkraceny_en)
                "predano_organizace__nazev",
                "predano_organizace__typ_organizace",
                "predano_organizace__oao",
                "predano_organizace__mesicu_do_zverejneni",
                "predano_organizace__zverejneni_pristupnost",
                "predano_organizace__email",
                "predano_organizace__telefon",
                "predano_organizace__adresa",
                "predano_organizace__ico",
                "predano_organizace__soucast",
                "predano_organizace__nazev_en",
                "predano_organizace__zanikla",
                "predano_organizace__ident_cely",
                "predano_organizace__cteni_dokumentu",
                "predano_organizace__ror",
                "predano_organizace__licence_id",
                "predano_organizace__web",
                # katastr (RuianKatastr.__str__ = nazev, kod, okres.nazev)
                "katastr__pian_id",
                "katastr__definicni_bod",
                "katastr__hranice",
                # okres (RuianOkres.__str__ = nazev)
                "katastr__okres__spz",
                "katastr__okres__kod",
                "katastr__okres__nazev_en",
                "katastr__okres__definicni_bod",
                "katastr__okres__hranice",
                # kraj (RuianKraj.__str__ = nazev)
                "katastr__okres__kraj__kod",
                "katastr__okres__kraj__rada_id",
                "katastr__okres__kraj__nazev_en",
                "katastr__okres__kraj__email",
                "katastr__okres__kraj__definicni_bod",
                "katastr__okres__kraj__hranice",
            )
        )

        return self.check_filter_permission(qs)


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    """
    Funkce pohledu pro smazání samostatného nálezu pomocí modalu.

    :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``create_transaction()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
    """
    nalez: SamostatnyNalez = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if check_stav_changed(request, nalez):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        nalez.deleted_by_user = request.user
        fedora_transaction = nalez.create_transaction(request.user, ZAZNAM_USPESNE_SMAZAN, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
        try:
            nalez.igsn_delete()
            nalez.close_active_transaction_when_finished = True
            nalez.record_deletion(nalez.active_transaction)
            resp1 = nalez.delete()
            if resp1:
                logger.info(
                    "pas.views.smazat.deleted",
                    extra={"value": resp1},
                )
                return JsonResponse({"redirect": reverse("pas:index")})
            else:
                logger.warning("pas.views.smazat.not_deleted", extra={"ident_cely": ident_cely})
                nalez.igsn_update(False, True)
                fedora_transaction.rollback_transaction()
                return JsonResponse(
                    {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
                    status=403,
                )
        except (DoiWriteError, FedoraError) as err:
            logger.info("pas.views.smazat.error", extra={"error": err, "ident_cely": ident_cely})
            transaction.set_rollback(True)
            fedora_transaction.rollback_transaction()
            if isinstance(err, FedoraError):
                nalez.igsn_update(False, True)
            return JsonResponse({"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})})
    else:
        form_check = CheckStavNotChangedForm(initial={"old_stav": nalez.stav})
        context = {
            "object": nalez,
            "title": _("pas.views.smazat.title.text"),
            "id_tag": "smazat-pas-form",
            "button": _("pas.views.smazat.submitButton.text"),
            "form_check": form_check,
        }
        return render(request, "core/transakce_modal.html", context)


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def zadost(request):
    """
    Funkce pohledu pro vytvoření žádosti o spolupráci.

    :param request: Parametr ``request`` se předává do volání ``CreateZadostForm()``, ``filter()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
    """
    if request.method == "POST":
        logger.debug("pas.views.zadost.start")
        form = CreateZadostForm(request.POST)
        if form.is_valid():
            logger.debug("pas.views.zadost.form_valid")
            uzivatel_email = form.cleaned_data["email_uzivatele"]
            uzivatel_text = form.cleaned_data["text"]
            uzivatel = get_object_or_404(User, email=uzivatel_email)
            exists = UzivatelSpoluprace.objects.filter(vedouci=uzivatel, spolupracovnik=request.user).exists()

            if uzivatel == request.user:
                messages.add_message(request, messages.ERROR, _("pas.views.zadost.uzivatel.error"))
                logger.debug(
                    "pas.views.zadost.post.error",
                    extra={"error": "Nelze vytvořit spolupráci sám se sebou"},
                )
            elif exists:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _("pas.views.zadost.existuje.error.part1")
                    + uzivatel_email
                    + _("pas.views.zadost.existuje.error.part2"),
                )
                logger.debug(
                    "pas.views.zadost.post.error",
                    extra={
                        "error": "Spoluprace jiz existuje",
                        "email": uzivatel_email,
                    },
                )

            else:
                hv = HistorieVazby(typ_vazby=UZIVATEL_SPOLUPRACE_RELATION_TYPE)
                hv.save()
                s = UzivatelSpoluprace(
                    vedouci=uzivatel,
                    spolupracovnik=request.user,
                    stav=SPOLUPRACE_NEAKTIVNI,
                    historie=hv,
                )
                s.active_transaction = FedoraTransaction()
                s.close_active_transaction_when_finished = True
                s.save()
                hist = Historie(
                    typ_zmeny=SPOLUPRACE_ZADOST,
                    uzivatel=request.user,
                    vazba=hv,
                    poznamka=uzivatel_text,
                )
                hist.save()
                messages.add_message(request, messages.SUCCESS, ZADOST_O_SPOLUPRACI_VYTVORENA)
                logger.debug(
                    "pas.views.zadost.post.success",
                    extra={"hv_pk": hv.pk, "s_pk": s.pk, "pk": hist.pk},
                )

                Mailer.send_en05(
                    email_to=uzivatel_email,
                    reason=uzivatel_text,
                    user=request.user,
                    spoluprace_id=s.pk,
                )
                return redirect("pas:spoluprace_list")
        else:
            logger.info("pas.views.zadost.form_invalid", extra={"error": form.errors})
    else:
        form = CreateZadostForm()

    return render(
        request,
        "pas/zadost.html",
        {"title": _("pas.views.zadost.title.text"), "header": _("pas.views.zadost.header.text"), "form": form},
    )


class UzivatelSpolupraceListView(SearchListView):
    """Třída pohledu pro zobrazení přehledu spoluprác s filtrem v podobe tabulky."""

    table_class = UzivatelSpolupraceTable
    model = UzivatelSpoluprace
    template_name = "pas/uzivatel_spoluprace_list.html"
    filterset_class = UzivatelSpolupraceFilter
    export_name = "export_spoluprace_"
    app = "spoluprace"
    redis_snapshot_prefix = "uzivatel_spoluprace"
    redis_value_list_field = "id"
    toolbar = "toolbar_spoluprace.html"
    typ_zmeny_lookup = SPOLUPRACE_ZADOST

    def init_translations(self):
        """
        Inicializuje překlady pro zobrazení seznamu.
        """
        super().init_translations()
        self.page_title = _("pas.views.uzivatelSpolupraceListView.pageTitle")
        self.search_sum = _("pas.views.uzivatelSpolupraceListView.pocetVyhledanych")
        self.pick_text = _("pas.views.uzivatelSpolupraceListView.pickText")
        self.toolbar_name = _("pas.views.uzivatelSpolupraceListView.toolbar.title")

    @staticmethod
    def rename_field_for_ordering(field: str):
        """
        Provádí operaci rename field for ordering.

        :param field: Parametr ``field`` předává se do volání ``get()``, pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``get()``.
        """
        field = field.replace("-", "")
        return {
            "organizace_vedouci": "vedouci__organizace__nazev_zkraceny",
            "organizace_spolupracovnik": "spolupracovnik__organizace__nazev_zkraceny",
        }.get(field, field)

    def get_queryset(self):
        """
        Vrací queryset. v aplikaci.

        :return: Vrací výsledek volání ``order_by()``.
        """
        sort_params = self._get_sort_params()
        sort_params = [self.rename_field_for_ordering(x) for x in sort_params]
        qs = super().get_queryset()
        if "vedouci" in sort_params:
            index = sort_params.index("vedouci")
            sort_params[index : index + 1] = ["vedouci__last_name", "vedouci__first_name", "vedouci__ident_cely"]
        if "spolupracovnik" in sort_params:
            index = sort_params.index("spolupracovnik")
            sort_params[index : index + 1] = [
                "spolupracovnik__last_name",
                "spolupracovnik__first_name",
                "spolupracovnik__ident_cely",
            ]
        qs = qs.order_by(*sort_params)
        qs = qs.distinct("pk", *sort_params)
        qs = qs.select_related(
            "vedouci",
            "spolupracovnik",
            "vedouci__organizace",
            "historie",
            "spolupracovnik__organizace",
        ).prefetch_related("projekty")
        return self.check_filter_permission(qs).order_by("id")

    def add_ownership_lookup(self, ownership, qs=None):
        """
        Provádí operaci add ownership lookup.

        :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
        :param qs: Parametr ``qs`` slouží jako vstup pro logiku funkce ``add_ownership_lookup``.

            :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, proměnná ``filtered_my``.
        """
        filtered_my = Q(spolupracovnik=self.request.user)
        if ownership == p.ownershipChoices.our:
            filtered_our = Q(vedouci__organizace=self.request.user.organizace)
            return filtered_our | filtered_my
        else:
            return filtered_my

    def add_accessibility_lookup(self, permission, qs):
        """
        Provádí operaci add accessibility lookup.

        :param permission: Parametr ``permission`` slouží jako vstup pro logiku funkce ``add_accessibility_lookup``.
        :param qs: Parametr ``qs`` vstupuje do návratové hodnoty.

            :return: Vrací proměnná ``qs``.
        """
        return qs

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["show_zadost"] = check_permissions(p.actionChoices.spoluprace_zadost, self.request.user)
        context["trans_deaktivovat"] = _("pas.templates.aktivace_deaktivace_cell.deaktivovat")
        context["trans_aktivovat"] = _("pas.templates.aktivace_deaktivace_cell.aktivovat")
        context["trans_smazat"] = _("pas.templates.smazat_cell.Smazat")
        return context

    def get_table_kwargs(self):
        """
        Vrací table kwargs s případným vyloučením sloupce ``smazani`` u neadminů a předáním uživatele.

        :return: Vrací slovník.
        """
        kwargs: dict = {"user": self.request.user}
        if self.request.user.hlavni_role.id != ROLE_ADMIN_ID:
            kwargs["exclude"] = ("smazani",)
        return kwargs


@login_required
@require_http_methods(["GET", "POST"])
def aktivace(request, pk):
    """
    Funkce pohledu pro aktivaci spolupráce pomocí modalu.

    :param request: Parametr ``request`` se předává do volání ``set_aktivni()``, ``add_message()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param pk: Identifikátor ``pk`` používaný pro dohledání cílového záznamu.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``redirect()``, výsledek volání ``render()``.
    """
    spoluprace = get_object_or_404(UzivatelSpoluprace, id=pk)
    if request.method == "POST":
        fedora_transaction = FedoraTransaction()
        try:
            spoluprace.active_transaction = fedora_transaction
            spoluprace.close_active_transaction_when_finished = True
            spoluprace.set_aktivni(request.user)
            messages.add_message(request, messages.SUCCESS, SPOLUPRACE_BYLA_AKTIVOVANA)
            Mailer.send_en06(cooperation=spoluprace)
            return JsonResponse({"redirect": reverse("pas:spoluprace_list")})
        except FedoraError as err:
            logger.info("pas.views.aktivace.error", extra={"error": err})
            fedora_transaction.rollback_transaction()
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, SPOLUPRACI_NELZE_AKTIVOVAT)
            return redirect(reverse("pas:spoluprace_list"))
    else:
        warnings = spoluprace.check_pred_aktivaci()
        logger.info("pas.views.aktivace.warnings", extra={"warning": warnings})
        if warnings:
            messages.add_message(request, messages.ERROR, f"{SPOLUPRACI_NELZE_AKTIVOVAT} {warnings[0]}")
            return JsonResponse({"redirect": reverse("pas:spoluprace_list")}, status=403)
    context = {
        "object": spoluprace,
        "title": (
            _("pas.views.aktivace.title.part1")
            + spoluprace.vedouci.email
            + _("pas.views.aktivace.title.part2")
            + spoluprace.spolupracovnik.email
        ),
        "id_tag": "aktivace-spoluprace-form",
        "button": _("pas.views.aktivace.submitButton.text"),
    }
    return render(request, "core/transakce_modal.html", context)


class AktivaceEmailView(LoginRequiredMixin, DetailView):
    """Implementuje komponentu ``AktivaceEmailView`` v rámci aplikace."""

    template_name = "pas/potvrdit_spolupraci.html"
    model = UzivatelSpoluprace

    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``set_aktivni()``, pracuje se s atributy ``user``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``redirect()``.
        """
        obj: UzivatelSpoluprace = self.get_object()
        fedora_transaction = FedoraTransaction()
        try:
            if not obj.aktivni:
                obj.active_transaction = fedora_transaction
                obj.close_active_transaction_when_finished = True
                obj.set_aktivni(request.user)
                Mailer.send_en06(cooperation=obj)
            return redirect(reverse("pas:spoluprace_list") + "?sort=organizace_vedouci&sort=spolupracovnik")
        except FedoraError as err:
            logger.info("pas.views.aktivace.error", extra={"error": err})
            fedora_transaction.rollback_transaction()
            transaction.set_rollback(True)
            return redirect(reverse("pas:spoluprace_list") + "?sort=organizace_vedouci&sort=spolupracovnik")


class DeaktivaceSpolupraceView(LoginRequiredMixin, TemplateView):
    """Definuje pohled pro deaktivaci spolupráce v modálním dialogu."""

    template_name = "core/transakce_modal.html"

    def get_object(self):
        """
        Vrací object. v aplikaci.

        :return: Vrací výsledek volání ``get_object_or_404()``.
        """
        return get_object_or_404(UzivatelSpoluprace, id=self.kwargs["pk"])

    def get_context_data(self, *args, **kwargs):
        """
        Vrací context data.

        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get_context_data``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

            :return: Vrací proměnná ``context``.
        """
        obj: UzivatelSpoluprace = self.get_object()
        form = DeaktivovatSpolupraciForm()
        context = {
            "object": obj,
            "title": (
                _("pas.views.deaktivace.title.part1")
                + obj.vedouci.email
                + _("pas.views.deaktivace.title.part2")
                + obj.spolupracovnik.email
            ),
            "id_tag": "deaktivace-spoluprace-form",
            "button": _("pas.views.deaktivace.submitButton.text"),
            "form": form,
        }
        return context

    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` předává se do volání ``add_message()``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.
        """
        context = self.get_context_data()
        warnings = context["object"].check_pred_deaktivaci()
        if warnings:
            logger.info("pas.views.deaktivace.warnings", extra={"warning": warnings})
            messages.add_message(request, messages.ERROR, f"{SPOLUPRACI_NELZE_DEAKTIVOVAT} {warnings[0]}")
            return JsonResponse({"redirect": reverse("pas:spoluprace_list")}, status=403)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``DeaktivovatSpolupraciForm()``, ``set_neaktivni()``, pracuje se s atributy ``POST``, ``user``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``redirect()``.
        """
        obj: UzivatelSpoluprace = self.get_object()
        logger.info("pas.views.deaktivace_spoluprace.start", extra={"pk": obj.pk})
        form = DeaktivovatSpolupraciForm(request.POST)
        if form.is_valid():
            fedora_transaction = FedoraTransaction()
            logger.info(
                "pas.views.deaktivace_spoluprace.form_valid",
                extra={"pk": obj.pk, "transaction": fedora_transaction.uid},
            )
            try:
                obj.active_transaction = fedora_transaction
                obj.close_active_transaction_when_finished = True
                obj.set_neaktivni(request.user, form.cleaned_data["reason"])
                Mailer.send_en07(cooperation=obj, reason=form.cleaned_data["reason"])
                messages.add_message(request, messages.SUCCESS, SPOLUPRACE_BYLA_DEAKTIVOVANA)
                return redirect(reverse("pas:spoluprace_list"))
            except FedoraError as err:
                logger.info("pas.views.deaktivace_spoluprace.fedora_error", extra={"error": err})
                fedora_transaction.rollback_transaction()
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, SPOLUPRACE_NEBYLA_DEAKTIVOVANA)
                return redirect(reverse("pas:spoluprace_list"))
        else:
            logger.info("pas.views.deaktivace_spoluprace.form_error", extra={"instance": obj.pk})
            messages.add_message(request, messages.ERROR, SPOLUPRACE_NEBYLA_DEAKTIVOVANA)
        return redirect(reverse("pas:spoluprace_list"))


@login_required
@require_http_methods(["GET", "POST"])
def smazat_spolupraci(request, pk):
    """
    Funkce pohledu pro smazání spolupráce pomocí modalu.

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``render()``, pracuje se s atributy ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param pk: Identifikátor ``pk`` používaný pro dohledání cílového záznamu.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
    """
    spoluprace = get_object_or_404(UzivatelSpoluprace, id=pk)
    if request.method == "POST":
        fedora_transaction = FedoraTransaction()
        try:
            spoluprace.active_transaction = fedora_transaction
            spoluprace.close_active_transaction_when_finished = True
            resp1 = spoluprace.delete()
            if resp1:
                logger.info(
                    "pas.views.smazat_spolupraci.deleted",
                    extra={"value": resp1},
                )
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
                return redirect(reverse("pas:spoluprace_list"))
            else:
                logger.warning("pas.views.smazat_spolupraci.not_deleted", extra={"pk": pk})
                messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
                return redirect(reverse("pas:spoluprace_list"))
        except FedoraError as err:
            logger.warning("pas.views.smazat_spolupraci.fedora_error", extra={"pk": pk, "error": err})
            fedora_transaction.rollback_transaction()
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            return redirect(reverse("pas:spoluprace_list"))
    else:
        context = {
            "object": spoluprace,
            "title": (
                _("pas.views.smazatSpolupraci.title.part1")
                + spoluprace.vedouci.email
                + _("pas.views.smazatSpolupraci.title.part2")
                + spoluprace.spolupracovnik.email
            ),
            "id_tag": "smazani-spoluprace-form",
            "button": _("pas.views.smazatSpolupraci.submitButton.text"),
        }
    return render(request, "core/transakce_modal.html", context)


class EditSpolupraceProjektyView(LoginRequiredMixin, TemplateView):
    """Pohled pro editaci projektů přiřazených ke spolupráci v modálním dialogu."""

    template_name = "core/transakce_table_modal.html"

    def get_object(self):
        """Vrací objekt spolupráce.

        :return: Vrací výsledek volání ``get_object_or_404()``.
        """
        return get_object_or_404(UzivatelSpoluprace, id=self.kwargs["pk"])

    def get_context_data(self, *args, **kwargs):
        """
        Vrací context data.

        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get_context_data``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

            :return: Vrací proměnná ``context``.
        """
        obj: UzivatelSpoluprace = self.get_object()
        form = EditSpolupraceProjektyForm(
            instance=obj, vedouci_organizace=obj.vedouci.organizace, prefix="edit-spoluprace-projekty"
        )
        return {
            "object": obj,
            "title": _("pas.views.editSpolupraceProjeky.title"),
            "id_tag": "edit-spoluprace-projekty-form",
            "button": _("pas.views.editSpolupraceProjeky.submitButton.text"),
            "form": form,
            "selected_projekty": obj.projekty.all(),
        }

    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` předává se do volání ``add_message()``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.
        """
        obj: UzivatelSpoluprace = self.get_object()
        if not check_permissions(p.actionChoices.spoluprace_edit_projekty, request.user, obj.id):
            messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
            return JsonResponse({"redirect": reverse("pas:spoluprace_list")}, status=403)
        context = self.get_context_data()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``EditSpolupraceProjektyForm()``, pracuje se s atributy ``POST``, ``user``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``.
        """
        obj: UzivatelSpoluprace = self.get_object()
        if not check_permissions(p.actionChoices.spoluprace_edit_projekty, request.user, obj.id):
            messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
            return JsonResponse({"redirect": reverse("pas:spoluprace_list")}, status=403)
        form = EditSpolupraceProjektyForm(
            request.POST, instance=obj, vedouci_organizace=obj.vedouci.organizace, prefix="edit-spoluprace-projekty"
        )
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, _("pas.views.editSpolupraceProjeky.success"))
        else:
            messages.add_message(request, messages.ERROR, FORM_NOT_VALID)
        next_url = request.POST.get("next") or request.GET.get("next") or request.META.get("HTTP_REFERER", "")
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            redirect_url = next_url
        else:
            redirect_url = reverse("pas:spoluprace_list")
        return JsonResponse({"redirect": redirect_url})


def get_history_dates(historie_vazby, request_user):
    """
    Funkce pro získaní historických datumu.

    :param historie_vazby: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
    :param request_user: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.
    :return: Slovník dat jednotlivých změn stavu pro zobrazení v historii.
    """
    anonymized = request_user.hlavni_role.pk not in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)
    historie = {
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_SN, anonymized),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_SN, anonymized),
        "datum_potvrzeni": historie_vazby.get_last_transaction_date(POTVRZENI_SN, anonymized),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_SN, anonymized),
        "datum_vraceni": historie_vazby.get_last_transaction_if_type(VRACENI_SN, anonymized),
    }
    return historie


def get_detail_template_shows(sn, user):
    """
    Funkce pro získaní kontextu pro zobrazování možností na stránkách.

    :param sn: Parametr ``sn`` se předává do volání ``check_permissions()``, pracuje se s atributy ``stav``, ``ident_cely``.
    :param user: Parametr ``user`` se předává do volání ``check_permissions()``, pracuje se s atributy ``is_archeolog_or_more``.
    :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.
    """
    show_arch_links = sn.stav == SN_ARCHIVOVANY
    show = {
        "vratit_link": check_permissions(p.actionChoices.pas_vratit, user, sn.ident_cely),
        "odeslat_link": check_permissions(p.actionChoices.pas_odeslat, user, sn.ident_cely),
        "potvrdit_link": check_permissions(p.actionChoices.pas_potvrdit, user, sn.ident_cely),
        "archivovat_link": check_permissions(p.actionChoices.pas_archivovat, user, sn.ident_cely),
        "editovat": check_permissions(p.actionChoices.pas_edit, user, sn.ident_cely),
        "arch_links": show_arch_links,
        "smazat": check_permissions(p.actionChoices.pas_smazat, user, sn.ident_cely),
        "ulozeni_edit": check_permissions(p.actionChoices.pas_ulozeni_edit, user, sn.ident_cely),
        "soubor_stahnout": check_permissions(p.actionChoices.soubor_stahnout_pas, user, sn.ident_cely),
        "soubor_nahled": check_permissions(p.actionChoices.soubor_nahled_pas, user, sn.ident_cely),
        "soubor_smazat": check_permissions(p.actionChoices.soubor_smazat_pas, user, sn.ident_cely),
        "soubor_nahradit": check_permissions(p.actionChoices.soubor_nahradit_pas, user, sn.ident_cely),
        "backtoprojekt": user.is_archeolog_or_more,
        "vypis": check_permissions(p.actionChoices.vypis_pas, user, sn.ident_cely),
    }
    return show


@login_required
@require_http_methods(["POST"])
def post_point_position_2_katastre(request):
    """
    Funkce pro získaní názvu katastru z bodu.

    :param request: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

        :return: Vrací výsledek volání ``JsonResponse()``.
    """
    body = json.loads(request.body.decode("utf-8"))
    logger.debug("pas.views.post_point_position_2_katastre", extra={"data": body})
    katastr_name = get_cadastre_from_point(Point(body["x1"], body["x2"]))
    if katastr_name is not None:
        return JsonResponse(
            {
                "katastr_name": katastr_name.nazev,
            },
            status=200,
        )
    else:
        return JsonResponse({"katastr_name": ""}, status=200)


@login_required
@require_http_methods(["POST"])
def post_point_position_2_katastre_with_geom(request):
    """
    Funkce pro získaní názvu katastru, geomu z bodu.

    :param request: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

        :return: Vrací výsledek volání ``JsonResponse()``.
    """
    body = json.loads(request.body.decode("utf-8"))
    [katastr_name, katastr_db, katastr_geom] = get_cadastre_from_point_with_geometry(Point(body["x1"], body["x2"]))
    if katastr_name is not None:
        return JsonResponse(
            {
                "katastr_name": katastr_name,
                "katastr_db": katastr_db,
                "katastr_geom": katastr_geom,
            },
            status=200,
        )
    else:
        return JsonResponse({"katastr_name": ""}, status=200)


def get_required_fields(zaznam=None, next=0):
    """
    Funkce pro získaní dictionary povinných polí podle stavu samostatného nálezu.

    :param zaznam: Parametr ``zaznam`` pracuje se s atributy ``stav``, ovlivňuje větvení podmínek.
    :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
    :return: Seznam názvů polí, která mají být v daném stavu povinná.
    """
    required_fields = []
    if zaznam:
        stav = zaznam.stav
    else:
        stav = 1
    if stav >= SN_ZAPSANY - next:
        required_fields = [
            "projekt",
        ]
    if stav > SN_ZAPSANY - next:
        required_fields += [
            "lokalizace",
            "datum_nalezu",
            "okolnosti",
            "hloubka",
            "katastr",
            "nalezce",
            "specifikace",
            "obdobi",
            "druh_nalezu",
            "visible_ss_combo",
            "visible_x1",
            "visible_x2",
        ]
    return required_fields


class ProjektPasTableView(LoginRequiredMixin, View):
    """Třída pohledu pro zobrazení řádku tabulky samostatných nálezů."""

    def get(self, request, ident_cely):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
        :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get()``.

            :return: Vrací výsledek volání ``HttpResponse()``.
        """
        projekt = Projekt.objects.get(ident_cely=ident_cely)
        qs = (
            projekt.samostatne_nalezy.select_related("obdobi", "druh_nalezu", "specifikace", "nalezce", "katastr")
            .all()
            .order_by("ident_cely")
        )
        perm_object = PasPermissionFilterMixin()
        perm_object.request = request
        perm_object.typ_zmeny_lookup = ZAPSANI_SN
        qs = perm_object.check_filter_permission(qs, p.actionChoices.projekt_pas_zobrazit)
        context = {"samostatne_nalezy": qs}
        return HttpResponse(render_to_string("pas/samostatne_nalezy_table.html", context))
