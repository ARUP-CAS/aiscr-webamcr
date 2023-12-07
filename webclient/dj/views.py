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
from heslar.hesla_dynamicka import TYP_DJ_CAST, TYP_DJ_KATASTR, TYP_DJ_LOKALITA, TYP_DJ_SONDA_ID
from heslar.models import Heslar
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
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=ident_cely)
    pian_db = dj.pian
    old_typ = dj.typ.id
    form = CreateDJForm(request.POST, instance=dj, prefix=ident_cely)
    if form.is_valid():
        logger.debug("dj.views.detail.form_is_valid")
        dj = form.save()
        if dj.pian is None:
            logger.debug("dj.views.detail.empty_pian")
            if pian_db is not None and not(old_typ == TYP_DJ_KATASTR and form.cleaned_data["typ"].id != TYP_DJ_KATASTR):
                logger.debug("dj.views.detail.added_pian_from_db", extra={"pian_db": pian_db})
                dj.pian = pian_db
                dj.save()
        elif old_typ == TYP_DJ_KATASTR and form.cleaned_data["typ"].id != TYP_DJ_KATASTR:
            logger.debug("dj.views.detail.disconnected_pian")
            dj.pian = None
            dj.save()
        if form.changed_data:
            logger.debug("dj.views.detail.changed")
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        if dj.typ.heslo == "Celek akce":
            logger.debug("dj.views.detail.celek_akce")
            typ = Heslar.objects.filter(Q(nazev_heslare=HESLAR_DJ_TYP) & Q(id=TYP_DJ_CAST)).first()
            dokumentacni_jednotka_query = DokumentacniJednotka.objects.filter(
                Q(archeologicky_zaznam=dj.archeologicky_zaznam)
                & ~Q(ident_cely=dj.ident_cely) & ~Q(typ=typ)
            )
            for dokumentacni_jednotka in dokumentacni_jednotka_query:
                dokumentacni_jednotka.typ = typ
                dokumentacni_jednotka.save()
            update_all_katastr_within_akce_or_lokalita(dj.ident_cely)
        elif dj.typ.heslo == "Sonda":
            logger.debug("dj.views.detail.sonda")
            typ = Heslar.objects.filter(Q(nazev_heslare=HESLAR_DJ_TYP) & Q(id=TYP_DJ_SONDA_ID)).first()
            dokumentacni_jednotka_query = DokumentacniJednotka.objects.filter(
                Q(archeologicky_zaznam=dj.archeologicky_zaznam)
                & ~Q(ident_cely=dj.ident_cely) & ~Q(typ=typ)
            )
            for dokumentacni_jednotka in dokumentacni_jednotka_query:
                dokumentacni_jednotka.typ = typ
                dokumentacni_jednotka.save()
            update_all_katastr_within_akce_or_lokalita(dj.ident_cely)
        elif dj.typ.heslo == "Lokalita":
            logger.debug("dj.views.detail.lokalita")
            dokumentacni_jednotka_query = DokumentacniJednotka.objects.filter(
                Q(archeologicky_zaznam=dj.archeologicky_zaznam)
                & Q(ident_cely=dj.ident_cely)
            )
            for dokumentacni_jednotka in dokumentacni_jednotka_query:
                dokumentacni_jednotka.typ = Heslar.objects.filter(
                    Q(nazev_heslare=HESLAR_DJ_TYP) & Q(id=TYP_DJ_LOKALITA)
                ).first()
                dokumentacni_jednotka.save()
            update_all_katastr_within_akce_or_lokalita(dj.ident_cely)
        elif dj.typ == Heslar.objects.get(id=TYP_DJ_KATASTR):
            new_ku = form.cleaned_data["ku_change"]
            if dj.archeologicky_zaznam.hlavni_katastr.pian:
                dj.pian = dj.archeologicky_zaznam.hlavni_katastr.pian
            else:
                dj.pian = vytvor_pian(dj.archeologicky_zaznam.hlavni_katastr)
            dj.save()
            if len(new_ku) > 3:
                update_main_katastr_within_ku(dj.ident_cely, new_ku)
        if dj.pian is not None and (pian_db is None or pian_db.pk != dj.pian.pk):
            dj.pian.save_metadata()
        if pian_db is not None and (dj.pian is None or dj.pian.pk != pian_db.pk):
            pian_db.save_metadata()

    else:
        logger.warning("dj.views.detail.form_is_not_valid", extra={"errors": form.errors})
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

    if "adb_detail" in request.POST:
        logger.debug("dj.views.detail.adb_detail")
        ident_cely = request.POST.get("adb_detail")
        adb = get_object_or_404(Adb, ident_cely=ident_cely)
        form = CreateADBForm(
            request.POST,
            instance=adb,
            #prefix=ident_cely,
        )
        if form.is_valid():
            logger.debug("dj.views.detail.adb_detail.form_is_valid")
            form.save()
            if form.changed_data:
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.debug("dj.views.detail.adb_detail.form_is_not_valid",
                         extra={"errors": form.errors, "ident_cely": ident_cely})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
            request.session["_old_adb_post"] = request.POST
            request.session["adb_ident_cely"] = ident_cely

    if "adb_zapsat_vyskove_body" in request.POST:
        logger.debug("dj.views.detail.adb_zapsat_vyskove_body")
        adb_ident_cely = request.POST.get("adb_zapsat_vyskove_body")
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
            logger.debug("dj.views.detail.adb_zapsat_vyskove_body.form_set_is_valid")
            instances = formset.save(commit=False)
            for i in range(0, len(instances)):
                vyskovy_bod = instances[i]
                vyskovy_bod_form = list(filter(lambda x: x.instance == vyskovy_bod, formset.forms))[0]
                vyskovy_bod: VyskovyBod
                if isinstance(vyskovy_bod, VyskovyBod):
                    logger.debug("dj.views.detail.adb_zapsat_vyskove_body.save",
                                 extra={"vyskovy_bod": vyskovy_bod.__dict__,
                                        "vyskovy_bod_form": vyskovy_bod_form.__dict__})
                    vyskovy_bod.set_geom(vyskovy_bod_form.cleaned_data.get("northing", 0),
                                         vyskovy_bod_form.cleaned_data.get("easting", 0),
                                         vyskovy_bod_form.cleaned_data.get("niveleta", 0))
                vyskovy_bod.save()
        if formset.is_valid():
            logger.debug("dj.views.detail.adb_zapsat_vyskove_body.form_set_is_valid")
            if (
                formset.has_changed()
            ):  # TODO tady to hazi porad ze se zmenila kvuli specifikaci a druhu
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.debug("dj.views.detail.adb_zapsat_vyskove_body.form_set_is_not_valid",
                         extra={"errors": formset.errors})
            messages.add_message(
                request,
                messages.ERROR,
                ZAZNAM_SE_NEPOVEDLO_EDITOVAT + _("detail.vyskovy_bod.povinna_pole"),
            )

    response = dj.archeologicky_zaznam.get_redirect(dj.ident_cely)
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
            resp = dj.save()
            logger.debug("dj.views.detail.zapsat.dj_resp", {"resp": resp})
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
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
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=ident_cely)
    if request.method == "POST":
        try:
            dj.deleted_by_user = request.user
            resp = dj.delete()
            update_all_katastr_within_akce_or_lokalita(dj.ident_cely)
            if resp:
                logger.debug("dj.views.detail.smazat.deleted", {"resp": resp})
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
                return JsonResponse({"redirect": dj.archeologicky_zaznam.get_absolute_url()})
            else:
                logger.warning("dj.views.detail.smazat.not_deleted", {"ident_cely": ident_cely})
                messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
                return JsonResponse(
                    {"redirect": dj.archeologicky_zaznam.get_absolute_url()},
                    status=403,
                )
        except RestrictedError as err:
            logger.warning("dj.views.detail.smazat.not_deleted", {"ident_cely": ident_cely, "err": err})
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

    def get_zaznam(self):
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
        zaznam = self.get_zaznam()
        form = ChangeKatastrForm(data=request.POST)
        if form.is_valid():
            az = zaznam.archeologicky_zaznam
            old_katastr = az.hlavni_katastr
            az.hlavni_katastr = form.cleaned_data["katastr"]
            az.save()
            if form.cleaned_data["katastr"].pian is not None:
                zaznam.pian = form.cleaned_data["katastr"].pian
                zaznam.save()
            else: 
                zaznam.pian = vytvor_pian(form.cleaned_data["katastr"])
                zaznam.save()
            if old_katastr.okres.kraj.rada_id != form.cleaned_data["katastr"].okres.kraj.rada_id:
                if az.stav == AZ_STAV_ARCHIVOVANY:
                    az.set_akce_ident(get_akce_ident(form.cleaned_data["katastr"].okres.kraj.rada_id))
                else:
                    az.set_akce_ident(
                        get_temp_akce_ident(form.cleaned_data["katastr"].okres.kraj.rada_id)
                    )
            zaznam.refresh_from_db()
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.debug("dj.views.ChangeKatastrView.post.form_not_valid", {"errors": form.errors})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        return JsonResponse({"redirect": zaznam.get_absolute_url()})
