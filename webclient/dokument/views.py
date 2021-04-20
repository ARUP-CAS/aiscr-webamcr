import logging

from arch_z.models import ArcheologickyZaznam
from core.constants import D_STAV_ZAPSANY
from core.ident_cely import (
    get_cast_dokumentu_ident,
    get_dokument_ident,
    get_dokument_rada,
)
from core.message_constants import ZAZNAM_USPECNE_VYTVOREN, ZAZNAM_USPESNE_EDITOVAN
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from dokument.forms import CreateDokumentExtraDataForm, CreateDokumentForm
from dokument.models import Dokument, DokumentCast
from heslar.hesla import HESLAR_DOKUMENT_TYP
from heslar.models import HeslarHierarchie

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {}
    dokument = Dokument.objects.select_related(
        "soubory",
        "organizace",
        "material_originalu",
        "typ_dokumentu",
        "rada",
        "pristupnost",
    ).get(ident_cely=ident_cely)

    context["dokument"] = dokument
    if dokument.soubory:
        context["soubory"] = dokument.soubory.soubory.all()
    else:
        context["soubory"] = None
    return render(request, "dokument/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    dokument = Dokument.objects.get(ident_cely=ident_cely)
    if request.method == "POST":
        form_d = CreateDokumentForm(request.POST, instance=dokument)
        form_extra = CreateDokumentExtraDataForm(
            request.POST, instance=dokument.extra_data
        )
        if form_d.is_valid() and form_extra.is_valid():
            form_d.save()
            form_extra.save()
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return redirect("dokument:detail", ident_cely=dokument.ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form_d.errors)
            logger.debug(form_extra.errors)
    else:
        form_d = CreateDokumentForm(instance=dokument)
        form_extra = CreateDokumentExtraDataForm(instance=dokument)

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
    zaznam = ArcheologickyZaznam.objects.get(ident_cely=arch_z_ident_cely)
    if request.method == "POST":
        form_d = CreateDokumentForm(request.POST)
        form_extra = CreateDokumentExtraDataForm(request.POST)

        if form_d.is_valid() and form_extra.is_valid():
            logger.debug("Form is valid")
            dokument = form_d.save(commit=False)
            rada = get_dokument_rada(
                dokument.typ_dokumentu, dokument.material_originalu
            )
            # todo region neni vzdy C
            dokument.ident_cely = get_dokument_ident(
                temporary=True, rada=rada, region="C"
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

            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPECNE_VYTVOREN)
            return redirect("dokument:detail", ident_cely=dokument.ident_cely)

        else:
            logger.warning("Form is not valid")
            logger.debug(form_d.errors)
            logger.debug(form_extra.errors)

    else:
        form_d = CreateDokumentForm()
        form_extra = CreateDokumentExtraDataForm()

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
