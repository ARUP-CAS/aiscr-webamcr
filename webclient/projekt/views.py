import logging
from datetime import datetime, timedelta

import simplejson as json
from arch_z.models import Akce
from cacheops import invalidate_model
from core.constants import (
    ARCHIVACE_PROJ,
    AZ_STAV_ZAPSANY,
    D_STAV_ARCHIVOVANY,
    D_STAV_ZAPSANY,
    NAVRZENI_KE_ZRUSENI_PROJ,
    OBLAST_CECHY,
    OZNAMENI_PROJ,
    OZNAMENI_PROJ_MANUALNI,
    PRIHLASENI_PROJ,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
    PROJEKT_STAV_OZNAMENY,
    PROJEKT_STAV_PRIHLASENY,
    PROJEKT_STAV_UKONCENY_V_TERENU,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_VYTVORENY,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    PROJEKT_STAV_ZAPSANY,
    PROJEKT_STAV_ZRUSENY,
    ROLE_ADMIN_ID,
    ROLE_ARCHEOLOG_ID,
    ROLE_ARCHIVAR_ID,
    RUSENI_PROJ,
    RUSENI_STARE_PROJ,
    SCHVALENI_OZNAMENI_PROJ,
    SN_ARCHIVOVANY,
    UKONCENI_V_TERENU_PROJ,
    UZAVRENI_PROJ,
    VRACENI_NAVRHU_ZRUSENI,
    VRACENI_ZRUSENI,
    ZAHAJENI_V_TERENU_PROJ,
    ZAPSANI_PROJ,
    ZAPSANI_SN,
)
from core.coordTransform import convertToJTSK
from core.decorators import allowed_user_groups
from core.exceptions import MaximalIdentNumberError
from core.forms import CheckStavNotChangedForm, VratitForm
from core.message_constants import (
    DATUM_OZNAMENI_SE_NEPOVEDLO_EDITOVAT,
    MAXIMUM_IDENT_DOSAZEN,
    PRISTUP_ZAKAZAN,
    PROJEKT_NELZE_ARCHIVOVAT,
    PROJEKT_NELZE_NAVRHNOUT_KE_ZRUSENI,
    PROJEKT_NELZE_SMAZAT,
    PROJEKT_NELZE_UZAVRIT,
    PROJEKT_NELZE_ZAHAJIT_V_TERENU,
    PROJEKT_NENI_TYP_PRUZKUMNY,
    PROJEKT_NENI_TYP_ZACHRANNY,
    PROJEKT_USPESNE_ARCHIVOVAN,
    PROJEKT_USPESNE_NAVRZEN_KE_ZRUSENI,
    PROJEKT_USPESNE_PRIHLASEN,
    PROJEKT_USPESNE_SCHVALEN,
    PROJEKT_USPESNE_UKONCEN_V_TERENU,
    PROJEKT_USPESNE_UZAVREN,
    PROJEKT_USPESNE_VRACEN,
    PROJEKT_USPESNE_ZAHAJEN_V_TERENU,
    PROJEKT_USPESNE_ZRUSEN,
    PROJEKT_ZADOST_ODHLASENI_PROJEKTU_ERROR,
    PROJEKT_ZADOST_ODHLASENI_PROJEKTU_SUCCESS,
    PROJEKT_ZADOST_UDAJE_OZNAMOVATEL_ERROR,
    PROJEKT_ZADOST_UDAJE_OZNAMOVATEL_SUCCESS,
    PROJEKT_ZADOST_ZRUSENI_PROJEKTU_ERROR,
    PROJEKT_ZADOST_ZRUSENI_PROJEKTU_SUCCESS,
    SPATNY_ZAZNAM_ZAZNAM_VAZBA,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from core.models import Permissions
from core.models import Permissions as p
from core.models import check_permissions
from core.repository_connector import FedoraError, FedoraRepositoryConnector, FedoraTransaction
from core.utils import (
    get_heatmap_project,
    get_num_projects_from_envelope,
    get_project_geom,
    get_project_pas_from_envelope,
    get_project_pian_from_envelope,
    get_projects_from_envelope,
    get_timezone,
)
from core.views import PermissionFilterMixin, SearchListView, check_stav_changed
from dal import autocomplete
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Length
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.generic import RedirectView, TemplateView
from dokument.models import Dokument, DokumentCast
from dokument.views import odpojit, pripojit
from fedora_management.decorators import handle_fedora_error
from heslar.hesla import HESLAR_PRISTUPNOST
from heslar.hesla_dynamicka import TYP_PROJEKTU_PRUZKUM_ID, TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar, RuianKatastr
from historie.models import Historie
from oznameni.forms import OznamovatelProjektCreateForm
from pas.models import SamostatnyNalez
from pas.views import PasPermissionFilterMixin
from pian.views import PianPermissionFilterMixin
from pid.exceptions import DoiWriteError
from projekt.filters import ProjektFilter
from projekt.forms import (
    CreateProjektForm,
    EditProjektForm,
    GenerovatExpertniListForm,
    GenerovatNovePotvrzeniForm,
    NavrhnoutZruseniProjektForm,
    NeodeslatMailForm,
    PrihlaseniProjektForm,
    UkoncitVTerenuForm,
    UpravitDatumOznameniForm,
    ZadostProjektForm,
    ZahajitVTerenuForm,
    ZruseniProjektForm,
)
from projekt.models import Projekt
from projekt.tables import ProjektTable
from services.mailer import Mailer
from uzivatel.forms import OsobaForm
from uzivatel.models import User

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def index(request):
    """
    Funkce pohledu pro zobrazení indexu s navigací projektu.

    :param request: Aktuální HTTP request předaný view/funkci.
    """
    return render(request, "projekt/index.html")


@never_cache
@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    """
    Funkce pohledu pro zobrazení detailu projektu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    context = {"warnings": request.session.pop("temp_data", None)}
    projekt = get_object_or_404(
        Projekt.objects.select_related("kulturni_pamatka", "typ_projektu", "vedouci_projektu", "organizace"),
        ident_cely=ident_cely,
    )
    context["projekt"] = projekt
    typ_projektu = projekt.typ_projektu
    if typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID and projekt.has_oznamovatel():
        context["oznamovatel"] = projekt.oznamovatel
    elif typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID:
        qs = (
            projekt.samostatne_nalezy.select_related("obdobi", "druh_nalezu", "specifikace", "nalezce", "katastr")
            .all()
            .order_by("ident_cely")
        )
        perm_object = PasPermissionFilterMixin()
        perm_object.request = request
        perm_object.typ_zmeny_lookup = ZAPSANI_SN
        qs = perm_object.check_filter_permission(qs, p.actionChoices.projekt_pas_zobrazit)
        context["samostatne_nalezy"] = qs

    akce = (
        Akce.objects.filter(projekt=projekt)
        .select_related("archeologicky_zaznam__pristupnost", "hlavni_typ")
        .order_by("archeologicky_zaznam__ident_cely")
    )
    dokumenty = (
        Dokument.objects.filter(casti__projekt__ident_cely=ident_cely)
        .select_related("soubory")
        .prefetch_related("soubory__soubory")
    ).order_by("ident_cely")
    context["akce"] = akce
    soubory = projekt.soubory.soubory.all().order_by("nazev")
    context["soubory"] = soubory
    context["dalsi_katastry"] = projekt.katastry.all()
    context["history_dates"] = get_history_dates(projekt.historie, request.user)
    context["show"] = get_detail_template_shows(projekt, request.user)
    context["dokumenty"] = dokumenty
    context["generovatNovePotvrzeniForm"] = GenerovatNovePotvrzeniForm()
    context["generovat_expertni_list_form"] = GenerovatExpertniListForm()

    return render(request, "projekt/detail.html", context)


# @csrf_exempt
@login_required
@require_http_methods(["POST"])
def post_ajax_get_projects_limit(request):
    """
    Funkce pohledu pro získaní heatmapy projektu.

    :param request: Aktuální HTTP request předaný view/funkci.
    """
    body = json.loads(request.body.decode("utf-8"))
    vrstvy_map = {"p1": [1], "p2": [2], "p3": [3], "p46": [4, 5, 6], "p78": [7, 8]}
    aktivni_p = []
    for key, hodnoty in vrstvy_map.items():
        if body.get(key):
            aktivni_p.extend(hodnoty)
    num = get_num_projects_from_envelope(
        body["southEast"]["lng"],
        body["northWest"]["lat"],
        body["northWest"]["lng"],
        body["southEast"]["lat"],
        aktivni_p,
        request,
    )
    logger.debug("projekt.views.post_ajax_get_projects_limit.num", extra={"number": num})
    if num < 5000:
        pians = get_projects_from_envelope(
            body["southEast"]["lng"],
            body["northWest"]["lat"],
            body["northWest"]["lng"],
            body["southEast"]["lat"],
            aktivni_p,
            request,
        )
        if len(pians) > 0:
            return JsonResponse({"points": list(pians), "algorithm": "detail"}, status=200)
        else:
            return JsonResponse({"points": [], "algorithm": "detail"}, status=200)
    else:
        heats = get_heatmap_project(
            body["southEast"]["lng"],
            body["northWest"]["lat"],
            body["northWest"]["lng"],
            body["southEast"]["lat"],
            body["zoom"],
        )
        if len(heats) > 0:
            return JsonResponse({"heat": list(heats), "algorithm": "heat"}, status=200)
        else:
            return JsonResponse({"heat": [], "algorithm": "heat"}, status=200)


@login_required
@require_http_methods(["POST"])
def post_ajax_get_project_one(request):
    """
    Funkce pohledu pro získaní geometrie projektu.

    :param request: Aktuální HTTP request předaný view/funkci.
    """
    body = json.loads(request.body.decode("utf-8"))
    pians = get_project_geom(
        body["projekt_ident_cely"],
    )
    back = []
    for pian in pians:
        back.append({"id": pian.id, "ident_cely": pian.ident_cely, "geom": pian.geom.wkt.replace(", ", ",")})
    if len(pians) > 0:
        return JsonResponse({"points": back, "algorithm": "detail"}, status=200)
    else:
        return JsonResponse({"points": [], "algorithm": "detail"}, status=200)


class ProjectPasFromEnvelopeView(LoginRequiredMixin, View, PasPermissionFilterMixin):
    """Trida pohledu pro získaní heatmapy pas."""

    typ_zmeny_lookup = ZAPSANI_SN

    def post(self, request):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Django HTTP požadavek použitý při zpracování.
        """
        body = json.loads(request.body.decode("utf-8"))
        pians = get_project_pas_from_envelope(
            body["southEast"]["lng"],
            body["northWest"]["lat"],
            body["northWest"]["lng"],
            body["southEast"]["lat"],
            body["projekt_ident_cely"],
        )
        if pians.count() > 0:
            pians = self.check_filter_permission(pians)
        back = []
        for pian in pians:
            back.append({"id": pian.id, "ident_cely": pian.ident_cely, "geom": pian.geom.wkt.replace(", ", ",")})
        if len(pians) > 0:
            return JsonResponse({"points": back, "algorithm": "detail"}, status=200)
        else:
            return JsonResponse({"points": [], "algorithm": "detail"}, status=200)


class ProjectPianFromEnvelopeView(LoginRequiredMixin, View, PianPermissionFilterMixin):
    """
    @jiri-bartos presunuto z post_ajax_get_project_pas_limit

    Trida pohledu pro získaní heatmapy pianu.
    """

    def post(self, request):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Django HTTP požadavek použitý při zpracování.
        """
        body = json.loads(request.body.decode("utf-8"))
        queries = get_project_pian_from_envelope(
            body["southEast"]["lng"],
            body["northWest"]["lat"],
            body["northWest"]["lng"],
            body["southEast"]["lat"],
            body["projekt_ident_cely"],
        )
        queries = self.check_filter_permission(queries)
        back = []
        back_ident_cely = []
        for pian in queries:
            if pian.ident_cely not in back_ident_cely:
                back_ident_cely.append(pian.ident_cely)
                back.append(
                    {
                        "id": pian.id,
                        "ident_cely": pian.ident_cely,
                        "geom": pian.geom.wkt.replace(", ", ","),
                        "presnost": pian.presnost.zkratka,
                    }
                )
        if len(back_ident_cely) > 0:
            return JsonResponse({"points": back, "algorithm": "detail"}, status=200)
        else:
            return JsonResponse({"points": [], "algorithm": "detail"}, status=200)


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def create(request):
    """
    @jiri-bartos presunuto z post_ajax_get_project_pian_limit upraveno na queryset

    Funkce pohledu pro vytvoření projektu.

    :param request: Aktuální HTTP request předaný view/funkci.
    """
    logger.debug("projekt.views.create.start")
    required_fields = get_required_fields()
    required_fields_next = get_required_fields(next=1)
    if request.method == "POST":
        request.POST = katastr_text_to_id(request)
        form_projekt = CreateProjektForm(request.POST, required=required_fields, required_next=required_fields_next)
        if request.POST["typ_projektu"] == TYP_PROJEKTU_ZACHRANNY_ID:
            required = True
        else:
            required = False
        form_oznamovatel = OznamovatelProjektCreateForm(request.POST, required=required)
        if form_projekt.is_valid():
            logger.debug("projekt.views.create.form_valid")
            x2 = form_projekt.cleaned_data["coordinate_x2"]
            x1 = form_projekt.cleaned_data["coordinate_x1"]
            projekt = form_projekt.save(commit=False)
            if projekt.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID:
                # Kontrola oznamovatele
                if not form_oznamovatel.is_valid():
                    logger.debug("projekt.views.create.form_not_valid", extra={"error": form_oznamovatel.errors})
                    return render(
                        request,
                        "projekt/create.html",
                        {
                            "form_projekt": form_projekt,
                            "form_oznamovatel": form_oznamovatel,
                            "title": _("projekt.views.create.title.text"),
                            "header": _("projekt.views.create.header.text"),
                            "button": _("projekt.views.create.submitButton.text"),
                        },
                    )
            fedora_transaction: FedoraTransaction = projekt.create_transaction(request.user, ZAZNAM_USPESNE_VYTVOREN)
            if x1 and x2:
                projekt.geom = Point(x1, x2)
                projekt.geom_sjtsk = Point(*convertToJTSK(x1, x2))
                projekt.geom_system = "5514"
            try:
                projekt.set_permanent_ident_cely(False)
            except MaximalIdentNumberError:
                fedora_transaction.error_message = MAXIMUM_IDENT_DOSAZEN
                fedora_transaction.rollback_transaction()
            else:
                repository_connector = FedoraRepositoryConnector(projekt, skip_container_check=False)
                if repository_connector.check_container_deleted_or_not_exists(projekt.ident_cely, "projekt"):
                    projekt.save()
                    projekt.set_zapsany(request.user)
                    form_projekt.save_m2m()
                    if projekt.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID:
                        # Vytvoření oznamovatele – formulář je už zkontrolovaný na začátku.
                        oznamovatel = form_oznamovatel.save(commit=False)
                        oznamovatel.active_transaction = fedora_transaction
                        oznamovatel.projekt = projekt
                        oznamovatel.save()
                        if form_oznamovatel.cleaned_data["send_mail"]:
                            if projekt.should_generate_confirmation_document:
                                rep_bin_file = projekt.create_confirmation_document(
                                    fedora_transaction, user=request.user
                                )
                            else:
                                rep_bin_file = True
                            projekt.send_ep01(rep_bin_file)

                    projekt.close_active_transaction_when_finished = True
                    projekt.save()
                    return redirect("projekt:detail", ident_cely=projekt.ident_cely)
                else:
                    fedora_transaction.rollback_transaction()
                    logger.debug(
                        "projekt.views.create.check_container_deleted_or_not_exists.incorrect",
                        extra={"ident_cely": projekt.ident_cely},
                    )
                    messages.add_message(
                        request,
                        messages.ERROR,
                        _("arch_z.views.zapsat.samostatnaAkce." "check_container_deleted_or_not_exists_error"),
                    )
        else:
            logger.debug("projekt.views.create.form_projekt_not_valid", extra={"error": str(form_projekt.errors)})
    else:
        form_projekt = CreateProjektForm(required=required_fields, required_next=required_fields_next)
        form_oznamovatel = OznamovatelProjektCreateForm(uzamknout_formular=True)
    return render(
        request,
        "projekt/create.html",
        {
            "form_projekt": form_projekt,
            "form_oznamovatel": form_oznamovatel,
            "title": _("projekt.views.create.title.text"),
            "header": _("projekt.views.create.header.text"),
            "button": _("projekt.views.create.submitButton.text"),
        },
    )


@never_cache
@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    """
    Funkce pohledu pro editaci projektu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    required_fields = get_required_fields(projekt)
    required_fields_next = get_required_fields(projekt, 1)
    edit_fields = None
    edit_geom = True
    if request.user.hlavni_role.id == ROLE_ARCHEOLOG_ID:
        if projekt.stav == PROJEKT_STAV_PRIHLASENY:
            edit_fields = [
                "vedouci_projektu",
                "uzivatelske_oznaceni",
                "kulturni_pamatka",
                "kulturni_pamatka_cislo",
                "kulturni_pamatka_popis",
                "hlavni_katastr",
                "coordinate_x1",
                "coordinate_x2",
                "katastry",
            ]
        elif projekt.stav in [PROJEKT_STAV_ZAHAJENY_V_TERENU, PROJEKT_STAV_UKONCENY_V_TERENU]:
            edit_fields = ["uzivatelske_oznaceni"]
        if projekt.stav >= PROJEKT_STAV_ZAHAJENY_V_TERENU:
            edit_geom = False
    if request.method == "POST":
        if request.POST.get("hlavni_katastr") is not None:
            request.POST = katastr_text_to_id(request)
        form = EditProjektForm(
            request.POST,
            instance=projekt,
            required=required_fields,
            required_next=required_fields_next,
            edit_fields=edit_fields,
        )
        if form.is_valid():
            logger.debug("projekt.views.edit.form_valid")
            if (form.fields["coordinate_x1"].disabled or form.fields["coordinate_x2"].disabled) and (
                projekt.geom is not None and len(projekt.geom) > 0
            ):
                x1 = projekt.geom.coords[0]
                x2 = projekt.geom.coords[1]
            else:
                x1 = form.cleaned_data["coordinate_x1"]
                x2 = form.cleaned_data["coordinate_x2"]
            # Obcházení kontroly změny lon/lat; důležitá je pouze geometrie.
            form.fields["coordinate_x1"].initial = x1
            form.fields["coordinate_x2"].initial = x2
            fedora_transaction = projekt.create_transaction(request.user)
            fedora_transaction.redirect_on_error = True
            projekt = form.save(commit=False)
            projekt.save()
            old_geom = projekt.geom
            if x1 and x2:
                new_geom = Point(x1, x2)
                if old_geom is None or new_geom.coords != old_geom.coords:
                    projekt.geom = new_geom
                    projekt.geom_sjtsk = Point(*convertToJTSK(x1, x2))
                    projekt.save()
                    logger.debug("projekt.views.edit.form_valid.geom_updated", extra={"geom": projekt.geom})
                else:
                    logger.warning("projekt.views.edit.form_valid.geom_not_updated")
            projekt.close_active_transaction_when_finished = True
            projekt.save()
            form.save_m2m()
            invalidate_model(Projekt)
            invalidate_model(Akce)
            return redirect("projekt:detail", ident_cely=ident_cely)
        else:
            logger.debug("projekt.views.edit.form_valid.form_not_valid", extra={"error": form.errors})

    else:
        form = EditProjektForm(
            instance=projekt, required=required_fields, required_next=required_fields_next, edit_fields=edit_fields
        )
        if projekt.geom is not None and len(projekt.geom) > 0:
            form.fields["coordinate_x1"].initial = projekt.geom.coords[0]
            form.fields["coordinate_x2"].initial = projekt.geom.coords[1]
        else:
            logger.debug("projekt.views.edit.empty")
    return render(
        request,
        "projekt/edit.html",
        {"form_projekt": form, "projekt": projekt, "edit_geom": edit_geom},
    )


@login_required
@allowed_user_groups([ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID])
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    """
    Funkce pohledu pro smazání projektu pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    projekt: Projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        projekt.create_transaction(request.user, ZAZNAM_USPESNE_SMAZAN)
        projekt.initial_dokumenty = list(projekt.casti_dokumentu.all().values_list("dokument__id", flat=True))
        projekt.close_active_transaction_when_finished = True
        projekt.deleted_by_user = request.user
        projekt.record_deletion()
        projekt.delete()
        return JsonResponse({"redirect": reverse("projekt:index")})
    else:
        warnings = projekt.check_pred_smazanim()
        if warnings:
            request.session["temp_data"] = warnings
            messages.add_message(request, messages.ERROR, PROJEKT_NELZE_SMAZAT)
            return JsonResponse(
                {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
                status=403,
            )
        form_check = CheckStavNotChangedForm(initial={"old_stav": projekt.stav})
        context = {
            "object": projekt,
            "title": _("projekt.views.smazat.title.text"),
            "id_tag": "smazat-form",
            "button": _("projekt.views.smazat.submitButton.text"),
            "form_check": form_check,
        }
        return render(request, "core/transakce_modal.html", context)


class ProjektPermissionFilterMixin(PermissionFilterMixin):
    """Implementuje komponentu ``ProjektPermissionFilterMixin`` v rámci aplikace."""

    def add_ownership_lookup(self, ownership, qs=None):
        """
        Provádí operaci add ownership lookup.

        :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
        :param qs: Vstupní queryset, který má být dále zpracován.
        """
        if ownership == Permissions.ownershipChoices.our:
            return Q(**{"organizace": self.request.user.organizace})
        else:
            return Q()

    def add_accessibility_lookup(self, permission, qs):
        """
        Provádí operaci add accessibility lookup.

        :param permission: Typová nebo konfigurační hodnota `permission` určující cílovou logiku.
        :param qs: Vstupní queryset, který má být dále zpracován.
        """
        accessibility_key = "pristupnost_snapshot__in"
        accessibilities = Heslar.objects.filter(
            nazev_heslare=HESLAR_PRISTUPNOST, id__in=self.group_to_accessibility.get(self.request.user.hlavni_role.id)
        )
        query_filter = {accessibility_key: accessibilities}
        return qs.filter(Q(**query_filter) | self.add_ownership_lookup(permission.accessibility))


class ProjektListView(SearchListView, ProjektPermissionFilterMixin):
    """Třida pohledu pro zobrazení listu/tabulky s projektami."""

    table_class = ProjektTable
    model = Projekt
    template_name = "projekt/projekt_list.html"
    filterset_class = ProjektFilter
    export_name = "export_projekty_"
    app = "projekt"
    toolbar = "toolbar_projekt.html"
    typ_zmeny_lookup = ZAPSANI_PROJ
    redis_snapshot_prefix = "projekt"
    redis_value_list_field = "ident_cely"
    vypis_app = "projekt"

    def init_translations(self):
        """Provádí operaci init translations."""
        super().init_translations()
        self.page_title = _("projekt.views.projektListView.pageTitle")
        self.search_sum = _("projekt.views.projektListView.pocetVyhledanych")
        self.pick_text = _("projekt.views.projektListView.pickText")
        self.hasOnlyVybrat_header = _("projekt.views.projektListView.header.hasOnlyVybrat")
        self.hasOnlyArchive_header = _("projekt.views.projektListView.header.hasOnlyArchive")
        self.default_header = _("projekt.views.projektListView.header.default")

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        context = super().get_context_data(**kwargs)
        context["hasSchvalitOznameni_header"] = _("projekt.views.projektListView.header.hasSchvalitOznameni")
        context["hasPrihlasit_header"] = _("projekt.views.projektListView.header.hasPrihlasit")
        context["hasPrihlasit_header"] = _("projekt.views.projektListView.header.hasPrihlasit")
        context["hasZahajitVyzkum_header"] = _("projekt.views.projektListView.header.hasZahajitVyzkum")
        context["hasUkoncitTeren_header"] = _("projekt.views.projektListView.header.hasUkoncitTeren")
        context["hasSpravovatAkce_header"] = _("projekt.views.projektListView.header.hasSpravovatAkce")
        context["hasUzavritProjekt_header"] = _("projekt.views.projektListView.header.hasUzavritProjekt")
        context["hasNaseProjekty_header"] = _("projekt.views.projektListView.header.hasNaseProjekty")
        context["hasOnlyZrusit_header"] = _("projekt.views.projektListView.header.hasZrusitProjekty")
        context["has_header"] = _("projekt.views.projektListView.header.hasNaseProjekty")
        return context

    def get_queryset(self):
        """Vrací queryset. v aplikaci."""
        qs = super().get_queryset()
        qs = qs.order_by(*self._get_sort_params())
        qs = (
            qs.filter(stav__gt=PROJEKT_STAV_VYTVORENY)
            .select_related(
                "kulturni_pamatka",
                "typ_projektu",
                "hlavni_katastr",
                "organizace",
                "vedouci_projektu",
                "hlavni_katastr__okres__kraj",
            )
            .prefetch_related("katastry__okres__kraj")
            .defer("geom")
        )
        return self.check_filter_permission(qs)


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def schvalit(request, ident_cely):
    """
    Funkce pohledu pro schválení projektu pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    logger.debug("projekt.views.schvalit.start", extra={"ident_cely": ident_cely})
    projekt: Projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_OZNAMENY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentálně zbytečné, případná chyba se propaguje výše.
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        logger.debug("projekt.views.schvalit.post.start", extra={"ident_cely": ident_cely})
        old_ident = projekt.ident_cely
        fedora_transaction = projekt.create_transaction(request.user, PROJEKT_USPESNE_SCHVALEN)
        if projekt.ident_cely[0] == "X":
            try:
                projekt.set_permanent_ident_cely()
            except MaximalIdentNumberError:
                logger.debug("projekt.views.schvalit.post.max_error", extra={"ident_cely": ident_cely})
                fedora_transaction.error_message = MAXIMUM_IDENT_DOSAZEN
                fedora_transaction.rollback_transaction()
                return JsonResponse(
                    {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
                    status=403,
                )
            else:
                logger.debug(
                    "projekt.views.schvalit.perm_ident",
                    extra={"ident_cely_old": old_ident, "ident_cely": projekt.ident_cely},
                )
        projekt.set_schvaleny(request.user, old_ident)
        form = NeodeslatMailForm(request.POST)
        if form.is_valid():
            send_mail = form.cleaned_data["send_mail"]  # Získání hodnoty checkboxu
            if send_mail:
                if projekt.typ_projektu.pk == TYP_PROJEKTU_ZACHRANNY_ID:
                    rep_bin_file = projekt.create_confirmation_document(fedora_transaction, user=request.user)
                else:
                    rep_bin_file = None
                projekt.send_ep01(rep_bin_file)
        projekt.close_active_transaction_when_finished = True
        projekt.save()
        logger.debug(
            "projekt.views.schvalit.post.done",
            extra={"ident_cely_old": old_ident, "ident_cely": ident_cely, "transaction": fedora_transaction.uid},
        )
        return JsonResponse({"redirect": reverse("projekt:detail", kwargs={"ident_cely": projekt.ident_cely})})
    form_check = CheckStavNotChangedForm(initial={"old_stav": projekt.stav})
    form = NeodeslatMailForm(initial={"send_mail": True})
    context = {
        "object": projekt,
        "title": _("projekt.views.schvalit.title.text"),
        "form": form,
        "id_tag": "schvalit-form",
        "button": _("projekt.views.schvalit.submitButton.text"),
        "form_check": form_check,
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def prihlasit(request, ident_cely):
    """
    Funkce pohledu pro přihlášení projektu pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_ZAPSANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentálně zbytečné, případná chyba se propaguje výše.
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if not request.user.organizace.oao:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    archivar = not request.user.is_archiver_or_more
    if request.method == "POST":
        if archivar:
            form = PrihlaseniProjektForm(
                request.POST, instance=projekt, initial={"organizace": request.user.organizace}, archivar=archivar
            )
        else:
            form = PrihlaseniProjektForm(request.POST, instance=projekt)
        if form.is_valid():
            projekt: Projekt = form.save(commit=False)
            projekt.create_transaction(request.user, PROJEKT_USPESNE_PRIHLASEN)
            projekt.set_prihlaseny(request.user)
            if projekt.ident_cely[0] == OBLAST_CECHY:
                Mailer.send_ep03a(project=projekt)
            else:
                Mailer.send_ep03b(project=projekt)
            projekt.close_active_transaction_when_finished = True
            projekt.save()
            return JsonResponse({"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})})
        else:
            logger.debug("projekt.views.prihlasit.form_not_valid", extra={"error": form.errors})
    else:
        form = PrihlaseniProjektForm(
            instance=projekt,
            initial={"organizace": request.user.organizace, "old_stav": projekt.stav},
            archivar=archivar,
        )
    osoba_form = OsobaForm()
    return render(
        request,
        "projekt/prihlasit.html",
        {"form": form, "projekt": projekt, "osoba_form": osoba_form},
    )


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def zahajit_v_terenu(request, ident_cely):
    """
    Funkce pohledu pro zahájení v terenu projektu pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_PRIHLASENY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    warnings = projekt.check_pred_zahajenim_v_terenu()
    if warnings:
        request.session["temp_data"] = warnings
        messages.add_message(request, messages.ERROR, PROJEKT_NELZE_ZAHAJIT_V_TERENU)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentálně zbytečné, případná chyba se propaguje výše.
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = ZahajitVTerenuForm(request.POST, instance=projekt)

        if form.is_valid():
            projekt = form.save(commit=False)
            projekt.create_transaction(request.user, PROJEKT_USPESNE_ZAHAJEN_V_TERENU)
            projekt.set_zahajeny_v_terenu(request.user, form.cleaned_data["info_text"])
            kraje_s_emailem = projekt.get_kraje_s_emailem()
            if kraje_s_emailem.count() > 0 and form.cleaned_data["poslat_email_kraj"] == "True":
                Mailer.send_ep09(projekt, form.cleaned_data["info_text"], request.user, kraje_s_emailem)
            projekt.close_active_transaction_when_finished = True
            projekt.save()
            return JsonResponse({"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})})
        else:
            logger.debug("projekt.views.zahajit_v_terenu.form_not_valid", extra={"error": str(form.errors)})
    else:
        form = ZahajitVTerenuForm(instance=projekt, initial={"old_stav": projekt.stav})
    return render(
        request,
        "projekt/transakce_v_terenu.html",
        {
            "form": form,
            "object": projekt,
            "title": _("projekt.views.zahajitvTerenu.title.text"),
            "id_tag": "zahajit-v-terenu-form",
            "button": _("projekt.views.zahajitvTerenu.submitButton.text"),
        },
    )


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def ukoncit_v_terenu(request, ident_cely):
    """
    Funkce pohledu pro ukončení v terenu projektu pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_ZAHAJENY_V_TERENU:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentálně zbytečné, případná chyba se propaguje výše.
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = UkoncitVTerenuForm(request.POST, instance=projekt)
        if form.is_valid():
            projekt = form.save(commit=False)
            projekt.create_transaction(request.user, PROJEKT_USPESNE_UKONCEN_V_TERENU)
            projekt.set_ukoncen_v_terenu(request.user, form.cleaned_data["info_text"])
            kraje_s_emailem = projekt.get_kraje_s_emailem()
            if kraje_s_emailem.count() > 0 and form.cleaned_data["poslat_email_kraj"] == "True":
                Mailer.send_ep10(projekt, form.cleaned_data["info_text"], request.user, kraje_s_emailem)
            projekt.close_active_transaction_when_finished = True
            projekt.save()
            return JsonResponse({"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})})
        else:
            logger.debug("projekt.views.ukoncit_v terenu.form_not_valid", extra={"error": form.errors})
    else:
        form = UkoncitVTerenuForm(instance=projekt, initial={"old_stav": projekt.stav})
    return render(
        request,
        "projekt/transakce_v_terenu.html",
        {
            "form": form,
            "object": projekt,
            "title": _("projekt.views.ukoncitvTerenu.title.text"),
            "id_tag": "ukoncit-v-terenu-form",
            "button": _("projekt.views.ukoncitvTerenu.submitButton.text"),
        },
    )


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def uzavrit(request, ident_cely):
    """
    Funkce pohledu pro uzavření projektu pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_UKONCENY_V_TERENU:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentálně zbytečné, případná chyba se propaguje výše.
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        # Přesuň všechny akce do stavu A2.
        fedora_transaction = projekt.create_transaction(request.user, PROJEKT_USPESNE_UZAVREN)
        akce_query = Akce.objects.filter(projekt=projekt)
        for akce in akce_query:
            if akce.archeologicky_zaznam.stav == AZ_STAV_ZAPSANY:
                logger.debug(
                    "projekt.views.uzavrit.set_a2",
                    extra={"ident_cely": ident_cely, "transaction": fedora_transaction.uid},
                )
                akce.archeologicky_zaznam.active_transaction = fedora_transaction
                akce.archeologicky_zaznam.set_odeslany(request.user, request, messages)
            for dokument_cast in akce.archeologicky_zaznam.casti_dokumentu.all():
                if dokument_cast.dokument.stav == D_STAV_ZAPSANY:
                    logger.debug(
                        "projekt.views.uzavrit.set_d2",
                        extra={"ident_cely": ident_cely, "transaction": fedora_transaction.uid},
                    )
                    dokument: Dokument = dokument_cast.dokument
                    old_ident = dokument.ident_cely
                    dokument.active_transaction = fedora_transaction
                    Dokument.set_permanent_identificator(dokument, request, messages, fedora_transaction)
                    dokument.set_odeslany(request.user, old_ident)
        projekt.set_uzavreny(request.user)
        projekt.close_active_transaction_when_finished = True
        projekt.save()
        return JsonResponse({"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})})
    else:
        # Ověří obchodní pravidla před uzavřením projektu.
        warnings = projekt.check_pred_uzavrenim()
        logger.debug("projekt.views.uzavrit.warnings", extra={"warning": str(warnings)})
        form_check = CheckStavNotChangedForm(initial={"old_stav": projekt.stav})
        if warnings:
            request.session["temp_data"] = []
            for key, item in warnings.items():
                if key == "has_event":
                    request.session["temp_data"].append(item)
                else:
                    request.session["temp_data"].append(f"{key}: {item}")
            messages.add_message(request, messages.ERROR, PROJEKT_NELZE_UZAVRIT)
            return JsonResponse(
                {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
                status=403,
            )
        if request.GET.get("from_arch") == "true":
            context = {
                "object": projekt,
                "title": _("projekt.views.uzavrit.fromAkce.title.text"),
                "text": _("projekt.views.uzavrit.fromAkce.text"),
                "id_tag": "uzavrit-form",
                "button": _("projekt.views.uzavrit.fromAkce.submitButton.text"),
                "form_check": form_check,
            }
        else:
            context = {
                "object": projekt,
                "title": _("projekt.views.uzavrit.title.text"),
                "id_tag": "uzavrit-form",
                "button": _("projekt.views.uzavrit.submitButton.text"),
                "form_check": form_check,
            }

        return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def archivovat(request, ident_cely):
    """
    Funkce pohledu pro archivaci projektu pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    projekt: Projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_UZAVRENY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentálně zbytečné, případná chyba se propaguje výše.
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        fedora_transaction = projekt.create_transaction(request.user, PROJEKT_USPESNE_ARCHIVOVAN)
        projekt_casti_dokumentu = list(projekt.casti_dokumentu.all())
        projekt_samostatne_nalezy = list(projekt.samostatne_nalezy.all())
        try:
            with transaction.atomic():
                projekt.set_archivovany(request.user)
                for item in projekt_casti_dokumentu:
                    item: DokumentCast
                    if item.dokument.doi and item.dokument.stav == D_STAV_ARCHIVOVANY:
                        item.dokument.doi_update()
                for item in projekt_samostatne_nalezy:
                    item: SamostatnyNalez
                    if item.igsn and item.stav == SN_ARCHIVOVANY:
                        item.igsn_update()
                projekt.close_active_transaction_when_finished = True
                projekt.save()
                return JsonResponse({"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})})
        except (DoiWriteError, FedoraError) as err:
            logger.info("projekt.views.archivovat.post_error", extra={"error": err, "ident_cely": projekt.ident_cely})
            transaction.set_rollback(True)
            fedora_transaction.rollback_transaction()
            for item in projekt_casti_dokumentu:
                item: DokumentCast
                if item.dokument.doi and item.dokument.stav == D_STAV_ARCHIVOVANY:
                    item.dokument.doi_update(False, True)
            for item in projekt_samostatne_nalezy:
                item: SamostatnyNalez
                if item.igsn and item.stav == SN_ARCHIVOVANY:
                    item.igsn_update(False, True)
        return JsonResponse({"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})})
    else:
        warnings = projekt.check_pred_archivaci()
        logger.debug("projekt.views.archivovat.warnings", extra={"warning": str(warnings)})
        form_check = CheckStavNotChangedForm(initial={"old_stav": projekt.stav})
        if warnings:
            request.session["temp_data"] = []
            for key, item in warnings.items():
                request.session["temp_data"].append(f"{key}: {item}")
            messages.add_message(request, messages.ERROR, PROJEKT_NELZE_ARCHIVOVAT)
            return JsonResponse(
                {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
                status=403,
            )
    if request.GET.get("from_arch") == "true":
        context = {
            "object": projekt,
            "title": _("projekt.views.archivovat.fromAkce.title.text"),
            "text": _("projekt.views.archivovat.fromAkce.text"),
            "id_tag": "archivovat-form",
            "button": _("projekt.views.archivovat.fromAkce.submitButton.text"),
            "form_check": form_check,
        }
    else:
        context = {
            "object": projekt,
            "title": _("projekt.views.archivovat.title.text"),
            "id_tag": "archivovat-form",
            "button": _("projekt.views.archivovat.submitButton.text"),
            "form_check": form_check,
        }
    return render(request, "core/transakce_modal.html", context)


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def navrhnout_ke_zruseni(request, ident_cely):
    """
    Funkce pohledu pro navržení projektu ke zrušení pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if not PROJEKT_STAV_ARCHIVOVANY > projekt.stav > PROJEKT_STAV_OZNAMENY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = NavrhnoutZruseniProjektForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            for a in form.fields["reason"].choices:
                if a[0] == duvod:
                    duvod_to_save = a[1]
            if duvod == "option1":
                duvod_to_save = str(duvod_to_save + " " + form.cleaned_data["projekt_id"])
            elif duvod == "option6":
                duvod_to_save = form.cleaned_data["reason_text"]
            else:
                duvod_to_save = duvod_to_save
            projekt.create_transaction(request.user, PROJEKT_USPESNE_NAVRZEN_KE_ZRUSENI)
            projekt.set_navrzen_ke_zruseni(request.user, duvod_to_save)
            projekt.close_active_transaction_when_finished = True
            projekt.save()
            return JsonResponse({"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})})
        else:
            logger.debug("projekt.views.navrhnout_ke_zruseni.form_not_valid", extra={"error": form.errors})
            context = {"projekt": projekt, "form": form}
    else:
        warnings = projekt.check_pred_navrzeni_k_zruseni()
        logger.debug("projekt.views.navrhnout_ke_zruseni.warnings", extra={"warning": warnings})

        if warnings:
            request.session["temp_data"] = []
            for key, item in warnings.items():
                if key == "has_event":
                    request.session["temp_data"].append(item)
            messages.add_message(request, messages.ERROR, PROJEKT_NELZE_NAVRHNOUT_KE_ZRUSENI)
            return JsonResponse(
                {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
                status=403,
            )
        context = {
            "projekt": projekt,
            "form": NavrhnoutZruseniProjektForm(initial={"old_stav": projekt.stav}),
        }
    return render(request, "projekt/navrhnout_zruseni.html", context)


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def zrusit(request, ident_cely):
    """
    Funkce pohledu pro zrušení projektu pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav not in [PROJEKT_STAV_NAVRZEN_KE_ZRUSENI, PROJEKT_STAV_OZNAMENY]:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = ZruseniProjektForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason_text"]
            projekt.create_transaction(request.user, PROJEKT_USPESNE_ZRUSEN)
            projekt.set_zruseny(request.user, duvod)
            if projekt.typ_projektu.pk == TYP_PROJEKTU_ZACHRANNY_ID and projekt.has_oznamovatel():
                rep_bin_file = projekt.create_cancel_confirmation_document(request.user)
            else:
                rep_bin_file = None
            projekt.close_active_transaction_when_finished = True
            projekt.save()
            Mailer.send_ep04(project=projekt, reason=duvod)
            if projekt.ident_cely[0] == OBLAST_CECHY:
                Mailer.send_ep06a(project=projekt, reason=duvod, rep_bin_file=rep_bin_file)
            else:
                Mailer.send_ep06b(project=projekt, reason=duvod, rep_bin_file=rep_bin_file)
            return JsonResponse({"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})})
        else:
            form_check = CheckStavNotChangedForm(initial={"old_stav": projekt.stav})
            logger.debug("projekt.views.zrusit.form_not_valid", extra={"error": form.errors})
            context = {
                "object": projekt,
                "title": _("projekt.views.zrusit.title.text"),
                "id_tag": "zrusit-form",
                "button": _("projekt.views.zrusit.submitButton.text"),
                "form_check": form_check,
                "form": form,
            }
    else:
        form_check = CheckStavNotChangedForm(initial={"old_stav": projekt.stav})
        context = {
            "object": projekt,
            "title": _("projekt.views.zrusit.title.text"),
            "id_tag": "zrusit-form",
            "button": _("projekt.views.zrusit.submitButton.text"),
            "form_check": form_check,
        }
        if projekt.stav == PROJEKT_STAV_NAVRZEN_KE_ZRUSENI:
            last_history_poznamka = (
                projekt.historie.historie_set.filter(typ_zmeny=NAVRZENI_KE_ZRUSENI_PROJ)
                .order_by("-datum_zmeny")[0]
                .poznamka
            )
            context["form"] = ZruseniProjektForm(initial={"reason_text": last_history_poznamka})
    return render(request, "core/transakce_modal.html", context)


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    """
    Funkce pohledu pro vrácení projektu pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if not PROJEKT_STAV_ARCHIVOVANY >= projekt.stav > PROJEKT_STAV_ZAPSANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = VratitForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            projekt.create_transaction(request.user, PROJEKT_USPESNE_VRACEN)
            projekt.set_vracen(request.user, projekt.stav - 1, duvod)
            projekt.close_active_transaction_when_finished = True
            projekt.save()
            return JsonResponse({"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})})
        else:
            logger.debug("projekt.views.vratit.form_not_valid", extra={"error": form.errors})
    else:
        form = VratitForm(initial={"old_stav": projekt.stav})
    context = {
        "object": projekt,
        "form": form,
        "title": _("projekt.views.vratit.title.text"),
        "id_tag": "vratit-form",
        "button": _("projekt.views.vratit.submitButton.text"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def vratit_navrh_zruseni(request, ident_cely):
    """
    Funkce pohledu pro vrácení návrhu na zrušení projektu pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)

    if projekt.stav not in [
        PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
        PROJEKT_STAV_ZRUSENY,
    ]:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = VratitForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            projekt.create_transaction(request.user, PROJEKT_USPESNE_VRACEN)
            projekt.set_znovu_zapsan(request.user, duvod)
            projekt.close_active_transaction_when_finished = True
            projekt.save()
            Mailer.send_ep05(project=projekt)
            return JsonResponse({"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})})
        else:
            logger.debug("projekt.views.vratit_navrh_zruseni.form_not_valid", extra={"error": form.errors})
    else:
        form = VratitForm(initial={"old_stav": projekt.stav})
    context = {
        "object": projekt,
        "form": form,
        "title": _("projekt.views.vratitNavrhZruseni.title.text"),
        "id_tag": "vratit-navrh-form",
        "button": _("projekt.views.vratitNavrhZruseni.submitButton.text"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def odpojit_dokument(request, ident_cely, proj_ident_cely):
    """
    Funkce pohledu pro odpojení dokumentu z projektu pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    :param proj_ident_cely: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.
    """
    proj = get_object_or_404(Projekt, ident_cely=proj_ident_cely)
    if proj.typ_projektu.id != TYP_PROJEKTU_PRUZKUM_ID:
        logger.debug("Projekt neni typu pruzkumny")
        messages.add_message(request, messages.SUCCESS, PROJEKT_NENI_TYP_PRUZKUMNY)
        return redirect(proj.get_absolute_url())
    relace_dokumentu = DokumentCast.objects.filter(dokument__ident_cely=ident_cely, projekt=proj)
    if not relace_dokumentu.count() > 0:
        logger.error("Projekt - Dokument wrong relation")
        messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
        if url_has_allowed_host_and_scheme(request.GET.get("next", "core:home"), allowed_hosts=settings.ALLOWED_HOSTS):
            safe_redirect = request.GET.get("next", "core:home")
        else:
            safe_redirect = "/"
        return redirect(safe_redirect)
    return odpojit(request, ident_cely, proj_ident_cely, proj)


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def pripojit_dokument(request, proj_ident_cely):
    """
    Funkce pohledu pro pripojení dokumentu z projektu pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param proj_ident_cely: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.
    """
    proj = get_object_or_404(Projekt, ident_cely=proj_ident_cely)
    if proj.typ_projektu.id != TYP_PROJEKTU_PRUZKUM_ID:
        logger.debug("Projekt neni typu pruzkumny")
        messages.add_message(request, messages.SUCCESS, PROJEKT_NENI_TYP_PRUZKUMNY)
        return redirect(proj.get_absolute_url())

    return pripojit(request, proj_ident_cely, None, Projekt)


@login_required
@handle_fedora_error
@require_http_methods(["POST"])
def generovat_oznameni(request, ident_cely):
    """
    Funkce pohledu pro generování oznámení projektu pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    logger.debug(
        "projekt.views.generovat_oznameni.start",
        extra={"ident_cely": ident_cely, "option": request.POST.get("odeslat_oznamovateli", False)},
    )
    projekt: Projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.typ_projektu.id != TYP_PROJEKTU_ZACHRANNY_ID:
        logger.debug("projekt.views.generovat_oznameni.wrong_project_tpye")
        messages.add_message(request, messages.SUCCESS, PROJEKT_NENI_TYP_ZACHRANNY)
        return redirect(projekt.get_absolute_url())
    fedora_transaction = projekt.create_transaction(request.user)
    fedora_transaction.success_message = _("projekt.views.generovat_oznameni.success")
    fedora_transaction.error_message = _("projekt.views.generovat_oznameni.error")
    fedora_transaction.redirect_url = projekt.get_absolute_url()
    rep_bin_file = projekt.create_confirmation_document(fedora_transaction, additional=True, user=request.user)
    if request.POST.get("odeslat_oznamovateli", False):
        projekt.send_ep01(rep_bin_file)
    projekt.close_active_transaction_when_finished = True
    projekt.save()
    return redirect(projekt.get_absolute_url())


class GenerovatOznameniView(LoginRequiredMixin, RedirectView):
    """Implementuje komponentu ``GenerovatOznameniView`` v rámci aplikace."""

    http_method_names = ["POST"]

    @method_decorator(handle_fedora_error)
    def get_redirect_url(self, *args, **kwargs):
        """
        Vrací redirect url.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        ident_cely = kwargs["ident_cely"]
        projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
        fedora_transaction = projekt.create_transaction(self.request.user)
        rep_bin_file = projekt.create_confirmation_document(fedora_transaction, additional=True, user=self.request.user)
        projekt.close_active_transaction_when_finished = True
        projekt.send_ep01(rep_bin_file)
        projekt.save()
        return super().get_redirect_url(*args, **kwargs)


@login_required
@require_http_methods(["POST"])
def generovat_expertni_list(request, ident_cely):
    """
    Funkce pohledu pro generování expertního listu projektu pomoci modalu.

    :param request: Aktuální HTTP request předaný view/funkci.
    :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
    """
    popup_parametry = request.POST
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.typ_projektu.id != TYP_PROJEKTU_ZACHRANNY_ID:
        logger.debug("Projekt neni typu pruzkumny")
        messages.add_message(request, messages.SUCCESS, PROJEKT_NENI_TYP_ZACHRANNY)
        return redirect(projekt.get_absolute_url())
    output = projekt.create_expert_list(popup_parametry)
    response = StreamingHttpResponse(output, content_type="text/rtf")
    response["Content-Disposition"] = f'attachment; filename="expertni_list_{ident_cely}.rtf"'
    return response


def get_history_dates(historie_vazby, request_user):
    """
    Funkce pro získaní dátumů pro historii.

    :param historie_vazby: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
    :param request_user: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.
    :return: Slovník dat jednotlivých změn stavu pro zobrazení v historii.
    """
    request_user: User
    anonymized = request_user.hlavni_role.pk not in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)
    datum_zruseni = historie_vazby.get_last_transaction_date(RUSENI_PROJ, anonymized)
    if not datum_zruseni:
        datum_zruseni = historie_vazby.get_last_transaction_date(RUSENI_STARE_PROJ, anonymized)
    historie = {
        "datum_oznameni": historie_vazby.get_last_transaction_date(OZNAMENI_PROJ, anonymized),
        "datum_zapsani": historie_vazby.get_last_transaction_date(
            [
                VRACENI_NAVRHU_ZRUSENI,
                SCHVALENI_OZNAMENI_PROJ,
                ZAPSANI_PROJ,
                VRACENI_ZRUSENI,
            ],
            anonymized,
        ),
        "datum_prihlaseni": historie_vazby.get_last_transaction_date(PRIHLASENI_PROJ, anonymized),
        "datum_zahajeni_v_terenu": historie_vazby.get_last_transaction_date(ZAHAJENI_V_TERENU_PROJ, anonymized),
        "datum_ukonceni_v_terenu": historie_vazby.get_last_transaction_date(UKONCENI_V_TERENU_PROJ, anonymized),
        "datum_uzavreni": historie_vazby.get_last_transaction_date(UZAVRENI_PROJ, anonymized),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_PROJ, anonymized),
        "datum_navrhu_ke_zruseni": historie_vazby.get_last_transaction_date(NAVRZENI_KE_ZRUSENI_PROJ, anonymized),
        "datum_zruseni": datum_zruseni,
    }
    return historie


def get_detail_template_shows(projekt, user):
    """
    Funkce pro získaní dictionary uživatelských akcí které mají být zobrazeny uživately.

    :param projekt: Doménový objekt `projekt`, se kterým funkce pracuje.
    :param user: Uživatel, v jehož kontextu se operace provádí.
    :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.
    """
    show_oznamovatel = get_show_oznamovatel(projekt, user)

    show_samostatne_nalezy = projekt.typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID
    show_pridat_akci = False
    show_pridat_sam_nalez = False
    show_pridat_oznamovatele = False
    show_zadost_udaje_oznamovatel = False
    if projekt.typ_projektu.id != TYP_PROJEKTU_PRUZKUM_ID:
        show_pridat_akci = check_permissions(p.actionChoices.archz_pripojit_do_proj, user, projekt.ident_cely)
    else:
        show_pridat_sam_nalez = check_permissions(p.actionChoices.pas_zapsat_do_projektu, user, projekt.ident_cely)
    if projekt.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID:
        if not projekt.has_oznamovatel():
            show_pridat_oznamovatele = check_permissions(
                p.actionChoices.projekt_oznamovatel_zapsat, user, projekt.ident_cely
            )
        elif not show_oznamovatel:
            show_zadost_udaje_oznamovatel = check_permissions(
                p.actionChoices.projekt_zadost_udaje_oznamovatel, user, projekt.ident_cely
            )
    show_dokumenty = projekt.typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID
    show_arch_links = projekt.stav == PROJEKT_STAV_ARCHIVOVANY
    show_akce = projekt.typ_projektu.id != TYP_PROJEKTU_PRUZKUM_ID
    show = {
        "oznamovatel": show_oznamovatel,
        "prihlasit_link": check_permissions(p.actionChoices.projekt_prihlasit, user, projekt.ident_cely)
        and user.organizace.oao,
        "vratit_link": check_permissions(p.actionChoices.projekt_vratit, user, projekt.ident_cely),
        "schvalit_link": check_permissions(p.actionChoices.projekt_schvalit, user, projekt.ident_cely),
        "zahajit_teren_link": check_permissions(p.actionChoices.projekt_zahajit_v_terenu, user, projekt.ident_cely),
        "ukoncit_teren_link": check_permissions(p.actionChoices.projekt_ukoncit_v_terenu, user, projekt.ident_cely),
        "uzavrit_link": check_permissions(p.actionChoices.projekt_uzavrit, user, projekt.ident_cely),
        "archivovat_link": check_permissions(p.actionChoices.projekt_archivovat, user, projekt.ident_cely),
        "navrhnout_zruseni_link": check_permissions(p.actionChoices.projekt_navrh_ke_zruseni, user, projekt.ident_cely),
        "zrusit_link": check_permissions(p.actionChoices.projekt_zrusit, user, projekt.ident_cely),
        "znovu_zapsat_link": check_permissions(p.actionChoices.projekt_vratit_navrh_zruseni, user, projekt.ident_cely),
        "samostatne_nalezy": show_samostatne_nalezy,
        "pridat_akci": show_pridat_akci,
        "editovat": check_permissions(p.actionChoices.projekt_edit, user, projekt.ident_cely),
        "oznamovatel_editovat": check_permissions(p.actionChoices.projekt_oznamovatel_edit, user, projekt.ident_cely),
        "dokumenty": show_dokumenty,
        "arch_links": show_arch_links,
        "akce": show_akce,
        "pripojit_dokumenty": check_permissions(p.actionChoices.projekt_dok_pripojit, user, projekt.ident_cely),
        "pridat_sam_nalez": show_pridat_sam_nalez,
        "pridat_oznamovatele": show_pridat_oznamovatele,
        "dokument_odpojit": check_permissions(p.actionChoices.projekt_dok_odpojit, user, projekt.ident_cely),
        "generovat_potvrzeni": check_permissions(p.actionChoices.projekt_generovat_oznameni, user, projekt.ident_cely),
        "generovat_exp_list": check_permissions(p.actionChoices.projekt_generovat_exp_list, user, projekt.ident_cely),
        "smazat_link": check_permissions(p.actionChoices.projekt_smazat, user, projekt.ident_cely),
        "zapsat_dokumenty": check_permissions(p.actionChoices.dok_zapsat_do_projekt, user, projekt.ident_cely),
        "soubor_stahnout": check_permissions(p.actionChoices.soubor_stahnout_projekt, user, projekt.ident_cely),
        "soubor_nahled": check_permissions(p.actionChoices.soubor_nahled_projekt, user, projekt.ident_cely),
        "soubor_smazat": check_permissions(p.actionChoices.soubor_smazat_projekt, user, projekt.ident_cely),
        "soubor_nahrat": check_permissions(p.actionChoices.soubor_nahrat_projekt, user, projekt.ident_cely),
        "zadost_udaje_oznamovatel": show_zadost_udaje_oznamovatel,
        "upravit_datum_oznameni": check_permissions(
            p.actionChoices.projekt_upravit_datum_oznameni, user, projekt.ident_cely
        ),
        "zadost_odhlaseni_projektu": check_permissions(
            p.actionChoices.projekt_zadost_odhlaseni_projektu, user, projekt.ident_cely
        ),
        "zadost_zruseni_projektu": check_permissions(
            p.actionChoices.projekt_zadost_zruseni_projektu, user, projekt.ident_cely
        ),
        "vypis": check_permissions(p.actionChoices.vypis_projekt, user, projekt.ident_cely),
    }
    return show


def get_show_oznamovatel(projekt, user):
    """
    Vrací show oznamovatel.

    :param projekt: Doménový objekt `projekt`, se kterým funkce pracuje.
    :param user: Uživatel, v jehož kontextu se operace provádí.
    :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.
    """
    if projekt.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID and projekt.has_oznamovatel():
        if user.is_archiver_or_more:
            return True
        elif user.hlavni_role.id == ROLE_ARCHEOLOG_ID:
            if projekt.stav == PROJEKT_STAV_ZAPSANY:
                return True
            elif projekt.organizace == user.organizace:
                if projekt.stav in [
                    PROJEKT_STAV_PRIHLASENY,
                    PROJEKT_STAV_ZAHAJENY_V_TERENU,
                    PROJEKT_STAV_UKONCENY_V_TERENU,
                ]:
                    return True
                elif projekt.stav == PROJEKT_STAV_UZAVRENY:
                    last_uzavreni = projekt.historie.get_last_transaction_date(UZAVRENI_PROJ)
                    if last_uzavreni and last_uzavreni["datum"] >= datetime.now(
                        last_uzavreni["datum"].tzinfo
                    ) - timedelta(days=90):
                        return True
            elif projekt.stav in [
                PROJEKT_STAV_PRIHLASENY,
                PROJEKT_STAV_ZAHAJENY_V_TERENU,
                PROJEKT_STAV_UKONCENY_V_TERENU,
                PROJEKT_STAV_UZAVRENY,
            ]:
                last_prihlaseni = projekt.historie.get_last_transaction_date(PRIHLASENI_PROJ)
                if last_prihlaseni and last_prihlaseni["datum"] >= datetime.now(
                    last_prihlaseni["datum"].tzinfo
                ) - timedelta(days=30):
                    return True
    return False


def get_required_fields(zaznam=None, next=0):
    """
    Funkce pro získaní dictionary povinných polí podle stavu projektu.

    :param zaznam: Záznam/objekt ``zaznam``, který funkce čte, validuje nebo upravuje.
    :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
    :return: Seznam názvů polí, která mají být v daném stavu povinná.
    """
    required_fields = []
    if zaznam:
        stav = zaznam.stav
    else:
        stav = 1
    if stav >= PROJEKT_STAV_OZNAMENY - next:
        required_fields = [
            "typ_projektu",
            "hlavni_katastr",
            "podnet",
            "lokalizace",
            "parcelni_cislo",
            "planovane_zahajeni",
        ]
    if PROJEKT_STAV_ZAPSANY - next < stav < PROJEKT_STAV_NAVRZEN_KE_ZRUSENI - next:
        required_fields += [
            "vedouci_projektu",
            "organizace",
            "kulturni_pamatka",
        ]
    if PROJEKT_STAV_PRIHLASENY - next < stav < PROJEKT_STAV_NAVRZEN_KE_ZRUSENI - next:
        required_fields += [
            "datum_zahajeni",
        ]
    if PROJEKT_STAV_ZAHAJENY_V_TERENU - next < stav < PROJEKT_STAV_NAVRZEN_KE_ZRUSENI - next:
        required_fields += ["datum_ukonceni"]
    if PROJEKT_STAV_UKONCENY_V_TERENU - next < stav < PROJEKT_STAV_NAVRZEN_KE_ZRUSENI - next:
        required_fields += ["termin_odevzdani_nz"]
    return required_fields


def katastr_text_to_id(request):
    """
    Funkce podlehu pro získaní ID katastru podle názvu katastru.

    :param request: Aktuální HTTP request předaný view/funkci.
    """
    hlavni_katastr: str = request.POST.get("hlavni_katastr")
    if hlavni_katastr is None or hlavni_katastr.strip() == "":
        return request.POST.copy()
    try:
        kod = hlavni_katastr[hlavni_katastr.find(";") + 1 : hlavni_katastr.find(")")].strip()
    except (ValueError, IndexError) as e:
        logger.warning("projekt.views.katastr_text_to_id.wrong_format", extra={"katastr": hlavni_katastr, "error": e})
        return request.POST.copy()
    if not kod.isnumeric():
        logger.warning("projekt.views.katastr_text_to_id.not_numeric", extra={"katastr": hlavni_katastr})
        return request.POST.copy()
    katastr_query = RuianKatastr.objects.filter(kod=kod)
    if katastr_query.count() > 0:
        post = request.POST.copy()
        post["hlavni_katastr"] = katastr_query.first().id
        return post
    logger.warning("projekt.views.katastr_text_to_id.not_found", extra={"katastr": hlavni_katastr})
    return request.POST.copy()


class ProjektAutocompleteBezZrusenych(autocomplete.Select2QuerySetView, ProjektPermissionFilterMixin):
    """Třída pohledu získaní projektů pro autocomplete pro připojení do dokumentu."""

    typ_zmeny_lookup = ZAPSANI_PROJ

    def get_result_label(self, result):
        """
        Vrací result label.

        :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.
        """
        return f"{result.ident_cely} ({result.hlavni_katastr}; {result.vedouci_projektu})"

    def get_queryset(self):
        """Vrací queryset. v aplikaci."""
        if not self.request.user.is_authenticated:
            return Projekt.objects.none()
        self.typ = self.kwargs.get("typ")
        if self.typ == "archz":
            qs = (
                Projekt.objects.exclude(typ_projektu__id=TYP_PROJEKTU_PRUZKUM_ID)
                .annotate(ident_len=Length("ident_cely"))
                .filter(ident_len__gt=0)
            ).order_by("ident_cely")
        elif self.typ == "dokument":
            qs = (
                Projekt.objects.filter(typ_projektu__id=TYP_PROJEKTU_PRUZKUM_ID)
                .annotate(ident_len=Length("ident_cely"))
                .filter(ident_len__gt=0)
            ).order_by("ident_cely")
        else:
            return Projekt.objects.none()
        if self.q:
            qs = qs.filter(
                Q(ident_cely__icontains=self.q)
                | Q(hlavni_katastr__nazev__icontains=self.q)
                | Q(vedouci_projektu__vypis_cely__icontains=self.q)
            )
        return self.check_filter_permission(qs)

    def check_filter_permission(self, qs):
        """
        Ověří filter permission.

        :param qs: Vstupní queryset, který má být dále zpracován.
        """
        permissions = Permissions.objects.filter(
            main_role=self.request.user.hlavni_role,
            address_in_app=self.request.resolver_match.route,
            action__endswith=self.typ,
        )
        if permissions.count() > 0:
            for idx, perm in enumerate(permissions):
                if idx == 0:
                    new_qs = self.filter_by_permission(qs, perm)
                else:
                    new_qs = self.filter_by_permission(qs, perm).exclude(pk__in=new_qs.values("pk")) | new_qs

            qs = new_qs
        return qs


class ProjectTableRowView(LoginRequiredMixin, View):
    """Třída pohledu pro zobrazení řádku tabulky projektů pri připájení."""

    def get(self, request):
        """
        Vrací výsledek operace.

        :param request: Django HTTP požadavek použitý při zpracování.
        """
        context = {"p": Projekt.objects.get(id=request.GET.get("id", ""))}
        return HttpResponse(render_to_string("projekt/projekt_table_row.html", context))


class UpravitDatumOznameniView(LoginRequiredMixin, TemplateView):
    """Implementuje komponentu ``UpravitDatumOznameniView`` v rámci aplikace."""

    template_name = "core/transakce_modal.html"

    def _get_existing_record(self, projekt):
        """
        Vrací existing record.

        :param projekt: Doménový objekt `projekt`, se kterým funkce pracuje.
        :return: Načtená data odpovídající zadaným vstupům.
        """
        historie_objects = Historie.objects.filter(vazba=projekt.historie, typ_zmeny=OZNAMENI_PROJ_MANUALNI)
        if historie_objects.exists():
            return historie_objects.last()

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        ident_cely = self.kwargs.get("ident_cely")
        projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
        context = {
            "object": projekt,
            "title": _("projekt.views.upravitDatumOznameniView.title"),
            "id_tag": "upravit-datum-oznameni-form",
            "button": _("projekt.views.upravitDatumOznameniView.submitButton"),
        }
        return context

    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Django HTTP požadavek použitý při zpracování.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        context = self.get_context_data(**kwargs)
        projekt: Projekt = context["object"]
        instance = self._get_existing_record(projekt)
        if instance:
            timezone = get_timezone()
            form = UpravitDatumOznameniForm(
                instance=instance,
                initial={
                    "datum_oznameni": instance.datum_zmeny,
                    "cas_oznameni": instance.datum_zmeny.astimezone(timezone),
                },
            )
        else:
            form = UpravitDatumOznameniForm()
        context["form"] = form
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Django HTTP požadavek použitý při zpracování.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        context = self.get_context_data(**kwargs)
        projekt: Projekt = context["object"]
        form = UpravitDatumOznameniForm(request.POST)
        if form.is_valid():
            histore = self._get_existing_record(projekt)
            if histore:
                timezone = get_timezone()
                histore.poznamka = form.cleaned_data["poznamka"]
                histore.datum_zmeny = datetime.combine(
                    form.cleaned_data["datum_oznameni"], form.cleaned_data["cas_oznameni"]
                ).astimezone(timezone)
            else:
                histore = form.save(commit=False)
                histore: Historie
                histore.typ_zmeny = OZNAMENI_PROJ_MANUALNI
                histore.uzivatel = self.request.user
                histore.vazba = projekt.historie
                # Musí se zavolat, jinak SQL přepíše datum na aktuální datum a čas.
                histore.save()
                histore.datum_zmeny = datetime.combine(
                    form.cleaned_data["datum_oznameni"], form.cleaned_data["cas_oznameni"]
                )
            histore.save()
            projekt.active_transaction = projekt.create_transaction(request.user)
            projekt.save_metadata(close_transaction=True)
        else:
            messages.add_message(request, messages.ERROR, DATUM_OZNAMENI_SE_NEPOVEDLO_EDITOVAT)
            logger.debug(
                "projekt.views.UpravitDatumOznameniView.form_invalid",
                extra={"error": form.errors, "ident_cely": projekt.ident_cely},
            )

        return JsonResponse({"redirect": projekt.get_absolute_url()})


class ZadostUdajeOznamovatelView(LoginRequiredMixin, TemplateView):
    """Třida pohledu pro odeslání žádosti o údaje o oznamovateli."""

    template_name = "core/transakce_modal.html"

    def get_zaznam(self):
        """Vrací zaznam. v aplikaci."""
        ident_cely = self.kwargs.get("ident_cely")
        zaznam = get_object_or_404(
            Projekt,
            ident_cely=ident_cely,
        )
        return zaznam

    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Django HTTP požadavek použitý při zpracování.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        zaznam = self.get_zaznam()
        context = {
            "object": zaznam,
            "title": _("projekt.views.ZadostUdajeOznamovatelView.title.text"),
            "id_tag": "zadost-udaje-oznamovatel-form",
            "button": _("projekt.views.ZadostUdajeOznamovatelView.submitButton.text"),
        }
        form = ZadostProjektForm(
            _("projekt.forms.zadostUdajeOznamovatel.duvod.label"),
            _("projekt.forms.zadostUdajeOznamovatel.duvod.tooltip"),
        )
        context["form"] = form
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Django HTTP požadavek použitý při zpracování.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        form = ZadostProjektForm(data=request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            zaznam = self.get_zaznam()
            Mailer.send_ep08(zaznam, duvod, request.user)
            messages.add_message(request, messages.SUCCESS, PROJEKT_ZADOST_UDAJE_OZNAMOVATEL_SUCCESS)
        else:
            messages.add_message(request, messages.SUCCESS, PROJEKT_ZADOST_UDAJE_OZNAMOVATEL_ERROR)
        return JsonResponse({"redirect": zaznam.get_absolute_url()})


class ZadostOdhlaseniProjektuView(LoginRequiredMixin, TemplateView):
    """Třida pohledu pro odeslání žádosti pro odhlášení projektu."""

    template_name = "core/transakce_modal.html"

    def get_zaznam(self):
        """Vrací zaznam. v aplikaci."""
        ident_cely = self.kwargs.get("ident_cely")
        zaznam = get_object_or_404(
            Projekt,
            ident_cely=ident_cely,
        )
        return zaznam

    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Django HTTP požadavek použitý při zpracování.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        zaznam = self.get_zaznam()
        context = {
            "object": zaznam,
            "title": _("projekt.views.ZadostOdhlaseniProjektuView.title.text"),
            "id_tag": "zadost-odhlaseni-projektu-form",
            "button": _("projekt.views.ZadostOdhlaseniProjektuView.submitButton.text"),
        }
        form = ZadostProjektForm(
            _("projekt.forms.ZadostOdhlaseniProjektu.duvod.label"),
            _("projekt.forms.ZadostOdhlaseniProjektu.duvod.tooltip"),
        )
        context["form"] = form
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Django HTTP požadavek použitý při zpracování.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        form = ZadostProjektForm(data=request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            zaznam = self.get_zaznam()
            Mailer.send_ep07(zaznam, duvod, request.user)
            messages.add_message(request, messages.SUCCESS, PROJEKT_ZADOST_ODHLASENI_PROJEKTU_SUCCESS)
        else:
            messages.add_message(request, messages.SUCCESS, PROJEKT_ZADOST_ODHLASENI_PROJEKTU_ERROR)
        return JsonResponse({"redirect": zaznam.get_absolute_url()})


class ZadostZruseniProjektuView(LoginRequiredMixin, TemplateView):
    """Třida pohledu pro odeslání žádosti pro zrušení projektu."""

    template_name = "core/transakce_modal.html"

    def get_zaznam(self):
        """Vrací zaznam. v aplikaci."""
        ident_cely = self.kwargs.get("ident_cely")
        zaznam = get_object_or_404(
            Projekt,
            ident_cely=ident_cely,
        )
        return zaznam

    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Django HTTP požadavek použitý při zpracování.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        zaznam = self.get_zaznam()
        form = ZadostProjektForm(
            _("projekt.forms.ZadostZruseniProjektu.duvod.label"),
            _("projekt.forms.ZadostZruseniProjektu.duvod.tooltip"),
        )
        context = {
            "object": zaznam,
            "title": _("projekt.views.ZadostZruseniProjektuView.title.text"),
            "id_tag": "zadost-zruseni-projektu-form",
            "button": _("projekt.views.ZadostZruseniProjektuView.submitButton.text"),
            "form": form,
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Django HTTP požadavek použitý při zpracování.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        form = ZadostProjektForm(data=request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            zaznam = self.get_zaznam()
            Mailer.send_ep11(zaznam, duvod, request.user, request)
            messages.add_message(request, messages.SUCCESS, PROJEKT_ZADOST_ZRUSENI_PROJEKTU_SUCCESS)
        else:
            messages.add_message(request, messages.SUCCESS, PROJEKT_ZADOST_ZRUSENI_PROJEKTU_ERROR)
        return JsonResponse({"redirect": zaznam.get_absolute_url()})
