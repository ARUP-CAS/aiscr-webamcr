import logging
import os
from django.views import View


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
    DOKUMENT_AZ_USPESNE_PRIPOJEN,
    DOKUMENT_CAST_USPESNE_ODPOJEN,
    DOKUMENT_CAST_USPESNE_SMAZANA,
    DOKUMENT_JIZ_BYL_PRIPOJEN,
    DOKUMENT_NEIDENT_AKCE_USPESNE_SMAZANA,
    DOKUMENT_NELZE_ARCHIVOVAT,
    DOKUMENT_NELZE_ARCHIVOVAT_CHYBY_SOUBOR,
    DOKUMENT_NELZE_ODESLAT,
    DOKUMENT_ODPOJ_ZADNE_RELACE,
    DOKUMENT_ODPOJ_ZADNE_RELACE_MEZI_DOK_A_ZAZNAM,
    DOKUMENT_PROJEKT_USPESNE_PRIPOJEN,
    DOKUMENT_USPESNE_ARCHIVOVAN,
    DOKUMENT_USPESNE_ODESLAN,
    DOKUMENT_USPESNE_ODPOJEN,
    DOKUMENT_USPESNE_PRIPOJEN,
    DOKUMENT_USPESNE_VRACEN,
    MAXIMUM_IDENT_DOSAZEN,
    PRISTUP_ZAKAZAN,
    VYBERTE_PROSIM_POLOHU,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from core.views import SearchListView, check_stav_changed
from dal import autocomplete
from django.db.models.functions import Length
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
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from dokument.filters import Model3DFilter, DokumentFilter
from dokument.forms import (
    CoordinatesDokumentForm,
    CreateModelDokumentForm,
    CreateModelExtraDataForm,
    DokumentCastCreateForm,
    DokumentCastForm,
    EditDokumentExtraDataForm,
    EditDokumentForm,
    PripojitDokumentForm,
    TvarFormSetHelper,
    create_tvar_form,
)
from dokument.models import (
    Dokument,
    DokumentAutor,
    DokumentCast,
    DokumentExtraData,
    Let,
    Tvar,
)
from dokument.tables import Model3DTable, DokumentTable
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
from services.mailer import Mailer
from neidentakce.forms import NeidentAkceForm
from neidentakce.models import NeidentAkce
from ez.forms import PripojitArchZaznamForm
from projekt.forms import PripojitProjektForm
from core.models import Soubor
from django.db.models import Prefetch, Subquery, OuterRef

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def index_model_3D(request):
    return render(request, "dokument/index_model_3D.html")


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
        logger.warning("dokument.views.detail_model_3D.casti_count_error", extra={"casti_count": casti.count()})
        raise UnexpectedDataRelations()
    komponenty = casti[0].komponenty.komponenty.all()
    if komponenty.count() != 1:
        logger.warning("dokument.views.detail_model_3D.komponenty_count_error",
                       extra={"casti_count": komponenty.count()})
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
    if dokument.soubory:
        context["soubory"] = dokument.soubory.soubory.all()
    else:
        context["soubory"] = None
    return render(request, "dokument/detail_model_3D.html", context)


class Model3DListView(SearchListView):
    table_class = Model3DTable
    model = Dokument
    filterset_class = Model3DFilter
    export_name = "export_modely_"
    page_title = _("knihovna3d.vyber.pageTitle")
    app = "knihovna_3d"
    toolbar = "toolbar_dokument.html"
    search_sum = _("knihovna3d.vyber.pocetVyhledanych")
    pick_text = _("knihovna3d.vyber.pickText")
    hasOnlyVybrat_header = _("knihovna3d.vyber.header.hasOnlyVybrat")
    hasOnlyVlastnik_header = _("knihovna3d.vyber.header.hasOnlyVlastnik")
    hasOnlyArchive_header = _("knihovna3d.vyber.header.default")
    hasOnlyPotvrdit_header = _("knihovna3d.vyber.header.default")
    default_header = _("knihovna3d.vyber.header.default")
    toolbar_name = _("knihovna3d.template.toolbar.title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_3d"] = True
        return context

    def get_queryset(self):
        # Only allow to view 3D models
        qs = super().get_queryset().filter(ident_cely__contains="3D")
        qs = qs.select_related(
            "typ_dokumentu", "extra_data", "organizace", "extra_data__format"
        )
        return qs


class DokumentIndexView(LoginRequiredMixin, TemplateView):
    template_name = "dokument/index_dokument.html"


class DokumentListView(SearchListView):
    table_class = DokumentTable
    model = Dokument
    filterset_class = DokumentFilter
    export_name = "export_dokumenty_"
    page_title = _("dokument.vyber.pageTitle")
    app = "dokument"
    toolbar = "toolbar_dokument.html"
    search_sum = _("dokument.vyber.pocetVyhledanych")
    pick_text = _("dokument.vyber.pickText")
    hasOnlyVybrat_header = _("dokument.vyber.header.hasOnlyVybrat")
    hasOnlyVlastnik_header = _("dokument.vyber.header.hasOnlyVlastnik")
    hasOnlyArchive_header = _("dokument.vyber.header.hasOnlyArchive")
    hasOnlyPotvrdit_header = _("dokument.vyber.header.default")
    default_header = _("dokument.vyber.header.default")
    toolbar_name = _("dokument.template.toolbar.title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_3d"] = False
        return context

    def get_queryset(self):
        # Only allow to view 3D models
        subqry = Subquery(
            Soubor.objects.filter(
                mimetype__startswith="image", vazba=OuterRef("vazba")
            ).values_list("id", flat=True)[:1]
        )
        qs = super().get_queryset().exclude(ident_cely__contains="3D")
        qs = qs.select_related(
            "typ_dokumentu",
            "extra_data",
            "organizace",
            "extra_data__format",
            "soubory",
            "let",
            "rada",
            "pristupnost",
            "material_originalu",
            "ulozeni_originalu",
        ).prefetch_related(
            Prefetch(
                "soubory__soubory",
                queryset=Soubor.objects.filter(id__in=subqry),
                to_attr="first_soubor",
            )
        )
        return qs


class RelatedContext(LoginRequiredMixin, TemplateView):
    def get_cast(self, context, cast, **kwargs):
        context["cast"] = cast
        cast_form = DokumentCastForm(
            instance=cast,
            readonly=True,
        )
        context["cast_form"] = cast_form
        neident_akce = NeidentAkce.objects.filter(dokument_cast=cast)
        if neident_akce.exists():
            context["neident_akce_form"] = NeidentAkceForm(
                instance=neident_akce[0], readonly=True
            )
        context["show_odpojit"] = False
        context["show_pripojit"] = True
        if cast.projekt or cast.archeologicky_zaznam:
            context["show_odpojit"] = True
            context["show_pripojit"] = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["warnings"] = self.request.session.pop("temp_data", None)
        dokument = get_object_or_404(
            Dokument.objects.select_related(
                "soubory",
                "organizace",
                "material_originalu",
                "typ_dokumentu",
                "rada",
            ),
            ident_cely=self.kwargs["ident_cely"],
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
        show = get_detail_template_shows(dokument)
        if dokument.rada.zkratka in ["LD", "LN", "DL"]:
            TvarFormset = inlineformset_factory(
                Dokument,
                Tvar,
                form=create_tvar_form(
                    not_readonly=show["editovat"],
                ),
                extra=1 if show["editovat"] else 0,
                can_delete=False,
            )
            context["form_tvary"] = TvarFormset(
                instance=dokument,
                prefix=dokument.ident_cely + "_d",
            )
            context["tvary_helper"] = TvarFormSetHelper()
        context["dokument"] = dokument
        context["form_dokument"] = form_dokument
        context["form_dokument_extra"] = form_dokument_extra
        context["history_dates"] = get_history_dates(dokument.historie)
        context["show"] = show

        if dokument.soubory:
            context["soubory"] = dokument.soubory.soubory.all()
        else:
            context["soubory"] = None

        context["casti"] = dokument.casti.all()
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        referer = urlparse(self.request.META.get("HTTP_REFERER", False)).path
        referer_next = urlparse(self.request.META.get("HTTP_REFERER", False)).query
        if referer:
            ident_referer = referer.split("/")[-1]
            if context["dokument"].ident_cely == ident_referer:
                pass
            elif (
                "arch-z/akce/detail/" in referer
                or "/projekt/detail/"
                or "arch-z/lokalita/detail/" in referer
            ):
                found = False
                for cast in context["casti"]:
                    if cast.archeologicky_zaznam:
                        if cast.archeologicky_zaznam.ident_cely == ident_referer:
                            logger.debug("dokument.views.RelatedContext.render_to_response.back_option_for_akce_found")
                            response.set_cookie(
                                "zpet",
                                cast.archeologicky_zaznam.get_absolute_url(),
                                max_age=1000,
                            )
                            found = True
                            break
                    if cast.projekt:
                        if cast.projekt.ident_cely == ident_referer:
                            logger.debug("dokument.views.RelatedContext.render_to_response."
                                         "back_option_for_projekt_found")
                            response.set_cookie(
                                "zpet",
                                reverse("projekt:detail", args=(ident_referer,)),
                                max_age=1000,
                            )
                            found = True
                            break
                if found is False:
                    logger.debug("dokument.views.RelatedContext.render_to_response.back_option_not_found")
                    response.delete_cookie("zpet")
            elif (
                "nahrat-soubor" in referer
                and context["dokument"].ident_cely in referer_next
            ):
                logger.debug("dokument.views.RelatedContext.render_to_response.back_option_not_changed")
            else:
                logger.debug("dokument.views.RelatedContext.render_to_response.no_back_option")
                response.delete_cookie("zpet")
        else:
            logger.debug("dokument.views.RelatedContext.render_to_response.no_referer")
            response.delete_cookie("zpet")
        return response


class DokumentDetailView(RelatedContext):
    template_name = "dokument/dok/detail.html"


class DokumentCastDetailView(RelatedContext):
    template_name = "dokument/dok/detail_cast_dokumentu.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cast = get_object_or_404(
            DokumentCast,
            ident_cely=self.kwargs["cast_ident_cely"],
        )
        self.get_cast(context, cast)
        context["active_dc_ident"] = cast.ident_cely
        return context


class DokumentCastEditView(LoginRequiredMixin, UpdateView):
    model = DokumentCast
    template_name = "core/transakce_modal.html"
    title = _("dokumentCast.modalForm.zmenitPoznamku.title.text")
    id_tag = "edit-cast-form"
    button = _("dokumentCast.modalForm.zmenitPoznamku.submit.button")
    form_class = DokumentCastForm
    slug_field = "ident_cely"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zaznam = self.object
        context = {
            "object": zaznam,
            "title": self.title,
            "id_tag": self.id_tag,
            "button": self.button,
        }
        context["form"] = DokumentCastForm(
            instance=self.object,
        )
        return context

    def get_success_url(self):
        context = self.get_context_data()
        dc = context["object"]
        return dc.get_absolute_url()

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return JsonResponse({"redirect": self.get_success_url()})

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        logger.debug("dokument.views.DokumentCastEditView.form_invalid", extra={"errors": form.errors})
        return super().form_invalid(form)


class KomponentaDokumentDetailView(RelatedContext):
    template_name = "dokument/dok/detail_komponenta.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        komponenta = get_object_or_404(
            Komponenta.objects.select_related(
                "komponenta_vazby__casti_dokumentu",
            ),
            ident_cely=self.kwargs["komp_ident_cely"],
        )
        context["k"] = komponenta
        cast = komponenta.komponenta_vazby.casti_dokumentu
        self.get_cast(context, cast)
        old_nalez_post = self.request.session.pop("_old_nalez_post", None)
        komp_ident_cely = self.request.session.pop("komp_ident_cely", None)

        context["k"] = get_komponenta_form_detail(
            komponenta, context["show"], old_nalez_post, komp_ident_cely
        )
        context["active_komp_ident"] = komponenta.ident_cely
        return context


class KomponentaDokumentCreateView(RelatedContext):
    template_name = "dokument/dok/create_komponenta.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cast = get_object_or_404(
            DokumentCast,
            ident_cely=self.kwargs["cast_ident_cely"],
        )
        self.get_cast(context, cast)
        context["komponenta_form_create"] = CreateKomponentaForm(
            get_obdobi_choices(), get_areal_choices()
        )
        return context


class TvarEditView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        dokument = get_object_or_404(Dokument, ident_cely=self.kwargs["ident_cely"])
        TvarFormset = inlineformset_factory(
            Dokument,
            Tvar,
            form=create_tvar_form(),
            extra=1,
        )
        formset = TvarFormset(
            request.POST, instance=dokument, prefix=dokument.ident_cely + "_d"
        )
        if formset.is_valid():
            logger.debug("dokument.views.TvarEditView.form_valid")
            formset.save()
            if formset.has_changed():
                logger.debug("dokument.views.TvarEditView.form_data_changed")
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.debug("dokument.views.TvarEditView.form_not_valid",
                         extra={"formset_errors": formset.errors, "formset_nonform_errors": formset.non_form_errors()})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        return redirect(dokument.get_absolute_url())


class TvarSmazatView(LoginRequiredMixin, TemplateView):
    template_name = "core/transakce_modal.html"
    title = _("dokument.modalForm.smazatTvar.title.text")
    id_tag = "smazat-tvar-form"
    button = _("dokument.modalForm.smazatTvar.submit.button")

    def get_zaznam(self):
        id = self.kwargs.get("pk")
        return get_object_or_404(
            Tvar,
            pk=id,
        )

    def get_context_data(self, **kwargs):
        zaznam = self.get_zaznam()
        context = {
            "object": zaznam,
            "title": self.title,
            "id_tag": self.id_tag,
            "button": self.button,
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        zaznam = self.get_zaznam()
        dokument = zaznam.dokument
        zaznam.delete()
        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)

        return JsonResponse({"redirect": dokument.get_absolute_url()})


class VytvoritCastView(LoginRequiredMixin, TemplateView):
    template_name = "core/transakce_modal.html"
    title = _("dokument.modalForm.vytvoritCast.title.text")
    id_tag = "vytvor-cast-form"
    button = _("dokument.modalForm.vytvoritCast.submit.button")

    def get_zaznam(self):
        ident_cely = self.kwargs.get("ident_cely")
        return get_object_or_404(
            Dokument,
            ident_cely=ident_cely,
        )

    def get_context_data(self, **kwargs):
        zaznam = self.get_zaznam()
        form = DokumentCastCreateForm()
        context = {
            "object": zaznam,
            "form": form,
            "title": self.title,
            "id_tag": self.id_tag,
            "button": self.button,
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        zaznam = self.get_zaznam()
        form = DokumentCastCreateForm(data=request.POST)
        if form.is_valid():
            dc_ident = get_cast_dokumentu_ident(zaznam)
            DokumentCast(
                dokument=zaznam,
                ident_cely=dc_ident,
                poznamka=form.cleaned_data["poznamka"],
            ).save()
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
            return JsonResponse(
                {
                    "redirect": reverse(
                        "dokument:detail-cast",
                        kwargs={
                            "ident_cely": zaznam.ident_cely,
                            "cast_ident_cely": dc_ident,
                        },
                    )
                }
            )
        else:
            logger.debug("dokument.views.VytvoritCastView.post.form_not_valid", extra={"form_errors": form.errors})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        return JsonResponse({"redirect": zaznam.get_absolute_url()})


class TransakceView(LoginRequiredMixin, TemplateView):
    template_name = "core/transakce_modal.html"
    title = "title"
    id_tag = "id_tag"
    button = "button"
    allowed_states = [D_STAV_ZAPSANY, D_STAV_ODESLANY, D_STAV_ARCHIVOVANY]
    success_message = "success"
    action = ""

    def get_zaznam(self):
        ident_cely = self.kwargs.get("ident_cely")
        logger.debug("dokument.views.TransakceView.get_zaznam", extra={"ident_cely": ident_cely})
        return get_object_or_404(
            DokumentCast,
            ident_cely=ident_cely,
        )

    def get_context_data(self, **kwargs):
        zaznam = self.get_zaznam()
        form_check = CheckStavNotChangedForm(initial={"old_stav": zaznam.dokument.stav})
        context = {
            "object": zaznam,
            "title": self.title,
            "id_tag": self.id_tag,
            "button": self.button,
            "form_check": form_check,
        }
        return context

    def dispatch(self, request, *args, **kwargs):
        zaznam = self.get_zaznam().dokument
        if zaznam.stav not in self.allowed_states:
            logger.debug("dokument.views.TransakceView.dispatch", extra={"action": self.action})
            messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
            return JsonResponse(
                {"redirect": zaznam.get_absolute_url()},
                status=403,
            )
        if check_stav_changed(request, zaznam):
            return JsonResponse(
                {"redirect": zaznam.get_absolute_url()},
                status=403,
            )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        zaznam = self.get_zaznam()
        getattr(Dokument, self.action)(zaznam, request.user)
        messages.add_message(request, messages.SUCCESS, self.success_message)

        return JsonResponse({"redirect": zaznam.get_absolute_url()})


class DokumentCastPripojitAkciView(TransakceView):
    template_name = "core/transakce_table_modal.html"
    title = _("dokument.modalForm.pripojitAZ.title.text")
    id_tag = "pripojit-eo-form"
    button = _("dokument.modalForm.pripojitAZ.submit.button")
    success_message = DOKUMENT_AZ_USPESNE_PRIPOJEN

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        type_arch = self.request.GET.get("type")
        form = PripojitArchZaznamForm(type_arch=type_arch, dok=True)
        context["form"] = form
        context["hide_table"] = True
        context["type"] = type_arch
        context["card_type"] = type_arch
        return context

    def post(self, request, *args, **kwargs):
        cast = self.get_zaznam()
        type_arch = self.request.GET.get("type")
        form = PripojitArchZaznamForm(data=request.POST, type_arch=type_arch, dok=True)
        if form.is_valid():
            logger.debug("dokument.views.DokumentCastPripojitAkciView.post.form_valid")
            arch_z_id = form.cleaned_data["arch_z"]
            arch_z = ArcheologickyZaznam.objects.get(id=arch_z_id)
            cast.archeologicky_zaznam = arch_z
            cast.projekt = None
            cast.save()
            messages.add_message(request, messages.SUCCESS, self.success_message)
        else:
            logger.debug("dokument.views.DokumentCastPripojitAkciView.post.form_invalid",
                         extra={"form_errors": form.errors})
        return JsonResponse({"redirect": cast.get_absolute_url()})


class DokumentCastPripojitProjektView(TransakceView):
    template_name = "core/transakce_table_modal.html"
    title = _("dokument.modalForm.pripojitProjekt.title.text")
    id_tag = "pripojit-projekt-form"
    button = _("dokument.modalForm.pripojitProjekt.submit.button")
    success_message = DOKUMENT_PROJEKT_USPESNE_PRIPOJEN

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = PripojitProjektForm(dok=True)
        context["form"] = form
        context["hide_table"] = True
        return context

    def post(self, request, *args, **kwargs):
        cast = self.get_zaznam()
        form = PripojitProjektForm(data=request.POST, dok=True)
        if form.is_valid():
            projekt = form.cleaned_data["projekt"]
            cast.archeologicky_zaznam = None
            cast.projekt = Projekt.objects.get(id=projekt)
            cast.save()
            messages.add_message(request, messages.SUCCESS, self.success_message)
        else:
            logger.debug("dokument.views.DokumentCastPripojitProjektView.post.form_invalid",
                         extra={"form_errors": form.errors})
        return JsonResponse({"redirect": cast.get_absolute_url()})


class DokumentCastOdpojitView(TransakceView):
    title = _("dokument.modalForm.odpojitVazbuCast.title.text")
    id_tag = "odpojit-cast-form"
    button = _("dokument.modalForm.odpojitVazbuCast.submit.button")
    success_message = DOKUMENT_CAST_USPESNE_ODPOJEN

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cast = self.get_zaznam()
        if cast.archeologicky_zaznam is not None:
            context["object"] = get_object_or_404(
                ArcheologickyZaznam,
                id=cast.archeologicky_zaznam.id,
            )
        else:
            context["object"] = get_object_or_404(
                Projekt,
                id=cast.projekt.id,
            )
        return context

    def post(self, request, *args, **kwargs):
        cast = self.get_zaznam()
        cast.archeologicky_zaznam = None
        cast.projekt = None
        cast.save()
        messages.add_message(request, messages.SUCCESS, self.success_message)
        return JsonResponse({"redirect": cast.get_absolute_url()})


class DokumentCastSmazatView(TransakceView):
    title = _("dokument.modalForm.smazatCast.title.text")
    id_tag = "smazat-cast-form"
    button = _("dokument.modalForm.smazatCast.submit.button")
    success_message = DOKUMENT_CAST_USPESNE_SMAZANA

    def post(self, request, *args, **kwargs):
        cast = self.get_zaznam()
        dokument = cast.dokument
        if cast.komponenty:
            komps = cast.komponenty
            cast.komponenty = None
            cast.save()
            komps.delete()
        cast.delete()
        messages.add_message(request, messages.SUCCESS, self.success_message)
        return JsonResponse({"redirect": dokument.get_absolute_url()})


class DokumentNeidentAkceSmazatView(TransakceView):
    title = _("dokument.modalForm.smazatNeidentAkce.title.text")
    id_tag = "smazat-neident-akce-form"
    button = _("dokument.modalForm.smazatNeidentAkce.submit.button")
    success_message = DOKUMENT_NEIDENT_AKCE_USPESNE_SMAZANA

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = context["object"].neident_akce
        return context

    def post(self, request, *args, **kwargs):
        cast = self.get_zaznam()
        if cast.neident_akce:
            cast.neident_akce.delete()
            messages.add_message(request, messages.SUCCESS, self.success_message)
        else:
            messages.add_message(request, messages.SUCCESS, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
        return JsonResponse({"redirect": cast.get_absolute_url()})


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
            logger.debug("dokument.views.edit.both_forms_valid")
            instance_d = form_d.save(commit=False)
            instance_d.osoby.set(form_extra.cleaned_data["dokument_osoba"])
            # instance_d.osoby.set(form_d.cleaned_data["jazyky"])
            if form_extra.cleaned_data["let"]:
                instance_d.let = Let.objects.get(id=form_extra.cleaned_data["let"])
            instance_d.autori.clear()
            instance_d.save()
            # form_d.save_m2m()
            form_extra.save()
            i = 1
            for autor in form_d.cleaned_data["autori"]:
                DokumentAutor(
                    dokument=dokument,
                    autor=autor,
                    poradi=i,
                ).save()
                i = i + 1
            if form_d.has_changed() or form_extra.has_changed():
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return redirect("dokument:detail", ident_cely=dokument.ident_cely)
        else:
            logger.debug("dokument.views.edit.forms_not_valid", extra={"form_errors": form_d.errors,
                                                                       "form_extra_errors": form_extra.errors})
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
        dx = None
        dy = None
        try:
            dx = float(form_coor.data.get("coordinate_x"))
            dy = float(form_coor.data.get("coordinate_y"))
            if dx > 0 and dy > 0:
                geom = Point(dy, dx)
        except Exception:
            logger.debug("dokument.views.edit_model_3D.coord_error", extra={"dx": dx, "dy": dy})
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
            logger.debug("dokument.views.edit_model_3D.forms_not_valid",
                         extra={"form_errors": form_d.errors, "form_extra_errors": form_extra.errors,
                                "form_komponenta": form_komponenta.errors})
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
        dx = None
        dy = None
        try:
            dx = float(form_extra.data.get("coordinate_x"))
            dy = float(form_extra.data.get("coordinate_y"))
            if dx > 0 and dy > 0:
                geom = Point(dy, dx)
        except Exception:
            logger.debug("dokument.views.create_model_3D.coord_error", extra={"dx": dx, "dy": dy})

        if form_d.is_valid() and form_extra.is_valid() and form_komponenta.is_valid():
            logger.debug("dokument.views.create_model_3D.forms_valid")
            dokument = form_d.save(commit=False)
            dokument.rada = Heslar.objects.get(id=DOKUMENT_RADA_DATA_3D)
            dokument.material_originalu = Heslar.objects.get(
                id=MATERIAL_DOKUMENTU_DIGITALNI_SOUBOR
            )
            try:
                dokument.ident_cely = get_temp_dokument_ident(rada="3D", region="C-")
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
            logger.debug("dokument.views.create_model_3D.forms_not_valid",
                         extra={"form_errors": form_d.errors, "form_extra_errors": form_extra.errors,
                                "form_komponenta": form_komponenta.errors})
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
    logger.debug("dokument.views.odeslat.start", ident_cely=ident_cely)
    if d.stav != D_STAV_ZAPSANY:
        logger.debug("dokument.views.odeslat.permission_denied", extra={"ident_cely": ident_cely})
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, d):
        logger.debug("dokument.views.odeslat.check_stav_changed", extra={"ident_cely": ident_cely})

        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    if request.method == "POST":
        d.set_odeslany(request.user)
        messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_ODESLAN)
        logger.debug("dokument.views.odeslat.sucess")
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)})
    else:
        warnings = d.check_pred_odeslanim()
        if warnings:
            logger.debug("dokument.views.odeslat.warnings", extra={"warnings": warnings, "ident_cely": ident_cely})
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
    logger.debug("dokument.views.odeslat.finish", extra={"ident_cely": ident_cely})
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def archivovat(request, ident_cely):
    d = get_object_or_404(Dokument, ident_cely=ident_cely)
    logger.debug("dokument.views.archivovat.start", extra={"ident_cely": ident_cely})
    if d.stav != D_STAV_ODESLANY:
        logger.debug("dokument.views.archivovat.permission_denied", extra={"ident_cely": ident_cely})
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, d):
        logger.debug("dokument.views.archivovat.check_stav_changed", extra={"ident_cely": ident_cely})
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
            except FileNotFoundError as e:
                messages.add_message(
                    request, messages.ERROR, DOKUMENT_NELZE_ARCHIVOVAT_CHYBY_SOUBOR
                )
                return JsonResponse(
                    {"redirect": get_detail_json_view(ident_cely)}, status=403
                )
            else:
                d.save()
                logger.debug("dokument.views.archivovat.permanent", extra={"ident_cely": d.ident_cely})
        d.set_archivovany(request.user)
        messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_ARCHIVOVAN)
        Mailer.send_ek01(document=d)
        return JsonResponse({"redirect": get_detail_json_view(d.ident_cely)})
    else:
        warnings = d.check_pred_archivaci()
        logger.debug("dokument.views.archivovat.warnings", extra={"warnings": warnings})
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
            if d.stav == D_STAV_ODESLANY:
                Mailer.send_ek02(document=d, reason=duvod)
            d.set_vraceny(request.user, d.stav - 1, duvod)
            messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_VRACEN)
            return JsonResponse({"redirect": get_detail_json_view(ident_cely)})
        else:
            logger.debug("dokument.views.vratit.not_valid", extra={"errors": form.errors})
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
                logger.debug("dokument.views.smazat.deleting", extra={"ident_cely": k.ident_cely})
                k.delete()

        if resp1:
            logger.debug("dokument.views.smazat.deleted", extra={"resp1": resp1, "resp2": resp2, "resp3": resp3})
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            return JsonResponse({"redirect": reverse("core:home")})
        else:
            logger.warning("dokument.views.smazat.not_deleted", extra={"ident_cely": ident_cely})
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
        qs = (
            qs.filter(stav__in=(D_STAV_ARCHIVOVANY, D_STAV_ODESLANY))
            .annotate(ident_len=Length("ident_cely"))
            .filter(ident_len__gt=0)
        )
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
    show_tvary = True if dokument.rada.zkratka in ["LD", "LN", "DL"] else False
    show = {
        "vratit_link": show_vratit,
        "odeslat_link": show_odeslat,
        "archivovat_link": show_archivovat,
        "editovat": show_edit,
        "arch_links": show_arch_links,
        "tvary": show_tvary,
    }
    return show


def zapsat(request, zaznam=None):
    required_fields = get_required_fields_dokument()
    required_fields_next = get_required_fields_dokument(next=1)
    if request.method == "POST":
        form_d = EditDokumentForm(
            request.POST,
            required=required_fields,
            required_next=required_fields_next,
        )
        if form_d.is_valid():
            logger.debug("dokument.views.zapsat.valid")
            dokument = form_d.save(commit=False)
            dokument.rada = get_dokument_rada(
                dokument.typ_dokumentu, dokument.material_originalu
            )
            try:
                if zaznam:
                    prefix = zaznam.ident_cely[0] + "-"
                    if isinstance(zaznam, ArcheologickyZaznam):
                        if zaznam.ident_cely.startswith("X"):
                            prefix = zaznam.ident_cely[2] + "-"
                            logger.debug(prefix)
                else:
                    prefix = form_d.cleaned_data["region"]
                dokument.ident_cely = get_temp_dokument_ident(
                    rada=dokument.rada.zkratka, region=prefix
                )
            except MaximalIdentNumberError:
                messages.add_message(request, messages.ERROR, MAXIMUM_IDENT_DOSAZEN)
            else:
                dokument.stav = D_STAV_ZAPSANY
                dokument.save()
                dokument.set_zapsany(request.user)
                i = 1
                for autor in form_d.cleaned_data["autori"]:
                    DokumentAutor(
                        dokument=dokument,
                        autor=autor,
                        poradi=i,
                    ).save()
                    i = i + 1

                # Vytvorit defaultni cast dokumentu
                if zaznam:
                    if isinstance(zaznam, ArcheologickyZaznam):
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
            logger.debug("dokument.views.zapsat.not_valid", extra={"erros": form_d.errors})

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
            "samostatny": True if not zaznam else False,
        },
    )


def odpojit(request, ident_doku, ident_zaznamu, zaznam):
    relace_dokumentu = DokumentCast.objects.filter(dokument__ident_cely=ident_doku)
    remove_orphan = False
    orphan_dokument = None
    if len(relace_dokumentu) == 0:
        logger.debug("dokument.views.odpojit.no_relace", extra={"ident_doku": ident_doku})
        messages.add_message(request, messages.ERROR, DOKUMENT_ODPOJ_ZADNE_RELACE)
        return JsonResponse({"redirect": zaznam.get_absolute_url()}, status=404)
    if len(relace_dokumentu) == 1:
        orphan_dokument = relace_dokumentu[0].dokument
        if orphan_dokument.ident_cely.startswith("X-"):
            remove_orphan = True
    if request.method == "POST":
        if isinstance(zaznam, ArcheologickyZaznam):
            dokument_cast = relace_dokumentu.filter(
                archeologicky_zaznam__ident_cely=ident_zaznamu
            )
        else:
            dokument_cast = relace_dokumentu.filter(projekt__ident_cely=ident_zaznamu)
        if len(dokument_cast) == 0:
            logger.debug("dokument.views.odpojit.no_relace", extra={"ident_doku": ident_doku})
            messages.add_message(
                request, messages.ERROR, DOKUMENT_ODPOJ_ZADNE_RELACE_MEZI_DOK_A_ZAZNAM
            )
            return JsonResponse({"redirect": zaznam.get_absolute_url()}, status=404)
        resp = dokument_cast[0].delete()
        logger.debug("dokument.views.odpojit.deleted", extra={"resp": resp})
        if remove_orphan:
            orphan_dokument.delete()
            logger.debug("dokument.views.odpojit.deleted")
        messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_ODPOJEN)
        return JsonResponse({"redirect": zaznam.get_absolute_url()})
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
    if isinstance(zaznam, ArcheologickyZaznam):
        casti_zaznamu = DokumentCast.objects.filter(
            archeologicky_zaznam__ident_cely=ident_zaznam
        )
        debug_name = "akci "
        redirect_name = zaznam.get_absolute_url()
        context = {
            "object": zaznam,
            "title": _("dokument.modalForm.pripojitDoAkce.title.text"),
            "id_tag": "pripojit-dokument-form",
            "button": _("dokument.modalForm.pripojitDoAkce.submit.button"),
        }
    else:
        casti_zaznamu = DokumentCast.objects.filter(projekt__ident_cely=ident_zaznam)
        debug_name = "projektu "
        redirect_name = reverse("projekt:detail", kwargs={"ident_cely": ident_zaznam})
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
                logger.debug("dokument.views.pripojit.pripojit",
                             extra={"debug_name": debug_name, "ident_zaznam": ident_zaznam,
                                    "ident_cely": dokument.ident_cely})
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    DOKUMENT_USPESNE_PRIPOJEN,
                )
            else:
                messages.add_message(
                    request, messages.WARNING, DOKUMENT_JIZ_BYL_PRIPOJEN
                )
        return JsonResponse({"redirect": redirect_name})
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
    context = {"d": Dokument.objects.get(id=request.GET.get("id", ""))}
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


def get_komponenta_form_detail(komponenta, show, old_nalez_post, komp_ident_cely):
    NalezObjektFormset = inlineformset_factory(
        Komponenta,
        NalezObjekt,
        form=create_nalez_objekt_form(
            heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT),
            heslar_12(HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT),
            not_readonly=show["editovat"],
        ),
        extra=1 if show["editovat"] else 0,
        can_delete=False,
    )
    NalezPredmetFormset = inlineformset_factory(
        Komponenta,
        NalezPredmet,
        form=create_nalez_predmet_form(
            heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT),
            list(
                Heslar.objects.filter(
                    nazev_heslare=HESLAR_PREDMET_SPECIFIKACE
                ).values_list("id", "heslo")
            ),
            not_readonly=show["editovat"],
        ),
        extra=1 if show["editovat"] else 0,
        can_delete=False,
    )

    komponenta_form_detail = {
        "ident_cely": komponenta.ident_cely,
        "form": CreateKomponentaForm(
            get_obdobi_choices(),
            get_areal_choices(),
            instance=komponenta,
            prefix=komponenta.ident_cely,
            readonly=not show["editovat"],
        ),
        "form_nalezy_objekty": NalezObjektFormset(
            old_nalez_post,
            instance=komponenta,
            prefix=komponenta.ident_cely + "_o",
        )
        if komponenta.ident_cely == komp_ident_cely
        else NalezObjektFormset(
            instance=komponenta, prefix=komponenta.ident_cely + "_o"
        ),
        "form_nalezy_predmety": NalezPredmetFormset(
            old_nalez_post,
            instance=komponenta,
            prefix=komponenta.ident_cely + "_p",
        )
        if komponenta.ident_cely == komp_ident_cely
        else NalezPredmetFormset(
            instance=komponenta, prefix=komponenta.ident_cely + "_p"
        ),
        "helper_predmet": NalezFormSetHelper(typ="predmet"),
        "helper_objekt": NalezFormSetHelper(typ="objekt"),
    }
    return komponenta_form_detail


def get_obdobi_choices():
    return heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)


def get_areal_choices():
    return heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
