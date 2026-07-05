import logging

import simplejson as json
from adb.forms import CreateADBForm, VyskovyBodFormSetHelper, create_vyskovy_bod_form
from adb.models import Adb, VyskovyBod
from arch_z.filters import AkceFilter
from arch_z.forms import AkceVedouciFormSetHelper, CreateAkceForm, CreateArchZForm, create_akce_vedouci_objekt_form
from arch_z.models import Akce, AkceVedouci, ArcheologickyZaznam, ExterniOdkaz, ExterniZdroj, get_akce_ident
from arch_z.tables import AkceTable
from cacheops import invalidate_model
from core.constants import (
    ARCHIVACE_AZ,
    AZ_STAV_ARCHIVOVANY,
    AZ_STAV_ODESLANY,
    AZ_STAV_ZAPSANY,
    D_STAV_ARCHIVOVANY,
    D_STAV_ODESLANY,
    ODESLANI_AZ,
    PIAN_NEPOTVRZEN,
    PIAN_POTVRZEN,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_UKONCENY_V_TERENU,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_ZAPSANY,
    ROLE_ADMIN_ID,
    ROLE_ARCHEOLOG_ID,
    ROLE_ARCHIVAR_ID,
    ROLE_BADATEL_ID,
    VRACENI_AZ,
    ZAPSANI_AZ,
    ZMENA_AZ,
)
from core.coordTransform import transform_geom_to_wgs84
from core.exceptions import MaximalEventCount, StateChangedError
from core.forms import CheckStavNotChangedForm, VratitFormAZ, VratitFormDokument
from core.ident_cely import get_project_event_ident, get_temp_akce_ident
from core.message_constants import (
    FORM_NOT_VALID,
    MAXIMUM_AKCII_DOSAZENO,
    PRISTUP_ZAKAZAN,
    SPATNY_ZAZNAM_ZAZNAM_VAZBA,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT_NAVAZANE_ZAZNAMY,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
)
from core.models import Permissions as p
from core.models import check_permissions
from core.repository_connector import FedoraError, FedoraRepositoryConnector
from core.utils import (
    CannotFindCadasterCentre,
    get_all_pians_with_akce,
    get_dj_pians_centroid,
    get_message,
    get_pians_from_akce,
)
from core.views import PermissionFilterMixin, SearchListView, check_stav_changed
from dal import autocomplete
from dj.forms import CreateDJForm
from dj.models import DokumentacniJednotka
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import transaction
from django.db.models import Q, RestrictedError
from django.forms import formset_factory, inlineformset_factory
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
from dokument.models import Dokument, DokumentCast
from dokument.views import get_komponenta_form_detail, odpojit, pripojit
from fedora_management.decorators import handle_fedora_error
from heslar.hesla import HESLAR_AREAL, HESLAR_AREAL_KAT, HESLAR_OBDOBI, HESLAR_OBDOBI_KAT
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
from pian.forms import PianCreateForm
from pian.models import Pian
from pid.exceptions import DoiConnectionError, DoiWriteError
from projekt.forms import PripojitProjektForm
from projekt.models import Projekt
from services.mailer import Mailer
from uzivatel.models import User

logger = logging.getLogger(__name__)


def get_obdobi_choices():
    """
    Funkce která vrací dvou stupňový heslař pro období.

    :return: Vrací výsledek volání ``heslar_12()``.
    """
    return heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)


def get_areal_choices():
    """
    Funkce která vrací dvou stupňový heslař pro areál.

    :return: Vrací výsledek volání ``heslar_12()``.
    """
    return heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)


class AkceRelatedRecordUpdateView(TemplateView):
    """Třida, která se dedí a která obsahuje metody pro získaní relací akce."""

    arch_zaznam = None
    scroll_to_dj = False

    def get_shows(self):
        """
        Metoda pro získaní informací které části stránky mají být zobrazeny.

        :return: Vrací výsledek volání ``get_detail_template_shows()``.
        """
        return get_detail_template_shows(self.get_archeologicky_zaznam(), self.get_jednotky(), self.request.user)

    def get_archeologicky_zaznam(self):
        """
        Metoda pro získaní akce z db.

        :return: Vrací výsledek volání ``get_object_or_404()``.
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
        Metoda pro získaní dokumentační jednotky navázané na akci.

        :return: Vrací výsledek volání ``prefetch_related()``.
        """
        return (
            DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely=self.arch_zaznam.ident_cely)
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
        Metoda pro získaní dokumentů navázaných na akci.

        :return: Vrací výsledek volání ``order_by()``.
        """
        return (
            Dokument.objects.filter(casti__archeologicky_zaznam__ident_cely=self.arch_zaznam.ident_cely)
            .select_related("soubory")
            .prefetch_related("soubory__soubory")
            .order_by("ident_cely")
        )

    def get_externi_odkazy(self):
        """
        Metoda pro získaní externích odkazů navázaných na akci.

        :return: Vrací výsledek volání ``order_by()``.
        """
        return (
            ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely=self.arch_zaznam.ident_cely)
            .select_related("externi_zdroj")
            .order_by("externi_zdroj__ident_cely")
        )

    def get_vedouci(self, context):
        """
        Metoda pro získaní dalších vedoucích navázaných na akci.

        :param context: Parametr ``context`` se předává do volání ``ostatni_vedouci_objekt_formset()``, ``filter()``.
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
            akce_zaznam_ostatni_vedouci.append([str(vedouci.vedouci), str(vedouci.organizace)])
        context["ostatni_vedouci_objekt_formset"] = ostatni_vedouci_objekt_formset
        context["ostatni_vedouci_objekt_formset_helper"] = AkceVedouciFormSetHelper()
        context["ostatni_vedouci_objekt_formset_readonly"] = True
        context["akce_zaznam_ostatni_vedouci"] = akce_zaznam_ostatni_vedouci

    def check_locality_arch_z_conflict(self):
        """
        Ověří locality arch z conflict.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        :raises Http404: Vyvolá se při splnění podmínky ``self.get_archeologicky_zaznam().lokalita``.
        """
        try:
            if self.get_archeologicky_zaznam().lokalita:
                raise Http404(_("arch_z.views.AkceRelatedRecordUpdateView.get_context_data.lokalita_error"))
        except ObjectDoesNotExist:
            return False

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní contextu akci pro template.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

        :return: Vrací kontext šablony
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
                context["arch_pr_link"] = (
                    '{% url "projekt:projekt_archivovat" zaznam.akce.projekt.ident_cely %}?sent_stav={{projekt.stav}}&from_arch=true'
                )
            else:
                context["app"] = "akce"
                context["arch_pr_link"] = None
            context["presna_specifikace"] = (
                True
                if self.arch_zaznam.akce.specifikace_data == Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE)
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
        context["scroll_to_dj"] = self.scroll_to_dj
        return context


class ArcheologickyZaznamDetailView(LoginRequiredMixin, AkceRelatedRecordUpdateView):
    """Třída pohledu pro zobrazení detailu akce."""

    template_name = "arch_z/dj/arch_z_detail.html"

    def get_archeologicky_zaznam(self) -> ArcheologickyZaznam:
        """
        Metoda pro získani záznamu akce z db podle ident_cely.

        :return: Vrací výsledek operace.
        """
        ident_cely = self.kwargs.get("ident_cely")
        return get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní context dat navíc oproti přepisované metóde.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

        :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["warnings"] = self.request.session.pop("temp_data", None)
        context["arch_projekt_link"] = (self.request.session.pop("arch_projekt_link", None),)
        context["arch_projekt_link_uzavrit"] = (self.request.session.pop("arch_projekt_link_uzavrit", None),)
        return context


class DokumentacniJednotkaRelatedUpdateView(AkceRelatedRecordUpdateView):
    """Třida, která se dedí a která obsahuje metody pro získaní relací DJ."""

    scroll_to_dj = True
    template_name = "arch_z/dj/dj_update.html"

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """
        Ověří správnost vazby mezi dokumentační jednotkou a archeologickým záznamem před zpracováním požadavku.

        :param request: HTTP požadavek; při nesprávné vazbě se použije k přesměrování na bezpečnou URL.
        :param args: Poziční argumenty předávané nadřazené metodě dispatch.
        :param kwargs: Klíčové argumenty obsahující ``dj_ident_cely`` a ``ident_cely`` pro načtení objektů.
        :return: Výstup funkce odpovídající implementované logice.
        """
        dj = get_object_or_404(DokumentacniJednotka, ident_cely=self.kwargs["dj_ident_cely"])
        az = get_object_or_404(ArcheologickyZaznam, ident_cely=self.kwargs["ident_cely"])
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
        Metoda pro získani záznamu DJ z db podle ident_cely.

        :return: Vrací proměnná ``objects``.
        """
        dj_ident_cely = self.kwargs["dj_ident_cely"]
        logger.debug("arch_z.views.DokumentacniJednotkaUpdateView.get_object", extra={"ident_cely": dj_ident_cely})
        objects = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
        return objects

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní context dat DJ navíc oproti přepisované metóde, záznam DJ.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

        :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["active_dj_ident"] = self.get_dokumentacni_jednotka().ident_cely
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


class DokumentacniJednotkaCreateView(LoginRequiredMixin, AkceRelatedRecordUpdateView):
    """Třída pohledu pro vytvoření dokumentační jednotky."""

    scroll_to_dj = True
    template_name = "arch_z/dj/dj_create.html"

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření DJ.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

        :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        typ_akce = None
        logger.debug("arch_z.views.DokumentacniJednotkaCreateView.get_context_data")
        try:
            self.get_archeologicky_zaznam()
            if self.get_archeologicky_zaznam().typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
                typ_akce = self.get_archeologicky_zaznam().akce.typ
        except Exception as err:
            logger.debug(
                "arch_z.views.DokumentacniJednotkaCreateView.get_context_data.cannot_get_typ_akce", extra={"error": err}
            )
        context["dj_form_create"] = CreateDJForm(
            jednotky=self.get_jednotky(),
            typ_arch_z=self.get_archeologicky_zaznam().typ_zaznamu,
            typ_akce=typ_akce,
        )
        logger.debug(
            "arch_z.views.DokumentacniJednotkaCreateView.get_context_data.end",
            extra={"typ_arch_z": self.get_archeologicky_zaznam().typ_zaznamu, "typ_akce": typ_akce},
        )
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


class DokumentacniJednotkaUpdateView(LoginRequiredMixin, DokumentacniJednotkaRelatedUpdateView):
    """Třída pohledu pro zobrazení detailu dokumentační jednotky s možností její úpravy."""

    template_name = "arch_z/dj/dj_update.html"

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní context dat DJ navíc oproti přepisované metóde, pro zobrazení správneho detailu.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

        :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        old_adb_post = self.request.session.pop("_old_adb_post", None)

        show = self.get_shows()
        jednotka: DokumentacniJednotka = self.get_dokumentacni_jednotka()
        jednotky = self.get_jednotky()
        context["j"] = get_dj_form_detail(
            "akce", jednotka, jednotky, show, old_adb_post, self.request.user, session=self.request.session
        )
        return context


class KomponentaCreateView(LoginRequiredMixin, DokumentacniJednotkaRelatedUpdateView):
    """Třida pohledu pro vytvoření komponenty dokumentační jednotky."""

    template_name = "arch_z/dj/komponenta_create.html"

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní context dat navíc oproti přepisované metóde, formulář na vytvoření komponenty.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

        :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["komponenta_form_create"] = CreateKomponentaForm(get_obdobi_choices(), get_areal_choices())
        context["j"] = self.get_dokumentacni_jednotka()
        return context


class KomponentaUpdateView(LoginRequiredMixin, DokumentacniJednotkaRelatedUpdateView):
    """Třida pohledu pro editaci komponenty dokumentační jednotky."""

    template_name = "arch_z/dj/komponenta_detail.html"

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """
        Ověří správnost vazby mezi komponentou a dokumentační jednotkou před zpracováním požadavku.

        :param request: HTTP požadavek; při nesprávné vazbě se použije k přesměrování na bezpečnou URL.
        :param args: Poziční argumenty předávané nadřazené metodě dispatch.
        :param kwargs: Klíčové argumenty obsahující ``dj_ident_cely`` a ``komponenta_ident_cely`` pro načtení objektů.
        :return: Výstup funkce odpovídající implementované logice.
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
        Metoda pro získani záznamu komponenty z db podle ident_cely.

        :return: Vrací proměnná ``object``.
        """
        dj_ident_cely = self.kwargs["komponenta_ident_cely"]
        object = get_object_or_404(Komponenta, ident_cely=dj_ident_cely)
        return object

    def get_dokumentacni_jednotka(self):
        """
        Vrací dokumentacni jednotka.

        :return: Vrací proměnná ``object``.
        """
        dj_ident_cely = self.kwargs["dj_ident_cely"]
        logger.debug("arch_z.views.DokumentacniJednotkaUpdateView.get_object", extra={"ident_cely": dj_ident_cely})
        object = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
        return object

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro úpravu komponenty,

        případně data poslaného chybného formuláře.

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


class PianCreateView(LoginRequiredMixin, DokumentacniJednotkaRelatedUpdateView):
    """Třida pohledu pro vytvoření PIANu dokumentační jednotky."""

    template_name = "arch_z/dj/pian_create.html"

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření PIANu.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

        :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        dj = self.get_dokumentacni_jednotka()
        context["j"] = dj
        context["pian_form_create"] = PianCreateForm(dj=dj)
        return context

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` předává se do volání ``get()``, ``str()``, pracuje se s atributy ``user``.
        :param args: Poziční argumenty předávané nadřazené metodě get.
        :param kwargs: Klíčové argumenty předávané do ``get_context_data()``.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render_to_response()``.
            :raises Exception: Vyvolá se s textem "arch_z.views.PianCreateView.get.label_not_found"; nebo s textem "arch_z.views.PianCreateView.get.transormation_error".
        """
        context = self.get_context_data(**kwargs)
        if "index" in self.request.GET and "label" in self.request.GET:
            try:
                geom = cache.get(str(request.user.id) + "_geom")
                index = int(self.request.GET["index"])
                if self.request.GET["label"] != str(geom.iloc[index]["label"]):
                    raise Exception("arch_z.views.PianCreateView.get.label_not_found")
                context["geom"] = geom.iloc[index].copy()
                if context["geom"]["epsg"] == "5514" or context["geom"]["epsg"] == 5514:
                    context["geom"]["geometry"], stat = transform_geom_to_wgs84(context["geom"]["geometry"])
                    if stat != "OK":
                        raise Exception("arch_z.views.PianCreateView.get.transormation_error")
            except Exception as err:
                logger.error("arch_z.views.PianCreateView.get.import_pian.error", extra={"error": err})
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    _("arch_z.views.DokumentacniJednotkaRelatedUpdateView.get.import_pian.error"),
                )
                return redirect(
                    reverse("arch_z:detail-dj", args=[self.arch_zaznam.ident_cely, context["dj_ident_cely"]])
                )
        return self.render_to_response(context)


class PianUpdateView(LoginRequiredMixin, DokumentacniJednotkaRelatedUpdateView):
    """Třida pohledu pro editaci PIANu dokumentační jednotky."""

    template_name = "arch_z/dj/pian_update.html"

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """
        Ověří správnost vazby mezi PIAN a dokumentační jednotkou před zpracováním požadavku.

        :param request: HTTP požadavek; při nesprávné vazbě se použije k přesměrování na bezpečnou URL.
        :param args: Poziční argumenty předávané nadřazené metodě dispatch.
        :param kwargs: Klíčové argumenty obsahující ``dj_ident_cely`` a ``pian_ident_cely`` pro načtení objektů.
        :return: Výstup funkce odpovídající implementované logice.
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

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro editaci PIANu.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

        :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        dj = self.get_dokumentacni_jednotka()
        context["j"] = dj
        pian = dj.pian
        context["pian_form_update"] = PianCreateForm(instance=pian, dj=dj)
        pian_ident_cely = pian.ident_cely
        context["pian_concurrent_changes"] = self.request.session.pop(
            f"pian_concurrent_changes_{pian_ident_cely}", None
        )
        context["pian_fresh_form_url"] = self.request.path
        return context

    def get(self, request, *args, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` předává se do volání ``get()``, ``str()``, pracuje se s atributy ``user``.
        :param args: Poziční argumenty předávané nadřazené metodě get.
        :param kwargs: Klíčové argumenty předávané do ``get_context_data()``.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render_to_response()``.
            :raises PermissionDenied: Vyvolá se při splnění podmínky ``context['j'].pian.stav == PIAN_POTVRZEN``.
            :raises Exception: Vyvolá se s textem "arch_z.views.PianUpdateView.get.label_not_found"; nebo s textem "arch_z.views.PianUpdateView.transormation_error".
        """
        context = self.get_context_data(**kwargs)
        if context["j"].pian.stav == PIAN_POTVRZEN:
            raise PermissionDenied
        if "index" in self.request.GET and "label" in self.request.GET:
            try:
                geom = cache.get(str(request.user.id) + "_geom")
                index = int(self.request.GET["index"])
                if self.request.GET["label"] != str(geom.iloc[index]["label"]):
                    raise Exception("arch_z.views.PianUpdateView.get.label_not_found")
                context["geom"] = geom.iloc[index].copy()
                if context["geom"]["epsg"] == "5514" or context["geom"]["epsg"] == 5514:
                    context["geom"]["geometry"], stat = transform_geom_to_wgs84(context["geom"]["geometry"])
                    if stat != "OK":
                        raise Exception("arch_z.views.PianUpdateView.transormation_error")
            except Exception as err:
                logger.error("arch_z.views.PianUpdateView.get.import_pian.error", extra={"error": err})
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    _("arch_z.views.DokumentacniJednotkaRelatedUpdateView.get.import_pian.error"),
                )
                return redirect(
                    reverse("arch_z:detail-dj", args=[self.arch_zaznam.ident_cely, context["dj_ident_cely"]])
                )
        return self.render_to_response(context)


class AdbCreateView(LoginRequiredMixin, DokumentacniJednotkaRelatedUpdateView):
    """Třida pohledu pro vytvoření PIANu dokumentační jednotky."""

    template_name = "arch_z/dj/adb_create.html"

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření ADB.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

        :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        context["j"] = self.get_dokumentacni_jednotka()
        context["adb_form_create"] = CreateADBForm()
        return context


@never_cache
@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    """
    Funkce pohledu pro zobrazení a zpracování editace akce.

    Na začátku se kontroluje, jestli stav není archivovaný.
    Zobrazení se skládá ze 3 formulářů: CreateArchZForm, CreateAkceForm a formsetu pro další vedoucí.

    :param request: Parametr ``request`` se předává do volání ``CreateArchZForm()``, ``CreateAkceForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``redirect()``, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
        :raises PermissionDenied: Vyvolá se při splnění podmínky ``zaznam.stav == AZ_STAV_ARCHIVOVANY``.
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

        if form_az.is_valid() and form_akce.is_valid() and ostatni_vedouci_objekt_formset.is_valid():
            logger.debug("arch_z.views.edit.form_valid")
            conflicting_fields = form_az.get_conflicting_fields() + form_akce.get_conflicting_fields()
            for formset_form in ostatni_vedouci_objekt_formset.forms:
                conflicting_fields += formset_form.get_conflicting_fields()
            if conflicting_fields:
                conflicting_labels = list(
                    dict.fromkeys(
                        [str(form_az.fields[f].label) for f in conflicting_fields if f in form_az.fields]
                        + [str(form_akce.fields[f].label) for f in conflicting_fields if f in form_akce.fields]
                        + [
                            str(label)
                            for fs_form in ostatni_vedouci_objekt_formset.forms
                            for f in conflicting_fields
                            if f in fs_form.fields
                            for label in [fs_form.fields[f].label]
                        ]
                    )
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
                        "ostatni_vedouci_objekt_formset_readonly": not check_permissions(
                            p.actionChoices.archz_vedouci_smazat, request.user, zaznam.ident_cely
                        ),
                        "title": _("arch_z.views.edit.title.text"),
                        "header": _("arch_z.views.edit.header.text"),
                        "button": _("arch_z.views.edit.submitButton.text"),
                        "sam_akce": False if zaznam.akce.projekt else True,
                        "heslar_specifikace_v_letech_presne": HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRESNE,
                        "heslar_specifikace_v_letech_priblizne": HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRIBLIZNE,
                        "arch_z_ident_cely": zaznam.ident_cely,
                        "toolbar_name": _("arch_z.views.edit.toolbar_name.text"),
                        "concurrent_changes": conflicting_labels,
                    },
                )
            az = form_az.save(commit=False)
            fedora_transaction = az.create_transaction(request.user)
            fedora_transaction.redirect_on_error = True
            az.save()
            form_az.save_m2m()
            akce = form_akce.save(commit=False)
            akce.active_transaction = fedora_transaction
            akce.save()
            ostatni_vedouci_objekt_formset.save()
            akce.set_snapshots()
            az.close_active_transaction_when_finished = True
            az.save()
            return redirect("arch_z:detail", ident_cely=ident_cely)
        else:
            logger.warning(
                "arch_z.views.edit.form_az_valid",
                extra={"az_error": str(form_az.errors), "error": str(form_akce.errors)},
            )
            messages.add_message(request, messages.WARNING, FORM_NOT_VALID)
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
            "ostatni_vedouci_objekt_formset_readonly": not check_permissions(
                p.actionChoices.archz_vedouci_smazat, request.user, zaznam.ident_cely
            ),
            "title": _("arch_z.views.edit.title.text"),
            "header": _("arch_z.views.edit.header.text"),
            "button": _("arch_z.views.edit.submitButton.text"),
            "sam_akce": False if zaznam.akce.projekt else True,
            "heslar_specifikace_v_letech_presne": HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRESNE,
            "heslar_specifikace_v_letech_priblizne": HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRIBLIZNE,
            "arch_z_ident_cely": zaznam.ident_cely,
            "toolbar_name": _("arch_z.views.edit.toolbar_name.text"),
        },
    )


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def odeslat(request, ident_cely):
    """
    Funkce pohledu pro zobrazení a zpracování odeslání akce.

    Na začátku se kontroluje, jestli stav není jiný než zapsaný nebo někdo nezměnil stav akce během odesílání.
    Při GET volání se kontrolují vyplněná pole akce a její relace pomocí metody na modelu.
    Po POST volání se volá metoda na modelu pro posun stavu do odeslaného.

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``debug()``.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
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
        fedora_transaction = az.create_transaction(request.user)
        az.set_odeslany(request.user, request, messages)
        az.save()
        if az.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            all_akce = Akce.objects.filter(projekt=az.akce.projekt).filter(archeologicky_zaznam__stav=AZ_STAV_ZAPSANY)
            if not all_akce and az.akce.projekt.stav == PROJEKT_STAV_UKONCENY_V_TERENU:
                request.session["arch_projekt_link_uzavrit"] = True
        fedora_transaction.success_message = get_message(az, "USPESNE_ODESLANA")
        logger.debug("arch_z.views.odeslat.akce_uspesne_odeslana", extra={"info": get_message(az, "USPESNE_ODESLANA")})
        az.close_active_transaction_when_finished = True
        az.save()
        return JsonResponse({"redirect": az.get_absolute_url()})
    else:
        warnings = az.check_pred_odeslanim()
        logger.debug("arch_z.views.odeslat.warnings", extra={"ident_cely": ident_cely, "warning": str(warnings)})

        if warnings:
            request.session["temp_data"] = warnings
            messages.add_message(request, messages.ERROR, get_message(az, "NELZE_ODESLAT"))
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
    Funkce pohledu pro zobrazení a zpracování archivace akce.

    Na začátku se kontroluje, jestli stav není jiný než odeslaný nebo někdo nezměnil stav akce během archivace.
    Při GET volání se kontrolují vyplněná pole akce a její relace pomocí metody na modelu.
    Po POST volání se volá metoda na modelu pro posun stavu do odeslaného.

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``debug()``, ``get_object_or_404()``.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
    """
    logger.debug("arch_z.views.archivovat.start", extra={"ident_cely": ident_cely})
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if az.stav != AZ_STAV_ODESLANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": az.get_absolute_url()},
            status=403,
        )
    # Momentálně zbytečné, případná chyba se propaguje výše.
    if check_stav_changed(request, az):
        return JsonResponse(
            {"redirect": az.get_absolute_url()},
            status=403,
        )
    if request.method == "POST":
        fedora_transaction = az.create_transaction(request.user, get_message(az, "USPESNE_ARCHIVOVANA"))
        try:
            az.set_archivovany(request.user)

            if az.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA:
                az.igsn_lokalita_publish()
                az.lokalita.set_igsn()
                az.lokalita.save()

            if az.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
                all_akce = Akce.objects.filter(projekt=az.akce.projekt).exclude(
                    archeologicky_zaznam__stav=AZ_STAV_ARCHIVOVANY
                )
                if not all_akce and az.akce.projekt.stav == PROJEKT_STAV_UZAVRENY:
                    request.session["arch_projekt_link"] = True
            Mailer.send_ea02(arch_z=az)
            az.close_active_transaction_when_finished = True
            az.save()
            for item in az.casti_dokumentu.all():
                item: DokumentCast
                if item.dokument.doi and item.dokument.stav == D_STAV_ARCHIVOVANY:
                    item.dokument.doi_update()
            return JsonResponse({"redirect": az.get_absolute_url()})
        except (DoiWriteError, FedoraError) as err:
            logger.info("arch_z.views.archivovat.post_error", extra={"error": err, "ident_cely": az.ident_cely})
            transaction.set_rollback(True)
            if isinstance(err, FedoraError):
                az.igsn_lokalita_hide(False)
            fedora_transaction.rollback_transaction()
        return JsonResponse({"redirect": az.get_absolute_url()})
    else:
        warnings, docs_warings = az.check_pred_archivaci()
        logger.debug("arch_z.views.archivovat", extra={"warning": warnings})
        if warnings:
            request.session["temp_data"] = warnings
            messages.add_message(request, messages.ERROR, get_message(az, "NELZE_ARCHIVOVAT"))
            return JsonResponse(
                {"redirect": az.get_absolute_url()},
                status=403,
            )
    try:
        igsn_exists = bool(az.lokalita and az.lokalita.igsn_exists())
        doi_confirmation = igsn_exists and not az.lokalita.igsn
    except ObjectDoesNotExist:
        doi_confirmation = False
    except DoiConnectionError as err:
        logger.warning(
            "arch_z.views.archivovat.igsn_exists.connection_error",
            extra={"error": err},
            exc_info=True,
        )
        doi_confirmation = False
    form_check = CheckStavNotChangedForm(
        require_confirmation=doi_confirmation, dokument_warnings=docs_warings, initial={"old_stav": az.stav}
    )
    context = {
        "object": az,
        "title": _("arch_z.views.archivovat.title.text"),
        "pid_confirmation": doi_confirmation,
        "id_tag": "archivovat-akci-form",
        "button": _("arch_z.views.archivovat.submitButton.text"),
        "form_check": form_check,
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    """
    Funkce pohledu pro zobrazení a zpracování vrácení stavu akce o jeden krok zpět.

    Na začátku se kontroluje, jestli někdo nezměnil stav akce během vrácení.
    Pro vrácení se používá formulář pro vrácení, který je jednotný napříč aplikací.
    Po POST volání se volá metoda na modelu pro posun stavu zpět.
    Pokud se jedná o projektovou akci, tak se vrací i stav projektu ze stavu uzavřený nebo archivovaný.

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``debug()``.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
        :raises PermissionDenied: Vyvolá se při splnění podmínky ``dokument.stav != D_STAV_ODESLANY``.
        :raises StateChangedError: Vyvolá se při splnění podmínky ``check_stav_changed(request, dokument)``.
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
    DokumentFormSet = formset_factory(VratitFormDokument, extra=0)
    if request.method == "POST":
        form = VratitFormAZ(request.POST, az=az)
        if form.is_valid():
            fedora_transaction = az.create_transaction(request.user)
            stav_initial = az.stav
            try:
                if az.stav == AZ_STAV_ODESLANY:
                    formset = DokumentFormSet(request.POST)
                    if formset.is_valid():
                        for form_row in formset:
                            dokument_ident_cely = form_row.cleaned_data["ident_cely"]
                            dokument = Dokument.objects.get(ident_cely=dokument_ident_cely)
                            dokument.active_transaction = fedora_transaction
                            if dokument.stav != D_STAV_ODESLANY:
                                messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
                                raise PermissionDenied
                            if check_stav_changed(request, dokument):
                                raise StateChangedError
                            form_row.duvod = form_row.cleaned_data["reason"]  # type: ignore[attr-defined]
                            form_row.dokument = dokument  # type: ignore[attr-defined]
                            form_row.before_save_state = dokument.stav  # type: ignore[attr-defined]
                            dokument.set_vraceny(request.user, dokument.stav - 1, form_row.duvod)
                            dokument.save()
                if stav_initial == AZ_STAV_ARCHIVOVANY:
                    az.igsn_lokalita_hide()
                duvod = form.cleaned_data["reason"]
                projekt = None
                if az.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
                    projekt = az.akce.projekt
                # BR-A-3
                if az.stav == AZ_STAV_ODESLANY and projekt is not None:
                    # Vrátit také projekt ze stavů P6 nebo P5 do P4.
                    projekt.active_transaction = fedora_transaction
                    projekt_stav = projekt.stav
                    logger.debug("arch_z.views.vratit.valid", extra={"ident_cely": ident_cely, "stav": projekt.stav})
                    if projekt_stav == PROJEKT_STAV_UZAVRENY:
                        projekt.set_vracen(request.user, projekt_stav - 1, "Automatické vrácení projektu")
                        projekt.save()
                    if projekt_stav == PROJEKT_STAV_ARCHIVOVANY:
                        projekt.set_vracen(request.user, projekt_stav - 1, "Automatické vrácení projektu")
                        projekt.save()
                        projekt.set_vracen(request.user, projekt_stav - 2, "Automatické vrácení projektu")
                        projekt.save()
                before_save_state = az.stav
                az.set_vraceny(request.user, az.stav - 1, duvod)
                az.close_active_transaction_when_finished = True
                az.save()
                if before_save_state == AZ_STAV_ODESLANY:
                    Mailer.send_ev01(zaznam=az, reason=duvod)
                    for form_row in formset:
                        if form_row.before_save_state == D_STAV_ODESLANY:
                            Mailer.send_ek02(document=form_row.dokument, reason=form_row.duvod)
                fedora_transaction.success_message = get_message(az, "USPESNE_VRACENA")
                return JsonResponse({"redirect": az.get_absolute_url()})
            except Exception as err:
                logger.info("arch_z.views.vratit.post_error", extra={"error": err, "ident_cely": az.ident_cely})
                transaction.set_rollback(True)
                fedora_transaction.rollback_transaction()
                if isinstance(err, FedoraError):
                    az.igsn_lokalita_publish(check_status=False)
            return JsonResponse({"redirect": az.get_absolute_url()})
        else:
            logger.debug("arch_z.views.vratit.not_valid", extra={"error": form.errors})
    else:
        form = VratitFormAZ(az=az, initial={"old_stav": az.stav})
    context = {
        "object": az,
        "form": form,
        "title": _("arch_z.views.vratit.title.text"),
        "button": _("arch_z.views.vratit.submitButton.text"),
        "id_tag": "vratit-akci-form",
    }
    if az.stav == AZ_STAV_ODESLANY:
        formset = DokumentFormSet()
        context.update(
            {
                "formset": formset,
            }
        )
    return render(request, "core/transakce_table_modal.html", context)


@never_cache
@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def zapsat(request, projekt_ident_cely=None):
    """
    Funkce pohledu pro vytvoření akce.

    Na začátku se kontroluje, jestli jde o vytvoření projektové nebo samostatné akce a zda je možné projektovou akci vytvořit.
    Zobrazení se skládá ze 3 formulářů: CreateArchZForm, CreateAkceForm a formsetu pro další vedoucí.

    :param request: Parametr ``request`` se předává do volání ``CreateArchZForm()``, ``CreateAkceForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param projekt_ident_cely: Identifikátor ``projekt_ident_cely`` používaný pro dohledání cílového záznamu.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
        :raises PermissionDenied: Vyvolá se při splnění podmínky ``not PROJEKT_STAV_ZAPSANY < projekt.stav < PROJEKT_STAV_ARCHIVOVANY``; nebo při splnění podmínky ``projekt.typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID``.
    """
    if projekt_ident_cely:
        projekt = get_object_or_404(Projekt, ident_cely=projekt_ident_cely)
        # Projektové akce lze přidávat pouze pokud je projekt již přihlášen.
        if not PROJEKT_STAV_ZAPSANY < projekt.stav < PROJEKT_STAV_ARCHIVOVANY:
            logger.debug(
                "arch_z.views.zapsat.stav_error", extra={"ident_cely": projekt_ident_cely, "stav": projekt.stav}
            )
            raise PermissionDenied("Nelze přidat akci k projektu ve stavu " + str(projekt.stav))
        # Projektové akce nelze vytvořit pro projekt typu průzkum.
        if projekt.typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID:
            logger.debug(
                "arch_z.views.zapsat.typ_projektu_error",
                extra={"ident_cely": projekt_ident_cely, "stav": projekt.stav},
            )
            raise PermissionDenied(f"Nelze přidat akci k projektu typu {projekt.typ_projektu}")
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
        if form_az.is_valid() and form_akce.is_valid() and ostatni_vedouci_objekt_formset.is_valid():
            logger.debug("arch_z.views.zapsat.form_valid", extra={"ident_cely": projekt_ident_cely})
            az = form_az.save(commit=False)
            az: ArcheologickyZaznam
            fedora_transaction = az.create_transaction(request.user)
            fedora_transaction.redirect_url = reverse("projekt:detail", args=[projekt_ident_cely])
            az.stav = AZ_STAV_ZAPSANY
            az.typ_zaznamu = ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
            try:
                if projekt:
                    az.ident_cely = get_project_event_ident(projekt)
                    typ_akce = Akce.TYP_AKCE_PROJEKTOVA
                else:
                    az.ident_cely = get_temp_akce_ident(az.hlavni_katastr.okres.kraj.rada_id)
                    typ_akce = Akce.TYP_AKCE_SAMOSTATNA
            except MaximalEventCount:
                messages.add_message(request, messages.ERROR, MAXIMUM_AKCII_DOSAZENO)
                fedora_transaction.rollback_transaction()
            else:
                if FedoraRepositoryConnector.check_container_deleted_or_not_exists(
                    az.ident_cely, "archeologicky_zaznam"
                ):
                    az.save()
                    form_az.save_m2m()
                    # Toto je nutné zavolat pro uložení many-to-many vazeb (katastry).
                    # Protože používáme `commit = False`.
                    az.set_zapsany(request.user)
                    akce = form_akce.save(commit=False)

                    if typ_akce == Akce.TYP_AKCE_PROJEKTOVA:
                        akce.specifikace_data = Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE)
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
                        logger.debug(
                            "arch_z.views.zapsat.form_not_valid",
                            extra={"error": ostatni_vedouci_objekt_formset.errors},
                        )
                    akce.set_snapshots()
                    fedora_transaction.success_message = get_message(az, "USPESNE_ZAPSANA")
                    logger.debug("arch_z.views.zapsat.success", extra={"pk": akce.pk, "ident_cely": projekt_ident_cely})
                    az.close_active_transaction_when_finished = True
                    az.save()
                    return redirect("arch_z:detail", az.ident_cely)
                else:
                    fedora_transaction.error_message = _(
                        "arch_z.views.zapsat.samostatnaAkce." "check_container_deleted_or_not_exists_error"
                    )
                    fedora_transaction.rollback_transaction()
                    logger.debug(
                        "arch_z.views.zapsat.check_container_deleted_or_not_exists.incorrect",
                        extra={"ident_cely": az.ident_cely},
                    )
        else:
            logger.debug("arch_z.views.zapsat.not_valid", extra={"az_error": form_az, "error": form_akce.errors})

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
            "toolbar_label": _("arch_z.views.zapsat.toolbar.title"),
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
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    """
    Funkce pohledu pro zobrazení a zpracování smazání akce.

    Na začátku se kontroluje, jestli někdo nezměnil stav akce během smazání.
    Po POST volání se volá metoda na modelu pro smazání akce.

    :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``create_transaction()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``debug()``.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
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
        fedora_transaction = az.create_transaction(request.user, ZAZNAM_USPESNE_SMAZAN, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
        try:
            with transaction.atomic():
                az.igsn_lokalita_delete()
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
                logger.debug(
                    "arch_z.views.smazat.success", extra={"ident_cely": ident_cely, "transaction": fedora_transaction}
                )
                if projekt:
                    return JsonResponse(
                        {"redirect": reverse("projekt:detail", kwargs={"ident_cely": projekt.ident_cely})}
                    )
                else:
                    if az.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA:
                        return JsonResponse({"redirect": reverse("lokalita:index")})
                    else:
                        return JsonResponse({"redirect": reverse("arch_z:index")})
        except RestrictedError as err:
            logger.debug("arch_z.views.smazat.error", extra={"ident_cely": ident_cely, "error": err})
            fedora_transaction.error_message = ZAZNAM_SE_NEPOVEDLO_SMAZAT_NAVAZANE_ZAZNAMY
            transaction.set_rollback(True)
            fedora_transaction.rollback_transaction()
            return JsonResponse(
                {"redirect": az.get_absolute_url()},
                status=403,
            )
        except (DoiWriteError, FedoraError) as err:
            logger.debug("arch_z.views.smazat.error", extra={"ident_cely": ident_cely, "error": err})
            transaction.set_rollback(True)
            fedora_transaction.rollback_transaction()
            if isinstance(err, FedoraError):
                az.igsn_lokalita_update(False, True)
            return JsonResponse({"redirect": az.get_absolute_url()})
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
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def pripojit_dokument(request, arch_z_ident_cely, proj_ident_cely=None):
    """
    Funkce pohledu pro připojení dokumentu do akce.

    Funkce volá další funkci pro připojení s parametrem třídou modelu navíc.

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``pripojit()``, vstupuje do návratové hodnoty.
    :param arch_z_ident_cely: Identifikátor ``arch_z_ident_cely`` používaný pro dohledání cílového záznamu.
    :param proj_ident_cely: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``pripojit()``.
    """
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=arch_z_ident_cely)
    if proj_ident_cely is not None and az.akce.projekt.ident_cely != proj_ident_cely:
        logger.error("Archeologiky zaznam - Projekt wrong relation")
        messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
        return JsonResponse({"redirect": az.get_absolute_url()}, status=403)
    return pripojit(request, arch_z_ident_cely, proj_ident_cely, ArcheologickyZaznam)


@login_required
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def odpojit_dokument(request, ident_cely, arch_z_ident_cely):
    """
    Funkce pohledu pro odpojení dokumentu do akce.

    Funkce volá další funkci pro odpojení s parametrem navíc - arch záznamem.

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``odpojit()``, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``filter()``, ``odpojit()``, vstupuje do návratové hodnoty.
    :param arch_z_ident_cely: Identifikátor ``arch_z_ident_cely`` používaný pro dohledání cílového záznamu.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``odpojit()``.
    """
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=arch_z_ident_cely)
    relace_dokumentu = DokumentCast.objects.filter(dokument__ident_cely=ident_cely, archeologicky_zaznam=az)
    if not relace_dokumentu.count() > 0:
        logger.error("Archeologiky zaznam - Dokument wrong relation")
        messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
        return JsonResponse({"redirect": az.get_absolute_url()}, status=403)
    return odpojit(request, ident_cely, arch_z_ident_cely, az)


@login_required
@require_http_methods(["POST"])
def post_ajax_get_pians(request):
    """
    Vypada nepouzito check s J. Bartos

    :param request: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

        :return: Vrací výsledek volání ``JsonResponse()``.
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
def post_akce2kat(request):
    """
    Funkce pohledu pro získaní souradnic katastru akce.

    :param request: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

        :return: Vrací výsledek volání ``JsonResponse()``.
    """
    body = json.loads(request.body.decode("utf-8"))
    logger.debug("arch_z.views.post_akce2kat.start", extra={"data": body})
    katastr_name = body["cadastre"]
    try:
        kod = katastr_name[katastr_name.find(";") + 1 : katastr_name.find(")")].strip()
    except (ValueError, IndexError) as e:
        logger.error("arch_z.views.post_akce2kat.katastr_name_error", extra={"katastr": katastr_name, "error": e})
        return JsonResponse(
            {
                "pians": [],
                "count": 0,
            },
            status=200,
        )
    katastr = RuianKatastr.objects.get(kod=kod)
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
            logger.error("arch_z.views.post_akce2kat.error", extra={"error": err})
            return JsonResponse(
                {
                    "pians": [],
                    "count": 0,
                },
                status=200,
            )


def get_history_dates(historie_vazby, request_user):
    """
    Funkce pro získaní dátumů pro historii.

    :param historie_vazby: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
    :param request_user: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.
    :return: Slovník dat jednotlivých změn stavu pro zobrazení v historii.
    """
    request_user: User
    anonymized = request_user.hlavni_role.pk not in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)
    historie = {
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_AZ, anonymized),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_AZ, anonymized),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_AZ, anonymized),
        "datum_vraceni": historie_vazby.get_last_transaction_if_type(VRACENI_AZ, anonymized),
    }
    return historie


def get_detail_template_shows(archeologicky_zaznam, dok_jednotky, user, app="akce"):
    """
    Funkce pro získaní dictionary uživatelských akcí které mají být zobrazeny uživately.

    :param archeologicky_zaznam: Parametr ``archeologicky_zaznam`` předává se do volání ``check_permissions()``, pracuje se s atributy ``ident_cely``, ``stav``, ovlivňuje větvení podmínek.
    :param dok_jednotky: Kolekce ``dok_jednotky`` zpracovávaná touto funkcí.
    :param user: Parametr ``user`` se předává do volání ``check_permissions()``, ovlivňuje větvení podmínek.
    :param app: Parametr ``app`` předává se do volání ``check_permissions()``.
    :return: Slovník příznaků určujících, které akce se mají v detailu zobrazit.
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
            zmenit_proj_akci = check_permissions(
                p.actionChoices.archz_zmenit_proj, user, archeologicky_zaznam.ident_cely
            )
            show_pripojit_dokumenty = check_permissions(
                p.actionChoices.archz_pripojit_dok_proj, user, archeologicky_zaznam.ident_cely
            )
        else:
            zmenit_sam_akci = check_permissions(p.actionChoices.archz_zmenit_sam, user, archeologicky_zaznam.ident_cely)
            show_pripojit_dokumenty = check_permissions(
                p.actionChoices.archz_pripojit_dok, user, archeologicky_zaznam.ident_cely
            )
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
        show_pripojit_dokumenty = check_permissions(
            p.actionChoices.archz_pripojit_dok, user, archeologicky_zaznam.ident_cely
        )
        if dok_jednotky.count() == 0 and check_permissions(
            p.actionChoices.lokalita_dj_zapsat, user, archeologicky_zaznam.ident_cely
        ):
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
        "dokument_odpojit": check_permissions(
            p.actionChoices.archz_odpojit_dokument, user, archeologicky_zaznam.ident_cely
        ),
        "komponenta_smazat": check_permissions(
            p.actionChoices.komponenta_smazat_akce, user, archeologicky_zaznam.ident_cely
        ),
        "pripojit_eo": check_permissions(p.actionChoices.eo_pripojit_ez, user, archeologicky_zaznam.ident_cely),
        "odpojit_eo": check_permissions(p.actionChoices.eo_odpojit_ez, user, archeologicky_zaznam.ident_cely),
        "paginace_edit": check_permissions(p.actionChoices.eo_edit_akce, user, archeologicky_zaznam.ident_cely),
        "nalez_smazat": check_permissions(p.actionChoices.nalez_smazat_akce, user, archeologicky_zaznam.ident_cely),
        "zapsat_dokumenty": check_permissions(
            p.actionChoices.dok_zapsat_do_archz, user, archeologicky_zaznam.ident_cely
        ),
        "historie_fedora": check_permissions(p.actionChoices.historie_fedora, user, archeologicky_zaznam.ident_cely),
        "vypis": check_permissions(
            p.actionChoices.vypis_lokalita if app == "lokalita" else p.actionChoices.vypis_akce,
            user,
            archeologicky_zaznam.ident_cely,
        ),
    }
    return show


def get_required_fields(zaznam=None, next=0):
    """
    Funkce pro získaní dictionary povinných polí podle stavu arch záznamů.

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
@handle_fedora_error
@require_http_methods(["GET", "POST"])
def smazat_akce_vedoucí(request, ident_cely, akce_vedouci_id):
    """
    Funkce pohledu pro smazání dalšího vedoucího akce.

    :param request: Parametr ``request`` se předává do volání ``add_message()``, ``create_transaction()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param ident_cely: Parametr ``ident_cely`` se předává do volání ``debug()``, ``get_object_or_404()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param akce_vedouci_id: Identifikátor ``akce_vedouci_id`` používaný pro dohledání cílového záznamu.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
    """
    logger.debug("arch_z.views.smazat_akce_vedoucí.start", extra={"ident_cely": ident_cely, "pk": akce_vedouci_id})
    zaznam: AkceVedouci = get_object_or_404(AkceVedouci, id=akce_vedouci_id)
    az: ArcheologickyZaznam = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if request.method == "POST":
        if zaznam.akce.archeologicky_zaznam.ident_cely != ident_cely:
            logger.debug(
                "arch_z.views.smazat_akce_vedoucí.error",
                extra={"ident_cely": ident_cely, "pk": akce_vedouci_id},
            )
            messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
            return JsonResponse({"redirect": az.get_absolute_url()}, status=403)
        zaznam.delete()
        fedora_transaction = az.create_transaction(request.user, ZAZNAM_USPESNE_SMAZAN, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
        az.save_metadata(fedora_transaction, close_transaction=True)
        logger.debug(
            "arch_z.views.smazat_akce_vedoucí.success",
            extra={"ident_cely": ident_cely, "pk": akce_vedouci_id},
        )
        return JsonResponse({"redirect": reverse("arch_z:edit", kwargs={"ident_cely": ident_cely})})
    else:
        logger.debug("arch_z.views.smazat_akce_vedoucí.get", extra={"ident_cely": ident_cely, "pk": akce_vedouci_id})
        context = {
            "object": zaznam,
            "title": _("arch_z.views.smazat_akce_vedoucí.title.text"),
            "id_tag": "smazat-objekt-form",
            "button": _("core.views.smazat.submitButton.text"),
            "warnings": [_("arch_z.views.smazat_akce_vedoucí.save_warning")],
        }
        return render(request, "core/transakce_modal.html", context)


class GetAkceOtherKatastrView(LoginRequiredMixin, View, PermissionFilterMixin):
    """Implementuje komponentu ``GetAkceOtherKatastrView`` v rámci aplikace."""

    typ_zmeny_lookup = ZAPSANI_AZ

    def post(self, request):
        """
        Trida pohledu pro získaní souradnic dalších katastrů akce.

        :param request: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

            :return: Vrací výsledek volání ``JsonResponse()``.
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
    """Třida pohledu pro zobrazení domovské stránky akcií s navigačními možnostmi."""

    template_name = "arch_z/index.html"

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní kontextu podlehu.

        :param kwargs: Klíčové argumenty; nejsou předávány nadřazené metodě, kontext se sestavuje přímo.

        :return: Vrací proměnná ``context``.
        """
        context = {
            "toolbar_name": _("arch_z.views.akceIndexView.toolbarName"),
        }
        return context


class AkceListView(SearchListView):
    """Třida pohledu pro zobrazení listu/tabulky s akcemi."""

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
    vypis_app = "akce"
    map_enabled = True
    map_layer = "akce"

    def init_translations(self):
        """Nastaví přeložené texty pro nadpisy, popisky a záhlaví přehledu akcí."""
        super().init_translations()
        self.page_title = _("arch_z.views.AkceListView.page_title.text")
        self.search_sum = _("arch_z.views.AkceListView.search_sum.text")
        self.pick_text = _("arch_z.views.AkceListView.pick_text.text")
        self.hasOnlyVybrat_header = _("arch_z.views.AkceListView.hasOnlyVybrat_header.text")
        self.hasOnlyVlastnik_header = _("arch_z.views.AkceListView.hasOnlyVlastnik_header.text")
        self.hasOnlyArchive_header = _("arch_z.views.AkceListView.hasOnlyArchive_header.text")
        self.hasOnlyNase_header = _("arch_z.views.AkceListView.hasOnlyNase_header.text")
        self.default_header = _("arch_z.views.AkceListView.default_header.text")
        self.toolbar_name = _("arch_z.views.AkceListView.toolbar_name.text")

    @staticmethod
    def rename_field_for_ordering(field: str):
        """
        Převede název pole z URL parametru na odpovídající databázový název pro řazení querysetu akcí.

        :param field: Název pole z požadavku (může začínat znaménkem ``-`` pro sestupné řazení).

            :return: Vrací výsledek volání ``get()``.
        """
        field = field.replace("-", "")
        return {
            "ident_cely": "archeologicky_zaznam__ident_cely",
            "pristupnost": "archeologicky_zaznam__pristupnost__razeni",
            "hlavni_katastr": "archeologicky_zaznam__hlavni_katastr__nazev",
            "okres": "archeologicky_zaznam__hlavni_katastr__okres__nazev",
            "kraj": "archeologicky_zaznam__hlavni_katastr__okres__kraj__nazev",
            "katastry": "archeologicky_zaznam__katastry__nazev",
            "stav": "archeologicky_zaznam__stav",
            "organizace": "organizace__nazev_zkraceny",
            "vedouci_organizace": "vedouci_organizace",
            "vedouci": "vedouci_snapshot",
            "hlavni_vedouci": "hlavni_vedouci__vypis_cely",
            "uzivatelske_oznaceni": "archeologicky_zaznam__uzivatelske_oznaceni",
            "specifikace_data": "specifikace_data__razeni",
            "hlavni_typ": "hlavni_typ__razeni",
            "vedlejsi_typ": "vedlejsi_typ__razeni",
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
            "archeologicky_zaznam__hlavni_katastr",
            "archeologicky_zaznam__hlavni_katastr__okres",
            "archeologicky_zaznam__hlavni_katastr__okres__kraj",
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
        qs = qs.defer(
            "archeologicky_zaznam__hlavni_katastr__definicni_bod",
            "archeologicky_zaznam__hlavni_katastr__hranice",
            "archeologicky_zaznam__hlavni_katastr__okres__definicni_bod",
            "archeologicky_zaznam__hlavni_katastr__okres__hranice",
        )

        return self.check_filter_permission(qs)


class ProjektAkceChange(LoginRequiredMixin, AkceRelatedRecordUpdateView):
    """Třida pohledu pro zmenu projektové akce na samostatnou."""

    scroll_to_dj = True
    template_name = "core/transakce_modal.html"

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní kontextu podlehu.

        :param kwargs: Klíčové argumenty předávané do sestavení kontextu.

        :return: Vrací proměnná ``context``.
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
        Metoda pro vrácení stránky při volání GET.

        :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ovlivňuje větvení podmínek.
        :param args: Poziční argumenty předávané nadřazené metodě get.
        :param kwargs: Klíčové argumenty předávané do ``get_context_data()``.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.
        """
        context = self.get_context_data(**kwargs)
        if check_stav_changed(request, context["object"]):
            return JsonResponse(
                {"redirect": context["object"].get_absolute_url()},
                status=403,
            )
        return self.render_to_response(context)

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Metoda po potvrzení zmeny akce na samostatnou.

        Pri zavolíní se kontroluje, že akce nebyla změnena v mezičase potvrzení.
        Po úspešné kontrole se odebere projekt, nastaví typ akce na samostatnú a nastaví nový ident celý.
        Celá událost je zapsaná do historie.
        Uživatel je presmerován na detail akce.

        :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``create_transaction()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
        :param args: Poziční argumenty předávané nadřazené metodě post.
        :param kwargs: Klíčové argumenty předávané do ``get_context_data()``.

        :return: Vrací výsledek volání ``JsonResponse()``.
        """
        context = self.get_context_data(**kwargs)
        az = context["object"]
        if check_stav_changed(request, az):
            return JsonResponse(
                {"redirect": az.get_absolute_url()},
                status=403,
            )
        az: ArcheologickyZaznam
        fedora_transaction = az.create_transaction(request.user, ZAZNAM_USPESNE_EDITOVAN)
        akce: Akce = az.akce
        akce.active_transaction = fedora_transaction
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
        az.close_active_transaction_when_finished = True
        az.save()
        logger.debug("arch_z.views.ProjektAkceChange.post", extra={"ident_cely": str(az.ident_cely)})
        return JsonResponse({"redirect": az.get_absolute_url()})


class SamostatnaAkceChange(LoginRequiredMixin, AkceRelatedRecordUpdateView):
    """Třida pohledu pro zmenu samostatní akce na projektovou."""

    scroll_to_dj = True
    template_name = "core/transakce_table_modal.html"

    def get_context_data(self, **kwargs):
        """
        Metoda pro získaní kontextu podlehu.

        :param kwargs: Klíčové argumenty předávané do sestavení kontextu.

        :return: Vrací proměnná ``context``.
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
        Metoda pro vrácení stránky při volání GET s formulářem pro výběr projektu.

        :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ovlivňuje větvení podmínek.
        :param args: Poziční argumenty předávané nadřazené metodě get.
        :param kwargs: Klíčové argumenty předávané do ``get_context_data()``.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.
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

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """
        Metoda po potvrzení zmeny akce na projektovou.

        Pri zavolíní se kontroluje, že akce nebyla změnena v mezičase potvrzení.
        Po úspešné kontrole se napojí projekt, nastaví typ akce na projektovou a nastaví nový ident celý.
        Celá událost je zapsaná do historie.
        Uživatel je presmerován na detail akce.

        :param request: Objekt HTTP požadavku s POST daty
        :param args: Další poziční argumenty dědězité z nadřazené třídy, nepoužívané.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``redirect()``.
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
            fedora_transaction = az.create_transaction(request.user, ZAZNAM_USPESNE_EDITOVAN)
            projekt = form.cleaned_data["projekt"]
            akce = az.akce
            akce.active_transaction = fedora_transaction
            akce.projekt = Projekt.objects.get(id=projekt)
            akce.typ = Akce.TYP_AKCE_PROJEKTOVA
            akce.save()
            old_ident = az.ident_cely
            az.set_akce_ident(get_project_event_ident(az.akce.projekt), delete_container=False)
            az.save()
            Historie(
                typ_zmeny=ZMENA_AZ,
                uzivatel=request.user,
                poznamka=f"{old_ident} -> {az.ident_cely}",
                vazba=az.historie,
            ).save()
            logger.debug("arch_z.views.SamostatnaAkceChange.post.valid", extra={"ident_cely": str(az.ident_cely)})
            az.close_active_transaction_when_finished = True
            az.save()
        else:
            logger.debug(
                "arch_z.views.SamostatnaAkceChange.post.not_valid",
                extra={"error": form.errors, "form_error": form.non_field_errors},
            )
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

        return redirect(az.get_absolute_url())


class ArchZAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView, PermissionFilterMixin):
    """Třida pohledu pro vrácení výsledku pro autocomplete arch záznamů."""

    typ_zmeny_lookup = ZAPSANI_AZ

    def get_result_label(self, result):
        """
        Vrací result label.

        :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.

            :return: Vrací hodnotu podle větve zpracování.
        """
        if self.lookup_type == "akce":
            return f"{result.ident_cely} ({result.hlavni_katastr}; {result.akce.hlavni_vedouci}; {result.akce.datum_zahajeni} - {result.akce.datum_ukonceni})"
        else:
            return f"{result.ident_cely} ({result.lokalita.nazev})"

    def get_queryset(self):
        """
        Vrací queryset. v aplikaci.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``none()``, výsledek volání ``check_filter_permission()``.
        """
        if not self.request.user.is_authenticated:
            return ArcheologickyZaznam.objects.none()
        self.lookup_type = self.kwargs.get("type")
        if self.lookup_type == "akce":
            qs = (
                ArcheologickyZaznam.objects.filter(typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_AKCE)
                .select_related("hlavni_katastr", "akce__hlavni_vedouci", "akce")
                .order_by("ident_cely")
            )
            if self.q:
                qs = qs.filter(
                    Q(ident_cely__icontains=self.q)
                    | Q(hlavni_katastr__nazev__icontains=self.q)
                    | Q(akce__hlavni_vedouci__vypis_cely__icontains=self.q)
                )
        else:
            qs = (
                ArcheologickyZaznam.objects.filter(typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA)
                .select_related("lokalita")
                .order_by("ident_cely")
            )
            if self.q:
                qs = qs.filter(Q(ident_cely__icontains=self.q) | Q(lokalita__nazev__icontains=self.q))
        return self.check_filter_permission(qs)


class ArchZTableRowView(LoginRequiredMixin, View):
    """Třida pohledu pro vrácení řádku tabulky s arch záznamem."""

    def get(self, request):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` předává se do volání ``get()``, pracuje se s atributy ``GET``.

            :return: Vrací výsledek volání ``HttpResponse()``.
        """
        zaznam = ArcheologickyZaznam.objects.get(id=request.GET.get("id", ""))
        context = {"arch_z": zaznam}
        if zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            context["type"] = "arch_z"
            context["card_type"] = "akce"
        else:
            context["type"] = "lokalita"
            context["card_type"] = "lokalita"
        return HttpResponse(render_to_string("ez/ez_odkazy_table_row.html", context))


def get_dj_form_detail(app, jednotka, jednotky=None, show=None, old_adb_post=None, user=None, session=None):
    """
    Funkce pro získaní dictionary contextu dokumentační jednotky.

    :param app: druh archeologického záznamu ro který se daný context počítá.
    :param jednotka: model DokumentacniJednotka pro který se daný context počítá.
    :param jednotky: list modelů DokumentacniJednotka použit pro správně zobrazení možnosti zmeny typu DJ.
    :param show: dictionary pro zobrazení možnosti uživatele na stránce.
    :param old_adb_post: staré volání CreateADBForm pro správně zobrazení chyb formuláře.
    :param user: Parametr ``user`` se předává do volání ``check_permissions()``, pracuje se s atributy ``hlavni_role``, ovlivňuje větvení podmínek.
    :param session: Volitelná Django session pro načtení dat souběžné editace ADB formuláře.

    :return: dictionary kontextu DJ pro správné zobrazení stránky.
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
        and check_permissions(p.actionChoices.adb_zapsat, user, jednotka.ident_cely)
    )
    show_add_pian = False if jednotka.pian else True
    show_approve_pian = (
        True
        if jednotka.pian
        and jednotka.pian.stav == PIAN_NEPOTVRZEN
        and check_permissions(p.actionChoices.pian_potvrdit, user, jednotka.ident_cely)
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
        show_add_komponenta = not jednotka.negativni_jednotka and check_permissions(
            p.actionChoices.archz_komponenta_zapsat, user, jednotka.ident_cely
        )
        show_pripojit_pian_mapa = show_add_pian and check_permissions(
            p.actionChoices.akce_pripojit_pian_mapa, user, jednotka.ident_cely
        )
        show_pripojit_pian_id = show_add_pian and check_permissions(
            p.actionChoices.akce_pripojit_pian_id, user, jednotka.ident_cely
        )
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
        show_add_komponenta = not jednotka.negativni_jednotka and check_permissions(
            p.actionChoices.lokalita_komponenta_zapsat, user, jednotka.ident_cely
        )
        show_pripojit_pian_mapa = show_add_pian and check_permissions(
            p.actionChoices.lokalita_pripojit_pian_mapa, user, jednotka.ident_cely
        )
        show_pripojit_pian_id = show_add_pian and check_permissions(
            p.actionChoices.lokalita_pripojit_pian_id, user, jednotka.ident_cely
        )
    if user.hlavni_role.pk in (ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID):
        show_import_pian_change_user = (
            jednotka.pian
            and jednotka.pian.stav == PIAN_NEPOTVRZEN
            and jednotka.archeologicky_zaznam.stav == AZ_STAV_ZAPSANY
        )
    else:
        show_import_pian_change_user = jednotka.archeologicky_zaznam.stav < AZ_STAV_ARCHIVOVANY
    if jednotky and jednotky.count() > 1 and jednotka.ident_cely.endswith("D01"):
        show_dj_smazat = False
    else:
        show_dj_smazat = check_permissions(p.actionChoices.dj_smazat, user, jednotka.ident_cely)
    concurrent_changes = session.pop(f"dj_concurrent_changes_{jednotka.ident_cely}", None) if session else None
    post_data_dict = (
        session.pop(f"dj_post_data_{jednotka.ident_cely}", None) if (session and concurrent_changes) else None
    )
    if post_data_dict:
        from django.http import QueryDict

        post_qd = QueryDict(mutable=True)
        post_qd.update(post_data_dict)
        create_db_form.data = post_qd
        create_db_form.files = {}
        create_db_form.is_bound = True

    dj_form_detail = {
        "ident_cely": jednotka.ident_cely,
        "concurrent_changes": concurrent_changes,
        "fresh_form_url": jednotka.archeologicky_zaznam.get_absolute_url(jednotka.ident_cely),
        "pian_ident_cely": jednotka.pian.ident_cely if jednotka.pian else "",
        "form": create_db_form,
        "show_add_adb": show_adb_add,
        "show_add_komponenta": show_add_komponenta,
        "show_add_pian": (show_add_pian and check_permissions(p.actionChoices.pian_zapsat, user, jednotka.ident_cely)),
        "show_add_pian_zapsat": (
            show_add_pian and check_permissions(p.actionChoices.pian_zapsat, user, jednotka.ident_cely)
        ),
        "show_add_pian_importovat": (
            show_add_pian and check_permissions(p.actionChoices.pian_zapsat, user, jednotka.ident_cely)
        ),
        "show_remove_pian": (
            not show_add_pian
            and check_permissions(p.actionChoices.pian_odpojit, user, jednotka.ident_cely)
            and jednotka.typ.id != TYP_DJ_KATASTR
        ),
        "show_uprav_pian": show_uprav_pian,
        "show_approve_pian": show_approve_pian,
        "show_pripojit_pian": True if jednotka.pian is None else False,
        "show_import_pian_new": show_add_pian
        and check_permissions(p.actionChoices.pian_import_new, user, jednotka.ident_cely),
        "show_import_pian_change": not show_add_pian
        and show_import_pian_change_user
        and check_permissions(p.actionChoices.pian_import_change, user, jednotka.pian.ident_cely),
        "show_change_katastr": (
            True
            if jednotka.typ.id == TYP_DJ_KATASTR
            and check_permissions(p.actionChoices.dj_zmenit_katastr, user, jednotka.ident_cely)
            else False
        ),
        "show_dj_smazat": show_dj_smazat,
        "show_vb_smazat": check_permissions(p.actionChoices.vb_smazat, user, jednotka.ident_cely),
        "show_pripojit_pian_mapa": show_pripojit_pian_mapa,
        "show_pripojit_pian_id": show_pripojit_pian_id,
    }
    if has_adb and app != "lokalita":
        logger.debug("arch_z.views.get_dj_form_detail", extra={"ident_cely": jednotka.ident_cely})
        adb_concurrent_changes = (
            session.pop(f"adb_concurrent_changes_{jednotka.adb.ident_cely}", None) if session else None
        )
        adb_form = CreateADBForm(
            old_adb_post,
            instance=jednotka.adb,
            # prefix=jednotka.adb.ident_cely,
            readonly=not show["editovat"],
        )
        if old_adb_post and adb_concurrent_changes:
            adb_form.is_bound = True
        dj_form_detail["adb_form"] = adb_form
        dj_form_detail["adb_ident_cely"] = jednotka.adb.ident_cely
        dj_form_detail["adb_concurrent_changes"] = adb_concurrent_changes
        dj_form_detail["adb_fresh_form_url"] = jednotka.archeologicky_zaznam.get_absolute_url(jednotka.ident_cely)
        dj_form_detail["vyskovy_bod_formset"] = vyskovy_bod_formset(
            instance=jednotka.adb, prefix=jednotka.adb.ident_cely + "_vb"
        )
        dj_form_detail["vyskovy_bod_formset_helper"] = VyskovyBodFormSetHelper()
        dj_form_detail["adb_pk"] = jednotka.adb.pk
        dj_form_detail["show_remove_adb"] = True if show["editovat"] else False
    return dj_form_detail
