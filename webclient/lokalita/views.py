import structlog

from django.contrib.auth.mixins import LoginRequiredMixin
from core.views import ExportMixinDate, check_stav_changed
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django.utils.translation import gettext as _
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import UpdateView, CreateView
from django.contrib import messages
from arch_z.models import ArcheologickyZaznam
from arch_z.forms import CreateArchZForm
from arch_z.views import get_arch_z_context
from core.constants import AZ_STAV_ZAPSANY
from core.exceptions import MaximalIdentNumberError
from core.ident_cely import get_temp_lokalita_ident
from core.message_constants import (
    LOKALITA_USPESNE_ZAPSANA,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
)

from .forms import LokalitaForm

from .filters import LokalitaFilter

from .models import Lokalita
from .tables import LokalitaTable

logger_s = structlog.get_logger(__name__)


class LokalitaIndexView(LoginRequiredMixin, TemplateView):
    template_name = "lokalita/index.html"


class LokalitaListView(
    ExportMixinDate, LoginRequiredMixin, SingleTableMixin, FilterView
):
    table_class = LokalitaTable
    model = Lokalita
    template_name = "search_list.html"
    filterset_class = LokalitaFilter
    paginate_by = 100
    export_name = "export_lokalita_"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["export_formats"] = ["csv", "json", "xlsx"]
        context["page_title"] = _("lokalita.vyber.pageTitle")
        context["app"] = "lokalita"
        context["toolbar"] = "toolbar_akce.html"
        context["search_sum"] = _("lokalita.vyber.pocetVyhledanych")
        context["pick_text"] = _("lokalita.vyber.pickText")
        context["hasOnlyVybrat_header"] = _("lokalita.vyber.header.hasOnlyVybrat")
        context["hasOnlyVlastnik_header"] = _("lokalita.vyber.header.hasOnlyVlastnik")
        context["hasOnlyArchive_header"] = _("lokalita.vyber.header.hasOnlyArchive")
        context["hasOnlyPotvrdit_header"] = _("lokalita.vyber.header.hasOnlyPotvrdit")
        context["default_header"] = _("lokalita.vyber.header.default")
        return context

    def get_queryset(self):
        # Only allow to view 3D models
        qs = super().get_queryset()
        qs = qs.select_related("druh", "typ_lokality", "zachovalost", "jistota")
        return qs


class LokalitaDetailView(DetailView, LoginRequiredMixin):
    model = Lokalita
    template_name = "lokalita/lokalita_detail.html"
    slug_field = "archeologicky_zaznam__ident_cely"

    def get_context_data(self, **kwargs):
        logger_s.debug(self.slug_field)
        logger_s.debug(self.get_object())
        lokalita_obj = self.get_object()
        context = get_arch_z_context(
            self.request,
            lokalita_obj.archeologicky_zaznam.ident_cely,
            zaznam=lokalita_obj.archeologicky_zaznam,
        )
        context["form"] = LokalitaForm(
            instance=lokalita_obj, readonly=True, required=False, detail=True
        )
        context["arch_z_form"] = CreateArchZForm(
            instance=lokalita_obj.archeologicky_zaznam, readonly=True, required=False
        )
        context["zaznam"] = lokalita_obj.archeologicky_zaznam
        context["app"] = "lokalita"
        context["page_title"] = _("lokalita.detal.pageTitle")
        context["detail_view"] = True
        return context


class LokalitaCreateView(CreateView, LoginRequiredMixin):
    model = Lokalita
    template_name = "lokalita/create.html"
    form_class = LokalitaForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        logger_s.debug("context is called")
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
        context["toolbar_name"] = _("lokalita.zapsat.toolbar.title")
        context["toolbar_label"] = _("lokalita.zapsat.toolbar.label")
        context["page_title"] = _("lokalita.zapsat.pageTitle")
        return context

    def form_valid(self, form):
        logger_s.debug(CreateArchZForm(self.request.POST))
        form_az = CreateArchZForm(self.request.POST)
        if form_az.is_valid():
            logger_s.debug("Form to save new Lokalita and AZ OK")
            az = form_az.save(commit=False)
            logger_s.debug(az)
            az.stav = AZ_STAV_ZAPSANY
            az.typ_zaznamu = ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
            lokalita = form.save(commit=False)
            try:
                region = az.hlavni_katastr.okres.kraj.rada_id
                typ = lokalita.typ_lokality.zkratka
                az.ident_cely = get_temp_lokalita_ident(typ, region)
            except MaximalIdentNumberError as e:
                logger_s.debug("Maximum lokalit dosazeno")
                messages.add_message(self.request, messages.ERROR, e.message)
                return self.form_invalid(form)
            else:
                az.save()
                form_az.save_m2m()
                az.set_zapsany(self.request.user)
                lokalita.archeologicky_zaznam = az
                lokalita.save()

                messages.add_message(
                    self.request, messages.SUCCESS, LOKALITA_USPESNE_ZAPSANA
                )
                logger_s.debug(
                    f"arch_z.views.zapsat: {LOKALITA_USPESNE_ZAPSANA}, ID akce: {lokalita.pk}."
                )
        else:
            logger_s.debug(form_az.errors)
            self.form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)
        logger_s.debug("main form is invalid")
        logger_s.debug(form.errors)
        return super().form_invalid(form)


class LokalitaEditView(UpdateView, LoginRequiredMixin):
    model = Lokalita
    template_name = "lokalita/create.html"
    form_class = LokalitaForm
    slug_field = "archeologicky_zaznam__ident_cely"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        required_fields = get_required_fields()
        logger_s.debug(required_fields[0:-1])
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
        context["toolbar_name"] = _("lokalita.edit.toolbar.title")
        context["toolbar_label"] = _("lokalita.edit.toolbar.label")
        context["edit_view"] = True
        context["page_title"] = _("lokalita.edit.pageTitle")
        return context

    def form_valid(self, form):
        logger_s.debug("Lokalita.EditForm is valid")
        form_az = CreateArchZForm(
            self.request.POST, instance=self.object.archeologicky_zaznam
        )
        if form_az.is_valid():
            logger_s.debug("Lokalita.EditFormAz is valid")
            form_az.save()
            messages.add_message(
                self.request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN
            )
        else:
            logger_s.debug("AZ form is invalid")
            logger_s.debug(form_az.errors)
            self.form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        logger_s.debug("main form is invalid")
        logger_s.debug(form.errors)
        return super().form_invalid(form)


def get_required_fields(zaznam=None, next=0):
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