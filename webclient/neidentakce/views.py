

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic.edit import UpdateView
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _

from core.message_constants import ZAZNAM_SE_NEPOVEDLO_EDITOVAT, ZAZNAM_USPESNE_EDITOVAN
from .forms import NeidentAkceForm

from .models import NeidentAkce

import logging

logger = logging.getLogger('python-logstash-logger')


class NeidentAkceEditView(LoginRequiredMixin, UpdateView):
    model = NeidentAkce
    template_name = "core/transakce_modal.html"
    title = _("neidentAkce.modalForm.edit.title.text")
    id_tag = "edit-neident-form"
    button = _("neidentAkce.modalForm.edit.submit.button")
    allowed_states = []
    success_message = "success"
    form_class = NeidentAkceForm
    slug_field = "dokument_cast__id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zaznam = self.object
        context = {
            "object": zaznam,
            "title": self.title,
            "id_tag": self.id_tag,
            "button": self.button,
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