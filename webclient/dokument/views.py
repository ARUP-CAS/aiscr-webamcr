import logging

import structlog
from arch_z.models import ArcheologickyZaznam
from core.constants import (
    ARCHIVACE_DOK,
    D_STAV_ARCHIVOVANY,
    D_STAV_ODESLANY,
    D_STAV_ZAPSANY,
    DOKUMENT_CAST_RELATION_TYPE,
    IDENTIFIKATOR_DOCASNY_PREFIX,
    ODESLANI_DOK,
    ZAPSANI_DOK,
)
from core.exceptions import MaximalIdentNumberError, UnexpectedDataRelations
from core.forms import CheckStavNotChangedForm, VratitForm
from core.ident_cely import (
    get_cast_dokumentu_ident,
    get_dokument_rada,
    get_temp_dokument_ident,
)
from core.message_constants import (
    DOKUMENT_JIZ_BYL_PRIPOJEN,
    DOKUMENT_NELZE_ARCHIVOVAT,
    DOKUMENT_NELZE_ODESLAT,
    DOKUMENT_ODPOJ_ZADNE_RELACE,
    DOKUMENT_ODPOJ_ZADNE_RELACE_MEZI_DOK_A_ZAZNAM,
    DOKUMENT_USPESNE_ARCHIVOVAN,
    DOKUMENT_USPESNE_ODESLAN,
    DOKUMENT_USPESNE_ODPOJEN,
    DOKUMENT_USPESNE_PRIPOJEN,
    DOKUMENT_USPESNE_VRACEN,
    MAXIMUM_IDENT_DOSAZEN,
    PRISTUP_ZAKAZAN,
    VYBERTE_PROSIM_POLOHU,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from core.views import check_stav_changed
from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied
from django.forms import inlineformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from dokument.filters import DokumentFilter
from dokument.forms import (
    CoordinatesDokumentForm,
    CreateModelDokumentForm,
    CreateModelExtraDataForm,
    EditDokumentExtraDataForm,
    EditDokumentForm,
    PripojitDokumentForm,
)
from dokument.models import Dokument, DokumentCast, DokumentExtraData, Let
from dokument.tables import DokumentTable
from heslar.hesla import (
    DOKUMENT_RADA_DATA_3D,
    HESLAR_AREAL,
    HESLAR_AREAL_KAT,
    HESLAR_DOKUMENT_TYP,
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_DRUH_KAT,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_OBJEKT_SPECIFIKACE_KAT,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_DRUH_KAT,
    HESLAR_PREDMET_SPECIFIKACE,
    MATERIAL_DOKUMENTU_DIGITALNI_SOUBOR,
    PRISTUPNOST_BADATEL_ID,
)
from heslar.models import Heslar, HeslarHierarchie
from heslar.views import heslar_12
from komponenta.forms import CreateKomponentaForm
from komponenta.models import Komponenta, KomponentaVazby
from nalez.forms import (
    NalezFormSetHelper,
    create_nalez_objekt_form,
    create_nalez_predmet_form,
)
from nalez.models import NalezObjekt, NalezPredmet
from urllib.parse import urlparse
from projekt.models import Projekt

logger = logging.getLogger(__name__)
logger_s = structlog.get_logger(__name__)


@login_required
@require_http_methods(["GET"])
def index_model_3D(request):
    return render(request, "dokument/index_model_3D.html")


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {"warnings": request.session.pop("temp_data", None)}
    dokument = get_object_or_404(
        Dokument.objects.select_related(
            "soubory",
            "organizace",
            "material_originalu",
            "typ_dokumentu",
            "rada",
        ),
        ident_cely=ident_cely,
    )
    if not dokument.has_extra_data():
        extra_data = DokumentExtraData(dokument=dokument)
        extra_data.save()
    else:
        extra_data = dokument.extra_data
    form_dokument = EditDokumentForm(instance=dokument, readonly=True)
    form_dokument_extra = EditDokumentExtraDataForm(
        rada=dokument.rada,
        let=(dokument.let.id if dokument.let else ""),
        dok_osoby=list(dokument.osoby.all().values_list("id", flat=True)),
        instance=extra_data,
        readonly=True,
    )
    context["dokument"] = dokument
    context["form_dokument"] = form_dokument
    context["form_dokument_extra"] = form_dokument_extra
    context["history_dates"] = get_history_dates(dokument.historie)
    context["show"] = get_detail_template_shows(dokument)

    if dokument.soubory:
        context["soubory"] = dokument.soubory.soubory.all()
    else:
        context["soubory"] = None
    response = render(request, "dokument/detail.html", context)
    casti = dokument.casti.all()
    referer = urlparse(request.META.get("HTTP_REFERER", False)).path
    referer_next = urlparse(request.META.get("HTTP_REFERER", False)).query
    if referer:
        ident_referer = referer.split("/")[-1]
        if ident_cely == ident_referer:
            pass
        elif "arch-z/akce/detail/" in referer or "/projekt/detail/" in referer:
            found = False
            for cast in casti:
                if cast.archeologicky_zaznam:
                    if cast.archeologicky_zaznam.ident_cely == ident_referer:
                        logger.debug("back option for akce found")
                        response.set_cookie(
                            "zpet",
                            reverse("arch_z:detail", args=(ident_referer,)),
                            max_age=1000,
                        )
                        found = True
                        break
                if cast.projekt:
                    if cast.projekt.ident_cely == ident_referer:
                        logger.debug("back option for projekt found")
                        response.set_cookie(
                            "zpet",
                            reverse("projekt:detail", args=(ident_referer,)),
                            max_age=1000,
                        )
                        found = True
                        break
            if found == False:
                logger.debug("no back option for projekt/akce found")
                response.delete_cookie("zpet")
        elif "nahrat-soubor" in referer and ident_cely in referer_next:
            logger.debug("referer is nahradit soubor so back option not changed")
        else:
            logger.debug("referer is other so no back option")
            response.delete_cookie("zpet")
    else:
        logger.debug("no referer so no back option")
        response.delete_cookie("zpet")
    return response


@login_required
@require_http_methods(["GET"])
def detail_model_3D(request, ident_cely):
    context = {"warnings": request.session.pop("temp_data", None)}
    old_nalez_post = request.session.pop("_old_nalez_post", None)
    dokument = get_object_or_404(
        Dokument.objects.select_related(
            "soubory",
            "organizace",
            "typ_dokumentu",
        ),
        ident_cely=ident_cely,
    )
    casti = dokument.casti.all()
    if casti.count() != 1:
        logger.error("Model ma mit jednu cast dokumentu: " + str(casti.count()))
        raise UnexpectedDataRelations()
    komponenty = casti[0].komponenty.komponenty.all()
    if komponenty.count() != 1:
        logger.error("Model ma mit jednu komponentu: " + str(komponenty.count()))
        raise UnexpectedDataRelations()
    show = get_detail_template_shows(dokument)
    obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
    areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
    druh_objekt_choices = heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT)
    druh_predmet_choices = heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT)
    specifikace_objekt_choices = heslar_12(
        HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT
    )
    specifikce_predmetu_choices = list(
        Heslar.objects.filter(nazev_heslare=HESLAR_PREDMET_SPECIFIKACE).values_list(
            "id", "heslo"
        )
    )
    NalezObjektFormset = inlineformset_factory(
        Komponenta,
        NalezObjekt,
        form=create_nalez_objekt_form(
            druh_objekt_choices,
            specifikace_objekt_choices,
            not_readonly=show["editovat"],
        ),
        extra=1 if show["editovat"] else 0,
        can_delete=False,
    )
    NalezPredmetFormset = inlineformset_factory(
        Komponenta,
        NalezPredmet,
        form=create_nalez_predmet_form(
            druh_predmet_choices,
            specifikce_predmetu_choices,
            not_readonly=show["editovat"],
        ),
        extra=1 if show["editovat"] else 0,
        can_delete=False,
    )
    context["dokument"] = dokument
    context["komponenta"] = komponenty[0]
    context["formDokument"] = CreateModelDokumentForm(instance=dokument, readonly=True)
    if dokument.extra_data.geom:
        geom = (
            str(dokument.extra_data.geom)
            .split("(")[1]
            .replace(", ", ",")
            .replace(")", "")
        )
        context["coordinate_x"] = geom.split(" ")[1]
        context["coordinate_y"] = geom.split(" ")[0]

    context["formExtraData"] = CreateModelExtraDataForm(
        instance=dokument.extra_data, readonly=True
    )
    context["formKomponenta"] = CreateKomponentaForm(
        obdobi_choices, areal_choices, instance=komponenty[0], readonly=True
    )
    context["formset"] = {
        "objekt": NalezObjektFormset(
            old_nalez_post,
            instance=komponenty[0],
            prefix=komponenty[0].ident_cely + "_o",
        ),
        "predmet": NalezPredmetFormset(
            old_nalez_post,
            instance=komponenty[0],
            prefix=komponenty[0].ident_cely + "_p",
        ),
        "helper_predmet": NalezFormSetHelper(typ="predmet"),
        "helper_objekt": NalezFormSetHelper(typ="objekt"),
    }
    context["history_dates"] = get_history_dates(dokument.historie)
    context["show"] = show
    context["global_map_can_edit"] = False
    logger.debug(context)
    if dokument.soubory:
        context["soubory"] = dokument.soubory.soubory.all()
    else:
        context["soubory"] = None
    return render(request, "dokument/detail_model_3D.html", context)


class DokumentListView(ExportMixin, LoginRequiredMixin, SingleTableMixin, FilterView):
    table_class = DokumentTable
    model = Dokument
    template_name = "dokument/dokument_list.html"
    filterset_class = DokumentFilter
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["export_formats"] = ["csv", "json", "xlsx"]
        return context

    def get_queryset(self):
        # Only allow to view 3D models
        qs = super().get_queryset().filter(ident_cely__contains="3D")
        qs = qs.select_related(
            "typ_dokumentu", "extra_data", "organizace", "extra_data__format"
        )
        return qs


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    dokument = get_object_or_404(Dokument, ident_cely=ident_cely)
    if dokument.stav == D_STAV_ARCHIVOVANY:
        raise PermissionDenied()
    if not dokument.has_extra_data():
        extra_data = DokumentExtraData(dokument=dokument)
        extra_data.save()
    else:
        extra_data = dokument.extra_data
    required_fields = get_required_fields_dokument(dokument)
    required_fields_next = get_required_fields_dokument(dokument, next=1)
    if request.method == "POST":
        form_d = EditDokumentForm(
            request.POST,
            instance=dokument,
            required=get_required_fields_dokument(dokument),
            required_next=get_required_fields_dokument(dokument, 1),
        )
        form_extra = EditDokumentExtraDataForm(
            request.POST,
            instance=extra_data,
            required=required_fields,
            required_next=required_fields_next,
        )
        if form_d.is_valid() and form_extra.is_valid():
            logger.debug("webclient.dokument.views: Both forms are valid")
            instance_d = form_d.save(commit=False)
            instance_d.osoby.set(form_extra.cleaned_data["dokument_osoba"])
            if form_extra.cleaned_data["let"]:
                instance_d.let = Let.objects.get(id=form_extra.cleaned_data["let"])
            instance_d.save()
            form_d.save_m2m()
            form_extra.save()
            if form_d.has_changed() or form_extra.has_changed():
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return redirect("dokument:detail", ident_cely=dokument.ident_cely)
        else:
            logger.debug("webclient.dokument.views: The form is not valid")
            logger.debug(f"webclient.dokument.views form_d.errors: {form_d.errors}")
            logger.debug(
                f"webclient.dokument.views form_extra.errors: {form_extra.errors}"
            )
    else:
        form_d = EditDokumentForm(
            instance=dokument,
            required=required_fields,
            required_next=required_fields_next,
        )
        form_extra = EditDokumentExtraDataForm(
            rada=dokument.rada,
            let=(dokument.let.id if dokument.let else ""),
            dok_osoby=list(dokument.osoby.all().values_list("id", flat=True)),
            instance=extra_data,
            required=required_fields,
            required_next=required_fields_next,
        )

    return render(
        request,
        "dokument/edit.html",
        {
            "formDokument": form_d,
            "formExtraData": form_extra,
            "dokument": dokument,
            "hierarchie": get_hierarchie_dokument_typ(),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def edit_model_3D(request, ident_cely):
    dokument = get_object_or_404(Dokument, ident_cely=ident_cely)
    if dokument.stav == D_STAV_ARCHIVOVANY:
        raise PermissionDenied()
    obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
    areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
    required_fields = get_required_fields_model3D(dokument)
    required_fields_next = get_required_fields_model3D(dokument, next=1)
    if request.method == "POST":
        form_d = CreateModelDokumentForm(
            request.POST,
            instance=dokument,
            required=required_fields,
            required_next=required_fields_next,
        )
        form_extra = CreateModelExtraDataForm(
            request.POST,
            instance=dokument.extra_data,
            required=required_fields,
            required_next=required_fields_next,
        )
        form_coor = CoordinatesDokumentForm(
            request.POST
        )  # Zmen musis ulozit data z formulare
        form_komponenta = CreateKomponentaForm(
            obdobi_choices,
            areal_choices,
            request.POST,
            instance=dokument.get_komponenta(),
            required=required_fields,
            required_next=required_fields_next,
        )
        geom = None
        try:
            dx = float(form_coor.data.get("coordinate_x"))
            dy = float(form_coor.data.get("coordinate_y"))
            if dx > 0 and dy > 0:
                geom = Point(dy, dx)
        except Exception:
            logger.error("Dokument.Chybny format souradnic:1")
        if form_d.is_valid() and form_extra.is_valid() and form_komponenta.is_valid():
            form_d.save()
            if geom is not None:
                dokument.extra_data.geom = geom
            form_extra.save()
            form_komponenta.save()
            if (
                form_d.changed_data
                or form_extra.changed_data
                or form_komponenta.changed_data
            ):
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return redirect("dokument:detail-model-3D", ident_cely=dokument.ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form_d.errors)
            logger.debug(form_extra.errors)
            logger.debug(form_komponenta.errors)
    else:
        form_d = CreateModelDokumentForm(
            instance=dokument,
            required=get_required_fields_model3D(dokument),
            required_next=get_required_fields_model3D(dokument, 1),
        )
        form_extra = CreateModelExtraDataForm(
            instance=dokument.extra_data,
            required=get_required_fields_model3D(dokument),
            required_next=get_required_fields_model3D(dokument, 1),
        )
        form_komponenta = CreateKomponentaForm(
            obdobi_choices,
            areal_choices,
            instance=dokument.get_komponenta(),
            required=get_required_fields_model3D(dokument),
            required_next=get_required_fields_model3D(dokument, 1),
        )
        if dokument.extra_data.geom:
            geom = (
                str(dokument.extra_data.geom)
                .split("(")[1]
                .replace(", ", ",")
                .replace(")", "")
            )
            return render(
                request,
                "dokument/create_model_3D.html",
                {
                    "coordinate_x": geom.split(" ")[1],
                    "coordinate_y": geom.split(" ")[0],
                    "global_map_can_edit": True,
                    "formDokument": form_d,
                    "formExtraData": form_extra,
                    "formKomponenta": form_komponenta,
                    "title": _("Editace modelu 3D"),
                    "header": _("Editace modelu 3D"),
                    "button": _("Upravit model"),
                },
            )

    return render(
        request,
        "dokument/create_model_3D.html",
        {
            "global_map_can_edit": True,
            "formDokument": form_d,
            "formExtraData": form_extra,
            "formKomponenta": form_komponenta,
            "title": _("Editace modelu 3D"),
            "header": _("Editace modelu 3D"),
            "button": _("Upravit model"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def zapsat_do_akce(request, arch_z_ident_cely):
    zaznam = get_object_or_404(ArcheologickyZaznam, ident_cely=arch_z_ident_cely)
    return zapsat(request, zaznam)


def zapsat_do_projektu(request, proj_ident_cely):
    zaznam = get_object_or_404(Projekt, ident_cely=proj_ident_cely)
    return zapsat(request, zaznam)


@login_required
@require_http_methods(["GET", "POST"])
def create_model_3D(request):
    obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
    areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
    required_fields = get_required_fields_model3D()
    required_fields_next = get_required_fields_model3D(next=1)
    if request.method == "POST":
        form_d = CreateModelDokumentForm(
            request.POST,
            required=required_fields,
            required_next=required_fields_next,
        )
        form_extra = CreateModelExtraDataForm(
            request.POST,
            required=required_fields,
            required_next=required_fields_next,
        )
        form_komponenta = CreateKomponentaForm(
            obdobi_choices,
            areal_choices,
            request.POST,
            required=required_fields,
            required_next=required_fields_next,
        )
        geom = None
        try:
            dx = float(form_extra.data.get("coordinate_x"))
            dy = float(form_extra.data.get("coordinate_y"))
            if dx > 0 and dy > 0:
                geom = Point(dy, dx)
        except Exception:
            logger.error("Dokument.Chybny format souradnic:2")

        if form_d.is_valid() and form_extra.is_valid() and form_komponenta.is_valid():
            logger.debug("Forms are valid")
            dokument = form_d.save(commit=False)
            dokument.rada = Heslar.objects.get(id=DOKUMENT_RADA_DATA_3D)
            dokument.material_originalu = Heslar.objects.get(
                id=MATERIAL_DOKUMENTU_DIGITALNI_SOUBOR
            )
            try:
                dokument.ident_cely = get_temp_dokument_ident(rada="3D", region="C")
            except MaximalIdentNumberError:
                messages.add_message(request, messages.ERROR, MAXIMUM_IDENT_DOSAZEN)
            else:
                dokument.pristupnost = Heslar.objects.get(id=PRISTUPNOST_BADATEL_ID)
                dokument.stav = D_STAV_ZAPSANY
                dokument.save()
                dokument.set_zapsany(request.user)
                # Vytvorit defaultni cast dokumentu
                kv = KomponentaVazby(typ_vazby=DOKUMENT_CAST_RELATION_TYPE)
                kv.save()
                dc = DokumentCast(
                    dokument=dokument,
                    ident_cely=get_cast_dokumentu_ident(dokument),
                    komponenty=kv,
                )
                dc.save()
                form_d.save_m2m()
                extra_data = form_extra.save(commit=False)
                extra_data.dokument = dokument
                if geom is not None:
                    extra_data.geom = geom
                extra_data.save()

                komponenta = form_komponenta.save(commit=False)
                komponenta.komponenta_vazby = dc.komponenty
                komponenta.ident_cely = dokument.ident_cely + "-K001"
                komponenta.save()

                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
                return redirect(
                    "dokument:detail-model-3D", ident_cely=dokument.ident_cely
                )

        else:
            logger.warning("Form is not valid")
            logger.debug(form_d.errors)
            logger.debug(form_extra.errors)
            logger.debug(form_komponenta.errors)
            if "geom" in form_extra.errors:
                messages.add_message(request, messages.ERROR, VYBERTE_PROSIM_POLOHU)
    else:
        form_d = CreateModelDokumentForm(
            required=required_fields,
            required_next=required_fields_next,
        )
        form_extra = CreateModelExtraDataForm(
            required=required_fields,
            required_next=required_fields_next,
        )
        form_komponenta = CreateKomponentaForm(
            obdobi_choices,
            areal_choices,
            required=required_fields,
            required_next=required_fields_next,
        )
    return render(
        request,
        "dokument/create_model_3D.html",
        {
            "global_map_can_edit": True,
            "formDokument": form_d,
            "formExtraData": form_extra,
            "formKomponenta": form_komponenta,
            "title": _("Nový model 3D"),
            "header": _("Nový model 3D"),
            "button": _("Vytvořit model"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def odeslat(request, ident_cely):
    d = get_object_or_404(Dokument, ident_cely=ident_cely)
    logger_s.debug("dokument.views.odeslat.start", ident_cely=ident_cely)
    if d.stav != D_STAV_ZAPSANY:
        logger_s.debug(
            "dokument.views.odeslat.permission_denied", ident_cely=ident_cely
        )
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, d):
        logger_s.debug(
            "dokument.views.odeslat.check_stav_changed", ident_cely=ident_cely
        )
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    if request.method == "POST":
        d.set_odeslany(request.user)
        messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_ODESLAN)
        logger_s.debug("dokument.views.odeslat.sucess")
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)})
    else:
        warnings = d.check_pred_odeslanim()
        if warnings:
            logger_s.debug(
                "dokument.views.odeslat.warnings",
                warnings=warnings,
                ident_cely=ident_cely,
            )
            request.session["temp_data"] = warnings
            messages.add_message(request, messages.ERROR, DOKUMENT_NELZE_ODESLAT)
            return JsonResponse(
                {"redirect": get_detail_json_view(ident_cely)}, status=403
            )
    form_check = CheckStavNotChangedForm(initial={"old_stav": d.stav})
    context = {
        "object": d,
        "title": _("dokument.modalForm.odeslat.title.text"),
        "id_tag": "odeslat-dokument-form",
        "button": _("dokument.modalForm.odeslat.submit.button"),
        "form_check": form_check,
    }
    logger_s.debug("dokument.views.odeslat.finish", ident_cely=ident_cely)
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def archivovat(request, ident_cely):
    d = get_object_or_404(Dokument, ident_cely=ident_cely)
    logger_s.debug("dokument.views.archivovat.start", ident_cely=ident_cely)
    if d.stav != D_STAV_ODESLANY:
        logger_s.debug(
            "dokument.views.archivovat.permission_denied", ident_cely=ident_cely
        )
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, d):
        logger_s.debug(
            "dokument.views.archivovat.check_stav_changed", ident_cely=ident_cely
        )
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    if request.method == "POST":
        # Nastav identifikator na permanentny
        if ident_cely.startswith(IDENTIFIKATOR_DOCASNY_PREFIX):
            rada = get_dokument_rada(d.typ_dokumentu, d.material_originalu)
            try:
                d.set_permanent_ident_cely(d.ident_cely[2:4] + rada.zkratka)
            except MaximalIdentNumberError:
                messages.add_message(request, messages.SUCCESS, MAXIMUM_IDENT_DOSAZEN)
                return JsonResponse(
                    {"redirect": get_detail_json_view(ident_cely)}, status=403
                )
            else:
                d.save()
                logger.debug(
                    "Dokumentu "
                    + ident_cely
                    + " a jeho castem byl prirazen permanentni identifikator "
                    + d.ident_cely
                )
        d.set_archivovany(request.user)
        messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_ARCHIVOVAN)
        return JsonResponse({"redirect": get_detail_json_view(d.ident_cely)})
    else:
        warnings = d.check_pred_archivaci()
        logger.debug(warnings)
        if warnings:
            request.session["temp_data"] = warnings
            messages.add_message(request, messages.ERROR, DOKUMENT_NELZE_ARCHIVOVAT)
            return JsonResponse(
                {"redirect": get_detail_json_view(ident_cely)}, status=403
            )
    form_check = CheckStavNotChangedForm(initial={"old_stav": d.stav})
    context = {
        "object": d,
        "title": _("dokument.modalForm.archivovat.title.text"),
        "id_tag": "archivovat-dokument-form",
        "button": _("dokument.modalForm.archivovat.submit.button"),
        "form_check": form_check,
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    d = get_object_or_404(Dokument, ident_cely=ident_cely)
    if d.stav != D_STAV_ODESLANY and d.stav != D_STAV_ARCHIVOVANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    if check_stav_changed(request, d):
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    if request.method == "POST":
        form = VratitForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            d.set_vraceny(request.user, d.stav - 1, duvod)
            messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_VRACEN)
            return JsonResponse({"redirect": get_detail_json_view(ident_cely)})
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
            return JsonResponse(
                {"redirect": get_detail_json_view(ident_cely)}, status=403
            )
    else:
        form = VratitForm(initial={"old_stav": d.stav})
    context = {
        "object": d,
        "form": form,
        "title": _("dokument.modalForm.vraceni.title.text"),
        "id_tag": "vratit-dokument-form",
        "button": _("dokument.modalForm.vraceni.submit.button"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    d = get_object_or_404(Dokument, ident_cely=ident_cely)
    if check_stav_changed(request, d):
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    if request.method == "POST":

        historie = d.historie
        soubory = d.soubory
        resp1 = d.delete()
        resp2 = historie.delete()
        resp3 = soubory.delete()

        # Kdyz mazu dokument ktery reprezentuje 3D model, mazu i komponenty
        if "3D" in d.ident_cely:
            for k in Komponenta.objects.filter(ident_cely__startswith=d.ident_cely):
                logger.debug("Mazu komponentu modelu 3D: " + str(k.ident_cely))
                k.delete()

        if resp1:
            logger.debug("Dokument byl smazan: " + str(resp1 + resp2 + resp3))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            return JsonResponse({"redirect": reverse("core:home")})
        else:
            logger.warning("Dokument nebyl smazan: " + str(ident_cely))
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            return JsonResponse(
                {"redirect": get_detail_json_view(ident_cely)}, status=403
            )
    else:
        form_check = CheckStavNotChangedForm(initial={"old_stav": d.stav})
        context = {
            "object": d,
            "title": _("dokument.modalForm.smazani.title.text"),
            "id_tag": "smazat-dokument-form",
            "button": _("dokument.modalForm.smazani.submit.button"),
            "form_check": form_check,
        }
        return render(request, "core/transakce_modal.html", context)


class DokumentAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Dokument.objects.none()
        qs = Dokument.objects.all()
        if self.q:
            qs = qs.filter(ident_cely__icontains=self.q)
        return qs


class DokumentAutocompleteBezZapsanych(DokumentAutocomplete):
    def get_queryset(self):
        qs = super(DokumentAutocompleteBezZapsanych, self).get_queryset()
        qs = qs.filter(stav__in=(D_STAV_ARCHIVOVANY, D_STAV_ODESLANY))
        return qs


def get_hierarchie_dokument_typ():
    hierarchie_qs = HeslarHierarchie.objects.filter(
        heslo_podrazene__nazev_heslare__id=HESLAR_DOKUMENT_TYP
    ).values_list("heslo_podrazene", "heslo_nadrazene")
    hierarchie = {}
    for v in hierarchie_qs:
        if v[0] in hierarchie:
            hierarchie[v[0]].append(v[1])
        else:
            hierarchie[v[0]] = [v[1]]
    return hierarchie


def get_history_dates(historie_vazby):
    historie = {
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_DOK),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_DOK),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_DOK),
    }
    return historie


def get_detail_template_shows(dokument):
    show_vratit = dokument.stav > D_STAV_ZAPSANY
    show_odeslat = dokument.stav == D_STAV_ZAPSANY
    show_archivovat = dokument.stav == D_STAV_ODESLANY
    show_edit = dokument.stav not in [
        D_STAV_ARCHIVOVANY,
    ]
    show_arch_links = dokument.stav == D_STAV_ARCHIVOVANY
    show = {
        "vratit_link": show_vratit,
        "odeslat_link": show_odeslat,
        "archivovat_link": show_archivovat,
        "editovat": show_edit,
        "arch_links": show_arch_links,
    }
    return show


def zapsat(request, zaznam):
    required_fields = get_required_fields_dokument()
    required_fields_next = get_required_fields_dokument(next=1)
    if request.method == "POST":
        form_d = EditDokumentForm(
            request.POST,
            required=required_fields,
            required_next=required_fields_next,
        )
        if form_d.is_valid():
            logger.debug("Dokument.Form is valid")
            dokument = form_d.save(commit=False)
            dokument.rada = get_dokument_rada(
                dokument.typ_dokumentu, dokument.material_originalu
            )
            try:
                dokument.ident_cely = get_temp_dokument_ident(
                    rada=dokument.rada.zkratka, region=zaznam.ident_cely[0]
                )
            except MaximalIdentNumberError:
                messages.add_message(request, messages.ERROR, MAXIMUM_IDENT_DOSAZEN)
            else:
                dokument.stav = D_STAV_ZAPSANY
                dokument.save()
                dokument.set_zapsany(request.user)

                # Vytvorit defaultni cast dokumentu
                if zaznam._meta.verbose_name == "archeologicky zaznam":
                    DokumentCast(
                        dokument=dokument,
                        ident_cely=get_cast_dokumentu_ident(dokument),
                        archeologicky_zaznam=zaznam,
                    ).save()
                else:
                    DokumentCast(
                        dokument=dokument,
                        ident_cely=get_cast_dokumentu_ident(dokument),
                        projekt=zaznam,
                    ).save()

                form_d.save_m2m()

                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
                return redirect("dokument:detail", ident_cely=dokument.ident_cely)

        else:
            logger.warning("Form is not valid")
            logger.debug(form_d.errors)

    else:
        form_d = EditDokumentForm(
            create=True,
            required=required_fields,
            required_next=required_fields_next,
        )

    return render(
        request,
        "dokument/create.html",
        {
            "formDokument": form_d,
            "hierarchie": get_hierarchie_dokument_typ(),
        },
    )


def odpojit(request, ident_doku, ident_zaznamu, view):
    relace_dokumentu = DokumentCast.objects.filter(dokument__ident_cely=ident_doku)
    remove_orphan = False
    if len(relace_dokumentu) == 0:
        logger.debug("Nelze najít zadne relace dokumentu " + str(ident_doku))
        messages.add_message(request, messages.ERROR, DOKUMENT_ODPOJ_ZADNE_RELACE)
        return JsonResponse({"redirect": reverse(f"{view}:detail")}, status=404)
    if len(relace_dokumentu) == 1:
        orphan_dokument = relace_dokumentu[0].dokument
        if orphan_dokument.ident_cely.startswith("X-"):
            remove_orphan = True
    if request.method == "POST":
        if view == "arch_z":
            dokument_cast = relace_dokumentu.filter(
                archeologicky_zaznam__ident_cely=ident_zaznamu
            )
        else:
            dokument_cast = relace_dokumentu.filter(projekt__ident_cely=ident_zaznamu)
        if len(dokument_cast) == 0:
            logger.debug("Nelze najít relaci mezi zaznamem a dokumentem")
            messages.add_message(
                request, messages.ERROR, DOKUMENT_ODPOJ_ZADNE_RELACE_MEZI_DOK_A_ZAZNAM
            )
            return JsonResponse({"redirect": reverse(f"{view}:detail")}, status=404)
        resp = dokument_cast[0].delete()
        logger.debug("Byla smazana cast dokumentu " + str(resp))
        if remove_orphan:
            orphan_dokument.delete()
            logger.debug("Docasny soubor bez relaci odstranen.")
        messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_ODPOJEN)
        return JsonResponse(
            {
                "redirect": reverse(
                    f"{view}:detail", kwargs={"ident_cely": ident_zaznamu}
                )
            }
        )
    else:
        warnings = []
        if remove_orphan:
            warnings.append(
                "Nearchivovaný dokument "
                + str(orphan_dokument)
                + " nemá žádnou jinou relaci a odpojením bude automaticky smazán."
            )
        return render(
            request,
            "core/transakce_modal.html",
            {
                "object": relace_dokumentu[0],
                "warnings": warnings,
                "title": _("dokument.modalForm.odpojit.title.text"),
                "id_tag": "odpojit-dokument-form",
                "button": _("dokument.modalForm.odpojit.submit.button"),
            },
        )


def pripojit(request, ident_zaznam, proj_ident_cely, typ):
    zaznam = get_object_or_404(typ, ident_cely=ident_zaznam)
    logger.debug(zaznam.__class__.__name__)
    if isinstance(zaznam, ArcheologickyZaznam):
        casti_zaznamu = DokumentCast.objects.filter(
            archeologicky_zaznam__ident_cely=ident_zaznam
        )
        debug_name = "akci "
        redirect_name = "arch_z"
        context = {
            "object": zaznam,
            "title": _("dokument.modalForm.pripojitDoAkce.title.text"),
            "id_tag": "pripojit-dokument-form",
            "button": _("dokument.modalForm.pripojitDoAkce.submit.button"),
        }
    else:
        casti_zaznamu = DokumentCast.objects.filter(projekt__ident_cely=ident_zaznam)
        debug_name = "projektu "
        redirect_name = "projekt"
        context = {
            "object": zaznam,
            "title": _("dokument.modalForm.pripojitDoProjektu.title.text"),
            "id_tag": "pripojit-dokument-form",
            "button": _("dokument.modalForm.pripojitDoProjektu.submit.button"),
        }
    if request.method == "POST":
        dokument_ids = request.POST.getlist("dokument")

        for dokument_id in dokument_ids:
            dokument = get_object_or_404(Dokument, id=dokument_id)
            relace = casti_zaznamu.filter(dokument__id=dokument_id)
            if not relace.exists():
                dc_ident = get_cast_dokumentu_ident(dokument)
                if isinstance(zaznam, ArcheologickyZaznam):
                    DokumentCast(
                        archeologicky_zaznam=zaznam,
                        dokument=dokument,
                        ident_cely=dc_ident,
                    ).save()
                else:
                    DokumentCast(
                        projekt=zaznam, dokument=dokument, ident_cely=dc_ident
                    ).save()
                logger.debug(
                    "K "
                    + str(debug_name)
                    + str(ident_zaznam)
                    + " byl pripojen dokument "
                    + str(dokument.ident_cely)
                )
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    DOKUMENT_USPESNE_PRIPOJEN,
                )
            else:
                messages.add_message(
                    request, messages.WARNING, DOKUMENT_JIZ_BYL_PRIPOJEN
                )
        return JsonResponse(
            {
                "redirect": reverse(
                    f"{redirect_name}:detail", kwargs={"ident_cely": ident_zaznam}
                )
            }
        )
    else:
        if proj_ident_cely:
            # Pridavam projektove dokumenty
            projektove_dokumenty = set()
            proj_dok_list = set()
            dokumenty_akce = set(
                Dokument.objects.filter(
                    casti__archeologicky_zaznam__ident_cely=ident_zaznam
                )
            )
            projekt = get_object_or_404(Projekt, ident_cely=proj_ident_cely)
            for akce in projekt.akce_set.all().exclude(
                archeologicky_zaznam__ident_cely=ident_zaznam
            ):
                for cast in akce.archeologicky_zaznam.casti_dokumentu.all():
                    if cast.dokument not in dokumenty_akce:
                        projektove_dokumenty.add(
                            (cast.dokument.id, cast.dokument.ident_cely)
                        )
                        proj_dok_list.add(cast.dokument)
            context["dokumenty"] = proj_dok_list
            context["pripojit"] = proj_dok_list
            return render(request, "core/transakce_table_modal.html", context)
        else:
            # Pridavam vsechny dokumenty
            form = PripojitDokumentForm()
        context["form"] = form
        context["hide_table"] = True
    return render(request, "core/transakce_table_modal.html", context)


@login_required
@require_http_methods(["GET"])
def get_dokument_table_row(request):
    context = {"d": Dokument.objects.get(id=request.GET.get("dok_id", ""))}
    return HttpResponse(render_to_string("dokument/dokument_table_row.html", context))


def get_detail_view(ident_cely):
    if "3D" in ident_cely:
        return redirect("dokument:detail-model-3D", ident_cely=ident_cely)
    else:
        return redirect("dokument:detail", ident_cely=ident_cely)


def get_detail_json_view(ident_cely):
    if "3D" in ident_cely:
        return reverse("dokument:detail-model-3D", kwargs={"ident_cely": ident_cely})
    else:
        return reverse("dokument:detail", kwargs={"ident_cely": ident_cely})


def get_required_fields_model3D(zaznam=None, next=0):
    required_fields = []
    if zaznam:
        stav = zaznam.stav
    else:
        stav = 1
    if stav >= D_STAV_ZAPSANY - next:
        required_fields = [
            "autori",
            "rok_vzniku",
            "organizace",
            "typ_dokumentu",
        ]
    if stav > D_STAV_ZAPSANY - next:
        required_fields += [
            "format",
            "popis",
            "duveryhodnost",
            "obdobi",
            "areal",
        ]
    return required_fields


def get_required_fields_dokument(zaznam=None, next=0):
    required_fields = []
    if zaznam:
        stav = zaznam.stav
    else:
        stav = 1
    if stav >= D_STAV_ZAPSANY - next:
        required_fields = [
            "rok_vzniku",
            "autori",
            "organizace",
            "typ_dokumentu",
            "material_originalu",
            "licence",
        ]
    if stav > D_STAV_ZAPSANY - next:
        required_fields += [
            "ulozeni_originalu",
            "popis",
            "pristupnost",
            "jazyky",
        ]
    return required_fields
