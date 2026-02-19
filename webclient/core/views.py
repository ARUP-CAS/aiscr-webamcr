import json
import logging
import math
import os
import re
import tempfile
import unicodedata
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas
from adb.models import Adb
from arch_z.models import ArcheologickyZaznam
from core.constants import (
    LIMIT_PRVKU_ZOBRAZENI_HEATMAP,
    MAX_POCET_SOUBORU_PROJEKTU,
    ROLE_ADMIN_ID,
    ROLE_ARCHEOLOG_ID,
    ROLE_ARCHIVAR_ID,
    ROLE_BADATEL_ID,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
)
from core.forms import CheckStavNotChangedForm, TransaltionImportForm
from core.ident_cely import get_record_from_ident
from core.message_constants import (
    APPLICATION_RESTART_ERROR,
    APPLICATION_RESTART_SUCCESS,
    DOKUMENT_NEKDO_ZMENIL_STAV,
    PRISTUP_ZAKAZAN,
    PROJEKT_NEKDO_ZMENIL_STAV,
    SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV,
    SPATNY_ZAZNAM_SOUBOR_VAZBA,
    SPATNY_ZAZNAM_ZAZNAM_VAZBA,
    TRANSLATION_DELETE_CANNOT_MAIN,
    TRANSLATION_DELETE_ERROR,
    TRANSLATION_DELETE_SUCCESS,
    TRANSLATION_UPLOAD_SUCCESS,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT_JINA_TRANSAKCE,
    ZAZNAM_USPESNE_SMAZAN,
)
from core.models import AntivirusCheckResult, Soubor
from core.repository_connector import (
    FedoraError,
    FedoraRepositoryConnector,
    FedoraTransaction,
    FedoraTransactionStatus,
    FedoraUpdatedByAnotherTransactionError,
)
from core.utils import (
    SessionIdentifier,
    find_pos_with_backup,
    get_heatmap_pas,
    get_heatmap_pian,
    get_message,
    get_pas_from_envelope,
    get_pian_from_envelope,
    replace_last,
)
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.db.models.functions import AsWKT
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import FilteredRelation, Q, Value
from django.http import FileResponse, Http404, HttpResponse, HttpResponseRedirect, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django_auto_logout.utils import now, seconds_until_idle_time_end
from django_filters.views import FilterView
from django_prometheus.exports import ExportToDjangoView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin, TableExport
from dokument.models import Dokument, get_dokument_soubor_name
from ez.models import ExterniZdroj
from heslar import hesla_dynamicka
from heslar.hesla import HESLAR_PRISTUPNOST
from heslar.hesla_dynamicka import (
    PRISTUPNOST_ANONYM_ID,
    PRISTUPNOST_ARCHEOLOG_ID,
    PRISTUPNOST_ARCHIVAR_ID,
    PRISTUPNOST_BADATEL_ID,
)
from heslar.models import Heslar
from historie.models import Historie
from pas.models import SamostatnyNalez
from pian.models import Pian
from polib import pofile
from projekt.models import Projekt
from rosetta import get_version as get_rosetta_version
from rosetta.access import can_translate_language
from rosetta.conf import settings as rosetta_settings
from rosetta.views import (
    RosettaFileLevelMixin,
    TranslationFileDownload,
    TranslationFileListView,
    TranslationFormView,
    get_app_name,
)
from uzivatel.models import User

from .connectors import RedisConnector
from .exceptions import ZaznamSouborNotmatching
from .mixins import IPWhitelistMixin
from .models import Permissions, PermissionsSkip, check_permissions

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def index(request):
    "Funkce podledu pro zobrazení hlavní stránky."
    return render(request, "core/index.html")


@require_http_methods(["POST"])
def delete_file_DZ(request, typ_vazby, ident_cely, pk):
    """
    Funkce pohledu pro smazání souboru z dropzone. Funkce maže jak záznam v DB tak i soubor na disku.
    """
    if not request.session.get("session_uuid"):
        return JsonResponse({"success": False}, status=400)

    session_identifier = SessionIdentifier(request)
    cache_ident = session_identifier.get_ident()
    file_can_delete = session_identifier.file_exists(pk)

    if cache_ident is None or ident_cely != cache_ident or not file_can_delete:
        return JsonResponse({"success": False}, status=400)
    logger.debug(
        "core.views.delete_file_DZ.start",
        extra={"ident_cely": ident_cely, "typ_vazby": typ_vazby, "pk": pk, "method": request.method},
    )

    soubor: Soubor = get_object_or_404(Soubor, pk=pk)
    try:
        check_soubor_vazba(typ_vazby, ident_cely, pk)
    except ZaznamSouborNotmatching as err:
        logger.debug(
            "core.views.delete_file_DZ.vazbar_error",
            extra={"ident_cely": ident_cely, "typ_vazby": typ_vazby, "pk": pk, "error": err},
        )
        messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
        return JsonResponse({"success": False}, status=400)
    fedora_transaction = FedoraTransaction()
    logger.debug(
        "core.views.delete_file_DZ.not_deleted",
        extra={"pk": soubor.pk, "transaction": fedora_transaction.uid},
    )
    soubor.deleted_by_user = request.user
    soubor.active_transaction = fedora_transaction
    soubor_pk = soubor.pk
    transaction_error = False
    with transaction.atomic():
        try:
            soubor.delete()
            connector = FedoraRepositoryConnector(soubor.vazba.navazany_objekt, fedora_transaction)
            logger.debug("core.views.delete_file_DZ.deleted.delete_binary_file_completely", extra={"pk": soubor_pk})
            connector.delete_binary_file_completely(soubor)
            fedora_transaction.mark_transaction_as_closed()
            session_identifier.remove_file_reference(pk)
            return JsonResponse({"success": True})
        except FedoraUpdatedByAnotherTransactionError as err:
            logger.debug(
                "core.views.delete_file_DZ.another_transaction",
                extra={"pk": soubor_pk, "error": err, "transaction": fedora_transaction.uid},
            )
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT_JINA_TRANSAKCE)
            transaction_error = True
    if transaction_error is False and Soubor.objects.filter(pk=soubor_pk).exists():
        # Není jisté, zda je 404 jediná správná varianta.
        logger.debug("core.views.delete_file_DZ.not_deleted", extra={"soubor": soubor})
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
        django_messages = []
        for message in messages.get_messages(request):
            django_messages.append(
                {
                    "level": message.level,
                    "message": message.message,
                    "extra_tags": message.tags,
                }
            )
        fedora_transaction.rollback_transaction()
        return JsonResponse({"success": False}, status=400)

    if not transaction_error and fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
        fedora_transaction.mark_transaction_as_closed()
    elif transaction_error and fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
        fedora_transaction.rollback_transaction()
    return JsonResponse({"success": False}, status=400)


@login_required
@require_http_methods(["POST", "GET"])
def delete_file(request, typ_vazby, ident_cely, pk):
    """
    Funkce pohledu pro smazání souboru. Funkce maže jak záznam v DB tak i soubor na disku.
    """
    logger.debug(
        "core.views.delete_file.start",
        extra={"ident_cely": ident_cely, "typ_vazby": typ_vazby, "pk": pk, "method": request.method},
    )
    soubor: Soubor = get_object_or_404(Soubor, pk=pk)
    try:
        check_soubor_vazba(typ_vazby, ident_cely, pk)
    except ZaznamSouborNotmatching as err:
        logger.debug(
            "core.views.delete_file.vazbar_error",
            extra={"ident_cely": ident_cely, "typ_vazby": typ_vazby, "pk": pk, "error": err},
        )
        messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
        if request.method == "POST":
            next_url = request.POST.get("next", "core:home")
        else:
            next_url = request.GET.get("next", "core:home")
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
            safe_redirect = next_url
        else:
            safe_redirect = "/"
        return redirect(safe_redirect)
    if request.method == "POST":
        fedora_transaction = FedoraTransaction()
        logger.debug(
            "core.views.delete_file.not_deleted",
            extra={"pk": soubor.pk, "transaction": fedora_transaction.uid},
        )
        soubor.deleted_by_user = request.user
        soubor.active_transaction = fedora_transaction
        soubor_pk = soubor.pk
        transaction_error = False
        with transaction.atomic():
            try:
                soubor.delete()
                connector = FedoraRepositoryConnector(soubor.vazba.navazany_objekt, fedora_transaction)
                logger.debug("core.views.delete_file.deleted.delete_binary_file", extra={"pk": soubor_pk})
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
                connector.delete_binary_file(soubor)

            except FedoraUpdatedByAnotherTransactionError as err:
                logger.debug(
                    "core.views.delete_file.another_transaction",
                    extra={"pk": soubor_pk, "error": err, "transaction": fedora_transaction.uid},
                )
                messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT_JINA_TRANSAKCE)
                transaction_error = True
                if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                    fedora_transaction.rollback_transaction()
                return JsonResponse({"success": False}, status=400)
        if transaction_error is False and Soubor.objects.filter(pk=soubor_pk).exists():
            # Není jisté, zda je 404 jediná správná varianta.
            logger.debug("core.views.delete_file.not_deleted", extra={"soubor": soubor})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            django_messages = []
            for message in messages.get_messages(request):
                django_messages.append(
                    {
                        "level": message.level,
                        "message": message.message,
                        "extra_tags": message.tags,
                    }
                )
            fedora_transaction.rollback_transaction()
            return JsonResponse({"messages": django_messages}, status=400)
        next_url = request.POST.get("next")
        if next_url:
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
                response = next_url
            else:
                logger.warning("core.views.delete_file.redirect_not_safe", extra={"next_url": next_url})
                response = reverse("core:home")
        else:
            response = reverse("core:home")
        if not transaction_error and fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
            fedora_transaction.mark_transaction_as_closed()
        elif transaction_error and fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
            fedora_transaction.rollback_transaction()
        return JsonResponse({"redirect": response})
    else:
        context = {
            "object": soubor,
            "title": _("core.views.delete_file.title.text") + f" {soubor.nazev}" + "?",
            "id_tag": "smazat-soubor-form",
            "button": _("core.views.smazat.submitButton.text"),
        }
        return render(request, "core/transakce_modal.html", context)


class DownloadFile(LoginRequiredMixin, View):
    thumb_small = False
    thumb_large = False

    @staticmethod
    def _preprocess_image(file_content: BytesIO) -> BytesIO:
        return file_content

    def get(self, request, typ_vazby, ident_cely, pk, *args, **kwargs) -> FileResponse | HttpResponse:
        try:
            check_soubor_vazba(typ_vazby, ident_cely, pk)
        except ZaznamSouborNotmatching as e:
            logger.debug(e)
            messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_SOUBOR_VAZBA)
            if url_has_allowed_host_and_scheme(
                request.GET.get("next", "core:home"), allowed_hosts=settings.ALLOWED_HOSTS
            ):
                safe_redirect = request.GET.get("next", "core:home")
            else:
                safe_redirect = "/"
            return redirect(safe_redirect)
        soubor: Soubor = get_object_or_404(Soubor, id=pk)
        if soubor.repository_uuid:
            if self.thumb_small and soubor.small_thumbnail is not None:
                return soubor.small_thumbnail
            elif self.thumb_large and soubor.large_thumbnail is not None:
                return soubor.large_thumbnail
            elif soubor.content_file_response is not None:
                return soubor.content_file_response
        raise Http404


class DownloadThumbnailSmall(DownloadFile):
    thumb_small = True


class DownloadThumbnailLarge(DownloadFile):
    thumb_large = True


class UpdateFileView(LoginRequiredMixin, TemplateView):
    """
    Třída pohledu pro zobrazení stránky pro nahrazení souboru.
    """

    template_name = "core/upload_file.html"

    def get(self, request, *args, **kwargs):
        typ_vazby = self.kwargs.get("typ_vazby")
        ident_cely = self.kwargs.get("ident_cely")
        file_id = self.kwargs.get("file_id")

        # Získání bezpečné URL pro přesměrování
        next_url = request.GET.get("next", "core:home")
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
            safe_redirect = next_url
        else:
            safe_redirect = "/"

        # Ověření vazby souboru
        try:
            check_soubor_vazba(typ_vazby, ident_cely, file_id)
        except ZaznamSouborNotmatching as e:
            logger.debug(e)
            messages.error(request, SPATNY_ZAZNAM_SOUBOR_VAZBA)
            return redirect(safe_redirect)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        next_url = request.GET.get("next", "core:home")
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
            safe_redirect = next_url
        else:
            safe_redirect = "/"
        return redirect(safe_redirect)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ident_cely"] = self.kwargs.get("ident_cely")
        context["back_url"] = self.request.GET.get("next", "/")
        context["file_id"] = self.kwargs.get("file_id")
        context["typ_vazby"] = self.kwargs.get("typ_vazby")
        context["info_tooltip"] = _("core.upload_file_replace.tooltip")
        return context


class UploadFileView(LoginRequiredMixin, TemplateView):
    """
    Třída pohledu pro zobrazení stránky s uploadem souboru.
    """

    template_name = "core/upload_file.html"
    http_method_names = ["get", "post"]

    def get_zaznam(self):
        self.typ_vazby = self.kwargs.get("typ_vazby")
        self.ident = self.kwargs.get("ident_cely")
        logger.debug(
            "core.views.UploadFileView.get_zaznam.start", extra={"typ_vazby": self.typ_vazby, "ident_cely": self.ident}
        )
        if self.typ_vazby == "pas":
            self.info_tooltip = _("core.upload_file_PAS.tooltip")
            return get_object_or_404(SamostatnyNalez, ident_cely=self.ident)
        elif self.typ_vazby == "dokument":
            self.info_tooltip = _("core.upload_file_dokument.tooltip")
            return get_object_or_404(Dokument, ident_cely=self.ident)
        elif self.typ_vazby == "model3d":
            self.info_tooltip = _("core.upload_file_model3d.tooltip")
            return get_object_or_404(Dokument, ident_cely=self.ident)
        else:
            self.info_tooltip = _("core.upload_file_projekt.tooltip")
            return get_object_or_404(Projekt, ident_cely=self.ident)

    def get_context_data(self, **kwargs):
        self.zaznam = self.get_zaznam()
        pk_set = self.session_identifier.get_cached_files()
        queryset = Soubor.objects.filter(pk__in=list(pk_set))
        seznam_mock = [obj.getMock() for obj in queryset]
        json_mock = json.dumps(seznam_mock, ensure_ascii=False)

        context = {
            "ident_cely": self.ident,
            "back_url": self.zaznam.get_absolute_url(),
            "typ_vazby": self.typ_vazby,
            "info_tooltip": self.info_tooltip,
            "seznam_mock": json_mock,
        }
        logger.debug(
            "core.views.UploadFileView.get_context_data.start",
            extra={"typ_vazby": self.typ_vazby, "ident_cely": self.ident},
        )
        return context

    def dispatch(self, request, *args, **kwargs):
        ident_cely = self.kwargs.get("ident_cely")
        self.session_identifier = SessionIdentifier(request)
        self.session_identifier.set_ident(ident_cely)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.session_identifier.clear_cached_files()
        self.zaznam = self.get_zaznam()
        return redirect(self.zaznam.get_absolute_url())


class BasePostUploadView(View):
    """
    Abstraktní třída pro zpracování nahrávání souborů.

    Poskytuje společnou logiku pro upload nového souboru i nahrazení existujícího souboru.
    Implementuje kompletní workflow pro validaci nahrávaných souborů včetně kontroly MIME typů,
    antivirové kontroly a detekce šifrovaných souborů. Potomci musí implementovat metodu
    handle_upload() pro specifické zpracování.

    Process Description:
        1. Kontrola přítomnosti souboru v requestu
        2. Validace MIME typu a detekce šifrování
        3. Antivirová kontrola nahrávaného obsahu
        4. Předání validovaného souboru potomkům pro konkrétní zpracování

    Attributes:
        http_method_names (list): Povolené HTTP metody - pouze POST
        source_url (str): URL zdroje souboru (pokud je specifikována)
        fedora_transaction (FedoraTransaction): Instance transakce pro práci s Fedora repository
        original_filename (str): Původní název nahrávaného souboru
    """

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        """
        Zpracuje POST request s nahrávaným souborem.

        Metoda provádí kompletní validaci nahrávaného souboru před jeho uložením:
        - Kontroluje přítomnost souboru v requestu
        - Validuje MIME typ a detekuje šifrované soubory
        - Provádí antivirovou kontrolu obsahu
        - Deleguje finální zpracování na potomky prostřednictvím handle_upload()

        Args:
            request (HttpRequest): Django HTTP request objekt obsahující nahrávaný soubor
            *args: Poziční argumenty předané z URL dispatcheru
            **kwargs: Klíčové argumenty z URL patternu (např. ident_cely, typ_vazby)

        Returns:
            JsonResponse: JSON odpověď s výsledkem operace

        Response Status Codes:
            200: Soubor byl úspěšně validován a zpracován
            400: Validační chyba (chybějící soubor, šifrovaný, virus, neplatný MIME typ)
            500: Neznámá chyba při zpracování
        """
        self.source_url = request.POST.get("source-url", "")
        self.fedora_transaction = FedoraTransaction()
        soubor: TemporaryUploadedFile = request.FILES.get("file")
        if not soubor:
            logger.error("core.views.post_upload.no_file")
            return self._unknown_error_response()
        self.original_filename = soubor.name
        soubor.seek(0)
        check_meme = Soubor.check_mime_for_url(soubor, self.source_url)
        if check_meme == "encrypted":
            logger.debug("core.views.post_upload.check_mime_for_url.encrypted")
            help_translation = _("core.views.post_upload.encrypted")
            return JsonResponse({"error": help_translation}, status=400)
        elif check_meme is False:
            logger.debug("core.views.post_upload.check_mime_for_url.rejected")
            help_translation = _("core.views.post_upload.mime_check_failed")
            return JsonResponse({"error": help_translation}, status=400)
        soubor_data = BytesIO(soubor.read())
        check_antivirus_result = Soubor.check_antivirus(soubor_data)
        if check_antivirus_result == AntivirusCheckResult.VIRUS_FOUND:
            logger.warning(
                "core.views.post_upload.check_antivirus_result.virus_found",
                extra={"soubor": soubor.name, "user": request.user.pk},
            )
            help_translation = _("core.views.post_upload.antivirus_check.virus_found")
            return JsonResponse({"error": help_translation}, status=400)
        if check_antivirus_result == AntivirusCheckResult.CHECK_FAILED:
            logger.warning(
                "core.views.post_upload.check_antivirus_result.check_failed",
                extra={"soubor": soubor.name, "user": request.user.pk},
            )
            help_translation = _("core.views.post_upload.antivirus_check.check_failed")
            return JsonResponse({"error": help_translation}, status=400)
        soubor.seek(0)
        return self.handle_upload(request, soubor, soubor_data, *args, **kwargs)

    def handle_upload(self, request, soubor, soubor_data, *args, **kwargs):
        """
        Abstraktní metoda pro implementaci konkrétního zpracování nahraného souboru.

        Tato metoda musí být implementována potomky třídy. Je volána z post() metody
        po úspěšné validaci souboru (MIME typ, antivirus). Potomci zde implementují
        specifickou logiku pro nové nahrání nebo aktualizaci existujícího souboru.

        Args:
            request (HttpRequest): Django HTTP request objekt s informacemi o uživateli a sessions
            soubor (TemporaryUploadedFile): Nahraný soubor z requestu
            soubor_data (BytesIO): Binární obsah souboru jako BytesIO objekt
            *args: Poziční argumenty z URL dispatcheru
            **kwargs: Klíčové argumenty z URL (např. ident_cely, typ_vazby, file_id)

        Returns:
            JsonResponse: JSON odpověď s výsledkem operace nahrání

        Raises:
            NotImplementedError: Pokud potomek tuto metodu neimplementuje
        """
        raise NotImplementedError

    def _append_duplicate_message(self, response_data, duplikat):
        """
        Přidá informaci o duplicitním souboru do odpovědi.

        Kontroluje, zda v systému již existuje soubor se stejným SHA-512 hashem.
        Pokud ano, přidá do response_data varovnou zprávu s informací o duplicitě
        včetně identifikátoru záznamu, ke kterému je duplicitní soubor připojen.

        Args:
            response_data (dict): Slovník s daty odpovědi, do kterého bude přidána zpráva
            duplikat (QuerySet): QuerySet s duplicitními soubory (Soubor objekty)

        Returns:
            dict: Upravený response_data slovník s přidanou duplicitní zprávou.
                  Pokud není nalezen žádný duplikát, vrací nezměněný slovník.

        Response Data Keys:
            duplicate (tuple): Tuple obsahující zprávu o duplicitě ve formátu:
                "Soubor {original_filename} byl již nahrán k záznamu {parent_ident}. Zpráva..."
        """
        if duplikat is not None and duplikat.exists():
            parent_ident = (
                duplikat.first().vazba.navazany_objekt.ident_cely
                if duplikat.first().vazba.navazany_objekt is not None
                else ""
            )
            help_translation = _("core.views.post_upload.duplikat2.text1")
            help_translation2 = _("core.views.post_upload.duplikat2.text2")
            help_translation3 = _("core.views.post_upload.duplikat2.text3")
            response_data["duplicate"] = (
                f"{help_translation} {self.original_filename} {help_translation2} "
                f"{parent_ident}. {help_translation3}",
            )
        return response_data

    def _append_rename_message(self, response_data, renamed, new_name):
        """
        Přidá informaci o přejmenování souboru do odpovědi.

        Pokud byl soubor během uploadu přejmenován (typicky kvůli úpravě přípony
        pro soulad s MIME typem), přidá do response_data informační zprávu.

        Args:
            response_data (dict): Slovník s daty odpovědi, do kterého bude přidána zpráva
            renamed (bool): True pokud došlo k přejmenování, False jinak
            new_name (str): Nový název souboru po přejmenování

        Returns:
            dict: Upravený response_data slovník s přidanou zprávou o přejmenování.
                  Pokud nedošlo k přejmenování (renamed=False), vrací nezměněný slovník.

        Response Data Keys:
            file_renamed (tuple): Tuple obsahující zprávu o přejmenování ve formátu:
                "Soubor {original_filename} byl přejmenován na {new_name}"
        """
        if renamed:
            help_translation = _("core.views.post_upload.renamed.text1")
            help_translation2 = _("core.views.post_upload.renamed.text2")
            response_data["file_renamed"] = (
                f"{help_translation} {self.original_filename} {help_translation2} " f"{new_name}",
            )
        return response_data

    def _unknown_error_response(self):
        """
        Vrátí JSON odpověď s chybovou zprávou a HTTP status 500 pro neočekávané chyby
        při zpracování souboru, které nejsou pokryty specifickými error handlery.

        Returns:
            JsonResponse: JSON odpověď s chybovou zprávou a HTTP status 500
        """
        help_translation = _("core.views.post_upload.unknown_error")
        logger.error("core.views.post_upload.unknown_error")
        return JsonResponse({"error": help_translation}, status=500)


class NewFileUploadView(BasePostUploadView):
    """
    Pohled pro nahrání nového souboru k záznamu (projekt, dokument, samostatný nález).

    Process Description:
        1. Kontrola oprávnění uživatele (nebo anonymního přístupu pro projekty)
        2. Rozlišení typu záznamu a generování názvu souboru
        3. Validace a případná úprava přípony souboru podle MIME typu
        4. Odstranění GPS dat z obrázků samostatných nálezů
        5. Uložení do Fedora repository
        6. Vytvoření záznamu v databázi s metadaty
        7. Detekce duplicit podle SHA-512 hashe
        8. Zaznamenání události nahrání do historie

    URL Parameters:
        ident_cely (str): Identifikátor záznamu, ke kterému má být soubor nahrán
        typ_vazby (str): Typ vazby - "projekt", "dokument", "model3d", nebo "pas"
    """

    def handle_upload(self, request, soubor, soubor_data, *args, **kwargs):
        """
        Implementuje nahrání nového souboru k záznamu.

        Provádí kompletní workflow pro vytvoření nového souboru včetně kontroly oprávnění,
        generování názvu, uložení do repository a vytvoření databázového záznamu.
        Podporuje anonymní upload pro oznámení a automaticky zpracovává metadata obrázků.

        Args:
            request (HttpRequest): HTTP request s informacemi o uživateli a session
            soubor (TemporaryUploadedFile): Nahraný soubor z requestu
            soubor_data (BytesIO): Binární obsah souboru
            *args: Poziční argumenty z URL
            **kwargs: Obsahuje 'ident_cely' (identifikátor záznamu) a 'typ_vazby' (typ vazby)

        Returns:
            JsonResponse: JSON odpověď s výsledkem operace

        Response Status Codes:
            200: Soubor úspěšně nahrán
            400: Chyba při nahrávání (transakční konflikt, MIME typ, atd.)
            403: Nedostatečná oprávnění nebo překročen limit souborů
            500: Neexistující záznam nebo jiná interní chyba
        """
        ident_cely = kwargs.get("ident_cely")
        logger.debug(
            "core.views.post_upload.start",
            extra={"pk": ident_cely, "source_url": self.source_url},
        )

        if not request.user.is_authenticated:
            typ_vazby = kwargs.get("typ_vazby")
            session_identifier = SessionIdentifier(request)
            if typ_vazby != "projekt" or not session_identifier.verify_project_ownership(ident_cely):
                logger.warning(
                    "core.views.post_upload.permission_denied_anonymous",
                    extra={"ident_cely": ident_cely},
                )
                return JsonResponse({"error": str(PRISTUP_ZAKAZAN)}, status=403)

        typ_vazby = kwargs.get("typ_vazby")
        resolved = self._resolve_object_and_name(request, ident_cely, soubor.name, typ_vazby)
        if isinstance(resolved, JsonResponse):
            return resolved
        objekt, new_name = resolved

        conn = FedoraRepositoryConnector(objekt, self.fedora_transaction, skip_container_check=False)
        mimetype = Soubor.get_mime_types(soubor)
        mime_extensions = Soubor.get_file_extension_by_mime(soubor)
        if len(mime_extensions) == 0:
            logger.debug("core.views.post_upload.check_mime_for_url.rejected")
            help_translation = _("core.views.post_upload.mime_rename_failed")
            return JsonResponse({"error": f"{help_translation}"}, status=400)
        file_name_extension = new_name.split(".")[-1].lower()
        if file_name_extension not in mime_extensions:
            old_name = new_name
            new_name = replace_last(new_name, new_name.split(".")[-1], mime_extensions[0])
            renamed = True
            logger.debug(
                "core.views.post_upload.check_mime_for_url.rename",
                extra={"mime_type": mimetype, "old": old_name, "new": new_name},
            )
        else:
            renamed = False
        if mimetype in ["image/png", "image/jpeg", "image/tiff"] and isinstance(objekt, SamostatnyNalez):
            soubor_data = Soubor.remove_gps_data(soubor_data)
        try:
            rep_bin_file = conn.save_binary_file(new_name, mimetype, soubor_data)
        except FedoraUpdatedByAnotherTransactionError as err:
            logger.debug("core.views.post_upload.upload_failed_another_transaction", extra={"error": err})
            help_translation = _("core.views.post_upload.upload_failed_another_transaction")
            return JsonResponse({"error": help_translation}, status=400)
        except FedoraError as err:
            logger.error("core.views.post_upload.fedora_error", extra={"error": err})
            help_translation = _("core.views.post_upload.fedora_error")
            return JsonResponse({"error": help_translation}, status=400)
        sha_512 = rep_bin_file.sha_512
        soubor_instance: Soubor = Soubor(
            vazba=objekt.soubory,
            nazev=new_name,
            mimetype=mimetype,
            size_mb=rep_bin_file.size_mb,
            path=rep_bin_file.url_without_domain,
            sha_512=sha_512,
        )
        soubor_instance.active_transaction = self.fedora_transaction
        soubor_instance.binary_data = soubor_data
        response_data = {"filename": soubor_instance.nazev}
        logger.debug("core.views.post_upload.saving", extra={"instance": soubor_instance})
        soubor_instance.save()
        if not request.user.is_authenticated:
            user_admin = User.objects.filter(pk=hesla_dynamicka.ADMIN_USER).first()
            soubor_instance.zaznamenej_nahrani(user_admin, self.original_filename)
        else:
            soubor_instance.zaznamenej_nahrani(request.user, self.original_filename)
        duplikat = Soubor.objects.filter(sha_512=sha_512).order_by("pk").exclude(id=soubor_instance.id)
        response_data = self._append_duplicate_message(response_data, duplikat)
        response_data = self._append_rename_message(response_data, renamed, new_name)
        logger.debug("core.views.post_upload.end", extra={"pk": soubor_instance.pk})
        response_data["id"] = soubor_instance.pk
        soubor_instance.close_active_transaction_when_finished = True
        soubor_instance.save()
        SessionIdentifier(request).add_file_reference(soubor_instance.pk)
        return JsonResponse(response_data, status=200)

    def _resolve_object_and_name(self, request, ident_cely, filename, typ_vazby):
        """
        Rozliší typ záznamu, zkontroluje oprávnění a vygeneruje standardizovaný název souboru.

        Na základě ident_cely a typ_vazby načte odpovídající záznam z databáze,
        ověří konzistenci mezi typ_vazby a skutečným typem objektu, zkontroluje
        oprávnění uživatele k nahrání souboru a vygeneruje standardizovaný název
        souboru podle příslušných konvencí.

        Args:
            request (HttpRequest): HTTP request s informacemi o uživateli
            ident_cely (str): Úplný identifikátor záznamu (např. "C-202400001")
            filename (str): Původní název nahrávaného souboru
            typ_vazby (str): Typ vazby - "projekt", "dokument", "model3d", nebo "pas"

        Returns:
            tuple | JsonResponse: Při úspěchu vrací tuple (objekt, new_name):
                - objekt (Projekt|Dokument|SamostatnyNalez): Instance nalezeného záznamu
                - new_name (str): Vygenerovaný standardizovaný název souboru
            Při chybě vrací JsonResponse s chybovou zprávou a status kódem 403/500
        """
        # Mapování typu vazby na permission action
        action_map = {
            "projekt": Permissions.actionChoices.soubor_nahrat_projekt,
            "dokument": Permissions.actionChoices.soubor_nahrat_dokument,
            "model3d": Permissions.actionChoices.soubor_nahrat_model3d,
            "pas": Permissions.actionChoices.soubor_nahrat_pas,
        }

        # Kontrola platnosti typu vazby
        action = action_map.get(typ_vazby)
        if action is None:
            self.fedora_transaction.rollback_transaction()
            logger.error(
                "core.views.post_upload.error.invalid_typ_vazby",
                extra={"typ_vazby": typ_vazby, "ident_cely": ident_cely},
            )
            return JsonResponse(
                {"error": _("core.views.post_upload.error.invalid_typ_vazby") + f": {typ_vazby}"},
                status=400,
            )

        # Rozlišení objektu podle typu vazby - dotazy pouze pro relevantní typ
        objekt = None
        new_name = None

        if typ_vazby == "projekt":
            projekt = Projekt.objects.filter(ident_cely=ident_cely).first()
            if projekt:
                objekt = projekt
                new_name = get_projekt_soubor_name(objekt, filename)
        elif typ_vazby in ("dokument", "model3d"):
            dokument = Dokument.objects.filter(ident_cely=ident_cely).first()
            if dokument:
                objekt = dokument
                new_name = get_dokument_soubor_name(objekt, filename)
        elif typ_vazby == "pas":
            samostatny_nalez = SamostatnyNalez.objects.filter(ident_cely=ident_cely).first()
            if samostatny_nalez:
                objekt = samostatny_nalez
                new_name = get_finds_soubor_name(objekt, filename)

        if objekt is None:
            self.fedora_transaction.rollback_transaction()
            logger.error(
                "core.views.post_upload.error.object_does_not_exist_or_type_mismatch",
                extra={"ident_cely": ident_cely, "typ_vazby": typ_vazby},
            )
            return JsonResponse(
                {"error": _("core.views.post_upload.error.object_does_not_exist") + " " + ident_cely},
                status=500,
            )

        if request.user.is_authenticated:
            if not check_permissions(action, request.user, objekt.ident_cely):
                self.fedora_transaction.rollback_transaction()
                logger.warning(
                    "core.views._resolve_object_and_name.permission_denied",
                    extra={"user": request.user.pk, "action": action, "ident_cely": ident_cely},
                )
                return JsonResponse({"error": str(PRISTUP_ZAKAZAN)}, status=403)

        if new_name is False:
            self.fedora_transaction.rollback_transaction()
            return JsonResponse(
                {
                    "error": (
                        _("core.views.post_upload.error.maximal_file_name_exceeded_part_1")
                        + f" {ident_cely} "
                        + _("core.views.post_upload.error.maximal_file_name_exceeded_part_2")
                    )
                },
                status=403,
            )
        return objekt, new_name


class UpdateExistingFileUploadView(LoginRequiredMixin, BasePostUploadView):
    """
    Pohled pro nahrazení existujícího souboru novou verzí.

    Rozdíly oproti NewFileUploadView:
        - Vždy vyžaduje přihlášení uživatele (LoginRequiredMixin)
        - Nepodporuje projekty (pouze dokument, model3d, pas)
        - Zachovává původní název souboru, aktualizuje pouze příponu
        - Aktualizuje existující záznam v Fedora repository místo vytváření nového
        - V historii zaznamenává jako novou verzi, ne nový soubor

    URL Parameters:
        typ_vazby (str): Typ vazby - "dokument", "model3d", nebo "pas"
        ident_cely (str): Identifikátor záznamu, ke kterému soubor patří
        file_id (int): Primary key existujícího Soubor objektu
    """

    def handle_upload(self, request, soubor, soubor_data, *args, **kwargs):
        """
        Implementuje aktualizaci existujícího souboru novou verzí.

        Provádí kompletní workflow pro nahrazení obsahu existujícího souboru včetně
        validace vazeb, aktualizace v repository a databázi. Zachovává původní název
        souboru (s možnou úpravou přípony) a vytváří novou verzi v historii.

        Args:
            request (HttpRequest): HTTP request s informacemi o přihlášeném uživateli
            soubor (TemporaryUploadedFile): Nový nahraný soubor z requestu
            soubor_data (BytesIO): Binární obsah nového souboru
            *args: Poziční argumenty z URL
            **kwargs: Obsahuje 'typ_vazby', 'ident_cely' a 'file_id'

        Returns:
            JsonResponse: JSON odpověď s výsledkem operace

        Response Status Codes:
            200: Soubor úspěšně aktualizován
            400: Chyba vazby, transakční konflikt, MIME typ nebo neplatný typ_vazby
            403: Nedostatečná oprávnění k nahrazení souboru
            500: Chybějící vazba nebo jiná interní chyba

        Raises:
            Http404: Pokud soubor s daným file_id neexistuje (get_object_or_404)
            ZaznamSouborNotmatching: Pokud soubor nepatří k danému záznamu
        """
        typ_vazby = kwargs.get("typ_vazby")
        ident_cely = kwargs.get("ident_cely")
        file_id = kwargs.get("file_id")
        logger.debug("core.views.post_upload.updating", extra={"pk": file_id, "source_url": self.source_url})

        # Kontrola platnosti typu vazby a oprávnění
        permission_check = self._check_update_permissions(request, typ_vazby, ident_cely, file_id)
        if isinstance(permission_check, JsonResponse):
            return permission_check

        try:
            check_soubor_vazba(typ_vazby, ident_cely, file_id)
        except ZaznamSouborNotmatching as err:
            logger.debug(
                "core.views.post_upload.vazbar_error_update",
                extra={"ident_cely": ident_cely, "typ_vazby": typ_vazby, "pk": file_id, "error": err},
            )
            self.fedora_transaction.rollback_transaction()
            return JsonResponse({"error": SPATNY_ZAZNAM_SOUBOR_VAZBA}, status=400)

        soubor_instance: Soubor = get_object_or_404(Soubor, id=file_id)
        soubor_instance.active_transaction = self.fedora_transaction
        logger.debug("core.views.post_upload.update", extra={"pk": soubor_instance.pk})
        objekt = soubor_instance.vazba.navazany_objekt
        new_name = soubor_instance.nazev
        original_name = soubor.name
        if soubor_instance.vazba.typ_vazby is None:
            self.fedora_transaction.rollback_transaction()
            logger.error("core.views.post_upload.error.no_vazba")
            return JsonResponse(
                {"error": _("core.views.post_upload.error.no_vazba")},
                status=500,
            )
        conn = FedoraRepositoryConnector(objekt, self.fedora_transaction)
        mimetype = Soubor.get_mime_types(soubor)
        mime_extensions = Soubor.get_file_extension_by_mime(soubor)
        if len(mime_extensions) == 0:
            logger.debug("core.views.post_upload.check_mime_for_url.rejected", extra={"old": original_name})
            help_translation = _("core.views.post_upload.mime_rename_failed")
            self.fedora_transaction.rollback_transaction()
            return JsonResponse({"error": f"{help_translation}"}, status=400)
        file_name_extension = new_name.split(".")[-1].lower()
        if file_name_extension not in mime_extensions:
            new_name = new_name.replace(new_name.split(".")[-1], mime_extensions[0])
            renamed = True
            logger.debug(
                "core.views.post_upload.check_mime_for_url.rename",
                extra={"mime_type": mimetype, "old": original_name, "new": new_name},
            )
        else:
            renamed = False
        if (
            mimetype in ["image/png", "image/jpeg", "image/tiff"]
            and soubor_instance.vazba.typ_vazby == SAMOSTATNY_NALEZ_RELATION_TYPE
        ):
            soubor_data = Soubor.remove_gps_data(soubor_data)
        rep_bin_file = None
        if soubor_instance.repository_uuid is not None:
            extension = soubor.name.split(".")[-1]
            new_name = f"{'.'.join(soubor_instance.nazev.split('.')[:-1])}.{extension}"
            try:
                rep_bin_file = conn.update_binary_file(new_name, mimetype, soubor_data, soubor_instance.repository_uuid)
            except FedoraUpdatedByAnotherTransactionError as err:
                logger.debug("core.views.post_upload.update_failed_another_transaction", extra={"error": err})
                help_translation = _("core.views.post_upload.update_failed_another_transaction")
                return JsonResponse({"error": help_translation}, status=400)
            except FedoraError as err:
                logger.error("core.views.post_upload.fedora_error", extra={"error": err})
                help_translation = _("core.views.post_upload.fedora_error")
                return JsonResponse({"error": help_translation}, status=400)
            logger.debug(
                "core.views.post_upload.update",
                extra={"pk": soubor_instance.pk, "new": new_name, "old": original_name},
            )
            soubor_instance.nazev = new_name
            soubor_instance.size_mb = rep_bin_file.size_mb
            soubor_instance.mimetype = mimetype
            soubor_instance.sha_512 = rep_bin_file.sha_512
            soubor_instance.binary_data = soubor_data
            soubor_instance.save()
            soubor_instance.zaznamenej_nahrani_nove_verze(request.user, original_name)
        if rep_bin_file is not None:
            duplikat = Soubor.objects.filter(sha_512=rep_bin_file.sha_512).exclude(id=soubor_instance.id).order_by("pk")
            response_data = {"filename": soubor_instance.nazev}
            response_data = self._append_duplicate_message(response_data, duplikat)
            response_data = self._append_rename_message(response_data, renamed, new_name)
            response_data["id"] = soubor_instance.pk
            soubor_instance.close_active_transaction_when_finished = True
            soubor_instance.save()
            return JsonResponse(response_data, status=200)
        else:
            soubor_instance.close_active_transaction_when_finished = True
            soubor_instance.save()
            logger.error("core.views.post_upload.rep_bin_file_is_none")
            return self._unknown_error_response()

    def _check_update_permissions(self, request, typ_vazby, ident_cely, file_id):
        """
        Zkontroluje platnost typu vazby a oprávnění uživatele k nahrazení souboru.

        Na základě typ_vazby ověří, zda je nahrazení souboru povoleno pro daný typ
        záznamu, a zkontroluje oprávnění uživatele pomocí check_permissions.

        Args:
            request (HttpRequest): HTTP request s informacemi o uživateli
            typ_vazby (str): Typ vazby - "dokument", "model3d", nebo "pas"
            ident_cely (str): Úplný identifikátor záznamu
            file_id (int): Primary key existujícího souboru

        Returns:
            bool | JsonResponse: True pokud je vše v pořádku,
                                 JsonResponse s chybovou zprávou při problému
        """
        # Mapování typu vazby na permission action
        # Poznámka: projekt není v mapování - nahrazení souborů projektu není povoleno
        action_map = {
            "dokument": Permissions.actionChoices.soubor_nahradit_dokument,
            "model3d": Permissions.actionChoices.soubor_nahradit_model3d,
            "pas": Permissions.actionChoices.soubor_nahradit_pas,
        }

        # Kontrola platnosti typu vazby
        action = action_map.get(typ_vazby)
        if action is None:
            self.fedora_transaction.rollback_transaction()
            logger.error(
                "core.views.post_upload.error.invalid_typ_vazby_for_update",
                extra={"typ_vazby": typ_vazby, "ident_cely": ident_cely, "file_id": file_id},
            )
            return JsonResponse(
                {"error": _("core.views.post_upload.error.invalid_typ_vazby") + f": {typ_vazby}"},
                status=400,
            )

        # Rozlišení objektu podle typu vazby - dotazy pouze pro relevantní typ
        objekt = None

        if typ_vazby in ("dokument", "model3d"):
            dokument = Dokument.objects.filter(ident_cely=ident_cely).first()
            if dokument:
                objekt = dokument
        elif typ_vazby == "pas":
            samostatny_nalez = SamostatnyNalez.objects.filter(ident_cely=ident_cely).first()
            if samostatny_nalez:
                objekt = samostatny_nalez

        # Kontrola, zda byl objekt nalezen
        if objekt is None:
            self.fedora_transaction.rollback_transaction()
            logger.error(
                "core.views.post_upload.error.object_does_not_exist_or_type_mismatch_update",
                extra={"ident_cely": ident_cely, "typ_vazby": typ_vazby, "file_id": file_id},
            )
            return JsonResponse(
                {"error": _("core.views.post_upload.error.object_does_not_exist") + " " + ident_cely},
                status=500,
            )

        # Kontrola oprávnění pro autentifikované uživatele
        if request.user.is_authenticated:
            if not check_permissions(action, request.user, objekt.ident_cely):
                self.fedora_transaction.rollback_transaction()
                logger.warning(
                    "core.views._check_update_permissions.permission_denied",
                    extra={"user": request.user.pk, "action": action, "ident_cely": ident_cely, "file_id": file_id},
                )
                return JsonResponse({"error": str(PRISTUP_ZAKAZAN)}, status=403)

        return True


def get_finds_soubor_name(find, filename, add_to_index=1):
    """
    Funkce pro získaní jména souboru pro samostatný nález.
    """
    ident_cely_sanitized = find.ident_cely.replace("-", "")
    files = find.soubory.soubory.filter(nazev__contains=ident_cely_sanitized)
    if not files.exists():
        return (f"{ident_cely_sanitized}F01") + os.path.splitext(filename)[1]
    else:
        list_last_char = [int(os.path.splitext(file.nazev)[0][-2:]) for file in files]
        last_char = max(list_last_char)
        if last_char != 99 or add_to_index == 0:
            new_last_char = str(last_char + add_to_index).zfill(2)
            extension = os.path.splitext(filename)[1]
            return f"{find.ident_cely.replace('-', '')}F{new_last_char}{extension}"
        else:
            logger.warning(
                "core.views.get_finds_soubor_name.cannot_upload",
                extra={"file": filename, "value": list_last_char},
            )
            return False


def get_projekt_soubor_name(projekt: Projekt, file_name):
    """
    Funkce pro získaní jména souboru pro projekt.
    """
    if Soubor.objects.filter(vazba__projekt_souboru=projekt).count() >= MAX_POCET_SOUBORU_PROJEKTU:
        return False
    split_file = os.path.splitext(file_name)
    nfkd_form = unicodedata.normalize("NFKD", split_file[0])
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return re.sub("[^A-Za-z0-9_]", "_", only_ascii) + split_file[1]
    # potrebne odstranit constraint soubor_filepath_key


def check_stav_changed(request, zaznam):
    """
    Funkce pro oveření jestli se zmenil stav záznamu pri uložení formuláře oproti jeho načtení.
    """
    logger.debug("core.views.check_stav_changed.start", extra={"pk": zaznam.pk})
    if request.method == "POST":
        # TODO: vyřešit úkol BR-A-5.
        form_check = CheckStavNotChangedForm(data=request.POST, db_stav=zaznam.stav)
        if form_check.is_valid():
            pass
        else:
            if "State_changed" in str(form_check.errors):
                if isinstance(zaznam, SamostatnyNalez):
                    messages.add_message(request, messages.ERROR, SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV)
                    logger.debug(
                        "core.views.check_stav_changed.state_changed.error",
                        extra={
                            "value": SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV,
                            "form_error": str(form_check.errors),
                        },
                    )
                elif isinstance(zaznam, ArcheologickyZaznam):
                    messages.add_message(
                        request,
                        messages.ERROR,
                        get_message(zaznam, "NEKDO_ZMENIL_STAV"),
                    )
                    logger.debug(
                        "core.views.check_stav_changed.state_changed.error",
                        extra={
                            "value": get_message(zaznam, "NEKDO_ZMENIL_STAV"),
                            "form_error": str(form_check.errors),
                        },
                    )
                elif isinstance(zaznam, Dokument):
                    messages.add_message(request, messages.ERROR, DOKUMENT_NEKDO_ZMENIL_STAV)
                    logger.debug(
                        "core.views.check_stav_changed.state_changed.error",
                        extra={"value": DOKUMENT_NEKDO_ZMENIL_STAV, "form_error": str(form_check.errors)},
                    )
                elif isinstance(zaznam, Projekt):
                    messages.add_message(request, messages.ERROR, PROJEKT_NEKDO_ZMENIL_STAV)
                    logger.debug(
                        "core.views.check_stav_changed.state_changed.error",
                        extra={"value": PROJEKT_NEKDO_ZMENIL_STAV, "form_error": str(form_check.errors)},
                    )
                return True

    else:
        # Ověří, že stav záznamu v DB odpovídá stavu při vstupu na detail.
        if request.GET.get("sent_stav", False) and str(request.GET.get("sent_stav")) != str(zaznam.stav):
            sent_stav = str(request.GET.get("sent_stav"))
            zaznam_stav = str(zaznam.stav)
            if isinstance(zaznam, SamostatnyNalez):
                messages.add_message(request, messages.ERROR, SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV)
                logger.debug(
                    "core.views.check_stav_changed.sent_stav.error",
                    extra={
                        "value": SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV,
                        "zaznam": zaznam_stav,
                        "info": sent_stav,
                    },
                )
            elif isinstance(zaznam, ArcheologickyZaznam):
                messages.add_message(request, messages.ERROR, get_message(zaznam, "NEKDO_ZMENIL_STAV"))
                logger.debug(
                    "core.views.check_stav_changed.sent_stav.error",
                    extra={
                        "value": get_message(zaznam, "NEKDO_ZMENIL_STAV"),
                        "zaznam": zaznam_stav,
                        "info": sent_stav,
                    },
                )
            elif isinstance(zaznam, Dokument):
                messages.add_message(request, messages.ERROR, DOKUMENT_NEKDO_ZMENIL_STAV)
                logger.debug(
                    "core.views.check_stav_changed.sent_stav.error",
                    extra={"value": DOKUMENT_NEKDO_ZMENIL_STAV, "zaznam": zaznam_stav, "info": sent_stav},
                )
            elif isinstance(zaznam, Projekt):
                messages.add_message(request, messages.ERROR, PROJEKT_NEKDO_ZMENIL_STAV)
                logger.debug(
                    "core.views.check_stav_changed.sent_stav.error",
                    extra={"value": PROJEKT_NEKDO_ZMENIL_STAV, "zaznam": zaznam_stav, "info": sent_stav},
                )
            return True
    logger.debug("core.views.check_stav_changed.sent_stav.false")
    return False


@login_required
@require_http_methods(["GET"])
def redirect_ident_view(request, ident_cely):
    """
    Funkce pro získaní správneho redirectu na záznam podle ident%cely záznamu.
    """
    object = get_record_from_ident(ident_cely)
    if object:
        try:
            if isinstance(object, Pian):
                return redirect(object.get_absolute_url(request))
            else:
                return redirect(object.get_absolute_url())
        except AttributeError:
            messages.error(request, _("core.views.redirectView.noRedirectUrl.message.text"))
            return redirect("core:home")
    else:
        messages.error(request, _("core.views.redirectView.identnotmatchingregex.message.text"))
        return redirect("core:home")


# Pro AJAX volání na prodloužení relace.
@login_required
@require_http_methods(["GET"])
def prolong_session(request):
    """
    Funkce pohledu pro prodloužení prihlášení.
    """
    options = getattr(settings, "AUTO_LOGOUT")
    current_time = now()
    session_time = seconds_until_idle_time_end(request, options["IDLE_TIME"], current_time)
    return JsonResponse(
        {"session_time": session_time},
        status=200,
    )


class ExportMixinDate(ExportMixin):
    """
    Mixin pro získaní názvu exportovaného souboru.
    """

    def get_export_filename(self, export_format, export_name=None):
        if export_name is None:
            export_name = self.export_name
        now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        return "{}{}.{}".format(export_name, now, export_format)


class PermissionFilterMixin:
    permission_model_lookup = ""
    typ_zmeny_lookup = ""
    group_to_accessibility = {
        ROLE_BADATEL_ID: [PRISTUPNOST_BADATEL_ID, PRISTUPNOST_ANONYM_ID],
        ROLE_ARCHEOLOG_ID: [PRISTUPNOST_ARCHEOLOG_ID, PRISTUPNOST_BADATEL_ID, PRISTUPNOST_ANONYM_ID],
        ROLE_ARCHIVAR_ID: [
            PRISTUPNOST_ARCHIVAR_ID,
            PRISTUPNOST_ARCHEOLOG_ID,
            PRISTUPNOST_BADATEL_ID,
            PRISTUPNOST_ANONYM_ID,
        ],
        ROLE_ADMIN_ID: [
            PRISTUPNOST_ARCHIVAR_ID,
            PRISTUPNOST_ARCHEOLOG_ID,
            PRISTUPNOST_BADATEL_ID,
            PRISTUPNOST_ANONYM_ID,
        ],
    }

    def check_filter_permission(self, qs, action=None):
        if action:
            permissions = Permissions.objects.filter(
                main_role=self.request.user.hlavni_role, address_in_app=self.request.resolver_match.route, action=action
            )
        else:
            permissions = Permissions.objects.filter(
                main_role=self.request.user.hlavni_role,
                address_in_app=self.request.resolver_match.route,
            )
        if permissions.count() > 0:
            for idx, perm in enumerate(permissions):
                if idx == 0:
                    new_qs = self.filter_by_permission(qs, perm)
                else:
                    new_qs = self.filter_by_permission(qs, perm) | new_qs

            perm_skips = list(
                PermissionsSkip.objects.filter(user=self.request.user).values_list("ident_list", flat=True)
            )
            if len(perm_skips) > 0:
                if "spoluprace/vyber" in perm.address_in_app:
                    ident_key = self.permission_model_lookup + "id__in"
                    perm_skips_list = [id for id in perm_skips[0].split(",") if id.isdigit()]
                else:
                    ident_key = self.permission_model_lookup + "ident_cely__in"
                    perm_skips_list = perm_skips[0].split(",")
                filterdoc = {ident_key: perm_skips_list}
                if perm.status:
                    filterdoc.update(self.add_status_lookup(perm))
                qs = new_qs | qs.filter(**filterdoc)
            else:
                qs = new_qs
        return qs

    def filter_by_permission(self, qs, permission):
        qs = qs.annotate(
            historie_zapsat=FilteredRelation(
                self.permission_model_lookup + "historie__historie",
                condition=Q(**{self.permission_model_lookup + "historie__historie__typ_zmeny": self.typ_zmeny_lookup}),
            ),
        )
        if not permission.base:
            logger.debug("core.views.PermissionFilterMixin.filter_by_permission.no_base")
            return qs.none()
        if permission.status:
            qs = qs.filter(**self.add_status_lookup(permission))
        if permission.ownership:
            qs = qs.filter(self.add_ownership_lookup(permission.ownership, qs))
        if permission.accessibility:
            qs = self.add_accessibility_lookup(permission, qs)

        return qs

    def add_status_lookup(self, permission):
        filterdoc = {}
        subed_status = re.sub("[a-zA-Z]", "", permission.status)
        if ">" in subed_status:
            operator_str = "__gt"
            status = subed_status[1]
        elif "<" in subed_status:
            operator_str = "__lt"
            status = subed_status[1]
        elif "-" in subed_status:
            operator_str = ["__gte", "__lte"]
        else:
            operator_str = ""
            status = subed_status[0]
        if isinstance(operator_str, list):
            i = 0
            for operator in operator_str:
                str_oper = self.permission_model_lookup + "stav" + operator
                filterdoc.update({str_oper: subed_status[i]})
                i -= 1
        else:
            str_oper = self.permission_model_lookup + "stav" + operator_str
            filterdoc.update({str_oper: status})
        return filterdoc

    def add_ownership_lookup(self, ownership, qs=None):
        filter_historie = {"uzivatel": self.request.user}
        filtered_my = Historie.objects.filter(**filter_historie)
        if ownership == Permissions.ownershipChoices.our:
            filter_historie = {"uzivatel__organizace": self.request.user.organizace}
            filtered_our = Historie.objects.filter(**filter_historie)
            return Q(**{"historie_zapsat__in": filtered_our})
        else:
            return Q(**{"historie_zapsat__in": filtered_my})

    def add_accessibility_lookup(self, permission, qs):
        accessibility_key = self.permission_model_lookup + "pristupnost__in"
        accessibilities = Heslar.objects.filter(
            nazev_heslare=HESLAR_PRISTUPNOST, id__in=self.group_to_accessibility.get(self.request.user.hlavni_role.id)
        )
        filter = {accessibility_key: accessibilities}
        return qs.filter(Q(**filter) | self.add_ownership_lookup(permission.accessibility, qs))


class SearchListView(ExportMixin, LoginRequiredMixin, SingleTableMixin, FilterView, PermissionFilterMixin):
    """
    Třída pohledu pro tabulky záznamů, která je použita jako základ pro jednotlivé pohledy.
    """

    template_name = "search_list.html"
    allow_empty = True
    export_formats = ["csv", "json", "xlsx"]
    app = "core"
    toolbar = "toolbar_akce.html"
    redis_value_list_field = None
    redis_snapshot_prefix = None
    vypis_app = "core"
    paginate_by = None
    table_pagination = {"per_page": 100}

    def create_export(self, export_format):
        from redis import Redis

        def check_if_aborted(r_inner: Redis, key_inner: str):
            aborted = r_inner.get(key_inner + "_stat") == "-1"
            if aborted:
                r_inner.delete(key_inner)
            return aborted

        def update_progress_bar(r_inner: Redis, key_inner: str, new_value: int, message: str):
            r_inner.set(key_inner, json.dumps({"percent": int(new_value), "text": message}), ex=3600)
            return check_if_aborted(r_inner, key_inner)

        def file_iterator(content, r, redis_variable_name, chunk_size=8192):
            bytes_sent = 0
            file_size = len(content)
            try:
                for i in range(0, len(content), chunk_size):
                    chunk = content[i : i + chunk_size]
                    bytes_sent += len(chunk)
                    if file_size > 100 and bytes_sent % (file_size // 20) < chunk_size:
                        update_progress_bar(
                            r,
                            redis_variable_name,
                            int(bytes_sent / file_size * 100),
                            _("core.templates.core.export_modal.sending_data"),
                        )
                    yield chunk
            except GeneratorExit:
                logger.warning("core.views.SearchListView.file_iterator.Connection_closed_by_client")
                r.delete(redis_variable_name)
            except Exception as e:
                logger.warning("core.views.SearchListView.file_iterator.Error_during_streaming", extra={"error": e})
                raise

        logger.debug("core.views.SearchListView.create_export.start", extra={"format": export_format})
        if self.redis_value_list_field and self.redis_snapshot_prefix:
            r = RedisConnector.get_connection_decode()
            export_suffix_string = self.request.GET["export_suffix_string"]
            redis_variable_name = f"export_{self.request.user.email.replace('@', '(at)')}_{export_suffix_string}"
            update_progress_bar(r, redis_variable_name, 0, _("core.templates.core.export_modal.collecting_data"))
            dataset = self.get_table_data()
            ident_cely_list = list(dataset.values_list(self.redis_value_list_field, flat=True))
            ident_cely_list = [f"{self.redis_snapshot_prefix}_{x}" for x in ident_cely_list]
            logger.debug(
                "core.views.SearchListView.create_export.redis_variable_name",
                extra={"redis": redis_variable_name},
            )
            r.set(redis_variable_name, 0)
            ident_cely_list_len = len(ident_cely_list)
            pipe = r.pipeline()
            data = []
            base_index = 0
            for i, key in enumerate(ident_cely_list):
                pipe.hgetall(key)
                if (i % 20000) == 0 or i == ident_cely_list_len - 1:
                    if update_progress_bar(
                        r,
                        redis_variable_name,
                        int(i / ident_cely_list_len * 100),
                        _("core.templates.core.export_modal.collecting_data"),
                    ):
                        return HttpResponse()
                    results = pipe.execute()
                    for index, result in enumerate(results):
                        if not result:
                            try:
                                ident_cely = ident_cely_list[base_index + index].split("_")[-1]
                                logger.warning(
                                    "core.views.SearchListView.snapshot.create.warning",
                                    extra={"ident_cely": ident_cely},
                                )
                                item = self.model.get_by_ident_cely(ident_cely)
                                key, value = item.generate_redis_snapshot()
                                if key and value:
                                    r.hset(key, mapping=value)
                                    results[index] = value
                            except Exception as err:
                                logger.error(
                                    "core.views.SearchListView.snapshot.error",
                                    extra={"ident_cely": ident_cely, "error": err},
                                )
                    data.extend(results)
                    base_index = i + 1

            if update_progress_bar(r, redis_variable_name, 100, _("core.templates.core.export_modal.converting_data")):
                return HttpResponse()
            data = pandas.DataFrame(data)
            filtered_column_order = [col.name for col in self.get_table().columns if col.name in data.columns]
            data = data[filtered_column_order]
            column_names = {str(column.name): str(column.verbose_name) for column in self.get_table().columns}
            data = data.rename(columns=column_names)
            if export_format == TableExport.CSV:
                filetype = 'attachment; filename="export.csv"'
                resdata = data.to_csv(index=False)
            elif export_format == TableExport.JSON:
                filetype = 'attachment; filename="export.json"'
                resdata = data.to_json(orient="records", force_ascii=False, index=False)
            elif export_format == TableExport.XLSX:
                excel_file = BytesIO()
                with pandas.ExcelWriter(excel_file, engine="openpyxl") as writer:
                    data.to_excel(writer, index=False)
                resdata = excel_file.getvalue()
                filetype = "attachment; filename=export.xlsx"
            else:
                return HttpResponse(_("core.views.SearchListView.create_export.export_format_not_supported"))
            response = StreamingHttpResponse(file_iterator(resdata, r, redis_variable_name))
            response["Content-Disposition"] = filetype
            if update_progress_bar(r, redis_variable_name, 100, _("core.templates.core.export_modal.file_generated")):
                return HttpResponse()
            logger.debug(
                "core.views.SearchListView.create_export.end",
                extra={
                    "format": export_format,
                    "redis": redis_variable_name,
                },
            )
            if check_if_aborted(r, redis_variable_name):
                logger.debug(
                    "core.views.SearchListView.create_export.aborted",
                    extra={"redis": redis_variable_name},
                )
                return HttpResponse()
            response["X-Accel-Buffering"] = "no"  # Zakázání bufferování v NGINX
            return response

    def init_translations(self):
        self.page_title = ""
        self.search_sum = ""
        self.pick_text = ""
        self.hasOnlyVybrat_header = ""
        self.hasOnlyVlastnik_header = ""
        self.hasOnlyArchive_header = ""
        self.hasOnlyPotvrdit_header = ""
        self.hasOnlyNase_header = ""
        self.default_header = ""
        self.toolbar_name = ""
        self.toolbar_label = ""

    def _get_sort_params(self):
        sort_params = self.request.GET.getlist("sort")
        return sort_params

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.init_translations()
        context["export_formats"] = self.export_formats
        context["page_title"] = self.page_title
        context["app"] = self.app
        context["toolbar"] = self.toolbar
        context["search_sum"] = self.search_sum
        context["pick_text"] = self.pick_text
        context["hasOnlyVybrat_header"] = self.hasOnlyVybrat_header
        context["hasOnlyVlastnik_header"] = self.hasOnlyVlastnik_header
        context["hasOnlyArchive_header"] = self.hasOnlyArchive_header
        context["hasOnlyPotvrdit_header"] = self.hasOnlyPotvrdit_header
        context["hasOnlyNase_header"] = self.hasOnlyNase_header
        context["default_header"] = self.default_header
        context["toolbar_name"] = self.toolbar_name
        context["toolbar_label"] = self.toolbar_label
        context["sort_params"] = self._get_sort_params()
        context["idents"] = context["table"].get_all_idents()
        context["vypis_app"] = self.vypis_app
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        qs.cache()
        return qs

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class StahnoutDataHistorickaView(LoginRequiredMixin, View):
    """
    Třída pohledu pro stažení historické verze souboru nebo metadat z Fedory
    """

    MODEL_MAP = {
        "Pian": Pian,
        "Projekt": Projekt,
        "ArcheologickyZaznam": ArcheologickyZaznam,
        "Adb": Adb,
        "Dokument": Dokument,
        "SamostatnyNalez": SamostatnyNalez,
        "ExterniZdroj": ExterniZdroj,
        "User": User,
        "Soubor": Soubor,
    }

    def get(self, request, model_name, ident_cely, timestamp):
        Model = self.MODEL_MAP.get(model_name)
        if Model is None:
            raise Http404

        def context_processor(content):
            yield content

        if model_name == "Soubor":
            record = Model.objects.get(pk=ident_cely)
            response = record.get_soubor_historicky(timestamp)
        else:
            record = Model.objects.get(ident_cely=ident_cely)
            metadata = record.get_metadata_historicka(timestamp)
            response = StreamingHttpResponse(context_processor(metadata), content_type="text/xml")
            response["Content-Disposition"] = 'attachment; filename="metadata.xml"'

        return response


class CheckUserAuthentication(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({"is_authenticated": request.user.is_authenticated})


@login_required
@require_http_methods(["POST"])
def post_ajax_get_pas_and_pian_limit(request):
    """
    Funkce pohledu pro získaní heatmapy.
    """
    body = json.loads(request.body.decode("utf-8"))
    params = [
        body["bounds"]["topLeft"]["lng"],
        body["bounds"]["bottomLeft"]["lat"],
        body["bounds"]["bottomRight"]["lng"],
        body["bounds"]["topRight"]["lat"],
        body["zoom"],
    ]
    num = 0
    req_pian = body["pian"]
    req_pas = body["pas"]
    pians = None
    if req_pas:
        pases = get_pas_from_envelope(body["bounds"], request).distinct()
        num = num + pases.count()

    if req_pian:
        pians, count = get_pian_from_envelope(body["bounds"], body["zoom"], request)
        num = num + count

    logger.debug("pas.views.post_ajax_get_pas_and_pian_limit.num", extra={"number": num})
    if (num < LIMIT_PRVKU_ZOBRAZENI_HEATMAP and not req_pian) or (
        num < LIMIT_PRVKU_ZOBRAZENI_HEATMAP and req_pian and pians is not None
    ):
        back = []

        if req_pas:
            back = list(pases.values("id", "ident_cely", type=Value("pas")).annotate(geom=AsWKT("geom")))

        if req_pian:
            logger.debug("Start getting pians")
            back += pians

            logger.debug("End building pians")
        if num > 0:
            return JsonResponse({"points": back, "algorithm": "detail", "count": num}, status=200)
        else:
            return JsonResponse({"points": [], "algorithm": "detail", "count": 0}, status=200)
    else:
        heats = []
        if req_pas:
            heats = heats + get_heatmap_pas(*params)
        if req_pian:
            heats = heats + get_heatmap_pian(*params)
        back = []
        cid = 0
        for heat in heats:
            cid += 1
            back.append(
                {
                    "id": str(cid),
                    "pocet": heat["count"],
                    "geom": heat["geometry"].replace(", ", ","),
                }
            )
        if len(heats) > 0:
            return JsonResponse({"heat": back, "algorithm": "heat", "count": len(heats)}, status=200)
        else:
            return JsonResponse({"heat": [], "algorithm": "heat", "count": len(heats)}, status=200)


def check_soubor_vazba(typ_vazby, ident, id_zaznamu):
    if typ_vazby == "model3d" or typ_vazby == "dokument":
        soubor = get_object_or_404(Dokument, ident_cely=ident).soubory.soubory.filter(pk=id_zaznamu)
    elif typ_vazby == "pas":
        soubor = get_object_or_404(SamostatnyNalez, ident_cely=ident).soubory.soubory.filter(pk=id_zaznamu)
    elif typ_vazby == "projekt":
        soubor = get_object_or_404(Projekt, ident_cely=ident).soubory.soubory.filter(pk=id_zaznamu)
    if soubor.count() > 0:
        return True
    else:
        raise ZaznamSouborNotmatching


class ReadTempValueView(View):
    def get(self, request):
        r = RedisConnector.get_connection_decode()
        temp_name = request.GET.get("temp_name", "")
        if temp_name.startswith("export_"):
            value = r.get(temp_name)
            try:
                return JsonResponse(json.loads(value))
            except Exception:
                # Ošetření případu, kdy klíč v Redis neexistuje.
                return JsonResponse({"percent": 0, "text": _("core.templates.core.export_modal.file_being_generated")})
        else:
            # Vrátí JSON odpověď se stavem 403 Forbidden.
            return JsonResponse({"error": "Access to 'export_' prefixed keys is forbidden"}, status=403)


class DeleteTempValueView(View):
    def get(self, request):
        r = RedisConnector.get_connection()
        temp_name = request.GET.get("temp_name", "")
        if temp_name.startswith("export_"):
            r.delete(temp_name)
            logger.debug("core.views.ResetTempValueView.get.result", extra={"value": temp_name})
            return JsonResponse({"result": "success"})
        else:
            # Vrátí JSON odpověď se stavem 403 Forbidden.
            return JsonResponse({"error": "Access to 'export_' prefixed keys is forbidden"}, status=403)


class AbortDownloadUpdateTempValueView(View):
    def get(self, request):
        r = RedisConnector.get_connection()
        temp_name = request.GET.get("temp_name", "")
        if temp_name.startswith("export_"):
            r.set(temp_name + "_stat", -1, ex=3500)
            logger.debug("core.views.AbortDownloadUpdateTempValueView.get.result", extra={"value": temp_name})
            return JsonResponse({"result": "success"})
        else:
            # Vrátí JSON odpověď se stavem 403 Forbidden.
            return JsonResponse({"error": "Access to 'export_' prefixed keys is forbidden"}, status=403)


class RosettaFileLevelMixinWithBackup(RosettaFileLevelMixin):
    """
    Třída podledu pro práci s prekladmi doplnena o backup osubory.
    """

    @cached_property
    def po_file_path(self):
        """Podle URL parametrů `kwargs` odvodí a vrátí cestu k `.po` souboru,
        který se má zobrazit nebo upravit.

        Pokud soubor neexistuje, vyvolá chybu 404.
        """
        # Dříve se tato hodnota označovala jako `rosetta_i18n_fn`.
        idx = self.kwargs["idx"]
        idx = int(idx)  # `idx` odpovídá regexu v URL; volání `int()` je bezpečné.

        third_party_apps = self.po_filter in ("all", "third-party")
        django_apps = self.po_filter in ("all", "django")
        project_apps = self.po_filter in ("all", "project")

        po_paths = find_pos_with_backup(
            self.language_id,
            project_apps=project_apps,
            django_apps=django_apps,
            third_party_apps=third_party_apps,
        )
        po_paths.sort(key=get_app_name)

        try:
            path = po_paths[idx]
        except IndexError:
            raise Http404
        return path


class TranslationImportView(FormView, RosettaFileLevelMixinWithBackup):
    """
    Třída pohledu pro import překladových souborů.
    """

    template_name = "rosetta/import_form.html"
    form_class = TransaltionImportForm

    def form_valid(self, form):
        new_pofile = form.cleaned_data["file"]
        tmp_path = None
        try:
            # Zapíše nahraný InMemoryUploadedFile do dočasného souboru a předá jeho cestu nástroji pofile.
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp_path = tmp.name
            for chunk in new_pofile.chunks():
                tmp.write(chunk)
            tmp.flush()
            tmp.close()
            po_file = pofile(tmp_path)
            # Dočasný soubor smaže až po načtení obsahu knihovnou polib.
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        except Exception as e:
            # Úklid při chybě.
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
            logger.error("core.views.TranslationImportView.form_valid", extra={"error": str(e)})
            messages.add_message(self.request, messages.ERROR, str(e))
            return redirect(reverse("rosetta-file-list", args=[self.po_filter]))
        p = Path(self.po_file_path)
        date_sufix = datetime.strftime(datetime.now(), "%d%m%Y%H%M")
        p.rename(Path(p.parent, f"{p.stem}_backup_{date_sufix}{p.suffix}"))
        self.handle_uploaded_file(new_pofile)
        po_filepath, ext = os.path.splitext(self.po_file_path)
        po_file.save_as_mofile(po_filepath + ".mo")
        messages.add_message(self.request, messages.SUCCESS, TRANSLATION_UPLOAD_SUCCESS)
        return redirect(reverse("rosetta-file-list", args=[self.po_filter]))

    def get_context_data(self, **kwargs):
        context = super(TranslationImportView, self).get_context_data(**kwargs)
        rosetta_i18n_lang_name = str(dict(rosetta_settings.ROSETTA_LANGUAGES).get(self.language_id))
        context.update(
            {
                "po_filter": self.po_filter,
                "lang_id": self.kwargs["lang_id"],
                "idx": self.kwargs["idx"],
                "rosetta_i18n_lang_name": rosetta_i18n_lang_name,
                "rosetta_i18n_app": get_app_name(self.po_file_path),
                "rosetta_i18n_write": self.po_file_is_writable,
            }
        )
        return context

    def handle_uploaded_file(self, f):
        with open(self.po_file_path, "wb+") as destination:
            for chunk in f.chunks():
                destination.write(chunk)


class TranslationFileListWithBackupView(TranslationFileListView):
    """
    Třída pohledu pro zobrazení prekladových souboru s backup souborami.
    """

    def get_context_data(self, **kwargs):
        context = super(TranslationFileListView, self).get_context_data(**kwargs)

        third_party_apps = self.po_filter in ("all", "third-party")
        django_apps = self.po_filter in ("all", "django")
        project_apps = self.po_filter in ("all", "project")

        languages = []
        has_pos = False
        for language in rosetta_settings.ROSETTA_LANGUAGES:
            if not can_translate_language(self.request.user, language[0]):
                continue

            po_paths = find_pos_with_backup(
                language[0],
                project_apps=project_apps,
                django_apps=django_apps,
                third_party_apps=third_party_apps,
            )
            po_files = [(get_app_name(lang), os.path.realpath(lang), pofile(lang)) for lang in po_paths]
            po_files.sort(key=lambda app: app[0])
            languages.append((language[0], _(language[1]), po_files))
            has_pos = has_pos or bool(po_paths)

        context["version"] = get_rosetta_version()
        context["languages"] = languages
        context["has_pos"] = has_pos
        context["po_filter"] = self.po_filter
        return context


class TranslationFormWithBackupView(RosettaFileLevelMixinWithBackup, LoginRequiredMixin, TranslationFormView):
    """
    Třída pohledu pro zobrazení formulaře s prekladmi i pro backup soubory
    """

    def get_context_data(self, **kwargs):
        context = super(TranslationFormWithBackupView, self).get_context_data(**kwargs)
        po_filename = self.po_file_path.split("/")[-1]
        context["po_filename"] = po_filename
        context["rosetta_i18n_write"] = self.po_file_is_writable and "_backup_" not in po_filename
        return context


class TranslationFileDownloadBackup(RosettaFileLevelMixinWithBackup, LoginRequiredMixin, TranslationFileDownload):
    """
    Třída pohledu pro stahování prekladových souboru is backup souborami.
    """

    def get(self, request, *args, **kwargs):
        try:
            if len(self.po_file_path.split("/")) >= 5:
                offered_fn = "_".join(self.po_file_path.split("/")[-5:])
            else:
                offered_fn = self.po_file_path.split("/")[-1]
            po_fn = str(self.po_file_path.split("/")[-1])
            mo_fn = str(po_fn.replace(".po", ".mo"))  # Jednoduchá náhrada názvu souboru.
            zipdata = BytesIO()
            with zipfile.ZipFile(zipdata, mode="w") as zipf:
                zipf.writestr(po_fn, str(self.po_file).encode("utf8"))
                abs_path = os.path.abspath(mo_fn)
                if os.path.isfile(abs_path):
                    zipf.writestr(mo_fn, self.po_file.to_binary())
            zipdata.seek(0)

            response = HttpResponse(zipdata.read())
            filename = "filename=%s.%s.zip" % (offered_fn, self.language_id)
            response["Content-Disposition"] = "attachment; %s" % filename
            response["Content-Type"] = "application/x-zip"
            return response
        except Exception as e:
            logger.error(e)
            return HttpResponseRedirect(reverse("rosetta-file-list", kwargs={"po_filter": "project"}))


class TranslationFileSmazatBackup(RosettaFileLevelMixinWithBackup, LoginRequiredMixin, TemplateView):
    """
    Třída pohledu pro smazání backup prekladových souboru.
    """

    template_name = "core/transakce_modal.html"

    def get(self, request, *args, **kwargs):
        context = {
            "object_identification": self.po_file_path.split("/")[-1],
            "title": _("core.views.translationFileSmazatbackup.title.text"),
            "id_tag": "smazat-translation-form",
            "button": _("core.views.translationFileSmazatbackup.submitButton.text"),
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if self.po_file_path.split("/")[-1] == "django.po":
            messages.add_message(self.request, messages.ERROR, TRANSLATION_DELETE_CANNOT_MAIN)
        else:
            try:
                os.remove(self.po_file_path)
                messages.add_message(self.request, messages.SUCCESS, TRANSLATION_DELETE_SUCCESS)
            except Exception as e:
                logger.error(e)
                messages.add_message(self.request, messages.ERROR, TRANSLATION_DELETE_ERROR)
        return JsonResponse({"redirect": reverse("rosetta-file-list", kwargs={"po_filter": "project"})})


class PrometheusMetricsView(IPWhitelistMixin, View):
    """
    Třída pohledu pro zobrazení prometheus metrík doplňena o mixin pro filtrování IP adres.
    """

    def get(self, request, *args, **kwargs):
        return ExportToDjangoView(request)


class ApplicationRestartView(LoginRequiredMixin, View):
    """
    Třída pohledu pro restartovani uwsgi aplikace.
    """

    http_method_names = ["post"]

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        if request.user.hlavni_role.id != ROLE_ADMIN_ID:
            raise PermissionDenied
        try:
            import uwsgi

            uwsgi.reload()  # pretty easy right?
            messages.add_message(self.request, messages.SUCCESS, APPLICATION_RESTART_SUCCESS)
        except Exception as e:
            logger.debug("core.views.ApplicationRestartView.exception", extra={"exception": e})
            messages.add_message(self.request, messages.ERROR, APPLICATION_RESTART_ERROR)
        referer = request.META.get("HTTP_REFERER")
        fallback_url = "/admin"
        if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts=settings.ALLOWED_HOSTS):
            # Validate referer URL
            try:
                validator = URLValidator()
                validator(referer)
            except ValidationError:
                referer = fallback_url
        else:
            referer = fallback_url
        # Redirect to referer or fallback URL
        return redirect(referer)


class DataImportProgress(LoginRequiredMixin, View):
    def get(self, request, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        job_id = kwargs.get("job_id")
        redis_connector = RedisConnector().get_connection_decode()
        try:
            record_count = int(redis_connector.get(f"import_data_count_{job_id}"))
            import_data_progress_files = int(redis_connector.get(f"import_data_progress_files_{job_id}"))
            status_message = redis_connector.get(f"import_data_status_message_{job_id}")
            stopped = redis_connector.get(f"import_data_stop_{job_id}") is not None

            import_data_primary_keys = json.loads(redis_connector.get(f"import_data_primary_keys_{job_id}"))
            serialized_results = json.loads(redis_connector.get(f"import_data_progress_{job_id}"))
            serialized_results_files = json.loads(redis_connector.get(f"import_data_files_{job_id}"))

            progress_data = math.floor((len(serialized_results) / record_count) * 100)
            progress_files = math.floor(import_data_progress_files * 100)
            if progress_data == progress_files == 100:
                status = "finished"
            elif stopped:
                status = "stopped"
            else:
                status = "in_progress"
            progress_response = {
                "record_count": record_count,
                "progress_data": progress_data,
                "progress_files": progress_files,
                "finished_record_count": len(serialized_results),
                "serialized_results": serialized_results,
                "primary_keys": import_data_primary_keys,
                "status": status,
                "serialized_results_files": serialized_results_files,
                "status_message": status_message,
            }
        except (AttributeError, TypeError):
            progress_response = {
                "status": "unknown",
                "status_message": _("core.views.dataImportProgress.unknown_import_status"),
            }
        return JsonResponse(progress_response)


class DataImportStop(LoginRequiredMixin, View):
    def get(self, request, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        job_id = kwargs.get("job_id")
        redis_connector = RedisConnector().get_connection_decode()
        redis_connector.set(f"import_data_stop_{job_id}", 1)
        return JsonResponse({"result": "ok"})


class DataImportStart(LoginRequiredMixin, View):
    def get(self, request, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        job_id = kwargs.get("job_id")
        from cron import tasks

        tasks.run_data_import.delay(job_id, request.user.id)
        return JsonResponse({"result": "ok"})
