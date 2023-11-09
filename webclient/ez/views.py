import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import View


from core.views import PermissionFilterMixin, SearchListView, check_stav_changed
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext as _
from django.views.generic import DetailView, TemplateView
from django.contrib import messages
from django.views.generic.edit import CreateView, UpdateView
from django.template.loader import render_to_string
from django.utils.http import url_has_allowed_host_and_scheme
from dal import autocomplete
from core.constants import (
    AZ_STAV_ARCHIVOVANY,
    AZ_STAV_ODESLANY,
    AZ_STAV_ZAPSANY,
    EZ_STAV_ODESLANY,
    EZ_STAV_POTVRZENY,
    EZ_STAV_ZAPSANY,
    ODESLANI_EXT_ZD,
    POTVRZENI_EXT_ZD,
    ZAPSANI_EXT_ZD, ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID,
)

from core.forms import CheckStavNotChangedForm, VratitForm
from core.message_constants import (
    EO_USPESNE_ODPOJEN,
    EZ_USPESNE_ODESLAN,
    EZ_USPESNE_POTVRZEN,
    EZ_USPESNE_VRACENA,
    EZ_USPESNE_ZAPSAN,
    PRISTUP_ZAKAZAN,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN, ZAZNAM_NELZE_SMAZAT_FEDORA,
)
from core.models import Permissions as p, check_permissions
from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
from core.utils import get_message
from core.ident_cely import get_temp_ez_ident
from .filters import ExterniZdrojFilter

# from .forms import LokalitaForm
from .models import ExterniZdroj, ExterniZdrojAutor, ExterniZdrojEditor
from .tables import ExterniZdrojTable
from .forms import (
    ExterniOdkazForm,
    ExterniZdrojForm,
    PripojitArchZaznamForm,
    PripojitExterniOdkazForm,
)
from django.db.models import Prefetch

from uzivatel.models import Osoba, User

logger = logging.getLogger(__name__)


class ExterniZdrojIndexView(LoginRequiredMixin, TemplateView):
    """
    Třida pohledu pro zobrazení domovské stránky externích zdrojů s navigačními možnostmi.
    """
    template_name = "ez/index.html"

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní kontextu podlehu.
        """
        context = {
            "toolbar_name": _("ez.views.externiZdrojIndexView.toolbarName"),
        }
        return context


class ExterniZdrojListView(SearchListView):
    """
    Třida pohledu pro zobrazení listu/tabulky s externím zdrojem.
    """
    table_class = ExterniZdrojTable
    model = ExterniZdroj
    filterset_class = ExterniZdrojFilter
    export_name = "export_externi-zdroje_"
    page_title = _("ez.templates.ExterniZdrojListView.pageTitle.text")
    app = "ext_zdroj"
    toolbar = "toolbar_externi_zdroj.html"
    search_sum = _("ez.templates.ExterniZdrojListView.search_sum.text")
    pick_text = _("ez.templates.ExterniZdrojListView.pickText.text")
    hasOnlyVybrat_header = _("ez.templates.ExterniZdrojListView.hasOnlyVybrat_header.text")
    hasOnlyVlastnik_header = _("ez.templates.ExterniZdrojListView.hasOnlyVlastnik_header.text")
    hasOnlyArchive_header = _("ez.templates.ExterniZdrojListView.hasOnlyPotvrdit_header.text")
    hasOnlyPotvrdit_header = _("ez.templates.ExterniZdrojListView.hasOnlyPotvrdit_header.text")
    default_header = _("ez.templates.ExterniZdrojListView.header.default_header.text")
    toolbar_name = _("ez.templates.ExterniZdrojListView.toolbar_name.text")
    typ_zmeny_lookup = ZAPSANI_EXT_ZD

    def get_queryset(self):
        qs = super().get_queryset()
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
            "autori"
        )
        return self.check_filter_permission(qs)
    
    def add_accessibility_lookup(self,permission, qs):
        return qs


class ExterniZdrojDetailView(LoginRequiredMixin, DetailView):
    """
    Třida pohledu pro zobrazení detailu externího zdroju.
    """
    model = ExterniZdroj
    template_name = "ez/detail.html"
    slug_field = "ident_cely"

    def get_context_data(self, **kwargs):
        context = {}
        zaznam = self.get_object()
        ez_odkazy = ExterniOdkaz.objects.filter(externi_zdroj=zaznam)
        ez_akce = (
            ez_odkazy.filter(
                archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
            )
            .select_related("archeologicky_zaznam")
            .select_related("archeologicky_zaznam__akce")
        ).order_by("archeologicky_zaznam__ident_cely")
        ez_lokality = (
            ez_odkazy.filter(
                archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
            )
            .select_related("archeologicky_zaznam")
            .select_related("archeologicky_zaznam__lokalita")
        ).order_by("archeologicky_zaznam__ident_cely")
        context["form"] = ExterniZdrojForm(
            instance=zaznam, readonly=True, required=False
        )
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
    """
    Třida pohledu pro vytvoření externího zdroje.
    """
    model = ExterniZdroj
    template_name = "ez/create.html"
    form_class = ExterniZdrojForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        required_fields = get_required_fields()
        kwargs.update({"required": required_fields, "required_next": required_fields})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["toolbar_name"] = _("ez.templates.ExterniZdrojCreateView.toolbar.title")
        context["page_title"] = _("ez.templates.ExterniZdrojCreateView.pageTitle")
        context["header"] = _("ez.templates.ExterniZdrojCreateView.formHeader.label")
        return context

    def form_valid(self, form):
        ez = form.save(commit=False)
        ez.stav = EZ_STAV_ZAPSANY
        ez.ident_cely = get_temp_ez_ident()
        ez.save()
        save_autor_editor(ez, form)
        ez.set_zapsany(self.request.user)
        messages.add_message(self.request, messages.SUCCESS, EZ_USPESNE_ZAPSAN)
        return HttpResponseRedirect(ez.get_absolute_url())

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)
        logger.debug("ez.views.ExterniZdrojCreateView.form_invalid", extra={"form_errors": form.errors})
        return super().form_invalid(form)


class ExterniZdrojEditView(LoginRequiredMixin, UpdateView):
    """
    Třida pohledu pro editaci externího zdroje.
    """
    model = ExterniZdroj
    template_name = "ez/create.html"
    form_class = ExterniZdrojForm
    slug_field = "ident_cely"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        required_fields = get_required_fields()
        kwargs.update({"required": required_fields, "required_next": required_fields})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["zaznam"] = self.object
        context["toolbar_name"] = _("ez.templates.ExterniZdrojEditView.toolbar.title")
        context["page_title"] = _("ez.templates.ExterniZdrojEditView.pageTitle")
        context["header"] = _("ez.templates.ExterniZdrojEditView.formHeader.label")
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.autori.clear()
        self.object.editori.clear()
        self.object.save()
        save_autor_editor(self.object, form)
        messages.add_message(self.request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        logger.debug("ez.views.ExterniZdrojEditView.form_invalid", extra={"form_errors": form.errors})
        return super().form_invalid(form)


class TransakceView(LoginRequiredMixin, TemplateView):
    """
    Třida pohledu pro změnu stavu a práci s externíma zdrojama cez modal, která se dedí pro jednotlivá změny.
    """
    template_name = "core/transakce_modal.html"
    title = "title"
    id_tag = "id_tag"
    button = "button"
    allowed_states = []
    success_message = "success"
    action = ""

    def get_zaznam(self):
        ident_cely = self.kwargs.get("ident_cely")
        logger.debug("ez.views.TransakceView.get_zaznam.start", extra={"ident_cely": ident_cely})
        return get_object_or_404(
            ExterniZdroj,
            ident_cely=ident_cely,
        )

    def get_context_data(self, **kwargs):
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
        zaznam = self.get_zaznam()
        if zaznam.stav not in self.allowed_states:
            logger.debug("ez.views.TransakceView.dispatch.start", extra={"action": self.action})
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
        context = self.get_context_data(**kwargs)
        zaznam = context["object"]
        getattr(ExterniZdroj, self.action)(zaznam, request.user)
        messages.add_message(request, messages.SUCCESS, self.success_message)

        return JsonResponse({"redirect": zaznam.get_absolute_url()})


class ExterniZdrojOdeslatView(TransakceView):
    """
    Třida pohledu pro odeslání externího zdroje pomoci modalu.
    """
    title = _("ez.templates.ExterniZdrojOdeslatView.title.text")
    id_tag = "odeslat-ez-form"
    button = _("ez.templates.ExterniZdrojOdeslatView.submitButton.text")
    allowed_states = [EZ_STAV_ZAPSANY]
    success_message = EZ_USPESNE_ODESLAN
    action = "set_odeslany"


class ExterniZdrojPotvrditView(TransakceView):
    """
    Třida pohledu pro potvrzení externího zdroje pomoci modalu.
    """
    title = _("ez.templates.ExterniZdrojPotvrditView.title.text")
    id_tag = "potvrdit-ez-form"
    button = _("ez.templates.ExterniZdrojPotvrditView.submitButton.text")
    allowed_states = [EZ_STAV_ODESLANY]
    success_message = EZ_USPESNE_POTVRZEN
    action = "set_potvrzeny"


class ExterniZdrojSmazatView(TransakceView):
    """
    Třida pohledu pro smazání externího zdroje pomoci modalu.
    """
    title = _("ez.templates.ExterniZdrojSmazatView.title.text")
    id_tag = "smazat-ez-form"
    button = _("ez.templates.ExterniZdrojSmazatView.submitButton.text")
    allowed_states = [EZ_STAV_ODESLANY, EZ_STAV_POTVRZENY, EZ_STAV_ZAPSANY]
    success_message = ZAZNAM_USPESNE_SMAZAN

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        zaznam = context["object"]
        zaznam.deleted_by_user = request.user
        if hasattr(zaznam, "container_creation_queued") and zaznam.container_creation_queued():
            messages.add_message(request, messages.ERROR, ZAZNAM_NELZE_SMAZAT_FEDORA)
            return JsonResponse({"redirect": zaznam.get_absolute_url()}, status=403)
        historie_vazby = zaznam.historie
        for eo in zaznam.externi_odkazy_zdroje.all():
            eo.delete()
        zaznam.delete()
        historie_vazby.delete()
        messages.add_message(request, messages.SUCCESS, self.success_message)
        return JsonResponse({"redirect": reverse("ez:index")})


class ExterniZdrojVratitView(TransakceView):
    """
    Třida pohledu pro vrácení externího zdroje pomoci modalu.
    """
    title = _("ez.templates.ExterniZdrojVratitView.title.text")
    id_tag = "vratit-ez-form"
    button = _("ez.templates.ExterniZdrojVratitView.submitButton.text")
    allowed_states = [EZ_STAV_ODESLANY, EZ_STAV_POTVRZENY]
    success_message = EZ_USPESNE_VRACENA
    action = "set_vraceny"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        form = VratitForm(initial={"old_stav": context["object"].stav})
        context["form"] = form
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        zaznam = context["object"]
        form = VratitForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            getattr(ExterniZdroj, self.action)(
                zaznam, request.user, zaznam.stav - 1, duvod
            )
            messages.add_message(request, messages.SUCCESS, self.success_message)

            return JsonResponse({"redirect": zaznam.get_absolute_url()})
        else:
            logger.debug("ez.views.ExterniZdrojVratitView.form_invalid", extra={"form_errors": form.errors})
            return self.render_to_response(context)


class ExterniOdkazOdpojitView(TransakceView):
    """
    Třida pohledu pro odpojení externího odkazu pomoci modalu.
    """
    title = _("ez.templates.ExterniOdkazOdpojitView.title.text")
    id_tag = "odpojit-az-form"
    button = _("ez.templates.ExterniOdkazOdpojitView.submitButton.text")
    allowed_states = [EZ_STAV_ODESLANY, EZ_STAV_POTVRZENY, EZ_STAV_ZAPSANY]
    success_message = EO_USPESNE_ODPOJEN

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = get_object_or_404(
            ArcheologickyZaznam,
            externi_odkazy__id=self.kwargs.get("eo_id"),
        )
        return context

    def post(self, request, *args, **kwargs):
        ez = self.get_zaznam()
        eo = ExterniOdkaz.objects.get(id=self.kwargs.get("eo_id"))
        eo.delete()
        messages.add_message(request, messages.SUCCESS, self.success_message)
        return JsonResponse({"redirect": ez.get_absolute_url()})


class ExterniOdkazPripojitView(TransakceView):
    """
    Třida pohledu pro připojení externího odkazu pomoci modalu.
    """
    template_name = "core/transakce_table_modal.html"
    title = _("ez.templates.ExterniOdkazPripojitView.title.text")
    id_tag = "pripojit-eo-form"
    button = _("ez.templates.ExterniOdkazPripojitView.submitButton.text")
    allowed_states = [EZ_STAV_ODESLANY, EZ_STAV_POTVRZENY, EZ_STAV_ZAPSANY]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        type_arch = self.request.GET.get("type")
        form = PripojitArchZaznamForm(type_arch=type_arch)
        context["form"] = form
        context["hide_table"] = True
        context["type"] = type_arch
        context["card_type"] = type_arch
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        logger.debug("ez.views.ExterniOdkazPripojitView.post.start", extra={"kwargs": self.kwargs})
        ez = self.get_zaznam()
        form = PripojitArchZaznamForm(data=request.POST, type_arch=context["type"])
        if form.is_valid():
            logger.debug("ez.views.ExterniOdkazPripojitView.post.form_valid")
            arch_z_id = form.cleaned_data["arch_z"]
            arch_z = ArcheologickyZaznam.objects.get(id=arch_z_id)
            eo = ExterniOdkaz.objects.create(
                externi_zdroj=ez,
                paginace=form.cleaned_data["paginace"],
                archeologicky_zaznam=arch_z,
            )
            eo.save()
            messages.add_message(
                request, messages.SUCCESS, get_message(arch_z, "EO_USPESNE_PRIPOJEN")
            )
        else:
            logger.debug("ez.views.ExterniOdkazPripojitView.post.form_error", extra={"form_errors": form.errors})
        return JsonResponse({"redirect": ez.get_absolute_url()})


class ExterniOdkazEditView(LoginRequiredMixin, UpdateView):
    """
    Třida pohledu pro editaci externího odkazu pomoci modalu.
    """
    model = ExterniOdkaz
    template_name = "core/transakce_modal.html"
    title = _("ez.templates.ExterniOdkazEditView.title.text")
    id_tag = "zmenit-eo-form"
    button = _("ez.templates.ExterniOdkazEditView.submitButton.text")
    allowed_states = []
    success_message = "success"
    form_class = ExterniOdkazForm
    slug_field = "id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zaznam = self.object
        context = {
            "object": zaznam,
            "title": self.title,
            "id_tag": self.id_tag,
            "button": self.button,
        }
        context["form"] = ExterniOdkazForm(
            instance=self.object,
        )
        return context

    def get_success_url(self):
        next_url = self.request.GET.get("next_url")
        if next_url:
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
                response = next_url
        else:
            response = self.get_context_data()[
                "object"
            ].externi_zdroj.get_absolute_url()
        return response

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return JsonResponse({"redirect": self.get_success_url()})

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        logger.debug("ez.views.ExterniOdkazEditView.form_invalid", extra={"errors": form.errors})
        return super().form_invalid(form)


class ExterniOdkazOdpojitAZView(TransakceView):
    """
    Třida pohledu pro odpojení externího odkazu z archeologického záznamu pomoci modalu.
    """
    id_tag = "odpojit-az-form"
    allowed_states = [AZ_STAV_ODESLANY, AZ_STAV_ZAPSANY, AZ_STAV_ARCHIVOVANY]
    success_message = EO_USPESNE_ODPOJEN

    def get_zaznam(self):
        ident_cely = self.kwargs.get("ident_cely")
        logger.debug("ez.views.TransakceView.ExterniOdkazOdpojitAZView.start", extra={"ident_cely": ident_cely})
        return get_object_or_404(
            ArcheologickyZaznam,
            ident_cely=ident_cely,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        logger.debug("ez.views.TransakceView.ExterniOdkazOdpojitAZView.get_context_data",
                     extra={"eo_id": self.kwargs.get("eo_id")})
        context["object"] = ExterniZdroj.objects.get(
            externi_odkazy_zdroje__id=self.kwargs.get("eo_id")
        )
        if self.get_zaznam().typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            context["title"] = _("ez.templates.ExterniOdkazOdpojitAZView.arch_z.title.text")
            context["button"] = _("ez.templates.ExterniOdkazOdpojitAZView.arch_z.submitButton.text")
        else:
            context["title"] = _("ez.templates.ExterniOdkazOdpojitAZView.lokalita.title.text")
            context["button"] = _("lokaez.templateslita.ExterniOdkazOdpojitAZView.lokalita.submitButton.text")
        return context

    def post(self, request, *args, **kwargs):
        az = self.get_zaznam()
        eo = ExterniOdkaz.objects.get(id=self.kwargs.get("eo_id"))
        eo.delete()
        messages.add_message(
            request, messages.SUCCESS, get_message(az, "EO_USPESNE_ODPOJEN")
        )
        return JsonResponse({"redirect": az.get_absolute_url()})


class ExterniZdrojAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView,PermissionFilterMixin):
    """
    Třída pohledu pro autocomplete externích zdrojů.
    """
    typ_zmeny_lookup = ZAPSANI_EXT_ZD

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return ExterniZdroj.objects.none()

        qs = ExterniZdroj.objects.filter()
        if self.q:
            qs = qs.filter(ident_cely__icontains=self.q)
        return self.check_filter_permission(qs)
    
    def add_accessibility_lookup(self,permission, qs):
        return qs


class ExterniZdrojTableRowView(LoginRequiredMixin, View):
    """
    Třída pohledu pro získaní řádku tabulky s externím zdrojem.
    """
    def get(self, request):
        zaznam = ExterniZdroj.objects.get(id=request.GET.get("id", ""))
        context = {"ez": zaznam}
        context["hide_paginace"] = True
        return HttpResponse(render_to_string("ez/az_ez_odkazy_table_row.html", context))


class ExterniOdkazPripojitDoAzView(TransakceView):
    """
    Třída pohledu pro připojení externího odkazu do arch záznamu.
    """
    template_name = "core/transakce_table_modal.html"
    title = _("ez.templates.ExterniOdkazPripojitDoAzView.title.text")
    id_tag = "pripojit-eo-doaz-form"
    button = _("ez.templates.ExterniOdkazPripojitDoAzView.submitButton.text")
    allowed_states = [EZ_STAV_ODESLANY, EZ_STAV_POTVRZENY, EZ_STAV_ZAPSANY]

    def get_zaznam(self):
        ident_cely = self.kwargs.get("ident_cely")
        return get_object_or_404(
            ArcheologickyZaznam,
            ident_cely=ident_cely,
        )

    def get_context_data(self, **kwargs):
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

    def post(self, request, *args, **kwargs):
        az = self.get_zaznam()
        form = PripojitExterniOdkazForm(data=request.POST)
        if form.is_valid():
            ez_id = form.cleaned_data["ez"]
            ez = ExterniZdroj.objects.get(id=ez_id)
            eo = ExterniOdkaz.objects.create(
                externi_zdroj=ez,
                paginace=form.cleaned_data["paginace"],
                archeologicky_zaznam=az,
            )
            eo.save()
            messages.add_message(
                request, messages.SUCCESS, get_message(az, "EO_USPESNE_PRIPOJEN")
            )
        else:
            logger.debug("ez.views.ExterniOdkazPripojitDoAzView.form_invalid", extra={"errors": form.errors})
        return JsonResponse({"redirect": az.get_absolute_url()})


def get_history_dates(historie_vazby, request_user):
    """
    Funkce pro získaní historických datumu.
    """
    request_user: User
    anonymized = not request_user.hlavni_role.pk in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)
    historie = {
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_EXT_ZD, anonymized),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_EXT_ZD, anonymized),
        "datum_potvrzeni": historie_vazby.get_last_transaction_date(POTVRZENI_EXT_ZD, anonymized),
    }
    return historie


def get_detail_template_shows(zaznam, user):
    """
    Funkce pro získaní kontextu pro zobrazování možností na stránkách.
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
    }
    return show


def get_required_fields():
    """
    Funkce pro získaní dictionary povinných polí podle stavu externího zdroje.

    Args:     
        zaznam (Externí zdroj): model ExterniZdroj pro který se dané pole počítají.

        next (int): pokud je poskytnuto číslo tak se jedná o povinné pole pro příští stav.

    Returns:
        required_fields: list polí.
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