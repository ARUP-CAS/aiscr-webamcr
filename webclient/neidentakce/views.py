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
    """Třída pohledu pro editaci neident akce pomocí modalu."""

    model = NeidentAkce
    template_name = "core/transakce_modal.html"
    id_tag = "edit-neident-form"
    allowed_states = []
    success_message = _("neidentAkce.views.neidentAkceEditView.success")
    form_class = NeidentAkceForm
    slug_field = "dokument_cast__ident_cely"
    prefix = "neident_modal"

    def get_form_kwargs(self):
        """
        Vrací form kwargs.

        :return: Vrací proměnná ``kwargs``.
        """
        kwargs = super().get_form_kwargs()
        kwargs["prefix"] = self.prefix
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
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
        """
        Vrací success url.

        :return: Vrací výsledek volání ``reverse()``.
        """
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
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``post()``.
        :param args: Parametr ``args`` se předává do volání ``post()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``post()``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        super().post(request, *args, **kwargs)
        return JsonResponse({"redirect": self.get_success_url()})

    def form_valid(self, form):
        """
        Zpracuje platný formulář editace neidentifikované akce a zobrazí zprávu o úspěchu.

        :param form: Validovaný formulář editace.

            :return: Vrací výsledek volání ``form_valid()``.
        """
        messages.add_message(self.request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Zpracuje neplatný formulář editace neidentifikované akce a zobrazí chybovou zprávu.

        :param form: Nevalidní formulář s chybami.

            :return: Vrací výsledek volání ``form_invalid()``.
        """
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        logger.debug("neidentakce.views.NeidentAkceEditView.form_invalid", extra={"error": form.errors})
        return super().form_invalid(form)
