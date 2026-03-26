import logging
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import simplejson as json
from arch_z.models import Akce, ArcheologickyZaznam
from cacheops import invalidate_model
from core.constants import (
    ARCHIVACE_DOK,
    AZ_STAV_ARCHIVOVANY,
    D_STAV_ARCHIVOVANY,
    D_STAV_ODESLANY,
    D_STAV_ZAPSANY,
    DOKUMENT_CAST_RELATION_TYPE,
    DOKUMENTACNI_JEDNOTKA_RELATION_TYPE,
    IDENTIFIKATOR_DOCASNY_PREFIX,
    ODESLANI_DOK,
    ROLE_ADMIN_ID,
    ROLE_ARCHIVAR_ID,
    ZAPSANI_DOK,
)
from core.coordTransform import convertToJTSK
from core.exceptions import MaximalIdentNumberError, UnexpectedDataRelations
from core.forms import CheckStavNotChangedForm, VratitForm, VratitFormDokument
from core.ident_cely import get_cast_dokumentu_ident, get_dokument_rada, get_temp_dokument_ident
from core.message_constants import (
    DOKUMENT_AZ_USPESNE_PRIPOJEN,
    DOKUMENT_CAST_USPESNE_ODPOJEN,
    DOKUMENT_CAST_USPESNE_SMAZANA,
    DOKUMENT_JIZ_BYL_PRIPOJEN,
    DOKUMENT_NEIDENT_AKCE_USPESNE_SMAZANA,
    DOKUMENT_NELZE_ARCHIVOVAT,
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
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from core.models import Permissions as p
from core.models import Soubor, check_permissions
from core.repository_connector import FedoraError, FedoraRepositoryConnector, FedoraTransaction
from core.utils import get_3d_from_envelope
from core.views import PermissionFilterMixin, SearchListView, check_stav_changed
from dal import autocomplete
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import OuterRef, Prefetch, Q, Subquery
from django.forms import inlineformset_factory
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from dokument.filters import DokumentFilter, Model3DFilter
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
from dokument.models import Dokument, DokumentAutor, DokumentCast, DokumentExtraData, Let, Tvar
from dokument.tables import DokumentTable, Model3DTable
from ez.forms import PripojitArchZaznamForm
from fedora_management.decorators import handle_fedora_error
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
    PRIMARNE_DIGITALNI,
    PRISTUPNOST_ANONYM_ID,
    TYP_PROJEKTU_PRUZKUM_ID,
)
from heslar.models import Heslar, HeslarHierarchie
from heslar.views import heslar_12, heslar_list
from komponenta.forms import CreateKomponentaForm
from komponenta.models import Komponenta, KomponentaVazby
from nalez.forms import NalezFormSetHelper, create_nalez_objekt_form, create_nalez_predmet_form
from nalez.models import NalezObjekt, NalezPredmet
from neidentakce.forms import NeidentAkceForm
from neidentakce.models import NeidentAkce
from pid.exceptions import DoiWriteError
from projekt.forms import PripojitProjektForm
from projekt.models import Projekt
from services.mailer import Mailer
from uzivatel.models import Organizace, Osoba, User

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def index_model_3D(request):
    """
    Funkce pohledu pro zobrazení domovské stránky modelu 3D s navigačními možnostmi.

    :param request: Parametr ``request`` se předává do volání ``render()``, vstupuje do návratové hodnoty.

        :return: Vrací výsledek volání ``render()``.
    """
    return render(request, "dokument/index_model_3D.html")


@login_required
@require_http_methods(["GET"])
def detail_model_3D(request, ident_cely):
    """
    Třida pohledu pro zobrazení detailu modelu 3D.

    :param request: Parametr ``request`` se předává do volání ``get_detail_template_shows()``, ``get_history_dates()``, pracuje se s atributy ``session``, ``user``, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``.

        :return: Vrací výsledek volání ``render()``.
        :raises UnexpectedDataRelations: Vyvolá se při splnění podmínky ``casti.count() != 1``; nebo při splnění podmínky ``komponenty.count() != 1``.
    """
    context = {"warnings": request.session.pop("temp_data", None)}
    old_nalez_post = request.session.pop("_old_nalez_post", None)
    request.session.pop("komp_ident_cely", None)
    dokument = get_object_or_404(
        Dokument.objects.select_related(
            "soubory",
            "organizace",
            "typ_dokumentu",
        ),
        ident_cely=ident_cely,
        typ_dokumentu__id__in=MODEL_3D_DOKUMENT_TYPES,
    )
    casti = dokument.casti.all()
    if casti.count() != 1:
        logger.warning("dokument.views.detail_model_3D.casti_count_error", extra={"count": casti.count()})
        raise UnexpectedDataRelations()
    komponenty = casti[0].komponenty.komponenty.all()
    if komponenty.count() != 1:
        logger.warning("dokument.views.detail_model_3D.komponenty_count_error", extra={"count": komponenty.count()})
        raise UnexpectedDataRelations()
    show = get_detail_template_shows(dokument, request.user)
    obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
    areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
    druh_objekt_choices = heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT)
    druh_predmet_choices = heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT)
    specifikace_objekt_choices = heslar_12(HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT)
    specifikce_predmetu_choices = heslar_list(HESLAR_PREDMET_SPECIFIKACE)
    NalezObjektFormset = inlineformset_factory(
        Komponenta,
        NalezObjekt,
        form=create_nalez_objekt_form(
            druh_objekt_choices,
            specifikace_objekt_choices,
            not_readonly=show["editovat"],
        ),
        extra=3 if show["editovat"] else 0,
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
        extra=3 if show["editovat"] else 0,
        can_delete=False,
    )
    context["dokument"] = dokument
    context["komponenta"] = komponenty[0]
    context["nalez_concurrent_changes"] = request.session.pop(
        f"komp_concurrent_changes_{komponenty[0].ident_cely}", None
    )
    context["formDokument"] = CreateModelDokumentForm(instance=dokument, readonly=True)
    if dokument.extra_data.geom:
        geom = str(dokument.extra_data.geom).split("(")[1].replace(", ", ",").replace(")", "")
        context["coordinate_wgs84_x1"] = geom.split(" ")[0]
        context["coordinate_wgs84_x2"] = geom.split(" ")[1]
    context["formExtraData"] = CreateModelExtraDataForm(instance=dokument.extra_data, readonly=True)
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
        context["soubory"] = sorted(dokument.soubory.soubory.all(), key=lambda x: (x.nazev.replace(".", "0"), x.nazev))
    else:
        context["soubory"] = None
    return render(request, "dokument/detail_model_3D.html", context)


class Model3DListView(SearchListView):
    """Třida pohledu pro zobrazení listu/tabulky s modelama 3D."""

    table_class = Model3DTable
    model = Dokument
    filterset_class = Model3DFilter
    export_name = "export_modely_"
    app = "knihovna_3d"
    toolbar = "toolbar_dokument.html"
    redis_snapshot_prefix = "dokument"
    redis_value_list_field = "ident_cely"
    typ_zmeny_lookup = ZAPSANI_DOK
    vypis_app = "model"

    def init_translations(self):
        """Provádí operaci init translations."""
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
        """
        Provádí operaci rename field for ordering.

        :param field: Parametr ``field`` předává se do volání ``get()``, pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``get()``.
        """
        field = field.replace("-", "")
        return {
            "typ_dokumentu": "typ_dokumentu__razeni",
            "autori": "autori_snapshot",
            "extra_data__format": "extra_data__format__razeni",
            "extra_data__zeme": "extra_data__zeme__razeni",
        }.get(field, field)

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["is_3d"] = True
        return context

    def get_queryset(self):
        """Vrací queryset. v aplikaci.

        :return: Vrací výsledek volání ``check_filter_permission()``.
        """
        sort_params = self._get_sort_params()
        sort_params = [self.rename_field_for_ordering(x) for x in sort_params]
        qs = super().get_queryset()
        qs = qs.order_by(*sort_params).distinct()
        qs = qs.filter(ident_cely__contains="3D")
        qs = qs.select_related("typ_dokumentu", "extra_data", "organizace", "extra_data__format").prefetch_related(
            Prefetch(
                "autori",
                queryset=Osoba.objects.all().order_by("dokumentautor__poradi"),
                to_attr="ordered_autors",
            ),
            "extra_data__zeme",
            "soubory__soubory",
        )

        return self.check_filter_permission(qs)


class DokumentIndexView(LoginRequiredMixin, TemplateView):
    """Třida pohledu pro zobrazení domovské stránky dokumentů s navigačními možnostmi."""

    template_name = "dokument/index_dokument.html"


class DokumentListView(SearchListView):
    """Třida pohledu pro zobrazení listu/tabulky s dokumentama."""

    table_class = DokumentTable
    model = Dokument
    filterset_class = DokumentFilter
    export_name = "export_dokumenty_"
    app = "dokument"
    toolbar = "toolbar_dokument.html"
    redis_snapshot_prefix = "dokument"
    redis_value_list_field = "ident_cely"
    typ_zmeny_lookup = ZAPSANI_DOK
    vypis_app = "dokument"

    def init_translations(self):
        """Provádí operaci init translations."""
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
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["is_3d"] = False
        return context

    @staticmethod
    def rename_field_for_ordering(field: str):
        """
        Provádí operaci rename field for ordering.

        :param field: Parametr ``field`` předává se do volání ``get()``, pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``get()``.
        """
        field = field.replace("-", "")
        return {
            "typ_dokumentu": "typ_dokumentu__razeni",
            "autori": "autori_snapshot",
            "pristupnost": "pristupnost__razeni",
            "rada": "rada__razeni",
            "material_originalu": "material_originalu__razeni",
            "extra_data__format": "extra_data__format__razeni",
            "ulozeni_originalu": "ulozeni_originalu__razeni",
            "licence": "licence__razeni",
            "extra_data__zachovalost": "extra_data__zachovalost__razeni",
            "extra_data__nahrada": "extra_data__nahrada__razeni",
            "extra_data__zeme": "extra_data__zeme__razeni",
            "extra_data__udalost_typ": "extra_data__udalost_typ__razeni",
            "osoby": "osoby_snapshot",
            "let": "let__ident_cely",
        }.get(field, field)

    def get_queryset(self):
        """Vrací queryset. v aplikaci.

        :return: Vrací výsledek volání ``check_filter_permission()``.
        """
        sort_params = self._get_sort_params()
        sort_params = [self.rename_field_for_ordering(x) for x in sort_params]
        qs = super().get_queryset()
        qs = qs.order_by(*sort_params).distinct()
        subqry = Subquery(Soubor.objects.filter(vazba=OuterRef("vazba")).values_list("id", flat=True)[:1])
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
            ),
            "typ_dokumentu",
            "let",
            "rada",
            "pristupnost",
        )
        return self.check_filter_permission(qs)


class RelatedContext(LoginRequiredMixin, TemplateView):
    """Třida, která se dedí a která obsahuje metody pro získaní relací dokumentů."""

    def get_cast(self, context, cast, **kwargs):
        """
        Metoda pro získaní informací ohlědně části dokumentu.

        :param context: Parametr ``context`` slouží jako vstup pro logiku funkce ``get_cast``.
        :param cast: Typ nebo hodnota použitá při převodu datového typu.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_cast``.
        """
        context["cast"] = cast
        cast_form = DokumentCastForm(
            instance=cast,
            readonly=True,
            prefix="cast",
        )
        context["cast_form"] = cast_form
        neident_akce = NeidentAkce.objects.filter(dokument_cast=cast)
        if neident_akce.exists():
            context["neident_akce_form"] = NeidentAkceForm(instance=neident_akce[0], prefix="neident", readonly=True)
        context["show_edit_cast"] = check_permissions(
            p.actionChoices.dok_cast_edit, self.request.user, cast.dokument.ident_cely
        )
        context["show_smazat_cast"] = check_permissions(
            p.actionChoices.dok_cast_smazat, self.request.user, cast.dokument.ident_cely
        )
        context["show_zapsat_komponentu"] = check_permissions(
            p.actionChoices.dok_komponenta_zapsat, self.request.user, cast.dokument.ident_cely
        )
        context["show_neident_akce_edit"] = check_permissions(
            p.actionChoices.neident_akce_edit, self.request.user, cast.dokument.ident_cely
        )
        context["show_neident_akce_smazat"] = check_permissions(
            p.actionChoices.neident_akce_smazat, self.request.user, cast.dokument.ident_cely
        )
        context["show_odpojit"] = False
        context["show_pripojit_proj"] = check_permissions(
            p.actionChoices.dok_pripojit_proj, self.request.user, cast.dokument.ident_cely
        )
        context["show_pripojit_archz"] = check_permissions(
            p.actionChoices.dok_pripojit_archz, self.request.user, cast.dokument.ident_cely
        )
        if cast.projekt or cast.archeologicky_zaznam:
            context["show_odpojit"] = check_permissions(
                p.actionChoices.dok_cast_odpojit, self.request.user, cast.dokument.ident_cely
            )
            context["show_pripojit_proj"] = False
            context["show_pripojit_archz"] = False

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní contextu dokumentu pro template.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
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
        show = get_detail_template_shows(dokument, self.request.user)
        context["tvar_concurrent_changes"] = self.request.session.pop(
            f"tvar_concurrent_changes_{dokument.ident_cely}", None
        )
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
            context["soubory"] = sorted(
                dokument.soubory.soubory.all(), key=lambda x: (x.nazev.replace(".", "0"), x.nazev)
            )
        else:
            context["soubory"] = None

        context["casti"] = dokument.casti.all()
        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Metoda pro render response, kvúli správnemu zobrazení zpět možnosti.

        :param context: Parametr ``context`` se předává do volání ``render_to_response()``, ovlivňuje větvení podmínek.
        :param response_kwargs: Dodatečné argumenty předané voláním.

            :return: Vrací proměnná ``response``.
        """
        response = super().render_to_response(context, **response_kwargs)
        referer = urlparse(self.request.META.get("HTTP_REFERER", False)).path
        referer_next = urlparse(self.request.META.get("HTTP_REFERER", False)).query
        if referer:
            ident_referer = referer.split("/")[-1]
            if context["dokument"].ident_cely == ident_referer:
                pass
            elif "arch-z/akce/detail/" in referer or "/projekt/detail/" or "arch-z/lokalita/detail/" in referer:
                found = False
                for cast in context["casti"]:
                    if cast.archeologicky_zaznam:
                        if cast.archeologicky_zaznam.ident_cely == ident_referer:
                            logger.debug("dokument.views.RelatedContext.render_to_response.back_option_for_akce_found")
                            response.set_cookie(
                                "zpet",
                                cast.archeologicky_zaznam.get_absolute_url(),
                                max_age=1000,
                                secure=True,
                                samesite="Strict",
                            )
                            found = True
                            break
                    if cast.projekt:
                        if cast.projekt.ident_cely == ident_referer:
                            logger.debug(
                                "dokument.views.RelatedContext.render_to_response." "back_option_for_projekt_found"
                            )
                            response.set_cookie(
                                "zpet",
                                reverse("projekt:detail", args=(ident_referer,)),
                                max_age=1000,
                                secure=True,
                                samesite="Strict",
                            )
                            found = True
                            break
                if found is False:
                    logger.debug("dokument.views.RelatedContext.render_to_response.back_option_not_found")
                    response.delete_cookie("zpet")
            elif "soubor/nahrat" in referer and context["dokument"].ident_cely in referer_next:
                logger.debug("dokument.views.RelatedContext.render_to_response.back_option_not_changed")
            else:
                logger.debug("dokument.views.RelatedContext.render_to_response.no_back_option")
                response.delete_cookie("zpet")
        else:
            logger.debug("dokument.views.RelatedContext.render_to_response.no_referer")
            response.delete_cookie("zpet")
        return response


class DokumentDetailView(RelatedContext):
    """Třida pohledu pro zobrazení detailu dokumentu."""

    template_name = "dokument/dok/detail.html"

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``get()``.
        """
        return super().get(request, *args, **kwargs)


class DokumentCastDetailView(RelatedContext):
    """Třida pohledu pro zobrazení detailu části dokumentu."""

    template_name = "dokument/dok/detail_cast_dokumentu.html"

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """
               Provádí operaci dispatch.

               :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
               :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
               :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.
        """
        cast = get_object_or_404(DokumentCast, ident_cely=self.kwargs["cast_ident_cely"])
        if cast.dokument.ident_cely != self.kwargs["ident_cely"]:
            logger.error("Dokument - Dokument cast wrong relation")
            messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
            if url_has_allowed_host_and_scheme(
                request.GET.get("next", "core:home"), allowed_hosts=settings.ALLOWED_HOSTS
            ):
                safe_redirect = request.GET.get("next", "core:home")
            else:
                safe_redirect = "/"
            return redirect(safe_redirect)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        cast = get_object_or_404(
            DokumentCast,
            ident_cely=self.kwargs["cast_ident_cely"],
        )
        self.get_cast(context, cast)
        context["active_dc_ident"] = cast.ident_cely
        return context


class DokumentCastEditView(LoginRequiredMixin, UpdateView):
    """Třida pohledu pro editaci části dokumentu pomocí modalu."""

    model = DokumentCast
    template_name = "core/transakce_modal.html"
    id_tag = "edit-cast-form"
    form_class = DokumentCastForm
    slug_field = "ident_cely"
    active_transaction = None

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
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
        """Vrací success url.

        :return: Vrací výsledek volání ``get_absolute_url()``.
        """
        context = self.get_context_data()
        dc = context["object"]
        return dc.get_absolute_url()

    def get_object(self, queryset=None):
        """
        Vrací object. v aplikaci.

        :param queryset: Parametr ``queryset`` předává se do volání ``get_object()``.

            :return: Vrací atribut objektu.
        """
        if hasattr(self, "object"):
            self.object = self.object
        else:
            self.object = super().get_object(queryset)
        if self.active_transaction and not self.object.active_transaction:
            self.object.active_transaction = self.active_transaction
        return self.object

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``create_transaction()``, ``post()``, pracuje se s atributy ``user``.
        :param args: Parametr ``args`` se předává do volání ``post()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``post()``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        self.active_transaction = self.get_object().create_transaction(request.user)
        self.active_transaction.redirect_on_error = False
        super().post(request, *args, **kwargs)
        self.active_transaction.mark_transaction_as_closed()
        return JsonResponse({"redirect": self.get_success_url()})

    def form_invalid(self, form):
        """
        Provádí operaci form invalid.

        :param form: Parametr ``form`` se předává do volání ``debug()``, ``form_invalid()``, pracuje se s atributy ``errors``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``form_invalid()``.
        """
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        logger.debug("dokument.views.DokumentCastEditView.form_invalid", extra={"error": form.errors})
        return super().form_invalid(form)


class KomponentaDokumentDetailView(RelatedContext):
    """Třida pohledu pro zobrazení detailu komponenty části dokumentu."""

    template_name = "dokument/dok/detail_komponenta.html"

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """
               Provádí operaci dispatch.

               :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
               :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
               :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.
        """
        komponenta = get_object_or_404(Komponenta, ident_cely=self.kwargs["komp_ident_cely"])
        if komponenta.komponenta_vazby.casti_dokumentu.dokument.ident_cely != self.kwargs["ident_cely"]:
            logger.error("Dokument - Komponenta wrong relation")
            messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
            if url_has_allowed_host_and_scheme(
                request.GET.get("next", "core:home"), allowed_hosts=settings.ALLOWED_HOSTS
            ):
                safe_redirect = request.GET.get("next", "core:home")
            else:
                safe_redirect = "/"
            return redirect(safe_redirect)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
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
            komponenta, context["show"], old_nalez_post, komp_ident_cely, session=self.request.session
        )
        context["active_komp_ident"] = komponenta.ident_cely
        context["show"]["komponenta_smazat"] = check_permissions(
            p.actionChoices.komponenta_smazat_dok, self.request.user, context["dokument"].ident_cely
        )
        return context


class KomponentaDokumentCreateView(RelatedContext):
    """Třida pohledu pro vytvoření komponenty části dokumentu."""

    template_name = "dokument/dok/create_komponenta.html"

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """
               Provádí operaci dispatch.

               :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
               :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
               :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.
        """
        cast = get_object_or_404(DokumentCast, ident_cely=self.kwargs["cast_ident_cely"])
        if cast.dokument.ident_cely != self.kwargs["ident_cely"]:
            logger.error("Dokument - Dokument cast wrong relation")
            messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
            if url_has_allowed_host_and_scheme(
                request.GET.get("next", "core:home"), allowed_hosts=settings.ALLOWED_HOSTS
            ):
                safe_redirect = request.GET.get("next", "core:home")
            else:
                safe_redirect = "/"
            return redirect(safe_redirect)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        cast = get_object_or_404(
            DokumentCast,
            ident_cely=self.kwargs["cast_ident_cely"],
        )
        self.get_cast(context, cast)
        context["komponenta_form_create"] = CreateKomponentaForm(get_obdobi_choices(), get_areal_choices())
        return context

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``get()``.
        """
        return super().get(request, *args, **kwargs)


class TvarEditView(LoginRequiredMixin, View):
    """Třida pohledu pro uložení zmeny tvaru z formuláře."""

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``TvarFormset()``, ``add_message()``, pracuje se s atributy ``POST``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``redirect()``.
        """
        dokument: Dokument = get_object_or_404(
            Dokument.objects.exclude(typ_dokumentu__id__in=MODEL_3D_DOKUMENT_TYPES),
            ident_cely=self.kwargs["ident_cely"],
        )
        TvarFormset = inlineformset_factory(
            Dokument,
            Tvar,
            form=create_tvar_form(),
            extra=1,
        )
        formset = TvarFormset(request.POST, instance=dokument, prefix=dokument.ident_cely + "_d")
        if formset.is_valid():
            conflicting_fields = []
            for fs_form in formset.forms:
                conflicting_fields += fs_form.get_conflicting_fields()
            if conflicting_fields:
                conflicting_labels = list(
                    dict.fromkeys(
                        str(fs_form.fields[f].label)
                        for fs_form in formset.forms
                        for f in fs_form.get_conflicting_fields()
                        if f in fs_form.fields
                    )
                )
                self.request.session[f"tvar_concurrent_changes_{dokument.ident_cely}"] = conflicting_labels
                return redirect(dokument.get_absolute_url())
            logger.debug("dokument.views.TvarEditView.form_valid")
            formset.save()
            if formset.has_changed():
                fedora_transaction = dokument.create_transaction(self.request.user, ZAZNAM_USPESNE_EDITOVAN)
                dokument.save_metadata(fedora_transaction, close_transaction=True)
                logger.debug("dokument.views.TvarEditView.form_data_changed")
        else:
            logger.debug(
                "dokument.views.TvarEditView.form_not_valid",
                extra={"form_error": formset.errors, "error": formset.non_form_errors()},
            )
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        return redirect(dokument.get_absolute_url())


class TvarSmazatView(LoginRequiredMixin, TemplateView):
    """Třida pohledu pro smazání tvaru dokumentu pomocí modalu."""

    template_name = "core/transakce_modal.html"
    id_tag = "smazat-tvar-form"

    def dispatch(self, request, *args: Any, **kwargs: Any) -> HttpResponse:
        """
               Provádí operaci dispatch.

               :param request: Parametr ``request`` předává se do volání ``add_message()``, ``dispatch()``, vstupuje do návratové hodnoty.
               :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
               :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.
        """
        tvar = self.get_zaznam()
        if tvar.dokument.ident_cely != self.kwargs.get("ident_cely"):
            logger.debug("Dokument - Tvar wrong relation")
            messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
            return JsonResponse({"redirect": tvar.dokument.get_absolute_url()}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_zaznam(self):
        """Vrací zaznam. v aplikaci.

        :return: Vrací výsledek volání ``get_object_or_404()``.
        """
        id = self.kwargs.get("pk")
        return get_object_or_404(
            Tvar,
            pk=id,
        )

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

            :return: Vrací proměnná ``context``.
        """
        zaznam = self.get_zaznam()
        context = {
            "object": zaznam,
            "title": _("dokument.views.TvarSmazatView.title.text"),
            "id_tag": self.id_tag,
            "button": _("dokument.views.TvarSmazatView.submitButton.text"),
            "warnings": [_("dokument.views.TvarSmazatView.save_warning")],
        }
        return context

    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací výsledek volání ``render_to_response()``.
        """
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``create_transaction()``, pracuje se s atributy ``user``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        zaznam: Tvar = self.get_zaznam()
        zaznam.active_transaction = zaznam.create_transaction(request.user, ZAZNAM_USPESNE_SMAZAN)
        zaznam.close_active_transaction_when_finished = True
        dokument = zaznam.dokument
        zaznam.delete()

        return JsonResponse({"redirect": dokument.get_absolute_url()})


class VytvoritCastView(LoginRequiredMixin, TemplateView):
    """Třida pohledu pro vytvoření části dokumentu pomoci modalu."""

    template_name = "core/transakce_modal.html"
    id_tag = "vytvor-cast-form"

    def get_zaznam(self) -> Dokument:
        """
        Vrací zaznam. v aplikaci.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        ident_cely = self.kwargs.get("ident_cely")
        return get_object_or_404(
            Dokument.objects.exclude(typ_dokumentu__id__in=MODEL_3D_DOKUMENT_TYPES),
            ident_cely=ident_cely,
        )

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

            :return: Vrací proměnná ``context``.
        """
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
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací výsledek volání ``render_to_response()``.
        """
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``DokumentCastCreateForm()``, ``add_message()``, pracuje se s atributy ``POST``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        zaznam: Dokument = self.get_zaznam()
        form = DokumentCastCreateForm(data=request.POST)
        if form.is_valid():
            fedora_transaction = zaznam.create_transaction(self.request.user, ZAZNAM_USPESNE_VYTVOREN)
            fedora_transaction.redirect_on_error = False
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
            logger.debug("dokument.views.VytvoritCastView.post.form_not_valid", extra={"error": form.errors})
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
        """Provádí operaci init translations."""
        self.title = "title"
        self.button = "button"

    def get_zaznam(self) -> DokumentCast:
        """
        Vrací zaznam. v aplikaci.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        ident_cely = self.kwargs.get("ident_cely")
        logger.debug("dokument.views.TransakceView.get_zaznam", extra={"ident_cely": ident_cely})
        return get_object_or_404(
            DokumentCast,
            ident_cely=ident_cely,
        )

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

            :return: Vrací proměnná ``context``.
        """
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
        """
        Provádí operaci dispatch.

        :param request: Parametr ``request`` předává se do volání ``add_message()``, ``check_stav_changed()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``dispatch()``.
        """
        zaznam = self.get_zaznam().dokument
        if zaznam.stav not in self.allowed_states:
            logger.debug("dokument.views.TransakceView.dispatch", extra={"value": self.action})
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
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací výsledek volání ``render_to_response()``.
        """
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``add_message()``, pracuje se s atributy ``user``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        zaznam = self.get_zaznam()
        getattr(Dokument, self.action)(zaznam, request.user)
        messages.add_message(request, messages.SUCCESS, self.success_message)

        return JsonResponse({"redirect": zaznam.get_absolute_url()})


class DokumentCastPripojitAkciView(TransakceView):
    """Třida pohledu pro připojení akce do části dokumentu pomoci modalu."""

    template_name = "core/transakce_table_modal.html"
    id_tag = "pripojit-eo-form"

    def init_translations(self):
        """Provádí operaci init translations."""
        self.title = _("dokument.views.DokumentCastPripojitAkciView.title.text")
        self.button = _("dokument.views.DokumentCastPripojitAkciView.submitButton.text")
        self.success_message = DOKUMENT_AZ_USPESNE_PRIPOJEN

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        type_arch = self.request.GET.get("type")
        form = PripojitArchZaznamForm(type_arch=type_arch, dok=True)
        context["form"] = form
        context["hide_table"] = True
        context["type"] = type_arch
        context["card_type"] = type_arch
        return context

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``PripojitArchZaznamForm()``, pracuje se s atributy ``POST``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        cast = self.get_zaznam()
        cast: DokumentCast
        type_arch = self.request.GET.get("type")
        form = PripojitArchZaznamForm(data=request.POST, type_arch=type_arch, dok=True)
        if form.is_valid():
            logger.debug("dokument.views.DokumentCastPripojitAkciView.post.form_valid")
            fedora_transaction = cast.create_transaction(self.request.user, self.success_message)
            fedora_transaction.redirect_on_error = False
            cast.active_transaction = fedora_transaction
            arch_z_id = form.cleaned_data["arch_z"]
            arch_z = ArcheologickyZaznam.objects.get(id=arch_z_id)
            cast.archeologicky_zaznam = arch_z
            cast.projekt = None
            cast.close_active_transaction_when_finished = True
            cast.save()
        else:
            logger.debug("dokument.views.DokumentCastPripojitAkciView.post.form_invalid", extra={"error": form.errors})
        return JsonResponse({"redirect": cast.get_absolute_url()})


class DokumentCastPripojitProjektView(TransakceView):
    """Třida pohledu pro připojení projektu do části dokumentu pomoci modalu."""

    template_name = "core/transakce_table_modal.html"
    id_tag = "pripojit-projekt-form"

    def init_translations(self):
        """Provádí operaci init translations."""
        self.title = _("dokument.views.DokumentCastPripojitProjektView.title.text")
        self.button = _("dokument.views.DokumentCastPripojitProjektView.submitButton.text")
        self.success_message = DOKUMENT_PROJEKT_USPESNE_PRIPOJEN

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        form = PripojitProjektForm(dok=True)
        context["form"] = form
        context["hide_table"] = True
        return context

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``PripojitProjektForm()``, pracuje se s atributy ``POST``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        cast = self.get_zaznam()
        form = PripojitProjektForm(data=request.POST, dok=True)
        if form.is_valid():
            projekt = form.cleaned_data["projekt"]
            fedora_transaction = cast.create_transaction(self.request.user, self.success_message)
            fedora_transaction.redirect_on_error = False
            cast.close_active_transaction_when_finished = True
            cast.archeologicky_zaznam = None
            cast.projekt = Projekt.objects.get(id=projekt)
            cast.save()
        else:
            logger.debug(
                "dokument.views.DokumentCastPripojitProjektView.post.form_invalid", extra={"error": form.errors}
            )
        return JsonResponse({"redirect": cast.get_absolute_url()})


class DokumentCastOdpojitView(TransakceView):
    """Třida pohledu pro odpojení části dokumentu pomoci modalu."""

    id_tag = "odpojit-cast-form"

    def init_translations(self):
        """Provádí operaci init translations."""
        self.title = _("dokument.views.DokumentCastOdpojitView.title.text")
        self.button = _("dokument.views.DokumentCastOdpojitView.submitButton.text")
        self.success_message = DOKUMENT_CAST_USPESNE_ODPOJEN

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
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

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``create_transaction()``, pracuje se s atributy ``user``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        cast = self.get_zaznam()
        fedora_transaction = cast.create_transaction(request.user, self.success_message)
        fedora_transaction.redirect_url = cast.get_absolute_url()
        archeologicky_zaznam = cast.archeologicky_zaznam
        cast.archeologicky_zaznam = None
        cast.projekt = None
        try:
            with transaction.atomic():
                cast.save()
                if (
                    archeologicky_zaznam
                    and archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
                    and archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
                    and archeologicky_zaznam.lokalita.igsn
                ):
                    archeologicky_zaznam.lokalita.igsn_update()
                if cast.dokument.stav == D_STAV_ARCHIVOVANY and cast.dokument.doi:
                    cast.dokument.doi_update()
                cast.close_active_transaction_when_finished = True
                cast.save()
                return JsonResponse({"redirect": cast.get_absolute_url()})
        except (DoiWriteError, FedoraError) as err:
            logger.info(
                "dokument.views.DokumentCastOdpojitView.post.post_error",
                extra={"error": err, "ident_cely": cast.ident_cely},
            )
            transaction.set_rollback(True)
            fedora_transaction.rollback_transaction()
            if (
                archeologicky_zaznam
                and archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
                and archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
                and archeologicky_zaznam.lokalita.igsn
            ):
                archeologicky_zaznam.lokalita.igsn_update(check_status=False)
            if cast.dokument.stav == D_STAV_ARCHIVOVANY and cast.dokument.doi:
                cast.dokument.doi_update(False, True)
        return JsonResponse({"redirect": cast.get_absolute_url()})


class DokumentCastSmazatView(TransakceView):
    """Třida pohledu pro smazání části dokumentu pomoci modalu."""

    id_tag = "smazat-cast-form"

    def init_translations(self):
        """Provádí operaci init translations."""
        self.title = _("dokument.views.DokumentCastSmazatView.title.text")
        self.button = _("dokument.views.DokumentCastSmazatView.submitButton.text")
        self.success_message = DOKUMENT_CAST_USPESNE_SMAZANA

    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``create_transaction()``, pracuje se s atributy ``user``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        cast = self.get_zaznam()
        cast.create_transaction(request.user, self.success_message)
        dokument = cast.dokument
        if (
            isinstance(cast.archeologicky_zaznam, ArcheologickyZaznam)
            and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
            and cast.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
            and cast.archeologicky_zaznam.lokalita.igsn
        ):
            lokalita_update = cast.archeologicky_zaznam.lokalita
        else:
            lokalita_update = None
        try:
            with transaction.atomic():
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
                except ObjectDoesNotExist:
                    logger.debug(
                        "dokument.views.DokumentCastSmazatView.post.neident_akce_not_exists",
                        extra={"ident_cely": cast.ident_cely},
                    )
                cast.close_active_transaction_when_finished = True
                cast.delete()
                if lokalita_update:
                    lokalita_update.igsn_update()
                return JsonResponse({"redirect": dokument.get_absolute_url()})
        except (DoiWriteError, FedoraError) as err:
            logger.info(
                "dokument.views.DokumentCastSmazatView.post.post_error",
                extra={"error": err, "ident_cely": dokument.ident_cely},
            )
            transaction.set_rollback(True)
            dokument.active_transaction.rollback()
            if lokalita_update:
                lokalita_update.igsn_update(False, True)
        return JsonResponse({"redirect": dokument.get_absolute_url()})


class DokumentNeidentAkceSmazatView(TransakceView):
    """Třida pohledu pro smazání neident akce z části dokumentu pomoci modalu."""

    id_tag = "smazat-neident-akce-form"

    def init_translations(self):
        """Provádí operaci init translations."""
        self.title = _("dokument.views.DokumentNeidentAkceSmazatView.title.text")
        self.button = _("dokument.views.DokumentNeidentAkceSmazatView.submitButton.text")
        self.success_message = DOKUMENT_NEIDENT_AKCE_USPESNE_SMAZANA

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["object"] = context["object"].neident_akce
        return context

    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``add_message()``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        cast = self.get_zaznam()
        if cast.neident_akce:
            cast.neident_akce.delete()
            messages.add_message(request, messages.SUCCESS, self.success_message)
        else:
            messages.add_message(request, messages.SUCCESS, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
        return JsonResponse({"redirect": cast.get_absolute_url()})


@never_cache
@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    """
    Funkce pohledu pro editaci dokumentu.

    :param request: Parametr ``request`` se předává do volání ``create_transaction()``, ``EditDokumentForm()``, pracuje se s atributy ``user``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
        :raises PermissionDenied: Vyvolá se při splnění podmínky ``dokument.stav == D_STAV_ARCHIVOVANY``.
    """
    dokument: Dokument = get_object_or_404(
        Dokument.objects.exclude(typ_dokumentu__id__in=MODEL_3D_DOKUMENT_TYPES), ident_cely=ident_cely
    )
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
        fedora_transaction.redirect_on_error = True
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
            conflicting_fields = form_d.get_conflicting_fields() + form_extra.get_conflicting_fields()
            if conflicting_fields:
                conflicting_labels = list(
                    dict.fromkeys(str(form_d.fields[f].label) for f in conflicting_fields if f in form_d.fields)
                )
                conflicting_labels += list(
                    dict.fromkeys(str(form_extra.fields[f].label) for f in conflicting_fields if f in form_extra.fields)
                )
                fedora_transaction.rollback_transaction()
                return render(
                    request,
                    "dokument/edit.html",
                    {
                        "formDokument": form_d,
                        "formExtraData": form_extra,
                        "dokument": dokument,
                        "hierarchie": get_hierarchie_dokument_typ(),
                        "concurrent_changes": conflicting_labels,
                        "fresh_form_url": reverse("dokument:edit", kwargs={"ident_cely": dokument.ident_cely}),
                    },
                )
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
            instance_d.save()
            instance_d.close_active_transaction_when_finished = True
            instance_d.save()
            form_d.save_m2m()
            invalidate_model(Dokument)
            invalidate_model(Akce)

            return redirect("dokument:detail", ident_cely=dokument.ident_cely)
        else:
            logger.debug(
                "dokument.views.edit.forms_not_valid",
                extra={"error": form_d.errors, "form_error": form_extra.errors},
            )
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


@never_cache
@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def edit_model_3D(request, ident_cely):
    """
    Funkce pohledu pro editaci modelu 3D.

    :param request: Parametr ``request`` se předává do volání ``CreateModelDokumentForm()``, ``CreateModelExtraDataForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
        :raises PermissionDenied: Vyvolá se při splnění podmínky ``dokument.stav == D_STAV_ARCHIVOVANY``.
    """
    dokument: Dokument = get_object_or_404(
        Dokument, ident_cely=ident_cely, typ_dokumentu__id__in=MODEL_3D_DOKUMENT_TYPES
    )
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
        form_coor = CoordinatesDokumentForm(request.POST)  # Pro uložení změn je potřeba zpracovat data z formuláře.
        form_komponenta = CreateKomponentaForm(
            obdobi_choices,
            areal_choices,
            request.POST,
            instance=dokument.get_komponenta(),
            required=required_fields,
            required_next=required_fields_next,
            prefix="komponenta",
        )
        geom = None
        geom_sjtsk = None
        x1 = None
        x2 = None
        try:
            x1 = float(form_coor.data.get("coordinate_wgs84_x1"))
            x2 = float(form_coor.data.get("coordinate_wgs84_x2"))
            geom = Point(x1, x2)
            geom_sjtsk = Point(*convertToJTSK(x1, x2))
        except Exception:
            logger.debug("dokument.views.edit_model_3D.coord_error", extra={"X": x1, "Y": x2})
        if form_d.is_valid() and form_extra.is_valid() and form_komponenta.is_valid():
            conflicting_fields = form_d.get_conflicting_fields() + form_komponenta.get_conflicting_fields()
            geom_label = str(_("dokument.forms.createModelExtraDataForm.souradnice.label"))
            extra_conflicting = [
                geom_label if f == "geom" else str(form_extra.fields[f].label)
                for f in form_extra.get_conflicting_fields()
                if f == "geom" or f in form_extra.fields
            ]
            conflicting_labels = [
                str(form_d.fields[f].label) if f in form_d.fields else str(form_komponenta.fields[f].label)
                for f in conflicting_fields
                if f in form_d.fields or f in form_komponenta.fields
            ] + extra_conflicting
            if conflicting_labels:
                form_d_get = CreateModelDokumentForm(
                    instance=dokument, required=required_fields, required_next=required_fields_next
                )
                form_extra_get = CreateModelExtraDataForm(
                    instance=form_extra.instance, required=required_fields, required_next=required_fields_next
                )
                form_komponenta_get = CreateKomponentaForm(
                    obdobi_choices,
                    areal_choices,
                    instance=dokument.get_komponenta(),
                    required=required_fields,
                    required_next=required_fields_next,
                    prefix="komponenta",
                )
                return render(
                    request,
                    "dokument/create_model_3D.html",
                    {
                        "object": dokument,
                        "global_map_can_edit": True,
                        "formDokument": form_d_get,
                        "formExtraData": form_extra_get,
                        "formKomponenta": form_komponenta_get,
                        "title": _("dokument.views.edit_model_3D.title"),
                        "header": _("dokument.views.edit_model_3D.header"),
                        "button": _("dokument.views.edit_model_3D.submitButton.text"),
                        "concurrent_changes": list(dict.fromkeys(conflicting_labels)),
                        "fresh_form_url": reverse("dokument:edit-model-3D", kwargs={"ident_cely": ident_cely}),
                    },
                )
            # uloží autory v požadovaném pořadí
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
                dokument.extra_data.geom_sjtsk = geom_sjtsk
            form_extra.save()
            komponenta = form_komponenta.save(commit=False)
            komponenta.active_transaction = fedora_transaction
            komponenta.save()
            form_komponenta.save_m2m()
            dokument_from_form.close_active_transaction_when_finished = True
            dokument_from_form.save()
            return redirect("dokument:detail-model-3D", ident_cely=dokument.ident_cely)
        else:
            logger.debug(
                "dokument.views.edit_model_3D.forms_not_valid",
                extra={
                    "error": form_d.errors,
                    "form_error": form_extra.errors,
                    "komponenta": form_komponenta.errors,
                },
            )
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
            prefix="komponenta",
        )
        if dokument.extra_data.geom:
            geom = str(dokument.extra_data.geom).split("(")[1].replace(", ", ",").replace(")", "")
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

    :param request: Parametr ``request`` se předává do volání ``zapsat()``, vstupuje do návratové hodnoty.
    :param arch_z_ident_cely: Identifikátor ``arch_z_ident_cely`` používaný pro dohledání cílového záznamu.

        :return: Vrací výsledek volání ``zapsat()``.
    """
    zaznam: ArcheologickyZaznam = get_object_or_404(ArcheologickyZaznam, ident_cely=arch_z_ident_cely)
    return zapsat(request, zaznam)


@login_required
def zapsat_do_projektu(request, proj_ident_cely):
    """
    Funkce pohledu pro zapsání dokumentu do projektu.

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``zapsat()``, vstupuje do návratové hodnoty.
    :param proj_ident_cely: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``zapsat()``.
    """
    zaznam = get_object_or_404(Projekt, ident_cely=proj_ident_cely)
    if zaznam.typ_projektu.id != TYP_PROJEKTU_PRUZKUM_ID:
        logger.debug("Projekt neni typu pruzkumny")
        messages.add_message(request, messages.SUCCESS, PROJEKT_NENI_TYP_PRUZKUMNY)
        return redirect(zaznam.get_absolute_url())
    return zapsat(request, zaznam)


@never_cache
@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def create_model_3D(request):
    """
    Funkce pohledu pro vytvoření modelu 3D.

    :param request: Parametr ``request`` se předává do volání ``CreateModelDokumentForm()``, ``CreateModelExtraDataForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
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
            prefix="komponenta",
        )
        geom = None
        geom_sjtsk = None
        x1 = None
        x2 = None
        try:
            x1 = float(form_extra.data.get("coordinate_wgs84_x1"))
            x2 = float(form_extra.data.get("coordinate_wgs84_x2"))
            geom = Point(x1, x2)
            geom_sjtsk = Point(*convertToJTSK(x1, x2))
        except Exception:
            logger.debug("dokument.views.create_model_3D.coord_error", extra={"X": x1, "Y": x2})

        if form_d.is_valid() and form_extra.is_valid() and form_komponenta.is_valid():
            logger.debug("dokument.views.create_model_3D.forms_valid")
            dokument: Dokument = form_d.save(commit=False)
            fedora_transaction = dokument.create_transaction(request.user, ZAZNAM_USPESNE_VYTVOREN)
            dokument.rada = Heslar.objects.get(id=DOKUMENT_RADA_DATA_3D)
            dokument.material_originalu = Heslar.objects.get(id=MATERIAL_DOKUMENTU_DIGITALNI_SOUBOR)
            try:
                dokument.ident_cely = get_temp_dokument_ident(rada="3D", region="C-")
            except MaximalIdentNumberError:
                messages.add_message(request, messages.ERROR, MAXIMUM_IDENT_DOSAZEN)
                fedora_transaction.rollback_transaction()
            else:
                dokument.pristupnost = Heslar.objects.get(id=PRISTUPNOST_ANONYM_ID)
                dokument.stav = D_STAV_ZAPSANY
                dokument.ulozeni_originalu = Heslar.objects.get(id=PRIMARNE_DIGITALNI)
                dokument.save()
                dokument.set_zapsany(request.user)
                # Vytvořit výchozí část dokumentu.
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
                if geom_sjtsk is not None:
                    extra_data.geom_sjtsk = geom_sjtsk
                extra_data.geom_system = "4326"
                extra_data.save()

                komponenta = form_komponenta.save(commit=False)
                komponenta.active_transaction = fedora_transaction
                komponenta.komponenta_vazby = dc.komponenty
                komponenta.ident_cely = dokument.ident_cely + "-K001"
                komponenta.save()
                form_komponenta.save_m2m()

                dokument.close_active_transaction_when_finished = True
                dokument.save()

                return redirect("dokument:detail-model-3D", ident_cely=dokument.ident_cely)

        else:
            logger.debug(
                "dokument.views.create_model_3D.forms_not_valid",
                extra={
                    "error": form_d.errors,
                    "form_error": form_extra.errors,
                    "komponenta": form_komponenta.errors,
                },
            )
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
            prefix="komponenta",
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
            "toolbar_label": _("dokument.views.create_model_3D.toolbar_label"),
        },
    )


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def odeslat(request, ident_cely):
    """
    Funkce pohledu pro odeslání dokumentu cez modal.

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``debug()``, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, proměnná ``returned_value``, výsledek volání ``render()``.
    """
    dokument = get_object_or_404(Dokument, ident_cely=ident_cely)
    dokument: Dokument
    logger.debug("dokument.views.odeslat.start", extra={"ident_cely": ident_cely})
    if dokument.stav != D_STAV_ZAPSANY:
        logger.debug("dokument.views.odeslat.permission_denied", extra={"ident_cely": ident_cely})
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    # Momentálně zbytečné, případná chyba se propaguje výše.
    if check_stav_changed(request, dokument):
        logger.debug("dokument.views.odeslat.check_stav_changed", extra={"ident_cely": ident_cely})

        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    if request.method == "POST":
        fedora_transaction = dokument.create_transaction(request.user, DOKUMENT_USPESNE_ODESLAN, DOKUMENT_NELZE_ODESLAT)
        fedora_transaction.redirect_url = get_detail_json_view(ident_cely)
        old_ident = dokument.ident_cely
        # Nastav identifikátor na permanentní.
        returned_value = Dokument.set_permanent_identificator(dokument, request, messages, fedora_transaction)
        if isinstance(returned_value, JsonResponse):
            fedora_transaction.rollback_transaction()
            return returned_value
        dokument.set_odeslany(request.user, old_ident)
        logger.debug("dokument.views.odeslat.sucess")
        dokument.close_active_transaction_when_finished = True
        dokument.save()
        return JsonResponse({"redirect": get_detail_json_view(dokument.ident_cely)})
    else:
        warnings = dokument.check_pred_odeslanim()
        if warnings:
            logger.debug("dokument.views.odeslat.warnings", extra={"warning": warnings, "ident_cely": ident_cely})
            request.session["temp_data"] = warnings
            messages.add_message(request, messages.ERROR, DOKUMENT_NELZE_ODESLAT)
            return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
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

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``debug()``, pracuje se s atributy ``startswith``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
    """
    dokument = get_object_or_404(Dokument, ident_cely=ident_cely)
    dokument: Dokument
    logger.debug("dokument.views.archivovat.start", extra={"ident_cely": ident_cely})
    if dokument.stav != D_STAV_ODESLANY:
        logger.debug("dokument.views.archivovat.permission_denied", extra={"ident_cely": ident_cely})
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    # Momentálně zbytečné, případná chyba se propaguje výše.
    if check_stav_changed(request, dokument):
        logger.debug("dokument.views.archivovat.check_stav_changed", extra={"ident_cely": ident_cely})
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    if request.method == "POST":
        fedora_transaction = dokument.create_transaction(request.user, DOKUMENT_USPESNE_ARCHIVOVAN)
        dokument.active_transaction = fedora_transaction
        old_ident = dokument.ident_cely
        dokument_casti = list(dokument.casti.all())
        try:
            with transaction.atomic():
                # Nastav identifikátor na permanentní.
                if ident_cely.startswith(IDENTIFIKATOR_DOCASNY_PREFIX):
                    rada = get_dokument_rada(dokument.typ_dokumentu, dokument.material_originalu)
                    try:
                        dokument.set_permanent_ident_cely(dokument.ident_cely[2], rada)
                    except MaximalIdentNumberError:
                        fedora_transaction.error_message = MAXIMUM_IDENT_DOSAZEN
                        fedora_transaction.rollback_transaction()
                        dokument.close_active_transaction_when_finished = True
                        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
                    else:
                        dokument.save()
                        logger.debug("dokument.views.archivovat.permanent", extra={"ident_cely": dokument.ident_cely})
                dokument.set_archivovany(request.user, old_ident)
                dokument.doi_publish()
                dokument.set_doi()
                for item in dokument_casti:
                    item: DokumentCast
                    if (
                        item.archeologicky_zaznam
                        and item.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
                        and item.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
                        and item.archeologicky_zaznam.lokalita.igsn
                    ):
                        item.archeologicky_zaznam.lokalita.igsn_update()
                if dokument.rada == Heslar.objects.get(id=DOKUMENT_RADA_DATA_3D):
                    Mailer.send_ek01(document=dokument)
                dokument.close_active_transaction_when_finished = True
                dokument.save()
                return JsonResponse({"redirect": get_detail_json_view(dokument.ident_cely)})
        except (DoiWriteError, FedoraError) as err:
            logger.info("dokument.views.archivovat.post_error", extra={"error": err, "ident_cely": ident_cely})
            transaction.set_rollback(True)
            fedora_transaction.rollback_transaction()
            dokument.doi_hide(False)
            for item in dokument_casti:
                item: DokumentCast
                if (
                    item.archeologicky_zaznam
                    and item.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
                    and item.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
                    and item.archeologicky_zaznam.lokalita.igsn
                ):
                    item.archeologicky_zaznam.lokalita.igsn_update(False, True)
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)})
    else:
        warnings = dokument.check_pred_archivaci()
        logger.debug("dokument.views.archivovat.warnings", extra={"warning": warnings})
        if warnings:
            request.session["temp_data"] = warnings
            messages.add_message(request, messages.ERROR, DOKUMENT_NELZE_ARCHIVOVAT)
            return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    doi_confirmation = dokument.doi_exists and dokument.doi is None
    form_check = CheckStavNotChangedForm(require_confirmation=doi_confirmation, initial={"old_stav": dokument.stav})
    context = {
        "object": dokument,
        "title": _("dokument.views.archivovat.title"),
        "pid_confirmation": doi_confirmation,
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

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
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
            fedora_transaction = dokument.create_transaction(request.user, DOKUMENT_USPESNE_VRACEN)
            try:
                if dokument.stav == D_STAV_ARCHIVOVANY:
                    dokument.doi_hide()
                duvod = form.cleaned_data["reason"]
                before_save_state = dokument.stav
                dokument.set_vraceny(request.user, dokument.stav - 1, duvod)
                dokument.close_active_transaction_when_finished = True
                dokument.save()
                if before_save_state == D_STAV_ODESLANY:
                    Mailer.send_ek02(document=dokument, reason=duvod)
                return JsonResponse({"redirect": get_detail_json_view(ident_cely)})
            except (DoiWriteError, FedoraError) as err:
                logger.info("dokument.views.vratit.post_error", extra={"error": err, "ident_cely": ident_cely})
                fedora_transaction.rollback_transaction()
                if isinstance(err, FedoraError):
                    dokument.doi_publish(False)
                transaction.set_rollback(True)
                return JsonResponse({"redirect": get_detail_json_view(ident_cely)})
        else:
            logger.debug("dokument.views.vratit.not_valid", extra={"error": form.errors})
            return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
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

    :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``create_transaction()``, pracuje se s atributy ``user``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
        :raises ValueError: Vyvolá se s textem "dokument.views.smazat.deleted".
    """
    dokument: Dokument = get_object_or_404(Dokument, ident_cely=ident_cely)
    dokument.deleted_by_user = request.user
    if check_stav_changed(request, dokument):
        return JsonResponse({"redirect": get_detail_json_view(ident_cely)}, status=403)
    if request.method == "POST":
        fedora_transaction = dokument.create_transaction(
            request.user, ZAZNAM_USPESNE_SMAZAN, ZAZNAM_SE_NEPOVEDLO_SMAZAT
        )
        try:
            with transaction.atomic():
                dokument.doi_delete()
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
                    logger.debug("dokument.views.smazat.deleted", extra={"value": resp1})
                    fedora_transaction.mark_transaction_as_closed()
                    if "3D" in ident_cely:
                        return JsonResponse({"redirect": reverse("dokument:index-model-3D")})
                    else:
                        return JsonResponse({"redirect": reverse("dokument:index")})
                else:
                    raise ValueError("dokument.views.smazat.deleted")
        except (DoiWriteError, FedoraError, ValueError) as err:
            logger.info("dokument.views.smazat.post_error", extra={"ident_cely": ident_cely, "error": err})
            transaction.set_rollback(True)
            fedora_transaction.rollback_transaction()
            if isinstance(err, FedoraError):
                dokument.doi_update(False, True)
            return JsonResponse({"redirect": get_detail_json_view(ident_cely)})
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


class DokumentAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView, PermissionFilterMixin):
    """Třída pohledu pro autocomplete dokumentů."""

    typ_zmeny_lookup = ZAPSANI_DOK

    def get_result_label(self, result):
        """
        Vrací result label.

        :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.

            :return: Vrací hodnotu podle větve zpracování.
        """
        return f"{result.ident_cely} ({result.autori_snapshot} {result.rok_vzniku})"

    def get_queryset(self):
        """Vrací queryset. v aplikaci.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``none()``, výsledek volání ``check_filter_permission()``.
        """
        if not self.request.user.is_authenticated:
            return Dokument.objects.none()
        ident = self.request.GET.get("ident")
        qs = Dokument.objects.exclude(
            Q(typ_dokumentu__id__in=MODEL_3D_DOKUMENT_TYPES)
            | Q(casti__archeologicky_zaznam__ident_cely=ident)
            | Q(casti__projekt__ident_cely=ident)
        ).order_by("ident_cely")
        if self.q:
            qs = qs.filter(
                Q(ident_cely__icontains=self.q) | Q(autori_snapshot__icontains=self.q) | Q(rok_vzniku__icontains=self.q)
            )
        return self.check_filter_permission(qs)


def get_hierarchie_dokument_typ():
    """Funkce pro získaní hierarchie pro heslař.

    :return: Vrací proměnná ``hierarchie``.
    """
    hierarchie_qs = HeslarHierarchie.objects.filter(heslo_podrazene__nazev_heslare__id=HESLAR_DOKUMENT_TYP).values_list(
        "heslo_podrazene", "heslo_nadrazene"
    )
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

    :param historie_vazby: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
    :param request_user: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.
    :return: Slovník dat jednotlivých změn stavu pro zobrazení v historii.
    """
    request_user: User
    anonymized = request_user.hlavni_role.pk not in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)
    historie = {
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_DOK, anonymized),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_DOK, anonymized),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_DOK, anonymized),
    }
    return historie


def get_detail_template_shows(dokument, user):
    """
    Funkce pro získaní kontextu pro zobrazování možností na stránkách.

    :param dokument: Parametr ``dokument`` předává se do volání ``check_permissions()``, pracuje se s atributy ``ident_cely``, ``stav``, ovlivňuje větvení podmínek.
    :param user: Parametr ``user`` se předává do volání ``check_permissions()``.
    :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.
    """
    if "3D" in dokument.ident_cely:
        show_edit = check_permissions(p.actionChoices.model_edit, user, dokument.ident_cely)
        soubor_stahnout_dokument = check_permissions(p.actionChoices.soubor_stahnout_model3d, user, dokument.ident_cely)
        soubor_nahled = check_permissions(p.actionChoices.soubor_nahled_model3d, user, dokument.ident_cely)
        soubor_smazat = check_permissions(p.actionChoices.soubor_smazat_model3d, user, dokument.ident_cely)
        soubor_nahradit = check_permissions(p.actionChoices.soubor_nahradit_model3d, user, dokument.ident_cely)
        vypis = check_permissions(p.actionChoices.vypis_model3d, user, dokument.ident_cely)
    else:
        show_edit = check_permissions(p.actionChoices.dok_edit, user, dokument.ident_cely)
        soubor_stahnout_dokument = check_permissions(
            p.actionChoices.soubor_stahnout_dokument, user, dokument.ident_cely
        )
        soubor_nahled = check_permissions(p.actionChoices.soubor_nahled_dokument, user, dokument.ident_cely)
        soubor_smazat = check_permissions(p.actionChoices.soubor_smazat_dokument, user, dokument.ident_cely)
        soubor_nahradit = check_permissions(p.actionChoices.soubor_nahradit_dokument, user, dokument.ident_cely)
        vypis = check_permissions(p.actionChoices.vypis_dokument, user, dokument.ident_cely)
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
        "soubor_stahnout": soubor_stahnout_dokument,
        "soubor_nahled": soubor_nahled,
        "soubor_smazat": soubor_smazat,
        "soubor_nahradit": soubor_nahradit,
        "vypis": vypis,
    }
    return show


@never_cache
@handle_fedora_error
@login_required
def zapsat(request, zaznam=None):
    """
    Funkce pohledu pro zapsání dokumentu.

    :param request: Parametr ``request`` se předává do volání ``EditDokumentForm()``, ``create_transaction()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param zaznam: Parametr ``zaznam`` předává se do volání ``isinstance()``, ``DokumentCast()``, pracuje se s atributy ``ident_cely``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
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
            fedora_transaction = dokument.create_transaction(
                request.user, ZAZNAM_USPESNE_VYTVOREN, ZAZNAM_SE_NEPOVEDLO_VYTVORIT
            )
            dokument.rada = get_dokument_rada(dokument.typ_dokumentu, dokument.material_originalu)
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
                dokument.ident_cely = get_temp_dokument_ident(rada=dokument.rada.zkratka, region=prefix)
            except MaximalIdentNumberError:
                fedora_transaction.error_message = MAXIMUM_IDENT_DOSAZEN
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

                    # Vytvořit výchozí část dokumentu.
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

                    return redirect("dokument:detail", ident_cely=dokument.ident_cely)
                else:
                    logger.debug(
                        "dokument.views.zapsat.check_container_deleted_or_not_exists.invalid",
                        extra={"ident_cely": dokument.ident_cely},
                    )
        else:
            logger.debug("dokument.views.zapsat.not_valid", extra={"error": form_d.errors})

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
            "toolbar_label": _("dokument.views.zapsat.dokument.toolbar_label"),
        },
    )


@handle_fedora_error
def odpojit(request, ident_doku, ident_zaznamu, zaznam):
    """
    Funkce pohledu pro odpojení dokumentu cez modal.

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``FedoraTransaction()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_doku: Identifikátor ``ident_doku`` používaný pro dohledání cílového záznamu.
    :param ident_zaznamu: Identifikátor ``ident_zaznamu`` používaný pro dohledání cílového záznamu.
    :param zaznam: Parametr ``zaznam`` předává se do volání ``JsonResponse()``, ``isinstance()``, pracuje se s atributy ``get_absolute_url``, ``typ_zaznamu``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
    """
    relace_dokumentu = DokumentCast.objects.filter(dokument__ident_cely=ident_doku)
    remove_orphan = False
    orphan_dokument = None
    lokalita_update = None
    dokument_update = None
    if len(relace_dokumentu) == 0:
        logger.debug("dokument.views.odpojit.no_relace", extra={"ident_cely": ident_doku})
        messages.add_message(request, messages.ERROR, DOKUMENT_ODPOJ_ZADNE_RELACE)
        return JsonResponse({"redirect": zaznam.get_absolute_url()}, status=404)
    if len(relace_dokumentu) == 1:
        orphan_dokument = relace_dokumentu[0].dokument
        if orphan_dokument.ident_cely.startswith("X-"):
            remove_orphan = True
    if request.method == "POST":
        if isinstance(zaznam, ArcheologickyZaznam):
            dokument_cast_query = relace_dokumentu.filter(archeologicky_zaznam__ident_cely=ident_zaznamu)
        else:
            dokument_cast_query = relace_dokumentu.filter(projekt__ident_cely=ident_zaznamu)
        if len(dokument_cast_query) == 0:
            logger.debug("dokument.views.odpojit.no_relace", extra={"ident_cely": ident_doku})
            messages.add_message(request, messages.ERROR, DOKUMENT_ODPOJ_ZADNE_RELACE_MEZI_DOK_A_ZAZNAM)
            return JsonResponse({"redirect": zaznam.get_absolute_url()}, status=404)
        fedora_transaction = FedoraTransaction(zaznam, request.user, DOKUMENT_USPESNE_ODPOJEN)
        fedora_transaction.main_record = zaznam
        dokument_cast = dokument_cast_query.first()
        dokument_cast.active_transaction = fedora_transaction
        if (
            isinstance(zaznam, ArcheologickyZaznam)
            and zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
            and zaznam.stav == AZ_STAV_ARCHIVOVANY
            and zaznam.lokalita.igsn
        ):
            lokalita_update = zaznam.lokalita
        if dokument_cast.dokument and dokument_cast.dokument.doi and dokument_cast.dokument.stav == D_STAV_ARCHIVOVANY:
            dokument_update = dokument_cast.dokument
        try:
            with transaction.atomic():
                resp = dokument_cast.delete()
                logger.debug("dokument.views.odpojit.deleted", extra={"value": resp})
                if remove_orphan:
                    orphan_dokument.active_transaction = fedora_transaction
                    orphan_dokument.record_deletion()
                    orphan_dokument.delete()
                    logger.debug("dokument.views.odpojit.deleted")
                if lokalita_update:
                    lokalita_update.igsn_update()
                if dokument_update:
                    dokument_update.doi_update()
                fedora_transaction.mark_transaction_as_closed()
                return JsonResponse({"redirect": zaznam.get_absolute_url()})
        except (DoiWriteError, FedoraError) as err:
            logger.info("dokument.views.odpojit.post_error", extra={"error": err, "ident_cely": zaznam.ident_cely})
            transaction.set_rollback(True)
            fedora_transaction.rollback_transaction()
            if lokalita_update:
                lokalita_update.igsn_update(False, True)
            if dokument_update:
                dokument_update.doi_update(False, True)
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


@handle_fedora_error(additional_exceptions=(IntegrityError,))
def pripojit(request, ident_zaznam, proj_ident_cely, typ):
    """
    Funkce pohledu pro pripojení dokumentu cez modal.

    :param request: Parametr ``request`` se předává do volání ``create_transaction()``, ``add_message()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_zaznam: Identifikátor ``ident_zaznam`` používaný pro dohledání cílového záznamu.
    :param proj_ident_cely: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.
    :param typ: Parametr ``typ`` předává se do volání ``get_object_or_404()``.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
    """
    zaznam = get_object_or_404(typ, ident_cely=ident_zaznam)
    if isinstance(zaznam, ArcheologickyZaznam):
        casti_zaznamu = DokumentCast.objects.filter(archeologicky_zaznam__ident_cely=ident_zaznam)
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
        if len(dokument_ids) > 0:
            fedora_transaction = zaznam.create_transaction(request.user)
            try:
                for dokument_id in dokument_ids:
                    dokument = get_object_or_404(Dokument, id=dokument_id)
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
                        else:
                            dc = DokumentCast(projekt=zaznam, dokument=dokument, ident_cely=dc_ident)
                        dc.active_transaction = fedora_transaction
                        dc.save()
                        dokument.save()
                        logger.debug(
                            "dokument.views.pripojit.pripojit",
                            extra={"value": debug_name, "zaznam": ident_zaznam, "ident_cely": dokument.ident_cely},
                        )
                        messages.add_message(
                            request, messages.SUCCESS, f"{dokument.ident_cely} {DOKUMENT_USPESNE_PRIPOJEN}"
                        )
                    else:
                        messages.add_message(
                            request, messages.ERROR, f"{dokument.ident_cely} {DOKUMENT_JIZ_BYL_PRIPOJEN}"
                        )
            except Exception as err:
                logger.error("dokument.views.pripojit.error", extra={"error": err, "ident_cely": dokument.ident_cely})
                transaction.set_rollback(True)
                fedora_transaction.rollback_transaction()
            else:
                fedora_transaction.mark_transaction_as_closed()
        return JsonResponse({"redirect": redirect_name})
    else:
        if proj_ident_cely:
            # Přidávám projektové dokumenty.
            projekt = get_object_or_404(Projekt, ident_cely=proj_ident_cely)
            proj_dok_list = (
                Dokument.objects.filter(casti__archeologicky_zaznam__akce__projekt=projekt)
                .exclude(casti__archeologicky_zaznam__ident_cely=ident_zaznam)
                .distinct()
            )
            context["dokumenty"] = proj_dok_list
            context["pripojit"] = True
            return render(request, "core/transakce_table_modal.html", context)
        else:
            # Přidávám všechny dokumenty.
            form = PripojitDokumentForm(ident_zaznam)
        context["form"] = form
        context["hide_table"] = True
    return render(request, "core/transakce_table_modal.html", context)


@login_required
@require_http_methods(["GET"])
def get_dokument_table_row(request):
    """
    Funkce pohledu pro získaní řádku dokumentu pro vykreslení v modalu.

    :param request: Parametr ``request`` se předává do volání ``get()``, pracuje se s atributy ``GET``.

        :return: Vrací výsledek volání ``HttpResponse()``.
    """
    context = {"d": Dokument.objects.get(id=request.GET.get("id", "")), "prefix": "modaldoc"}
    return HttpResponse(render_to_string("dokument/dokument_table_row.html", context))


@login_required
@require_http_methods(["GET"])
def get_dokument_table_row_vratit(request):
    """
    AJAX pohled pro načtení jednoho řádku dokumentu do tabulky pro "vrácení dokumentu".

    :param request: Parametr ``request`` pracuje se s atributy ``GET``.

        :return: Vrací výsledek volání ``HttpResponse()``.
        :raises Http404: Vyvolá se s textem "Dokument neexistuje.".
    """
    dokument_id = request.GET.get("id")
    index = request.GET.get("index")
    if not dokument_id:
        return HttpResponse(status=400)
    qs = Dokument.objects.filter(id=dokument_id)
    perm_object = PermissionFilterMixin()
    perm_object.request = request
    qs = perm_object.check_filter_permission(qs)
    dokument = qs.first()
    if dokument is None:
        raise Http404("Dokument neexistuje.")
    form = VratitFormDokument(
        initial={"old_stav": dokument.stav, "ident_cely": dokument.ident_cely}, prefix=f"form-{index}"
    )
    context = {
        "vratit": True,
        "d": dokument,
        "form": form,
        "prefix": "modaldoc",
    }
    return HttpResponse(render_to_string("dokument/dokument_table_row.html", context))


def get_detail_view(ident_cely):
    """
    Funkce pohledu pro redirect podle identu na model 3D nebo dokument detail.

    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``redirect()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací výsledek volání ``redirect()``.
    """
    if "3D" in ident_cely:
        return redirect("dokument:detail-model-3D", ident_cely=ident_cely)
    else:
        return redirect("dokument:detail", ident_cely=ident_cely)


def get_detail_json_view(ident_cely):
    """
    Funkce pohledu pro vrácení url pro redirect podle identu na model 3D nebo dokument detail.

    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``reverse()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací výsledek volání ``reverse()``.
    """
    if "3D" in ident_cely:
        return reverse("dokument:detail-model-3D", kwargs={"ident_cely": ident_cely})
    else:
        return reverse("dokument:detail", kwargs={"ident_cely": ident_cely})


def get_required_fields_model3D(zaznam=None, next=0):
    """
    Funkce pro získaní dictionary povinných polí podle stavu modelu 3D.

    :param zaznam: Parametr ``zaznam`` pracuje se s atributy ``stav``, ovlivňuje větvení podmínek.
    :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
    :return: Seznam názvů polí, která mají být v daném stavu povinná.
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
            "licence",
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

    :param zaznam: Parametr ``zaznam`` pracuje se s atributy ``stav``, ovlivňuje větvení podmínek.
    :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
    :return: Seznam názvů polí, která mají být v daném stavu povinná.
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


def get_komponenta_form_detail(komponenta, show, old_nalez_post, komp_ident_cely, session=None):
    """
    Funkce pro získaní formsetu predmetu a objektu pro komponentu.

    :param komponenta: Komponenta, se kterou funkce pracuje.
    :param show: Parametr ``show`` se předává do volání ``inlineformset_factory()``, ``create_nalez_objekt_form()``.
    :param old_nalez_post: Parametr ``old_nalez_post`` se předává do volání ``NalezObjektFormset()``, ``NalezPredmetFormset()``.
    :param komp_ident_cely: Identifikátor ``komp_ident_cely`` používaný pro dohledání cílového záznamu.
    :param session: Volitelná Django session pro načtení dat souběžné editace.

        :return: Vrací proměnná ``komponenta_form_detail``.
    """
    NalezObjektFormset = inlineformset_factory(
        Komponenta,
        NalezObjekt,
        form=create_nalez_objekt_form(
            heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT),
            heslar_12(HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT),
            not_readonly=show["editovat"],
        ),
        extra=3 if show["editovat"] else 0,
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
        extra=3 if show["editovat"] else 0,
        can_delete=False,
    )

    concurrent_changes = session.pop(f"komp_concurrent_changes_{komponenta.ident_cely}", None) if session else None
    post_data_dict = (
        session.pop(f"komp_post_data_{komponenta.ident_cely}", None) if (session and concurrent_changes) else None
    )
    create_komp_form = CreateKomponentaForm(
        get_obdobi_choices(),
        get_areal_choices(),
        instance=komponenta,
        prefix=komponenta.ident_cely,
        readonly=not show["editovat"],
    )
    if post_data_dict:
        from django.http import QueryDict

        post_qd = QueryDict(mutable=True)
        post_qd.update(post_data_dict)
        create_komp_form.data = post_qd
        create_komp_form.files = {}
        create_komp_form.is_bound = True
    if komponenta.komponenta_vazby.typ_vazby == DOKUMENTACNI_JEDNOTKA_RELATION_TYPE:
        dj = komponenta.komponenta_vazby.dokumentacni_jednotka
        if dj.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            fresh_form_url = reverse(
                "arch_z:update-komponenta",
                args=[dj.archeologicky_zaznam.ident_cely, dj.ident_cely, komponenta.ident_cely],
            )
        else:
            fresh_form_url = reverse(
                "lokalita:update-komponenta",
                args=[dj.archeologicky_zaznam.ident_cely, dj.ident_cely, komponenta.ident_cely],
            )
    else:
        cast = komponenta.komponenta_vazby.casti_dokumentu
        fresh_form_url = reverse(
            "dokument:detail-komponenta",
            args=[cast.dokument.ident_cely, komponenta.ident_cely],
        )
    komponenta_form_detail = {
        "ident_cely": komponenta.ident_cely,
        "form": create_komp_form,
        "form_nalezy_objekty": (
            NalezObjektFormset(
                old_nalez_post,
                instance=komponenta,
                prefix=komponenta.ident_cely + "_o",
            )
            if komponenta.ident_cely == komp_ident_cely
            else NalezObjektFormset(instance=komponenta, prefix=komponenta.ident_cely + "_o")
        ),
        "form_nalezy_predmety": (
            NalezPredmetFormset(
                old_nalez_post,
                instance=komponenta,
                prefix=komponenta.ident_cely + "_p",
            )
            if komponenta.ident_cely == komp_ident_cely
            else NalezPredmetFormset(instance=komponenta, prefix=komponenta.ident_cely + "_p")
        ),
        "helper_predmet": NalezFormSetHelper(typ="predmet"),
        "helper_objekt": NalezFormSetHelper(typ="objekt"),
        "concurrent_changes": concurrent_changes,
        "fresh_form_url": fresh_form_url,
    }
    return komponenta_form_detail


def get_obdobi_choices():
    """Funkce která vrací dvou stupňový heslař pro období.

    :return: Vrací výsledek volání ``heslar_12()``.
    """
    return heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)


def get_areal_choices():
    """Funkce která vrací dvou stupňový heslař pro areál.

    :return: Vrací výsledek volání ``heslar_12()``.
    """
    return heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)


@login_required
@require_http_methods(["POST"])
def post_ajax_get_3d_limit(request):
    """
    Funkce pohledu pro získaní 3D.

    :param request: Parametr ``request`` se předává do volání ``loads()``, ``get_3d_from_envelope()``, pracuje se s atributy ``body``.

        :return: Vrací výsledek volání ``JsonResponse()``.
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
        back.append(
            {
                "id": pian["dokument__id"],
                "ident_cely": pian["dokument__ident_cely"],
                "geom": pian["geom"].wkt.replace(", ", ","),
            }
        )
    if len(pians) > 0:
        return JsonResponse({"points": back, "algorithm": "detail"}, status=200)
    else:
        return JsonResponse({"points": [], "algorithm": "detail"}, status=200)


class DokumentyAzTableView(LoginRequiredMixin, View):
    """Třída pohledu pro zobrazení tabulky dokumentů."""

    def get(self, request, typ_vazby, ident_cely):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` předává se do volání ``check_permissions()``, pracuje se s atributy ``user``.
        :param typ_vazby: Parametr ``typ_vazby`` ovlivňuje větvení podmínek.
        :param ident_cely: Parametr ``ident_cely`` se předává do volání ``filter()``, ``get()``.

            :return: Vrací výsledek volání ``HttpResponse()``.
        """
        if typ_vazby == "arch_z":
            qs = (
                Dokument.objects.filter(casti__archeologicky_zaznam__ident_cely=ident_cely)
                .select_related("soubory")
                .prefetch_related("soubory__soubory")
                .order_by("ident_cely")
            )
            zaznam = ArcheologickyZaznam.objects.get(ident_cely=ident_cely)
            dokument_odpojit = check_permissions(
                p.actionChoices.archz_odpojit_dokument, request.user, zaznam.ident_cely
            )
        else:
            qs = (
                Dokument.objects.filter(casti__projekt__ident_cely=ident_cely)
                .select_related("soubory")
                .prefetch_related("soubory__soubory")
            ).order_by("ident_cely")
            zaznam = Projekt.objects.get(ident_cely=ident_cely)
            dokument_odpojit = (
                check_permissions(p.actionChoices.projekt_dok_odpojit, request.user, zaznam.ident_cely),
            )
        context = {
            "dokumenty": qs,
            "show": {"dokument_odpojit": dokument_odpojit},
            "zaznam": zaznam,
            "type": typ_vazby,
            "prefix": "doc",
        }
        logger.debug(context)
        return HttpResponse(render_to_string("dokument/dokument_table_only.html", context))


@login_required
def zjisti_licenci_organizace(request):
    """
    Funkce pohledu pro zjištení licence organizace.

    :param request: Parametr ``request`` pracuje se s atributy ``GET``.

        :return: Vrací výsledek volání ``JsonResponse()``.
    """
    organizace_id = request.GET.get("organizace", "").strip()
    organizace_id = int(organizace_id) if organizace_id and organizace_id.isdigit() else 0
    organizace = Organizace.objects.filter(pk=organizace_id)
    if len(organizace) != 1:
        logger.debug("dokument.views.zjisti_licenci_organizace.does_not_exist", extra={"data": organizace_id})

        return JsonResponse(data={}, status=400)
    list = {"licence": organizace.first().licence_id}
    return JsonResponse(data=list, status=200, safe=False)
