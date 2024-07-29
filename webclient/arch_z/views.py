import logging
from io import BytesIO

import pandas
import redis
import simplejson as json
from cacheops import invalidate_model
from django.db.models import RestrictedError
from django_tables2.export import TableExport

from adb.forms import CreateADBForm, VyskovyBodFormSetHelper, create_vyskovy_bod_form
from adb.models import Adb, VyskovyBod
from arch_z.filters import AkceFilter
from arch_z.forms import (
    AkceVedouciFormSetHelper,
    CreateAkceForm,
    CreateArchZForm,
    create_akce_vedouci_objekt_form,
)
from arch_z.models import (
    Akce,
    AkceVedouci,
    ArcheologickyZaznam,
    ExterniOdkaz,
    get_akce_ident,
    ExterniZdroj
)
from arch_z.tables import AkceTable
from core.constants import (
    ARCHIVACE_AZ,
    AZ_STAV_ARCHIVOVANY,
    AZ_STAV_ODESLANY,
    AZ_STAV_ZAPSANY,
    IDENTIFIKATOR_DOCASNY_PREFIX,
    ODESLANI_AZ,
    PIAN_NEPOTVRZEN,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_UKONCENY_V_TERENU,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_ZAPSANY,
    ROLE_ADMIN_ID,
    ROLE_ARCHEOLOG_ID,
    ROLE_ARCHIVAR_ID,
    ROLE_BADATEL_ID,
    ZAPSANI_AZ,
    ZMENA_AZ,
    PIAN_POTVRZEN
)
from core.exceptions import MaximalEventCount
from core.forms import CheckStavNotChangedForm, VratitForm
from core.ident_cely import get_project_event_ident, get_temp_akce_ident
from core.message_constants import (
    MAXIMUM_AKCII_DOSAZENO,
    PRISTUP_ZAKAZAN,
    SPATNY_ZAZNAM_ZAZNAM_VAZBA,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN, ZAZNAM_SE_NEPOVEDLO_SMAZAT_NAVAZANE_ZAZNAMY, ZAZNAM_NELZE_SMAZAT_FEDORA,
)
from core.repository_connector import FedoraRepositoryConnector, FedoraTransaction
from core.utils import (
    get_all_pians_with_akce,
    get_dj_pians_centroid,
    get_pians_from_akce,
    get_heatmap_pian,
    get_heatmap_pian_density,
    get_message,
    get_num_pians_from_envelope,
    get_dj_pians_from_envelope, CannotFindCadasterCentre,
)
from core.coordTransform import transform_geom_to_wgs84
from core.views import PermissionFilterMixin, SearchListView, check_stav_changed
from dal import autocomplete
from dj.forms import CreateDJForm
from dj.models import DokumentacniJednotka
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.core.cache import cache
from django.forms import inlineformset_factory
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from dokument.models import Dokument, DokumentCast
from dokument.views import get_komponenta_form_detail, odpojit, pripojit
from heslar.hesla import (
    HESLAR_AREAL,
    HESLAR_AREAL_KAT,
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
    HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRESNE,
    HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRIBLIZNE,
    SPECIFIKACE_DATA_PRESNE,
    TYP_DJ_KATASTR,
    TYP_DJ_SONDA_ID,
    TYP_PROJEKTU_PRUZKUM_ID,
)
from heslar.models import Heslar, RuianKatastr
from heslar.views import heslar_12
from historie.models import Historie
from komponenta.forms import CreateKomponentaForm
from komponenta.models import Komponenta
from nalez.forms import (
    NalezFormSetHelper,
    create_nalez_objekt_form,
    create_nalez_predmet_form,
)
from nalez.models import NalezObjekt, NalezPredmet
from pian.forms import PianCreateForm
from pian.models import Pian
from projekt.forms import PripojitProjektForm
from projekt.models import Projekt
from services.mailer import Mailer
from uzivatel.models import User
from core.models import Permissions as p, check_permissions
from webclient.settings.base import get_plain_redis_pass

logger = logging.getLogger(__name__)


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


class AkceRelatedRecordUpdateView(TemplateView):
    """
    Třida, která se dedí a která obsahuje metódy pro získaní relací akce.
    """

    arch_zaznam = None

    def get_shows(self):
        """
        Metóda pro získaní informací které části stránky mají být zobrazeny.
        """
        return get_detail_template_shows(
            self.get_archeologicky_zaznam(), self.get_jednotky(), self.request.user
        )

    def get_archeologicky_zaznam(self):
        """
        Metóda pro získaní akce z db.
        """
        ident_cely = self.kwargs.get("ident_cely")
        return get_object_or_404(
            ArcheologickyZaznam.objects.select_related("hlavni_katastr")
            .select_related("akce")
            .select_related("akce__vedlejsi_typ")
            .select_related("akce__hlavni_typ")
            .select_related("pristupnost"),
            ident_cely=ident_cely,
        )

    def get_jednotky(self):
        """
        Metóda pro získaní dokumentační jednotky navázané na akci.
        """
        return (
            DokumentacniJednotka.objects.filter(
                archeologicky_zaznam__ident_cely=self.arch_zaznam.ident_cely
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

    def get_dokumenty(self):
        """
        Metóda pro získaní dokumentů navázaných na akci.
        """
        return (
            Dokument.objects.filter(casti__archeologicky_zaznam__ident_cely=self.arch_zaznam.ident_cely)
            .select_related("soubory")
            .prefetch_related("soubory__soubory")
            .order_by("ident_cely")
        )

    def get_externi_odkazy(self):
        """
        Metóda pro získaní externích odkazů navázaných na akci.
        """
        return (
            ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely=self.arch_zaznam.ident_cely)
            .select_related("externi_zdroj")
            .order_by("externi_zdroj__ident_cely")
        )

    def get_vedouci(self, context):
        """
        Metóda pro získaní dalších vedoucích navázaných na akci.
        """
        ostatni_vedouci_objekt_formset = inlineformset_factory(
            Akce,
            AkceVedouci,
            form=create_akce_vedouci_objekt_form(readonly=True),
            extra=0,
            can_delete=False,
        )
        ostatni_vedouci_objekt_formset = ostatni_vedouci_objekt_formset(
            instance=context["zaznam"].akce,
            prefix="",
        )
        akce_zaznam_ostatni_vedouci = []
        for vedouci in AkceVedouci.objects.filter(akce=context["zaznam"].akce).order_by(
           "vedouci__prijmeni", "vedouci__jmeno"
        ):
            vedouci: AkceVedouci
            akce_zaznam_ostatni_vedouci.append(
                [str(vedouci.vedouci), str(vedouci.organizace)]
            )
        context["ostatni_vedouci_objekt_formset"] = ostatni_vedouci_objekt_formset
        context["ostatni_vedouci_objekt_formset_helper"] = AkceVedouciFormSetHelper()
        context["ostatni_vedouci_objekt_formset_readonly"] = True
        context["akce_zaznam_ostatni_vedouci"] = akce_zaznam_ostatni_vedouci

    def check_locality_arch_z_conflict(self):
        try:
            if self.get_archeologicky_zaznam().lokalita:
                raise Http404(_("arch_z.views.AkceRelatedRecordUpdateView.get_context_data.lokalita_error"))
        except ObjectDoesNotExist:
            return False

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní contextu akci pro template.
        """
        context = super().get_context_data(**kwargs)
        self.check_locality_arch_z_conflict()
        self.arch_zaznam = self.get_archeologicky_zaznam()
        context["showbackdetail"] = False
        context["zaznam"] = self.arch_zaznam
        if self.arch_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            if self.arch_zaznam.akce.typ == Akce.TYP_AKCE_PROJEKTOVA:
                context["showbackdetail"] = True if self.request.user.hlavni_role.pk != ROLE_BADATEL_ID else False
                context["app"] = "pr"
                context[
                    "arch_pr_link"
                ] = '{% url "projekt:projekt_archivovat" zaznam.akce.projekt.ident_cely %}?sent_stav={{projekt.stav}}&from_arch=true'
            else:
                context["app"] = "akce"
                context["arch_pr_link"] = None
            context["presna_specifikace"] = (
                True
                if self.arch_zaznam.akce.specifikace_data
                == Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE)
                else False
            )
            self.get_vedouci(context)
        else:
            context["app"] = "lokalita"
        context["dokumentacni_jednotky"] = self.get_jednotky()
        context["dokumenty"] = self.get_dokumenty()
        context["history_dates"] = get_history_dates(self.arch_zaznam.historie, self.request.user)
        context["show"] = get_detail_template_shows(
            self.arch_zaznam, self.get_jednotky(), self.request.user, context["app"]
        )
        context["externi_odkazy"] = self.get_externi_odkazy()            
        context["next_url"] = self.arch_zaznam.get_absolute_url()
        return context


class ArcheologickyZaznamDetailView(LoginRequiredMixin, AkceRelatedRecordUpdateView):
    """
    Třída pohledu pro zobrazení detailu akce.
    """
    template_name = "arch_z/dj/arch_z_detail.html"

    def get_archeologicky_zaznam(self) -> ArcheologickyZaznam:
        """
        Metóda pro získani záznamu akce z db podle ident_cely.
        """
        ident_cely = self.kwargs.get("ident_cely")
        return get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní context dat navíc oproti přepisované metóde.
        """
        context = super().get_context_data(**kwargs)
        context["warnings"] = self.request.session.pop("temp_data", None)
        context["arch_projekt_link"] = (
            self.request.session.pop("arch_projekt_link", None),
        )
        context["arch_projekt_link_uzavrit"] = (
            self.request.session.pop("arch_projekt_link_uzavrit", None),
        )
        return context


class DokumentacniJednotkaRelatedUpdateView(AkceRelatedRecordUpdateView):
    """
    Třida, která se dedí a která obsahuje metódy pro získaní relací DJ.
    """
    template_name = "arch_z/dj/dj_update.html"

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        dj = get_object_or_404(DokumentacniJednotka, ident_cely=self.kwargs["dj_ident_cely"])
        az = get_object_or_404(ArcheologickyZaznam, ident_cely=self.kwargs["ident_cely"])
        if not dj.archeologicky_zaznam == az:
            logger.error("Archeologicky zaznam - Dokumentacni jednotka wrong relation")
            messages.add_message(
                        request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA
                    )
            if url_has_allowed_host_and_scheme(request.GET.get("next","core:home"), allowed_hosts=settings.ALLOWED_HOSTS):
                safe_redirect = request.GET.get("next","core:home")
            else:
                safe_redirect = "/"
            return redirect(safe_redirect)
        return super().dispatch(request, *args, **kwargs)

    def get_dokumentacni_jednotka(self):
        """
        Metóda pro získani záznamu DJ z db podle ident_cely.
        """
        dj_ident_cely = self.kwargs["dj_ident_cely"]
        logger.debug("arch_z.views.DokumentacniJednotkaUpdateView.get_object", extra={"dj_ident_cely": dj_ident_cely})
        objects = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
        return objects

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní context dat DJ navíc oproti přepisované metóde, záznam DJ.
        """
        context = super().get_context_data(**kwargs)
        context["active_dj_ident"] = self.get_dokumentacni_jednotka().ident_cely
        return context


class DokumentacniJednotkaCreateView(LoginRequiredMixin, AkceRelatedRecordUpdateView):
    """
    Třída pohledu pro vytvoření dokumentační jednotky.
    """
    template_name = "arch_z/dj/dj_create.html"

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření DJ.
        """
        context = super().get_context_data(**kwargs)
        typ_akce = None
        logger.debug("arch_z.views.DokumentacniJednotkaCreateView.get_context_data")
        try:
            self.get_archeologicky_zaznam()
            if (
                self.get_archeologicky_zaznam().typ_zaznamu
                == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
            ):
                typ_akce = self.get_archeologicky_zaznam().akce.typ
        except Exception as err:
            logger.debug("arch_z.views.DokumentacniJednotkaCreateView.get_context_data.cannot_get_typ_akce",
                         extra={"err": err})
        context["dj_form_create"] = CreateDJForm(
            jednotky=self.get_jednotky(),
            typ_arch_z=self.get_archeologicky_zaznam().typ_zaznamu,
            typ_akce=typ_akce,
        )
        logger.debug("arch_z.views.DokumentacniJednotkaCreateView.get_context_data.end",
                     extra={"typ_arch_z": self.get_archeologicky_zaznam().typ_zaznamu, "typ_akce": typ_akce})
        return context


class DokumentacniJednotkaUpdateView(
    LoginRequiredMixin, DokumentacniJednotkaRelatedUpdateView
):
    """
    Třída pohledu pro zobrazení detailu dokumentační jednotky s možností její úpravy.
    """
    template_name = "arch_z/dj/dj_update.html"

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní context dat DJ navíc oproti přepisované metóde, pro zobrazení správneho detailu.
        """
        context = super().get_context_data(**kwargs)
        old_adb_post = self.request.session.pop("_old_adb_post", None)

        show = self.get_shows()
        jednotka: DokumentacniJednotka = self.get_dokumentacni_jednotka()
        jednotky = self.get_jednotky()
        # check po MR
        context["j"] = get_dj_form_detail(
            "akce", jednotka, jednotky, show, old_adb_post,self.request.user
        )
        return context


class KomponentaCreateView(LoginRequiredMixin, DokumentacniJednotkaRelatedUpdateView):
    """
    Třida pohledu pro vytvoření komponenty dokumentační jednotky.
    """
    template_name = "arch_z/dj/komponenta_create.html"

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní context dat navíc oproti přepisované metóde, formulář na vytvoření komponenty.
        """
        context = super().get_context_data(**kwargs)
        context["komponenta_form_create"] = CreateKomponentaForm(
            get_obdobi_choices(), get_areal_choices()
        )
        context["j"] = self.get_dokumentacni_jednotka()
        return context


class KomponentaUpdateView(LoginRequiredMixin, DokumentacniJednotkaRelatedUpdateView):
    """
    Třida pohledu pro editaci komponenty dokumentační jednotky.
    """
    template_name = "arch_z/dj/komponenta_detail.html"

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        dj = get_object_or_404(DokumentacniJednotka, ident_cely=self.kwargs["dj_ident_cely"])
        komponenta = get_object_or_404(Komponenta, ident_cely=self.kwargs["komponenta_ident_cely"])
        if not dj.komponenty == komponenta.komponenta_vazby:
            logger.error("Komponenta - Dokumentacni jednotka wrong relation")
            messages.add_message(
                        request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA
                    )
            if url_has_allowed_host_and_scheme(request.GET.get("next","core:home"), allowed_hosts=settings.ALLOWED_HOSTS):
                safe_redirect = request.GET.get("next","core:home")
            else:
                safe_redirect = "/"
            return redirect(safe_redirect)
        return super().dispatch(request, *args, **kwargs)

    def get_komponenta(self):
        """
        Metóda pro získani záznamu komponenty z db podle ident_cely.
        """
        dj_ident_cely = self.kwargs["komponenta_ident_cely"]
        object = get_object_or_404(Komponenta, ident_cely=dj_ident_cely)
        return object

    def get_dokumentacni_jednotka(self):
        dj_ident_cely = self.kwargs["dj_ident_cely"]
        logger.debug("arch_z.views.DokumentacniJednotkaUpdateView.get_object", extra={"dj_ident_cely": dj_ident_cely})
        object = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
        return object
        
    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní context dat navíc oproti přepisované metóde, formulář pro úpravu komponenty,
        případne data poslaného chybného formuláře.
        """
        context = super().get_context_data(**kwargs)
        komponenta = self.get_komponenta()
        old_nalez_post = self.request.session.pop("_old_nalez_post", None)
        komp_ident_cely = self.request.session.pop("komp_ident_cely", None)
        show = self.get_shows()

        context["k"] = get_komponenta_form_detail(
            komponenta, show, old_nalez_post, komp_ident_cely
        )
        context["j"] = self.get_dokumentacni_jednotka()
        context["active_komp_ident"] = komponenta.ident_cely
        return context


class PianCreateView(LoginRequiredMixin, DokumentacniJednotkaRelatedUpdateView):
    """
    Třida pohledu pro vytvoření PIANu dokumentační jednotky.
    """
    template_name = "arch_z/dj/pian_create.html"

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření PIANu.
        """
        context = super().get_context_data(**kwargs)
        context["j"] = self.get_dokumentacni_jednotka()
        context["pian_form_create"] = PianCreateForm()
        return context
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if "index" in self.request.GET and "label" in self.request.GET:
            try:
                geom=cache.get(str(request.user.id) + "_geom")
                #cache.delete(str(request.user.id) + "_geom")
                index=int(self.request.GET["index"])
                if self.request.GET["label"]!=geom.iloc[index]["label"]:
                    raise Exception("arch_z.views.PianCreateView.get.label_not_found")
                context["geom"] = geom.iloc[index].copy()
                if context["geom"]["epsg"]=='5514' or context["geom"]["epsg"] == 5514:
                    context["geom"]['geometry'],stat =  transform_geom_to_wgs84(context["geom"]['geometry'])
                    if stat != "OK":
                        raise Exception("arch_z.views.PianCreateView.get.transormation_error")
            except Exception as err:
                logger.error("arch_z.views.PianCreateView.get.import_pian.error", extra={"err": err})
                messages.add_message(self.request, messages.ERROR, _("arch_z.views.DokumentacniJednotkaRelatedUpdateView.get.import_pian.error"))
                return redirect(reverse("arch_z:detail-dj", args=[self.arch_zaznam.ident_cely, context['dj_ident_cely']] ))
        return self.render_to_response(context)


class PianUpdateView(LoginRequiredMixin, DokumentacniJednotkaRelatedUpdateView):
    """
    Třida pohledu pro editaci PIANu dokumentační jednotky.
    """
    template_name = "arch_z/dj/pian_update.html"

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        dj = get_object_or_404(DokumentacniJednotka, ident_cely=self.kwargs["dj_ident_cely"])
        pian = get_object_or_404(Pian, ident_cely=self.kwargs["pian_ident_cely"])
        if not dj.pian == pian:
            logger.error("Pian - Dokumentacni jednotka wrong relation")
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
        """
        Metóda pro získaní context dat navíc oproti přepisované metóde, formulář pro editaci PIANu.
        """
        context = super().get_context_data(**kwargs)
        context["j"] = self.get_dokumentacni_jednotka()
        context["pian_form_update"] = PianCreateForm(presnost=context["j"].pian.presnost)
        return context
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if context["j"].pian.stav == PIAN_POTVRZEN:
            raise PermissionDenied
        if "index" in self.request.GET and "label" in self.request.GET:
            try:
                geom=cache.get(str(request.user.id) + "_geom")
                #cache.delete(str(request.user.id) + "_geom")
                index=int(self.request.GET["index"])
                if self.request.GET["label"]!=geom.iloc[index]["label"]:
                    raise Exception("arch_z.views.PianUpdateView.get.label_not_found")
                context["geom"] = geom.iloc[index].copy()
                if context["geom"]["epsg"]=='5514' or context["geom"]["epsg"] == 5514:
                    context["geom"]['geometry'],stat =  transform_geom_to_wgs84(context["geom"]['geometry'])
                    if stat != "OK":
                        raise Exception("arch_z.views.PianUpdateView.transormation_error")
            except Exception as err:
                logger.error("arch_z.views.PianUpdateView.get.import_pian.error", extra={"err": err})
                messages.add_message(self.request, messages.ERROR, _("arch_z.views.DokumentacniJednotkaRelatedUpdateView.get.import_pian.error"))
                return redirect(reverse("arch_z:detail-dj", args=[self.arch_zaznam.ident_cely, context['dj_ident_cely']] ))
        return self.render_to_response(context)
    


class AdbCreateView(LoginRequiredMixin, DokumentacniJednotkaRelatedUpdateView):
    """
    Třida pohledu pro vytvoření PIANu dokumentační jednotky.
    """
    template_name = "arch_z/dj/adb_create.html"

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření ADB.
        """
        context = super().get_context_data(**kwargs)
        context["j"] = self.get_dokumentacni_jednotka()
        context["adb_form_create"] = CreateADBForm()
        return context


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    """
    Funkce pohledu pro zobrazení a spracováni editace akce.
    Na začátku se kontroluje jestli stav není archivovaný.
    Zobrazení pozostáva ze 3 formulářů: CreateArchZForm, CreateAkceForm, formset na další vedoucí.
    """
    zaznam = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if zaznam.stav == AZ_STAV_ARCHIVOVANY:
        raise PermissionDenied()
    required_fields = get_required_fields(zaznam)
    required_fields_next = get_required_fields(zaznam, 1)
    if request.method == "POST":
        form_az = CreateArchZForm(request.POST, instance=zaznam)
        form_akce = CreateAkceForm(
            request.POST,
            instance=zaznam.akce,
            required=required_fields,
            required_next=required_fields_next,
        )

        ostatni_vedouci_objekt_formset = inlineformset_factory(
            Akce,
            AkceVedouci,
            form=create_akce_vedouci_objekt_form(readonly=False),
            extra=1,
            can_delete=False,
        )
        ostatni_vedouci_objekt_formset = ostatni_vedouci_objekt_formset(
            request.POST,
            instance=zaznam.akce,
            prefix="_osv",
        )

        if (
            form_az.is_valid()
            and form_akce.is_valid()
            and ostatni_vedouci_objekt_formset.is_valid()
        ):
            fedora_trasnaction = FedoraTransaction()
            logger.debug("arch_z.views.edit.form_valid")
            az = form_az.save(commit=False)
            az.active_transaction = fedora_trasnaction
            az.save()
            form_az.save_m2m()
            akce = form_akce.save()
            ostatni_vedouci_objekt_formset.save()
            if form_az.changed_data or form_akce.changed_data:
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            akce.set_snapshots()
            az.close_active_transaction_when_finished = True
            az.save()
            return redirect("arch_z:detail", ident_cely=ident_cely)
        else:
            logger.warning("arch_z.views.edit.form_az_valid", extra={"form_az_errors": form_az.errors,
                                                                     "form_akce_errors": form_akce.errors})
    else:
        form_az = CreateArchZForm(instance=zaznam)
        form_akce = CreateAkceForm(
            instance=zaznam.akce,
            required=required_fields,
            required_next=required_fields_next,
        )
        ostatni_vedouci_objekt_formset = inlineformset_factory(
            Akce,
            AkceVedouci,
            form=create_akce_vedouci_objekt_form(readonly=False),
            extra=3,
            can_delete=False,
        )
        ostatni_vedouci_objekt_formset = ostatni_vedouci_objekt_formset(
            None,
            instance=zaznam.akce,
            prefix="_osv",
        )

    return render(
        request,
        "arch_z/create.html",
        {
            "zaznam": zaznam,
            "formAZ": form_az,
            "formAkce": form_akce,
            "ostatni_vedouci_objekt_formset": ostatni_vedouci_objekt_formset,
            "ostatni_vedouci_objekt_formset_helper": AkceVedouciFormSetHelper(),
            "ostatni_vedouci_objekt_formset_readonly": not check_permissions(p.actionChoices.archz_vedouci_smazat, request.user, zaznam.ident_cely),
            "title": _("arch_z.views.edit.title.text"),
            "header": _("arch_z.views.edit.header.text"),
            "button": _("arch_z.views.edit.submitButton.text"),
            "sam_akce": False if zaznam.akce.projekt else True,
            "heslar_specifikace_v_letech_presne": HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRESNE,
            "heslar_specifikace_v_letech_priblizne": HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRIBLIZNE,
            "arch_z_ident_cely":zaznam.ident_cely,
            "toolbar_name": _("arch_z.views.edit.toolbar_name.text"),
            "katastry_edit": zaznam.dokumentacni_jednotky_akce.count()==1 and  zaznam.dokumentacni_jednotky_akce.first().typ.id==TYP_DJ_KATASTR,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def odeslat(request, ident_cely):
    """
    Funkce pohledu pro zobrazení a spracováni odeslání akce.
    Na začátku se kontroluje jestli stav není jiný než zapsaný nebo nekdo nezmenil stav akce počas odesílaní.
    Při get volání se kontrolují vyplnená pole akce a její relaci pomoci metódy na modelu.
    Po post volání se volá metóda na modelu pro posun stavu do odeslaná.
    """
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    az: ArcheologickyZaznam
    if az.stav != AZ_STAV_ZAPSANY:
        logger.debug("arch_z.views.odeslat permission denied")
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": az.get_absolute_url()},
            status=403,
        )
    if check_stav_changed(request, az):
        logger.debug("arch_z.views.odeslat.redirec_to_arch_z:detail")
        return JsonResponse(
            {"redirect": az.get_absolute_url()},
            status=403,
        )
    if request.method == "POST":
        fedora_trasnaction = FedoraTransaction()
        az.active_transaction = fedora_trasnaction
        az.set_odeslany(request.user, request, messages)
        az.save()
        if az.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            all_akce = Akce.objects.filter(projekt=az.akce.projekt).filter(
                archeologicky_zaznam__stav=AZ_STAV_ZAPSANY
            )
            if not all_akce and az.akce.projekt.stav == PROJEKT_STAV_UKONCENY_V_TERENU:
                request.session["arch_projekt_link_uzavrit"] = True
        messages.add_message(
            request, messages.SUCCESS, get_message(az, "USPESNE_ODESLANA")
        )
        logger.debug("arch_z.views.odeslat.akce_uspesne_odeslana",
                     extra={"info": get_message(az, "USPESNE_ODESLANA")})
        az.close_active_transaction_when_finished = True
        az.save()
        return JsonResponse({"redirect": az.get_absolute_url()})
    else:
        warnings = az.check_pred_odeslanim()
        logger.debug("arch_z.views.odeslat.warnings", extra={"ident_cely": ident_cely, "warnings": str(warnings)})

        if warnings:
            request.session["temp_data"] = warnings
            messages.add_message(
                request, messages.ERROR, get_message(az, "NELZE_ODESLAT")
            )
            logger.debug("arch_z.views.odeslat_akci_nelze_odeslat")
            return JsonResponse(
                {"redirect": az.get_absolute_url()},
                status=403,
            )
    form_check = CheckStavNotChangedForm(initial={"old_stav": az.stav})
    context = {
        "object": az,
        "title": _("arch_z.views.odeslat.title.text"),
        "id_tag": "odeslat-akci-form",
        "button": _("arch_z.views.odeslat.submitButton.text"),
        "form_check": form_check,
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def archivovat(request, ident_cely):
    """
    Funkce pohledu pro zobrazení a spracováni archivace akce.
    Na začátku se kontroluje jestli stav není jiný než odeslaný nebo nekdo nezmenil stav akce počas archivace.
    Při get volání se kontrolují vyplnená pole akce a její relaci pomoci metódy na modelu.
    Po post volání se volá metóda na modelu pro posun stavu do odeslaná.
    """
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if az.stav != AZ_STAV_ODESLANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": az.get_absolute_url()},
            status=403,
        )
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, az):
        return JsonResponse(
            {"redirect": az.get_absolute_url()},
            status=403,
        )
    if request.method == "POST":
        fedora_trasnaction = FedoraTransaction()
        az.active_transaction = fedora_trasnaction
        az.set_archivovany(request.user)
        if az.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            all_akce = Akce.objects.filter(projekt=az.akce.projekt).exclude(
                archeologicky_zaznam__stav=AZ_STAV_ARCHIVOVANY
            )
            if not all_akce and az.akce.projekt.stav == PROJEKT_STAV_UZAVRENY:
                request.session["arch_projekt_link"] = True
        messages.add_message(
            request, messages.SUCCESS, get_message(az, "USPESNE_ARCHIVOVANA")
        )
        Mailer.send_ea02(arch_z=az)
        az.close_active_transaction_when_finished = True
        az.save()
        return JsonResponse({"redirect": az.get_absolute_url()})
    else:
        warnings = az.check_pred_archivaci()
        logger.debug("arch_z.views.archivovat", extra={"warnings": warnings})
        if warnings:
            request.session["temp_data"] = warnings
            messages.add_message(
                request, messages.ERROR, get_message(az, "NELZE_ARCHIVOVAT")
            )
            return JsonResponse(
                {"redirect": az.get_absolute_url()},
                status=403,
            )
    form_check = CheckStavNotChangedForm(initial={"old_stav": az.stav})
    context = {
        "object": az,
        "title": _("arch_z.views.archivovat.title.text"),
        "id_tag": "archivovat-akci-form",
        "button": _("arch_z.views.archivovat.submitButton.text"),
        "form_check": form_check,
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    """
    Funkce pohledu pro zobrazení a spracováni vrácení stacu akce o jedno naspátek.
    Na začátku se kontroluje jestli nekdo nezmenil stav akce počas vrácení.
    Pro vrácení se používa formulář pro vrácení, který je jednotný napríč aplikací.
    Po post volání se volá metóda na modelu pro posun stavu naspátek.
    Pokud se jedná o projektovou akci, tak se vrací i stav projektu ze stavu uzavřený nebo archivovaný.
    """
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if az.stav != AZ_STAV_ODESLANY and az.stav != AZ_STAV_ARCHIVOVANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": az.get_absolute_url()},
            status=403,
        )
    if check_stav_changed(request, az):
        return JsonResponse(
            {"redirect": az.get_absolute_url()},
            status=403,
        )
    if request.method == "POST":
        form = VratitForm(request.POST)
        if form.is_valid():
            fedora_trasnaction = FedoraTransaction()
            az.active_transaction = fedora_trasnaction
            duvod = form.cleaned_data["reason"]
            projekt = None
            if az.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
                projekt = az.akce.projekt
            # BR-A-3
            if az.stav == AZ_STAV_ODESLANY and projekt is not None:
                #  Return also project from the states P6 or P5 to P4
                projekt.active_transaction = fedora_trasnaction
                projekt_stav = projekt.stav
                logger.debug("arch_z.views.vratit.valid", extra={"ident": ident_cely, "stav": projekt.stav})
                if projekt_stav == PROJEKT_STAV_UZAVRENY:
                    projekt.set_vracen(
                        request.user, projekt_stav - 1, "Automatické vrácení projektu"
                    )
                    projekt.save()
                if projekt_stav == PROJEKT_STAV_ARCHIVOVANY:
                    projekt.set_vracen(
                        request.user, projekt_stav - 1, "Automatické vrácení projektu"
                    )
                    projekt.save()
                    projekt.set_vracen(
                        request.user, projekt_stav - 2, "Automatické vrácení projektu"
                    )
                    projekt.save()
            before_save_state = az.stav
            az.set_vraceny(request.user, az.stav - 1, duvod)
            az.close_active_transaction_when_finished = True
            az.save()
            if before_save_state == AZ_STAV_ODESLANY:
                Mailer.send_ev01(zaznam=az, reason=duvod)
            messages.add_message(
                request, messages.SUCCESS, get_message(az, "USPESNE_VRACENA")
            )
            return JsonResponse({"redirect": az.get_absolute_url()})
        else:
            logger.debug("arch_z.views.vratit.not_valid", extra={"errors": form.errors})
    else:
        form = VratitForm(initial={"old_stav": az.stav})
    context = {
        "object": az,
        "form": form,
        "title": _("arch_z.views.vratit.title.text"),
        "id_tag": "vratit-akci-form",
        "button": _("arch_z.views.vratit.submitButton.text"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def zapsat(request, projekt_ident_cely=None):
    """
    Funkce pohledu pro vytvoření akce.
    Na začátku se kontroluje jestli jde o vytvoření projektové nebo samostatné akce a případne či je možné vytvořit projektovou akci.
    Zobrazení pozostáva ze 3 formulářů: CreateArchZForm, CreateAkceForm, formset na další vedoucí.
    """
    if projekt_ident_cely:
        projekt = get_object_or_404(Projekt, ident_cely=projekt_ident_cely)
        # Projektove akce lze pridavat pouze pokud je projekt jiz prihlasen
        if not PROJEKT_STAV_ZAPSANY < projekt.stav < PROJEKT_STAV_ARCHIVOVANY:
            logger.debug(
                "arch_z.views.zapsat.stav_error", extra={"projekt_ident_cely": projekt_ident_cely, "stav": projekt.stav}
            )
            raise PermissionDenied(
                "Nelze pridat akci k projektu ve stavu " + str(projekt.stav)
            )
        # Projektove akce nelze vytvorit pro projekt typu pruzkum
        if projekt.typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID:
            logger.debug(
                "arch_z.views.zapsat.typ_projektu_error", extra={"projekt_ident_cely": projekt_ident_cely,
                                                                 "stav": projekt.stav}
            )
            raise PermissionDenied(
                f"Nelze pridat akci k projektu typu {projekt.typ_projektu}"
            )
        uzamknout_specifik = True
        context = {
            "title": _("arch_z.views.zapsat.projektovaAkce.title.text"),
            "header": _("arch_z.views.zapsat.projektovaAkce.header.text"),
            "create_akce": False,
            "projekt_ident_cely": projekt_ident_cely,
        }
    else:
        projekt = None
        uzamknout_specifik = False
        context = {
            "title": _("arch_z.views.zapsat.samostatnaAkce.title.text"),
            "header": _("arch_z.views.zapsat.samostatnaAkce.header.text"),
            "create_akce": True,
            "sam_akce": True,
        }

    required_fields = get_required_fields()
    required_fields_next = get_required_fields(next=1)
    if request.method == "POST":
        form_az = CreateArchZForm(request.POST)
        form_akce = CreateAkceForm(
            request.POST,
            required=required_fields,
            required_next=required_fields_next,
            uzamknout_specifikace=uzamknout_specifik,
        )
        ostatni_vedouci_objekt_formset = inlineformset_factory(
            Akce,
            AkceVedouci,
            form=create_akce_vedouci_objekt_form(readonly=False),
            extra=1,
            can_delete=False,
        )
        ostatni_vedouci_objekt_formset = ostatni_vedouci_objekt_formset(
            request.POST,
            instance=None,
            prefix="_osv",
        )
        if (
            form_az.is_valid()
            and form_akce.is_valid()
            and ostatni_vedouci_objekt_formset.is_valid()
        ):
            logger.debug("arch_z.views.zapsat.form_valid", extra={"projekt_ident_cely": projekt_ident_cely})
            az = form_az.save(commit=False)
            az: ArcheologickyZaznam
            fedora_transaction = FedoraTransaction()
            az.active_transaction = fedora_transaction
            az.stav = AZ_STAV_ZAPSANY
            az.typ_zaznamu = ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
            try:
                if projekt:
                    az.ident_cely = get_project_event_ident(projekt)
                    typ_akce = Akce.TYP_AKCE_PROJEKTOVA
                else:
                    az.ident_cely = get_temp_akce_ident(
                        az.hlavni_katastr.okres.kraj.rada_id
                    )
                    typ_akce = Akce.TYP_AKCE_SAMOSTATNA
            except MaximalEventCount:
                messages.add_message(request, messages.ERROR, MAXIMUM_AKCII_DOSAZENO)
            else:
                if FedoraRepositoryConnector.check_container_deleted_or_not_exists(az.ident_cely,
                                                                                   "archeologicky_zaznam"):
                    az.save()
                    form_az.save_m2m()
                    # This must be called to save many to many (katastry)
                    # since we are doing commit = False
                    az.set_zapsany(request.user)
                    akce = form_akce.save(commit=False)

                    if typ_akce == Akce.TYP_AKCE_PROJEKTOVA:
                        akce.specifikace_data = Heslar.objects.get(
                            id=SPECIFIKACE_DATA_PRESNE
                        )
                    akce.archeologicky_zaznam = az
                    akce.active_transaction = fedora_transaction
                    akce.projekt = projekt
                    akce.typ = typ_akce
                    akce.save()

                    ostatni_vedouci_objekt_formset = inlineformset_factory(
                        Akce,
                        AkceVedouci,
                        form=create_akce_vedouci_objekt_form(readonly=False),
                        extra=1,
                        can_delete=False,
                    )
                    ostatni_vedouci_objekt_formset = ostatni_vedouci_objekt_formset(
                        request.POST,
                        instance=akce,
                        prefix="_osv",
                    )
                    if ostatni_vedouci_objekt_formset.is_valid():
                        ostatni_vedouci_objekt_formset.save()
                    else:
                        logger.debug("arch_z.views.zapsat.form_not_valid",
                                     extra={"errors": ostatni_vedouci_objekt_formset.errors})
                    akce.set_snapshots()
                    messages.add_message(
                        request, messages.SUCCESS, get_message(az, "USPESNE_ZAPSANA")
                    )
                    logger.debug("arch_z.views.zapsat.success", extra={"akce": akce.pk, "projekt": projekt_ident_cely})
                    az.close_active_transaction_when_finished = True
                    az.save()
                    return redirect("arch_z:detail", az.ident_cely)
                else:
                    fedora_transaction.rollback_transaction()
                    logger.debug("arch_z.views.zapsat.check_container_deleted_or_not_exists.incorrect",
                                 extra={"ident_cely": az.ident_cely})
                    messages.add_message(
                        request, messages.ERROR, _("arch_z.views.zapsat.samostatnaAkce."
                                                   "check_container_deleted_or_not_exists_error"))
        else:
            logger.debug("arch_z.views.zapsat.not_valid", extra={"form_az_errors": form_az,
                                                                 "form_akce_errors": form_akce.errors})

    else:
        ostatni_vedouci_objekt_formset = inlineformset_factory(
            Akce,
            AkceVedouci,
            form=create_akce_vedouci_objekt_form(readonly=False),
            extra=3,
            can_delete=False,
        )
        ostatni_vedouci_objekt_formset = ostatni_vedouci_objekt_formset(
            None,
            instance=None,
            prefix="_osv",
        )
        form_az = CreateArchZForm(projekt=projekt)
        form_akce = CreateAkceForm(
            projekt=projekt,
            required=required_fields,
            required_next=required_fields_next,
            uzamknout_specifikace=uzamknout_specifik,
        )
    context.update(
        {
            "formAZ": form_az,
            "formAkce": form_akce,
            "ostatni_vedouci_objekt_formset": ostatni_vedouci_objekt_formset,
            "ostatni_vedouci_objekt_formset_helper": AkceVedouciFormSetHelper(),
            "ostatni_vedouci_objekt_formset_readonly": True,
            "button": _("arch_z.views.zapsat.submitButton.text"),
            "toolbar_name": _("arch_z.views.zapsat.toolbarName"),
            "heslar_specifikace_v_letech_presne": HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRESNE,
            "heslar_specifikace_v_letech_priblizne": HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRIBLIZNE,
        }
    )
    return render(
        request,
        "arch_z/create.html",
        context,
    )


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    """
    Funkce pohledu pro zobrazení a spracováni smazání akce.
    Na začátku se kontroluje jestli nekdo nezmenil stav akce počas smazání.
    Po post volání se volá metóda na modelu pro smazání akce.
    """
    az: ArcheologickyZaznam = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if check_stav_changed(request, az):
        return JsonResponse(
            {"redirect": az.get_absolute_url()},
            status=403,
        )
    if az.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
        projekt = az.akce.projekt
    else:
        projekt = None
    if request.method == "POST":
        fedora_transaction = FedoraTransaction()
        try:
            az.active_transaction = fedora_transaction
            az.skip_container_check = True
            az.close_active_transaction_when_finished = True
            az.deleted_by_user = request.user
            az.record_deletion(fedora_transaction)
            for dj in az.dokumentacni_jednotky_akce.all():
                dj: DokumentacniJednotka
                dj.active_transaction = fedora_transaction
                dj.suppress_signal_arch_z = True
                dj.delete()
            if az.externi_odkazy:
                for eo in az.externi_odkazy.all():
                    eo.suppress_signal_arch_z = True
                    eo.active_transaction = az.active_transaction
                    eo.delete()
                invalidate_model(ExterniZdroj)
            for pk in az.initial_casti_dokumentu:
                item = DokumentCast.objects.get(pk=pk)
                item.suppress_signal_arch_z = True
                item.active_transaction = fedora_transaction
                item.delete()
            from arch_z.signals import invalidate_arch_z_related_models
            invalidate_arch_z_related_models()
            az.delete()
            logger.debug("arch_z.views.smazat.success", extra={"ident_cely": ident_cely,
                                                               "transaction": fedora_transaction})
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
        except RestrictedError as err:
            logger.debug("arch_z.views.smazat.error", extra={"ident_cely": ident_cely, "err": err})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT_NAVAZANE_ZAZNAMY)
            fedora_transaction.rollback_transaction()
            return JsonResponse(
                {"redirect": az.get_absolute_url()},
                status=403,
            )

        if projekt:
            return JsonResponse(
                {
                    "redirect": reverse(
                        "projekt:detail", kwargs={"ident_cely": projekt.ident_cely}
                    )
                }
            )
        else:
            if az.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA:
                return JsonResponse({"redirect": reverse("lokalita:index")})
            else:
                return JsonResponse({"redirect": reverse("arch_z:index")})
    else:
        form_check = CheckStavNotChangedForm(initial={"old_stav": az.stav})
        context = {
            "object": az,
            "title": _("arch_z.views.smazat.title.text"),
            "id_tag": "smazat-akci-form",
            "button": _("arch_z.views.smazat.submitButton.text"),
            "form_check": form_check,
        }
        return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def pripojit_dokument(request, arch_z_ident_cely, proj_ident_cely=None):
    """
    Funkce pohledu pro připojení dokumentu do akce.
    Funkce volá další funkci pro připojení s parametrem třídou modelu navíc.
    """
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=arch_z_ident_cely)
    if proj_ident_cely is not None and az.akce.projekt.ident_cely != proj_ident_cely:
        logger.error("Archeologiky zaznam - Projekt wrong relation")
        messages.add_message(
                    request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA
                )
        return JsonResponse({"redirect": az.get_absolute_url()},status=403)
    return pripojit(request, arch_z_ident_cely, proj_ident_cely, ArcheologickyZaznam)


@login_required
@require_http_methods(["GET", "POST"])
def odpojit_dokument(request, ident_cely, arch_z_ident_cely):
    """
    Funkce pohledu pro odpojení dokumentu do akce.
    Funkce volá další funkci pro odpojení s parametrem navíc - arch záznamem.
    """
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=arch_z_ident_cely)
    relace_dokumentu = DokumentCast.objects.filter(dokument__ident_cely=ident_cely, archeologicky_zaznam=az)
    if not relace_dokumentu.count() > 0:
        logger.error("Archeologiky zaznam - Dokument wrong relation")
        messages.add_message(
                    request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA
                )
        return JsonResponse({"redirect": az.get_absolute_url()},status=403)
    return odpojit(request, ident_cely, arch_z_ident_cely, az)


@login_required
@require_http_methods(["POST"])
def post_ajax_get_pians(request):
    """
    Vypada nepouzito check s J. Bartos
    """
    body = json.loads(request.body.decode("utf-8"))
    pians = get_dj_pians_centroid(body["dj_ident_cely"], body["lat"], body["lng"])
    back = []
    for pian in pians:
        back.append(
            {
                "id": pian.id,
                "ident_cely": pian.ident_cely,
                "geom": pian.geometry.replace(", ", ","),
                "dj": pian.dj,
            }
        )
    if len(pians) > 0:
        return JsonResponse({"points": back}, status=200)
    else:
        return JsonResponse({"points": []}, status=200)


@login_required
@require_http_methods(["POST"])
def post_ajax_get_pians_limit(request):
    """
    Funkce pohledu pro získaní pianu pro zobrazení heat mapy.
    """
    body = json.loads(request.body.decode("utf-8"))
    num = get_num_pians_from_envelope(
        body["southEast"]["lng"],
        body["northWest"]["lat"],
        body["northWest"]["lng"],
        body["southEast"]["lat"],
    )
    clusters = num >= 500
    logger.debug("arch_z.views.post_ajax_get_pians_limit.pocet_geometrii", extra={"num": num})
    if num < 5000:
        pians = get_dj_pians_from_envelope(
            body["southEast"]["lng"],
            body["northWest"]["lat"],
            body["northWest"]["lng"],
            body["southEast"]["lat"],
            body["dj_ident_cely"],
        )
        back = []
        for pian in pians:
            back.append(
                {
                    "id": pian.id,
                    "ident_cely": pian.ident_cely,
                    "geom": pian.geometry.replace(", ", ",")
                    if not clusters
                    else pian.centroid.replace(", ", ","),
                    "dj": pian.dj,
                    "presnost": pian.presnost.zkratka,
                }
            )
        if len(pians) > 0:
            return JsonResponse(
                {
                    "points": back,
                    "algorithm": "detail",
                    "count": num,
                    "clusters": clusters,
                },
                status=200,
            )
        else:
            return JsonResponse(
                {"points": [], "algorithm": "detail", "count": 0, "clusters": clusters},
                status=200,
            )
    else:
        density = get_heatmap_pian_density(
            body["southEast"]["lng"],
            body["northWest"]["lat"],
            body["northWest"]["lng"],
            body["southEast"]["lat"],
            body["zoom"],
        )
        logger.debug("arch_z.views.post_ajax_get_pians_limit.density", extra={"density": density})

        heats = get_heatmap_pian(
            body["southEast"]["lng"],
            body["northWest"]["lat"],
            body["northWest"]["lng"],
            body["southEast"]["lat"],
            body["zoom"],
        )
        back = []
        cid = 0
        for heat in heats:
            cid += 1
            back.append(
                {
                    "id": str(cid),
                    "pocet": heat["count"],
                    "density": heat["count"] / density,
                    "geom": heat["geometry"].replace(", ", ","),
                }
            )
        if len(heat) > 0:
            return JsonResponse({"heat": back, "algorithm": "heat"}, status=200)
        else:
            return JsonResponse({"heat": [], "algorithm": "heat"}, status=200)


@login_required
@require_http_methods(["POST"])
def post_akce2kat(request):
    """
    Funkce pohledu pro získaní souradnic katastru akce.
    """
    body = json.loads(request.body.decode("utf-8"))
    logger.debug("arch_z.views.post_akce2kat.start", extra={"body": body})
    katastr_name = body["cadastre"]
    katastr_nazev, okres_nazev = [x.strip(")").strip() for x in katastr_name.split("(")]
    katastr = RuianKatastr.objects.get(nazev__iexact=katastr_nazev, okres__nazev__iexact=okres_nazev)
    akce_ident_cely = body["akce_ident_cely"]

    if len(katastr_name) > 0:
        try:
            pians = get_pians_from_akce(katastr, akce_ident_cely)            
            return JsonResponse(
                    {
                        "pians": pians,
                        "count": len(pians),                        
                    },
                    status=200,
                )
        except CannotFindCadasterCentre as err:
            logger.error("arch_z.views.post_akce2kat.error", extra={"err": err})
            return JsonResponse({ "pians": [], "count": 0,    }, status=200)


def get_history_dates(historie_vazby, request_user):
    """
    Funkce pro získaní dátumů pro historii.

    Args:     
        historie_vazby (HistorieVazby): model historieVazby dané akce.
    
    Returns:
        historie: dictionary dátumů k historii.
    """
    request_user: User
    anonymized = not request_user.hlavni_role.pk in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)
    historie = {
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_AZ, anonymized),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_AZ, anonymized),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_AZ, anonymized),
    }
    return historie


def get_detail_template_shows(archeologicky_zaznam, dok_jednotky, user, app="akce"):
    """
    Funkce pro získaní dictionary uživatelských akcí které mají být zobrazeny uživately.

    Args:     
        archeologicky_zaznam (ArcheologickyZaznam): model ArcheologickyZaznam pro který se dané akce počítají.

        dok_jednotky (DokumentacniJednotka): model DokumentacniJednotka pro který se dané akce počítají.

        user (AuthUser): uživatel pro kterého se dané akce počítají.

        app (string): druh archeologického záznamu ro který se dané akce počítají.
    
    Returns:
        historie: dictionary možností pro zobrazení.
    """
    show_vratit = check_permissions(p.actionChoices.archz_vratit, user, archeologicky_zaznam.ident_cely)
    show_odeslat = check_permissions(p.actionChoices.archz_odeslat, user, archeologicky_zaznam.ident_cely)
    show_archivovat = check_permissions(p.actionChoices.archz_archivovat, user, archeologicky_zaznam.ident_cely)
    show_arch_links = archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
    zmenit_proj_akci = False
    zmenit_sam_akci = False
    if archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
        show_edit = check_permissions(p.actionChoices.archz_edit, user, archeologicky_zaznam.ident_cely)
        logger.debug(show_edit)
        if archeologicky_zaznam.akce.typ == Akce.TYP_AKCE_PROJEKTOVA:
            zmenit_proj_akci = check_permissions(p.actionChoices.archz_zmenit_proj, user, archeologicky_zaznam.ident_cely)
            show_pripojit_dokumenty = check_permissions(p.actionChoices.archz_pripojit_dok_proj, user, archeologicky_zaznam.ident_cely)
        else:
            zmenit_sam_akci = check_permissions(p.actionChoices.archz_zmenit_sam, user, archeologicky_zaznam.ident_cely)
            show_pripojit_dokumenty = check_permissions(p.actionChoices.archz_pripojit_dok, user, archeologicky_zaznam.ident_cely)
        if (
            archeologicky_zaznam.akce.typ == Akce.TYP_AKCE_SAMOSTATNA
            and dok_jednotky.count() == 1
            and dok_jednotky.first().typ == Heslar.objects.get(id=TYP_DJ_KATASTR)
            and not check_permissions(p.actionChoices.archz_dj_zapsat, user, archeologicky_zaznam.ident_cely)
        ) or dok_jednotky.filter(typ__id=TYP_DJ_KATASTR).exists():
            add_dj = False
        else:
            add_dj = True
    else:
        show_edit = check_permissions(p.actionChoices.lokalita_edit, user, archeologicky_zaznam.ident_cely)
        show_pripojit_dokumenty = check_permissions(p.actionChoices.archz_pripojit_dok, user, archeologicky_zaznam.ident_cely)
        if dok_jednotky.count() == 0 and check_permissions(p.actionChoices.lokalita_dj_zapsat, user, archeologicky_zaznam.ident_cely):
            add_dj = True
        else:
            add_dj = False
    show = {
        "vratit_link": show_vratit,
        "odeslat_link": show_odeslat,
        "archivovat_link": show_archivovat,
        "editovat": show_edit,
        "arch_links": show_arch_links,
        "pripojit_dokumenty": show_pripojit_dokumenty,
        "add_dj": add_dj,
        "zmenit_proj_akci": zmenit_proj_akci,
        "zmenit_sam_akci": zmenit_sam_akci,
        "smazat": check_permissions(p.actionChoices.archz_smazat, user, archeologicky_zaznam.ident_cely),
        "dokument_odpojit": check_permissions(p.actionChoices.archz_odpojit_dokument, user, archeologicky_zaznam.ident_cely),
        "komponenta_smazat": check_permissions(p.actionChoices.komponenta_smazat_akce, user, archeologicky_zaznam.ident_cely),
        "pripojit_eo": check_permissions(p.actionChoices.eo_pripojit_ez, user, archeologicky_zaznam.ident_cely),
        "odpojit_eo": check_permissions(p.actionChoices.eo_odpojit_ez, user, archeologicky_zaznam.ident_cely),
        "paginace_edit": check_permissions(p.actionChoices.eo_edit_akce, user, archeologicky_zaznam.ident_cely),
        "nalez_smazat": check_permissions(p.actionChoices.nalez_smazat_akce, user, archeologicky_zaznam.ident_cely),
        "zapsat_dokumenty": check_permissions(p.actionChoices.dok_zapsat_do_archz, user, archeologicky_zaznam.ident_cely),
        "stahnout_metadata": check_permissions(p.actionChoices.stahnout_metadata, user, archeologicky_zaznam.ident_cely),
    }
    return show


def get_required_fields(zaznam=None, next=0):
    """
    Funkce pro získaní dictionary povinných polí podle stavu arch záznamů.

    Args:     
        zaznam (ArcheologickyZaznam): model ArcheologickyZaznam pro který se dané pole počítají.

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
        required_fields = []
    if stav > AZ_STAV_ZAPSANY - next:
        required_fields += [
            "lokalizace_okolnosti",
            "hlavni_vedouci",
            "organizace",
            "datum_ukonceni",
            "hlavni_typ",
            "datum_zahajeni",
        ]
    return required_fields


@login_required
@require_http_methods(["GET", "POST"])
def smazat_akce_vedoucí(request, ident_cely, akce_vedouci_id):
    """
    Funkce pohledu pro smazání dalšího vedoucího akce.
    """
    logger.debug("arch_z.views.smazat_akce_vedoucí.start", extra={"ident_cely": ident_cely,
                                                                  "akce_vedouci_id": akce_vedouci_id})
    zaznam: AkceVedouci = AkceVedouci.objects.get(id=akce_vedouci_id)
    az: ArcheologickyZaznam = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if request.method == "POST":
        if zaznam.akce.archeologicky_zaznam.ident_cely != ident_cely:
            logger.debug("arch_z.views.smazat_akce_vedoucí.error",
                         extra={"ident_cely": ident_cely, "akce_vedouci_id": akce_vedouci_id})
            messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
            return JsonResponse({"redirect": az.get_absolute_url()}, status=403)
        zaznam.delete()
        fedora_transaction = FedoraTransaction()
        az.save_metadata(fedora_transaction, close_transaction=True)
        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
        logger.debug("arch_z.views.smazat_akce_vedoucí.success", extra={"ident_cely": ident_cely,
                                                                      "akce_vedouci_id": akce_vedouci_id})
        return JsonResponse(
            {"redirect": reverse("arch_z:edit", kwargs={"ident_cely": ident_cely})}
        )
    else:
        logger.debug("arch_z.views.smazat_akce_vedoucí.get", extra={"ident_cely": ident_cely,
                                                                      "akce_vedouci_id": akce_vedouci_id})
        context = {
            "object": zaznam,
            "title": _("arch_z.views.smazat_akce_vedoucí.title.text"),
            "id_tag": "smazat-objekt-form",
            "button": _("core.views.smazat.submitButton.text"),
        }
        return render(request, "core/transakce_modal.html", context)

    
class GetAkceOtherKatastrView(LoginRequiredMixin, View, PermissionFilterMixin):
    typ_zmeny_lookup = ZAPSANI_AZ

    def post(self, request):
        """
        Trida pohledu pro získaní souradnic dalších katastrů akce.
        """
        body = json.loads(request.body.decode("utf-8"))
        arch_zaznam = ArcheologickyZaznam.objects.filter(ident_cely=body["akce_ident_cely"])
        back = []

        if self.check_filter_permission(arch_zaznam).count() > 0:
            dis = get_all_pians_with_akce(body["akce_ident_cely"])
            for di in dis:
                back.append(
                    {
                        # "id": pian.id,
                        "pian_ident_cely": di["pian_ident_cely"],
                        "pian_geom": di["pian_geom"].replace(", ", ","),
                        "dj": di["dj"],
                        "dj_katastr": di["dj_katastr"],
                    }
                )
            if len(dis) > 0:
                return JsonResponse({"points": back}, status=200)
        return JsonResponse({"points": []}, status=200)


class AkceIndexView(LoginRequiredMixin, TemplateView):
    """
    Třida pohledu pro zobrazení domovské stránky akcií s navigačními možnostmi.
    """
    template_name = "arch_z/index.html"

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní kontextu podlehu.
        """
        context = {
            "toolbar_name": _("arch_z.views.akceIndexView.toolbarName"),
        }
        return context


class AkceListView(SearchListView):
    """
    Třida pohledu pro zobrazení listu/tabulky s akcemi.
    """
    table_class = AkceTable
    model = Akce
    filterset_class = AkceFilter
    export_name = "export_akce_"
    app = "akce"
    toolbar = "toolbar_akce.html"
    permission_model_lookup = "archeologicky_zaznam__"
    typ_zmeny_lookup = ZAPSANI_AZ
    redis_snapshot_prefix = "akce"
    redis_value_list_field = "archeologicky_zaznam__ident_cely"

    def init_translations(self):
        super().init_translations()
        self.page_title = _("arch_z.views.AkceListView.page_title.text")
        self.search_sum = _("arch_z.views.AkceListView.search_sum.text")
        self.pick_text = _("arch_z.views.AkceListView.pick_text.text")
        self.hasOnlyVybrat_header = _("arch_z.views.AkceListView.hasOnlyVybrat_header.text")
        self.hasOnlyVlastnik_header = _("arch_z.views.AkceListView.hasOnlyVlastnik_header.text")
        self.hasOnlyArchive_header = _("arch_z.views.AkceListView.hasOnlyArchive_header.text")
        self.hasOnlyPotvrdit_header = _("arch_z.views.AkceListView.hasOnlyPotvrdit_header.text")
        self.hasOnlyNase_header = _("arch_z.views.AkceListView.hasOnlyNase_header.text")
        self.default_header = _("arch_z.views.AkceListView.default_header.text")
        self.toolbar_name = _("arch_z.views.AkceListView.toolbar_name.text")

    @staticmethod
    def rename_field_for_ordering(field: str):
        field = field.replace("-", "")
        return {
            "ident_cely": "archeologicky_zaznam__ident_cely",
            "pristupnost": "archeologicky_zaznam__pristupnost__razeni",
            "hlavni_katastr": "archeologicky_zaznam__hlavni_katastr__nazev",
            "katastry": "archeologicky_zaznam__katastry__nazev",
            "stav": "archeologicky_zaznam__stav",
            "organizace": "organizace__nazev_zkraceny",
            "vedouci_organizace": "vedouci_organizace",
            "vedouci": "vedouci_snapshot",
            "hlavni_vedouci": "hlavni_vedouci__vypis_cely",
            "uzivatelske_oznaceni": "archeologicky_zaznam__uzivatelske_oznaceni",
            "specifikace_data" :"specifikace_data__razeni",
            "hlavni_typ":"hlavni_typ__razeni",
            "vedlejsi_typ":"vedlejsi_typ__razeni",
        }.get(field, field)

    def get_queryset(self):
        sort_params = self._get_sort_params()
        sort_params = [self.rename_field_for_ordering(x) for x in sort_params]
        qs = super().get_queryset()
        qs = qs.order_by(*sort_params)            
        qs = qs.distinct("pk", *sort_params)
        qs = (
            qs.select_related(
                "archeologicky_zaznam__hlavni_katastr",
                "archeologicky_zaznam__hlavni_katastr__okres",
                "organizace",
                "hlavni_vedouci",  
           ).prefetch_related(
                "archeologicky_zaznam__pristupnost",
                "archeologicky_zaznam__katastry",
                "archeologicky_zaznam__katastry__okres",
                "specifikace_data",
                "hlavni_typ",
                "vedlejsi_typ",
                "akcevedouci_set__organizace",
                "archeologicky_zaznam__dokumentacni_jednotky_akce",
                "archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty",
                "archeologicky_zaznam__dokumentacni_jednotky_akce__adb",
                "archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__predmety",
                "archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__objekty",
                "archeologicky_zaznam__casti_dokumentu",
                "archeologicky_zaznam__casti_dokumentu__dokument",
            )
        )
        qs.cache()
        return self.check_filter_permission(qs)


class ProjektAkceChange(LoginRequiredMixin, AkceRelatedRecordUpdateView):
    """
    Třida pohledu pro zmenu projektové akce na samostatnou.
    """
    template_name = "core/transakce_modal.html"

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní kontextu podlehu.
        """
        az = self.get_archeologicky_zaznam()
        form_check = CheckStavNotChangedForm(initial={"old_stav": az.stav})
        context = {
            "object": az,
            "title": _("arch_z.views.ProjektAkceChange.title.text"),
            "id_tag": "zmenit-akci-form",
            "button": _("arch_z.views.ProjektAkceChange.submitButton.text"),
            "form_check": form_check,
        }
        return context

    def get(self, request, *args, **kwargs):
        """
        Metóda pro vrácení stránky pri voláni GET.
        """
        context = self.get_context_data(**kwargs)
        if check_stav_changed(request, context["object"]):
            return JsonResponse(
                {"redirect": context["object"].get_absolute_url()},
                status=403,
            )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Metóda po potvrzení zmeny akce na samostatnou.
        Pri zavolíní se kontroluje, že akce nebyla změnena v mezičase potvrzení.
        Po úspešné kontrole se odebere projekt, nastaví typ akce na samostatnú a nastaví nový ident celý.
        Celá událost je zapsaná do historie.
        Uživatel je presmerován na detail akce.
        """
        context = self.get_context_data(**kwargs)
        fedora_transaction = FedoraTransaction()
        az = context["object"]
        if check_stav_changed(request, az):
            return JsonResponse(
                {"redirect": az.get_absolute_url()},
                status=403,
            )
        akce: Akce = az.akce
        akce.active_transaction = fedora_transaction
        az.active_transaction = fedora_transaction
        akce.projekt = None
        akce.typ = Akce.TYP_AKCE_SAMOSTATNA
        akce.save()
        old_ident = az.ident_cely
        az.set_akce_ident(get_akce_ident(az.hlavni_katastr.okres.kraj.rada_id), delete_container=False)
        Historie(
            typ_zmeny=ZMENA_AZ,
            uzivatel=request.user,
            poznamka=f"{old_ident} -> {az.ident_cely}",
            vazba=az.historie,
        ).save()
        invalidate_model(ArcheologickyZaznam)
        az.close_active_transaction_when_finished = True
        az.save()
        logger.debug("arch_z.views.ProjektAkceChange.post", extra={"az_ident_cely": str(az.ident_cely)})
        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)

        return JsonResponse({"redirect": az.get_absolute_url()})


class SamostatnaAkceChange(LoginRequiredMixin, AkceRelatedRecordUpdateView):
    """
    Třida pohledu pro zmenu samostatní akce na projektovou.
    """
    template_name = "core/transakce_table_modal.html"

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní kontextu podlehu.
        """
        az = self.get_archeologicky_zaznam()
        form_check = CheckStavNotChangedForm(initial={"old_stav": az.stav})
        context = {
            "object": az,
            "title": _("arch_z.views.SamostatnaAkceChange.title.text"),
            "id_tag": "akce-change-form",
            "button": _("arch_z.views.SamostatnaAkceChange.submitButton.text"),
            "form_check": form_check,
        }
        return context

    def get(self, request, *args, **kwargs):
        """
        Metóda pro vrácení stránky pri voláni GET s formulářem pro výber projektu.
        """
        context = self.get_context_data(**kwargs)
        if check_stav_changed(request, context["object"]):
            return JsonResponse(
                {"redirect": context["object"].get_absolute_url()},
                status=403,
            )
        form = PripojitProjektForm()
        context["form"] = form
        context["hide_table"] = True
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Metóda po potvrzení zmeny akce na projektovou.
        Pri zavolíní se kontroluje, že akce nebyla změnena v mezičase potvrzení.
        Po úspešné kontrole se napojí projekt, nastaví typ akce na projektovou a nastaví nový ident celý.
        Celá událost je zapsaná do historie.
        Uživatel je presmerován na detail akce.
        """
        context = self.get_context_data(**kwargs)
        az = context["object"]
        az: ArcheologickyZaznam
        if check_stav_changed(request, context["object"]):
            return JsonResponse(
                {"redirect": az.get_absolute_url()},
                status=403,
            )
        form = PripojitProjektForm(data=request.POST)
        if form.is_valid():
            fedora_transaction = FedoraTransaction()
            projekt = form.cleaned_data["projekt"]
            akce = az.akce
            akce.active_transaction = fedora_transaction
            akce.projekt = Projekt.objects.get(id=projekt)
            akce.typ = Akce.TYP_AKCE_PROJEKTOVA
            akce.save()
            old_ident = az.ident_cely
            az.active_transaction = fedora_transaction
            az.set_akce_ident(get_project_event_ident(az.akce.projekt), delete_container=False)
            az.save()
            Historie(
                typ_zmeny=ZMENA_AZ,
                uzivatel=request.user,
                poznamka=f"{old_ident} -> {az.ident_cely}",
                vazba=az.historie,
            ).save()
            logger.debug("arch_z.views.SamostatnaAkceChange.post.valid", extra={"az_ident_cely": str(az.ident_cely)})
            az.close_active_transaction_when_finished = True
            invalidate_model(ArcheologickyZaznam)
            az.save()
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.debug("arch_z.views.SamostatnaAkceChange.post.not_valid", extra={"errors": form.errors, 
                                                                                    "form_non_field_errors": form.non_field_errors})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

        return redirect(az.get_absolute_url())


class ArchZAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView, PermissionFilterMixin):
    """
    Třida pohledu pro vrácení výsledku pro autocomplete arch záznamů.
    """
    typ_zmeny_lookup = ZAPSANI_AZ

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return ArcheologickyZaznam.objects.none()
        type = self.kwargs.get("type")
        if type == "akce":
            qs = ArcheologickyZaznam.objects.filter(
                typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
            )
        else:
            qs = ArcheologickyZaznam.objects.filter(
                typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
            )
        if self.q:
            qs = qs.filter(ident_cely__icontains=self.q)
        return self.check_filter_permission(qs)


class ArchZTableRowView(LoginRequiredMixin, View):
    """
    Třida pohledu pro vrácení řádku tabulky s arch záznamem.
    """
    def get(self, request):
        zaznam = ArcheologickyZaznam.objects.get(id=request.GET.get("id", ""))
        context = {"arch_z": zaznam}
        if zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            context["type"] = "arch_z"
            context["card_type"] = "akce"
        else:
            context["type"] = "lokalita"
            context["card_type"] = "lokalita"
        return HttpResponse(render_to_string("ez/ez_odkazy_table_row.html", context))


def get_dj_form_detail(app, jednotka, jednotky=None, show=None, old_adb_post=None, user=None):
    """
    Funkce pro získaní dictionary contextu dokumentační jednotky.

    Args:     
        app (string): druh archeologického záznamu ro který se daný context počítá.
        
        jednotka (DokumentacniJednotka): model DokumentacniJednotka pro který se daný context počítá.

        jednotky (DokumentacniJednotka): list modelů DokumentacniJednotka použit pro správne zobrazení možnosti zmeny typu DJ.

        show (dictionary): dictionary pro zobrazení možnosti uživatele na stránce.

        old_adb_post (CreateADBForm): staré volání CreateADBForm pro správne zobrazení chyb formuláře.

    Returns:
        dj_form_detail: dictionary kontextu DJ pro správné zobrazení stránky.
    """
    vyskovy_bod_formset = inlineformset_factory(
        Adb,
        VyskovyBod,
        form=create_vyskovy_bod_form(pian=jednotka.pian, not_readonly=show["editovat"]),
        extra=1,
        can_delete=False,
    )
    has_adb = jednotka.has_adb()
    show_adb_add = (
        jednotka.pian
        and jednotka.typ.id == TYP_DJ_SONDA_ID
        and not has_adb
        and check_permissions(p.actionChoices.adb_zapsat,user, jednotka.ident_cely)
    )
    show_add_pian = False if jednotka.pian else True
    show_approve_pian = (
        True
        if jednotka.pian and jednotka.pian.stav == PIAN_NEPOTVRZEN and check_permissions(p.actionChoices.pian_potvrdit, user, jednotka.ident_cely)
        else False
    )
    if app == "akce":
        create_db_form = CreateDJForm(
            instance=jednotka,
            jednotky=jednotky,
            prefix=jednotka.ident_cely,
            not_readonly=show["editovat"],
        )
        show_uprav_pian = (
            jednotka.pian
            and jednotka.pian.stav == PIAN_NEPOTVRZEN
            and check_permissions(p.actionChoices.archz_pian_edit, user, jednotka.ident_cely)
            )
        show_add_komponenta = not jednotka.negativni_jednotka and check_permissions(p.actionChoices.archz_komponenta_zapsat, user, jednotka.ident_cely)
        show_pripojit_pian_mapa = show_add_pian and check_permissions(p.actionChoices.akce_pripojit_pian_mapa, user, jednotka.ident_cely)
        show_pripojit_pian_id = show_add_pian and check_permissions(p.actionChoices.akce_pripojit_pian_id, user, jednotka.ident_cely)
    else:
        create_db_form = CreateDJForm(
            instance=jednotka,
            typ_arch_z=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA,
            prefix=jednotka.ident_cely,
            not_readonly=show["editovat"],
        )
        show_uprav_pian = (
            jednotka.pian
            and jednotka.pian.stav == PIAN_NEPOTVRZEN
            and check_permissions(p.actionChoices.lokalita_pian_edit, user, jednotka.ident_cely)
            )
        show_add_komponenta = not jednotka.negativni_jednotka and check_permissions(p.actionChoices.lokalita_komponenta_zapsat, user, jednotka.ident_cely)
        show_pripojit_pian_mapa = show_add_pian and check_permissions(p.actionChoices.lokalita_pripojit_pian_mapa, user, jednotka.ident_cely)
        show_pripojit_pian_id = show_add_pian and check_permissions(p.actionChoices.lokalita_pripojit_pian_id, user, jednotka.ident_cely)
    if user.hlavni_role.pk in (ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID):
        show_import_pian_change_user = jednotka.pian and jednotka.pian.stav == PIAN_NEPOTVRZEN and jednotka.archeologicky_zaznam.stav == AZ_STAV_ZAPSANY
    else:
        show_import_pian_change_user = jednotka.archeologicky_zaznam.stav < AZ_STAV_ARCHIVOVANY
    if jednotky and jednotky.count() > 1 and jednotka.ident_cely.endswith('D01'):
        show_dj_smazat = False
    else:
        show_dj_smazat = check_permissions(p.actionChoices.dj_smazat, user, jednotka.ident_cely)
    dj_form_detail = {
        "ident_cely": jednotka.ident_cely,
        "pian_ident_cely": jednotka.pian.ident_cely if jednotka.pian else "",
        "form": create_db_form,
        "show_add_adb": show_adb_add,
        "show_add_komponenta": show_add_komponenta,
        "show_add_pian": (show_add_pian and check_permissions(p.actionChoices.pian_zapsat, user, jednotka.ident_cely)),
        "show_add_pian_zapsat": (show_add_pian and check_permissions(p.actionChoices.pian_zapsat, user, jednotka.ident_cely)),
        "show_add_pian_importovat": (show_add_pian and check_permissions(p.actionChoices.pian_zapsat, user, jednotka.ident_cely)),
        "show_remove_pian": (not show_add_pian and check_permissions(p.actionChoices.pian_odpojit, user, jednotka.ident_cely) and jednotka.typ.id != TYP_DJ_KATASTR),
        "show_uprav_pian": show_uprav_pian,
        "show_approve_pian": show_approve_pian,
        "show_pripojit_pian": True if jednotka.pian is None else False,
        "show_import_pian_new": show_add_pian and check_permissions(p.actionChoices.pian_import_new, user, jednotka.ident_cely),
        "show_import_pian_change": not show_add_pian and show_import_pian_change_user and check_permissions(p.actionChoices.pian_import_change, user, jednotka.pian.ident_cely),
        "show_change_katastr": True if jednotka.typ.id == TYP_DJ_KATASTR and check_permissions(p.actionChoices.dj_zmenit_katastr, user, jednotka.ident_cely) else False,
        "show_dj_smazat": show_dj_smazat,
        "show_vb_smazat": check_permissions(p.actionChoices.vb_smazat,user,jednotka.ident_cely),
        "show_pripojit_pian_mapa": show_pripojit_pian_mapa,
        "show_pripojit_pian_id": show_pripojit_pian_id
    }
    if has_adb and app != "lokalita":
        logger.debug("arch_z.views.get_dj_form_detail", extra={"jednotka_ident_cely": jednotka.ident_cely})
        dj_form_detail["adb_form"] = CreateADBForm(
            old_adb_post,
            instance=jednotka.adb,
            #prefix=jednotka.adb.ident_cely,
            readonly=not show["editovat"],
        )
        dj_form_detail["adb_ident_cely"] = jednotka.adb.ident_cely
        dj_form_detail["vyskovy_bod_formset"] = vyskovy_bod_formset(
            instance=jednotka.adb, prefix=jednotka.adb.ident_cely + "_vb"
        )
        dj_form_detail["vyskovy_bod_formset_helper"] = VyskovyBodFormSetHelper()
        dj_form_detail["adb_pk"] = jednotka.adb.pk
        dj_form_detail["show_remove_adb"] = True if show["editovat"] else False
    return dj_form_detail
