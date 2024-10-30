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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zaznam = self.object
        context = {
            "object": zaznam,
            "title": _("neidentAkce.views.neidentAkceEditView.title.text"),
            "id_tag": self.id_tag,
            "button": _("neidentAkce.views.neidentAkceEditView.submitButton"),
        }
        context["form"] = NeidentAkceForm(
            instance=self.object,
        )
        return context

    def get_success_url(self):
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
        super().post(request, *args, **kwargs)
        return JsonResponse({"redirect": self.get_success_url()})

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        logger.debug("neidentakce.views.NeidentAkceEditView.form_invalid", extra={"errors": form.errors})
        return super().form_invalid(form)
