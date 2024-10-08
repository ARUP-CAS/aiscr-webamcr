import logging

from core.message_constants import (
    HLIDACI_PES_NEUSPESNE_SMAZAN,
    HLIDACI_PES_NEUSPESNE_VYTVOREN,
    HLIDACI_PES_USPESNE_SMAZAN,
    HLIDACI_PES_USPESNE_VYTVOREN,
)
from core.repository_connector import FedoraTransaction
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import OuterRef, Subquery
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView
from heslar.models import RuianKatastr, RuianKraj, RuianOkres
from uzivatel.models import User

from .forms import (
    CONTENT_TYPES,
    KATASTR_CONTENT_TYPE,
    KRAJ_CONTENT_TYPE,
    OKRES_CONTENT_TYPE,
    PesFormSetHelper,
    create_pes_form,
)
from .models import Pes

logger = logging.getLogger(__name__)


ALLOWED_ROLES = ["admin", "archeolog", "archivar"]
CARD_NAME_TRANS = {
    KRAJ_CONTENT_TYPE: _("notifikaceProjekty.views.list.card.ruianKraj.label"),
    OKRES_CONTENT_TYPE: _("notifikaceProjekty.views.list.card.ruianOkres.label"),
    KATASTR_CONTENT_TYPE: _("notifikaceProjekty.views.list.card.ruianKatastr.label"),
}


class PesListView(LoginRequiredMixin, TemplateView):
    """
    Třída pohledu pro zobrazení listu hlídacích psů.
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
            filter_type = ContentType.objects.get(model=model_type).model_class()
            nazev = filter_type.objects.filter(id=OuterRef("object_id")).values("nazev")
            if old_pes_post and old_pes_type == model_type:
                pes_formset = PesFormset[model_type](
                    data=old_pes_post,
                    instance=self.request.user,
                    queryset=Pes.objects.filter(content_type__model=model_type)
                    .annotate(razeni=Subquery(nazev))
                    .order_by("razeni"),
                )
                pes_formset.is_valid()
            else:
                pes_formset = PesFormset[model_type](
                    instance=self.request.user,
                    queryset=Pes.objects.filter(content_type__model=model_type)
                    .annotate(razeni=Subquery(nazev))
                    .order_by("razeni"),
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
    Třída pohledu pro vytvořené hlídacího psa.
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
            messages.add_message(request, messages.SUCCESS, HLIDACI_PES_USPESNE_VYTVOREN)
            user: User = request.user
            user.active_transaction = FedoraTransaction(user, self.request.user)
            user.close_active_transaction_when_finished = True
            user.save()
        else:
            logger.debug("notifikace_projekty.PesCreateView.post.not_valid", extra={"errors": formset_pes.errors})
            request.session["_old_pes_post"] = request.POST
            request.session["_old_pes_type"] = model_typ
            messages.add_message(request, messages.ERROR, HLIDACI_PES_NEUSPESNE_VYTVOREN)
        return redirect("notifikace_projekty:list")


class PesSmazatView(LoginRequiredMixin, TemplateView):
    """
    Třída pohledu pro smazání hlídacího psa pomocí modalu.
    """

    template_name = "core/transakce_modal.html"
    title = _("notifikaceProjekty.views.pesSmazatView.title.text")
    id_tag = "smazat-pes-form"
    button = _("notifikaceProjekty.views.pesSmazatView.submitButton")

    def get_zaznam(self) -> Pes:
        id = self.kwargs.get("pk")
        return get_object_or_404(
            Pes,
            pk=id,
        )

    def get_object_identification(self) -> str:
        pes: Pes = self.get_zaznam()
        object = pes.content_object
        if isinstance(object, RuianKatastr) or isinstance(object, RuianOkres) or isinstance(object, RuianKraj):
            return object.nazev
        if hasattr(object, "ident_cely"):
            return object.ident_cely
        return ""

    def get_context_data(self, **kwargs):
        zaznam = self.get_zaznam()
        context = {
            "object": zaznam,
            "title": self.title,
            "id_tag": self.id_tag,
            "button": self.button,
            "question": True,
            "object_identification": self.get_object_identification(),
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
            messages.add_message(request, messages.SUCCESS, HLIDACI_PES_NEUSPESNE_SMAZAN)
        request.user.save_metadata()
        return JsonResponse({"redirect": reverse("notifikace_projekty:list")})
