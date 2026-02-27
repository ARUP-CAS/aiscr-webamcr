import logging

from core.message_constants import ZAZNAM_SE_NEPOVEDLO_EDITOVAT, ZAZNAM_USPESNE_EDITOVAN
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic.edit import UpdateView

from .forms import NeidentAkceForm
from .models import NeidentAkce

logger = logging.getLogger(__name__)


class NeidentAkceEditView(LoginRequiredMixin, UpdateView):
    """
    Třída pohledu pro editaci neident akce pomocí modalu.
    """

    model = NeidentAkce
    template_name = "core/transakce_modal.html"
    id_tag = "edit-neident-form"
    allowed_states = []
    success_message = _("neidentAkce.views.neidentAkceEditView.success")
    form_class = NeidentAkceForm
    slug_field = "dokument_cast__ident_cely"
    prefix = "neident_modal"

    def get_form_kwargs(self):
        """Vrací form kwargs.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        kwargs = super().get_form_kwargs()
        kwargs["prefix"] = self.prefix
        return kwargs

    def get_context_data(self, **kwargs):
        """Vrací context data.

        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        context = super().get_context_data(**kwargs)
        zaznam = self.object
        context = {
            "object": zaznam,
            "title": _("neidentAkce.views.neidentAkceEditView.title.text"),
            "id_tag": self.id_tag,
            "button": _("neidentAkce.views.neidentAkceEditView.submitButton"),
            "form": self.get_form(),
        }
        return context

    def get_success_url(self):
        """Vrací success url.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        context = self.get_context_data()
        dc = context["object"].dokument_cast
        return reverse(
            "dokument:detail-cast",
            kwargs={
                "ident_cely": dc.dokument.ident_cely,
                "cast_ident_cely": dc.ident_cely,
            },
        )

    def post(self, request, *args, **kwargs):
        """Obsluhuje HTTP metodu POST.

        :param request: Django HTTP požadavek použitý při zpracování.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Vrací výsledek provedené operace."""
        super().post(request, *args, **kwargs)
        return JsonResponse({"redirect": self.get_success_url()})

    def form_valid(self, form):
        """Provádí operaci form valid.

        :param form: Vstupní hodnota ``form`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        messages.add_message(self.request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        return super().form_valid(form)

    def form_invalid(self, form):
        """Provádí operaci form invalid.

        :param form: Vstupní hodnota ``form`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        logger.debug("neidentakce.views.NeidentAkceEditView.form_invalid", extra={"error": form.errors})
        return super().form_invalid(form)
