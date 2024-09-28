import logging


from adb.forms import CreateADBForm, create_vyskovy_bod_form
from adb.models import Adb, VyskovyBod
from arch_z.models import ArcheologickyZaznam, get_akce_ident
from core.constants import AZ_STAV_ARCHIVOVANY, DOKUMENTACNI_JEDNOTKA_RELATION_TYPE
from core.exceptions import MaximalIdentNumberError
from core.ident_cely import get_dj_ident, get_temp_akce_ident
from core.message_constants import (
    MAXIMUM_DJ_DOSAZENO,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN, ZAZNAM_SE_NEPOVEDLO_SMAZAT_NAVAZANE_ZAZNAMY,
)
from core.repository_connector import FedoraTransaction
from core.utils import (
    update_all_katastr_within_akce_or_lokalita,
    update_main_katastr_within_ku,
)
from dj.forms import ChangeKatastrForm, CreateDJForm
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, RestrictedError
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from heslar.hesla import HESLAR_DJ_TYP
from heslar.hesla_dynamicka import TYP_DJ_CAST, TYP_DJ_KATASTR, TYP_DJ_LOKALITA, TYP_DJ_SONDA_ID, TYP_DJ_CELEK
from heslar.models import Heslar, RuianKatastr
from komponenta.models import KomponentaVazby
from pian.models import Pian, vytvor_pian

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def detail(request, typ_vazby, ident_cely):
    """
    Funkce pohledu pro editaci dokumentační jednotky a ADB.
    """
    logger.debug("dj.views.detail.start")
    dj: DokumentacniJednotka = get_object_or_404(DokumentacniJednotka, ident_cely=ident_cely)
    fedora_transaction = dj.archeologicky_zaznam.create_transaction(request.user)
    pian_db: Pian = dj.pian
    if pian_db is not None:
        pian_db.active_transaction = fedora_transaction
    old_typ = dj.typ.id
    form = CreateDJForm(request.POST, instance=dj, prefix=ident_cely)
    if form.is_valid():
        logger.debug("dj.views.detail.form_is_valid", extra={"ident_cely": dj.ident_cely})
        dj: DokumentacniJednotka = form.save(commit=False)
        dj.active_transaction = fedora_transaction
        if dj.pian is None:
            logger.debug("dj.views.detail.empty_pian", {"ident_cely": dj.ident_cely})
            if pian_db is not None and not(old_typ == TYP_DJ_KATASTR and form.cleaned_data["typ"].id != TYP_DJ_KATASTR):
                logger.debug("dj.views.detail.added_pian_from_db", extra={"pian_db": pian_db,
                                                                          "ident_cely": dj.ident_cely})
                dj.pian = pian_db
            dj.save()
        elif old_typ == TYP_DJ_KATASTR and form.cleaned_data["typ"].id != TYP_DJ_KATASTR:
            logger.debug("dj.views.detail.disconnected_pian", extra={"ident_cely": dj.ident_cely})
            dj.pian = None
            dj.save()
        else:
            logger.debug("dj.views.detail.else_branch", extra={"ident_cely": dj.ident_cely})
            dj.save()
        if form.changed_data:
            logger.debug("dj.views.detail.changed", extra={"ident_cely": dj.ident_cely})
        update_all_katastr_within_akce_or_lokalita(dj, fedora_transaction)
        if dj.typ.id == TYP_DJ_CELEK:
            logger.debug("dj.views.detail.celek_akce", extra={"ident_cely": dj.ident_cely})
            typ = Heslar.objects.filter(Q(nazev_heslare=HESLAR_DJ_TYP) & Q(id=TYP_DJ_CAST)).first()
            dokumentacni_jednotka_query = DokumentacniJednotka.objects.filter(
                Q(archeologicky_zaznam=dj.archeologicky_zaznam)
                & ~Q(ident_cely=dj.ident_cely) & ~Q(typ=typ)
            )
            for dokumentacni_jednotka in dokumentacni_jednotka_query:
                dokumentacni_jednotka.typ = typ
                dokumentacni_jednotka.active_transaction = fedora_transaction
                dokumentacni_jednotka.save()
        elif dj.typ.id == TYP_DJ_SONDA_ID:
            logger.debug("dj.views.detail.sonda", extra={"ident_cely": dj.ident_cely})
            typ = Heslar.objects.filter(Q(nazev_heslare=HESLAR_DJ_TYP) & Q(id=TYP_DJ_SONDA_ID)).first()
            dokumentacni_jednotka_query = DokumentacniJednotka.objects.filter(
                Q(archeologicky_zaznam=dj.archeologicky_zaznam)
                & ~Q(ident_cely=dj.ident_cely) & ~Q(typ=typ)
            )
            for dokumentacni_jednotka in dokumentacni_jednotka_query:
                dokumentacni_jednotka.typ = typ
                dokumentacni_jednotka.active_transaction = fedora_transaction
                dokumentacni_jednotka.save()
        elif dj.typ.id == TYP_DJ_LOKALITA:
            logger.debug("dj.views.detail.lokalita", extra={"ident_cely": dj.ident_cely})
            dokumentacni_jednotka_query = DokumentacniJednotka.objects.filter(
                Q(archeologicky_zaznam=dj.archeologicky_zaznam)
                & Q(ident_cely=dj.ident_cely)
            )
            for dokumentacni_jednotka in dokumentacni_jednotka_query:
                dokumentacni_jednotka.typ = Heslar.objects.filter(
                    Q(nazev_heslare=HESLAR_DJ_TYP) & Q(id=TYP_DJ_LOKALITA)
                ).first()
                dokumentacni_jednotka.active_transaction = fedora_transaction
                dokumentacni_jednotka.save()
        elif dj.typ.id == TYP_DJ_KATASTR:
            logger.debug("dj.views.detail.katastr", extra={"ident_cely": dj.ident_cely})            
            if dj.archeologicky_zaznam.hlavni_katastr.pian:
                dj.pian = dj.archeologicky_zaznam.hlavni_katastr.pian
            else:
                dj.pian = vytvor_pian(dj.archeologicky_zaznam.hlavni_katastr, fedora_transaction)
            dj.save()            
        if dj.pian is not None and (pian_db is None or pian_db.pk != dj.pian.pk):
            logger.debug("dj.views.detail.update_pian_metadata",
                         extra={"pian_db": pian_db.ident_cely if pian_db else "None",
                                "instance_pian": dj.pian.ident_cely, "ident_cely": dj.ident_cely})
            dj.pian.active_transaction = fedora_transaction
            dj.pian.update_all_azs = False
            dj.pian.save()
        if pian_db is not None and (dj.pian is None or dj.pian.pk != pian_db.pk):
            logger.debug("dj.views.detail.changed_or_removed_pian", extra={"ident_cely": dj.ident_cely})
            pian_db.update_all_azs = False
            if dj.typ != Heslar.objects.get(id=TYP_DJ_KATASTR):
                pian_db.save()
    else:
        logger.warning("dj.views.detail.form_is_not_valid", extra={"errors": form.errors,
                                                                   "ident_cely": dj.ident_cely})
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

    if "adb_detail" in request.POST:
        ident_cely = request.POST.get("adb_detail")
        logger.debug("dj.views.detail.adb_detail", extra={"ident_cely": dj.ident_cely,
                                                          "adb_ident_cely": ident_cely})
        adb = get_object_or_404(Adb, ident_cely=ident_cely)
        form = CreateADBForm(
            request.POST,
            instance=adb,
            #prefix=ident_cely,
        )
        if form.is_valid():
            logger.debug("dj.views.detail.adb_detail.form_is_valid", extra={"ident_cely": dj.ident_cely,
                                                                            "adb_ident_cely": ident_cely})
            adb = form.save(commit=False)
            adb.active_transaction = fedora_transaction
            adb.save()
        else:
            logger.debug("dj.views.detail.adb_detail.form_is_not_valid",
                         extra={"errors": form.errors, "ident_cely": ident_cely, "adb_ident_cely": ident_cely})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
            request.session["_old_adb_post"] = request.POST
            request.session["adb_ident_cely"] = ident_cely

    if "adb_zapsat_vyskove_body" in request.POST:
        adb_ident_cely = request.POST.get("adb_zapsat_vyskove_body")
        logger.debug("dj.views.detail.adb_zapsat_vyskove_body", extra={"ident_cely": dj.ident_cely,
                                                                       "adb_ident_cely": adb_ident_cely})
        adb = get_object_or_404(Adb, ident_cely=adb_ident_cely)
        vyskovy_bod_formset = inlineformset_factory(
            Adb,
            VyskovyBod,
            form=create_vyskovy_bod_form(pian=pian_db),
            extra=3,
        )
        formset = vyskovy_bod_formset(
            request.POST, instance=adb, prefix=adb.ident_cely + "_vb"
        )
        if formset.is_valid():
            logger.debug("dj.views.detail.adb_zapsat_vyskove_body.form_set_is_valid",
                         extra={"ident_cely": dj.ident_cely, "adb_ident_cely": adb_ident_cely})
            instances = formset.save(commit=False)
            for i in range(0, len(instances)):
                vyskovy_bod = instances[i]
                vyskovy_bod_form = list(filter(lambda x: x.instance == vyskovy_bod, formset.forms))[0]
                vyskovy_bod: VyskovyBod
                vyskovy_bod.active_transaction = fedora_transaction
                if isinstance(vyskovy_bod, VyskovyBod):
                    logger.debug("dj.views.detail.adb_zapsat_vyskove_body.save",
                                 extra={"vyskovy_bod": vyskovy_bod.__dict__,
                                        "vyskovy_bod_form": vyskovy_bod_form.__dict__})
                    vyskovy_bod.set_geom(vyskovy_bod_form.cleaned_data.get("northing", 0),
                                         vyskovy_bod_form.cleaned_data.get("easting", 0),
                                         vyskovy_bod_form.cleaned_data.get("niveleta", 0))
                vyskovy_bod.save()
        if formset.is_valid():
            logger.debug("dj.views.detail.adb_zapsat_vyskove_body.form_set_is_valid",
                         extra={"ident_cely": dj.ident_cely, "adb_ident_cely": adb_ident_cely})
        else:
            logger.debug("dj.views.detail.adb_zapsat_vyskove_body.form_set_is_not_valid",
                         extra={"errors": formset.errors, "ident_cely": dj.ident_cely,
                                "adb_ident_cely": adb_ident_cely})
            messages.add_message(
                request,
                messages.ERROR,
                ZAZNAM_SE_NEPOVEDLO_EDITOVAT + " " + _("detail.vyskovy_bod.povinna_pole"),
            )

    response = dj.archeologicky_zaznam.get_redirect(dj.ident_cely)
    dj.close_active_transaction_when_finished = True
    dj.save()
    return response


@login_required
@require_http_methods(["POST"])
def zapsat(request, arch_z_ident_cely):
    """
    Funkce pohledu pro vytvoření dokumentační jednotky.
    """
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=arch_z_ident_cely)
    form = CreateDJForm(request.POST)
    if form.is_valid():
        logger.debug("dj.views.detail.zapsat.form_valid")
        vazba = KomponentaVazby(typ_vazby=DOKUMENTACNI_JEDNOTKA_RELATION_TYPE)
        vazba.save()  # TODO rewrite to signals

        dj = form.save(commit=False)
        try:
            ident_cely = get_dj_ident(az)
            dj.ident_cely = ident_cely
            redirect = az.get_redirect(dj.ident_cely)
        except MaximalIdentNumberError:
            messages.add_message(request, messages.ERROR, MAXIMUM_DJ_DOSAZENO)
            redirect = az.get_redirect()
        else:
            dj.komponenty = vazba
            dj.archeologicky_zaznam = az
            fedora_transaction = az.create_transaction(request.user, ZAZNAM_USPESNE_VYTVOREN,
                                                       ZAZNAM_SE_NEPOVEDLO_VYTVORIT)
            dj.active_transaction = fedora_transaction
            dj.close_active_transaction_when_finished = True
            resp = dj.save()
            logger.debug("dj.views.detail.zapsat.dj_resp", {"resp": resp})
    else:
        logger.debug("dj.views.detail.zapsat.form_not_valid", {"errors": form.errors})
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)
        redirect = az.get_redirect()
    return redirect


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    """
    Funkce pohledu pro smazání dokumentační jednotky.
    """
    dj: DokumentacniJednotka \
        = get_object_or_404(DokumentacniJednotka, ident_cely=ident_cely)
    if request.method == "POST":
        try:
            dj.deleted_by_user = request.user
            fedora_transaction = dj.archeologicky_zaznam.create_transaction(request.user, ZAZNAM_USPESNE_SMAZAN,
                                                                            ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            dj.active_transaction = fedora_transaction
            resp = dj.delete()
            update_all_katastr_within_akce_or_lokalita(dj, fedora_transaction)
            if resp:
                fedora_transaction.mark_transaction_as_closed()
                logger.debug("dj.views.detail.smazat.deleted", extra={"resp": resp})
                return JsonResponse({"redirect": dj.archeologicky_zaznam.get_absolute_url()})
            else:
                fedora_transaction.rollback_transaction()
                logger.warning("dj.views.detail.smazat.not_deleted", extra={"ident_cely": ident_cely})
                return JsonResponse(
                    {"redirect": dj.archeologicky_zaznam.get_absolute_url()},
                    status=403,
                )
        except RestrictedError as err:
            logger.warning("dj.views.detail.smazat.not_deleted", extra={"ident_cely": ident_cely, "err": err})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT_NAVAZANE_ZAZNAMY)
            return JsonResponse(
                {"redirect": dj.archeologicky_zaznam.get_absolute_url()},
                status=403,
            )
    else:
        context = {
            "object": dj,
            "title": _("dj.views.smazat.title.text"),
            "id_tag": "smazat-dj-form",
            "button": _("dj.views.smazat.submitButton.text"),
        }
        return render(request, "core/transakce_modal.html", context)

class ChangeKatastrView(LoginRequiredMixin, TemplateView):
    """
    Třída pohledu pro editaci katastru dokumentační jednotky.
    """
    template_name = "core/transakce_modal.html"
    id_tag = "zmenit-katastr-form"

    def get_zaznam(self) -> DokumentacniJednotka:
        ident_cely = self.kwargs.get("ident_cely")
        return get_object_or_404(
            DokumentacniJednotka,
            ident_cely=ident_cely,
        )

    def get_context_data(self, **kwargs):
        zaznam = self.get_zaznam()
        form = ChangeKatastrForm(initial={"katastr":zaznam.archeologicky_zaznam.hlavni_katastr})
        context = {
            "object": zaznam,
            "form": form,
            "title": _("dj.views.ChangeKatastrView.title.text"),
            "id_tag": self.id_tag,
            "button": _("dj.views.ChangeKatastrView.submitButton.text"),
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        zaznam: DokumentacniJednotka = self.get_zaznam()
        form = ChangeKatastrForm(data=request.POST)
        if form.is_valid():
            az = zaznam.archeologicky_zaznam
            az: ArcheologickyZaznam
            fedora_transaction = az.create_transaction(request.user)
            az.hlavni_katastr = form.cleaned_data["katastr"]
            az.save()
            zaznam.active_transaction = fedora_transaction
            zaznam.close_active_transaction_when_finished = True
            if form.cleaned_data["katastr"].pian is not None:
                zaznam.pian = form.cleaned_data["katastr"].pian
                zaznam.save()
            else: 
                zaznam.pian = vytvor_pian(form.cleaned_data["katastr"], fedora_transaction)
                zaznam.save()
            zaznam.refresh_from_db()
        else:
            logger.debug("dj.views.ChangeKatastrView.post.form_not_valid", {"errors": form.errors})
        return JsonResponse({"redirect": zaznam.get_absolute_url()})
