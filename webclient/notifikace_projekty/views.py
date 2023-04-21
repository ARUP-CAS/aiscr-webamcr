import logging
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from core.message_constants import (
    HLIDACI_PES_USPESNE_VYTVOREN,
    HLIDACI_PES_USPESNE_SMAZAN,
    HLIDACI_PES_NEUSPESNE_VYTVOREN,
    HLIDACI_PES_NEUSPESNE_SMAZAN,
)
from uzivatel.models import User
from django.views import View
from django.views.generic import TemplateView
from .models import Pes
from .forms import (
    KATASTR_CONTENT_TYPE,
    KRAJ_CONTENT_TYPE,
    OKRES_CONTENT_TYPE,
    PesFormSetHelper,
    create_pes_form,
)
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from .forms import CONTENT_TYPES

logger = logging.getLogger('python-logstash-logger')


ALLOWED_ROLES = ["admin", "archeolog", "archivar"]
CARD_NAME_TRANS = {
    KRAJ_CONTENT_TYPE: _("notifikaceProjekty.list.card.ruianKraj.label"),
    OKRES_CONTENT_TYPE: _("notifikaceProjekty.list.card.ruianOkres.label"),
    KATASTR_CONTENT_TYPE: _("notifikaceProjekty.list.card.ruianKatastr.label"),
}


class PesListView(LoginRequiredMixin, TemplateView):
    """
    View to get list of all hlidacich psu on user.
    3 separate formsets per 1 content type
    """

    http_method_names = ["get"]
    template_name = "notifikace_projekty/pes_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        old_pes_post = self.request.session.pop("_old_pes_post", None)
        old_pes_type = self.request.session.pop("_old_pes_type", None)
        PesFormset = {}
        context["formsets"] = []
        for model_type in CONTENT_TYPES:
            PesFormset[model_type] = inlineformset_factory(
                User,
                Pes,
                form=create_pes_form(
                    model_typ=model_type,
                ),
                extra=1,
                can_delete=False,
            )
            if old_pes_post and old_pes_type == model_type:
                pes_formset = PesFormset[model_type](
                    data=old_pes_post,
                    instance=self.request.user,
                    queryset=Pes.objects.filter(content_type__model=model_type),
                )
                pes_formset.is_valid()
            else:
                pes_formset = PesFormset[model_type](
                    instance=self.request.user,
                    queryset=Pes.objects.filter(content_type__model=model_type),
                )
            context["formsets"].append(
                {
                    "name": CARD_NAME_TRANS[model_type],
                    "form": pes_formset,
                    "model_typ": model_type,
                }
            )
        context["pes_helper"] = PesFormSetHelper()
        context["show"] = {"editovat": True}
        return context


class PesCreateView(LoginRequiredMixin, View):
    """
    View to create new hlidaci pes
    """

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        model_typ = request.GET.get("model-typ")
        PesFormset = inlineformset_factory(
            User,
            Pes,
            form=create_pes_form(model_typ=model_typ),
            extra=1,
        )
        formset_pes = PesFormset(
            request.POST,
            instance=request.user,
            queryset=Pes.objects.filter(content_type__model=model_typ),
        )
        if formset_pes.is_valid():
            logger.debug("notifikace_projekty.PesCreateView.post.is_valid")
            formset_pes.save()
            messages.add_message(
                request, messages.SUCCESS, HLIDACI_PES_USPESNE_VYTVOREN
            )
        else:
            logger.debug("notifikace_projekty.PesCreateView.post.not_valid", extra={"errors": formset_pes.errors})
            request.session["_old_pes_post"] = request.POST
            request.session["_old_pes_type"] = model_typ
            messages.add_message(
                request, messages.ERROR, HLIDACI_PES_NEUSPESNE_VYTVOREN
            )
        return redirect("notifikace_projekty:list")


class PesSmazatView(LoginRequiredMixin, TemplateView):
    """
    View to delete hlidaci pes
    """

    template_name = "core/transakce_modal.html"
    title = _("notifikace_projekty.modalForm.smazatPsa.title.text")
    id_tag = "smazat-pes-form"
    button = _("notifikace_projekty.modalForm.smazatPes.submit.button")

    def get_zaznam(self):
        id = self.kwargs.get("pk")
        return get_object_or_404(
            Pes,
            pk=id,
        )

    def get_context_data(self, **kwargs):
        zaznam = self.get_zaznam()
        context = {
            "object": zaznam,
            "title": self.title,
            "id_tag": self.id_tag,
            "button": self.button,
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        try:
            zaznam = self.get_zaznam()
            zaznam.delete()
            messages.add_message(request, messages.SUCCESS, HLIDACI_PES_USPESNE_SMAZAN)
        except Exception as err:
            logger.warning("notifikace_projekty.PesSmazatView.post.not_valid", extra={"err": err})
            messages.add_message(
                request, messages.SUCCESS, HLIDACI_PES_NEUSPESNE_SMAZAN
            )
        return JsonResponse({"redirect": reverse("notifikace_projekty:list")})
