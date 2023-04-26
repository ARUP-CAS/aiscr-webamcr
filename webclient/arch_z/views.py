import simplejson as json

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
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_ZAPSANY,
    ROLE_ADMIN_ID,
    ROLE_ARCHIVAR_ID,
    ZAPSANI_AZ,
    ZMENA_AZ
)
from core.exceptions import MaximalEventCount
from core.forms import CheckStavNotChangedForm, VratitForm
from core.ident_cely import get_project_event_ident
from core.message_constants import (
    MAXIMUM_AKCII_DOSAZENO,
    PRISTUP_ZAKAZAN,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
)
from core.utils import (
    get_all_pians_with_akce,
    get_all_pians_with_dj,
    get_centre_from_akce,
    get_heatmap_pian,
    get_heatmap_pian_density,
    get_message,
    get_num_pians_from_envelope,
    get_pians_from_envelope,
)
from core.views import SearchListView, check_stav_changed
from dal import autocomplete
from dj.forms import CreateDJForm
from dj.models import DokumentacniJednotka
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.forms import inlineformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from dokument.models import Dokument
from dokument.views import get_komponenta_form_detail, odpojit, pripojit
from heslar.hesla import (
    HESLAR_AREAL,
    HESLAR_AREAL_KAT,
    HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRESNE,
    HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRIBLIZNE,
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_DRUH_KAT,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_OBJEKT_SPECIFIKACE_KAT,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_DRUH_KAT,
    HESLAR_PREDMET_SPECIFIKACE,
    SPECIFIKACE_DATA_PRESNE,
    TYP_DJ_KATASTR,
    TYP_DJ_SONDA_ID,
    TYP_PROJEKTU_PRUZKUM_ID,
)
from heslar.models import Heslar
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
from projekt.forms import PripojitProjektForm
from projekt.models import Projekt
from services.mailer import Mailer


logger = logging.getLogger('python-logstash-logger')


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
    def get_shows(self):
        """
        Metóda pro získaní informací které čáasti stránky mají být zobrazeny.
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

    def get_dokumenty(self):
        """
        Metóda pro získaní dokumentů navázaných na akci.
        """
        ident_cely = self.kwargs.get("ident_cely")
        return (
            Dokument.objects.filter(casti__archeologicky_zaznam__ident_cely=ident_cely)
            .select_related("soubory")
            .prefetch_related("soubory__soubory")
            .order_by("ident_cely")
        )

    def get_externi_odkazy(self):
        """
        Metóda pro získaní externích odkazů navázaných na akci.
        """
        ident_cely = self.kwargs.get("ident_cely")
        return (
            ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely=ident_cely)
            .select_related("externi_zdroj")
            .order_by("id")
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
            "id"
        ):
            vedouci: AkceVedouci
            akce_zaznam_ostatni_vedouci.append(
                [str(vedouci.vedouci), str(vedouci.organizace)]
            )
        context["ostatni_vedouci_objekt_formset"] = ostatni_vedouci_objekt_formset
        context["ostatni_vedouci_objekt_formset_helper"] = AkceVedouciFormSetHelper()
        context["ostatni_vedouci_objekt_formset_readonly"] = True
        context["akce_zaznam_ostatni_vedouci"] = akce_zaznam_ostatni_vedouci

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní contextu akci pro template.
        """
        context = super().get_context_data(**kwargs)
        zaznam = self.get_archeologicky_zaznam()
        context["zaznam"] = zaznam
        context["dokumentacni_jednotky"] = self.get_jednotky()
        context["dokumenty"] = self.get_dokumenty()
        context["history_dates"] = get_history_dates(zaznam.historie)
        context["show"] = get_detail_template_shows(
            zaznam, self.get_jednotky(), self.request.user
        )
        context["externi_odkazy"] = self.get_externi_odkazy()
        if zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            context["presna_specifikace"] = (
                True
                if zaznam.akce.specifikace_data
                == Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE)
                else False
            )
        context["app"] = "akce"
        context["showbackdetail"] = False
        if zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            if zaznam.akce.typ == Akce.TYP_AKCE_PROJEKTOVA:
                context["showbackdetail"] = True
        self.get_vedouci(context)
        context["next_url"] = zaznam.get_absolute_url()
        return context


class ArcheologickyZaznamDetailView(LoginRequiredMixin, AkceRelatedRecordUpdateView):
    """
    Třída pohledu pro zobrazení detailu akce.
    """
    template_name = "arch_z/dj/arch_z_detail.html"

    def get_archeologicky_zaznam(self):
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
        return context


class DokumentacniJednotkaRelatedUpdateView(AkceRelatedRecordUpdateView):
    """
    Třida, která se dedí a která obsahuje metódy pro získaní relací DJ.
    """
    template_name = "arch_z/dj/dj_update.html"

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
        except Exception as e:
            pass
        context["dj_form_create"] = CreateDJForm(
            jednotky=self.get_jednotky(),
            typ_arch_z=self.get_archeologicky_zaznam().typ_zaznamu,
            typ_akce=typ_akce,
        )
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
            "akce", jednotka, jednotky, show, old_adb_post
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


class PianUpdateView(LoginRequiredMixin, DokumentacniJednotkaRelatedUpdateView):
    """
    Třida pohledu pro editaci PIANu dokumentační jednotky.
    """
    template_name = "arch_z/dj/pian_update.html"

    def get_context_data(self, **kwargs):
        """
        Metóda pro získaní context dat navíc oproti přepisované metóde, formulář pro editaci PIANu.
        """
        context = super().get_context_data(**kwargs)
        context["j"] = self.get_dokumentacni_jednotka()
        context["pian_form_update"] = PianCreateForm()
        return context


class AdbCreateView(DokumentacniJednotkaRelatedUpdateView):
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
            logger.debug("arch_z.views.edit.form_valid")
            form_az.save()
            form_akce.save()
            ostatni_vedouci_objekt_formset.save()
            if form_az.changed_data or form_akce.changed_data:
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
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
            "formAZ": form_az,
            "formAkce": form_akce,
            "ostatni_vedouci_objekt_formset": ostatni_vedouci_objekt_formset,
            "ostatni_vedouci_objekt_formset_helper": AkceVedouciFormSetHelper(),
            "ostatni_vedouci_objekt_formset_readonly": False,
            "title": _("Editace archeologického záznamu"),
            "header": _("Archeologický záznam"),
            "button": _("Uložit změny"),
            "sam_akce": False if zaznam.akce.projekt else True,
            "heslar_specifikace_v_letech_presne": HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRESNE,
            "heslar_specifikace_v_letech_priblizne": HESLAR_DATUM_SPECIFIKACE_V_LETECH_PRIBLIZNE,
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
    if az.stav != AZ_STAV_ZAPSANY:
        logger_s.debug("arch_z.views.odeslat permission denied")
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
        az.set_odeslany(request.user)
        az.save()
        messages.add_message(
            request, messages.SUCCESS, get_message(az, "USPESNE_ODESLANA")
        )
        logger.debug("arch_z.views.odeslat.akce_uspesne_odeslana",
                     extra={"message": get_message(az, "USPESNE_ODESLANA")})
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
        "title": _("arch_z.modalForm.odeslatArchz.title.text"),
        "id_tag": "odeslat-akci-form",
        "button": _("arch_z.modalForm.odeslatArchz.submit.button"),
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
        # TODO BR-A-5
        az.set_archivovany(request.user)
        if az.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA and az.ident_cely.startswith(IDENTIFIKATOR_DOCASNY_PREFIX):
            az.set_lokalita_permanent_ident_cely()
        az.save()
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
        "title": _("arch_z.modalForm.archivovatArchz.title.text"),
        "id_tag": "archivovat-akci-form",
        "button": _("arch_z.modalForm.archivovatArchz.submit.button"),
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
            duvod = form.cleaned_data["reason"]
            projekt = None
            if az.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
                projekt = az.akce.projekt
            # BR-A-3
            if az.stav == AZ_STAV_ODESLANY and projekt is not None:
                #  Return also project from the states P6 or P5 to P4
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
            az.save()
            if before_save_state == AZ_STAV_ODESLANY:
                Mailer.send_ev01(arch_z=az, reason=duvod)
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
        "title": _("arch_z.modalForm.vratitArchz.title.text"),
        "id_tag": "vratit-akci-form",
        "button": _("arch_z.modalForm.vratitArchz.submit.button"),
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
            "title": _("Nová projektová akce"),
            "header": _("Nová projektová akce"),
            "create_akce": False,
        }
    else:
        projekt = None
        uzamknout_specifik = False
        context = {
            "title": _("Nová samostatna akce"),
            "header": _("Nová samostatna akce"),
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
            az.stav = AZ_STAV_ZAPSANY
            az.typ_zaznamu = ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
            try:
                if projekt:
                    az.ident_cely = get_project_event_ident(projekt)
                    typ_akce = Akce.TYP_AKCE_PROJEKTOVA
                else:
                    az.save()
                    az.ident_cely = get_akce_ident(
                        az.hlavni_katastr.okres.kraj.rada_id, True, az.id
                    )
                    typ_akce = Akce.TYP_AKCE_SAMOSTATNA
            except MaximalEventCount:
                messages.add_message(request, messages.ERROR, MAXIMUM_AKCII_DOSAZENO)
            else:
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

                messages.add_message(
                    request, messages.SUCCESS, get_message(az, "USPESNE_ZAPSANA")
                )
                logger.debug("arch_z.views.zapsat.success", extra={"akce": akce.pk, "projekt": projekt_ident_cely})
                return redirect("arch_z:detail", az.ident_cely)

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
            "button": _("Vytvoř akci"),
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
    Po post volání se volá metóda na modelu pro smazání akce, historických vazeb, komponent, externích odkazů a DJ.
    """
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if check_stav_changed(request, az):
        return JsonResponse(
            {"redirect": az.archeologicky_zaznam.get_absolute_url()},
            status=403,
        )
    if az.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
        projekt = az.akce.projekt
    else:
        projekt = None
    if request.method == "POST":
        # Parent records
        historie_vazby = az.historie
        komponenty_jednotek_vazby = []
        for dj in az.dokumentacni_jednotky_akce.all():
            if dj.komponenty:
                komponenty_jednotek_vazby.append(dj.komponenty)
        for eo in az.externi_odkazy.all():
            eo.delete()
        az.delete()
        historie_vazby.delete()
        for komponenta_vazba in komponenty_jednotek_vazby:
            komponenta_vazba.delete()
        logger.debug("arch_z.views.smazat.success", extra={"ident_cely": ident_cely})
        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)

        if projekt:
            return JsonResponse(
                {
                    "redirect": reverse(
                        "projekt:detail", kwargs={"ident_cely": projekt.ident_cely}
                    )
                }
            )
        else:
            return JsonResponse({"redirect": reverse("lokalita:index")})
    else:
        form_check = CheckStavNotChangedForm(initial={"old_stav": az.stav})
        context = {
            "object": az,
            "title": _("arch_z.modalForm.smazani.title.text"),
            "id_tag": "smazat-akci-form",
            "button": _("arch_z.modalForm.smazani.submit.button"),
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
    return pripojit(request, arch_z_ident_cely, proj_ident_cely, ArcheologickyZaznam)


@login_required
@require_http_methods(["GET", "POST"])
def odpojit_dokument(request, ident_cely, arch_z_ident_cely):
    """
    Funkce pohledu pro odpojení dokumentu do akce.
    Funkce volá další funkci pro odpojení s parametrem navíc - arch záznamem.
    """
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=arch_z_ident_cely)
    if az.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
        return odpojit(request, ident_cely, arch_z_ident_cely, az)
    else:
        return odpojit(request, ident_cely, arch_z_ident_cely, az)


@login_required
@require_http_methods(["POST"])
def post_ajax_get_pians(request):
    """
    Vypada nepouzito check s J. Bartos
    """
    body = json.loads(request.body.decode("utf-8"))
    pians = get_all_pians_with_dj(body["dj_ident_cely"], body["lat"], body["lng"])
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
        pians = get_pians_from_envelope(
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


@require_http_methods(["POST"])
def post_akce2kat(request):
    """
    Funkce pohledu pro získaní souradnic katastru akce.
    """
    body = json.loads(request.body.decode("utf-8"))
    logger.debug("arch_z.views.post_akce2kat.start", extra={"body": body})
    katastr_name = body["cadastre"]
    pian_ident_cely = body["pian"]

    if len(katastr_name) > 0:
        [poi, geom, presnost] = get_centre_from_akce(katastr_name, pian_ident_cely)
        if len(str(poi)) > 0:
            return JsonResponse(
                {
                    "lat": str(poi.lat),
                    "lng": str(poi.lng),
                    "zoom": str(poi.zoom),
                    "geom": str(geom).split(";")[1].replace(", ", ",")
                    if geom
                    else None,
                    "presnost": str(presnost) if geom else 4,
                },
                status=200,
            )
    return JsonResponse({"lat": "", "lng": "", "zoom": "", "geom": ""}, status=200)


def get_history_dates(historie_vazby):
    """
    Funkce pro získaní dátumů pro historii.

    Args:     
        historie_vazby (HistorieVazby): model historieVazby dané akce.
    
    Returns:
        historie: dictionary dátumů k historii.
    """
    historie = {
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_AZ),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_AZ),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_AZ),
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
    show_vratit = archeologicky_zaznam.stav > AZ_STAV_ZAPSANY
    show_odeslat = archeologicky_zaznam.stav == AZ_STAV_ZAPSANY
    show_archivovat = archeologicky_zaznam.stav == AZ_STAV_ODESLANY and app == "akce"
    show_edit = archeologicky_zaznam.stav not in [
        AZ_STAV_ARCHIVOVANY,
    ]
    show_arch_links = archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
    zmenit_proj_akci = False
    zmenit_sam_akci = False
    if archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
        allowed_groups = Group.objects.filter(id__in=[ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID])
        if user.hlavni_role in allowed_groups:
            if archeologicky_zaznam.akce.typ == Akce.TYP_AKCE_PROJEKTOVA:
                zmenit_proj_akci = True
            else:
                zmenit_sam_akci = True
        if (
            archeologicky_zaznam.akce.typ == Akce.TYP_AKCE_SAMOSTATNA
            and dok_jednotky.count() == 1
            and dok_jednotky.first().typ == Heslar.objects.get(id=TYP_DJ_KATASTR)
        ):
            add_dj = False
        else:
            add_dj = True
    elif dok_jednotky.count() == 0:
        add_dj = True
    else:
        add_dj = False
    show = {
        "vratit_link": show_vratit,
        "odeslat_link": show_odeslat,
        "archivovat_link": show_archivovat,
        "editovat": show_edit,
        "arch_links": show_arch_links,
        "pripojit_dokumenty": True,
        "add_dj": add_dj,
        "zmenit_proj_akci": zmenit_proj_akci,
        "zmenit_sam_akci": zmenit_sam_akci,
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
@require_http_methods(["GET"])
def smazat_akce_vedoucí(request, akce_vedouci_id):
    """
    Funkce pohledu pro smazání dalšího vedoucího akce.
    """
    zaznam = AkceVedouci.objects.get(id=akce_vedouci_id)
    zaznam.delete()
    next_url = request.GET.get("next")
    if next_url:
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
            response = next_url
        else:
            logger.debug("arch_z.views.smazat_akce_vedoucí.redirect", extra={"next_url": next_url})
            response = reverse("core:home")
    messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
    response = redirect(next_url)
    return response


@login_required
@require_http_methods(["POST"])
def post_ajax_get_akce_other_katastr(request):
    """
    Funkce pohledu pro získaní souradnic dalších katastrů akce.
    """
    body = json.loads(request.body.decode("utf-8"))
    dis = get_all_pians_with_akce(body["akce_ident_cely"])
    back = []
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
    else:
        return JsonResponse({"points": []}, status=200)


def get_arch_z_context(request, ident_cely, zaznam, app):
    """
    Funkce pro získaní dictionary contextu archeologického záznamu.

    Args:     
        ident_cely (string): string ident celý záznamu.
        
        zaznam (ArcheologickyZaznam): model ArcheologickyZaznam pro který se daný context počítá.

        app (string): druh archeologického záznamu ro který se daný context počítá.

    Returns:
        context: dictionary kontextu pro správné zobrazení stránky.
    """
    context = {"warnings": request.session.pop("temp_data", None)}
    if app == "akce":
        context["arch_projekt_link"] = request.session.pop("arch_projekt_link", None)
    else:
        context["arch_projekt_link"] = None
    old_nalez_post = request.session.pop("_old_nalez_post", None)
    komp_ident_cely = request.session.pop("komp_ident_cely", None)
    old_adb_post = request.session.pop("_old_adb_post", None)
    adb_ident_cely = request.session.pop("adb_ident_cely", None)
    obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
    areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
    druh_objekt_choices = heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT)
    druh_predmet_choices = heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT)
    specifikace_objekt_choices = heslar_12(
        HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT
    )
    specifikce_predmetu_choices = list(
        Heslar.objects.filter(nazev_heslare=HESLAR_PREDMET_SPECIFIKACE).values_list(
            "id", "heslo"
        )
    )
    dokumenty = (
        Dokument.objects.filter(casti__archeologicky_zaznam__ident_cely=ident_cely)
        .select_related("soubory")
        .prefetch_related("soubory__soubory")
    ).order_by("ident_cely")
    jednotky = (
        DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely=ident_cely)
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
    show = get_detail_template_shows(zaznam, jednotky, request.user)

    dj_form_create = CreateDJForm(jednotky=jednotky, typ_arch_z=zaznam.typ_zaznamu)
    pian_form_create = PianCreateForm()
    komponenta_form_create = CreateKomponentaForm(obdobi_choices, areal_choices)
    adb_form_create = CreateADBForm()
    dj_forms_detail = []
    komponenta_forms_detail = []
    pian_forms_detail = []
    NalezObjektFormset = inlineformset_factory(
        Komponenta,
        NalezObjekt,
        form=create_nalez_objekt_form(
            druh_objekt_choices,
            specifikace_objekt_choices,
            not_readonly=show["editovat"],
        ),
        extra=1 if show["editovat"] else 0,
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
        extra=1 if show["editovat"] else 0,
        can_delete=False,
    )
    for jednotka in jednotky:
        jednotka: DokumentacniJednotka
        vyskovy_bod_formset = inlineformset_factory(
            Adb,
            VyskovyBod,
            form=create_vyskovy_bod_form(
                pian=jednotka.pian, not_readonly=show["editovat"]
            ),
            extra=1,
            can_delete=False,
        )
        has_adb = jednotka.has_adb()
        show_adb_add = (
            jednotka.pian
            and jednotka.typ.id == TYP_DJ_SONDA_ID
            and not has_adb
            and show["editovat"]
        )
        show_add_komponenta = not jednotka.negativni_jednotka and show["editovat"]
        show_add_pian = False if jednotka.pian else True
        show_approve_pian = (
            True
            if jednotka.pian
            and jednotka.pian.stav == PIAN_NEPOTVRZEN
            and show["editovat"]
            else False
        )
        dj_form_detail = {
            "ident_cely": jednotka.ident_cely,
            "pian_ident_cely": jednotka.pian.ident_cely if jednotka.pian else "",
            "form": CreateDJForm(
                instance=jednotka,
                jednotky=jednotky,
                prefix=jednotka.ident_cely,
                not_readonly=show["editovat"],
                typ_arch_z=zaznam.typ_zaznamu,
            ),
            "show_add_adb": show_adb_add,
            "show_add_komponenta": show_add_komponenta,
            "show_add_pian": (show_add_pian and show["editovat"]),
            "show_remove_pian": (not show_add_pian and show["editovat"]),
            "show_uprav_pian": jednotka.pian
            and jednotka.pian.stav == PIAN_NEPOTVRZEN
            and show["editovat"],
            "show_approve_pian": show_approve_pian,
            "show_pripojit_pian": True if jednotka.pian is None else False,
        }
        if has_adb:
            logger.debug("arch_z.views.get_arch_z_context.adb", extra={"jednotka_ident_cely": jednotka.ident_cely})
            dj_form_detail["adb_form"] = (
                CreateADBForm(
                    old_adb_post,
                    instance=jednotka.adb,
                    prefix=jednotka.adb.ident_cely,
                    readonly=not show["editovat"],
                )
                if jednotka.adb.ident_cely == adb_ident_cely
                else CreateADBForm(
                    instance=jednotka.adb,
                    prefix=jednotka.adb.ident_cely,
                    readonly=not show["editovat"],
                )
            )
            dj_form_detail["adb_ident_cely"] = jednotka.adb.ident_cely
            dj_form_detail["vyskovy_bod_formset"] = vyskovy_bod_formset(
                instance=jednotka.adb, prefix=jednotka.adb.ident_cely + "_vb"
            )
            dj_form_detail["vyskovy_bod_formset_helper"] = VyskovyBodFormSetHelper()
            dj_form_detail["show_remove_adb"] = True if show["editovat"] else False
        dj_forms_detail.append(dj_form_detail)
        if jednotka.pian:
            pian_forms_detail.append(
                {
                    "ident_cely": jednotka.pian.ident_cely,
                    "center_point": "",
                    "form": PianCreateForm(
                        instance=jednotka.pian, prefix=jednotka.pian.ident_cely
                    ),
                }
            )
        for komponenta in jednotka.komponenty.komponenty.all():
            komponenta_forms_detail.append(
                {
                    "ident_cely": komponenta.ident_cely,
                    "form": CreateKomponentaForm(
                        obdobi_choices,
                        areal_choices,
                        instance=komponenta,
                        prefix=komponenta.ident_cely,
                        readonly=not show["editovat"],
                    ),
                    "form_nalezy_objekty": NalezObjektFormset(
                        old_nalez_post,
                        instance=komponenta,
                        prefix=komponenta.ident_cely + "_o",
                    )
                    if komponenta.ident_cely == komp_ident_cely
                    else NalezObjektFormset(
                        instance=komponenta, prefix=komponenta.ident_cely + "_o"
                    ),
                    "form_nalezy_predmety": NalezPredmetFormset(
                        old_nalez_post,
                        instance=komponenta,
                        prefix=komponenta.ident_cely + "_p",
                    )
                    if komponenta.ident_cely == komp_ident_cely
                    else NalezPredmetFormset(
                        instance=komponenta, prefix=komponenta.ident_cely + "_p"
                    ),
                    "helper_predmet": NalezFormSetHelper(typ="predmet"),
                    "helper_objekt": NalezFormSetHelper(typ="objekt"),
                }
            )
    externi_odkazy = (
        ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely=ident_cely)
        .select_related("externi_zdroj")
        .order_by("id")
    )

    context["dj_form_create"] = dj_form_create
    context["pian_form_create"] = pian_form_create
    context["dj_forms_detail"] = dj_forms_detail
    context["adb_form_create"] = adb_form_create
    context["komponenta_form_create"] = komponenta_form_create
    context["komponenta_forms_detail"] = komponenta_forms_detail
    context["pian_forms_detail"] = pian_forms_detail
    context["history_dates"] = get_history_dates(zaznam.historie)
    context["zaznam"] = zaznam
    context["dokumenty"] = dokumenty
    context["dokumentacni_jednotky"] = jednotky
    context["show"] = show
    context["externi_odkazy"] = externi_odkazy
    if zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
        if zaznam.akce.typ == Akce.TYP_AKCE_PROJEKTOVA:
            context["showbackdetail"] = True
            context["app"] = "pr"
            context[
                "arch_pr_link"
            ] = '{% url "projekt:projekt_archivovat" zaznam.akce.projekt.ident_cely %}?sent_stav={{projekt.stav}}&from_arch=true'
        else:
            context["showbackdetail"] = False
            context["app"] = "sam"
            context["arch_pr_link"] = None

    return context


class AkceIndexView(LoginRequiredMixin, TemplateView):
    """
    Třida pohledu pro zobrazení domovské stránky akcií s navigačními možnostmi.
    """
    template_name = "arch_z/index.html"


class AkceListView(SearchListView):
    """
    Třida pohledu pro zobrazení listu/tabulky s akcemi.
    """
    table_class = AkceTable
    model = Akce
    filterset_class = AkceFilter
    export_name = "export_akce_"
    page_title = _("akce.vyber.pageTitle")
    app = "akce"
    toolbar = "toolbar_akce.html"
    search_sum = _("akce.vyber.pocetVyhledanych")
    pick_text = _("akce.vyber.pickText")
    hasOnlyVybrat_header = _("akce.vyber.header.hasOnlyVybrat")
    hasOnlyVlastnik_header = _("akce.vyber.header.hasOnlyVlastnik")
    hasOnlyArchive_header = _("akce.vyber.header.hasOnlyArchive")
    hasOnlyPotvrdit_header = _("akce.vyber.header.default")
    default_header = _("akce.vyber.header.default")
    toolbar_name = _("akce.template.toolbar.title")

    def get_queryset(self):
        qs = super().get_queryset()
        qs = (
            qs.all()
            .select_related(
                "archeologicky_zaznam__hlavni_katastr",
                "archeologicky_zaznam__hlavni_katastr__okres",
                "organizace",
                "hlavni_vedouci",  
            ).prefetch_related("archeologicky_zaznam__katastry","archeologicky_zaznam__katastry__okres")
        )
        return qs


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
            "title": _("arch_z.modalForm.zmenaProjektoveAkce.title.text"),
            "id_tag": "zmenit-akci-form",
            "button": _("arch_z.modalForm.zmenaProjektoveAkce.submit.button"),
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
        az = context["object"]
        if check_stav_changed(request, az):
            return JsonResponse(
                {"redirect": az.get_absolute_url()},
                status=403,
            )

        az.akce.projekt = None
        az.akce.typ = Akce.TYP_AKCE_SAMOSTATNA
        az.akce.save()
        old_ident = az.ident_cely
        if az.stav == AZ_STAV_ARCHIVOVANY:
            az.set_akce_ident(get_akce_ident(az.hlavni_katastr.okres.kraj.rada_id))
        else:
            az.set_akce_ident(
                get_akce_ident(az.hlavni_katastr.okres.kraj.rada_id, True, az.id)
            )
        az.save()
        Historie(
            typ_zmeny=ZMENA_AZ,
            uzivatel=request.user,
            poznamka=f"{old_ident} -> {az.ident_cely}",
            vazba=az.historie,
        ).save()
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
            "title": _("arch_z.modalForm.zmenaSamostatneAkce.title.text"),
            "id_tag": "akce-change-form",
            "button": _("arch_z.modalForm.zmenaSamostatneAkce.submit.button"),
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
        if check_stav_changed(request, context["object"]):
            return JsonResponse(
                {"redirect": az.get_absolute_url()},
                status=403,
            )
        form = PripojitProjektForm(data=request.POST)
        if form.is_valid():
            projekt = form.cleaned_data["projekt"]
            az.akce.projekt = Projekt.objects.get(id=projekt)
            az.akce.typ = Akce.TYP_AKCE_PROJEKTOVA
            az.akce.save()
            old_ident = az.ident_cely
            az.set_akce_ident(get_project_event_ident(az.akce.projekt))
            az.save()
            Historie(
                typ_zmeny=ZMENA_AZ,
                uzivatel=request.user,
                poznamka=f"{old_ident} -> {az.ident_cely}",
                vazba=az.historie,
            ).save()
            logger.debug("arch_z.views.SamostatnaAkceChange.post.valid", extra={"az_ident_cely": str(az.ident_cely)})
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.debug("arch_z.views.SamostatnaAkceChange.post.not_valid", extra={"errors": form.errors, 
                                                                                    "form_non_field_errors": form.non_field_errors})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

        return redirect(az.get_absolute_url())


class ArchZAutocomplete(autocomplete.Select2QuerySetView):
    """
    Třida pohledu pro vrácení výsledku pro autocomplete arch záznamů.
    """
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
        return qs


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


def get_dj_form_detail(app, jednotka, jednotky=None, show=None, old_adb_post=None):
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
        and show["editovat"]
    )
    show_add_komponenta = not jednotka.negativni_jednotka and show["editovat"]
    show_add_pian = False if jednotka.pian else True
    show_approve_pian = (
        True
        if jednotka.pian and jednotka.pian.stav == PIAN_NEPOTVRZEN and show["editovat"]
        else False
    )
    if app == "akce":
        create_db_form = CreateDJForm(
            instance=jednotka,
            jednotky=jednotky,
            prefix=jednotka.ident_cely,
            not_readonly=show["editovat"],
        )
    else:
        create_db_form = CreateDJForm(
            instance=jednotka,
            typ_arch_z=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA,
            prefix=jednotka.ident_cely,
            not_readonly=show["editovat"],
        )
    dj_form_detail = {
        "ident_cely": jednotka.ident_cely,
        "pian_ident_cely": jednotka.pian.ident_cely if jednotka.pian else "",
        "form": create_db_form,
        "show_add_adb": show_adb_add,
        "show_add_komponenta": show_add_komponenta,
        "show_add_pian": (show_add_pian and show["editovat"]),
        "show_remove_pian": (not show_add_pian and show["editovat"] and jednotka.typ.id != TYP_DJ_KATASTR),
        "show_uprav_pian": jednotka.pian
        and jednotka.pian.stav == PIAN_NEPOTVRZEN
        and show["editovat"],
        "show_approve_pian": show_approve_pian,
        "show_pripojit_pian": True if jednotka.pian is None else False,
        "show_change_katastr": True if jednotka.typ.id == TYP_DJ_KATASTR else False,
    }
    if has_adb and app != "lokalita":
        logger.debug("arch_z.views.get_dj_form_detail", extra={"jednotka_ident_cely": jednotka.ident_cely})
        dj_form_detail["adb_form"] = CreateADBForm(
            old_adb_post,
            instance=jednotka.adb,
            prefix=jednotka.adb.ident_cely,
            readonly=not show["editovat"],
        )
        dj_form_detail["adb_ident_cely"] = jednotka.adb.ident_cely
        dj_form_detail["vyskovy_bod_formset"] = vyskovy_bod_formset(
            instance=jednotka.adb, prefix=jednotka.adb.ident_cely + "_vb"
        )
        dj_form_detail["vyskovy_bod_formset_helper"] = VyskovyBodFormSetHelper()
        dj_form_detail["show_remove_adb"] = True if show["editovat"] else False
    return dj_form_detail
