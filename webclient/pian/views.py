import logging
import pandas as pd

from core.constants import KLADYZM10, KLADYZM50, PIAN_NEPOTVRZEN, PIAN_POTVRZEN, ROLE_ADMIN_ID, ZAPSANI_AZ, ZAPSANI_PIAN, ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID
from core.exceptions import MaximalIdentNumberError, NeznamaGeometrieError
from core.ident_cely import get_temporary_pian_ident
from core.message_constants import (
    MAXIMUM_IDENT_DOSAZEN,
    PIAN_NEVALIDNI_GEOMETRIE,
    PIAN_USPESNE_ODPOJEN,
    PIAN_USPESNE_POTVRZEN,
    PIAN_USPESNE_SMAZAN,
    PIAN_VALIDACE_VYPNUTA,
    VALIDATION_EMPTY,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from core.repository_connector import FedoraTransaction, FedoraRepositoryConnector
from core.utils import (
    file_validate_epsg,
    validate_and_split_geometry,
    get_validation_messages,
    update_all_katastr_within_akce_or_lokalita,
    get_dj_akce_for_pian,
)
from dal import autocomplete
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.db.models.functions import Centroid
from django.contrib.gis.geos import LineString, Point, Polygon
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.db import connection
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.db.models import OuterRef, Subquery, Q, FilteredRelation
from django.urls import reverse
from heslar.hesla_dynamicka import GEOMETRY_BOD, GEOMETRY_LINIE, GEOMETRY_PLOCHA, PRISTUPNOST_BADATEL_ID, PRISTUPNOST_ARCHEOLOG_ID, PRISTUPNOST_ARCHIVAR_ID, PRISTUPNOST_ANONYM_ID
from heslar.models import Heslar
from pian.forms import PianCreateForm
from pian.models import Kladyzm, Pian
from core.views import PermissionFilterMixin
from core.models import Permissions
from historie.models import Historie
from arch_z.models import ArcheologickyZaznam
from heslar.hesla import HESLAR_PRISTUPNOST

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def detail(request, ident_cely):
    """
    Funkce pohledu pro zapsání změny pianu.
    """
    dj_ident_cely = request.POST["dj_ident_cely"]
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    pian = get_object_or_404(Pian, ident_cely=ident_cely)
    if pian == PIAN_POTVRZEN:
        raise PermissionDenied
    form = PianCreateForm(
        data=request.POST,
        instance=pian,
    )
    c = connection.cursor()
    validation_results = ""
    validation_geom = ""
    logger.debug("pian.views.detail.start")
    try:
        dict1 = dict(request.POST)
        logger.debug("pian.views.detail", extra={"post": dict1.items()})
        for key in dict1.keys():
            if key == "geom":
                validation_geom = dict1.get(key)[0]
                c.execute("BEGIN")
                c.callproc("validateGeom", [validation_geom])
                validation_results = c.fetchone()[0]
                logger.debug("pian.views.detail", extra={"validation_results": validation_results,
                                                         "validation_geom": validation_geom, "key": key})
                c.execute("COMMIT")
    except Exception as e:
        logger.debug(e)
        validation_results = PIAN_VALIDACE_VYPNUTA
    finally:
        c.close()
    if validation_geom == "undefined":
        messages.add_message(
            request,
            messages.ERROR,
            PIAN_NEVALIDNI_GEOMETRIE + " " + get_validation_messages(VALIDATION_EMPTY),
        )
    elif validation_results == PIAN_VALIDACE_VYPNUTA:
        messages.add_message(request, messages.ERROR, PIAN_VALIDACE_VYPNUTA)
    elif validation_results != "valid":
        messages.add_message(
            request,
            messages.ERROR,
            PIAN_NEVALIDNI_GEOMETRIE
            + " "
            + get_validation_messages(validation_results),
        )
    elif form.is_valid():
        logger.debug("pian.views.detail.form.valid", extra={"pian_ident_cely": pian.ident_cely})
        pian = form.save(commit=False)
        fedora_transaction = pian.create_transaction(request.user)
        pian.save()
        djs=DokumentacniJednotka.objects.filter(pian__ident_cely=ident_cely)
        for fdj in djs:
            update_all_katastr_within_akce_or_lokalita(fdj, fedora_transaction)
        pian.close_active_transaction_when_finished = True
        pian.save()
        if form.changed_data:
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        logger.debug("pian.views.detail.form.finished", extra={"transaction": fedora_transaction.uid})
    else:
        logger.debug("pian.views.detail.form.not_valid", extra={"form_errors": form.errors})
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

    response = redirect(dj.get_absolute_url())
    if validation_results != "valid" and validation_results != PIAN_VALIDACE_VYPNUTA:
        response = redirect(dj.get_absolute_url()+"/pian/edit/"+str(ident_cely))
    response.set_cookie("show-form", f"detail_dj_form_{dj_ident_cely}", max_age=1000)
    response.set_cookie(
        "set-active",
        f"el_div_dokumentacni_jednotka_{dj_ident_cely.replace('-', '_')}",
        max_age=1000,
    )
    return response


@login_required
@require_http_methods(["GET", "POST"])
def odpojit(request, dj_ident_cely):
    """
    Funkce pohledu pro odpojení pianu pomocí modalu.
    """
    dj: DokumentacniJednotka = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    pian_djs = DokumentacniJednotka.objects.filter(pian=dj.pian)
    delete_pian = (
        True if pian_djs.count() < 2 and dj.pian.stav == PIAN_NEPOTVRZEN else False
    )
    pian = dj.pian
    pian: Pian
    if request.method == "POST":
        fedora_transaction = dj.archeologicky_zaznam.create_transaction(request.user)
        dj.archeologicky_zaznam.get_absolute_url()
        dj.pian = None
        dj.active_transaction = fedora_transaction
        dj.save()
        update_all_katastr_within_akce_or_lokalita(dj, fedora_transaction)
        logger.debug("pian.views.odpojit.odpojen", extra={"pian_ident_cely": pian.ident_cely,
                                                          "transaction": fedora_transaction.uid})
        if delete_pian:
            pian.skip_container_check = True
            pian.active_transaction = fedora_transaction
            try:
                pian.delete()
                dj.initial_pian = None
                logger.debug("pian.views.odpojit.smazan", extra={"pian_ident_cely": pian.ident_cely,
                                                                 "transaction": fedora_transaction.uid})
            except ValueError as err:
                logger.debug("pian.views.odpojit.error", extra={"pian_ident_cely": pian.ident_cely,
                                                                "transaction": fedora_transaction.uid, "err": err})

            messages.add_message(request, messages.SUCCESS, PIAN_USPESNE_SMAZAN)
        else:
            messages.add_message(request, messages.SUCCESS, PIAN_USPESNE_ODPOJEN)
        dj.close_active_transaction_when_finished = True
        dj.save()
        logger.debug("pian.views.odpojit.finished", extra={"transaction": fedora_transaction.uid})
        response = JsonResponse({"redirect": dj.get_absolute_url()})
        response.set_cookie(
            "show-form", f"detail_dj_form_{dj.ident_cely}", max_age=1000
        )
        response.set_cookie(
            "set-active",
            f"el_div_dokumentacni_jednotka_{dj.ident_cely.replace('-', '_')}",
            max_age=1000,
        )
        return response
    else:
        context = {
            "object": pian,
            "title": _("pian.views.odpojit.title.text"),
            "id_tag": "odpojit-pian-form",
            "button": _("pian.views.odpojit.submit.button"),
            "text": _("pian.views.odpojit.text.part1")
            + pian.ident_cely
            + _("pian.views.odpojit.text.part2")
            + dj.ident_cely
            + "?",
        }
        return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def potvrdit(request, dj_ident_cely):
    """
    Funkce pohledu pro potvrzení pianu pomocí modalu.
    """
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    pian = dj.pian
    if pian == PIAN_POTVRZEN:
        raise PermissionDenied
    if request.method == "POST":
        redirect_view = dj.archeologicky_zaznam.get_absolute_url(dj_ident_cely)
        fedora_transaction = pian.create_transaction(request.user)
        try:
            old_ident = pian.ident_cely
            pian.set_permanent_ident_cely()
        except MaximalIdentNumberError:
            messages.add_message(request, messages.ERROR, MAXIMUM_IDENT_DOSAZEN)
            logger.debug("pian.views.potvrdit", extra={"pian_ident_cely": pian.ident_cely,
                                                       "transaction": fedora_transaction.uid})
            fedora_transaction.mark_transaction_as_closed()
            return JsonResponse(
                {"redirect": redirect_view},
                status=403,
            )
        else:
            pian.set_potvrzeny(request.user, old_ident)
            pian.close_active_transaction_when_finished = True
            pian.save()
            logger.debug("pian.views.potvrdit.potvrzen", extra={"pian_ident_cely": pian.ident_cely,
                                                                "transaction": fedora_transaction.uid})
            messages.add_message(request, messages.SUCCESS, PIAN_USPESNE_POTVRZEN)
            response = JsonResponse({"redirect": dj.get_absolute_url()})
            response.set_cookie(
                "show-form", f"detail_dj_form_{dj.ident_cely}", max_age=1000
            )
            response.set_cookie(
                "set-active",
                f"el_div_dokumentacni_jednotka_{dj.ident_cely.replace('-', '_')}",
                max_age=1000,
            )
            return response
    context = {
        "object": pian,
        "title": _("pian.views.potvrdit.title.text"),
        "id_tag": "potvrdit-pian-form",
        "button": _("pian.views.potvrdit.submitButton.text"),
        "text": _("pian.views.potvrdit.text") + pian.ident_cely + "?",
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["POST"])
def create(request, dj_ident_cely):
    """
    Funkce pohledu pro vytvoření pianu.
    """
    logger.debug("pian.views.create.start")
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    form = PianCreateForm(data=request.POST)
    logger.debug("pian.views.create.form_data", extra={"form_data": form.data, "post_data": request.POST})
    c = connection.cursor()
    try:
        c.execute("BEGIN")
        c.callproc("validateGeom", [str(form.data["geom"])])
        validation_results = c.fetchone()[0]
        c.execute("COMMIT")
        logger.debug("pian.views.create.commit", extra={"validation_results": validation_results,
                                                        "geom": str(form.data["geom"])})
    except Exception as ex:
        logger.warning("pian.views.create.validation_exception", extra={"exception": ex})
        validation_results = PIAN_VALIDACE_VYPNUTA
    finally:
        c.close()
    if validation_results == PIAN_VALIDACE_VYPNUTA:
        messages.add_message(request, messages.ERROR, PIAN_VALIDACE_VYPNUTA)
    elif validation_results != "valid":
        messages.add_message(
            request,
            messages.ERROR,
            PIAN_NEVALIDNI_GEOMETRIE
            + " "
            + get_validation_messages(validation_results),
        )
        logger.debug("pian.views.create", extra={"error_message": PIAN_NEVALIDNI_GEOMETRIE})
        response = redirect(dj.get_absolute_url()+"/pian/zapsat")
        return response
    elif form.is_valid():
        logger.debug("pian.views.create.form_valid")
        pian = form.save(commit=False)
        # Assign base map references
        if type(pian.geom) == Point:
            pian.typ = Heslar.objects.get(id=GEOMETRY_BOD)
            point = pian.geom
        elif type(pian.geom) == LineString:
            pian.typ = Heslar.objects.get(id=GEOMETRY_LINIE)
            point = pian.geom.interpolate(0.5)
        elif type(pian.geom) == Polygon:
            pian.typ = Heslar.objects.get(id=GEOMETRY_PLOCHA)
            point = Centroid(pian.geom)
        else:
            raise NeznamaGeometrieError()
        logger.debug("pian.views.create.geom", extra={"geom": str(form.data["geom"])})
        zm10s = (
            Kladyzm.objects.filter(kategorie=KLADYZM10)            
            .filter(the_geom__contains=point)
        )
        zm50s = (
            Kladyzm.objects.filter(kategorie=KLADYZM50)
            .filter(the_geom__contains=point)
        )
        if zm10s.count() == 1 and zm50s.count() == 1:
            pian.zm10 = zm10s[0]
            pian.zm50 = zm50s[0]
            try:
                pian.ident_cely = get_temporary_pian_ident(zm50s[0])
            except MaximalIdentNumberError as e:
                logger.warning("pian.views.create.error", extra={"message": messages.ERROR, "exception": e.message})
                messages.add_message(request, messages.ERROR, e.message)
            else:
                if FedoraRepositoryConnector.check_container_deleted_or_not_exists(pian.ident_cely, "pian"):
                    fedora_transaction = pian.create_transaction(request.user)
                    pian.save()
                    pian.set_vymezeny(request.user)
                    dj.active_transaction = fedora_transaction
                    dj.pian = pian
                    dj.save()
                    update_all_katastr_within_akce_or_lokalita(dj, fedora_transaction)
                    pian.close_active_transaction_when_finished = True
                    pian.save()
                    logger.debug("pian.views.create.finished",
                                 extra={"info": ZAZNAM_USPESNE_VYTVOREN, "dj_pk": dj.pk,
                                        "transaction": fedora_transaction.uid})
                    messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
                else:
                    logger.info("pian.views.create.check_container_deleted_or_not_exists.incorrect",
                                extra={"ident_cely": pian.ident_cely})
                    messages.add_message(
                        request, messages.SUCCESS, ZAZNAM_SE_NEPOVEDLO_VYTVORIT
                    )
        else:
            logger.info("pian.views.create.assignment_error", extra={"zm10s": zm10s, "zm50s": zm50s})
            messages.add_message(
                request, messages.SUCCESS, ZAZNAM_SE_NEPOVEDLO_VYTVORIT
            )
        redirect(dj.get_absolute_url())
    else:
        logger.info("pian.views.create.not_valid", extra={"errors": form.errors})
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)

    response = redirect(dj.get_absolute_url())
    response.set_cookie("show-form", f"detail_dj_form_{dj.ident_cely}", max_age=1000)
    response.set_cookie(
        "set-active",
        f"el_div_dokumentacni_jednotka_{dj.ident_cely.replace('-', '_')}",
        max_age=1000,
    )
    return response

@login_required
@require_http_methods(["POST"])
def mapa_dj(request, ident_cely):
    """
    Funkce ziskej Dj pro Pian
    """
    logger.debug("pian.views.create.start")
    back=[]
    for i in get_dj_akce_for_pian(ident_cely, request):
        logger.debug(i)#G {'ident_cely': 'C-201339492A-D01', 'archeologicky_zaznam__ident_cely': 'C-201339492A'}
        back.append({
            "dj": str(i['ident_cely']),
            "akce": str(i['archeologicky_zaznam__ident_cely']),
            })

    if back is not None:
        return JsonResponse({"points": back}, status=200,
        )
    else:
        return JsonResponse({"points": None}, status=200)


class PianPermissionFilterMixin(PermissionFilterMixin):

    def filter_by_permission(self, qs, permission):
        qs = qs.annotate(
            historie_zapsat_pian=FilteredRelation(
            "historie__historie",
            condition=Q(**{"historie__historie__typ_zmeny":ZAPSANI_PIAN}),
            ),
            historie_zapsat_az=FilteredRelation(
            "dokumentacni_jednotky_pianu__archeologicky_zaznam__historie__historie",
            condition=Q(**{"dokumentacni_jednotky_pianu__archeologicky_zaznam__historie__historie__typ_zmeny":ZAPSANI_AZ}),
            )
        )
        if not permission.base:
            logger.debug("no base")
            return qs.none()
        if permission.status:
            qs = qs.filter(**self.add_status_lookup(permission))
        if permission.ownership:
            qs = qs.filter(self.add_ownership_lookup(permission.ownership,qs))
        if permission.accessibility:
            qs = self.add_accessibility_lookup(permission,qs)

        return qs
    
    def add_ownership_lookup(self, ownership, qs=None):
        filtered_pian_history = Historie.objects.filter(uzivatel=self.request.user)
        filtered_az_history = Historie.objects.filter(uzivatel=self.request.user)
        if ownership == Permissions.ownershipChoices.our:
            filtered_pian_history_our = Historie.objects.filter(uzivatel__organizace=self.request.user.organizace)            
            return Q(**{"historie_zapsat_pian__in":filtered_pian_history_our}) |  (Q(dokumentacni_jednotky_pianu__archeologicky_zaznam__historie__historie__typ_zmeny=ZAPSANI_AZ) & Q(dokumentacni_jednotky_pianu__archeologicky_zaznam__historie__historie__organizace_snapshot=self.request.user.organizace) ) | Q(**{"dokumentacni_jednotky_pianu__archeologicky_zaznam__akce__projekt__organizace":self.request.user.organizace})
        else:
            return Q(**{"historie_zapsat_pian__in":filtered_pian_history}) | Q(**{"historie_zapsat_az__in":filtered_az_history})

    
    def add_accessibility_lookup(self,permission, qs):
        accessibility_key = self.permission_model_lookup+"pristupnost_filter__in"
        accessibilities = Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST, id__in=self.group_to_accessibility.get(self.request.user.hlavni_role.id))
        filter = {accessibility_key:accessibilities}
        pristupnost = (
            ArcheologickyZaznam.objects.filter(dokumentacni_jednotky_akce__pian=OuterRef("pk"),pristupnost__isnull=False)
            .order_by("pristupnost__razeni")
            .values("pristupnost")
        )
        qs = qs.annotate(pristupnost_filter=Subquery(pristupnost[:1]))
        return qs.filter(Q(**filter)|Q(pristupnost_filter__isnull=True)|Q(self.add_ownership_lookup(permission.accessibility)))


class PianAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView, PianPermissionFilterMixin):
    """
    Třída pohledu pro autocomplete pianu.
    """
    def get_queryset(self):
        qs = Pian.objects.all().order_by("ident_cely")
        if self.q:
            qs = qs.filter(ident_cely__icontains=self.q).exclude(presnost__zkratka="4")
        return self.check_filter_permission(qs)
    

class ImportovatPianView(LoginRequiredMixin, TemplateView):
    """
    Třída pohledu pro získaní řádku tabulky s externím zdrojem.
    """
    sheet = None

    http_method_names = [
        "post",
    ]
    template_name = "pian/pian_import_table.html"

    def post(self, request):
        docfile = request.FILES["file"]
        if docfile.size == 0:
            logger.debug("pian.views.ImportovatPianView.post.label_check.fileEmpty")
            return HttpResponseBadRequest(_("pian.views.importovatPianView.check.fileEmpty."))
        try:
            sheet = pd.read_csv(docfile, sep=",")
        except ValueError as err:
            logger.debug("pian.views.ImportovatPianView.post.label_check.unreadable_or_empty",
                         extra={"err": err})
            return HttpResponseBadRequest(_("pian.views.importovatPianView.check.unreadable_or_empty."))
        if sheet.shape[1] == 0:
            return HttpResponseBadRequest(_("pian.views.importovatPianView.check.unreadable_or_empty."))
        if sheet.shape[1] != 3:
            logger.debug("pian.views.ImportovatPianView.post.label_check.incorrect_column_count",
                         extra={"columns": sheet.columns})
            return HttpResponseBadRequest(_("pian.views.importovatPianView.check.wrongColumnName")+" "+
                                          (', '.join(sheet.columns)))
        if sheet.shape[0] == 0:
            logger.debug("pian.views.ImportovatPianView.post.label_check.no_data")
            return HttpResponseBadRequest(_("pian.views.importovatPianView.check.no_data"))
        if not isinstance(sheet.columns[0], str) or sheet.columns[0].lower() != "label":
            logger.debug("pian.views.ImportovatPianView.post.label_check.column0",
                         extra={"columns": sheet.columns})
            return HttpResponseBadRequest(_("pian.views.importovatPianView.check.wrongColumnName.Column0")+" "+
                                          sheet.columns[0])
        if not isinstance(sheet.columns[1], str) or sheet.columns[1].lower() != "epsg":
            logger.debug("pian.views.ImportovatPianView.post.label_check.column1",
                         extra={"columns": sheet.columns})
            return HttpResponseBadRequest(_("pian.views.importovatPianView.check.wrongColumnName.Column1")+" "+
                                          sheet.columns[1])
        if not isinstance(sheet.columns[2], str) or sheet.columns[2].lower() != "geometry":
            logger.debug("pian.views.ImportovatPianView.post.label_check.column2",
                         extra={"columns": sheet.columns})
            return HttpResponseBadRequest(_("pian.views.importovatPianView.check.wrongColumnName.Column2")+" "+
                                          sheet.columns[2])
        try:
            new_sheet = pd.DataFrame(columns=list(sheet.columns) + ['result'])
            for index, row in sheet.iterrows():                
                if sheet['label'].value_counts()[row.iloc[0]] > 1:
                    row['result'] = _("pian.views.importovatPianView.check.notUniquelabel")
                    new_sheet = pd.concat([new_sheet, pd.DataFrame([row])], ignore_index=True)
                elif not self.check_epsg(row.iloc[1]):
                    row['result'] = _("pian.views.importovatPianView.check.wrongEpsg")
                    new_sheet = pd.concat([new_sheet, pd.DataFrame([row])], ignore_index=True)
                else:
                    rows= validate_and_split_geometry(row)
                    new_sheet = pd.concat([new_sheet, pd.DataFrame(rows)], ignore_index=True)
        except KeyError as err:
            logger.debug("pian.views.ImportovatPianView.post.sheet_apply.key_error",
                         extra={"columns": sheet.columns, "err": err})
            return HttpResponseBadRequest(_("pian.views.importovatPianView.check.unreadable_or_empty."))
        context = self.get_context_data()
        context["table"] = new_sheet
        cache.set(str(request.user.id) + "_geom", new_sheet, timeout=60*60)
        if ArcheologickyZaznam.objects.get(ident_cely=request.POST.get("arch_ident")).typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            if request.POST.get("action",False) == "change":
                context["url"] = reverse("arch_z:update-pian", args=[request.POST.get("arch_ident"), request.POST.get("dj_ident"),request.POST.get("pian_ident")])
            else:
                context["url"] = reverse("arch_z:create-pian", args=[request.POST.get("arch_ident"), request.POST.get("dj_ident")])
        else:
            if request.POST.get("action",False) == "change":
                context["url"] = reverse("lokalita:update-pian", args=[request.POST.get("arch_ident"), request.POST.get("dj_ident"),request.POST.get("pian_ident")])
            else:
                context["url"] = reverse("lokalita:create-pian", args=[request.POST.get("arch_ident"), request.POST.get("dj_ident")])
        logger.debug(context["url"])
        return self.render_to_response(context)

    def check_epsg(self, epsg):
        # @jiribartos kontrola geometrie
        return file_validate_epsg(epsg)

