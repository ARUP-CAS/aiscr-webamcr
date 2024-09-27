import logging
from datetime import datetime, timedelta

from cacheops import invalidate_model
from typing import Any
import simplejson as json

from django.db.models.signals import post_save
from django.views import View


from arch_z.models import ArcheologickyZaznam, Akce
from core.constants import (
    ARCHIVACE_DOK,
    D_STAV_ARCHIVOVANY,
    D_STAV_ODESLANY,
    D_STAV_ZAPSANY,
    DOKUMENT_CAST_RELATION_TYPE,
    IDENTIFIKATOR_DOCASNY_PREFIX,
    ODESLANI_DOK,
    ZAPSANI_DOK, ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID,
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
    PROJEKT_NENI_TYP_PRUZKUMNY,
    SPATNY_ZAZNAM_ZAZNAM_VAZBA,
    VYBERTE_PROSIM_POLOHU,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN, ZAZNAM_NELZE_SMAZAT_FEDORA,
)
from core.repository_connector import FedoraTransaction, FedoraRepositoryConnector
from core.views import PermissionFilterMixin, SearchListView, check_stav_changed
from core.models import Permissions as p, check_permissions
from dal import autocomplete
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.forms import inlineformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.http import url_has_allowed_host_and_scheme
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
)
from heslar.hesla_dynamicka import (
    DOKUMENT_RADA_DATA_3D,
    MATERIAL_DOKUMENTU_DIGITALNI_SOUBOR,
    MODEL_3D_DOKUMENT_TYPES,
    PRISTUPNOST_BADATEL_ID,
    TYP_PROJEKTU_PRUZKUM_ID,
)
from heslar.models import Heslar, HeslarHierarchie
from heslar.views import heslar_12, heslar_list
from historie.models import Historie
from komponenta.forms import CreateKomponentaForm
from komponenta.models import Komponenta, KomponentaAktivita, KomponentaVazby
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

from uzivatel.models import Osoba, User

from core.utils import (
    get_3d_from_envelope,
)

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def index_model_3D(request):
    """
    Funkce pohledu pro zobrazení domovské stránky modelu 3D s navigačními možnostmi.
    """
    return render(request, "dokument/index_model_3D.html")


@login_required
@require_http_methods(["GET"])
def detail_model_3D(request, ident_cely):
    """
    Třida pohledu pro zobrazení detailu modelu 3D.
    """
    context = {"warnings": request.session.pop("temp_data", None)}
    old_nalez_post = request.session.pop("_old_nalez_post", None)
    dokument = get_object_or_404(
        Dokument.objects.select_related(
            "soubory",
            "organizace",
            "typ_dokumentu",
        ),
        ident_cely=ident_cely,
        typ_dokumentu__id__in=MODEL_3D_DOKUMENT_TYPES
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
    show = get_detail_template_shows(dokument, request.user)
    obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
    areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
    druh_objekt_choices = heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT)
    druh_predmet_choices = heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT)
    specifikace_objekt_choices = heslar_12(
        HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT
    )
    specifikce_predmetu_choices = heslar_list(HESLAR_PREDMET_SPECIFIKACE)
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
        context["coordinate_wgs84_x1"] = geom.split(" ")[0]
        context["coordinate_wgs84_x2"] = geom.split(" ")[1]
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
    context["history_dates"] = get_history_dates(dokument.historie, request.user)
    context["show"] = show
    context["global_map_can_edit"] = False
    if dokument.soubory:
        context["soubory"] = sorted(dokument.soubory.soubory.all(), key=lambda x: (x.nazev.replace('.', '0'), x.nazev))
    else:
        context["soubory"] = None
    return render(request, "dokument/detail_model_3D.html", context)


class Model3DListView(SearchListView):
    """
    Třida pohledu pro zobrazení listu/tabulky s modelama 3D.
    """
    table_class = Model3DTable
    model = Dokument
    filterset_class = Model3DFilter
    export_name = "export_modely_"
    app = "knihovna_3d"
    toolbar = "toolbar_dokument.html"
    redis_snapshot_prefix = "dokument"
    redis_value_list_field = "ident_cely"
    typ_zmeny_lookup = ZAPSANI_DOK

    def init_translations(self):
        super().init_translations()
        self.page_title = _("dokument.views.Model3DListView.pageTitle.text")
        self.search_sum = _("dokument.views.Model3DListView.search_sum.text")
        self.pick_text = _("dokument.views.Model3DListView.pick_text.text")
        self.hasOnlyVybrat_header = _("dokument.views.Model3DListView.hasOnlyVybrat_header.text")
        self.hasOnlyVlastnik_header = _("dokument.views.Model3DListView.hasOnlyVlastnik_header.text")
        self.hasOnlyArchive_header = _("dokument.views.Model3DListView.hasOnlyArchive_header.text")
        self.hasOnlyNase_header = _("dokument.views.Model3DListView.hasOnlyNase_header.text")
        self.default_header = _("dokument.views.Model3DListView.default_header.text")

    @staticmethod
    def rename_field_for_ordering(field: str):
        field = field.replace("-", "")
        return {
            "typ_dokumentu": "typ_dokumentu__razeni",
            "autori": "autori_snapshot",
            "extra_data__format": "extra_data__format__razeni",
            "extra_data__zeme": "extra_data__zeme__razeni"
        }.get(field, field)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_3d"] = True
        return context

    def get_queryset(self):
        sort_params = self._get_sort_params()
        sort_params = [self.rename_field_for_ordering(x) for x in sort_params]
        qs = super().get_queryset()
        qs = qs.order_by(*sort_params)  
        qs = qs.distinct("pk", *sort_params)
        qs = qs.filter(ident_cely__contains="3D")
        qs = qs.select_related(
            "typ_dokumentu", "extra_data", "organizace", "extra_data__format"
        ).prefetch_related(
            Prefetch(
                "autori",
                queryset=Osoba.objects.all().order_by("dokumentautor__poradi"),
                to_attr="ordered_autors",
            ),"extra_data__zeme","soubory__soubory"
        )
               
        return self.check_filter_permission(qs)


class DokumentIndexView(LoginRequiredMixin, TemplateView):
    """
    Třida pohledu pro zobrazení domovské stránky dokumentů s navigačními možnostmi.
    """
    template_name = "dokument/index_dokument.html"


class DokumentListView(SearchListView):
    """
    Třida pohledu pro zobrazení listu/tabulky s dokumentama.
    """
    table_class = DokumentTable
    model = Dokument
    filterset_class = DokumentFilter
    export_name = "export_dokumenty_"
    app = "dokument"
    toolbar = "toolbar_dokument.html"
    redis_snapshot_prefix = "dokument"
    redis_value_list_field = "ident_cely"
    typ_zmeny_lookup = ZAPSANI_DOK

    def init_translations(self):
        super().init_translations()
        self.page_title = _("dokument.views.DokumentListView.pageTitle.text")
        self.search_sum = _("dokument.views.DokumentListView.search_sum.text")
        self.pick_text = _("dokument.views.DokumentListView.pick_text.text")
        self.hasOnlyVybrat_header = _("dokument.views.DokumentListView.hasOnlyVybrat_header.text")
        self.hasOnlyVlastnik_header = _("dokument.views.DokumentListView.hasOnlyVlastnik_header.text")
        self.hasOnlyArchive_header = _("dokument.views.DokumentListView.hasOnlyArchive_header.text")
        self.hasOnlyNase_header = _("dokument.views.DokumentListView.hasOnlyNase_header.text")
        self.default_header = _("dokument.views.DokumentListView.default_header.text")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_3d"] = False
        return context

    @staticmethod
    def rename_field_for_ordering(field: str):
        field = field.replace("-", "")
        return {
            "typ_dokumentu": "typ_dokumentu__razeni",
            "autori": "autori_snapshot",
            "pristupnost": "pristupnost__razeni",
            "rada":"rada__razeni",
            "material_originalu":"material_originalu__razeni",
            "extra_data__format":"extra_data__format__razeni",
            "ulozeni_originalu":"ulozeni_originalu__razeni",
            "licence":"licence__razeni",
            "extra_data__zachovalost":"extra_data__zachovalost__razeni",
            "extra_data__nahrada":"extra_data__nahrada__razeni",
            "extra_data__zeme":"extra_data__zeme__razeni",
            "extra_data__udalost_typ": "extra_data__udalost_typ__razeni",
            "osoby":"osoby_snapshot",
            "let": "let__ident_cely"
        }.get(field, field)

    def get_queryset(self):
        sort_params = self._get_sort_params()
        sort_params = [self.rename_field_for_ordering(x) for x in sort_params]
        qs = super().get_queryset()
        qs = qs.order_by(*sort_params) 
        qs = qs.distinct("pk", *sort_params)
        subqry = Subquery(
            Soubor.objects.filter(vazba=OuterRef("vazba")).values_list("id", flat=True)[:1]
        )
        qs = qs.exclude(ident_cely__contains="3D")
        qs = qs.select_related(           
            "extra_data",
            "organizace",
            "extra_data__format",
            "soubory",            
            "material_originalu",
            "ulozeni_originalu",
        ).prefetch_related(
            Prefetch(
                "soubory__soubory",
                queryset=Soubor.objects.filter(id__in=subqry),
                to_attr="first_soubor",
            ),
            Prefetch(
                "autori",
                queryset=Osoba.objects.all().order_by("dokumentautor__poradi"),
                to_attr="ordered_autors",
            ), "typ_dokumentu", "let", "rada","pristupnost",
        )
        return self.check_filter_permission(qs)


class RelatedContext(LoginRequiredMixin, TemplateView):
    """
    Třida, která se dedí a která obsahuje metódy pro získaní relací dokumentů.
    """
    def get_cast(self, context, cast, **kwargs):
        """
        Metóda pro získaní informací ohlědně části dokumentu.
        """
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
        context["show_edit_cast"] = check_permissions(p.actionChoices.dok_cast_edit, self.request.user, cast.dokument.ident_cely)
        context["show_smazat_cast"] = check_permissions(p.actionChoices.dok_cast_smazat, self.request.user, cast.dokument.ident_cely)
        context["show_zapsat_komponentu"] = check_permissions(p.actionChoices.dok_komponenta_zapsat, self.request.user, cast.dokument.ident_cely)
        context["show_neident_akce_edit"] = check_permissions(p.actionChoices.neident_akce_edit, self.request.user, cast.dokument.ident_cely)
        context["show_neident_akce_smazat"] = check_permissions(p.actionChoices.neident_akce_smazat, self.request.user, cast.dokument.ident_cely)
        context["show_odpojit"] = False
        context["show_pripojit_proj"] = check_permissions(p.actionChoices.dok_pripojit_proj, self.request.user, cast.dokument.ident_cely)
        context["show_pripojit_archz"] = check_permissions(p.actionChoices.dok_pripojit_archz, self.request.user, cast.dokument.ident_cely)
        if cast.projekt or cast.archeologicky_zaznam:
            context["show_odpojit"] = check_permissions(p.actionChoices.dok_cast_odpojit, self.request.user, cast.dokument.ident_cely)
            context["show_pripojit_proj"] = False
            context["show_pripojit_archz"] = False

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní contextu dokumentu pro template.
        """
        context = super().get_context_data(**kwargs)
        context["warnings"] = self.request.session.pop("temp_data", None)
        dokument = get_object_or_404(
            Dokument.objects.exclude(typ_dokumentu__id__in=MODEL_3D_DOKUMENT_TYPES).select_related(
                "soubory",
                "organizace",
                "material_originalu",
                "typ_dokumentu",
                "rada",
            ),
            ident_cely=self.kwargs["ident_cely"]
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
        show = get_detail_template_shows(dokument, self.request.user)
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
        context["history_dates"] = get_history_dates(dokument.historie, self.request.user)
        context["show"] = show

        if dokument.soubory:
            context["soubory"] = sorted(dokument.soubory.soubory.all(),
                                        key=lambda x: (x.nazev.replace('.', '0'), x.nazev))
        else:
            context["soubory"] = None

        context["casti"] = dokument.casti.all()
        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Metóda pro render response, kvúli správnemu zobrazení zpět možnosti.
        """
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
                "soubor/nahrat" in referer
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
    """
    Třida pohledu pro zobrazení detailu dokumentu.
    """
    template_name = "dokument/dok/detail.html"


class DokumentCastDetailView(RelatedContext):
    """
    Třida pohledu pro zobrazení detailu části dokumentu.
    """
    template_name = "dokument/dok/detail_cast_dokumentu.html"

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        cast = get_object_or_404(DokumentCast, ident_cely=self.kwargs["cast_ident_cely"])
        if cast.dokument.ident_cely != self.kwargs["ident_cely"]:
            logger.error("Dokument - Dokument cast wrong relation")
            messages.add_message(
                        request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA
                    )
            if url_has_allowed_host_and_scheme(request.GET.get("next","core:home"), allowed_hosts=settings.ALLOWED_HOSTS):
                safe_redirect = request.GET.get("next","core:home")
            else:
                safe_redirect = "/"
            return redirect(safe_redirect)
        return super().dispatch(request, *args, **kwargs)

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
    """
    Třida pohledu pro editaci části dokumentu pomocí modalu.
    """
    model = DokumentCast
    template_name = "core/transakce_modal.html"
    id_tag = "edit-cast-form"
    form_class = DokumentCastForm
    slug_field = "ident_cely"
    active_transaction = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zaznam = self.object
        context = {
            "object": zaznam,
            "title": _("dokument.views.DokumentCastEditView.title.text"),
            "id_tag": self.id_tag,
            "button": _("dokument.views.DokumentCastEditView.submitButton.text"),
        }
        context["form"] = DokumentCastForm(
            instance=self.object,
        )
        return context

    def get_success_url(self):
        context = self.get_context_data()
        dc = context["object"]
        return dc.get_absolute_url()

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            self.object = self.object
        else:
            self.object = super().get_object(queryset)
        if self.active_transaction and not self.object.active_transaction:
            self.object.active_transaction = self.active_transaction
        return self.object

    def post(self, request, *args, **kwargs):
        self.active_transaction = self.object.create_transaction(request.user)
        super().post(request, *args, **kwargs)
        self.active_transaction.mark_transaction_as_closed()
        return JsonResponse({"redirect": self.get_success_url()})

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        logger.debug("dokument.views.DokumentCastEditView.form_invalid", extra={"errors": form.errors})
        return super().form_invalid(form)


class KomponentaDokumentDetailView(RelatedContext):
    """
    Třida pohledu pro zobrazení detailu komponenty části dokumentu.
    """
    template_name = "dokument/dok/detail_komponenta.html"

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        komponenta = get_object_or_404(Komponenta, ident_cely=self.kwargs["komp_ident_cely"])
        if komponenta.komponenta_vazby.casti_dokumentu.dokument.ident_cely != self.kwargs["ident_cely"]:
            logger.error("Dokument - Komponenta wrong relation")
            messages.add_message(
                        request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA
                    )
            if url_has_allowed_host_and_scheme(request.GET.get("next","core:home"), allowed_hosts=settings.ALLOWED_HOSTS):
                safe_redirect = request.GET.get("next","core:home")
            else:
                safe_redirect = "/"
            return redirect(safe_redirect)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        komponenta = get_object_or_404(
            Komponenta.objects.select_related(
                "komponenta_vazby__casti_dokumentu",
            ),
            ident_cely=self.kwargs["komp_ident_cely"],
        )
        cast = komponenta.komponenta_vazby.casti_dokumentu
        self.get_cast(context, cast)
        old_nalez_post = self.request.session.pop("_old_nalez_post", None)
        komp_ident_cely = self.request.session.pop("komp_ident_cely", None)

        context["k"] = get_komponenta_form_detail(
            komponenta, context["show"], old_nalez_post, komp_ident_cely
        )
        context["active_komp_ident"] = komponenta.ident_cely
        context["show"]["komponenta_smazat"] = check_permissions(p.actionChoices.komponenta_smazat_dok, self.request.user, context["dokument"].ident_cely)
        return context


class KomponentaDokumentCreateView(RelatedContext):
    """
    Třida pohledu pro vytvoření komponenty části dokumentu.
    """
    template_name = "dokument/dok/create_komponenta.html"

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        cast = get_object_or_404(DokumentCast, ident_cely=self.kwargs["cast_ident_cely"])
        if cast.dokument.ident_cely != self.kwargs["ident_cely"]:
            logger.error("Dokument - Dokument cast wrong relation")
            messages.add_message(
                        request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA
                    )
            if url_has_allowed_host_and_scheme(request.GET.get("next","core:home"), allowed_hosts=settings.ALLOWED_HOSTS):
                safe_redirect = request.GET.get("next","core:home")
            else:
                safe_redirect = "/"
            return redirect(safe_redirect)
        return super().dispatch(request, *args, **kwargs)

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
    """
    Třida pohledu pro uložení zmeny tvaru z formuláře.
    """
    def post(self, request, *args, **kwargs):
        dokument: Dokument = get_object_or_404(Dokument.objects.exclude(typ_dokumentu__id__in=MODEL_3D_DOKUMENT_TYPES), ident_cely=self.kwargs["ident_cely"])
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
                fedora_transaction = dokument.create_transaction(self.request.user)
                dokument.save_metadata(fedora_transaction, close_transaction=True)
                logger.debug("dokument.views.TvarEditView.form_data_changed")
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.debug("dokument.views.TvarEditView.form_not_valid",
                         extra={"formset_errors": formset.errors, "formset_nonform_errors": formset.non_form_errors()})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        return redirect(dokument.get_absolute_url())


class TvarSmazatView(LoginRequiredMixin, TemplateView):
    """
    Třida pohledu pro smazání tvaru dokumentu pomocí modalu.
    """
    template_name = "core/transakce_modal.html"
    id_tag = "smazat-tvar-form"

    def dispatch(self, request, *args: Any, **kwargs: Any) -> HttpResponse:
        tvar = self.get_zaznam()
        if tvar.dokument.ident_cely != self.kwargs.get("ident_cely"):
            logger.debug("Dokument - Tvar wrong relation")
            messages.add_message(
                            request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA
                        )
            return JsonResponse({"redirect": tvar.dokument.get_absolute_url()},status=403)
        return super().dispatch(request, *args, **kwargs)

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
            "title": _("dokument.views.TvarSmazatView.title.text"),
            "id_tag": self.id_tag,
            "button": _("dokument.views.TvarSmazatView.submitButton.text"),
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        zaznam: Tvar = self.get_zaznam()
        zaznam.active_transaction = zaznam.create_transaction(request.user)
        zaznam.close_active_transaction_when_finished = True
        dokument = zaznam.dokument
        zaznam.delete()
        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)

        return JsonResponse({"redirect": dokument.get_absolute_url()})


class VytvoritCastView(LoginRequiredMixin, TemplateView):
    """
    Třida pohledu pro vytvoření části dokumentu pomoci modalu.
    """
    template_name = "core/transakce_modal.html"
    id_tag = "vytvor-cast-form"

    def get_zaznam(self) -> Dokument:
        ident_cely = self.kwargs.get("ident_cely")
        return get_object_or_404(
            Dokument.objects.exclude(typ_dokumentu__id__in=MODEL_3D_DOKUMENT_TYPES),
            ident_cely=ident_cely,
        )

    def get_context_data(self, **kwargs):
        zaznam = self.get_zaznam()
        form = DokumentCastCreateForm()
        context = {
            "object": zaznam,
            "form": form,
            "title": _("dokument.views.VytvoritCastView.title.text"),
            "id_tag": self.id_tag,
            "button": _("dokument.views.VytvoritCastView.submitButton.text"),
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        zaznam: Dokument = self.get_zaznam()
        form = DokumentCastCreateForm(data=request.POST)
        if form.is_valid():
            fedora_transaction = zaznam.create_transaction(self.request.user)
            zaznam.active_transaction = fedora_transaction
            dc_ident = get_cast_dokumentu_ident(zaznam)
            dc = DokumentCast(
                dokument=zaznam,
                ident_cely=dc_ident,
                poznamka=form.cleaned_data["poznamka"],
            )
            dc.active_transaction = fedora_transaction
            dc.save()
            zaznam.close_active_transaction_when_finished = True
            zaznam.save()
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
    """
    Třida pohledu pro změnu stavu a práci s dokumentama cez modal, která se dedí pro jednotlivá změny.
    """
    template_name = "core/transakce_modal.html"
    id_tag = "id_tag"
    allowed_states = [D_STAV_ZAPSANY, D_STAV_ODESLANY, D_STAV_ARCHIVOVANY]
    success_message = _("dokument.views.TransakceView.success")
    action = ""

    def init_translations(self):
        self.title = "title"
        self.button = "button"

    def get_zaznam(self) -> DokumentCast:
        ident_cely = self.kwargs.get("ident_cely")
        logger.debug("dokument.views.TransakceView.get_zaznam", extra={"ident_cely": ident_cely})
        return get_object_or_404(
            DokumentCast,
            ident_cely=ident_cely,
        )

    def get_context_data(self, **kwargs):
        self.init_translations()
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
    """
    Třida pohledu pro připojení akce do části dokumentu pomoci modalu.
    """
    template_name = "core/transakce_table_modal.html"
    id_tag = "pripojit-eo-form"

    def init_translations(self):
        self.title = _("dokument.views.DokumentCastPripojitAkciView.title.text")
        self.button = _("dokument.views.DokumentCastPripojitAkciView.submitButton.text")
        self.success_message = DOKUMENT_AZ_USPESNE_PRIPOJEN

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
        cast: DokumentCast
        type_arch = self.request.GET.get("type")
        form = PripojitArchZaznamForm(data=request.POST, type_arch=type_arch, dok=True)
        if form.is_valid():
            logger.debug("dokument.views.DokumentCastPripojitAkciView.post.form_valid")
            fedora_transaction = cast.create_transaction(self.request.user)
            cast.active_transaction = fedora_transaction
            arch_z_id = form.cleaned_data["arch_z"]
            arch_z = ArcheologickyZaznam.objects.get(id=arch_z_id)
            cast.archeologicky_zaznam = arch_z
            cast.projekt = None
            cast.close_active_transaction_when_finished = True
            cast.save()
            messages.add_message(request, messages.SUCCESS, self.success_message)
        else:
            logger.debug("dokument.views.DokumentCastPripojitAkciView.post.form_invalid",
                         extra={"form_errors": form.errors})
        return JsonResponse({"redirect": cast.get_absolute_url()})


class DokumentCastPripojitProjektView(TransakceView):
    """
    Třida pohledu pro připojení projektu do části dokumentu pomoci modalu.
    """
    template_name = "core/transakce_table_modal.html"
    id_tag = "pripojit-projekt-form"

    def init_translations(self):
        self.title = _("dokument.views.DokumentCastPripojitProjektView.title.text")
        self.button = _("dokument.views.DokumentCastPripojitProjektView.submitButton.text")
        self.success_message = DOKUMENT_PROJEKT_USPESNE_PRIPOJEN

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
            cast.create_transaction(self.request.user)
            cast.close_active_transaction_when_finished = True
            cast.archeologicky_zaznam = None
            cast.projekt = Projekt.objects.get(id=projekt)
            cast.save()
            messages.add_message(request, messages.SUCCESS, self.success_message)
        else:
            logger.debug("dokument.views.DokumentCastPripojitProjektView.post.form_invalid",
                         extra={"form_errors": form.errors})
        return JsonResponse({"redirect": cast.get_absolute_url()})


class DokumentCastOdpojitView(TransakceView):
    """
    Třida pohledu pro odpojení části dokumentu pomoci modalu.
    """
    id_tag = "odpojit-cast-form"

    def init_translations(self):
        self.title = _("dokument.views.DokumentCastOdpojitView.title.text")
        self.button = _("dokument.views.DokumentCastOdpojitView.submitButton.text")
        self.success_message = DOKUMENT_CAST_USPESNE_ODPOJEN

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
        cast.create_transaction(request.user)
        cast.close_active_transaction_when_finished = True
        cast.archeologicky_zaznam = None
        cast.projekt = None
        cast.save()
        messages.add_message(request, messages.SUCCESS, self.success_message)
        return JsonResponse({"redirect": cast.get_absolute_url()})


class DokumentCastSmazatView(TransakceView):
    """
    Třida pohledu pro smazání části dokumentu pomoci modalu.
    """
    id_tag = "smazat-cast-form"

    def init_translations(self):
        self.title = _("dokument.views.DokumentCastSmazatView.title.text")
        self.button = _("dokument.views.DokumentCastSmazatView.submitButton.text")
        self.success_message = DOKUMENT_CAST_USPESNE_SMAZANA

    def post(self, request, *args, **kwargs):
        cast = self.get_zaznam()
        cast.create_transaction(request.user)
        dokument = cast.dokument
        if cast.komponenty:
            komps = cast.komponenty
            cast.komponenty = None
            cast.save()
            komps.delete()
        try:
            if cast.neident_akce:
                neident_akce = cast.neident_akce
                neident_akce: NeidentAkce
                neident_akce.suppress_signal = True
                neident_akce.delete()
        except ObjectDoesNotExist as err:
            logger.debug("dokument.views.DokumentCastSmazatView.post.neident_akce_not_exists",
                         extra={"ident:cely": cast.ident_cely})
        cast.close_active_transaction_when_finished = True
        cast.delete()
        messages.add_message(request, messages.SUCCESS, self.success_message)
        return JsonResponse({"redirect": dokument.get_absolute_url()})


class DokumentNeidentAkceSmazatView(TransakceView):
    """
    Třida pohledu pro smazání neident akce z části dokumentu pomoci modalu.
    """
    id_tag = "smazat-neident-akce-form"

    def init_translations(self):
        self.title = _("dokument.views.DokumentNeidentAkceSmazatView.title.text")
        self.button = _("dokument.views.DokumentNeidentAkceSmazatView.submitButton.text")
        self.success_message = DOKUMENT_NEIDENT_AKCE_USPESNE_SMAZANA

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
    """
    Funkce pohledu pro editaci dokumentu.
    """
    dokument = get_object_or_404(Dokument.objects.exclude(typ_dokumentu__id__in=MODEL_3D_DOKUMENT_TYPES), ident_cely=ident_cely)
    if dokument.stav == D_STAV_ARCHIVOVANY:
        raise PermissionDenied()
    if not dokument.has_extra_data():
        extra_data = DokumentExtraData(dokument=dokument)
        extra_data.save()
    else:
        extra_data = dokument.extra_data
    if request.user.hlavni_role.id in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID):
        can_edit_datum_zverejneni = True
    else:
        can_edit_datum_zverejneni = False
    required_fields = get_required_fields_dokument(dokument)
    required_fields_next = get_required_fields_dokument(dokument, next=1)
    if request.method == "POST":
        fedora_transaction = dokument.create_transaction(request.user)
        form_d = EditDokumentForm(
            request.POST,
            instance=dokument,
            required=get_required_fields_dokument(dokument),
            required_next=get_required_fields_dokument(dokument, 1),
            can_edit_datum_zverejneni=can_edit_datum_zverejneni,
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
            instance_d: Dokument
            instance_d.active_transaction = fedora_transaction
            instance_d.osoby.set(form_extra.cleaned_data["dokument_osoba"])
            if form_extra.cleaned_data["let"]:
                instance_d.let = Let.objects.get(id=form_extra.cleaned_data["let"])
            else:
                instance_d.let = None
            instance_d.autori.clear()
            i = 1
            for autor in form_d.cleaned_data["autori"]:
                da = DokumentAutor(
                    dokument=dokument,
                    autor=autor,
                    poradi=i,
                )
                da.active_transaction = fedora_transaction
                da.save()
                i = i + 1
            dokument_extra = form_extra.save(commit=False)
            dokument_extra.active_transaction = fedora_transaction
            dokument_extra.save()
            instance_d.close_active_transaction_when_finished = True
            instance_d.save()
            form_d.save_m2m()
            invalidate_model(Dokument)
            invalidate_model(Akce)
            invalidate_model(ArcheologickyZaznam)
            invalidate_model(Historie)
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
            can_edit_datum_zverejneni=can_edit_datum_zverejneni,
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
    """
    Funkce pohledu pro editaci modelu 3D.
    """
    dokument: Dokument = get_object_or_404(Dokument, ident_cely=ident_cely, typ_dokumentu__id__in=MODEL_3D_DOKUMENT_TYPES)
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
            prefix="komponenta_",
        )
        geom = None
        x1 = None
        x2 = None
        try:
            x1 = float(form_coor.data.get("coordinate_wgs84_x1"))
            x2 = float(form_coor.data.get("coordinate_wgs84_x2"))
            if x1 > 0 and x2 > 0:
                geom = Point(x1, x2)
        except Exception:
            logger.debug("dokument.views.edit_model_3D.coord_error", extra={"x1": x1, "x2": x2})
        if form_d.is_valid() and form_extra.is_valid() and form_komponenta.is_valid():
            # save autors with order
            fedora_transaction = dokument.create_transaction(request.user)
            dokument_from_form = form_d.save(commit=False)
            dokument_from_form.active_transaction = fedora_transaction
            dokument_from_form.autori.clear()
            dokument_from_form.save()
            i = 1
            for autor in form_d.cleaned_data["autori"]:
                DokumentAutor(
                    dokument=dokument,
                    autor=autor,
                    poradi=i,
                ).save()
                i = i + 1
            if geom is not None:
                dokument.extra_data.geom = geom
            form_extra.save()
            komponenta = form_komponenta.save(commit=False)
            komponenta.active_transaction = fedora_transaction
            komponenta.save()
            form_komponenta.save_m2m()
            invalidate_model(KomponentaAktivita)
            invalidate_model(Historie)
            if (
                form_d.changed_data
                or form_extra.changed_data
                or form_komponenta.changed_data
            ):
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            dokument_from_form.close_active_transaction_when_finished = True
            dokument_from_form.save()
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
            prefix="komponenta_",
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
                    "object": dokument,
                    "coordinate_wgs84_x1": geom.split(" ")[0],
                    "coordinate_wgs84_x2": geom.split(" ")[1],
                    "global_map_can_edit": True,
                    "formDokument": form_d,
                    "formExtraData": form_extra,
                    "formKomponenta": form_komponenta,
                    "title": _("dokument.views.edit_model_3D.title"),
                    "header": _("dokument.views.edit_model_3D.header"),
                    "button": _("dokument.views.edit_model_3D.submitButton.text"),
                },
            )

    return render(
        request,
        "dokument/create_model_3D.html",
        {
            "object": dokument,
            "global_map_can_edit": True,
            "formDokument": form_d,
            "formExtraData": form_extra,
            "formKomponenta": form_komponenta,
            "title": _("dokument.views.edit_model_3D.title"),
            "header": _("dokument.views.edit_model_3D.header"),
            "button": _("dokument.views.edit_model_3D.submitButton.text"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def zapsat_do_akce(request, arch_z_ident_cely):
    """
    Funkce pohledu pro zapsání dokumentu do akce.
    """
    zaznam: ArcheologickyZaznam = get_object_or_404(ArcheologickyZaznam, ident_cely=arch_z_ident_cely)
    return zapsat(request, zaznam)

@login_required
def zapsat_do_projektu(request, proj_ident_cely):
    """
    Funkce pohledu pro zapsání dokumentu do projektu.
    """
    zaznam = get_object_or_404(Projekt, ident_cely=proj_ident_cely)
    if zaznam.typ_projektu.id != TYP_PROJEKTU_PRUZKUM_ID:
        logger.debug("Projekt neni typu pruzkumny")
        messages.add_message(request, messages.SUCCESS, PROJEKT_NENI_TYP_PRUZKUMNY)
        return redirect(zaznam.get_absolute_url())
    return zapsat(request, zaznam)


@login_required
@require_http_methods(["GET", "POST"])
def create_model_3D(request):
    """
    Funkce pohledu pro vytvoření modelu 3D.
    """
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
            prefix="komponenta_",
        )
        geom = None
        x1 = None
        x2 = None
        try:
            x1 = float(form_extra.data.get("coordinate_wgs84_x1"))
            x2 = float(form_extra.data.get("coordinate_wgs84_x2"))
            if x1 > 0 and x2 > 0:
                geom = Point(x1, x2)
        except Exception:
            logger.debug("dokument.views.create_model_3D.coord_error", extra={"x1": x1, "x2": x2})

        if form_d.is_valid() and form_extra.is_valid() and form_komponenta.is_valid():
            logger.debug("dokument.views.create_model_3D.forms_valid")
            dokument = form_d.save(commit=False)
            fedora_transaction = dokument.create_transaction(request.user)
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
                dc.active_transaction = fedora_transaction
                dc.save()
                i = 1
                for autor in form_d.cleaned_data["autori"]:
                    DokumentAutor(
                        dokument=dokument,
                        autor=autor,
                        poradi=i,
                    ).save()
                    i = i + 1
                form_d.save_m2m()
                extra_data = form_extra.save(commit=False)
                extra_data.dokument = dokument
                if geom is not None:
                    extra_data.geom = geom
                extra_data.save()

                komponenta = form_komponenta.save(commit=False)
                komponenta.active_transaction = fedora_transaction
                komponenta.komponenta_vazby = dc.komponenty
                komponenta.ident_cely = dokument.ident_cely + "-K001"
                komponenta.save()
                form_komponenta.save_m2m()

                dokument.close_active_transaction_when_finished = True
                dokument.save()

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
            prefix="komponenta_",
        )
    return render(
        request,
        "dokument/create_model_3D.html",
        {
            "global_map_can_edit": True,
            "formDokument": form_d,
            "formExtraData": form_extra,
            "formKomponenta": form_komponenta,
            "title": _("dokument.views.create_model_3D.title"),
            "header": _("dokument.views.create_model_3D.header"),
            "button": _("dokument.views.create_model_3D.submitButton.text"),
            "toolbar_label": _("dokument.views.create_model_3D.toolbar_label")
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def odeslat(request, ident_cely):
    """
    Funkce pohledu pro odeslání dokumentu cez modal.
    """
    dokument = get_object_or_404(Dokument, ident_cely=ident_cely)
    dokument: Dokument
    logger.debug("dokument.views.odeslat.start", extra={"ident_cely": ident_cely})
    if dokument.stav != D_STAV_ZAPSANY:
        logger.debug("dokument.views.odeslat.permission_denied", extra={"ident_cely": ident_cely})
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, dokument):
        logger.debug("dokument.views.odeslat.check_stav_changed", extra={"ident_cely": ident_cely})

        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    if request.method == "POST":
        fedora_transaction = dokument.create_transaction(request.user)
        old_ident = dokument.ident_cely
        # Nastav identifikator na permanentny
        returned_value = Dokument.set_permanent_identificator(dokument, request, messages, fedora_transaction)
        if isinstance(returned_value, JsonResponse):
            return returned_value
        dokument.set_odeslany(request.user, old_ident)
        messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_ODESLAN)
        logger.debug("dokument.views.odeslat.sucess")
        dokument.close_active_transaction_when_finished = True
        dokument.save()
        return JsonResponse({"redirect": get_detail_json_view(dokument.ident_cely)})
    else:
        warnings = dokument.check_pred_odeslanim()
        if warnings:
            logger.debug("dokument.views.odeslat.warnings", extra={"warnings": warnings, "ident_cely": ident_cely})
            request.session["temp_data"] = warnings
            messages.add_message(request, messages.ERROR, DOKUMENT_NELZE_ODESLAT)
            return JsonResponse(
                {"redirect": get_detail_json_view(ident_cely)}, status=403
            )
    form_check = CheckStavNotChangedForm(initial={"old_stav": dokument.stav})
    context = {
        "object": dokument,
        "title": _("dokument.views.odeslat.title"),
        "id_tag": "odeslat-dokument-form",
        "button": _("dokument.views.odeslat.submitButton.text"),
        "form_check": form_check,
    }
    logger.debug("dokument.views.odeslat.finish", extra={"ident_cely": ident_cely})
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def archivovat(request, ident_cely):
    """
    Funkce pohledu pro archivaci dokumentu cez modal.
    """
    dokument = get_object_or_404(Dokument, ident_cely=ident_cely)
    dokument: Dokument
    logger.debug("dokument.views.archivovat.start", extra={"ident_cely": ident_cely})
    if dokument.stav != D_STAV_ODESLANY:
        logger.debug("dokument.views.archivovat.permission_denied", extra={"ident_cely": ident_cely})
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, dokument):
        logger.debug("dokument.views.archivovat.check_stav_changed", extra={"ident_cely": ident_cely})
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    if request.method == "POST":
        fedora_transaction = dokument.create_transaction(request.user)
        dokument.active_transaction = fedora_transaction
        old_ident = dokument.ident_cely
        # Nastav identifikator na permanentny
        if ident_cely.startswith(IDENTIFIKATOR_DOCASNY_PREFIX):
            rada = get_dokument_rada(dokument.typ_dokumentu, dokument.material_originalu)
            try:
                dokument.set_permanent_ident_cely(dokument.ident_cely[2], rada)
            except MaximalIdentNumberError:
                messages.add_message(request, messages.SUCCESS, MAXIMUM_IDENT_DOSAZEN)
                fedora_transaction.rollback_transaction()
                dokument.close_active_transaction_when_finished = True
                return JsonResponse(
                    {"redirect": get_detail_json_view(ident_cely)}, status=403
                )
            else:
                dokument.save()
                logger.debug("dokument.views.archivovat.permanent", extra={"ident_cely": dokument.ident_cely})
        dokument.set_archivovany(request.user, old_ident)
        messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_ARCHIVOVAN)
        if dokument.rada == Heslar.objects.get(id=DOKUMENT_RADA_DATA_3D):
            Mailer.send_ek01(document=dokument)
        dokument.close_active_transaction_when_finished = True
        dokument.save()
        return JsonResponse({"redirect": get_detail_json_view(dokument.ident_cely)})
    else:
        warnings = dokument.check_pred_archivaci()
        logger.debug("dokument.views.archivovat.warnings", extra={"warnings": warnings})
        if warnings:
            request.session["temp_data"] = warnings
            messages.add_message(request, messages.ERROR, DOKUMENT_NELZE_ARCHIVOVAT)
            return JsonResponse(
                {"redirect": get_detail_json_view(ident_cely)}, status=403
            )
    form_check = CheckStavNotChangedForm(initial={"old_stav": dokument.stav})
    context = {
        "object": dokument,
        "title": _("dokument.views.archivovat.title"),
        "id_tag": "archivovat-dokument-form",
        "button": _("dokument.views.archivovat.submitButton.text"),
        "form_check": form_check,
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    """
    Funkce pohledu pro vrácení dokumentu cez modal.
    """
    dokument = get_object_or_404(Dokument, ident_cely=ident_cely)
    if dokument.stav != D_STAV_ODESLANY and dokument.stav != D_STAV_ARCHIVOVANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    if check_stav_changed(request, dokument):
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    if request.method == "POST":
        form = VratitForm(request.POST)
        if form.is_valid():
            dokument.create_transaction(request.user)
            duvod = form.cleaned_data["reason"]
            if dokument.stav == D_STAV_ODESLANY:
                Mailer.send_ek02(document=dokument, reason=duvod)
            dokument.set_vraceny(request.user, dokument.stav - 1, duvod)
            messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_VRACEN)
            dokument.close_active_transaction_when_finished = True
            dokument.save()
            return JsonResponse({"redirect": get_detail_json_view(ident_cely)})
        else:
            logger.debug("dokument.views.vratit.not_valid", extra={"errors": form.errors})
            return JsonResponse(
                {"redirect": get_detail_json_view(ident_cely)}, status=403
            )
    else:
        form = VratitForm(initial={"old_stav": dokument.stav})
    context = {
        "object": dokument,
        "form": form,
        "title": _("dokument.views.vratit.title"),
        "id_tag": "vratit-dokument-form",
        "button": _("dokument.views.vratit.submitButton.text"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    """
    Funkce pohledu pro smazání dokumentu cez modal.
    """
    dokument: Dokument = get_object_or_404(Dokument, ident_cely=ident_cely)
    dokument.deleted_by_user = request.user
    if check_stav_changed(request, dokument):
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    if request.method == "POST":
        fedora_transaction = dokument.create_transaction(request.user)
        dokument.save_record_deletion_record(fedora_transaction, request.user)
        for item in dokument.casti.all():
            if hasattr(item, "neident_akce"):
                neident_akce = item.neident_akce
                neident_akce: NeidentAkce
                neident_akce.suppress_signal = True
                neident_akce.delete()
            item: DokumentCast
            item.suppress_dokument_signal = True
            item.active_transaction = fedora_transaction
            item.delete()
        resp1 = dokument.delete()
        if resp1:
            logger.debug("dokument.views.smazat.deleted", extra={"resp1": resp1})
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            fedora_transaction.mark_transaction_as_closed()
            if "3D" in ident_cely:
                return JsonResponse({"redirect": reverse("dokument:index-model-3D")})
            else:
                return JsonResponse({"redirect": reverse("dokument:index")})
        else:
            logger.warning("dokument.views.smazat.not_deleted", extra={"ident_cely": ident_cely})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            fedora_transaction.rollback_transaction()
            return JsonResponse(
                {"redirect": get_detail_json_view(ident_cely)}, status=403
            )
    else:
        form_check = CheckStavNotChangedForm(initial={"old_stav": dokument.stav})
        context = {
            "object": dokument,
            "title": _("dokument.views.smazat.title"),
            "id_tag": "smazat-dokument-form",
            "button": _("dokument.views.smazat.submitButton.text"),
            "form_check": form_check,
        }
        return render(request, "core/transakce_modal.html", context)


class DokumentAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView,PermissionFilterMixin):
    """
    Třída pohledu pro autocomplete dokumentů.
    """
    typ_zmeny_lookup = ZAPSANI_DOK

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Dokument.objects.none()
        qs = Dokument.objects.exclude(typ_dokumentu__id__in=MODEL_3D_DOKUMENT_TYPES)
        if self.q:
            qs = qs.filter(ident_cely__icontains=self.q)
        return self.check_filter_permission(qs)


def get_hierarchie_dokument_typ():
    """
    Funkce pro získaní hierarchie pro heslař.
    """
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


def get_history_dates(historie_vazby, request_user):
    """
    Funkce pro získaní historických datumu.
    """
    request_user: User
    anonymized = not request_user.hlavni_role.pk in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)
    historie = {
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_DOK, anonymized),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_DOK, anonymized),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_DOK, anonymized),
    }
    return historie


def get_detail_template_shows(dokument,user):
    """
    Funkce pro získaní kontextu pro zobrazování možností na stránkách.
    """
    if "3D" in dokument.ident_cely:
        show_edit = check_permissions(p.actionChoices.model_edit, user, dokument.ident_cely)
        soubor_stahnout_dokument = check_permissions(p.actionChoices.soubor_stahnout_model3d, user, dokument.ident_cely)
        soubor_nahled = check_permissions(p.actionChoices.soubor_nahled_model3d, user, dokument.ident_cely)
        soubor_smazat = check_permissions(p.actionChoices.soubor_smazat_model3d, user, dokument.ident_cely)
        soubor_nahradit = False
    else:
        show_edit = check_permissions(p.actionChoices.dok_edit, user, dokument.ident_cely)
        soubor_stahnout_dokument = check_permissions(p.actionChoices.soubor_stahnout_dokument, user, dokument.ident_cely)
        soubor_nahled = check_permissions(p.actionChoices.soubor_nahled_dokument, user, dokument.ident_cely)
        soubor_smazat = check_permissions(p.actionChoices.soubor_smazat_dokument, user, dokument.ident_cely)
        soubor_nahradit = check_permissions(p.actionChoices.soubor_nahradit_dokument, user, dokument.ident_cely)
    show_arch_links = dokument.stav == D_STAV_ARCHIVOVANY
    show_tvary = True if dokument.rada.zkratka in ["LD", "LN", "DL"] else False
    show = {
        "vratit_link": check_permissions(p.actionChoices.dok_vratit, user, dokument.ident_cely),
        "odeslat_link": check_permissions(p.actionChoices.dok_odeslat, user, dokument.ident_cely),
        "archivovat_link": check_permissions(p.actionChoices.dok_archivovat, user, dokument.ident_cely),
        "editovat": show_edit,
        "smazat": check_permissions(p.actionChoices.dok_smazat, user, dokument.ident_cely),
        "arch_links": show_arch_links,
        "tvary": show_tvary,
        "tvary_edit": show_tvary and check_permissions(p.actionChoices.dok_tvary_edit, user, dokument.ident_cely),
        "tvary_smazat": show_tvary and check_permissions(p.actionChoices.dok_tvary_smazat, user, dokument.ident_cely),
        "zapsat_cast": check_permissions(p.actionChoices.dok_cast_zapsat, user, dokument.ident_cely),
        "nalez_smazat": check_permissions(p.actionChoices.nalez_smazat_dokument, user, dokument.ident_cely),
        "stahnout_metadata": check_permissions(p.actionChoices.stahnout_metadata, user, dokument.ident_cely),
        "soubor_stahnout": soubor_stahnout_dokument,
        "soubor_nahled": soubor_nahled,
        "soubor_smazat": soubor_smazat,
        "soubor_nahradit": soubor_nahradit,
    }
    return show

@login_required
def zapsat(request, zaznam=None):
    """
    Funkce pohledu pro zapsání dokumentu.
    """
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
            dokument: Dokument
            fedora_transaction = dokument.create_transaction(request.user)
            dokument.rada = get_dokument_rada(
                dokument.typ_dokumentu, dokument.material_originalu
            )
            if isinstance(zaznam, Projekt):
                dokument.datum_zverejneni = datetime.now().date() + timedelta(days=365 * 100)
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
                fedora_transaction.rollback_transaction()
            else:
                if FedoraRepositoryConnector.check_container_deleted_or_not_exists(dokument.ident_cely, "dokument"):
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
                            dc = DokumentCast(
                                dokument=dokument,
                                ident_cely=get_cast_dokumentu_ident(dokument),
                                archeologicky_zaznam=zaznam,
                            )
                            dc.active_transaction = fedora_transaction
                            dc.save()
                        else:
                            dc = DokumentCast(
                                dokument=dokument,
                                ident_cely=get_cast_dokumentu_ident(dokument),
                                projekt=zaznam,
                            )
                            dc.active_transaction = fedora_transaction
                            dc.save()

                    form_d.save_m2m()
                    dokument.close_active_transaction_when_finished = True
                    dokument.save()

                    messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
                    return redirect("dokument:detail", ident_cely=dokument.ident_cely)
                else:
                    logger.debug("dokument.views.zapsat.check_container_deleted_or_not_exists.invalid",
                                 extra={"ident_cely": dokument.ident_cely})
        else:
            logger.debug("dokument.views.zapsat.not_valid", extra={"erros": form_d.errors})

    else:
        form_d = EditDokumentForm(
            create=True,
            required=required_fields,
            required_next=required_fields_next,
            region_not_required=True if zaznam else None,
        )
    back_ident = None
    back_model = None
    if zaznam:
        if isinstance(zaznam, ArcheologickyZaznam):
            back_ident = zaznam.ident_cely
            back_model = "ArcheologickyZaznam"
        elif isinstance(zaznam, Projekt):
            back_ident = zaznam.ident_cely
            back_model = "Projekt"
    return render(
        request,
        "dokument/create.html",
        {
            "back_ident": back_ident,
            "back_model": back_model,
            "zaznam": zaznam,
            "TYP_ZAZNAMU_LOKALITA": ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA,
            "TYP_ZAZNAMU_AKCE": ArcheologickyZaznam.TYP_ZAZNAMU_AKCE,
            "formDokument": form_d,
            "hierarchie": get_hierarchie_dokument_typ(),
            "samostatny": True if not zaznam else False,
            "toolbar_label": _("dokument.views.zapsat.dokument.toolbar_label")
        },
    )


def odpojit(request, ident_doku, ident_zaznamu, zaznam):
    """
    Funkce pohledu pro odpojení dokumentu cez modal.
    """
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
        fedora_transaction = dokument_cast[0].create_transaction(request.user)
        resp = dokument_cast[0].delete()
        logger.debug("dokument.views.odpojit.deleted", extra={"resp": resp})
        if remove_orphan:
            orphan_dokument.active_transaction = fedora_transaction
            orphan_dokument.record_deletion()
            orphan_dokument.delete()
            logger.debug("dokument.views.odpojit.deleted")
        fedora_transaction.mark_transaction_as_closed()
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
                "title": _("dokument.views.odpojit.title"),
                "id_tag": "odpojit-dokument-form",
                "button": _("dokument.views.odpojit.submitButton.text"),
            },
        )


def pripojit(request, ident_zaznam, proj_ident_cely, typ):
    """
    Funkce pohledu pro pripojení dokumentu cez modal.
    """
    zaznam = get_object_or_404(typ, ident_cely=ident_zaznam)
    if isinstance(zaznam, ArcheologickyZaznam):
        casti_zaznamu = DokumentCast.objects.filter(
            archeologicky_zaznam__ident_cely=ident_zaznam
        )
        debug_name = "akci "
        redirect_name = zaznam.get_absolute_url()
        context = {
            "object": zaznam,
            "title": _("dokument.views.pripojit.pripojitDoAkce.title"),
            "id_tag": "pripojit-dokument-form",
            "button": _("dokument.views.pripojit.pripojitDoAkce.submitButton.text"),
        }
    else:
        casti_zaznamu = DokumentCast.objects.filter(projekt__ident_cely=ident_zaznam)
        debug_name = "projektu "
        redirect_name = reverse("projekt:detail", kwargs={"ident_cely": ident_zaznam})
        context = {
            "object": zaznam,
            "title": _("dokument.views.pripojit.pripojitDoProjektu.title"),
            "id_tag": "pripojit-dokument-form",
            "button": _("dokument.views.pripojit.pripojitDoProjektu.submitButton.text"),
        }
    if request.method == "POST":
        dokument_ids = request.POST.getlist("dokument")

        for dokument_id in dokument_ids:
            dokument = get_object_or_404(Dokument, id=dokument_id)
            fedora_transaction = zaznam.create_transaction(request.user)
            dokument.active_transaction = fedora_transaction
            relace = casti_zaznamu.filter(dokument__id=dokument_id)
            if not relace.exists():
                dc_ident = get_cast_dokumentu_ident(dokument)
                if isinstance(zaznam, ArcheologickyZaznam):
                    dc = DokumentCast(
                        archeologicky_zaznam=zaznam,
                        dokument=dokument,
                        ident_cely=dc_ident,
                    )
                    dc.active_transaction = fedora_transaction
                    dc.save()
                else:
                    dc = DokumentCast(
                        projekt=zaznam, dokument=dokument, ident_cely=dc_ident
                    )
                    dc.active_transaction = fedora_transaction
                    dc.save()
                dokument.close_active_transaction_when_finished = True
                dokument.save()
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
    """
    Funkce pohledu pro získaní řádku dokumentu pro vykreslení v modalu.
    """
    context = {"d": Dokument.objects.get(id=request.GET.get("id", ""))}
    return HttpResponse(render_to_string("dokument/dokument_table_row.html", context))


def get_detail_view(ident_cely):
    """
    Funkce pohledu pro redirect podle identu na model 3D nebo dokument detail.
    """
    if "3D" in ident_cely:
        return redirect("dokument:detail-model-3D", ident_cely=ident_cely)
    else:
        return redirect("dokument:detail", ident_cely=ident_cely)


def get_detail_json_view(ident_cely):
    """
    Funkce pohledu pro vrácení url pro redirect podle identu na model 3D nebo dokument detail.
    """
    if "3D" in ident_cely:
        return reverse("dokument:detail-model-3D", kwargs={"ident_cely": ident_cely})
    else:
        return reverse("dokument:detail", kwargs={"ident_cely": ident_cely})


def get_required_fields_model3D(zaznam=None, next=0):
    """
    Funkce pro získaní dictionary povinných polí podle stavu modelu 3D.

    Args:     
        zaznam (Dokument): model Dokument pro který se dané pole počítají.

        next (int): pokud je poskytnuto číslo tak se jedná o povinné pole pro příští stav.

    Returns:
        required_fields: list polí.
    """
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
    """
    Funkce pro získaní dictionary povinných polí podle stavu dokumentu.

    Args:     
        zaznam (Dokument): model Dokument pro který se dané pole počítají.

        next (int): pokud je poskytnuto číslo tak se jedná o povinné pole pro příští stav.

    Returns:
        required_fields: list polí.
    """
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
            "pristupnost",
        ]
    if stav > D_STAV_ZAPSANY - next:
        required_fields += [
            "ulozeni_originalu",
            "popis",
            "jazyky",
        ]
    return required_fields


def get_komponenta_form_detail(komponenta, show, old_nalez_post, komp_ident_cely):
    """
    Funkce pro získaní formsetu predmetu a objektu pro komponentu.
    """
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
            heslar_list(HESLAR_PREDMET_SPECIFIKACE),
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
    """
    Funkce která vrací dvou stupňový heslař pro období.
    """
    return heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)


def get_areal_choices():
    """
    Funkce která vrací dvou stupňový heslař pro areál.
    """
    return heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)

@login_required
@require_http_methods(["POST"])
def post_ajax_get_3d_limit(request):
    """
    Funkce pohledu pro získaní 3D.
    """
    body = json.loads(request.body.decode("utf-8"))
    pians = get_3d_from_envelope(
        body["southEast"]["lng"],
        body["northWest"]["lat"],
        body["northWest"]["lng"],
        body["southEast"]["lat"],
        request,
    )
    back = []
    for pian in pians:
        logger.debug(pian)
        back.append(
            {
                "id": pian["dokument__id"],
                "ident_cely": pian["dokument__ident_cely"],
                "geom": pian["geom"].wkt.replace(", ", ",")
            }
        )
    if len(pians) > 0:
        return JsonResponse({"points": back, "algorithm": "detail"}, status=200)
    else:
        return JsonResponse({"points": [], "algorithm": "detail"}, status=200)
