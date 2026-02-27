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
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView
from fedora_management.decorators import handle_fedora_error
from heslar.models import RuianKatastr, RuianKraj, RuianOkres
from uzivatel.models import User, UserNotificationType

from .forms import (
    CONTENT_TYPES,
    KATASTR_CONTENT_TYPE,
    KRAJ_CONTENT_TYPE,
    OKRES_CONTENT_TYPE,
    PES_NOTIFICATIONS,
    PesFormSetHelper,
    PesInlineFormSet,
    PesNotificationsForm,
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
        """Vrací context data.

        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        context = super().get_context_data(**kwargs)
        old_pes_post = self.request.session.pop("_old_pes_post", None)
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
                formset=PesInlineFormSet,
                can_delete=False,
            )
            filter_type = ContentType.objects.get(model=model_type).model_class()
            nazev = filter_type.objects.filter(id=OuterRef("object_id")).values("nazev")
            if old_pes_post:
                pes_formset = PesFormset[model_type](
                    data=old_pes_post,
                    instance=self.request.user,
                    prefix=model_type,
                    queryset=Pes.objects.filter(content_type__model=model_type)
                    .annotate(razeni=Subquery(nazev))
                    .order_by("razeni"),
                )
            else:
                pes_formset = PesFormset[model_type](
                    instance=self.request.user,
                    prefix=model_type,
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
        old_pes_notifications = {
            "notifications-notification_types": self.request.session.pop("_old_pes_notifications", None)
        }
        if (
            old_pes_notifications["notifications-notification_types"]
            or old_pes_notifications["notifications-notification_types"] == []
        ):
            context["form_notifications"] = PesNotificationsForm(
                data=old_pes_notifications,
                instance=self.request.user,
                prefix="notifications",
            )
        else:
            context["form_notifications"] = PesNotificationsForm(
                instance=self.request.user,
                prefix="notifications",
            )
        context["pes_helper"] = PesFormSetHelper()
        context["show"] = {"editovat": True}
        return context


class PesCreateView(LoginRequiredMixin, View):
    """
    Třída pohledu pro vytvořené hlídacího psa.
    """

    http_method_names = ["post"]

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        """Obsluhuje HTTP metodu POST.

        :param request: Django HTTP požadavek použitý při zpracování.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Vrací výsledek provedené operace."""
        formsets = []
        valid = True
        pes_form_valid = False
        pes_object_count = 0
        for model_typ in CONTENT_TYPES:
            PesFormset = inlineformset_factory(
                User,
                Pes,
                form=create_pes_form(model_typ=model_typ),
                extra=1,
                formset=PesInlineFormSet,
            )
            formset_pes = PesFormset(
                request.POST,
                instance=request.user,
                prefix=model_typ,
                queryset=Pes.objects.filter(content_type__model=model_typ),
            )
            if not formset_pes.is_valid():
                valid = False
                break
            formsets.append(formset_pes)
            pes_object_count += formset_pes.count_non_empty_forms()

        pes_form = PesNotificationsForm(pes_object_count, request.POST, prefix="notifications")
        if pes_form.is_valid():
            pes_form_valid = True

        if valid and pes_form_valid:
            for formset_pes in formsets:
                formset_pes.save()
            notifications = pes_form.cleaned_data.get("notification_types")
            user: User = request.user
            user.active_transaction = FedoraTransaction(user, request.user)
            notification_group_idents = {x.ident_cely: x for x in notifications.all()}
            for group_ident in PES_NOTIFICATIONS:
                if group_ident in notification_group_idents:
                    user.notification_types.add(notification_group_idents[group_ident])
                else:
                    type_obj = UserNotificationType.objects.get(ident_cely=group_ident)
                    user.notification_types.remove(type_obj)
            messages.add_message(request, messages.SUCCESS, HLIDACI_PES_USPESNE_VYTVOREN)

            user.close_active_transaction_when_finished = True
            user.save()
        else:
            logger.debug(
                "notifikace_projekty.PesCreateView.post.not_valid", extra={"error": [fs.errors for fs in formsets]}
            )
            request.session["_old_pes_post"] = request.POST
            request.session["_old_pes_notifications"] = request.POST.getlist("notifications-notification_types")
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
        """Vrací zaznam.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        id = self.kwargs.get("pk")
        return get_object_or_404(
            Pes,
            pk=id,
        )

    def get_object_identification(self) -> str:
        """Vrací object identification.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        pes: Pes = self.get_zaznam()
        object = pes.content_object
        if isinstance(object, RuianKatastr) or isinstance(object, RuianOkres) or isinstance(object, RuianKraj):
            return object.nazev
        if hasattr(object, "ident_cely"):
            return object.ident_cely
        return ""

    def get_context_data(self, **kwargs):
        """Vrací context data.

        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
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
        """Vrací výsledek operace.

        :param request: Django HTTP požadavek použitý při zpracování.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """Obsluhuje HTTP metodu POST.

        :param request: Django HTTP požadavek použitý při zpracování.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Vrací výsledek provedené operace."""
        try:
            zaznam = self.get_zaznam()
            zaznam.delete()
            if Pes.objects.filter(user=request.user).count() == 0:
                request.user.notification_types.clear()
            messages.add_message(request, messages.SUCCESS, HLIDACI_PES_USPESNE_SMAZAN)
            user: User = request.user
            user.active_transaction = FedoraTransaction()
            user.close_active_transaction_when_finished = True
            user.save()
        except Exception as err:
            logger.warning("notifikace_projekty.PesSmazatView.post.not_valid", extra={"error": err})
            messages.add_message(request, messages.SUCCESS, HLIDACI_PES_NEUSPESNE_SMAZAN)
        return JsonResponse({"redirect": reverse("notifikace_projekty:list")})
