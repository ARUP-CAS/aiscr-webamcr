import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import View

import structlog
from core.views import SearchListView, check_stav_changed
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
    ZAPSANI_EXT_ZD,
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
    ZAZNAM_USPESNE_SMAZAN,
)
from core.exceptions import MaximalIdentNumberError
from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
from core.utils import get_message
from .filters import ExterniZdrojFilter

# from .forms import LokalitaForm
from .models import ExterniZdroj, ExterniZdrojAutor, ExterniZdrojEditor, get_ez_ident
from .tables import ExterniZdrojTable
from .forms import (
    ExterniOdkazForm,
    ExterniZdrojForm,
    PripojitArchZaznamForm,
    PripojitExterniOdkazForm,
)

logger = logging.getLogger(__name__)
logger_s = structlog.get_logger(__name__)


class ExterniZdrojIndexView(LoginRequiredMixin, TemplateView):
    template_name = "ez/index.html"


class ExterniZdrojListView(SearchListView):
    table_class = ExterniZdrojTable
    model = ExterniZdroj
    filterset_class = ExterniZdrojFilter
    export_name = "export_externi-zdroje_"
    page_title = _("externiZdroj.vyber.pageTitle")
    app = "ext_zdroj"
    toolbar = "toolbar_externi_zdroj.html"
    search_sum = _("externiZdroj.vyber.pocetVyhledanych")
    pick_text = _("externiZdroj.vyber.pickText")
    hasOnlyVybrat_header = _("externiZdroj.vyber.header.hasOnlyVybrat")
    hasOnlyVlastnik_header = _("externiZdroj.vyber.header.hasOnlyVlastnik")
    hasOnlyArchive_header = _("externiZdroj.vyber.header.hasOnlyPotvrdit")
    hasOnlyPotvrdit_header = _("externiZdroj.vyber.header.hasOnlyPotvrdit")
    default_header = _("externiZdroj.vyber.header.default")
    toolbar_name = _("externiZdroj.template.toolbar.title")


class ExterniZdrojDetailView(LoginRequiredMixin, DetailView):
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
        )
        ez_lokality = (
            ez_odkazy.filter(
                archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
            )
            .select_related("archeologicky_zaznam")
            .select_related("archeologicky_zaznam__lokalita")
        )
        context["form"] = ExterniZdrojForm(
            instance=zaznam, readonly=True, required=False
        )
        context["zaznam"] = zaznam
        context["app"] = "ext_zdroj"
        context["page_title"] = _("externiZdroj.detail.pageTitle")
        context["toolbar_name"] = _("externiZdroj.detail.toolbar.title")
        context["history_dates"] = get_history_dates(zaznam.historie)
        context["show"] = get_detail_template_shows(zaznam)
        context["ez_akce"] = ez_akce
        context["ez_lokality"] = ez_lokality
        return context


class ExterniZdrojCreateView(LoginRequiredMixin, CreateView):
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
        context["toolbar_name"] = _("externiZdroj.zapsat.toolbar.title")
        context["page_title"] = _("externiZdroj.zapsat.pageTitle")
        context["header"] = _("externiZdroj.zapsat.formHeader.label")
        return context

    def form_valid(self, form):
        ez = form.save(commit=False)
        ez.stav = EZ_STAV_ZAPSANY
        ez.save()
        try:
            ez.ident_cely = get_ez_ident(ez)
        except MaximalIdentNumberError as e:
            logger_s.debug("Maximum lokalit dosazeno")
            messages.add_message(self.request, messages.ERROR, e.message)
            return self.form_invalid(form)
        ez.save()
        save_autor_editor(ez, form)
        ez.set_zapsany(self.request.user)
        messages.add_message(self.request, messages.SUCCESS, EZ_USPESNE_ZAPSAN)
        return HttpResponseRedirect(ez.get_absolute_url())

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)
        logger_s.debug("main form is invalid")
        logger_s.debug(form.errors)
        return super().form_invalid(form)


class ExterniZdrojEditView(LoginRequiredMixin, UpdateView):
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
        context["toolbar_name"] = _("externiZdroj.edit.toolbar.title")
        context["page_title"] = _("externiZdroj.edit.pageTitle")
        context["header"] = _("externiZdroj.edit.formHeader.label")
        return context

    def form_valid(self, form):
        super().form_valid(form)
        self.object.autori.clear()
        self.object.editori.clear()
        self.object.save()
        save_autor_editor(self.object, form)
        messages.add_message(self.request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        logger_s.debug("main form is invalid")
        logger_s.debug(form.errors)
        return super().form_invalid(form)


class TransakceView(LoginRequiredMixin, TemplateView):
    template_name = "core/transakce_modal.html"
    title = "title"
    id_tag = "id_tag"
    button = "button"
    allowed_states = []
    success_message = "success"
    action = ""

    def get_zaznam(self):
        ident_cely = self.kwargs.get("ident_cely")
        logger.debug(ident_cely)
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
            logger.debug("state not allowed for action: %s", self.action)
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
    title = _("externiZdroj.modalForm.odeslat.title.text")
    id_tag = "odeslat-ez-form"
    button = _("externiZdroj.modalForm.odeslat.submit.button")
    allowed_states = [EZ_STAV_ZAPSANY]
    success_message = EZ_USPESNE_ODESLAN
    action = "set_odeslany"


class ExterniZdrojPotvrditView(TransakceView):
    title = _("externiZdroj.modalForm.potvrdit.title.text")
    id_tag = "potvrdit-ez-form"
    button = _("externiZdroj.modalForm.potvrdit.submit.button")
    allowed_states = [EZ_STAV_ODESLANY]
    success_message = EZ_USPESNE_POTVRZEN
    action = "set_potvrzeny"


class ExterniZdrojSmazatView(TransakceView):
    title = _("externiZdroj.modalForm.smazat.title.text")
    id_tag = "smazat-ez-form"
    button = _("externiZdroj.modalForm.smazat.submit.button")
    allowed_states = [EZ_STAV_ODESLANY, EZ_STAV_POTVRZENY, EZ_STAV_ZAPSANY]
    success_message = ZAZNAM_USPESNE_SMAZAN

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        zaznam = context["object"]
        historie_vazby = zaznam.historie
        for eo in zaznam.externi_odkazy_zdroje.all():
            eo.delete()
        zaznam.delete()
        historie_vazby.delete()
        messages.add_message(request, messages.SUCCESS, self.success_message)
        return JsonResponse({"redirect": reverse("ez:index")})


class ExterniZdrojVratitView(TransakceView):
    title = _("externiZdroj.modalForm.vratit.title.text")
    id_tag = "vratit-ez-form"
    button = _("externiZdroj.modalForm.vratit.submit.button")
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
            logger.debug("The form is not valid")
            logger.debug(form.errors)
            return self.render_to_response(context)


class ExterniOdkazOdpojitView(TransakceView):
    title = _("externiZdroj.modalForm.odpojitAZ.title.text")
    id_tag = "odpojit-az-form"
    button = _("externiZdroj.modalForm.odpojitAZ.submit.button")
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
    template_name = "core/transakce_table_modal.html"
    title = _("externiZdroj.modalForm.pripojitAZ.title.text")
    id_tag = "pripojit-eo-form"
    button = _("externiZdroj.modalForm.pripojitAZ.submit.button")
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
        logger.debug(self.kwargs)
        ez = self.get_zaznam()
        form = PripojitArchZaznamForm(data=request.POST, type_arch=context["type"])
        if form.is_valid():
            logger_s.debug("ez.views.ExterniOdkazPripojitView.post.form_valid")
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
            logger_s.debug("ez.views.ExterniOdkazPripojitView.post.form_error", form_errors=form.errors)
        return JsonResponse({"redirect": ez.get_absolute_url()})


class ExterniOdkazEditView(LoginRequiredMixin, UpdateView):
    model = ExterniOdkaz
    template_name = "core/transakce_modal.html"
    title = _("externiZdroj.modalForm.zmeniPaginaci.title.text")
    id_tag = "zmenit-eo-form"
    button = _("externiZdroj.modalForm.zmeniPaginaci.submit.button")
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
        logger_s.debug("main form is invalid")
        logger_s.debug(form.errors)
        return super().form_invalid(form)


class ExterniOdkazOdpojitAZView(TransakceView):
    id_tag = "odpojit-az-form"
    allowed_states = [AZ_STAV_ODESLANY, AZ_STAV_ZAPSANY, AZ_STAV_ARCHIVOVANY]
    success_message = EO_USPESNE_ODPOJEN

    def get_zaznam(self):
        ident_cely = self.kwargs.get("ident_cely")
        logger.debug(ident_cely)
        return get_object_or_404(
            ArcheologickyZaznam,
            ident_cely=ident_cely,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        logger.debug("eo_id")
        logger.debug(self.kwargs.get("eo_id"))
        context["object"] = ExterniZdroj.objects.get(
            externi_odkazy_zdroje__id=self.kwargs.get("eo_id")
        )
        if self.get_zaznam().typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            context["title"] = _("arch_z.modalForm.odpojitEO.title.text")
            context["button"] = _("arch_z.modalForm.odpojitEO.submit.button")
        else:
            context["title"] = _("lokalita.modalForm.odpojitEO.title.text")
            context["button"] = _("lokalita.modalForm.odpojitEO.submit.button")
        return context

    def post(self, request, *args, **kwargs):
        az = self.get_zaznam()
        eo = ExterniOdkaz.objects.get(id=self.kwargs.get("eo_id"))
        eo.delete()
        messages.add_message(
            request, messages.SUCCESS, get_message(az, "EO_USPESNE_ODPOJEN")
        )
        return JsonResponse({"redirect": az.get_absolute_url()})


class ExterniZdrojAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return ExterniZdroj.objects.none()

        qs = ExterniZdroj.objects.filter()
        if self.q:
            qs = qs.filter(ident_cely__icontains=self.q)
        return qs


class ExterniZdrojTableRowView(LoginRequiredMixin, View):
    def get(self, request):
        zaznam = ExterniZdroj.objects.get(id=request.GET.get("id", ""))
        context = {"ez": zaznam}
        context["hide_paginace"] = True
        return HttpResponse(render_to_string("ez/az_ez_odkazy_table_row.html", context))


class ExterniOdkazPripojitDoAzView(TransakceView):
    template_name = "core/transakce_table_modal.html"
    title = _("externiZdroj.modalForm.pripojitAZ.title.text")
    id_tag = "pripojit-eo-doaz-form"
    button = _("externiZdroj.modalForm.pripojitAZ.submit.button")
    allowed_states = [EZ_STAV_ODESLANY, EZ_STAV_POTVRZENY, EZ_STAV_ZAPSANY]

    def get_zaznam(self):
        ident_cely = self.kwargs.get("ident_cely")
        logger.debug(ident_cely)
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
            context["title"] = _("arch_z.modalForm.pripojitEO.title.text")
            context["button"] = _("arch_z.modalForm.pripojitEO.submit.button")
        else:
            context["title"] = _("lokalita.modalForm.pripojitEO.title.text")
            context["button"] = _("lokalita.modalForm.pripojitEO.submit.button")
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
            logger.debug("not valid")
            logger.debug(form.errors)
        return JsonResponse({"redirect": az.get_absolute_url()})


def get_history_dates(historie_vazby):
    historie = {
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_EXT_ZD),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_EXT_ZD),
        "datum_potvrzeni": historie_vazby.get_last_transaction_date(POTVRZENI_EXT_ZD),
    }
    return historie


def get_detail_template_shows(zaznam):
    show_vratit = zaznam.stav > EZ_STAV_ZAPSANY
    show_odeslat = zaznam.stav == EZ_STAV_ZAPSANY
    show_potvrdit = zaznam.stav == EZ_STAV_ODESLANY
    show_edit = zaznam.stav not in [EZ_STAV_POTVRZENY]
    show_arch_links = zaznam.stav == EZ_STAV_POTVRZENY
    show_ez_odkazy = True
    show_paginace = True
    show_odpojit = True
    show = {
        "vratit_link": show_vratit,
        "odeslat_link": show_odeslat,
        "potvrdit_link": show_potvrdit,
        "editovat": show_edit,
        "odpojit": show_odpojit,
        "arch_links": show_arch_links,
        "ez_odkazy": show_ez_odkazy,
        "paginace": show_paginace,
    }
    return show


def get_required_fields():
    required_fields = [
        "typ",
        "autori",
        "rok_vydani_vzniku",
        "nazev",
    ]
    return required_fields


def save_autor_editor(zaznam, form):
    i = 1
    for autor in form.cleaned_data["autori"]:
        ExterniZdrojAutor.objects.create(
            externi_zdroj=zaznam,
            autor=autor,
            poradi=i,
        )
        i = i + 1
    for editor in form.cleaned_data["editori"]:
        ExterniZdrojEditor.objects.create(
            externi_zdroj=zaznam,
            editor=editor,
            poradi=i,
        )
        i = i + 1