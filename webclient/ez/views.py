import logging

from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
from core.constants import (
    AZ_STAV_ARCHIVOVANY,
    AZ_STAV_ODESLANY,
    AZ_STAV_ZAPSANY,
    EZ_STAV_ODESLANY,
    EZ_STAV_POTVRZENY,
    EZ_STAV_ZAPSANY,
    ODESLANI_EXT_ZD,
    POTVRZENI_EXT_ZD,
    ROLE_ADMIN_ID,
    ROLE_ARCHIVAR_ID,
    ZAPSANI_EXT_ZD,
)
from core.forms import CheckStavNotChangedForm, VratitForm
from core.ident_cely import get_temp_ez_ident
from core.message_constants import (
    EO_USPESNE_ODPOJEN,
    EZ_USPESNE_ODESLAN,
    EZ_USPESNE_POTVRZEN,
    EZ_USPESNE_VRACENA,
    EZ_USPESNE_ZAPSAN,
    PRISTUP_ZAKAZAN,
    SPATNY_ZAZNAM_ZAZNAM_VAZBA,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT_NAVAZANE_ZAZNAMY,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
)
from core.models import Permissions as p
from core.models import check_permissions
from core.repository_connector import FedoraError, FedoraRepositoryConnector, FedoraTransaction
from core.utils import get_message
from core.views import PermissionFilterMixin, SearchListView, check_stav_changed
from dal import autocomplete
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Prefetch, Q, RestrictedError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from fedora_management.decorators import handle_fedora_error
from pid.exceptions import DoiWriteError
from uzivatel.models import Osoba, User

from .filters import ExterniZdrojFilter
from .forms import ExterniOdkazForm, ExterniZdrojForm, PripojitArchZaznamForm, PripojitExterniOdkazForm
from .models import ExterniZdroj, ExterniZdrojAutor, ExterniZdrojEditor
from .tables import ExterniZdrojTable

logger = logging.getLogger(__name__)


class ExterniZdrojIndexView(LoginRequiredMixin, TemplateView):
    """Třida pohledu pro zobrazení domovské stránky externích zdrojů s navigačními možnostmi."""

    template_name = "ez/index.html"

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní kontextu podlehu.

        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

            :return: Vrací proměnná ``context``.
        """
        context = {
            "toolbar_name": _("ez.views.externiZdrojIndexView.toolbarName"),
        }
        return context


class ExterniZdrojListView(SearchListView):
    """Třida pohledu pro zobrazení listu/tabulky s externím zdrojem."""

    table_class = ExterniZdrojTable
    model = ExterniZdroj
    filterset_class = ExterniZdrojFilter
    export_name = "export_externi-zdroje_"
    app = "ext_zdroj"
    toolbar = "toolbar_externi_zdroj.html"
    redis_snapshot_prefix = "externi_zdroj"
    redis_value_list_field = "ident_cely"
    typ_zmeny_lookup = ZAPSANI_EXT_ZD
    vypis_app = "ez"

    def init_translations(self):
        """Provádí operaci init translations."""
        super().init_translations()
        self.page_title = _("ez.templates.ExterniZdrojListView.pageTitle.text")
        self.search_sum = _("ez.templates.ExterniZdrojListView.search_sum.text")
        self.pick_text = _("ez.templates.ExterniZdrojListView.pickText.text")
        self.hasOnlyVybrat_header = _("ez.templates.ExterniZdrojListView.hasOnlyVybrat_header.text")
        self.hasOnlyVlastnik_header = _("ez.templates.ExterniZdrojListView.hasOnlyVlastnik_header.text")
        self.hasOnlyArchive_header = _("ez.templates.ExterniZdrojListView.hasOnlyPotvrdit_header.text")
        self.hasOnlyNase_header = _("ez.views.ExterniZdrojListView.hasOnlyNase_header.text")
        self.default_header = _("ez.templates.ExterniZdrojListView.header.default_header.text")
        self.toolbar_name = _("ez.templates.ExterniZdrojListView.toolbar_name.text")

    @staticmethod
    def rename_field_for_ordering(field: str):
        """
        Provádí operaci rename field for ordering.

        :param field: Parametr ``field`` předává se do volání ``get()``, pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``get()``.
        """
        field = field.replace("-", "")
        return {
            "autori": "autori_snapshot",
            "editori": "editori_snapshot",
            "typ": "typ__razeni",
            "typ_dokumentu": "typ_dokumentu__razeni",
        }.get(field, field)

    def get_queryset(self):
        """Vrací queryset. v aplikaci.

        :return: Vrací výsledek volání ``check_filter_permission()``.
        """
        sort_params = self._get_sort_params()
        sort_params = [self.rename_field_for_ordering(x) for x in sort_params]
        qs = super().get_queryset()
        qs = qs.order_by(*sort_params)
        qs = qs.distinct("pk", *sort_params)
        qs = qs.select_related(
            "typ",
        ).prefetch_related(
            Prefetch(
                "autori",
                queryset=Osoba.objects.all().order_by("externizdrojautor__poradi"),
                to_attr="ordered_autors",
            ),
            Prefetch(
                "editori",
                queryset=Osoba.objects.all().order_by("externizdrojeditor__poradi"),
                to_attr="ordered_editors",
            ),
            "editori",
            "autori",
        )
        return self.check_filter_permission(qs)

    def add_accessibility_lookup(self, permission, qs):
        """
        Provádí operaci add accessibility lookup.

        :param permission: Parametr ``permission`` slouží jako vstup pro logiku funkce ``add_accessibility_lookup``.
        :param qs: Parametr ``qs`` vstupuje do návratové hodnoty.

            :return: Vrací proměnná ``qs``.
        """
        return qs


class ExterniZdrojDetailView(LoginRequiredMixin, DetailView):
    """Třida pohledu pro zobrazení detailu externího zdroju."""

    model = ExterniZdroj
    template_name = "ez/detail.html"
    slug_field = "ident_cely"

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

            :return: Vrací proměnná ``context``.
        """
        context = {}
        zaznam = self.get_object()
        ez_odkazy = ExterniOdkaz.objects.filter(externi_zdroj=zaznam)
        ez_akce = (
            ez_odkazy.filter(archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_AKCE)
            .select_related("archeologicky_zaznam")
            .select_related("archeologicky_zaznam__akce")
        ).order_by("archeologicky_zaznam__ident_cely")
        ez_lokality = (
            ez_odkazy.filter(archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA)
            .select_related("archeologicky_zaznam")
            .select_related("archeologicky_zaznam__lokalita")
        ).order_by("archeologicky_zaznam__ident_cely")
        context["form"] = ExterniZdrojForm(instance=zaznam, readonly=True, required=False)
        context["zaznam"] = zaznam
        context["app"] = "ext_zdroj"
        context["page_title"] = _("ez.templates.ExterniZdrojDetailView.pageTitle")
        context["toolbar_name"] = _("ez.templates.ExterniZdrojDetailView.toolbar.title")
        context["history_dates"] = get_history_dates(zaznam.historie, self.request.user)
        context["show"] = get_detail_template_shows(zaznam, self.request.user)
        context["ez_akce"] = ez_akce
        context["ez_lokality"] = ez_lokality
        return context


class ExterniZdrojCreateView(LoginRequiredMixin, CreateView):
    """Třida pohledu pro vytvoření externího zdroje."""

    model = ExterniZdroj
    template_name = "ez/create.html"
    form_class = ExterniZdrojForm

    def get_form_kwargs(self):
        """Vrací form kwargs.

        :return: Vrací proměnná ``kwargs``.
        """
        kwargs = super().get_form_kwargs()
        required_fields = get_required_fields()
        kwargs.update({"required": required_fields, "required_next": required_fields})
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["toolbar_name"] = _("ez.templates.ExterniZdrojCreateView.toolbar.title")
        context["page_title"] = _("ez.templates.ExterniZdrojCreateView.pageTitle")
        context["header"] = _("ez.templates.ExterniZdrojCreateView.formHeader.label")
        context["toolbar_label"] = _("ez.templates.ExterniZdrojCreateView.toolbar_label.title")
        context["submit_button"] = _("ez.templates.ExterniZdrojCreateView.ulozitButton.label")
        return context

    def form_valid(self, form):
        """
        Provádí operaci form valid.

        :param form: Parametr ``form`` se předává do volání ``save_autor_editor()``, ``form_invalid()``, pracuje se s atributy ``save``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``HttpResponseRedirect()``, výsledek volání ``form_invalid()``.
        """
        ez = form.save(commit=False)
        ez: ExterniZdroj
        fedora_transaction = ez.create_transaction(self.request.user, EZ_USPESNE_ZAPSAN)
        ez.stav = EZ_STAV_ZAPSANY
        ez.ident_cely = get_temp_ez_ident()
        repository_connector = FedoraRepositoryConnector(ez, skip_container_check=False)
        if repository_connector.check_container_deleted_or_not_exists(ez.ident_cely, "ext_zdroj"):
            ez.active_transaction = fedora_transaction
            ez.save()
            save_autor_editor(ez, form)
            ez.set_zapsany(self.request.user)
            ez.close_active_transaction_when_finished = True
            ez.save()
            return HttpResponseRedirect(ez.get_absolute_url())
        else:
            logger.debug(
                "ez.views.ExterniZdrojCreateView.form_valid.check_container_deleted_or_not_exists.incorrect",
                extra={"ident_cely": ez.ident_cely},
            )
            messages.add_message(
                self.request,
                messages.ERROR,
                _("ez.views.zapsat.ExterniZdrojCreateView." "check_container_deleted_or_not_exists_error"),
            )
            return super().form_invalid(form)

    def form_invalid(self, form):
        """
        Provádí operaci form invalid.

        :param form: Parametr ``form`` se předává do volání ``debug()``, ``form_invalid()``, pracuje se s atributy ``errors``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``form_invalid()``.
        """
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)
        logger.debug("ez.views.ExterniZdrojCreateView.form_invalid", extra={"error": form.errors})
        return super().form_invalid(form)

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


class ExterniZdrojEditView(LoginRequiredMixin, UpdateView):
    """Třida pohledu pro editaci externího zdroje."""

    model = ExterniZdroj
    template_name = "ez/create.html"
    form_class = ExterniZdrojForm
    slug_field = "ident_cely"

    def get_form_kwargs(self):
        """Vrací form kwargs.

        :return: Vrací proměnná ``kwargs``.
        """
        kwargs = super().get_form_kwargs()
        required_fields = get_required_fields()
        kwargs.update({"required": required_fields, "required_next": required_fields})
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["zaznam"] = self.object
        context["toolbar_name"] = _("ez.templates.ExterniZdrojEditView.toolbar.title")
        context["page_title"] = _("ez.templates.ExterniZdrojEditView.pageTitle")
        context["header"] = _("ez.templates.ExterniZdrojEditView.formHeader.label")
        context["submit_button"] = _("ez.templates.ExterniZdrojEditView.ulozitButton.label")
        return context

    @method_decorator(handle_fedora_error)
    def form_valid(self, form):
        """
        Provádí operaci form valid.

        :param form: Parametr ``form`` se předává do volání ``save_autor_editor()``, pracuje se s atributy ``save``.

            :return: Vrací výsledek volání ``HttpResponseRedirect()``.
        """
        conflicting_fields = form.get_conflicting_fields()
        if conflicting_fields:
            conflicting_labels = [str(form.fields[f].label) for f in conflicting_fields if f in form.fields]
            context = self.get_context_data(form=form)
            context["concurrent_changes"] = conflicting_labels
            context["fresh_form_url"] = reverse("ez:edit", kwargs={"slug": self.object.ident_cely})
            return self.render_to_response(context)
        self.object: ExterniZdroj = form.save(commit=False)
        self.object.active_transaction = self.object.create_transaction(self.request.user)
        self.object.active_transaction.redirect_on_error = True
        self.object.autori.clear()
        self.object.editori.clear()
        self.object.save()
        self.object.close_active_transaction_when_finished = True
        self.object.save()
        save_autor_editor(self.object, form)
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        """
        Provádí operaci form invalid.

        :param form: Parametr ``form`` se předává do volání ``debug()``, ``form_invalid()``, pracuje se s atributy ``errors``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``form_invalid()``.
        """
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        logger.debug("ez.views.ExterniZdrojEditView.form_invalid", extra={"error": form.errors})
        return super().form_invalid(form)

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

    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``post()``, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``post()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``post()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``post()``.
        """
        return super().post(request, *args, **kwargs)


class TransakceView(LoginRequiredMixin, TemplateView):
    """
    Třida pohledu pro změnu stavu a práci s externíma zdrojama cez modal, která se dedí pro jednotlivá změny.
    """

    template_name = "core/transakce_modal.html"
    id_tag = "id_tag"
    allowed_states = []
    success_message = "success"
    action = ""
    active_transaction = None

    def init_translation(self):
        """Provádí operaci init translation."""
        self.title = "title"
        self.button = "button"

    def get_zaznam(self) -> ExterniZdroj:
        """
        Vrací zaznam. v aplikaci.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        ident_cely = self.kwargs.get("ident_cely")
        logger.debug("ez.views.TransakceView.get_zaznam.start", extra={"ident_cely": ident_cely})
        zaznam = get_object_or_404(
            ExterniZdroj,
            ident_cely=ident_cely,
        )
        if self.active_transaction:
            zaznam.active_transaction = self.active_transaction
        return zaznam

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

            :return: Vrací proměnná ``context``.
        """
        self.init_translation()
        zaznam = self.get_zaznam()
        form_check = CheckStavNotChangedForm(initial={"old_stav": zaznam.stav})
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
        zaznam = self.get_zaznam()
        if zaznam.stav not in self.allowed_states:
            logger.debug("ez.views.TransakceView.dispatch.start", extra={"value": self.action})
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

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``create_transaction()``, pracuje se s atributy ``user``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        context = self.get_context_data(**kwargs)
        zaznam = context["object"]
        zaznam.create_transaction(request.user, self.success_message)
        zaznam.save()
        zaznam.close_active_transaction_when_finished = True
        getattr(ExterniZdroj, self.action)(zaznam, request.user)

        return JsonResponse({"redirect": zaznam.get_absolute_url()})


class ExterniZdrojOdeslatView(TransakceView):
    """Třida pohledu pro odeslání externího zdroje pomoci modalu."""

    id_tag = "odeslat-ez-form"
    allowed_states = [EZ_STAV_ZAPSANY]
    action = "set_odeslany"

    def init_translation(self):
        """Provádí operaci init translation."""
        self.title = _("ez.templates.ExterniZdrojOdeslatView.title.text")
        self.button = _("ez.templates.ExterniZdrojOdeslatView.submitButton.text")
        self.success_message = EZ_USPESNE_ODESLAN


class ExterniZdrojPotvrditView(TransakceView):
    """Třida pohledu pro potvrzení externího zdroje pomoci modalu."""

    id_tag = "potvrdit-ez-form"
    allowed_states = [EZ_STAV_ODESLANY]
    action = "set_potvrzeny"

    def init_translation(self):
        """Provádí operaci init translation."""
        self.title = _("ez.templates.ExterniZdrojPotvrditView.title.text")
        self.button = _("ez.templates.ExterniZdrojPotvrditView.submitButton.text")
        self.success_message = EZ_USPESNE_POTVRZEN

    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``create_transaction()``, pracuje se s atributy ``user``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        context = self.get_context_data(**kwargs)
        zaznam: ExterniZdroj = context["object"]
        fedora_transaction = zaznam.create_transaction(request.user, self.success_message)
        try:
            with transaction.atomic():
                zaznam.save()
                zaznam.close_active_transaction_when_finished = True
                getattr(ExterniZdroj, self.action)(zaznam, request.user)
                return JsonResponse({"redirect": zaznam.get_absolute_url()})
        except (DoiWriteError, FedoraError) as err:
            logger.info(
                "ez.models.ExterniZdroj.set_potvrzeny.error", extra={"error": err, "ident_cely": zaznam.ident_cely}
            )
            from arch_z.models import ArcheologickyZaznam

            for akce in zaznam.externi_odkazy_zdroje.all():
                if (
                    akce.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
                    and akce.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
                    and akce.archeologicky_zaznam.lokalita.igsn
                ):
                    akce.archeologicky_zaznam.igsn_lokalita_update(False, True)
            fedora_transaction.rollback_transaction()
            transaction.set_rollback(True)
            return JsonResponse({"redirect": zaznam.get_absolute_url()})


class ExterniZdrojSmazatView(TransakceView):
    """Třida pohledu pro smazání externího zdroje pomoci modalu."""

    id_tag = "smazat-ez-form"
    allowed_states = [EZ_STAV_ODESLANY, EZ_STAV_POTVRZENY, EZ_STAV_ZAPSANY]

    def init_translation(self):
        """Provádí operaci init translation."""
        self.title = _("ez.templates.ExterniZdrojSmazatView.title.text")
        self.button = _("ez.templates.ExterniZdrojSmazatView.submitButton.text")
        self.success_message = ZAZNAM_USPESNE_SMAZAN

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``create_transaction()``, ``add_message()``, pracuje se s atributy ``user``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        context = self.get_context_data(**kwargs)
        zaznam = context["object"]
        zaznam.deleted_by_user = request.user
        fedora_transaction: FedoraTransaction = zaznam.create_transaction(
            request.user, error_message=ZAZNAM_SE_NEPOVEDLO_SMAZAT
        )
        zaznam.close_active_transaction_when_finished = True
        try:
            zaznam.delete()
        except RestrictedError as err:
            logger.debug("ez.views.ExterniZdrojSmazatView.error", extra={"ident_cely": zaznam.ident_cely, "error": err})
            fedora_transaction.error_message = ZAZNAM_SE_NEPOVEDLO_SMAZAT_NAVAZANE_ZAZNAMY
            fedora_transaction.rollback_transaction()
            return JsonResponse(
                {"redirect": zaznam.get_absolute_url()},
                status=403,
            )
        messages.add_message(request, messages.SUCCESS, self.success_message)
        return JsonResponse({"redirect": reverse("ez:index")})


class ExterniZdrojVratitView(TransakceView):
    """Třida pohledu pro vrácení externího zdroje pomoci modalu."""

    id_tag = "vratit-ez-form"
    allowed_states = [EZ_STAV_ODESLANY, EZ_STAV_POTVRZENY]
    action = "set_vraceny"

    def init_translation(self):
        """Provádí operaci init translation."""
        self.title = _("ez.templates.ExterniZdrojVratitView.title.text")
        self.button = _("ez.templates.ExterniZdrojVratitView.submitButton.text")
        self.success_message = EZ_USPESNE_VRACENA

    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací výsledek volání ``render_to_response()``.
        """
        context = self.get_context_data(**kwargs)
        form = VratitForm(initial={"old_stav": context["object"].stav})
        context["form"] = form
        return self.render_to_response(context)

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``create_transaction()``, ``VratitForm()``, pracuje se s atributy ``user``, ``POST``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.
        """
        context = self.get_context_data(**kwargs)
        zaznam = context["object"]
        zaznam.create_transaction(request.user, self.success_message)
        zaznam.close_active_transaction_when_finished = True
        form = VratitForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            getattr(ExterniZdroj, self.action)(zaznam, request.user, zaznam.stav - 1, duvod)
            return JsonResponse({"redirect": zaznam.get_absolute_url()})
        else:
            logger.debug("ez.views.ExterniZdrojVratitView.form_invalid", extra={"error": form.errors})
            return self.render_to_response(context)


class ExterniOdkazOdpojitView(TransakceView):
    """Třida pohledu pro odpojení externího odkazu pomoci modalu."""

    id_tag = "odpojit-az-form"
    allowed_states = [EZ_STAV_ODESLANY, EZ_STAV_POTVRZENY, EZ_STAV_ZAPSANY]

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """
               Provádí operaci dispatch.

               :param request: Parametr ``request`` předává se do volání ``add_message()``, ``dispatch()``, vstupuje do návratové hodnoty.
               :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
               :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.
        """
        eo = get_object_or_404(
            ExterniOdkaz,
            id=self.kwargs.get("eo_id"),
        )
        if eo.externi_zdroj.ident_cely != self.kwargs["ident_cely"]:
            logger.debug("Externi odkaz - Externi zdroj wrong relation")
            messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
            return JsonResponse({"redirect": self.get_zaznam().get_absolute_url()}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def init_translation(self):
        """Provádí operaci init translation."""
        self.title = _("ez.templates.ExterniOdkazOdpojitView.title.text")
        self.button = _("ez.templates.ExterniOdkazOdpojitView.submitButton.text")
        self.success_message = EO_USPESNE_ODPOJEN

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["object"] = get_object_or_404(
            ArcheologickyZaznam,
            externi_odkazy__id=self.kwargs.get("eo_id"),
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
        self.init_translation()
        ez = self.get_zaznam()
        lokalita_update = None
        self.active_transaction = ez.create_transaction(request.user, self.success_message)
        eo = ExterniOdkaz.objects.get(id=self.kwargs.get("eo_id"))
        eo.active_transaction = self.active_transaction
        if (
            eo.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
            and eo.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
            and eo.archeologicky_zaznam.lokalita.igsn
        ):
            lokalita_update = eo.archeologicky_zaznam.lokalita
        eo.close_active_transaction_when_finished = True
        try:
            with transaction.atomic():
                eo.delete()
                if lokalita_update:
                    lokalita_update.igsn_update()
                return JsonResponse({"redirect": ez.get_absolute_url()})
        except (DoiWriteError, FedoraError) as err:
            logger.info("ez.views.ExterniOdkazOdpojitView.error", extra={"error": err, "ident_cely": ez.ident_cely})
            transaction.set_rollback(True)
            if lokalita_update:
                lokalita_update.igsn_update(False, True)
            self.active_transaction.rollback_transaction()
        return JsonResponse({"redirect": ez.get_absolute_url()})


class ExterniOdkazPripojitView(TransakceView):
    """Třida pohledu pro připojení externího odkazu pomoci modalu."""

    template_name = "core/transakce_table_modal.html"
    id_tag = "pripojit-eo-form"
    allowed_states = [EZ_STAV_ODESLANY, EZ_STAV_POTVRZENY, EZ_STAV_ZAPSANY]

    def init_translation(self):
        """Provádí operaci init translation."""
        self.title = _("ez.templates.ExterniOdkazPripojitView.title.text")
        self.button = _("ez.templates.ExterniOdkazPripojitView.submitButton.text")

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        type_arch = self.request.GET.get("type")
        form = PripojitArchZaznamForm(type_arch=type_arch)
        context["form"] = form
        context["hide_table"] = True
        context["type"] = type_arch
        context["card_type"] = type_arch
        return context

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``PripojitArchZaznamForm()``, ``create_transaction()``, pracuje se s atributy ``POST``, ``user``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        context = self.get_context_data(**kwargs)
        logger.debug("ez.views.ExterniOdkazPripojitView.post.start", extra={"key": self.kwargs})
        ez = self.get_zaznam()
        form = PripojitArchZaznamForm(data=request.POST, type_arch=context["type"])
        if form.is_valid():
            logger.debug("ez.views.ExterniOdkazPripojitView.post.form_valid")
            ez = self.get_zaznam()
            arch_z_id = form.cleaned_data["arch_z"]
            arch_z = ArcheologickyZaznam.objects.get(id=arch_z_id)
            self.active_transaction = ez.create_transaction(request.user, get_message(arch_z, "EO_USPESNE_PRIPOJEN"))
            eo = ExterniOdkaz(
                externi_zdroj=ez,
                paginace=form.cleaned_data["paginace"],
                archeologicky_zaznam=arch_z,
            )
            eo.active_transaction = self.active_transaction
            eo.close_active_transaction_when_finished = True
            eo.save()
        else:
            logger.debug("ez.views.ExterniOdkazPripojitView.post.form_error", extra={"error": form.errors})
        return JsonResponse({"redirect": ez.get_absolute_url()})


class ExterniOdkazEditView(LoginRequiredMixin, UpdateView):
    """Třida pohledu pro editaci externího odkazu pomoci modalu."""

    model = ExterniOdkaz
    template_name = "core/transakce_modal.html"
    id_tag = "zmenit-eo-form"
    allowed_states = []
    success_message = "success"
    form_class = ExterniOdkazForm
    slug_field = "id"
    active_transaction = None

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """
               Provádí operaci dispatch.

               :param request: Parametr ``request`` předává se do volání ``add_message()``, ``dispatch()``, vstupuje do návratové hodnoty.
               :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
               :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.
        """
        eo = self.get_object()
        if self.kwargs.get("typ_vazby") == "ez":
            check = eo.externi_zdroj.ident_cely != self.kwargs.get("ident_cely")
        elif self.kwargs.get("typ_vazby") == "akce":
            check = eo.archeologicky_zaznam.ident_cely != self.kwargs.get("ident_cely")
        else:
            check = True
        if check:
            messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
            return JsonResponse({"redirect": self.get_object().get_absolute_url()}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context = {
            "object": self.object,
            "title": _("ez.templates.ExterniOdkazPripojitView.title.text"),
            "id_tag": self.id_tag,
            "button": _("ez.templates.ExterniOdkazEditView.submitButton.text"),
        }
        context["form"] = ExterniOdkazForm(
            instance=self.object,
        )
        return context

    def get_success_url(self):
        """Vrací success url.

        :return: Vrací proměnná ``response``.
        """
        next_url = self.request.GET.get("next_url")
        if next_url:
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
                response = next_url
        else:
            response = self.get_context_data()["object"].externi_zdroj.get_absolute_url()
        return response

    def get_object(self, queryset=None):
        """
        Vrací object. v aplikaci.

        :param queryset: Parametr ``queryset`` slouží jako vstup pro logiku funkce ``get_object``.

            :return: Vrací proměnná ``object``.
        """
        object = super().get_object()
        object: ExterniOdkaz
        if self.active_transaction:
            object.close_active_transaction_when_finished = True
            object.active_transaction = self.active_transaction
        return object

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
        super().post(request, *args, **kwargs)
        self.active_transaction = None
        return JsonResponse({"redirect": self.get_success_url()})

    def form_valid(self, form):
        """
        Provádí operaci form valid.

        :param form: Parametr ``form`` se předává do volání ``form_valid()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``form_valid()``.
        """
        messages.add_message(self.request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Provádí operaci form invalid.

        :param form: Parametr ``form`` se předává do volání ``debug()``, ``form_invalid()``, pracuje se s atributy ``errors``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``form_invalid()``.
        """
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        logger.debug("ez.views.ExterniOdkazEditView.form_invalid", extra={"error": form.errors})
        return super().form_invalid(form)


class ExterniOdkazOdpojitAZView(TransakceView):
    """Třida pohledu pro odpojení externího odkazu z archeologického záznamu pomoci modalu."""

    id_tag = "odpojit-az-form"
    allowed_states = [AZ_STAV_ODESLANY, AZ_STAV_ZAPSANY, AZ_STAV_ARCHIVOVANY]

    def init_translation(self):
        """Provádí operaci init translation."""
        super().init_translation()
        self.success_message = EO_USPESNE_ODPOJEN

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """
               Provádí operaci dispatch.

               :param request: Parametr ``request`` předává se do volání ``add_message()``, ``dispatch()``, vstupuje do návratové hodnoty.
               :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
               :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.
        """
        eo = get_object_or_404(
            ExterniOdkaz,
            id=self.kwargs.get("eo_id"),
        )
        if eo.archeologicky_zaznam.ident_cely != self.kwargs["ident_cely"]:
            logger.debug("Externi odkaz - Archeologicky zaznam wrong relation")
            messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
            return JsonResponse({"redirect": self.get_zaznam().get_absolute_url()}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_zaznam(self):
        """Vrací zaznam. v aplikaci.

        :return: Vrací výsledek volání ``get_object_or_404()``.
        """
        ident_cely = self.kwargs.get("ident_cely")
        logger.debug("ez.views.TransakceView.ExterniOdkazOdpojitAZView.start", extra={"ident_cely": ident_cely})
        return get_object_or_404(
            ArcheologickyZaznam,
            ident_cely=ident_cely,
        )

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        logger.debug(
            "ez.views.TransakceView.ExterniOdkazOdpojitAZView.get_context_data",
            extra={"pk": self.kwargs.get("eo_id")},
        )
        context["object"] = ExterniZdroj.objects.get(externi_odkazy_zdroje__id=self.kwargs.get("eo_id"))
        if self.get_zaznam().typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            context["title"] = _("ez.templates.ExterniOdkazOdpojitAZView.arch_z.title.text")
            context["button"] = _("ez.templates.ExterniOdkazOdpojitAZView.arch_z.submitButton.text")
        else:
            context["title"] = _("ez.templates.ExterniOdkazOdpojitAZView.lokalita.title.text")
            context["button"] = _("lokaez.templateslita.ExterniOdkazOdpojitAZView.lokalita.submitButton.text")
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
        az = self.get_zaznam()
        lokalita_update = None
        self.active_transaction = az.create_transaction(request.user, get_message(az, "EO_USPESNE_ODPOJEN"))
        eo = ExterniOdkaz.objects.get(id=self.kwargs.get("eo_id"))
        eo.active_transaction = self.active_transaction
        if (
            eo.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
            and eo.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
            and eo.archeologicky_zaznam.lokalita.igsn
        ):
            lokalita_update = eo.archeologicky_zaznam.lokalita
        try:
            with transaction.atomic():
                eo.close_active_transaction_when_finished = True
                eo.delete()
                if lokalita_update:
                    lokalita_update.igsn_update()
                return JsonResponse({"redirect": az.get_absolute_url()})
        except (DoiWriteError, FedoraError) as err:
            logger.info("ez.views.ExterniOdkazOdpojitAZView.error", extra={"error": err, "ident_cely": az.ident_cely})
            transaction.set_rollback(True)
            if lokalita_update:
                lokalita_update.igsn_update(False, True)
            self.active_transaction.rollback_transaction()
        return JsonResponse({"redirect": az.get_absolute_url()})


class ExterniZdrojAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView, PermissionFilterMixin):
    """Třída pohledu pro autocomplete externích zdrojů."""

    typ_zmeny_lookup = ZAPSANI_EXT_ZD

    def get_result_label(self, result):
        """
        Vrací result label.

        :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.

            :return: Vrací hodnotu podle větve zpracování.
        """
        return f"{result.ident_cely} ({result.autori_snapshot} {result.rok_vydani_vzniku}: {result.nazev})"

    def get_queryset(self):
        """Vrací queryset. v aplikaci.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``none()``, výsledek volání ``check_filter_permission()``.
        """
        if not self.request.user.is_authenticated:
            return ExterniZdroj.objects.none()

        qs = ExterniZdroj.objects.filter().order_by("ident_cely")
        if self.q:
            qs = qs.filter(
                Q(ident_cely__icontains=self.q)
                | Q(autori_snapshot__icontains=self.q)
                | Q(rok_vydani_vzniku__icontains=self.q)
                | Q(nazev__icontains=self.q)
            )
        return self.check_filter_permission(qs)

    def add_accessibility_lookup(self, permission, qs):
        """
        Provádí operaci add accessibility lookup.

        :param permission: Parametr ``permission`` slouží jako vstup pro logiku funkce ``add_accessibility_lookup``.
        :param qs: Parametr ``qs`` vstupuje do návratové hodnoty.

            :return: Vrací proměnná ``qs``.
        """
        return qs


class ExterniZdrojTableRowView(LoginRequiredMixin, View):
    """Třída pohledu pro získaní řádku tabulky s externím zdrojem."""

    def get(self, request):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` předává se do volání ``get()``, pracuje se s atributy ``GET``.

            :return: Vrací výsledek volání ``HttpResponse()``.
        """
        zaznam = ExterniZdroj.objects.get(id=request.GET.get("id", ""))
        context = {"ez": zaznam}
        context["hide_paginace"] = True
        return HttpResponse(render_to_string("ez/az_ez_odkazy_table_row.html", context))


class ExterniOdkazPripojitDoAzView(TransakceView):
    """Třída pohledu pro připojení externího odkazu do arch záznamu."""

    template_name = "core/transakce_table_modal.html"
    id_tag = "pripojit-eo-doaz-form"
    allowed_states = [EZ_STAV_ODESLANY, EZ_STAV_POTVRZENY, EZ_STAV_ZAPSANY]

    def get_zaznam(self):
        """Vrací zaznam. v aplikaci.

        :return: Vrací proměnná ``zaznam``.
        """
        ident_cely = self.kwargs.get("ident_cely")
        zaznam = get_object_or_404(
            ArcheologickyZaznam,
            ident_cely=ident_cely,
        )
        if self.active_transaction:
            zaznam.active_transaction = self.active_transaction
            zaznam.close_active_transaction_when_finished = True
        return zaznam

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        form = PripojitExterniOdkazForm()
        context["form"] = form
        context["hide_table"] = True
        context["hide_paginace"] = True
        if self.get_zaznam().typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            context["title"] = _("ez.templates.ExterniOdkazPripojitDoAzView.arch_z.title.text")
            context["button"] = _("ez.templates.ExterniOdkazPripojitDoAzView.arch_z.submitButton.text")
        else:
            context["title"] = _("ez.templates.ExterniOdkazPripojitDoAzView.lokalita.title.text")
            context["button"] = _("ez.templates.ExterniOdkazPripojitDoAzView.lokalita.submitButton.text")
        return context

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``create_transaction()``, ``PripojitExterniOdkazForm()``, pracuje se s atributy ``user``, ``POST``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        az = self.get_zaznam()
        self.active_transaction = az.create_transaction(request.user, get_message(az, "EO_USPESNE_PRIPOJEN"))
        form = PripojitExterniOdkazForm(data=request.POST)
        if form.is_valid():
            ez_id = form.cleaned_data["ez"]
            ez = ExterniZdroj.objects.get(id=ez_id)
            eo = ExterniOdkaz(
                externi_zdroj=ez,
                paginace=form.cleaned_data["paginace"],
                archeologicky_zaznam=az,
            )
            eo: ExterniOdkaz
            eo.active_transaction = self.active_transaction
            eo.close_active_transaction_when_finished = True
            eo.suppress_signal = False
            eo.save()
        else:
            logger.debug("ez.views.ExterniOdkazPripojitDoAzView.form_invalid", extra={"error": form.errors})
        return JsonResponse({"redirect": az.get_absolute_url()})


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
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_EXT_ZD, anonymized),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_EXT_ZD, anonymized),
        "datum_potvrzeni": historie_vazby.get_last_transaction_date(POTVRZENI_EXT_ZD, anonymized),
    }
    return historie


def get_detail_template_shows(zaznam, user):
    """
    Funkce pro získaní kontextu pro zobrazování možností na stránkách.

    :param zaznam: Parametr ``zaznam`` předává se do volání ``check_permissions()``, pracuje se s atributy ``stav``, ``ident_cely``.
    :param user: Parametr ``user`` se předává do volání ``check_permissions()``.
    :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.
    """
    show_arch_links = zaznam.stav == EZ_STAV_POTVRZENY
    show_ez_odkazy = True
    show_paginace = True
    show = {
        "vratit_link": check_permissions(p.actionChoices.ez_vratit, user, zaznam.ident_cely),
        "odeslat_link": check_permissions(p.actionChoices.ez_odeslat, user, zaznam.ident_cely),
        "potvrdit_link": check_permissions(p.actionChoices.ez_potvrdit, user, zaznam.ident_cely),
        "editovat": check_permissions(p.actionChoices.ez_edit, user, zaznam.ident_cely),
        "odpojit": check_permissions(p.actionChoices.eo_odpojit_akce, user, zaznam.ident_cely),
        "arch_links": show_arch_links,
        "ez_odkazy": show_ez_odkazy,
        "paginace": show_paginace,
        "pripojit_eo": check_permissions(p.actionChoices.eo_pripojit_akce, user, zaznam.ident_cely),
        "paginace_edit": check_permissions(p.actionChoices.eo_edit_ez, user, zaznam.ident_cely),
        "smazat": check_permissions(p.actionChoices.ez_smazat, user, zaznam.ident_cely),
        "vypis": check_permissions(p.actionChoices.vypis_ez, user, zaznam.ident_cely),
    }
    return show


def get_required_fields():
    """
    Funkce pro získaní dictionary povinných polí podle stavu externího zdroje.

        :return: Vrací proměnná ``required_fields``.
    """
    required_fields = [
        "typ",
        "autori",
        "rok_vydani_vzniku",
        "nazev",
    ]
    return required_fields


def save_autor_editor(zaznam, form):
    """
    Funkce pro uložení autorů a editorů k externímu zdroji podle toho v jakém pořadí byly zadáni.

    :param zaznam: Parametr ``zaznam`` předává se do volání ``create()``.
    :param form: Parametr ``form`` pracuje se s atributy ``cleaned_data``.
    """
    i = 1
    for autor in form.cleaned_data["autori"]:
        ExterniZdrojAutor.objects.create(
            externi_zdroj=zaznam,
            autor=autor,
            poradi=i,
        )
        i = i + 1
    i = 1
    for editor in form.cleaned_data["editori"]:
        ExterniZdrojEditor.objects.create(
            externi_zdroj=zaznam,
            editor=editor,
            poradi=i,
        )
        i = i + 1


class EzOdkazyTableView(LoginRequiredMixin, View):
    """Třída pohledu pro zobrazení řádků tabulky externích odkazů."""

    def get(self, request, ident_cely):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` předává se do volání ``check_permissions()``, pracuje se s atributy ``GET``, ``user``.
        :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get()``.

            :return: Vrací výsledek volání ``HttpResponse()``.
        """
        card_type = request.GET.get("card_type", False)
        action_type = request.GET.get("type", False)
        zaznam = ExterniZdroj.objects.get(ident_cely=ident_cely)
        ez_odkazy = ExterniOdkaz.objects.filter(externi_zdroj=zaznam)
        if card_type == "akce":
            zaznamy = (
                ez_odkazy.filter(archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_AKCE)
                .select_related("archeologicky_zaznam")
                .select_related("archeologicky_zaznam__akce")
            ).order_by("archeologicky_zaznam__ident_cely")
        elif card_type == "lokalita":
            zaznamy = (
                ez_odkazy.filter(archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA)
                .select_related("archeologicky_zaznam")
                .select_related("archeologicky_zaznam__lokalita")
            ).order_by("archeologicky_zaznam__ident_cely")
        context = {
            "zaznamy": zaznamy,
            "card_type": card_type,
            "type": action_type,
            "show": {
                "paginace": True,
                "paginace_edit": check_permissions(p.actionChoices.eo_edit_ez, request.user, zaznam.ident_cely),
                "odpojit": check_permissions(p.actionChoices.eo_odpojit_akce, request.user, zaznam.ident_cely),
            },
            "zaznam": zaznam,
        }
        return HttpResponse(render_to_string("ez/ez_odkazy_table_only.html", context))
