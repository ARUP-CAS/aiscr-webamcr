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
from core.ident_cely import get_temp_lokalita_ident
from core.message_constants import (
    LOKALITA_USPESNE_ZAPSANA,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
)
from core.views import SearchListView
from dj.forms import CreateDJForm
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView
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
    """
    Třida pohledu pro zobrazení domovské stránky lokalit s navigačními možnostmi.
    """

    template_name = "lokalita/index.html"

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní kontextu podlehu.
        """
        context = {
            "toolbar_name": _("ez.views.lokalitaIndexView.toolbarName"),
        }
        return context


class LokalitaListView(SearchListView):
    """
    Třida pohledu pro zobrazení listu/tabulky s lokalitami.
    """

    table_class = LokalitaTable
    model = Lokalita
    filterset_class = LokalitaFilter
    export_name = "export_lokalita_"
    app = "lokalita"
    toolbar = "toolbar_akce.html"
    permission_model_lookup = "archeologicky_zaznam__"
    typ_zmeny_lookup = ZAPSANI_AZ

    def init_translations(self):
        self.page_title = _("lokalita.views.lokalitaListView.pageTitle.text")
        self.search_sum = _("lokalita.views.lokalitaListView.pocetVyhledanych.text")
        self.pick_text = _("lokalita.views.lokalitaListView.pickText.text")
        self.hasOnlyVybrat_header = _(
            "lokalita.views.lokalitaListView.header.hasOnlyVybrat.text"
        )
        self.hasOnlyVlastnik_header = _(
            "lokalita.views.lokalitaListView.header.hasOnlyVlastnik.text"
        )
        self.hasOnlyArchive_header = _(
            "lokalita.views.lokalitaListView.header.hasOnlyArchive.text"
        )
        self.hasOnlyPotvrdit_header = _(
            "lokalita.views.lokalitaListView.header.hasOnlyPotvrdit.text"
        )
        self.default_header = _("lokalita.views.lokalitaListView.header.default.text")
        self.toolbar_name = _("lokalita.views.lokalitaListView.toolbar.title.text")
        self.toolbar_label = _("lokalita.views.lokalitaListView.toolbar_label.text")

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related(
            "druh",
            "typ_lokality",
            "zachovalost",
            "jistota",
            "archeologicky_zaznam__hlavni_katastr",
            "archeologicky_zaznam__hlavni_katastr__okres",
            "archeologicky_zaznam",
            "archeologicky_zaznam__pristupnost",
        ).prefetch_related(
            "archeologicky_zaznam__katastry", "archeologicky_zaznam__katastry__okres"
        )
        return self.check_filter_permission(qs)


class LokalitaDetailView(
    LoginRequiredMixin, SingleObjectMixin, AkceRelatedRecordUpdateView
):
    """
    Třida pohledu pro zobrazení detailu lokality.
    """

    model = Lokalita
    template_name = "lokalita/lokalita_detail.html"
    slug_field = "archeologicky_zaznam__ident_cely"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_archeologicky_zaznam(self):
        """
        Metóda pro získaní akce z db.
        """
        return self.object.archeologicky_zaznam

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní contextu akci pro template.
        """
        self.object = self.get_object()
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("lokalita.views.lokalitaDetailView.pageTitle")
        context["detail_view"] = True
        context["form"] = LokalitaForm(
            instance=self.object, readonly=True, required=False, detail=True
        )
        context["arch_z_form"] = CreateArchZForm(
            instance=self.arch_zaznam, readonly=True, required=False
        )
        return context

    def get_shows(self):
        return get_detail_template_shows(
            self.get_object().archeologicky_zaznam,
            self.get_jednotky(),
            self.request.user,
            app="lokalita",
        )


class LokalitaCreateView(LoginRequiredMixin, CreateView):
    """
    Třida pohledu pro vytvoření lokality.
    """

    model = Lokalita
    template_name = "lokalita/create.html"
    form_class = LokalitaForm

    def get_context_data(self, **kwargs):
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
        return context

    def form_valid(self, form):
        logger.debug(CreateArchZForm(self.request.POST))
        form_az = CreateArchZForm(self.request.POST)
        if form_az.is_valid():
            logger.debug("Form to save new Lokalita and AZ OK")
            az = form_az.save(commit=False)
            logger.debug(az)
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
            logger.debug(
                f"arch_z.views.zapsat: {LOKALITA_USPESNE_ZAPSANA}, ID akce: {lokalita.pk}."
            )
        else:
            logger.debug(form_az.errors)
            self.form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)
        logger.debug("main form is invalid")
        logger.debug(form.errors)
        return super().form_invalid(form)


class LokalitaEditView(LoginRequiredMixin, UpdateView):
    """
    Třida pohledu pro editaci lokality.
    """

    model = Lokalita
    template_name = "lokalita/create.html"
    form_class = LokalitaForm
    slug_field = "archeologicky_zaznam__ident_cely"

    def get_context_data(self, **kwargs):
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
        logger.debug("Lokalita.EditForm is valid")
        form_az = CreateArchZForm(
            self.request.POST, instance=self.object.archeologicky_zaznam
        )
        if form_az.is_valid():
            logger.debug("Lokalita.EditFormAz is valid")
            form_az.save()
            messages.add_message(
                self.request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN
            )
        else:
            logger.debug("AZ form is invalid")
            logger.debug(form_az.errors)
            self.form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        logger.debug("main form is invalid")
        logger.debug(form.errors)
        return super().form_invalid(form)


class LokalitaRelatedView(LokalitaDetailView):
    """
    Třida pohledu pro získaní relací lokality, která je dedená v dalších pohledech.
    """

    model = Lokalita
    slug_field = "archeologicky_zaznam__ident_cely"
    """
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
    """


class LokalitaDokumentacniJednotkaCreateView(LokalitaRelatedView):
    """
    Třida pohledu pro vytvoření dokumentační jednotky lokality.
    """

    template_name = "lokalita/dj/dj_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dj_form_create"] = CreateDJForm(
            typ_arch_z=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
        )
        return context


class LokalitaDokumentacniJednotkaRelatedView(LokalitaRelatedView):
    """
    Třida pohledu pro získaní dokumentačních jednotek lokality, která je dedená v dalších pohledech.
    """

    def get_dokumentacni_jednotka(self):
        dj_ident_cely = self.kwargs["dj_ident_cely"]
        logger.debug(
            "arch_z.views.DokumentacniJednotkaUpdateView.get_object",
            extra={"dj_ident_cely": dj_ident_cely},
        )
        object = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
        return object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dj_ident_cely"] = self.get_dokumentacni_jednotka().ident_cely
        return context


class LokalitaDokumentacniJednotkaUpdateView(LokalitaDokumentacniJednotkaRelatedView):
    """
    Třida pohledu pro editaci dokumentační jednotky lokality.
    """

    template_name = "lokalita/dj/dj_update.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["j"] = get_dj_form_detail(
            "lokalita", self.get_dokumentacni_jednotka(), show=self.get_shows(), user=self.request.user
        )
        return context


class LokalitaKomponentaCreateView(LokalitaDokumentacniJednotkaRelatedView):
    """
    Třida pohledu pro vytvoření komponenty lokality.
    """

    template_name = "lokalita/dj/komponenta_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["komponenta_form_create"] = CreateKomponentaForm(
            get_obdobi_choices(), get_areal_choices()
        )
        context["j"] = self.get_dokumentacni_jednotka()
        return context


class LokalitaKomponentaUpdateView(LokalitaDokumentacniJednotkaRelatedView):
    """
    Třida pohledu pro editaci komponenty lokality.
    """

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
    """
    Třida pohledu pro vytvoření pianu dokumentační jednotky lokality.
    """

    template_name = "lokalita/dj/pian_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pian_form_create"] = PianCreateForm()
        return context


class LokalitaPianUpdateView(LokalitaDokumentacniJednotkaRelatedView):
    """
    Třida pohledu pro editaci pianu dokumentační jednotky lokality.
    """

    template_name = "lokalita/dj/pian_update.html"

    def get_pian(self):
        pian_ident_cely = self.kwargs["pian_ident_cely"]
        return get_object_or_404(Pian, ident_cely=pian_ident_cely)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.pian = self.get_pian()
        context["pian_ident_cely"] = self.pian.ident_cely
        context["pian_form_update"] = PianCreateForm(instance=self.pian)
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if self.pian == PIAN_POTVRZEN:
            raise PermissionDenied
        return self.render_to_response(context)


def get_required_fields(zaznam=None, next=0):
    """
    Funkce pro získaní dictionary povinných polí podle stavu lokality.

    Args:
        zaznam (Lokalita): model Lokalita pro který se dané pole počítají.

        next (int): pokud je poskytnuto číslo tak se jedná o povinné pole pro příští stav.

    Returns:
        required_fields: list polí.
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
