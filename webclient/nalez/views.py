import logging

from core.message_constants import ZAZNAM_SE_NEPOVEDLO_EDITOVAT, ZAZNAM_USPESNE_EDITOVAN
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from heslar.hesla import (
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_DRUH_KAT,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_OBJEKT_SPECIFIKACE_KAT,
)
from heslar.views import heslar_12
from komponenta.models import Komponenta
from nalez.forms import create_nalez_objekt_form
from nalez.models import NalezObjekt

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def edit(request, komp_ident_cely):
    komponenta = Komponenta.objects.get(ident_cely=komp_ident_cely)
    druh_objekt_choices = heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT)
    specifikace_objekt_choices = heslar_12(
        HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT
    )
    NalezObjektFormset = inlineformset_factory(
        Komponenta,
        NalezObjekt,
        form=create_nalez_objekt_form(druh_objekt_choices, specifikace_objekt_choices),
        extra=1,
    )
    formset = NalezObjektFormset(request.POST, instance=komponenta)
    if formset.is_valid():
        logger.debug("Form is valid")
        formset.save()
        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
    else:
        logger.warning("Form is not valid")
        logger.debug(formset.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

    return redirect(request.META.get("HTTP_REFERER"))
