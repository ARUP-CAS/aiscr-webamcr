import logging

import simplejson as json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView

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
    ZAPSANI_SN,
    SPOLUPRACE_ZADOST,
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
    SAMOSTATNY_NALEZ_NELZE_ODESLAT,
    SAMOSTATNY_NALEZ_ODESLAN,
    SAMOSTATNY_NALEZ_POTVRZEN,
    SAMOSTATNY_NALEZ_VRACEN,
    SPOLUPRACE_BYLA_AKTIVOVANA,
    SPOLUPRACE_BYLA_DEAKTIVOVANA,
    SPOLUPRACI_NELZE_AKTIVOVAT,
    SPOLUPRACI_NELZE_DEAKTIVOVAT,
    ZADOST_O_SPOLUPRACI_VYTVORENA,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN, ZAZNAM_NELZE_SMAZAT_FEDORA, SAMOSTATNY_NALEZ_NELZE_POTVRDIT,
    SAMOSTATNY_NALEZ_NELZE_ARCHIVOVAT,
)
from core.repository_connector import FedoraRepositoryConnector, FedoraTransaction
from core.utils import (
    get_cadastre_from_point,
    get_cadastre_from_point_with_geometry,
    get_pian_from_envelope,
    get_pas_from_envelope,
    get_num_pian_from_envelope,
    get_dj_pians_from_envelope,
)
from core.views import PermissionFilterMixin, SearchListView, check_stav_changed
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from dokument.forms import CoordinatesDokumentForm
from heslar.hesla_dynamicka import PRISTUPNOST_ARCHEOLOG_ID, TYP_PROJEKTU_PRUZKUM_ID
from heslar.models import Heslar
from historie.models import Historie, HistorieVazby
from pas.filters import SamostatnyNalezFilter, UzivatelSpolupraceFilter
from pas.forms import CreateSamostatnyNalezForm, CreateZadostForm, PotvrditNalezForm
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from pas.tables import SamostatnyNalezTable, UzivatelSpolupraceTable
from services.mailer import Mailer
from uzivatel.models import Organizace, User
from core.models import Permissions as p, check_permissions
from projekt.models import Projekt

logger = logging.getLogger(__name__)


def get_detail_context(sn, request):
    """
    Funkce pro získaní potřebného kontextu pro samostatný nález.
    """
    context = {"sn": sn}
    context["form"] = CreateSamostatnyNalezForm(
        instance=sn, readonly=True, user=request.user
    )
    context["ulozeni_form"] = PotvrditNalezForm(instance=sn, readonly=True)
    context["history_dates"] = get_history_dates(sn.historie, request.user)
    context["show"] = get_detail_template_shows(sn, request.user)
    logger.debug("pas.views.get_detail_context", extra=context)
    if sn.soubory:
        context["soubory"] = sn.soubory.soubory.all().order_by("nazev")
    else:
        context["soubory"] = None
    context["app"] = "pas"
    return context


@login_required
@require_http_methods(["GET"])
def index(request):
    """
    Funkce pohledu pro zobrazení domovské stránky samostatného nálezu s navigačními možnostmi.
    """
    return render(request, "pas/index.html")


@login_required
@require_http_methods(["GET", "POST"])
def create(request, ident_cely=None):
    """
    Funkce pohledu pro vytvoření samostatného nálezu.
    """
    required_fields = get_required_fields()
    required_fields_next = get_required_fields(next=1)
    if request.method == "POST":
        form = CreateSamostatnyNalezForm(
            request.POST,
            user=request.user,
            required=required_fields,
            required_next=required_fields_next,
        )
        form_coor = CoordinatesDokumentForm(
            request.POST,
        )
        if form.is_valid():
            geom = None
            geom_sjtsk = None
            try:
                wgs84_x1 = float(form_coor.data.get("coordinate_wgs84_x1"))
                wgs84_x2 = float(form_coor.data.get("coordinate_wgs84_x2"))
                if wgs84_x1 > 0 and wgs84_x2 > 0:
                    geom = Point(wgs84_x1, wgs84_x2)
                sjtsk_x1 = float(form_coor.data.get("coordinate_sjtsk_x1"))
                sjtsk_x2 = float(form_coor.data.get("coordinate_sjtsk_x2"))
                if sjtsk_x1 < 0 and sjtsk_x2 < 0:
                    geom_sjtsk = Point(sjtsk_x1,sjtsk_x2)
            except Exception:
                logger.info(
                    "pas.views.create.corrd_format_error",
                    extra={"geom": geom, "geom_sjtsk": geom_sjtsk},
                )
            sn: SamostatnyNalez = form.save(commit=False)
            fedora_transaction = FedoraTransaction()
            sn.active_transaction = fedora_transaction
            try:
                sn.ident_cely = get_sn_ident(sn.projekt)
            except MaximalIdentNumberError:
                messages.add_message(request, messages.ERROR, MAXIMUM_IDENT_DOSAZEN)
            else:
                repository_connector = FedoraRepositoryConnector(sn)
                if repository_connector.check_container_deleted_or_not_exists(sn.ident_cely, "samostatny_nalez"):
                    sn.stav = SN_ZAPSANY
                    sn.pristupnost = Heslar.objects.get(id=PRISTUPNOST_ARCHEOLOG_ID)
                    sn.predano_organizace = sn.projekt.organizace
                    sn.geom_system = form_coor.data.get("coordinate_system")
                    if geom is not None:
                        sn.katastr = get_cadastre_from_point(geom)
                        sn.geom = geom
                    if geom_sjtsk is not None:
                        sn.geom_sjtsk = geom_sjtsk
                    sn.save()
                    sn.set_zapsany(request.user)
                    form.save_m2m()
                    sn.close_active_transaction_when_finished = True
                    sn.save()
                    messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
                    return redirect("pas:detail", ident_cely=sn.ident_cely)
                else:
                    logger.info("pas.views.create.check_container_deleted_or_not_exists.incorrect",
                                extra={"ident_cely": sn.ident_cely})
                    messages.add_message(request, messages.ERROR, _("pas.views.zapsat.create."
                                                                    "check_container_deleted_or_not_exists_error"))
                    fedora_transaction.mark_transaction_as_closed()

        else:
            logger.info("pas.views.create.form_invalid", extra={"errors": form.errors})
            messages.add_message(request, messages.ERROR, FORM_NOT_VALID)
    else:
        if ident_cely:
            proj = get_object_or_404(Projekt, ident_cely=ident_cely)
            if proj.typ_projektu.id != TYP_PROJEKTU_PRUZKUM_ID:
                logger.debug("Projekt neni typu pruzkumny")
                messages.add_message(request, messages.SUCCESS, PROJEKT_NENI_TYP_PRUZKUMNY)
                return redirect(proj.get_absolute_url())
        form = CreateSamostatnyNalezForm(
            user=request.user,
            required=required_fields,
            required_next=required_fields_next,
            project_ident=ident_cely,
        )
        form_coor = CoordinatesDokumentForm()
    return render(
        request,
        "pas/create.html",
        {
            "global_map_can_edit": True,
            "formCoor": form_coor,
            "form": form,
            "title": _("pas.views.create.title"),
            "header": _("pas.views.create.header"),
            "button": _("pas.views.create.submitButton.text"),
        },
    )


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    """
    Funkce pohledu pro zobrazení detailu samostatného nálezu.
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
            extra={"sn_geom_system": sn.geom_system, "ident_cely": sn.ident_cely},
        )
        context["formCoor"] = CoordinatesDokumentForm(
            initial=sn.generate_coord_forms_initial()
        )  # Zmen musis poslat data do formulare
        context["global_map_can_edit"] = False
    else:
        context["formCoor"] = CoordinatesDokumentForm()
    return render(request, "pas/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    """
    Funkce pohledu pro editaci samostatného nálezu.
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
                geom_sjtsk = Point(sjtsk_x1,sjtsk_x2)
        except Exception as e:
            logger.info(
                "pas.views.edit.corrd_format_error",
                extra={"geom": geom, "geom_sjtsk": geom_sjtsk},
            )
        if form.is_valid():
            logger.debug("pas.views.edit.form_valid")
            sn.geom_system = form_coor.data.get("coordinate_system")
            if geom is not None:
                sn.katastr = get_cadastre_from_point(geom)
                sn.geom = geom
            if geom_sjtsk is not None:
                sn.geom_sjtsk = geom_sjtsk
            sn: SamostatnyNalez = form.save(commit=False)
            fedora_transaction = FedoraTransaction()
            sn.active_transaction = fedora_transaction
            sn.close_active_transaction_when_finished = True
            sn.save()
            if form.changed_data:
                logger.debug(
                    "pas.views.edit.form_changed_data",
                    extra={"changed_data": form.changed_data},
                )
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return redirect("pas:detail", ident_cely=ident_cely)
        else:
            logger.info(
                "pas.views.edit.form_invalid", extra={"form_errors": form.errors}
            )

    else:
        form = CreateSamostatnyNalezForm(
            instance=sn,
            user=request.user,
            required=required_fields,
            required_next=required_fields_next,
            **kwargs,
        )
        if sn.geom:
            form_coor= CoordinatesDokumentForm(
                initial=sn.generate_coord_forms_initial()
            )
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
@require_http_methods(["GET", "POST"])
def edit_ulozeni(request, ident_cely):
    """
    Funkce pohledu pro editaci uložení samostatného nálezu pomocí modalu.
    """
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    predano_required = True if sn.stav == SN_POTVRZENY else False
    if check_stav_changed(request, sn):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = PotvrditNalezForm(
            request.POST, instance=sn, predano_required=predano_required
        )
        if form.is_valid():
            logger.debug("pas.views.edit_ulozeni.form_valid")
            fedora_transaction = FedoraTransaction()
            sn: SamostatnyNalez = form.save(commit=False)
            sn.predano_organizace = get_object_or_404(
                Organizace, id=sn.projekt.organizace_id
            )
            sn.active_transaction = fedora_transaction
            sn.close_active_transaction_when_finished = True
            sn.save()
            if form.changed_data:
                logger.debug(
                    "pas.views.edit_ulozeni.form_changed_data",
                    extra={"changed_data": form.changed_data},
                )
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return JsonResponse(
                {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})}
            )
        else:
            logger.info(
                "pas.views.edit_ulozeni.form_invalid",
                extra={"form_errors": form.errors},
            )
    else:
        form = PotvrditNalezForm(
            instance=sn,
            predano_required=predano_required,
            initial={"old_stav": sn.stav},
            predano_hidden=True,
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
    """
    sn: SamostatnyNalez = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if not SN_ARCHIVOVANY >= sn.stav > SN_ZAPSANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, sn):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = VratitForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            fedora_transaction = FedoraTransaction()
            sn.active_transaction = fedora_transaction
            sn.set_vracen(request.user, sn.stav - 1, duvod)
            sn.close_active_transaction_when_finished = True
            sn.save()
            Mailer.send_en03_en04(samostatny_nalez=sn, reason=duvod)
            messages.add_message(request, messages.SUCCESS, SAMOSTATNY_NALEZ_VRACEN)
            return JsonResponse(
                {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})}
            )
        else:
            logger.info(
                "pas.views.vratit.form_invalid", extra={"form_errors": form.errors}
            )
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
    """
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
    if sn.stav != SN_ZAPSANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, sn):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        fedora_transaction = FedoraTransaction()
        sn.active_transaction = fedora_transaction
        sn.set_odeslany(request.user)
        sn.close_active_transaction_when_finished = True
        sn.save()
        messages.add_message(request, messages.SUCCESS, SAMOSTATNY_NALEZ_ODESLAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})}
        )

    warnings = sn.check_pred_odeslanim()
    logger.info("pas.views.odeslat.warnings", extra={"warnings": warnings})
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
@require_http_methods(["GET", "POST"])
def potvrdit(request, ident_cely):
    """
    Funkce pohledu pro potvrzení samostatného nálezu pomocí modalu.
    """
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if sn.stav != SN_ODESLANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if check_stav_changed(request, sn):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    warnings = sn.check_pred_odeslanim()
    logger.info("pas.views.potvrdit.warnings", extra={"warnings": warnings})
    if warnings:
        request.session["temp_data"] = warnings
        messages.add_message(request, messages.ERROR, SAMOSTATNY_NALEZ_NELZE_POTVRDIT)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = PotvrditNalezForm(request.POST, instance=sn, predano_required=True)
        if form.is_valid():
            form_obj: SamostatnyNalez = form.save(commit=False)
            fedora_transaction = FedoraTransaction()
            form_obj.active_transaction = fedora_transaction
            form_obj.set_potvrzeny(request.user)
            form_obj.predano_organizace = get_object_or_404(
                Organizace, id=sn.projekt.organizace_id
            )
            form_obj.close_active_transaction_when_finished = True
            form_obj.save()
            messages.add_message(request, messages.SUCCESS, SAMOSTATNY_NALEZ_POTVRZEN)
            return JsonResponse(
                {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})}
            )
        else:
            logger.info(
                "pas.views.potvrdit.form_invalid", extra={"form_errors": form.errors}
            )
    else:
        form = PotvrditNalezForm(
            instance=sn, initial={"old_stav": sn.stav}, predano_hidden=True
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
    """
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if sn.stav != SN_POTVRZENY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, sn):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    warnings = sn.check_pred_odeslanim()
    logger.info("pas.views.archivovat.warnings", extra={"warnings": warnings})
    if warnings:
        request.session["temp_data"] = warnings
        messages.add_message(request, messages.ERROR, SAMOSTATNY_NALEZ_NELZE_ARCHIVOVAT)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        fedora_transaction = FedoraTransaction()
        sn.active_transaction = fedora_transaction
        sn.set_archivovany(request.user)
        sn.close_active_transaction_when_finished = True
        sn.save()
        messages.add_message(request, messages.SUCCESS, SAMOSTATNY_NALEZ_ARCHIVOVAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})}
        )
    else:
        # TODO nejake kontroly? warnings = sn.check_pred_archivaci()
        form_check = CheckStavNotChangedForm(initial={"old_stav": sn.stav})
        context = {
            "object": sn,
            "title": _("pas.views.archivovat.title.text"),
            "id_tag": "archivovat-pas-form",
            "button": _("pas.views.archivovat.submitButton.text"),
            "form_check": form_check,
        }
    return render(request, "core/transakce_modal.html", context)

class PasPermissionFilterMixin(PermissionFilterMixin):
    def add_ownership_lookup(self, ownership, qs):
        filter_historie = {"uzivatel":self.request.user}
        filtered_my = Historie.objects.filter(**filter_historie)
        if ownership == p.ownershipChoices.our:
            return Q(**{"projekt__organizace":self.request.user.organizace})
        else:
            return Q(**{"historie_zapsat__in":filtered_my})


class SamostatnyNalezListView(SearchListView, PasPermissionFilterMixin):
    """
    Třída pohledu pro zobrazení přehledu samostatných nálezu s filtrem v podobe tabulky.
    """

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

    def init_translations(self):
        self.page_title = _("pas.views.samostatnyNalezListView.pageTitle")
        self.search_sum = _("pas.views.samostatnyNalezListView.pocetVyhledanych")
        self.pick_text = _("pas.views.samostatnyNalezListView.pickText")
        self.hasOnlyVybrat_header = _("pas.views.samostatnyNalezListView.header.hasOnlyVybrat")
        self.hasOnlyVlastnik_header = _("pas.views.samostatnyNalezListView.header.hasOnlyVlastnik")
        self.hasOnlyArchive_header = _("pas.views.samostatnyNalezListView.header.hasOnlyArchive")
        self.hasOnlyPotvrdit_header = _("pas.views.samostatnyNalezListView.header.hasOnlyPotvrdit")
        self.default_header = _("pas.views.samostatnyNalezListView.header.default")
        self.toolbar_name = _("pas.views.samostatnyNalezListView.toolbar.title")
        self.toolbar_label = _("pas.views.samostatnyNalezListView.toolbar_label.text")

    @staticmethod
    def rename_field_for_ordering(field: str):
        field = field.replace("-", "")
        return {
            "katastr": "katastr__nazev",
            "nalezce": "nalezce__vypis_cely",
            "predano_organizace": "predano_organizace__nazev_zkraceny",
            "obdobi": "obdobi__razeni",
            "druh_nalezu": "druh_nalezu__razeni",
            "specifikace": "specifikace__razeni",
            "pristupnost": "pristupnost__razeni",
            "okolnosti": "okolnosti__razeni",
        }.get(field, field)

    def get_queryset(self):
        sort_params = self._get_sort_params()
        sort_params = [self.rename_field_for_ordering(x) for x in sort_params]
        qs = super().get_queryset()
        qs = qs.order_by(*sort_params) 
        qs = qs.distinct("pk", *sort_params)
        qs = qs.select_related(            
            "nalezce",           
            "predano_organizace",
            "katastr",
            "katastr__okres",
            "soubory"
        ).prefetch_related( "specifikace","okolnosti","pristupnost","soubory__soubory","obdobi","druh_nalezu",)
        
        return self.check_filter_permission(qs)
    
    



@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    """
    Funkce pohledu pro smazání samostatného nálezu pomocí modalu.
    """
    nalez: SamostatnyNalez = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if check_stav_changed(request, nalez):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        nalez.deleted_by_user = request.user
        nalez.active_transaction = FedoraTransaction()
        nalez.close_active_transaction_when_finished = True
        nalez.record_deletion(nalez.active_transaction)
        resp1 = nalez.delete()
        if resp1:
            logger.info(
                "pas.views.smazat.deleted",
                extra={"resp1": resp1},
            )
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            return JsonResponse({"redirect": reverse("pas:index")})
        else:
            logger.warning(
                "pas.views.smazat.not_deleted", extra={"ident_cely": ident_cely}
            )
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            return JsonResponse(
                {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
                status=403,
            )
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
@require_http_methods(["GET", "POST"])
def zadost(request):
    """
    Funkce pohledu pro vytvoření žádosti o spolupráci.
    """
    if request.method == "POST":
        logger.debug("pas.views.zadost.start")
        form = CreateZadostForm(request.POST)
        if form.is_valid():
            logger.debug("pas.views.zadost.form_valid")
            uzivatel_email = form.cleaned_data["email_uzivatele"]
            uzivatel_text = form.cleaned_data["text"]
            uzivatel = get_object_or_404(User, email=uzivatel_email)
            exists = UzivatelSpoluprace.objects.filter(
                vedouci=uzivatel, spolupracovnik=request.user
            ).exists()

            if uzivatel == request.user:
                messages.add_message(
                    request, messages.ERROR, _("pas.views.zadost.uzivatel.error")
                )
                logger.debug(
                    "pas.views.zadost.post.error",
                    extra={"error": "Nelze vytvořit spolupráci sám se sebou"},
                )
            elif exists:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _(
                        "pas.views.zadost.existuje.error.part1")
                        + uzivatel_email
                        + _("pas.views.zadost.existuje.error.part2"
                    ),
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
                messages.add_message(
                    request, messages.SUCCESS, ZADOST_O_SPOLUPRACI_VYTVORENA
                )
                logger.debug(
                    "pas.views.zadost.post.success",
                    extra={"hv_id": hv.pk, "s_id": s.pk, "hist_id": hist.pk},
                )

                Mailer.send_en05(
                    email_to=uzivatel_email,
                    reason=uzivatel_text,
                    user=request.user,
                    spoluprace_id=s.pk,
                )
                return redirect("pas:spoluprace_list")
        else:
            logger.info(
                "pas.views.zadost.form_invalid", extra={"form_errors": form.errors}
            )
    else:
        form = CreateZadostForm()

    return render(
        request,
        "pas/zadost.html",
        {"title": _("pas.views.zadost.title.text"), "header": _("pas.views.zadost.header.text"), "form": form},
    )


class UzivatelSpolupraceListView(SearchListView):
    """
    Třída pohledu pro zobrazení přehledu spoluprác s filtrem v podobe tabulky.
    """

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
        super().init_translations()
        self.page_title = _("pas.views.uzivatelSpolupraceListView.pageTitle")
        self.search_sum = _("pas.views.uzivatelSpolupraceListView.pocetVyhledanych")
        self.pick_text = _("pas.views.uzivatelSpolupraceListView.pickText")
        self.toolbar_name = _("pas.views.uzivatelSpolupraceListView.toolbar.title")
        self.toolbar_label = _("pas.views.uzivatelSpolupraceListView.toolbar_label.text")

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related(
            "vedouci",
            "spolupracovnik",
            "vedouci__organizace",
            "historie",
            "spolupracovnik__organizace",
        )
        return self.check_filter_permission(qs).order_by("id")
    
    def add_ownership_lookup(self, ownership, qs=None):
        filtered_my = Q(spolupracovnik=self.request.user)
        if ownership == p.ownershipChoices.our:
            filtered_our = Q(vedouci__organizace=self.request.user.organizace)
            return filtered_our | filtered_my
        else:
            return filtered_my
    
    def add_accessibility_lookup(self,permission, qs):
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_zadost"] = check_permissions(p.actionChoices.spoluprace_zadost, self.request.user)
        context["trans_deaktivovat"] = _("pas.templates.aktivace_deaktivace_cell.deaktivovat")
        context["trans_aktivovat"] = _("pas.templates.aktivace_deaktivace_cell.aktivovat")
        context["trans_smazat"] = _("pas.templates.smazat_cell.Smazat")
        return context
    
    def get_table_kwargs(self):
        if self.request.user.hlavni_role.id != ROLE_ADMIN_ID:
            return {
                    'exclude': ('smazani', )
                }
        return {}


@login_required
@require_http_methods(["GET", "POST"])
def aktivace(request, pk):
    """
    Funkce pohledu pro aktivaci spolupráce pomocí modalu.
    """
    spoluprace = get_object_or_404(UzivatelSpoluprace, id=pk)
    if request.method == "POST":
        spoluprace.active_transaction = FedoraTransaction()
        spoluprace.close_active_transaction_when_finished = True
        spoluprace.set_aktivni(request.user)
        messages.add_message(request, messages.SUCCESS, SPOLUPRACE_BYLA_AKTIVOVANA)
        Mailer.send_en06(cooperation=spoluprace)
        return JsonResponse(
            {"redirect": reverse("pas:spoluprace_list")}, status=403
        )
    else:
        warnings = spoluprace.check_pred_aktivaci()
        logger.info("pas.views.aktivace.warnings", extra={"warnings": warnings})
        if warnings:
            messages.add_message(
                request, messages.ERROR, f"{SPOLUPRACI_NELZE_AKTIVOVAT} {warnings[0]}"
            )
            return JsonResponse(
                {"redirect": reverse("pas:spoluprace_list")}, status=403
            )
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
    template_name = "pas/potvrdit_spolupraci.html"
    model = UzivatelSpoluprace

    def post(self, request, *args, **kwargs):
        obj: UzivatelSpoluprace = self.get_object()
        if not obj.aktivni:
            obj.set_aktivni(request.user)
            Mailer.send_en06(cooperation=obj)
        return redirect(reverse("pas:spoluprace_list")+"?sort=organizace_vedouci&sort=spolupracovnik")


@login_required
@require_http_methods(["GET", "POST"])
def deaktivace(request, pk):
    """
    Funkce pohledu pro deaktivaci spolupráce pomocí modalu.
    """
    spoluprace = get_object_or_404(UzivatelSpoluprace, id=pk)
    if request.method == "POST":
        spoluprace.active_transaction = FedoraTransaction()
        spoluprace.close_active_transaction_when_finished = True
        spoluprace.set_neaktivni(request.user)
        messages.add_message(request, messages.SUCCESS, SPOLUPRACE_BYLA_DEAKTIVOVANA)
        return JsonResponse({"redirect": reverse("pas:spoluprace_list")})
    else:
        warnings = spoluprace.check_pred_deaktivaci()
        logger.info("pas.views.deaktivace.warnings", extra={"warnings": warnings})
        if warnings:
            messages.add_message(
                request, messages.ERROR, f"{SPOLUPRACI_NELZE_DEAKTIVOVAT} {warnings[0]}"
            )
            return JsonResponse(
                {"redirect": reverse("pas:spoluprace_list")}, status=403
            )
    context = {
        "object": spoluprace,
        "title": (
            _("pas.views.deaktivace.title.part1")
            + spoluprace.vedouci.email
            + _("pas.views.deaktivace.title.part2")
            + spoluprace.spolupracovnik.email
        ),
        "id_tag": "deaktivace-spoluprace-form",
        "button": _("pas.views.deaktivace.submitButton.text"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def smazat_spolupraci(request, pk):
    """
    Funkce pohledu pro smazání spolupráce pomocí modalu.
    """
    spoluprace = get_object_or_404(UzivatelSpoluprace, id=pk)
    if request.method == "POST":
        spoluprace.active_transaction = FedoraTransaction()
        spoluprace.close_active_transaction_when_finished = True
        resp1 = spoluprace.delete()
        if resp1:
            logger.info(
                "pas.views.smazat_spolupraci.deleted",
                extra={"resp1": resp1},
            )
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            return JsonResponse({"redirect": reverse("pas:spoluprace_list")})
        else:
            logger.warning("pas.views.smazat_spolupraci.not_deleted", extra={"pk": pk})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            return JsonResponse(
                {"redirect": reverse("pas:spoluprace_list")}, status=403
            )
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


def get_history_dates(historie_vazby, request_user):
    """
    Funkce pro získaní historických datumu.
    """
    anonymized = not request_user.hlavni_role.pk in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)
    historie = {
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_SN, anonymized),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_SN, anonymized),
        "datum_potvrzeni": historie_vazby.get_last_transaction_date(POTVRZENI_SN, anonymized),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_SN, anonymized),
    }
    return historie


def get_detail_template_shows(sn, user):
    """
    Funkce pro získaní kontextu pro zobrazování možností na stránkách.
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
        "stahnout_metadata": check_permissions(p.actionChoices.stahnout_metadata, user, sn.ident_cely),
        "soubor_stahnout": check_permissions(p.actionChoices.soubor_stahnout_pas, user, sn.ident_cely),
        "soubor_nahled": check_permissions(p.actionChoices.soubor_nahled_pas, user, sn.ident_cely),
        "soubor_smazat": check_permissions(p.actionChoices.soubor_smazat_pas, user, sn.ident_cely),
        "soubor_nahradit": check_permissions(p.actionChoices.soubor_nahradit_pas, user, sn.ident_cely),
    }
    return show


@login_required
@require_http_methods(["POST"])
def post_point_position_2_katastre(request):
    """
    Funkce pro získaní názvu katastru z bodu.
    """
    body = json.loads(request.body.decode("utf-8"))
    logger.warning("pas.views.post_point_position_2_katastre", extra={"body": body})
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
    """
    body = json.loads(request.body.decode("utf-8"))
    [katastr_name, katastr_db, katastr_geom] = get_cadastre_from_point_with_geometry(
        Point(body["x1"], body["x2"])
    )
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

    Args:
        zaznam (PAS): model samostatního nálezu pro který se dané pole počítají.

        next (int): pokud je poskytnuto číslo tak se jedná o povinné pole pro příští stav.

    Returns:
        required_fields: list polí.
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
