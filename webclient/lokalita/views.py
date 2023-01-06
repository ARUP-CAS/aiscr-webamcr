import logging

import structlog
from arch_z.forms import CreateArchZForm
from arch_z.models import ArcheologickyZaznam
from arch_z.views import (
    AkceRelatedRecordUpdateView,
    DokumentacniJednotkaRelatedUpdateView,
    get_arch_z_context,
    get_areal_choices,
    get_detail_template_shows,
    get_dj_form_detail,
    get_komponenta_form_detail,
    get_obdobi_choices,
)
from core.constants import AZ_STAV_ZAPSANY
from core.exceptions import MaximalIdentNumberError
from core.ident_cely import get_temp_lokalita_ident
from core.message_constants import (
    LOKALITA_USPESNE_ZAPSANA,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
)
from core.views import ExportMixinDate
from dj.forms import CreateDJForm
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from komponenta.forms import CreateKomponentaForm
from komponenta.models import Komponenta
from pian.forms import PianCreateForm
from pian.models import Pian

from .filters import LokalitaFilter
from .forms import LokalitaForm
from .models import Lokalita
from .tables import LokalitaTable

logger = logging.getLogger(__name__)
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
        context["toolbar_name"] = _("lokalita.template.toolbar.title")
        return context

    def get_queryset(self):
        # Only allow to view 3D models
        qs = super().get_queryset()
        qs = qs.select_related("druh", "typ_lokality", "zachovalost", "jistota")
        return qs


class LokalitaDetailView(LoginRequiredMixin, DetailView):
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
            app="lokalita",
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
        context["next_url"] = lokalita_obj.get_absolute_url()
        return context


class LokalitaCreateView(LoginRequiredMixin, CreateView):
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
        context["header"] = _("lokalita.create.formHeader.label")
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
            az.save()
            form_az.save_m2m()
            region = az.hlavni_katastr.okres.kraj.rada_id
            typ = lokalita.typ_lokality.zkratka
            az.ident_cely = get_temp_lokalita_ident(typ, region, az)
            az.save()
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


class LokalitaEditView(LoginRequiredMixin, UpdateView):
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
        context["edit_view"] = True
        context["page_title"] = _("lokalita.edit.pageTitle")
        context["header"] = _("lokalita.edit.formHeader.label")
        context["zaznam"] = self.object.archeologicky_zaznam
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


class LokalitaRelatedView(LokalitaDetailView):
    model = Lokalita
    slug_field = "archeologicky_zaznam__ident_cely"

    def get_jednotky(self):
        ident_cely = self.kwargs.get("ident_cely")
        return (
            DokumentacniJednotka.objects.filter(
                archeologicky_zaznam__ident_cely=ident_cely
            )
            .select_related("komponenty", "typ", "pian")
            .prefetch_related(
                "komponenty__komponenty",
                "komponenty__komponenty__aktivity",
                "komponenty__komponenty__obdobi",
                "komponenty__komponenty__areal",
                "komponenty__komponenty__objekty",
                "komponenty__komponenty__predmety",
                "adb",
            )
        )

    def get_shows(self):
        return get_detail_template_shows(
            self.get_object().archeologicky_zaznam,
            self.get_jednotky(),
            self.request.user,
            app="lokalita",
        )


class LokalitaDokumentacniJednotkaCreateView(LokalitaRelatedView):
    template_name = "lokalita/dj/dj_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dj_form_create"] = CreateDJForm(
            typ_arch_z=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
        )
        return context


class LokalitaDokumentacniJednotkaRelatedView(LokalitaRelatedView):
    def get_dokumentacni_jednotka(self):
        dj_ident_cely = self.kwargs["dj_ident_cely"]
        logger_s.debug(
            "arch_z.views.DokumentacniJednotkaUpdateView.get_object",
            dj_ident_cely=dj_ident_cely,
        )
        object = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
        return object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dj_ident_cely"] = self.get_dokumentacni_jednotka().ident_cely
        return context


class LokalitaDokumentacniJednotkaUpdateView(LokalitaDokumentacniJednotkaRelatedView):
    template_name = "lokalita/dj/dj_update.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["j"] = get_dj_form_detail(
            "lokalita", self.get_dokumentacni_jednotka(), show=self.get_shows()
        )
        return context


class LokalitaKomponentaCreateView(LokalitaDokumentacniJednotkaRelatedView):
    template_name = "lokalita/dj/komponenta_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["komponenta_form_create"] = CreateKomponentaForm(
            get_obdobi_choices(), get_areal_choices()
        )
        context["j"] = self.get_dokumentacni_jednotka()
        return context


class LokalitaKomponentaUpdateView(LokalitaDokumentacniJednotkaRelatedView):
    template_name = "lokalita/dj/komponenta_detail.html"

    def get_komponenta(self):
        dj_ident_cely = self.kwargs["komponenta_ident_cely"]
        object = get_object_or_404(Komponenta, ident_cely=dj_ident_cely)
        return object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        komponenta = self.get_komponenta()
        old_nalez_post = self.request.session.pop("_old_nalez_post", None)
        komp_ident_cely = self.request.session.pop("komp_ident_cely", None)
        show = self.get_shows()
        context["k"] = get_komponenta_form_detail(
            komponenta, show, old_nalez_post, komp_ident_cely
        )
        return context


class LokalitaPianCreateView(LokalitaDokumentacniJednotkaRelatedView):
    template_name = "lokalita/dj/pian_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pian_form_create"] = PianCreateForm()
        return context


class LokalitaPianUpdateView(LokalitaDokumentacniJednotkaRelatedView):
    template_name = "lokalita/dj/pian_update.html"

    def get_pian(self):
        pian_ident_cely = self.kwargs["pian_ident_cely"]
        return get_object_or_404(Pian, ident_cely=pian_ident_cely)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pian_ident_cely"] = self.get_pian().ident_cely
        context["pian_form_update"] = PianCreateForm(instance=self.get_pian())
        return context


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
