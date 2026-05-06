import logging

from arch_z.forms import CreateArchZForm
from arch_z.models import ArcheologickyZaznam
from arch_z.views import (
    AkceRelatedRecordUpdateView,
    get_areal_choices,
    get_detail_template_shows,
    get_dj_form_detail,
    get_komponenta_form_detail,
    get_obdobi_choices,
)
from core.constants import AZ_STAV_ZAPSANY, PIAN_POTVRZEN, ZAPSANI_AZ
from core.coordTransform import transform_geom_to_wgs84
from core.ident_cely import get_temp_lokalita_ident
from core.message_constants import (
    LOKALITA_USPESNE_ZAPSANA,
    SPATNY_ZAZNAM_ZAZNAM_VAZBA,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
)
from core.views import SearchListView
from dj.forms import CreateDJForm
from dj.models import DokumentacniJednotka
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView
from fedora_management.decorators import handle_fedora_error
from komponenta.forms import CreateKomponentaForm
from komponenta.models import Komponenta
from pian.forms import PianCreateForm
from pian.models import Pian

from .filters import LokalitaFilter
from .forms import LokalitaForm
from .models import Lokalita
from .tables import LokalitaTable

logger = logging.getLogger(__name__)


class LokalitaIndexView(LoginRequiredMixin, TemplateView):
    """Třida pohledu pro zobrazení domovské stránky lokalit s navigačními možnostmi."""

    template_name = "lokalita/index.html"

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní kontextu podlehu.

        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

            :return: Vrací proměnná ``context``.
        """
        context = {
            "toolbar_name": _("ez.views.lokalitaIndexView.toolbarName"),
            "toolbar_icon": "tour",
        }
        return context


class LokalitaListView(SearchListView):
    """Třida pohledu pro zobrazení listu/tabulky s lokalitami."""

    table_class = LokalitaTable
    model = Lokalita
    filterset_class = LokalitaFilter
    export_name = "export_lokalita_"
    app = "lokalita"
    toolbar = "toolbar_akce.html"
    permission_model_lookup = "archeologicky_zaznam__"
    redis_snapshot_prefix = "lokalita"
    redis_value_list_field = "archeologicky_zaznam__ident_cely"
    typ_zmeny_lookup = ZAPSANI_AZ
    vypis_app = "lokalita"

    def init_translations(self):
        """Provádí operaci init translations."""
        super().init_translations()
        self.page_title = _("lokalita.views.lokalitaListView.pageTitle.text")
        self.search_sum = _("lokalita.views.lokalitaListView.pocetVyhledanych.text")
        self.pick_text = _("lokalita.views.lokalitaListView.pickText.text")
        self.hasOnlyVybrat_header = _("lokalita.views.lokalitaListView.header.hasOnlyVybrat.text")
        self.hasOnlyVlastnik_header = _("lokalita.views.lokalitaListView.header.hasOnlyVlastnik.text")
        self.hasOnlyArchive_header = _("lokalita.views.lokalitaListView.header.hasOnlyArchive.text")
        self.hasOnlyNase_header = _("lokalita.views.lokalitaListView.hasOnlyNase_header.text")
        self.default_header = _("lokalita.views.lokalitaListView.header.default.text")
        self.toolbar_name = _("lokalita.views.lokalitaListView.toolbar.title.text")

    @staticmethod
    def rename_field_for_ordering(field: str):
        """
        Provádí operaci rename field for ordering.

        :param field: Parametr ``field`` předává se do volání ``get()``, pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``get()``.
        """
        field = field.replace("-", "")
        return {
            "ident_cely": "archeologicky_zaznam__ident_cely",
            "pristupnost": "archeologicky_zaznam__pristupnost__razeni",
            "katastr": "archeologicky_zaznam__hlavni_katastr__nazev",
            "okres": "archeologicky_zaznam__hlavni_katastr__okres__nazev",
            "kraj": "archeologicky_zaznam__hlavni_katastr__okres__kraj__nazev",
            "dalsi_katastry": "dalsi_katastry_snapshot",
            "stav": "archeologicky_zaznam__stav",
            "organizace": "organizace__nazev_zkraceny",
            "vedouci_organizace": "vedouci_organizace",
            "vedouci": "vedouci_snapshot",
            "uzivatelske_oznaceni": "archeologicky_zaznam__uzivatelske_oznaceni",
            "zachovalost": "zachovalost__heslo",
            "jistota": "jistota__heslo",
            "druh": "druh__heslo",
            "typ_lokality": "typ_lokality__heslo",
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
        qs = qs.select_related(
            "druh",
            "typ_lokality",
            "zachovalost",
            "jistota",
            "archeologicky_zaznam__hlavni_katastr",
            "archeologicky_zaznam__hlavni_katastr__okres",
            "archeologicky_zaznam__hlavni_katastr__okres__kraj",
            "archeologicky_zaznam",
            "archeologicky_zaznam__pristupnost",
        ).prefetch_related("archeologicky_zaznam__katastry", "archeologicky_zaznam__katastry__okres")
        return self.check_filter_permission(qs)

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["toolbar_icon"] = "tour"
        context["type"] = "lokalita"
        return context


class LokalitaDetailView(LoginRequiredMixin, SingleObjectMixin, AkceRelatedRecordUpdateView):
    """Třida pohledu pro zobrazení detailu lokality."""

    model = Lokalita
    template_name = "lokalita/lokalita_detail.html"
    slug_field = "archeologicky_zaznam__ident_cely"

    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

            :return: Vrací výsledek volání ``render_to_response()``.
        """
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_archeologicky_zaznam(self):
        """
        Metoda pro získaní akce z db.

        :return: Vrací atribut objektu.
        """
        return self.object.archeologicky_zaznam

    def check_locality_arch_z_conflict(self):
        """Ověří locality arch z conflict."""
        return

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní contextu akci pro template.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        self.object = self.get_object()
        context = super().get_context_data(**kwargs)
        context["warnings"] = self.request.session.pop("temp_data", None)
        context["page_title"] = _("lokalita.views.lokalitaDetailView.pageTitle")
        context["detail_view"] = True
        context["form"] = LokalitaForm(instance=self.object, readonly=True, required=False, detail=True)
        context["arch_z_form"] = CreateArchZForm(instance=self.arch_zaznam, readonly=True, required=False)
        return context

    def get_shows(self):
        """
        Vrací shows. v aplikaci.

        :return: Vrací výsledek volání ``get_detail_template_shows()``.
        """
        return get_detail_template_shows(
            self.get_object().archeologicky_zaznam,
            self.get_jednotky(),
            self.request.user,
            app="lokalita",
        )


class LokalitaCreateView(LoginRequiredMixin, CreateView):
    """Třida pohledu pro vytvoření lokality."""

    model = Lokalita
    template_name = "lokalita/create.html"
    form_class = LokalitaForm

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        logger.debug("context is called")
        required_fields = get_required_fields()
        required_fields_next = get_required_fields(next=1)
        context["form"] = LokalitaForm(
            data=self.request.POST if self.request.POST else None,
            required=required_fields,
            required_next=required_fields_next,
        )
        context["arch_z_form"] = CreateArchZForm(
            data=self.request.POST if self.request.POST else None,
            required=required_fields,
            required_next=required_fields_next,
        )
        context["toolbar_name"] = _("lokalita.views.lokalitaCreateView.toolbar.title")
        context["header"] = _("lokalita.views.lokalitaCreateView.formHeader.label")
        context["page_title"] = _("lokalita.views.lokalitaCreateView.pageTitle")
        context["submit_button"] = _("lokalita.views.lokalitaCreateView.submitButton")
        context["toolbar_label"] = _("lokalita.views.lokalitaCreateView.toolbar_label.title")
        return context

    def form_valid(self, form):
        """
        Validuje data ve formuláři

        :param form: Instance vyplněného formuláře.
        :return: HTTP odpověď.
        """
        logger.debug("lokalita.views.LokalitaCreateView.form_valid.start")
        form_az = CreateArchZForm(self.request.POST)
        if form_az.is_valid():
            az = form_az.save(commit=False)
            az: ArcheologickyZaznam
            fedora_transaction = az.create_transaction(self.request.user, LOKALITA_USPESNE_ZAPSANA)
            logger.debug(
                "lokalita.views.LokalitaCreateView.form_valid.true",
                extra={"transaction": getattr(fedora_transaction, "uid", None)},
            )
            az.stav = AZ_STAV_ZAPSANY
            az.typ_zaznamu = ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
            lokalita = form.save(commit=False)
            lokalita.active_transaction = fedora_transaction
            az.save()
            form_az.save_m2m()
            region = az.hlavni_katastr.okres.kraj.rada_id
            typ = lokalita.typ_lokality.zkratka
            az.ident_cely = get_temp_lokalita_ident(typ, region)
            az.save()
            az.set_zapsany(self.request.user)
            lokalita.archeologicky_zaznam = az
            lokalita.save()

            az.close_active_transaction_when_finished = True
            az.save()

            logger.debug(f"arch_z.views.zapsat: {LOKALITA_USPESNE_ZAPSANA}, ID akce: {lokalita.pk}.")
        else:
            logger.debug(form_az.errors)
            self.form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Informuje uživatele o nevalidním vyplnění formuláře a zaloguje ho.

        :param form: Instance vyplněného formuláře.
        :return: HTTP odpověď.
        """
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)
        logger.debug("main form is invalid")
        logger.debug(form.errors)
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

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``post()``, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``post()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``post()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``post()``.
        """
        return super().post(request, *args, **kwargs)


class LokalitaEditView(LoginRequiredMixin, UpdateView):
    """Třida pohledu pro editaci lokality."""

    model = Lokalita
    template_name = "lokalita/create.html"
    form_class = LokalitaForm
    slug_field = "archeologicky_zaznam__ident_cely"

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        required_fields = get_required_fields()
        logger.debug(required_fields[0:-1])
        required_fields_next = get_required_fields(next=1)
        context["form"] = LokalitaForm(
            instance=self.object,
            required=required_fields[0:-1],
            required_next=required_fields_next,
        )
        context["arch_z_form"] = CreateArchZForm(
            instance=self.object.archeologicky_zaznam,
            required=required_fields[0:-1],
            required_next=required_fields_next,
        )
        context["toolbar_name"] = _("lokalita.views.lokalitaEditView.toolbar.title")
        context["edit_view"] = True
        context["page_title"] = _("lokalita.views.lokalitaEditView.pageTitle")
        context["header"] = _("lokalita.views.lokalitaEditView.formHeader.label")
        context["zaznam"] = self.object.archeologicky_zaznam
        context["submit_button"] = _("lokalita.views.LokalitaEditView.submitButton")
        return context

    def form_valid(self, form):
        """
        Informuje uživatele o nevalidním vyplnění formuláře a zaloguje ho.

        :param form: Instance vyplněného formuláře.
        :return: HTTP odpověď.
        """
        logger.debug("Lokalita.EditForm is valid")
        form_az = CreateArchZForm(self.request.POST, instance=self.object.archeologicky_zaznam)
        form_az_valid = form_az.is_valid()
        conflicting_fields = form.get_conflicting_fields() + (form_az.get_conflicting_fields() if form_az_valid else [])
        if conflicting_fields:
            conflicting_labels = list(
                dict.fromkeys(str(form.fields[f].label) for f in conflicting_fields if f in form.fields)
            )
            conflicting_labels += list(
                dict.fromkeys(str(form_az.fields[f].label) for f in conflicting_fields if f in form_az.fields)
            )
            context = self.get_context_data(form=form)
            context["concurrent_changes"] = conflicting_labels
            context["fresh_form_url"] = reverse(
                "lokalita:edit", kwargs={"slug": self.object.archeologicky_zaznam.ident_cely}
            )
            return self.render_to_response(context)
        if form_az_valid:
            logger.debug("Lokalita.EditFormAz is valid")
            az = form_az.save(commit=False)
            az: ArcheologickyZaznam
            fedora_transaction = az.create_transaction(self.request.user)
            az.active_transaction = fedora_transaction
            az.close_active_transaction_when_finished = True
            az.save()
            form_az.save_m2m()
        else:
            logger.debug("AZ form is invalid")
            logger.debug(form_az.errors)
            self.form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Informuje uživatele o nevalidním vyplnění formuláře a zaloguje ho.

        :param form: Instance vyplněného formuláře.
        :return: HTTP odpověď.
        """
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        logger.debug("main form is invalid")
        logger.debug(form.errors)
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

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``post()``, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``post()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``post()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``post()``.
        """
        return super().post(request, *args, **kwargs)


class LokalitaRelatedView(LokalitaDetailView):
    """Třida pohledu pro získaní relací lokality, která je dedená v dalších pohledech."""

    model = Lokalita
    slug_field = "archeologicky_zaznam__ident_cely"


class LokalitaDokumentacniJednotkaCreateView(LokalitaRelatedView):
    """Třida pohledu pro vytvoření dokumentační jednotky lokality."""

    template_name = "lokalita/dj/dj_create.html"

    def get_context_data(self, **kwargs):
        """
        Zpracuje dispečing požadavku.

        :param request: HTTP požadavek.
        :param args: Poziční argumenty.
        :param kwargs: Pojmenované argumenty.
        :return: HTTP odpověď.
        """
        context = super().get_context_data(**kwargs)
        context["dj_form_create"] = CreateDJForm(typ_arch_z=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA)
        return context


class LokalitaDokumentacniJednotkaRelatedView(LokalitaRelatedView):
    """
    Třida pohledu pro získaní dokumentačních jednotek lokality, která je dedená v dalších pohledech.
    """

    scroll_to_dj = True

    def dispatch(self, request, *args, **kwargs):
        """
        Provádí operaci dispatch.

        :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``dispatch()``.
        """
        dj = get_object_or_404(DokumentacniJednotka, ident_cely=self.kwargs["dj_ident_cely"])
        az = self.get_object().archeologicky_zaznam
        if not dj.archeologicky_zaznam == az:
            logger.error("Archeologicky zaznam - Dokumentacni jednotka wrong relation")
            messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
            if url_has_allowed_host_and_scheme(
                request.GET.get("next", "core:home"), allowed_hosts=settings.ALLOWED_HOSTS
            ):
                safe_redirect = request.GET.get("next", "core:home")
            else:
                safe_redirect = "/"
            return redirect(safe_redirect)
        return super().dispatch(request, *args, **kwargs)

    def get_dokumentacni_jednotka(self):
        """
        Vrací dokumentacni jednotka.

        :return: Vrací proměnná ``object``.
        """
        dj_ident_cely = self.kwargs["dj_ident_cely"]
        logger.debug(
            "arch_z.views.DokumentacniJednotkaUpdateView.get_object",
            extra={"ident_cely": dj_ident_cely},
        )
        object = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
        return object

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["dj_ident_cely"] = self.get_dokumentacni_jednotka().ident_cely
        return context


class LokalitaDokumentacniJednotkaUpdateView(LokalitaDokumentacniJednotkaRelatedView):
    """Třida pohledu pro editaci dokumentační jednotky lokality."""

    template_name = "lokalita/dj/dj_update.html"

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["j"] = get_dj_form_detail(
            "lokalita",
            self.get_dokumentacni_jednotka(),
            show=self.get_shows(),
            user=self.request.user,
            session=self.request.session,
        )
        return context


class LokalitaKomponentaCreateView(LokalitaDokumentacniJednotkaRelatedView):
    """Třida pohledu pro vytvoření komponenty lokality."""

    template_name = "lokalita/dj/komponenta_create.html"

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["komponenta_form_create"] = CreateKomponentaForm(get_obdobi_choices(), get_areal_choices())
        context["j"] = self.get_dokumentacni_jednotka()
        return context

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        """
        Zpracuje dispečing požadavku.

        :param request: HTTP požadavek.
        :param args: Poziční argumenty.
        :param kwargs: Pojmenované argumenty.
        :return: HTTP odpověď.
        """
        return super().get(request, *args, **kwargs)


class LokalitaKomponentaUpdateView(LokalitaDokumentacniJednotkaRelatedView):
    """Třida pohledu pro editaci komponenty lokality."""

    template_name = "lokalita/dj/komponenta_detail.html"

    def dispatch(self, request, *args, **kwargs):
        """
        Provádí operaci dispatch.

        :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``dispatch()``.
        """
        dj = get_object_or_404(DokumentacniJednotka, ident_cely=self.kwargs["dj_ident_cely"])
        komponenta = get_object_or_404(Komponenta, ident_cely=self.kwargs["komponenta_ident_cely"])
        if not dj.komponenty == komponenta.komponenta_vazby:
            logger.warning("Komponenta - Dokumentacni jednotka wrong relation")
            messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
            if url_has_allowed_host_and_scheme(
                request.GET.get("next", "core:home"), allowed_hosts=settings.ALLOWED_HOSTS
            ):
                safe_redirect = request.GET.get("next", "core:home")
            else:
                safe_redirect = "/"
            return redirect(safe_redirect)
        return super().dispatch(request, *args, **kwargs)

    def get_komponenta(self):
        """
        Vrací komponenta. v aplikaci.

        :return: Vrací proměnná ``object``.
        """
        dj_ident_cely = self.kwargs["komponenta_ident_cely"]
        object = get_object_or_404(Komponenta, ident_cely=dj_ident_cely)
        return object

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        komponenta = self.get_komponenta()
        old_nalez_post = self.request.session.pop("_old_nalez_post", None)
        komp_ident_cely = self.request.session.pop("komp_ident_cely", None)
        show = self.get_shows()
        context["k"] = get_komponenta_form_detail(
            komponenta, show, old_nalez_post, komp_ident_cely, session=self.request.session
        )
        context["j"] = self.get_dokumentacni_jednotka()
        context["active_komp_ident"] = komponenta.ident_cely
        return context


class LokalitaPianCreateView(LokalitaDokumentacniJednotkaRelatedView):
    """Třida pohledu pro vytvoření pianu dokumentační jednotky lokality."""

    template_name = "lokalita/dj/pian_create.html"

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["pian_form_create"] = PianCreateForm(dj=self.get_dokumentacni_jednotka())
        return context

    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` předává se do volání ``get()``, ``str()``, pracuje se s atributy ``user``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render_to_response()``.
            :raises Exception: Vyvolá se s textem "lokalita.views.LokalitaPianCreateView.get.label_not_found"; nebo s textem "lokalita.views.LokalitaPianCreateView.get.transormation_error".
        """
        context = self.get_context_data(**kwargs)
        if "index" in self.request.GET and "label" in self.request.GET:
            try:
                geom = cache.get(str(request.user.id) + "_geom")
                index = int(self.request.GET["index"])
                if self.request.GET["label"] != str(geom.iloc[index]["label"]):
                    raise Exception("lokalita.views.LokalitaPianCreateView.get.label_not_found")
                context["geom"] = geom.iloc[index].copy()
                if context["geom"]["epsg"] == "5514" or context["geom"]["epsg"] == 5514:
                    context["geom"]["geometry"], stat = transform_geom_to_wgs84(context["geom"]["geometry"])
                    if stat != "OK":
                        raise Exception("lokalita.views.LokalitaPianCreateView.get.transormation_error")
            except Exception as err:
                logger.error("lokalita.views.LokalitaPianCreateView.get.import_pian.error", extra={"error": err})
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    _("lokalita.views.LokalitaDokumentacniJednotkaRelatedView.import_pian.error"),
                )
                return redirect(
                    reverse("lokalita:detail-dj", args=[self.arch_zaznam.ident_cely, context["dj_ident_cely"]])
                )
        return self.render_to_response(context)


class LokalitaPianUpdateView(LokalitaDokumentacniJednotkaRelatedView):
    """Třida pohledu pro editaci pianu dokumentační jednotky lokality."""

    template_name = "lokalita/dj/pian_update.html"

    def dispatch(self, request, *args, **kwargs):
        """
        Provádí operaci dispatch.

        :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``dispatch()``.
        """
        dj = get_object_or_404(DokumentacniJednotka, ident_cely=self.kwargs["dj_ident_cely"])
        pian = get_object_or_404(Pian, ident_cely=self.kwargs["pian_ident_cely"])
        if not dj.pian == pian:
            logger.error("Pian - Dokumentacni jednotka wrong relation")
            messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
            if url_has_allowed_host_and_scheme(
                request.GET.get("next", "core:home"), allowed_hosts=settings.ALLOWED_HOSTS
            ):
                safe_redirect = request.GET.get("next", "core:home")
            else:
                safe_redirect = "/"
            return redirect(safe_redirect)
        return super().dispatch(request, *args, **kwargs)

    def get_pian(self):
        """
        Vrací pian. v aplikaci.

        :return: Vrací výsledek volání ``get_object_or_404()``.
        """
        pian_ident_cely = self.kwargs["pian_ident_cely"]
        return get_object_or_404(Pian, ident_cely=pian_ident_cely)

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        self.pian = self.get_pian()
        pian_ident_cely = self.pian.ident_cely
        context["pian_ident_cely"] = pian_ident_cely
        context["pian_form_update"] = PianCreateForm(instance=self.pian, dj=self.get_dokumentacni_jednotka())
        context["pian_concurrent_changes"] = self.request.session.pop(
            f"pian_concurrent_changes_{pian_ident_cely}", None
        )
        context["pian_fresh_form_url"] = self.request.path
        return context

    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` předává se do volání ``get()``, ``str()``, pracuje se s atributy ``user``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render_to_response()``.
            :raises PermissionDenied: Vyvolá se při splnění podmínky ``self.pian == PIAN_POTVRZEN``.
            :raises Exception: Vyvolá se s textem "lokalita.views.LokalitaPianUpdateView.get.label_not_found"; nebo s textem "lokalita.views.LokalitaPianUpdateView.get.transormation_error".
        """
        context = self.get_context_data(**kwargs)
        if self.pian == PIAN_POTVRZEN:
            raise PermissionDenied
        if "index" in self.request.GET and "label" in self.request.GET:
            try:
                geom = cache.get(str(request.user.id) + "_geom")
                index = int(self.request.GET["index"])
                if self.request.GET["label"] != str(geom.iloc[index]["label"]):
                    raise Exception("lokalita.views.LokalitaPianUpdateView.get.label_not_found")
                context["geom"] = geom.iloc[index].copy()
                if context["geom"]["epsg"] == "5514" or context["geom"]["epsg"] == 5514:
                    context["geom"]["geometry"], stat = transform_geom_to_wgs84(context["geom"]["geometry"])
                    if stat != "OK":
                        raise Exception("lokalita.views.LokalitaPianUpdateView.get.transormation_error")
            except Exception as err:
                logger.error("lokalita.views.LokalitaPianUpdateView.get.import_pian.error", extra={"error": err})
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    _("lokalita.views.LokalitaDokumentacniJednotkaRelatedView.import_pian.error"),
                )
                return redirect(
                    reverse("lokalita:detail-dj", args=[self.arch_zaznam.ident_cely, context["dj_ident_cely"]])
                )
        return self.render_to_response(context)


def get_required_fields(zaznam=None, next=0):
    """
    Funkce pro získaní dictionary povinných polí podle stavu lokality.

    :param zaznam: Parametr ``zaznam`` pracuje se s atributy ``stav``, ovlivňuje větvení podmínek.
    :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
    :return: Seznam názvů polí, která mají být v daném stavu povinná.
    """
    required_fields = []
    if zaznam:
        stav = zaznam.stav
    else:
        stav = 1
    if stav >= AZ_STAV_ZAPSANY - next:
        required_fields = [
            "typ_lokality",
            "druh",
            "nazev",
            "pristupnost",
            "hlavni_katastr",
        ]
    return required_fields
