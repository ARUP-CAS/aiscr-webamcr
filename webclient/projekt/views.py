import logging
from django.views import View

import simplejson as json

from django.db.models.functions import Length
from django.template.loader import render_to_string
from dal import autocomplete
from arch_z.models import Akce
from core.constants import (
    ARCHIVACE_PROJ,
    AZ_STAV_ZAPSANY,
    D_STAV_ZAPSANY,
    NAVRZENI_KE_ZRUSENI_PROJ,
    OZNAMENI_PROJ,
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
    ROLE_ARCHIVAR_ID,
    RUSENI_PROJ,
    SCHVALENI_OZNAMENI_PROJ,
    UKONCENI_V_TERENU_PROJ,
    UZAVRENI_PROJ,
    VRACENI_NAVRHU_ZRUSENI,
    VRACENI_ZRUSENI,
    ZAHAJENI_V_TERENU_PROJ,
    ZAPSANI_PROJ,
)
from core.decorators import allowed_user_groups
from core.exceptions import MaximalIdentNumberError
from core.forms import CheckStavNotChangedForm, VratitForm
from core.message_constants import (
    MAXIMUM_IDENT_DOSAZEN,
    PRISTUP_ZAKAZAN,
    PROJEKT_NELZE_ARCHIVOVAT,
    PROJEKT_NELZE_NAVRHNOUT_KE_ZRUSENI,
    PROJEKT_NELZE_SMAZAT,
    PROJEKT_NELZE_UZAVRIT,
    PROJEKT_USPESNE_ARCHIVOVAN,
    PROJEKT_USPESNE_NAVRZEN_KE_ZRUSENI,
    PROJEKT_USPESNE_PRIHLASEN,
    PROJEKT_USPESNE_SCHVALEN,
    PROJEKT_USPESNE_UKONCEN_V_TERENU,
    PROJEKT_USPESNE_UZAVREN,
    PROJEKT_USPESNE_VRACEN,
    PROJEKT_USPESNE_ZAHAJEN_V_TERENU,
    PROJEKT_USPESNE_ZRUSEN,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from core.utils import (
    get_heatmap_project,
    get_heatmap_project_density,
    get_num_projects_from_envelope,
    get_projects_from_envelope,
)
from core.views import SearchListView, check_stav_changed
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from dokument.models import Dokument
from dokument.views import odpojit, pripojit
from heslar.hesla import TYP_PROJEKTU_PRUZKUM_ID, TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import RuianKatastr
from oznameni.forms import OznamovatelForm
from projekt.filters import ProjektFilter
from projekt.forms import (
    CreateProjektForm,
    EditProjektForm,
    GenerovatExpertniListForm,
    GenerovatNovePotvrzeniForm,
    NavrhnoutZruseniProjektForm,
    PrihlaseniProjektForm,
    UkoncitVTerenuForm,
    ZahajitVTerenuForm,
    ZruseniProjektForm,
)
from projekt.models import Projekt
from projekt.tables import ProjektTable
from uzivatel.forms import OsobaForm
from services.mailer import Mailer


logger = logging.getLogger('python-logstash-logger')


@login_required
@require_http_methods(["GET"])
def index(request):
    return render(request, "projekt/index.html")


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {"warnings": request.session.pop("temp_data", None)}
    projekt = get_object_or_404(
        Projekt.objects.select_related(
            "kulturni_pamatka", "typ_projektu", "vedouci_projektu", "organizace"
        ),
        ident_cely=ident_cely,
    )
    context["projekt"] = projekt
    typ_projektu = projekt.typ_projektu
    if typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID and projekt.has_oznamovatel():
        context["oznamovatel"] = projekt.oznamovatel
    elif typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID:
        context["samostatne_nalezy"] = projekt.samostatne_nalezy.select_related(
            "obdobi", "druh_nalezu", "specifikace", "nalezce", "katastr"
        ).all()

    akce = Akce.objects.filter(projekt=projekt).select_related(
        "archeologicky_zaznam__pristupnost", "hlavni_typ"
    )
    dokumenty = (
        Dokument.objects.filter(casti__projekt__ident_cely=ident_cely)
        .select_related("soubory")
        .prefetch_related("soubory__soubory")
    ).order_by("ident_cely")
    context["akce"] = akce
    soubory = projekt.soubory.soubory.all()
    context["soubory"] = soubory
    context["dalsi_katastry"] = projekt.katastry.all()
    context["history_dates"] = get_history_dates(projekt.historie)
    context["show"] = get_detail_template_shows(projekt, request.user)
    context["dokumenty"] = dokumenty
    context["generovatNovePotvrzeniForm"] = GenerovatNovePotvrzeniForm()
    context["generovat_expertni_list_form"] = GenerovatExpertniListForm()

    return render(request, "projekt/detail.html", context)


# @csrf_exempt
@login_required
@require_http_methods(["POST"])
def post_ajax_get_projects_limit(request):
    body = json.loads(request.body.decode("utf-8"))
    num = get_num_projects_from_envelope(
        body["southEast"]["lng"],
        body["northWest"]["lat"],
        body["northWest"]["lng"],
        body["southEast"]["lat"],
    )
    logger.debug("projekt.views.post_ajax_get_projects_limit.num", extra={"num": num})
    if num < 5000:
        pians = get_projects_from_envelope(
            body["southEast"]["lng"],
            body["northWest"]["lat"],
            body["northWest"]["lng"],
            body["southEast"]["lat"],
        )
        back = []
        for pian in pians:
            back.append(
                {
                    "id": pian.id,
                    "ident_cely": pian.ident_cely,
                    "geom": pian.geometry.replace(", ", ","),
                }
            )
        if len(pians) > 0:
            return JsonResponse({"points": back, "algorithm": "detail"}, status=200)
        else:
            return JsonResponse({"points": [], "algorithm": "detail"}, status=200)
    else:
        density = get_heatmap_project_density(
            body["southEast"]["lng"],
            body["northWest"]["lat"],
            body["northWest"]["lng"],
            body["southEast"]["lat"],
            body["zoom"],
        )
        logger.debug("projekt.views.post_ajax_get_projects_limit.density", extra={"density": density})

        heats = get_heatmap_project(
            body["southEast"]["lng"],
            body["northWest"]["lat"],
            body["northWest"]["lng"],
            body["southEast"]["lat"],
            body["zoom"],
        )
        back = []
        cid = 0
        for heat in heats:
            cid += 1
            back.append(
                {
                    "id": str(cid),
                    "pocet": heat["count"],
                    "density": 0,
                    "geom": heat["geometry"].replace(", ", ","),
                }
            )
        if len(heat) > 0:
            return JsonResponse({"heat": back, "algorithm": "heat"}, status=200)
        else:
            return JsonResponse({"heat": [], "algorithm": "heat"}, status=200)


@login_required
@require_http_methods(["GET", "POST"])
def create(request):
    logger.debug("projekt.views.create.start")
    required_fields = get_required_fields()
    required_fields_next = get_required_fields(next=1)
    if request.method == "POST":
        request.POST = katastr_text_to_id(request)
        form_projekt = CreateProjektForm(
            request.POST, required=required_fields, required_next=required_fields_next
        )
        if request.POST["typ_projektu"] == TYP_PROJEKTU_ZACHRANNY_ID:
            required = True
        else:
            required = False
        form_oznamovatel = OznamovatelForm(request.POST, required=required)
        if form_projekt.is_valid():
            logger.debug("projekt.views.create.form_valid")
            lat = form_projekt.cleaned_data["latitude"]
            long = form_projekt.cleaned_data["longitude"]
            p = form_projekt.save(commit=False)
            if p.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID:
                # Kontrola oznamovatele
                if not form_oznamovatel.is_valid():
                    logger.debug("projekt.views.create.form_not_valid", extra={"errors": form_oznamovatel.errors})
                    return render(
                        request,
                        "projekt/create.html",
                        {
                            "form_projekt": form_projekt,
                            "form_oznamovatel": form_oznamovatel,
                            "title": _("Zápis projektu"),
                            "header": _("Zápis projektu"),
                            "button": _("Zapsat projekt"),
                        },
                    )
            if long and lat:
                p.geom = Point(long, lat)
            try:
                p.set_permanent_ident_cely()
            except MaximalIdentNumberError:
                messages.add_message(request, messages.SUCCESS, MAXIMUM_IDENT_DOSAZEN)
            else:
                p.save()
                p.set_zapsany(request.user)
                form_projekt.save_m2m()
                if p.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID:
                    # Vytvoreni oznamovatele - kontrola formu uz je na zacatku
                    oznamovatel = form_oznamovatel.save(commit=False)
                    oznamovatel.projekt = p
                    oznamovatel.save()
                if p.should_generate_confirmation_document:
                    p.create_confirmation_document()
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
                return redirect("projekt:detail", ident_cely=p.ident_cely)
        else:
            logger.debug("projekt.views.create.form_projekt_not_valid", extra={"errors": form_projekt.errors})
    else:
        form_projekt = CreateProjektForm(
            required=required_fields, required_next=required_fields_next
        )
        form_oznamovatel = OznamovatelForm(uzamknout_formular=True)
    return render(
        request,
        "projekt/create.html",
        {
            "form_projekt": form_projekt,
            "form_oznamovatel": form_oznamovatel,
            "title": _("Zápis projektu"),
            "header": _("Zápis projektu"),
            "button": _("Zapsat projekt"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav == PROJEKT_STAV_ARCHIVOVANY:
        raise PermissionDenied()
    required_fields = get_required_fields(projekt)
    required_fields_next = get_required_fields(projekt, 1)
    if request.method == "POST":
        request.POST = katastr_text_to_id(request)
        form = EditProjektForm(
            request.POST,
            instance=projekt,
            required=required_fields,
            required_next=required_fields_next,
        )
        if form.is_valid():
            logger.debug("projekt.views.edit.form_valid")
            lat = form.cleaned_data["latitude"]
            long = form.cleaned_data["longitude"]
            # Workaroud to not check if long and lat has been changed, only geom is interesting
            form.fields["latitude"].initial = lat
            form.fields["longitude"].initial = long
            p = form.save()
            old_geom = p.geom
            new_geom = Point(long, lat)
            geom_changed = False
            if old_geom is None or new_geom.coords != old_geom.coords:
                p.geom = new_geom
                p.save()
                geom_changed = True
                logger.debug("projekt.views.edit.form_valid.geom_updated", extra={"geom": p.geom})
            else:
                logger.warning("projekt.views.edit.form_valid.geom_not_updated")
            if form.changed_data or geom_changed:
                logger.debug("projekt.views.edit.form_valid.form_changed", extra={"changed_data": form.changed_data})
                logger.debug(form.changed_data)
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return redirect("projekt:detail", ident_cely=ident_cely)
        else:
            logger.debug("projekt.views.edit.form_valid.form_not_valid", extra={"form_errors": form.errors})

    else:
        form = EditProjektForm(
            instance=projekt,
            required=required_fields,
            required_next=required_fields_next,
        )
        if projekt.geom is not None:
            form.fields["latitude"].initial = projekt.geom.coords[1]
            form.fields["longitude"].initial = projekt.geom.coords[0]
        else:
            logger.warning("Projekt geom is empty.")
    return render(
        request,
        "projekt/edit.html",
        {"form_projekt": form, "projekt": projekt},
    )


@login_required
@allowed_user_groups([ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID])
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        projekt.delete()
        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
        return JsonResponse({"redirect": reverse("projekt:list")})
    else:
        warnings = projekt.check_pred_smazanim()
        if warnings:
            request.session["temp_data"] = warnings
            messages.add_message(request, messages.ERROR, PROJEKT_NELZE_SMAZAT)
            return JsonResponse(
                {
                    "redirect": reverse(
                        "projekt:detail", kwargs={"ident_cely": ident_cely}
                    )
                },
                status=403,
            )
        form_check = CheckStavNotChangedForm(initial={"old_stav": projekt.stav})
        context = {
            "object": projekt,
            "title": _("projekt.modalForm.smazani.title.text"),
            "id_tag": "smazat-form",
            "button": _("projekt.modalForm.smazani.submit.button"),
            "form_check": form_check,
        }
        return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["POST"])
def odebrat_sloupec_z_vychozich(request):
    if request.method == "POST":
        if "projekt_vychozi_skryte_sloupce" not in request.session:
            request.session["projekt_vychozi_skryte_sloupce"] = []
        sloupec = json.loads(request.body.decode("utf8"))["sloupec"]
        zmena = json.loads(request.body.decode("utf8"))["zmena"]
        skryte_sloupce = request.session["projekt_vychozi_skryte_sloupce"]
        if zmena == "zobraz":
            try:
                skryte_sloupce.remove(sloupec)
            except ValueError:
                logger.error(
                    f"projekt.odebrat_sloupec_z_vychozich nelze odebrat sloupec {sloupec}"
                )
                HttpResponse(f"Nelze odebrat sloupec {sloupec}", status=400)
        else:
            skryte_sloupce.append(sloupec)
        request.session.modified = True
    return HttpResponse("Odebráno")


class ProjektListView(SearchListView):
    table_class = ProjektTable
    model = Projekt
    template_name = "projekt/projekt_list.html"
    filterset_class = ProjektFilter
    export_name = "export_projekty_"
    page_title = _("projekt.vyber.pageTitle")
    app = "projekt"
    toolbar = "toolbar_projekt.html"
    search_sum = _("projekt.vyber.pocetVyhledanych")
    pick_text = _("projekt.vyber.pickText")
    hasOnlyVybrat_header = _("projekt.vyber.header.hasOnlyVybrat")
    hasOnlyArchive_header = _("projekt.vyber.header.hasOnlyArchive")
    default_header = _("projekt.vyber.header.default")
    toolbar_name = _("projekt.template.toolbar.title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hasSchvalitOznameni_header"] = _(
            "projekt.vyber.header.hasSchvalitOznameni"
        )
        context["hasPrihlasit_header"] = _("projekt.vyber.header.hasPrihlasit")
        context["hasPrihlasit_header"] = _("projekt.vyber.header.hasPrihlasit")
        context["hasZahajitVyzkum_header"] = _("projekt.vyber.header.hasZahajitVyzkum")
        context["hasUkoncitTeren_header"] = _("projekt.vyber.header.hasUkoncitTeren")
        context["hasSpravovatAkce_header"] = _("projekt.vyber.header.hasSpravovatAkce")
        context["hasUzavritProjekt_header"] = _(
            "projekt.vyber.header.hasUzavritProjekt"
        )
        context["hasNaseProjekty_header"] = _("projekt.vyber.header.hasNaseProjekty")
        context["has_header"] = _("projekt.vyber.header.hasNaseProjekty")
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        qs = (
            qs.filter(stav__gt=PROJEKT_STAV_VYTVORENY)
            .select_related(
                "kulturni_pamatka",
                "typ_projektu",
                "hlavni_katastr",
                "organizace",
                "vedouci_projektu",
                "hlavni_katastr__okres",
            )
            .defer("geom")
        )
        return qs


@login_required
@require_http_methods(["GET", "POST"])
def schvalit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_OZNAMENY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        projekt.set_schvaleny(request.user)
        if projekt.ident_cely[0] == "X":
            try:
                projekt.set_permanent_ident_cely()
            except MaximalIdentNumberError:
                messages.add_message(request, messages.SUCCESS, MAXIMUM_IDENT_DOSAZEN)
                return JsonResponse(
                    {
                        "redirect": reverse(
                            "projekt:detail", kwargs={"ident_cely": ident_cely}
                        )
                    },
                    status=403,
                )
            else:
                logger.debug(
                    "Projektu "
                    + ident_cely
                    + " byl prirazen permanentni ident "
                    + projekt.ident_cely
                )
        projekt.save()
        if projekt.typ_projektu.pk == TYP_PROJEKTU_ZACHRANNY_ID:
            projekt.create_confirmation_document(user=request.user)
        messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_SCHVALEN)
        if projekt.ident_cely[0] == "C":
            Mailer.send_ep01a(project=projekt)
        else:
            Mailer.send_ep01b(project=projekt)
        return JsonResponse(
            {
                "redirect": reverse(
                    "projekt:detail", kwargs={"ident_cely": projekt.ident_cely}
                )
            }
        )
    form_check = CheckStavNotChangedForm(initial={"old_stav": projekt.stav})
    context = {
        "object": projekt,
        "title": _("projekt.modalForm.schvaleni.title.text"),
        "id_tag": "schvalit-form",
        "button": _("projekt.modalForm.schvaleni.submit.button"),
        "form_check": form_check,
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def prihlasit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_ZAPSANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    logger.debug("something")
    if request.method == "POST":
        form = PrihlaseniProjektForm(request.POST, instance=projekt)
        if form.is_valid():
            projekt = form.save(commit=False)
            projekt.set_prihlaseny(request.user)
            messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_PRIHLASEN)
            if projekt.ident_cely[0] == "C":
                Mailer.send_ep03a(project=projekt)
            else:
                Mailer.send_ep03b(project=projekt)
            return JsonResponse(
                {
                    "redirect": reverse(
                        "projekt:detail", kwargs={"ident_cely": ident_cely}
                    )
                }
            )
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        archivar = True if request.user.hlavni_role.id == ROLE_ARCHIVAR_ID else False
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
@require_http_methods(["GET", "POST"])
def zahajit_v_terenu(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_PRIHLASENY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = ZahajitVTerenuForm(request.POST, instance=projekt)

        if form.is_valid():
            projekt = form.save(commit=False)
            projekt.set_zahajeny_v_terenu(request.user)
            messages.add_message(
                request, messages.SUCCESS, PROJEKT_USPESNE_ZAHAJEN_V_TERENU
            )
            return JsonResponse(
                {
                    "redirect": reverse(
                        "projekt:detail", kwargs={"ident_cely": ident_cely}
                    )
                }
            )
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = ZahajitVTerenuForm(instance=projekt, initial={"old_stav": projekt.stav})
    return render(
        request,
        "projekt/transakce_v_terenu.html",
        {
            "form": form,
            "object": projekt,
            "title": _("projekt.modalForm.zahajitvTerenu.title.text"),
            "id_tag": "zahajit-v-terenu-form",
            "button": _("projekt.modalForm.zahajitvTerenu.submit.button"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def ukoncit_v_terenu(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_ZAHAJENY_V_TERENU:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = UkoncitVTerenuForm(request.POST, instance=projekt)
        if form.is_valid():
            projekt = form.save(commit=False)
            projekt.set_ukoncen_v_terenu(request.user)
            messages.add_message(
                request, messages.SUCCESS, PROJEKT_USPESNE_UKONCEN_V_TERENU
            )
            return JsonResponse(
                {
                    "redirect": reverse(
                        "projekt:detail", kwargs={"ident_cely": ident_cely}
                    )
                }
            )
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = UkoncitVTerenuForm(instance=projekt, initial={"old_stav": projekt.stav})
    return render(
        request,
        "projekt/transakce_v_terenu.html",
        {
            "form": form,
            "object": projekt,
            "title": _("projekt.modalForm.ukoncitvTerenu.title.text"),
            "id_tag": "ukoncit-v-terenu-form",
            "button": _("projekt.modalForm.ukoncitvTerenu.submit.button"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def uzavrit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_UKONCENY_V_TERENU:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        # Move all events to state A2
        akce = Akce.objects.filter(projekt=projekt)
        for a in akce:
            if a.archeologicky_zaznam.stav == AZ_STAV_ZAPSANY:
                logger.debug("Setting event to state A2")
                a.archeologicky_zaznam.set_odeslany(request.user)
            for dokument_cast in a.archeologicky_zaznam.casti_dokumentu.all():
                if dokument_cast.dokument.stav == D_STAV_ZAPSANY:
                    logger.debug("Setting dokument to state D2")
                    dokument_cast.dokument.set_odeslany(request.user)
        projekt.set_uzavreny(request.user)
        messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_UZAVREN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})}
        )
    else:
        # Check business rules
        warnings = projekt.check_pred_uzavrenim()
        logger.debug(warnings)
        form_check = CheckStavNotChangedForm(initial={"old_stav": projekt.stav})
        if warnings:
            request.session["temp_data"] = []
            for key, item in warnings.items():
                if key == "has_event":
                    request.session["temp_data"].append(item)
                else:
                    items = ""
                    for i, list_items in enumerate(item):
                        if isinstance(list_items, list):
                            items += list_items.pop(0)
                            items += ", ".join(list_items)
                        else:
                            items += list_items
                        if i + 1 < len(item):
                            items += ", "
                    request.session["temp_data"].append(f"{key}: {items}")
            messages.add_message(request, messages.ERROR, PROJEKT_NELZE_UZAVRIT)
            return JsonResponse(
                {
                    "redirect": reverse(
                        "projekt:detail", kwargs={"ident_cely": ident_cely}
                    )
                },
                status=403,
            )

        context = {
            "object": projekt,
            "title": _("projekt.modalForm.uzavrit.title.text"),
            "id_tag": "uzavrit-form",
            "button": _("projekt.modalForm.uzavrit.submit.button"),
            "form_check": form_check,
        }

        return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def archivovat(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_UZAVRENY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, projekt):
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        projekt.set_archivovany(request.user)
        projekt.save()
        messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_ARCHIVOVAN)
        return JsonResponse(
            {"redirect": reverse("projekt:detail", kwargs={"ident_cely": ident_cely})}
        )
    else:
        warnings = projekt.check_pred_archivaci()
        logger.debug(warnings)
        form_check = CheckStavNotChangedForm(initial={"old_stav": projekt.stav})
        if warnings:
            request.session["temp_data"] = []
            for key, item in warnings.items():
                request.session["temp_data"].append(f"{key}: {item}")
            messages.add_message(request, messages.ERROR, PROJEKT_NELZE_ARCHIVOVAT)
            return JsonResponse(
                {
                    "redirect": reverse(
                        "projekt:detail", kwargs={"ident_cely": ident_cely}
                    )
                },
                status=403,
            )
    if request.GET.get("from_arch") == "true":
        context = {
            "object": projekt,
            "title": _("arch_z.modal.archivovatProjekt.title"),
            "text": _("arch_z.modal.archivovatProjekt.text"),
            "id_tag": "archivovat-form",
            "button": _("arch_z.modal.archivovatProjekt.confirmButton.text"),
            "form_check": form_check,
        }
    else:
        context = {
            "object": projekt,
            "title": _("projekt.modalForm.archivovat.title.text"),
            "id_tag": "archivovat-form",
            "button": _("projekt.modalForm.archivovat.submit.button"),
            "form_check": form_check,
        }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def navrhnout_ke_zruseni(request, ident_cely):
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
                duvod_to_save = str(
                    duvod_to_save + " " + form.cleaned_data["projekt_id"]
                )
            elif duvod == "option6":
                duvod_to_save = form.cleaned_data["reason_text"]
            else:
                duvod_to_save = duvod_to_save
            logger.debug(duvod_to_save)
            projekt.set_navrzen_ke_zruseni(request.user, duvod_to_save)
            projekt.save()
            messages.add_message(
                request, messages.SUCCESS, PROJEKT_USPESNE_NAVRZEN_KE_ZRUSENI
            )
            return JsonResponse(
                {
                    "redirect": reverse(
                        "projekt:detail", kwargs={"ident_cely": ident_cely}
                    )
                }
            )
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
            context = {"projekt": projekt, "form": form}
    else:
        warnings = projekt.check_pred_navrzeni_k_zruseni()
        logger.debug(warnings)

        if warnings:
            request.session["temp_data"] = []
            for key, item in warnings.items():
                if key == "has_event":
                    request.session["temp_data"].append(item)
            messages.add_message(
                request, messages.ERROR, PROJEKT_NELZE_NAVRHNOUT_KE_ZRUSENI
            )
            return JsonResponse(
                {
                    "redirect": reverse(
                        "projekt:detail", kwargs={"ident_cely": ident_cely}
                    )
                },
                status=403,
            )
        context = {
            "projekt": projekt,
            "form": NavrhnoutZruseniProjektForm(initial={"old_stav": projekt.stav}),
        }
    return render(request, "projekt/navrhnout_zruseni.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def zrusit(request, ident_cely):
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
            projekt.set_zruseny(request.user, duvod)
            projekt.save()
            messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_ZRUSEN)
            Mailer.send_ep04(project=projekt, reason=duvod)
            if projekt.ident_cely[0] == "C":
                Mailer.send_ep06a(project=projekt, reason=duvod)
            else:
                Mailer.send_ep06b(project=projekt, reason=duvod)
            return JsonResponse(
                {
                    "redirect": reverse(
                        "projekt:detail", kwargs={"ident_cely": ident_cely}
                    )
                }
            )
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
            context = context = {
                "object": projekt,
                "title": _("projekt.modalForm.zruseni.title.text"),
                "id_tag": "zrusit-form",
                "button": _("projekt.modalForm.zruseni.submit.button"),
                "form_check": form_check,
                "form": form,
            }
    else:
        form_check = CheckStavNotChangedForm(initial={"old_stav": projekt.stav})
        context = {
            "object": projekt,
            "title": _("projekt.modalForm.zruseni.title.text"),
            "id_tag": "zrusit-form",
            "button": _("projekt.modalForm.zruseni.submit.button"),
            "form_check": form_check,
        }
        if projekt.stav == PROJEKT_STAV_NAVRZEN_KE_ZRUSENI:
            last_history_poznamka = (
                projekt.historie.historie_set.filter(typ_zmeny=NAVRZENI_KE_ZRUSENI_PROJ)
                .order_by("-datum_zmeny")[0]
                .poznamka
            )
            logger.debug(last_history_poznamka)
            context["form"] = ZruseniProjektForm(
                initial={"reason_text": last_history_poznamka}
            )
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
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
            projekt_mail = projekt
            if projekt.stav == PROJEKT_STAV_PRIHLASENY:
                Mailer.send_ep07(project=projekt_mail, reason=duvod)
            projekt.set_vracen(request.user, projekt.stav - 1, duvod)
            projekt.save()
            messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_VRACEN)
            return JsonResponse(
                {
                    "redirect": reverse(
                        "projekt:detail", kwargs={"ident_cely": ident_cely}
                    )
                }
            )
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = VratitForm(initial={"old_stav": projekt.stav})
    context = {
        "object": projekt,
        "form": form,
        "title": _("projekt.modalForm.vraceni.title.text"),
        "id_tag": "vratit-form",
        "button": _("projekt.modalForm.vraceni.submit.button"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def vratit_navrh_zruseni(request, ident_cely):
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
            projekt.set_znovu_zapsan(request.user, duvod)
            projekt.save()
            messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_VRACEN)
            Mailer.send_ep05(project=projekt)
            return JsonResponse(
                {
                    "redirect": reverse(
                        "projekt:detail", kwargs={"ident_cely": ident_cely}
                    )
                }
            )
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = VratitForm(initial={"old_stav": projekt.stav})
    context = {
        "object": projekt,
        "form": form,
        "title": _("projekt.modalForm.vratitNavrhZruseni.title.text"),
        "id_tag": "vratit-navrh-form",
        "button": _("projekt.modalForm.vratitNavrhZruseni.submit.button"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def odpojit_dokument(request, ident_cely, proj_ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=proj_ident_cely)
    return odpojit(request, ident_cely, proj_ident_cely, projekt)


@login_required
@require_http_methods(["GET", "POST"])
def pripojit_dokument(request, proj_ident_cely):
    return pripojit(request, proj_ident_cely, None, Projekt)


@login_required
@require_http_methods(["POST"])
def generovat_oznameni(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    projekt.create_confirmation_document(additional=True, user=request.user)
    if projekt.ident_cely[0] == "C":
        Mailer.send_ep01a(project=projekt)
    else:
        Mailer.send_ep01b(project=projekt)
    return redirect("projekt:detail", ident_cely=ident_cely)


@login_required
@require_http_methods(["POST"])
def generovat_expertni_list(request, ident_cely):
    popup_parametry = request.POST
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    path = projekt.create_expert_list(popup_parametry)
    file = open(path, "rb")
    return FileResponse(file)


def get_history_dates(historie_vazby):
    # Transakce do stavu "Zapsan" jsou 2
    historie = {
        "datum_oznameni": historie_vazby.get_last_transaction_date(OZNAMENI_PROJ),
        "datum_zapsani": historie_vazby.get_last_transaction_date(
            [
                VRACENI_NAVRHU_ZRUSENI,
                SCHVALENI_OZNAMENI_PROJ,
                ZAPSANI_PROJ,
                VRACENI_ZRUSENI,
            ]
        ),
        "datum_prihlaseni": historie_vazby.get_last_transaction_date(PRIHLASENI_PROJ),
        "datum_zahajeni_v_terenu": historie_vazby.get_last_transaction_date(
            ZAHAJENI_V_TERENU_PROJ
        ),
        "datum_ukonceni_v_terenu": historie_vazby.get_last_transaction_date(
            UKONCENI_V_TERENU_PROJ
        ),
        "datum_uzavreni": historie_vazby.get_last_transaction_date(UZAVRENI_PROJ),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_PROJ),
        "datum_navrhu_ke_zruseni": historie_vazby.get_last_transaction_date(
            NAVRZENI_KE_ZRUSENI_PROJ
        ),
        "datum_zruseni": historie_vazby.get_last_transaction_date(RUSENI_PROJ),
    }
    return historie


def get_detail_template_shows(projekt, user):
    show_oznamovatel = (
        projekt.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID
        and projekt.has_oznamovatel()
    )
    show_prihlasit = projekt.stav == PROJEKT_STAV_ZAPSANY
    show_vratit = PROJEKT_STAV_ARCHIVOVANY >= projekt.stav > PROJEKT_STAV_ZAPSANY
    show_schvalit = projekt.stav == PROJEKT_STAV_OZNAMENY
    show_zahajit = projekt.stav == PROJEKT_STAV_PRIHLASENY
    show_ukoncit = projekt.stav == PROJEKT_STAV_ZAHAJENY_V_TERENU
    show_uzavrit = projekt.stav == PROJEKT_STAV_UKONCENY_V_TERENU
    show_archivovat = projekt.stav == PROJEKT_STAV_UZAVRENY
    show_navrzen_ke_zruseni = projekt.stav not in [
        PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
        PROJEKT_STAV_ZRUSENY,
        PROJEKT_STAV_ARCHIVOVANY,
        PROJEKT_STAV_OZNAMENY,
    ]
    show_zrusit = projekt.stav in [
        PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
    ]
    show_znovu_zapsat = projekt.stav in [
        PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
        PROJEKT_STAV_ZRUSENY,
    ]
    show_samostatne_nalezy = projekt.typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID
    archivar_group = Group.objects.get(id=ROLE_ARCHIVAR_ID)
    admin_group = Group.objects.get(id=ROLE_ADMIN_ID)
    show_pridat_akci = False
    show_pridat_sam_nalez = False
    show_pridat_oznamovatele = False
    if projekt.typ_projektu.id != TYP_PROJEKTU_PRUZKUM_ID:
        if user.hlavni_role == archivar_group or user.hlavni_role == admin_group:
            show_pridat_akci = (
                PROJEKT_STAV_PRIHLASENY < projekt.stav < PROJEKT_STAV_ARCHIVOVANY
            )
        else:
            show_pridat_akci = (
                PROJEKT_STAV_PRIHLASENY < projekt.stav < PROJEKT_STAV_UZAVRENY
            )
    else:
        if user.hlavni_role == archivar_group or user.hlavni_role == admin_group:
            show_pridat_sam_nalez = (
                PROJEKT_STAV_PRIHLASENY < projekt.stav < PROJEKT_STAV_ARCHIVOVANY
            )
        else:
            show_pridat_sam_nalez = (
                PROJEKT_STAV_PRIHLASENY < projekt.stav < PROJEKT_STAV_UZAVRENY
            )
    if projekt.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID:
        if user.hlavni_role == archivar_group or user.hlavni_role == admin_group:
            if not projekt.has_oznamovatel():
                if PROJEKT_STAV_ZAPSANY <= projekt.stav <= PROJEKT_STAV_UZAVRENY:
                    show_pridat_oznamovatele = True
    show_edit = projekt.stav not in [
        PROJEKT_STAV_ARCHIVOVANY,
    ]
    show_dokumenty = projekt.typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID
    show_arch_links = projekt.stav == PROJEKT_STAV_ARCHIVOVANY
    show_akce = projekt.typ_projektu.id != TYP_PROJEKTU_PRUZKUM_ID
    show_pripojit_dokumenty = projekt.stav in [
        PROJEKT_STAV_ZAHAJENY_V_TERENU,
        PROJEKT_STAV_UKONCENY_V_TERENU,
        PROJEKT_STAV_UZAVRENY,
    ]
    show = {
        "oznamovatel": show_oznamovatel,
        "prihlasit_link": show_prihlasit,
        "vratit_link": show_vratit,
        "schvalit_link": show_schvalit,
        "zahajit_teren_link": show_zahajit,
        "ukoncit_teren_link": show_ukoncit,
        "uzavrit_link": show_uzavrit,
        "archivovat_link": show_archivovat,
        "navrhnout_zruseni_link": show_navrzen_ke_zruseni,
        "zrusit_link": show_zrusit,
        "znovu_zapsat_link": show_znovu_zapsat,
        "samostatne_nalezy": show_samostatne_nalezy,
        "pridat_akci": show_pridat_akci,
        "editovat": show_edit,
        "dokumenty": show_dokumenty,
        "arch_links": show_arch_links,
        "akce": show_akce,
        "pripojit_dokumenty": show_pripojit_dokumenty,
        "pridat_sam_nalez": show_pridat_sam_nalez,
        "pridat_oznamovatele": show_pridat_oznamovatele,
    }
    return show


def get_required_fields(zaznam=None, next=0):
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
    if (
        PROJEKT_STAV_ZAHAJENY_V_TERENU - next
        < stav
        < PROJEKT_STAV_NAVRZEN_KE_ZRUSENI - next
    ):
        required_fields += ["datum_ukonceni"]
    if (
        PROJEKT_STAV_UKONCENY_V_TERENU - next
        < stav
        < PROJEKT_STAV_NAVRZEN_KE_ZRUSENI - next
    ):
        required_fields += ["termin_odevzdani_nz"]
    return required_fields


def katastr_text_to_id(request):
    hlavni_katastr: str = request.POST.get("hlavni_katastr")
    hlavni_katastr_name = hlavni_katastr[: hlavni_katastr.find("(")].strip()
    okres_name = (
        (hlavni_katastr[hlavni_katastr.find("(") + 1 :]).replace(")", "").strip()
    )
    katastr_query = RuianKatastr.objects.filter(
        Q(nazev=hlavni_katastr_name) & Q(okres__nazev=okres_name)
    )
    if katastr_query.count() > 0:
        post = request.POST.copy()
        post["hlavni_katastr"] = katastr_query.first().id
        return post
    else:
        if hlavni_katastr_name.isnumeric() and okres_name.isnumeric():
            logger.debug(
                f"Katastr {hlavni_katastr_name} and {okres_name} are already numbers"
            )
        else:
            logger.error(f"Cannot find katastr {hlavni_katastr_name} in {okres_name}!")
        return request.POST.copy()


class ProjektAutocompleteBezZrusenych(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Projekt.objects.none()
        typ = self.kwargs.get("typ")
        if typ == "projekt":
            qs = (
                Projekt.objects.filter(
                    stav__gte=PROJEKT_STAV_ZAHAJENY_V_TERENU,
                    stav__lte=PROJEKT_STAV_ARCHIVOVANY,
                )
                .exclude(typ_projektu__id=TYP_PROJEKTU_PRUZKUM_ID)
                .annotate(ident_len=Length("ident_cely"))
                .filter(ident_len__gt=0)
            )
        else:
            qs = (
                Projekt.objects.filter(
                    stav__gte=PROJEKT_STAV_ZAHAJENY_V_TERENU,
                    stav__lte=PROJEKT_STAV_ARCHIVOVANY,
                )
                .filter(typ_projektu__id=TYP_PROJEKTU_PRUZKUM_ID)
                .annotate(ident_len=Length("ident_cely"))
                .filter(ident_len__gt=0)
            )
        if self.q:
            qs = qs.filter(ident_cely__icontains=self.q)
        return qs


class ProjectTableRowView(LoginRequiredMixin, View):
    def get(self, request):
        context = {"p": Projekt.objects.get(id=request.GET.get("id", ""))}
        return HttpResponse(render_to_string("projekt/projekt_table_row.html", context))
