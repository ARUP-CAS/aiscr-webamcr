import logging

from arch_z.models import ArcheologickyZaznam
from core.constants import (
    ARCHIVACE_DOK,
    D_STAV_ARCHIVOVANY,
    D_STAV_ODESLANY,
    D_STAV_ZAPSANY,
    DOKUMENT_CAST_RELATION_TYPE,
    IDENTIFIKATOR_DOCASNY_PREFIX,
    ODESLANI_DOK,
    ZAPSANI_DOK,
)
from core.exceptions import UnexpectedDataRelations
from core.forms import VratitForm
from core.ident_cely import (
    get_cast_dokumentu_ident,
    get_dokument_ident,
    get_dokument_rada,
)
from core.message_constants import (
    DOKUMENT_NELZE_ARCHIVOVAT,
    DOKUMENT_USPESNE_ARCHIVOVAN,
    DOKUMENT_USPESNE_ODESLAN,
    DOKUMENT_USPESNE_VRACEN,
    VYBERTE_PROSIM_POLOHU,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from core.utils import get_cadastre_from_point
from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from dokument.forms import (
    CreateDokumentForm,
    CreateModelDokumentForm,
    CreateModelExtraDataForm,
    EditDokumentExtraDataForm,
    EditDokumentForm,
)
from dokument.models import Dokument, DokumentCast, DokumentExtraData
from heslar.hesla import (
    DOKUMENT_RADA_DATA_3D,
    HESLAR_AREAL,
    HESLAR_AREAL_KAT,
    HESLAR_DOKUMENT_TYP,
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
    MATERIAL_DOKUMENTU_DIGITALNI_SOUBOR,
    PRISTUPNOST_BADATEL_ID,
)
from heslar.models import Heslar, HeslarHierarchie
from heslar.views import heslar_12
from komponenta.forms import CreateKomponentaForm
from komponenta.models import Komponenta, KomponentaVazby

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {}
    dokument = get_object_or_404(
        Dokument.objects.select_related(
            "soubory",
            "organizace",
            "material_originalu",
            "typ_dokumentu",
            "rada",
            "pristupnost",
        ),
        ident_cely=ident_cely,
    )

    context["dokument"] = dokument
    context["history_dates"] = get_history_dates(dokument.historie)
    context["show"] = get_detail_template_shows(dokument)

    if dokument.soubory:
        context["soubory"] = dokument.soubory.soubory.all()
    else:
        context["soubory"] = None
    return render(request, "dokument/detail.html", context)


@login_required
@require_http_methods(["GET"])
def detail_model_3D(request, ident_cely):
    context = {}
    dokument = get_object_or_404(
        Dokument.objects.select_related(
            "soubory",
            "organizace",
            "extra_data__format",
            "typ_dokumentu",
        ),
        ident_cely=ident_cely,
    )
    casti = dokument.casti.all()
    if casti.count() != 1:
        logger.error("Model ma mit jednu cast dokumentu: " + str(casti.count()))
        raise UnexpectedDataRelations()
    komponenty = casti[0].komponenty.komponenty.all()
    if komponenty.count() != 1:
        logger.error("Model ma mit jednu komponentu: " + str(komponenty.count()))
        raise UnexpectedDataRelations()
    context["dokument"] = dokument
    context["komponenta"] = komponenty[0]
    context["history_dates"] = get_history_dates(dokument.historie)
    context["show"] = get_detail_template_shows(dokument)
    logger.debug(context)
    if dokument.soubory:
        context["soubory"] = dokument.soubory.soubory.all()
    else:
        context["soubory"] = None
    return render(request, "dokument/detail_model_3D.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    dokument = get_object_or_404(Dokument, ident_cely=ident_cely)
    if not dokument.has_extra_data():
        extra_data = DokumentExtraData(dokument=dokument)
        extra_data.save()
    else:
        extra_data = dokument.extra_data
    if request.method == "POST":
        form_d = EditDokumentForm(request.POST, instance=dokument)
        form_extra = EditDokumentExtraDataForm(request.POST, instance=extra_data)
        if form_d.is_valid() and form_extra.is_valid():
            form_d.save()
            form_extra.save()
            if form_d.changed_data or form_extra.changed_data:
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return redirect("dokument:detail", ident_cely=dokument.ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form_d.errors)
            logger.debug(form_extra.errors)
    else:
        form_d = EditDokumentForm(instance=dokument)
        form_extra = EditDokumentExtraDataForm(instance=extra_data)

    return render(
        request,
        "dokument/create.html",
        {
            "formDokument": form_d,
            "formExtraData": form_extra,
            "dokument": dokument,
            "hierarchie": get_hierarchie_dokument_typ(),
            "title": _("Editace dokumentu"),
            "header": _("Editace dokumentu"),
            "button": _("Edituj dokument"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def zapsat(request, arch_z_ident_cely):
    zaznam = get_object_or_404(ArcheologickyZaznam, ident_cely=arch_z_ident_cely)
    if request.method == "POST":
        form_d = CreateDokumentForm(request.POST)
        form_extra = EditDokumentExtraDataForm(request.POST)

        if form_d.is_valid() and form_extra.is_valid():
            logger.debug("Form is valid")
            dokument = form_d.save(commit=False)
            identifikator = form_d.cleaned_data["identifikator"]
            rada = get_dokument_rada(
                dokument.typ_dokumentu, dokument.material_originalu
            )
            dokument.ident_cely = get_dokument_ident(
                temporary=True, rada=rada.zkratka, region=identifikator
            )
            dokument.rada = rada
            dokument.stav = D_STAV_ZAPSANY
            dokument.save()
            dokument.set_zapsany(request.user)

            # Vytvorit defaultni cast dokumentu
            DokumentCast(
                dokument=dokument,
                ident_cely=get_cast_dokumentu_ident(dokument),
                archeologicky_zaznam=zaznam,
            ).save()

            form_d.save_m2m()
            extra_data = form_extra.save(commit=False)
            extra_data.dokument = dokument
            extra_data.save()

            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
            return redirect("dokument:detail", ident_cely=dokument.ident_cely)

        else:
            logger.warning("Form is not valid")
            logger.debug(form_d.errors)
            logger.debug(form_extra.errors)

    else:
        form_d = CreateDokumentForm()
        form_extra = EditDokumentExtraDataForm()

    return render(
        request,
        "dokument/create.html",
        {
            "formDokument": form_d,
            "formExtraData": form_extra,
            "hierarchie": get_hierarchie_dokument_typ(),
            "title": _("Nový dokument"),
            "header": _("Nový dokument"),
            "button": _("Vytvořit dokument"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def create_model_3D(request):
    obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
    areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
    if request.method == "POST":
        form_d = CreateModelDokumentForm(request.POST)
        form_extra = CreateModelExtraDataForm(request.POST)
        form_komponenta = CreateKomponentaForm(
            obdobi_choices, areal_choices, request.POST
        )

        if form_d.is_valid() and form_extra.is_valid() and form_komponenta.is_valid():
            logger.debug("Forms are valid")
            dokument = form_d.save(commit=False)
            dokument.rada = Heslar.objects.get(id=DOKUMENT_RADA_DATA_3D)
            dokument.material_originalu = Heslar.objects.get(
                id=MATERIAL_DOKUMENTU_DIGITALNI_SOUBOR
            )
            point = form_extra.cleaned_data["geom"]
            region = get_cadastre_from_point(point).okres.kraj.rada_id
            dokument.ident_cely = get_dokument_ident(
                temporary=True, rada="3D", region=region
            )
            dokument.pristupnost = Heslar.objects.get(id=PRISTUPNOST_BADATEL_ID)
            dokument.stav = D_STAV_ZAPSANY
            dokument.save()
            dokument.set_zapsany(request.user)
            # Vytvorit defaultni cast dokumentu
            kv = KomponentaVazby(typ_vazby=DOKUMENT_CAST_RELATION_TYPE)
            kv.save()
            dc = DokumentCast(
                dokument=dokument,
                ident_cely=get_cast_dokumentu_ident(dokument),
                komponenty=kv,
            )
            dc.save()
            form_d.save_m2m()
            extra_data = form_extra.save(commit=False)
            extra_data.dokument = dokument
            extra_data.save()

            komponenta = form_komponenta.save(commit=False)
            komponenta.komponenta_vazby = dc.komponenty
            komponenta.ident_cely = dokument.ident_cely + "-K001"
            komponenta.save()

            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
            return redirect("dokument:detail-model-3D", ident_cely=dokument.ident_cely)

        else:
            logger.warning("Form is not valid")
            logger.debug(form_d.errors)
            logger.debug(form_extra.errors)
            logger.debug(form_komponenta.errors)
            if "geom" in form_extra.errors:
                messages.add_message(request, messages.ERROR, VYBERTE_PROSIM_POLOHU)
    else:
        form_d = CreateModelDokumentForm()
        form_extra = CreateModelExtraDataForm()
        form_komponenta = CreateKomponentaForm(obdobi_choices, areal_choices)
    return render(
        request,
        "dokument/create_model_3D.html",
        {
            "formDokument": form_d,
            "formExtraData": form_extra,
            "formKomponenta": form_komponenta,
            "title": _("Nový model 3D"),
            "header": _("Nový model 3D"),
            "button": _("Vytvořit model"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def odeslat(request, ident_cely):
    d = get_object_or_404(Dokument, ident_cely=ident_cely)
    if d.stav != D_STAV_ZAPSANY:
        raise PermissionDenied()
    if request.method == "POST":
        d.set_odeslany(request.user)
        messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_ODESLAN)
        if "3D" in ident_cely:
            return redirect("dokument:detail-model-3D", ident_cely=ident_cely)
        else:
            return redirect("dokument:detail", ident_cely=ident_cely)
    else:
        # warnings = d.check_pred_odeslanim()
        # logger.debug(warnings)
        context = {"object": d}
        # if warnings:
        #    context["warnings"] = warnings
        #    messages.add_message(request, messages.ERROR, DOKUMENT_NELZE_ODESLAT)
        # else:
        #    pass
    context["title"] = _("Odeslání dokumentu")
    context["header"] = _("Odeslání dokumentu")
    context["button"] = _("Odeslat dokument")
    return render(request, "core/transakce.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def archivovat(request, ident_cely):
    d = get_object_or_404(Dokument, ident_cely=ident_cely)
    if d.stav != D_STAV_ODESLANY:
        raise PermissionDenied()
    if request.method == "POST":
        d.set_archivovany(request.user)
        # Nastav identifikator na permanentny
        if ident_cely.startswith(IDENTIFIKATOR_DOCASNY_PREFIX):
            rada = get_dokument_rada(d.typ_dokumentu, d.material_originalu)
            d.ident_cely = get_dokument_ident(
                temporary=False, rada=rada.zkratka, region=ident_cely[2:3]
            )
            d.save()
            logger.debug(
                "Dokumentu "
                + ident_cely
                + " byl prirazen permanentni identifikator "
                + d.ident_cely
            )
            # Prejmenuj i dokumentacni jednotky
            counter = 1
            for cast in d.casti.all().order_by("ident_cely"):
                if cast.ident_cely.startswith(IDENTIFIKATOR_DOCASNY_PREFIX):
                    old_ident = cast.ident_cely
                    cast.ident_cely = d.ident_cely + "-D" + str(counter).zfill(2)
                    cast.save()
                    logger.debug(
                        "Casti dokumentu "
                        + old_ident
                        + " byl zmenen identifikator na "
                        + cast.ident_cely
                    )
                    counter += 1

        messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_ARCHIVOVAN)
        return redirect("dokument:detail", ident_cely=d.ident_cely)
    else:
        warnings = d.check_pred_archivaci()
        logger.debug(warnings)
        context = {"object": d}
        if warnings:
            context["warnings"] = warnings
            messages.add_message(request, messages.ERROR, DOKUMENT_NELZE_ARCHIVOVAT)
        else:
            pass
    context["title"] = _("Archivace dokumentu")
    context["header"] = _("Archivace dokumentu")
    context["button"] = _("Archivovat dokument")
    return render(request, "core/transakce.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    d = get_object_or_404(Dokument, ident_cely=ident_cely)
    if d.stav != D_STAV_ODESLANY and d.stav != D_STAV_ARCHIVOVANY:
        raise PermissionDenied()
    if request.method == "POST":
        form = VratitForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            d.set_vraceny(request.user, d.stav - 1, duvod)
            messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_VRACEN)
            if "3D" in ident_cely:
                return redirect("dokument:detail-model-3D", ident_cely=ident_cely)
            else:
                return redirect("dokument:detail", ident_cely=ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = VratitForm()
    return render(request, "core/vratit.html", {"form": form, "objekt": d})


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    d = get_object_or_404(Dokument, ident_cely=ident_cely)
    if request.method == "POST":

        historie = d.historie
        soubory = d.soubory
        resp1 = d.delete()
        resp2 = historie.delete()
        resp3 = soubory.delete()

        # Kdyz mazu dokument ktery reprezentuje 3D model, mazu i komponenty
        if "3D" in d.ident_cely:
            for k in Komponenta.objects.filter(ident_cely__startswith=d.ident_cely):
                logger.debug("Mazu komponentu modelu 3D: " + str(k.ident_cely))
                k.delete()

        if resp1:
            logger.debug("Dokument byl smazan: " + str(resp1 + resp2 + resp3))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
        else:
            logger.warning("Dokument nebyl smazan: " + str(ident_cely))
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)

        return redirect("core:home")
    else:
        return render(request, "core/smazat.html", {"objekt": d})


class DokumentAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Dokument.objects.none()
        qs = Dokument.objects.all()
        if self.q:
            qs = qs.filter(ident_cely__icontains=self.q)
        return qs


def get_hierarchie_dokument_typ():
    hierarchie_qs = HeslarHierarchie.objects.filter(
        heslo_podrazene__nazev_heslare__id=HESLAR_DOKUMENT_TYP
    ).values_list("heslo_podrazene", "heslo_nadrazene")
    hierarchie = {}
    for v in hierarchie_qs:
        if v[0] in hierarchie:
            hierarchie[v[0]].append(v[1])
        else:
            hierarchie[v[0]] = [v[1]]
    return hierarchie


def get_history_dates(historie_vazby):
    historie = {
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_DOK),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_DOK),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_DOK),
    }
    return historie


def get_detail_template_shows(dokument):
    show_vratit = dokument.stav > D_STAV_ZAPSANY
    show_odeslat = dokument.stav == D_STAV_ZAPSANY
    show_archivovat = dokument.stav == D_STAV_ODESLANY
    show = {
        "vratit_link": show_vratit,
        "odeslat_link": show_odeslat,
        "archivovat_link": show_archivovat,
    }
    return show
