import json
import logging
import math
import os
import re
import secrets
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
from core.forms import CheckStavNotChangedForm, RenameSouborForm, TranslationImportForm
from core.ident_cely import get_record_from_ident
from core.message_constants import (
    APPLICATION_RESTART_ERROR,
    APPLICATION_RESTART_SUCCESS,
    DOKUMENT_NEKDO_ZMENIL_STAV,
    PRISTUP_ZAKAZAN,
    PROJEKT_NEKDO_ZMENIL_STAV,
    SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV,
    SOUBOR_NEJVYSSI_SUFFIX_OBSAZEN,
    SOUBOR_SE_NEPOVEDLO_PREJMENOVAT,
    SOUBOR_SUFFIX_OBSAZEN,
    SOUBOR_USPESNE_PREJMENOVAN,
    SPATNY_ZAZNAM_SOUBOR_VAZBA,
    SPATNY_ZAZNAM_ZAZNAM_VAZBA,
    TRANSLATION_DELETE_CANNOT_MAIN,
    TRANSLATION_DELETE_ERROR,
    TRANSLATION_DELETE_SUCCESS,
    TRANSLATION_UPLOAD_SUCCESS,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT_JINA_TRANSAKCE,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_ZMENEN_JINOU_TRANSAKCI,
)
from core.models import AntivirusCheckResult, Soubor
from core.repository_connector import (
    FedoraError,
    FedoraRepositoryConnector,
    FedoraTransaction,
    FedoraTransactionStatus,
    FedoraUpdatedByAnotherTransactionError,
)
from core.soubor_naming import get_dokument_free_suffixes, get_finds_free_suffixes, get_soubor_suffix
from core.utils import (
    SessionIdentifier,
    find_pos_with_backup,
    get_heatmap_pas,
    get_heatmap_pian,
    get_heatmap_project,
    get_list_map_records_in_envelope,
    get_message,
    get_pas_from_envelope,
    get_pian_from_envelope,
    is_maintenance_in_progress,
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
from django.http import (
    FileResponse,
    Http404,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
    StreamingHttpResponse,
)
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
    """
    Zobrazí hlavní stránku aplikace po přihlášení uživatele.

    :param request: HTTP požadavek aktuálního uživatele.

        :return: Vrací výsledek volání ``render()``.
    """
    return render(request, "core/index.html")


@require_http_methods(["POST"])
def delete_file_DZ(request, typ_vazby, ident_cely, pk):
    """
    Smaže soubor nahraný přes dropzone včetně záznamu v databázi i ve Fedora úložišti.

    :param request: HTTP požadavek obsahující session identifikátor dropzone uploadu.
    :param typ_vazby: Typ vazby souboru na doménový objekt (např. dokument, projekt, PAS).
    :param ident_cely: Identifikátor záznamu, ke kterému je soubor navázán.
    :param pk: Primární klíč mazaného souboru.

        :return: Vrací výsledek volání ``JsonResponse()``.
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
    Smaže existující soubor, jeho databázový záznam i binární obsah v repozitáři.

    :param request: HTTP požadavek s metodou GET/POST a případnou návratovou URL.
    :param typ_vazby: Typ vazby souboru na navázaný doménový objekt.
    :param ident_cely: Identifikátor záznamu, u kterého se soubor odstraňuje.
    :param pk: Primární klíč mazaného souboru.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
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


# Zástupná hodnota pro prázdný (bezpísmenný) slot dokumentu – ``ChoiceField`` s ``required=True``
# nepřijímá prázdný řetězec jako platnou volbu, proto se v nabídce reprezentuje sentinelem.
RENAME_BASE_SLOT_VALUE = "__zaklad__"


def _rename_file_safe_redirect(request):
    """
    Vrátí bezpečnou návratovou URL z parametru ``next`` požadavku na přejmenování.

    :param request: HTTP požadavek s parametrem ``next`` v GET nebo POST.
    :return: Bezpečná návratová URL nebo domovská stránka.
    """
    next_url = request.POST.get("next") if request.method == "POST" else request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
        return next_url
    return reverse("core:home")


class _SuffixNoLongerFreeError(Exception):
    """Zvolený suffix byl mezi načtením formuláře a uložením obsazen jiným požadavkem."""


def _rename_file_messages_response(request, message, status=400):
    """
    Vrátí ``JsonResponse`` s frontovanými django zprávami pro AJAX modal (vzor ``delete_file``).

    :param request: HTTP požadavek, do jehož zpráv se přidá chybová hláška.
    :param message: Chybová zpráva k zobrazení uživateli.
    :param status: HTTP status odpovědi.
    :return: ``JsonResponse`` se seznamem zpráv v klíči ``messages``.
    """
    messages.add_message(request, messages.ERROR, message)
    django_messages = [
        {"level": m.level, "message": m.message, "extra_tags": m.tags} for m in messages.get_messages(request)
    ]
    return JsonResponse({"messages": django_messages}, status=status)


@login_required
@require_http_methods(["POST", "GET"])
def rename_file(request, typ_vazby, ident_cely, pk):
    """
    Přejmenuje existující soubor změnou suffixu na volnou povolenou hodnotu.

    Mění název v databázi (``soubor.nazev``), ve Fedoře (``ebucore:filename`` souboru i jeho potomků)
    a vyvolá přegenerování XML metadat navázaného záznamu. Dostupné pro dokumenty (včetně 3D modelů)
    a samostatné nálezy, které mají suffixové schéma názvů.

    :param request: HTTP požadavek s metodou GET (modal) nebo POST (provedení).
    :param typ_vazby: Typ vazby souboru na navázaný doménový objekt.
    :param ident_cely: Identifikátor záznamu, u kterého se soubor přejmenovává.
    :param pk: Primární klíč přejmenovávaného souboru.
    :return: Vrací modal (GET) nebo ``JsonResponse`` s přesměrováním či chybou (POST).
    """
    logger.debug(
        "core.views.rename_file.start",
        extra={"ident_cely": ident_cely, "typ_vazby": typ_vazby, "pk": pk, "method": request.method},
    )
    soubor: Soubor = get_object_or_404(Soubor, pk=pk)
    try:
        check_soubor_vazba(typ_vazby, ident_cely, pk)
    except ZaznamSouborNotmatching as err:
        logger.debug(
            "core.views.rename_file.vazba_error",
            extra={"ident_cely": ident_cely, "typ_vazby": typ_vazby, "pk": pk, "error": err},
        )
        messages.add_message(request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA)
        # POST jde přes AJAX z modalu – ten očekává JSON s přesměrováním, ne HTTP redirect.
        if request.method == "POST":
            return JsonResponse({"redirect": _rename_file_safe_redirect(request)})
        return redirect(_rename_file_safe_redirect(request))

    navazany_objekt = soubor.vazba.navazany_objekt
    base = navazany_objekt.ident_cely.replace("-", "")
    extension = os.path.splitext(soubor.nazev)[1]
    if isinstance(navazany_objekt, Dokument):
        free_suffixes = get_dokument_free_suffixes(navazany_objekt, soubor)
    elif isinstance(navazany_objekt, SamostatnyNalez):
        free_suffixes = get_finds_free_suffixes(navazany_objekt, soubor)
    else:
        logger.warning(
            "core.views.rename_file.unsupported_record",
            extra={"ident_cely": ident_cely, "typ_vazby": typ_vazby, "pk": pk},
        )
        # GET modal se načítá přes AJAX .load() (očekává HTML) – vrátíme redirect; POST očekává JSON.
        if request.method == "POST":
            return _rename_file_messages_response(request, SOUBOR_SE_NEPOVEDLO_PREJMENOVAT)
        return redirect(_rename_file_safe_redirect(request))
    suffix_choices = [(suffix or RENAME_BASE_SLOT_VALUE, f"{base}{suffix}{extension}") for suffix in free_suffixes]

    if request.method == "POST":
        form = RenameSouborForm(request.POST, suffix_choices=suffix_choices)
        if not form.is_valid():
            return _rename_file_messages_response(request, SOUBOR_SUFFIX_OBSAZEN)
        chosen_suffix = form.cleaned_data["suffix"]
        if chosen_suffix == RENAME_BASE_SLOT_VALUE:
            chosen_suffix = ""
        new_nazev = f"{base}{chosen_suffix}{extension}"
        old_nazev = soubor.nazev
        if new_nazev == old_nazev:
            messages.add_message(request, messages.SUCCESS, SOUBOR_USPESNE_PREJMENOVAN)
            return JsonResponse({"redirect": _rename_file_safe_redirect(request)})
        fedora_transaction = FedoraTransaction()
        try:
            with transaction.atomic():
                # Zámek nadřazeného záznamu serializuje souběžná přejmenování; po zamčení znovu
                # ověříme, že zvolený suffix je stále volný (jiný požadavek jej mohl mezitím obsadit).
                type(navazany_objekt).objects.select_for_update().get(pk=navazany_objekt.pk)
                if isinstance(navazany_objekt, Dokument):
                    current_free = get_dokument_free_suffixes(navazany_objekt, soubor)
                else:
                    current_free = get_finds_free_suffixes(navazany_objekt, soubor)
                if chosen_suffix not in current_free:
                    raise _SuffixNoLongerFreeError()
                connector = FedoraRepositoryConnector(navazany_objekt, fedora_transaction)
                connector.update_file_name(soubor, old_nazev, new_nazev)
                soubor.zaznamenej_prejmenovani(request.user, old_nazev, new_nazev)
                soubor.nazev = new_nazev
                soubor.active_transaction = fedora_transaction
                soubor.close_active_transaction_when_finished = True
                soubor.save()
        except _SuffixNoLongerFreeError:
            logger.debug("core.views.rename_file.suffix_taken", extra={"pk": pk, "suffix": chosen_suffix})
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            return _rename_file_messages_response(request, SOUBOR_SUFFIX_OBSAZEN)
        except FedoraUpdatedByAnotherTransactionError as err:
            logger.debug(
                "core.views.rename_file.another_transaction",
                extra={"pk": pk, "error": err, "transaction": fedora_transaction.uid},
            )
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            return _rename_file_messages_response(request, ZAZNAM_ZMENEN_JINOU_TRANSAKCI)
        except FedoraError as err:
            logger.error(
                "core.views.rename_file.fedora_error",
                extra={"pk": pk, "error": err, "transaction": fedora_transaction.uid},
            )
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            return _rename_file_messages_response(request, SOUBOR_SE_NEPOVEDLO_PREJMENOVAT)
        except Exception as err:
            # Neočekávaná chyba (např. IntegrityError nebo chyba v save_metadata): DB se rollbackne
            # přes atomic(), ale otevřenou Fedora transakci musíme uklidit ručně, jinak zůstane viset.
            # Chybu zalogujeme (včetně tracebacku) a uživateli vrátíme hlášku – HTTP 500 by v modalu
            # skončilo jen slepým reloadem bez vysvětlení.
            logger.exception(
                "core.views.rename_file.unexpected_error",
                extra={"pk": pk, "error": err, "transaction": fedora_transaction.uid},
            )
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            return _rename_file_messages_response(request, SOUBOR_SE_NEPOVEDLO_PREJMENOVAT)
        logger.debug(
            "core.views.rename_file.success",
            extra={"pk": pk, "old_nazev": old_nazev, "new_nazev": new_nazev, "transaction": fedora_transaction.uid},
        )
        messages.add_message(request, messages.SUCCESS, SOUBOR_USPESNE_PREJMENOVAN)
        return JsonResponse({"redirect": _rename_file_safe_redirect(request)})

    initial_suffix = get_soubor_suffix(soubor) or RENAME_BASE_SLOT_VALUE
    form = RenameSouborForm(suffix_choices=suffix_choices, initial={"suffix": initial_suffix})
    context = {
        "object": soubor,
        "title": _("core.views.rename_file.title.text") + f" {soubor.nazev}",
        "id_tag": "prejmenovat-soubor-form",
        "button": _("core.views.rename_file.submitButton.text"),
        "form": form,
    }
    return render(request, "core/transakce_modal.html", context)


class DownloadFile(LoginRequiredMixin, View):
    """Implementuje komponentu ``DownloadFile`` v rámci aplikace."""

    thumb_small = False
    thumb_large = False

    def get(self, request, typ_vazby, ident_cely, pk, *args, **kwargs) -> FileResponse | HttpResponse:
        """
        Vrátí požadovaný soubor nebo jeho náhled po ověření vazby k záznamu.

        :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek.
        :param typ_vazby: Typ vazby souboru na doménový záznam.
        :param ident_cely: Identifikátor záznamu, ke kterému soubor patří.
        :param pk: Primární klíč souboru.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.
        :return: Odpověď s obsahem souboru, náhledem nebo redirect při chybě vazby.

            :raises Http404: Vyvolá se v konkrétních chybových větvích této funkce.
        """
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


class DownloadThumbnailDZ(View):
    """
    Třída pohledu pro nahrání miniatury do DropZone při obnovení stránky.
    """

    def get(self, request, typ_vazby, ident_cely, pk, *args, **kwargs) -> FileResponse | HttpResponse:
        """
        Vrátí miniaturu souboru z dočasného uploadu po kontrole oprávnění a vazby.

        :param request: Parametr ``request`` předává se do volání ``SessionIdentifier()``, pracuje se s atributy ``session``, ovlivňuje větvení podmínek.
        :param typ_vazby: Typ vazby souboru na doménový záznam.
        :param ident_cely: Identifikátor záznamu, ke kterému soubor patří.
        :param pk: Primární klíč souboru.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.
        :return: Odpověď s miniaturou souboru.

            :raises PermissionDenied: Vyvolá se při splnění podmínky ``not request.session.get('session_uuid')``; nebo při splnění podmínky ``cache_ident is None or ident_cely != cache_ident or (not file_can_download)``.
            :raises Http404: Vyvolá se v konkrétních chybových větvích této funkce.
        """
        if not request.session.get("session_uuid"):
            raise PermissionDenied
        session_identifier = SessionIdentifier(request)
        cache_ident = session_identifier.get_ident()
        file_can_download = session_identifier.file_exists(pk)
        if cache_ident is None or ident_cely != cache_ident or not file_can_download:
            raise PermissionDenied
        try:
            check_soubor_vazba(typ_vazby, ident_cely, pk)
        except ZaznamSouborNotmatching as e:
            logger.debug(e)
            raise PermissionDenied
        soubor: Soubor = get_object_or_404(Soubor, id=pk)
        if soubor.repository_uuid and soubor.small_thumbnail is not None:
            return soubor.small_thumbnail
        raise Http404


class DownloadThumbnailSmall(DownloadFile):
    """Implementuje komponentu ``DownloadThumbnailSmall`` v rámci aplikace."""

    thumb_small = True


class DownloadThumbnailLarge(DownloadFile):
    """Implementuje komponentu ``DownloadThumbnailLarge`` v rámci aplikace."""

    thumb_large = True


class UpdateFileView(LoginRequiredMixin, TemplateView):
    """Třída pohledu pro zobrazení stránky pro nahrazení souboru."""

    template_name = "core/upload_file.html"

    def get(self, request, *args, **kwargs):
        """
        Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

        :param request: Parametr ``request`` předává se do volání ``error()``, ``get()``, pracuje se s atributy ``GET``, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``get()``.
        """
        typ_vazby = self.kwargs.get("typ_vazby")
        ident_cely = self.kwargs.get("ident_cely")
        file_id = self.kwargs.get("file_id")

        # Získání bezpečné URL pro přesměrování.
        next_url = request.GET.get("next", "core:home")
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
            safe_redirect = next_url
        else:
            safe_redirect = "/"

        # Ověření vazby souboru.
        try:
            check_soubor_vazba(typ_vazby, ident_cely, file_id)
        except ZaznamSouborNotmatching as e:
            logger.debug(e)
            messages.error(request, SPATNY_ZAZNAM_SOUBOR_VAZBA)
            return redirect(safe_redirect)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

        :param request: Parametr ``request`` pracuje se s atributy ``GET``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``redirect()``.
        """
        self.session_identifier.clear_cached_files()
        next_url = request.GET.get("next", "core:home")
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
            safe_redirect = next_url
        else:
            safe_redirect = "/"
        return redirect(safe_redirect)

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super().get_context_data(**kwargs)
        pk_set = self.session_identifier.get_cached_files()
        queryset = Soubor.objects.filter(pk__in=list(pk_set))
        seznam_mock = [obj.getMock() for obj in queryset]
        json_mock = json.dumps(seznam_mock, ensure_ascii=False)
        context["ident_cely"] = self.kwargs.get("ident_cely")
        context["back_url"] = self.request.GET.get("next", "/")
        context["file_id"] = self.kwargs.get("file_id")
        context["typ_vazby"] = self.kwargs.get("typ_vazby")
        context["info_tooltip"] = _("core.upload_file_replace.tooltip")
        context["seznam_mock"] = json_mock
        return context

    def dispatch(self, request, *args, **kwargs):
        """
        Inicializuje identifikaci session pro práci s cache nahraných souborů.

        :param request: Parametr ``request`` předává se do volání ``SessionIdentifier()``, ``dispatch()``, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
        :return: Výsledek standardního zpracování dispatch.
        """
        ident_cely = self.kwargs.get("ident_cely")
        self.session_identifier = SessionIdentifier(request)
        self.session_identifier.set_ident(ident_cely)
        return super().dispatch(request, *args, **kwargs)


class UploadFileView(LoginRequiredMixin, TemplateView):
    """Třída pohledu pro zobrazení stránky s uploadem souboru."""

    template_name = "core/upload_file.html"
    http_method_names = ["get", "post"]

    def get_zaznam(self):
        """
        Načte doménový záznam, ke kterému se budou soubory nahrávat.

        :return: Vrací výsledek volání ``get_object_or_404()``.
        """
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
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

            :return: Vrací proměnná ``context``.
        """
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
        """
        Zpracuje HTTP požadavek na nahrání souboru s ověřením přístupu.

        :param request: HTTP požadavek.
        :param args: Poziční argumenty.
        :param kwargs: Pojmenované argumenty.
        :return: HTTP odpověď.
        """
        ident_cely = self.kwargs.get("ident_cely")
        self.session_identifier = SessionIdentifier(request)
        self.session_identifier.set_ident(ident_cely)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``post``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``redirect()``.
        """
        self.session_identifier.clear_cached_files()
        self.zaznam = self.get_zaznam()
        return redirect(self.zaznam.get_absolute_url())


class BasePostUploadView(View):
    """
    Abstraktní třída pro zpracování nahrávání souborů.

    Poskytuje společnou logiku pro upload nového souboru i nahrazení existujícího souboru.
    Implementuje kompletní workflow pro validaci nahrávaných souborů včetně kontroly MIME typů,
    antivirové kontroly a detekce šifrovaných souborů. Workflow zahrnuje: kontrolu přítomnosti
    souboru, validaci MIME typu a detekci šifrování, antivirovou kontrolu a předání validovaného
    souboru potomkům přes handle_upload(). Potomci musí tuto metodu implementovat.

    :ivar http_method_names: Povolené HTTP metody — pouze POST.
    :ivar source_url: URL zdroje souboru, pokud je specifikována.
    :ivar fedora_transaction: Instance transakce pro práci s Fedora repository.
    :ivar original_filename: Původní název nahrávaného souboru.
    """

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        """
        Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

        Metoda provádí kompletní validaci nahrávaného souboru před jeho uložením:
        - Kontroluje přítomnost souboru v requestu
        - Validuje MIME typ a detekuje šifrované soubory
        - Provádí antivirovou kontrolu obsahu
        - Deleguje finální zpracování na potomky prostřednictvím handle_upload()

        Response Status Codes:
            200: Soubor byl úspěšně validován a zpracován
            400: Validační chyba (chybějící soubor, šifrovaný, virus, neplatný MIME typ)
            500: Neznámá chyba při zpracování

        :param request: Parametr ``request`` předává se do volání ``warning()``, ``handle_upload()``, pracuje se s atributy ``POST``, ``FILES``, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``handle_upload()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``handle_upload()``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``_unknown_error_response()``, výsledek volání ``JsonResponse()``, výsledek volání ``handle_upload()``.
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

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``handle_upload``.
        :param soubor: Nahraný soubor z requestu připravený k uložení.
        :param soubor_data: Binární obsah souboru v objektu ``BytesIO``.
        :param args: Dodatečné poziční argumenty z URL dispatcheru.
        :param kwargs: Dodatečné klíčové argumenty z URL (např. ``ident_cely``).
        :raises NotImplementedError: Pokud potomek metodu nepřepíše.
        """
        raise NotImplementedError

    def _append_duplicate_message(self, response_data, duplikat):
        """
        Přidá informaci o duplicitním souboru do odpovědi.

        Kontroluje, zda v systému již existuje soubor se stejným SHA-512 hashem.
        Pokud ano, přidá do response_data varovnou zprávu s informací o duplicitě
        včetně identifikátoru záznamu, ke kterému je duplicitní soubor připojen.
        :param response_data: Slovník s daty odpovědi, který se případně rozšíří o varování.
        :param duplikat: QuerySet duplicitních souborů podle hashe.
        :return: Upravený slovník odpovědi (beze změny, pokud duplicita není nalezena).
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
        :param response_data: Slovník s daty odpovědi, který se případně doplní o zprávu.
        :param renamed: Parametr ``renamed`` ovlivňuje větvení podmínek.
        :param new_name: Nově přidělený název souboru.
        :return: Upravený slovník odpovědi (beze změny, pokud k přejmenování nedošlo).
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
        :return: JSON odpověď s obecnou chybou a HTTP statusem 500.
        """
        help_translation = _("core.views.post_upload.unknown_error")
        logger.error("core.views.post_upload.unknown_error")
        return JsonResponse({"error": help_translation}, status=500)


class NewFileUploadView(BasePostUploadView):
    """
    Pohled pro nahrání nového souboru k záznamu (projekt, dokument, samostatný nález).

    Zpracovává workflow vytvoření nového souboru: kontrolu oprávnění (vč. anonymního přístupu
    pro projekty), rozlišení typu záznamu, validaci a úpravu přípony podle MIME typu, odstranění
    GPS dat z obrázků, uložení do Fedora repository, vytvoření databázového záznamu s metadaty,
    detekci duplicit podle SHA-512 hashe a zaznamenání události do historie.

    :ivar ident_cely: Identifikátor záznamu, ke kterému má být soubor nahrán.
    :ivar typ_vazby: Typ vazby — ``"projekt"``, ``"dokument"``, ``"model3d"`` nebo ``"pas"``.
    """

    def handle_upload(self, request, soubor, soubor_data, *args, **kwargs):
        """
        Implementuje nahrání nového souboru k záznamu.

        Provádí workflow vytvoření nového souboru včetně kontroly oprávnění,
        generování názvu, uložení do repository a založení databázového záznamu.
        Podporuje anonymní upload pro oznámení a automaticky zpracovává metadata obrázků.

        Response Status Codes:
            200: Soubor úspěšně nahrán
            400: Chyba při nahrávání (transakční konflikt, MIME typ, atd.)
            403: Nedostatečná oprávnění nebo překročen limit souborů
            500: Neexistující záznam nebo jiná interní chyba

        :param request: HTTP request s informacemi o uživateli a session.
        :param soubor: Nahraný soubor z requestu.
        :param soubor_data: Binární obsah souboru.
        :param args: Dodatečné poziční argumenty z URL.
        :param kwargs: Klíčové argumenty včetně ``ident_cely`` a ``typ_vazby``.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, proměnná ``resolved``.
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
        :param request: HTTP request s kontextem aktuálního uživatele.
        :param ident_cely: Úplný identifikátor cílového záznamu.
        :param filename: Původní název nahrávaného souboru.
        :param typ_vazby: Typ vazby (``projekt``, ``dokument``, ``model3d`` nebo ``pas``).
        :return: Při úspěchu dvojice ``(objekt, new_name)``, jinak ``JsonResponse`` s chybou.
        """
        # Mapování typu vazby na oprávnění akce.
        action_map = {
            "projekt": Permissions.actionChoices.soubor_nahrat_projekt,
            "dokument": Permissions.actionChoices.soubor_nahrat_dokument,
            "model3d": Permissions.actionChoices.soubor_nahrat_model3d,
            "pas": Permissions.actionChoices.soubor_nahrat_pas,
        }

        # Kontrola platnosti typu vazby.
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

        # Rozlišení objektu podle typu vazby – dotazy pouze pro relevantní typ.
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
            # Nejvyšší suffix už nelze přidělit. Pokud jsou nižší sloty volné (vznikly přejmenováním
            # či smazáním), poradíme uživateli je uvolnit přejmenováním; jinak je záznam skutečně plný.
            free_suffixes = []
            if typ_vazby in ("dokument", "model3d"):
                free_suffixes = get_dokument_free_suffixes(objekt)
            elif typ_vazby == "pas":
                free_suffixes = get_finds_free_suffixes(objekt)
            if free_suffixes:
                return JsonResponse({"error": str(SOUBOR_NEJVYSSI_SUFFIX_OBSAZEN)}, status=403)
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

        Nahrazuje obsah existujícího souboru, zachovává název (s případnou úpravou
        přípony), aktualizuje repository a zapisuje novou verzi do historie.

        Response Status Codes:
            200: Soubor úspěšně aktualizován
            400: Chyba vazby, transakční konflikt, MIME typ nebo neplatný typ_vazby
            403: Nedostatečná oprávnění k nahrazení souboru
            500: Chybějící vazba nebo jiná interní chyba

        :param request: HTTP request s informacemi o přihlášeném uživateli.
        :param soubor: Nový nahraný soubor z requestu.
        :param soubor_data: Binární obsah nového souboru.
        :param args: Dodatečné poziční argumenty z URL.
        :param kwargs: Klíčové argumenty včetně ``typ_vazby``, ``ident_cely`` a ``file_id``.
        :raises Http404: Pokud soubor s daným ``file_id`` neexistuje.
        :raises ZaznamSouborNotmatching: Pokud soubor nepatří k uvedenému záznamu.

            :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``permission_check``, výsledek volání ``JsonResponse()``, výsledek volání ``_unknown_error_response()``.
        """
        typ_vazby = kwargs.get("typ_vazby")
        ident_cely = kwargs.get("ident_cely")
        file_id = kwargs.get("file_id")
        logger.debug("core.views.post_upload.updating", extra={"pk": file_id, "source_url": self.source_url})

        # Kontrola platnosti typu vazby. a oprávnění
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
            SessionIdentifier(request).add_file_reference(soubor_instance.pk)
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
        :param request: HTTP request s informacemi o přihlášeném uživateli.
        :param typ_vazby: Typ vazby (``dokument``, ``model3d`` nebo ``pas``).
        :param ident_cely: Úplný identifikátor záznamu.
        :param file_id: Primární klíč nahrazovaného souboru.
        :return: ``True`` při úspěchu, jinak ``JsonResponse`` s chybovým popisem.
        """
        # Mapování typu vazby na oprávnění akce.
        # Poznámka: projekt není v mapování – nahrazení souborů projektu není povoleno.
        action_map = {
            "dokument": Permissions.actionChoices.soubor_nahradit_dokument,
            "model3d": Permissions.actionChoices.soubor_nahradit_model3d,
            "pas": Permissions.actionChoices.soubor_nahradit_pas,
        }

        # Kontrola platnosti typu vazby.
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

        # Rozlišení objektu podle typu vazby – dotazy pouze pro relevantní typ.
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

    Název se přiděluje navýšením podle nejvyššího obsazeného suffixu (``F01`` … ``F99``). Toto výchozí
    chování se záměrně nemění – uvolnění či změnu pozice řeší přejmenování souboru.

    :param find: Textový název, klíč nebo výraz ``find`` používaný v rámci operace.
    :param filename: Parametr ``filename`` se předává do volání ``splitext()``, ``warning()``, vstupuje do návratové hodnoty.
    :param add_to_index: Číselná hodnota ``add_to_index`` použitá při výpočtu nebo transformaci.

        :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, bool.
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
    Vygeneruje bezpečný název souboru pro upload do projektu.

    :param projekt: Projekt, ke kterému se soubor nahrává.
    :param file_name: Původní název nahrávaného souboru.

        :return: Vrací hodnotu podle větve zpracování, typicky: bool, hodnotu podle větve zpracování.
    """
    if Soubor.objects.filter(vazba__projekt_souboru=projekt).count() >= MAX_POCET_SOUBORU_PROJEKTU:
        return False
    split_file = os.path.splitext(file_name)
    nfkd_form = unicodedata.normalize("NFKD", split_file[0])
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return re.sub("[^A-Za-z0-9_]", "_", only_ascii) + split_file[1]
    # Potřebné odstranit omezení `soubor_filepath_key`.


def check_stav_changed(request, zaznam, prefix=None):
    """
    Ověří, zda se stav záznamu mezitím změnil oproti hodnotě odeslané ve formuláři.

    :param request: Parametr ``request`` předává se do volání ``CheckStavNotChangedForm()``, ``add_message()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek.
    :param zaznam: Ukládaný záznam, jehož stav se porovnává.
    :param prefix: Volitelný prefix formuláře použitý při renderování, nutný pro správné načtení ``old_stav`` z POST dat.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
    """
    logger.debug("core.views.check_stav_changed.start", extra={"pk": zaznam.pk})
    if request.method == "POST":
        form_check = CheckStavNotChangedForm(data=request.POST, db_stav=zaznam.stav, prefix=prefix)
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
    Přesměruje uživatele na detail záznamu nalezeného podle identifikátoru.
    Pokud identifikátor není nalezen mezi aktuálními, pokusí se hledat mezi dočasnými v historii.

    :param request: Parametr ``request`` předává se do volání ``redirect()``, ``get_absolute_url()``, vstupuje do návratové hodnoty.
    :param ident_cely: Hledaný identifikátor záznamu.

        :return: Vrací výsledek volání ``redirect()``.
    """
    try:
        object = get_record_from_ident(ident_cely)
    except Http404:
        # Záznamy přejmenování ukládají poznamka ve formátu "starý_ident -> nový_ident". Hledáme "ident_cely ->"
        # abychom zachytili pouze záznamy, kde ident_cely byl zdrojový ident a vyloučili shody,
        # kde se ident vyskytuje jako cílový ident nebo v jiném kontextu.
        # order_by() odstraňuje výchozí řazení; [:1] zabrání zbytečnému načítání dalších řádků. Nejedná se o bug.
        h = next(
            iter(
                Historie.objects.select_related("vazba").filter(poznamka__icontains=f"{ident_cely} ->").order_by()[:1]
            ),
            None,
        )
        object = h.vazba.navazany_objekt if h and h.vazba else None
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
    Vrátí zbývající čas relace pro AJAX prodloužení přihlášení.

    :param request: Parametr ``request`` předává se do volání ``seconds_until_idle_time_end()``.

        :return: Vrací výsledek volání ``JsonResponse()``.
    """
    options = getattr(settings, "AUTO_LOGOUT")
    current_time = now()
    session_time = seconds_until_idle_time_end(request, options["IDLE_TIME"], current_time)
    return JsonResponse(
        {"session_time": session_time},
        status=200,
    )


class ExportMixinDate(ExportMixin):
    """Mixin pro získaní názvu exportovaného souboru."""

    def get_export_filename(self, export_format, export_name=None):
        """
        Sestaví název exportního souboru s časovým razítkem.

        :param export_format: Cílový formát exportu (např. ``csv``, ``xlsx``).
        :param export_name: Volitelný základ názvu; pokud není zadán, použije ``self.export_name``.

            :return: Vrací výsledek volání ``format()``.
        """
        if export_name is None:
            export_name = self.export_name
        now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        return "{}{}.{}".format(export_name, now, export_format)


class PermissionFilterMixin:
    """Implementuje komponentu ``PermissionFilterMixin`` v rámci aplikace."""

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
        """
        Ověří filter permission.

        :param qs: Parametr ``qs`` předává se do volání ``filter_by_permission()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
        :param action: Identifikátor akce, která se má provést.

            :return: Vrací proměnná ``qs``.
        """
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
        """
        Filtruje by permission.

        :param qs: Parametr ``qs`` předává se do volání ``filter()``, ``add_ownership_lookup()``, pracuje se s atributy ``annotate``, ``none``, vstupuje do návratové hodnoty.
        :param permission: Parametr ``permission`` předává se do volání ``filter()``, ``add_status_lookup()``, pracuje se s atributy ``base``, ``status``, ovlivňuje větvení podmínek.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``none()``, proměnná ``qs``.
        """
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
        """
        Provádí operaci add status lookup.

        :param permission: Parametr ``permission`` předává se do volání ``sub()``, pracuje se s atributy ``status``.

            :return: Vrací proměnná ``filterdoc``.
        """
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
        """
        Provádí operaci add ownership lookup.

        :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
        :param qs: Parametr ``qs`` slouží jako vstup pro logiku funkce ``add_ownership_lookup``.

            :return: Vrací výsledek volání ``Q()``.
        """
        filter_historie = {"uzivatel": self.request.user}
        filtered_my = Historie.objects.filter(**filter_historie)
        if ownership == Permissions.ownershipChoices.our:
            filter_historie = {"uzivatel__organizace": self.request.user.organizace}
            filtered_our = Historie.objects.filter(**filter_historie)
            return Q(**{"historie_zapsat__in": filtered_our})
        else:
            return Q(**{"historie_zapsat__in": filtered_my})

    def add_accessibility_lookup(self, permission, qs):
        """
        Provádí operaci add accessibility lookup.

        :param permission: Parametr ``permission`` předává se do volání ``filter()``, ``add_ownership_lookup()``, pracuje se s atributy ``accessibility``, vstupuje do návratové hodnoty.
        :param qs: Parametr ``qs`` předává se do volání ``filter()``, ``add_ownership_lookup()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``filter()``.
        """
        accessibility_key = self.permission_model_lookup + "pristupnost__in"
        accessibilities = Heslar.objects.filter(
            nazev_heslare=HESLAR_PRISTUPNOST, id__in=self.group_to_accessibility.get(self.request.user.hlavni_role.id)
        )
        filter = {accessibility_key: accessibilities}
        return qs.filter(Q(**filter) | self.add_ownership_lookup(permission.accessibility, qs))


class SearchListView(ExportMixin, LoginRequiredMixin, SingleTableMixin, FilterView, PermissionFilterMixin):
    """Třída pohledu pro tabulky záznamů, která je použita jako základ pro jednotlivé pohledy."""

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
    map_enabled = False
    map_layer = None  # "pas" | "projekt" | "akce" | "lokalita" | "3d"

    def create_export(self, export_format):
        """
        Vytvoří export výsledků vyhledávání v požadovaném formátu.

        :param export_format: Parametr ``export_format`` předává se do volání ``debug()``, ovlivňuje větvení podmínek.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``HttpResponse()``, proměnná ``response``.
        """
        from redis import Redis

        def check_if_aborted(r_inner: Redis, key_inner: str):
            """
            Ověří if aborted.

            :param r_inner: Parametr ``r_inner`` pracuje se s atributy ``get``, ``delete``.
            :param key_inner: Textový název nebo klíč ``key_inner`` používaný v rámci operace.

                :return: Vrací proměnná ``aborted``.
            """
            aborted = r_inner.get(key_inner + "_stat") == "-1"
            if aborted:
                r_inner.delete(key_inner)
            return aborted

        def update_progress_bar(r_inner: Redis, key_inner: str, new_value: int, message: str):
            """
            Aktualizuje progress bar.

            :param r_inner: Parametr ``r_inner`` se předává do volání ``check_if_aborted()``, pracuje se s atributy ``set``, vstupuje do návratové hodnoty.
            :param key_inner: Textový název nebo klíč ``key_inner`` používaný v rámci operace.
            :param new_value: Parametr ``new_value`` se předává do volání ``set()``, ``dumps()``.
            :param message: Parametr ``message`` předává se do volání ``set()``, ``dumps()``.

                :return: Vrací výsledek volání ``check_if_aborted()``.
            """
            r_inner.set(key_inner, json.dumps({"percent": int(new_value), "text": message}), ex=3600)
            return check_if_aborted(r_inner, key_inner)

        def file_iterator(content, r, redis_variable_name, chunk_size=8192):
            """
            Provádí operaci file iterator.

            :param content: Textový nebo strukturální vstup `content` používaný při sestavení nebo zpracování obsahu.
            :param r: Parametr ``r`` se předává do volání ``update_progress_bar()``, pracuje se s atributy ``delete``.
            :param redis_variable_name: Textový název nebo klíč ``redis_variable_name`` používaný v rámci operace.
            :param chunk_size: Parametr ``chunk_size`` se předává do volání ``range()``, ovlivňuje větvení podmínek.

                :raises Exception: Vyvolá se při zpracování zachycené výjimky typu ``Exception``.
            """
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
            data = self.postprocess_export_dataframe(data)
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

    def postprocess_export_dataframe(self, df):
        """
        Hook pro post-processing exportního DataFrame před přejmenováním sloupců.

        Metoda je volána v ``create_export`` po sestavení DataFramu z Redis snapshotů
        a po aplikaci ``filtered_column_order``, ale před přejmenováním sloupců na verbose names.
        Sloupce jsou v tuto chvíli identifikovány strojovými názvy (shodné s názvy v tabulce).

        Výchozí implementace vrací DataFrame beze změny. Podtřídy mohou přepsat tuto metodu
        pro aplikaci oprávnění nebo jiné úpravy dat.

        :param df: DataFrame sestavený z Redis snapshotů se strojovými názvy sloupců.
        :return: Upravený (nebo nezměněný) DataFrame.
        """
        return df

    def init_translations(self):
        """Provádí operaci init translations."""
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
        """
        Vrací sort params.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        sort_params = self.request.GET.getlist("sort")
        return sort_params

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
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
        context["map_enabled"] = self.map_enabled
        context["map_layer"] = self.map_layer
        context["map_data_url"] = (
            reverse("core:post_ajax_get_list_map_data", args=[self.map_layer]) if self.map_enabled else ""
        )
        return context

    #: Horní mez součinu počtů hodnot vícehodnotových GET parametrů, do které se ještě
    #: zapíná cacheops cache. Způsob výpočtu a zdůvodnění viz ``_is_query_cacheable``.
    cache_filter_value_product_limit = 1000

    def _is_query_cacheable(self):
        """
        Vrací, zda je bezpečné zapnout cacheops cache pro aktuální filtr.

        cacheops sestavuje invalidační schéma (DNF) jako kartézský součin hodnot napříč
        vícehodnotovými filtry, takže rozsáhlé kombinace vedou k milionům konjunkcí a
        k vyčerpání paměti (OOM) při výpočtu ``cacheops.tree.dnfs``. Motivací jsou hluboké
        M2M filtry (předměty a objekty komponent), kontrola ale platí pro libovolný
        vícehodnotový GET parametr.

        Jako míra slouží součin počtů hodnot vícehodnotových GET parametrů. Jde
        o konzervativní odhad řádové velikosti DNF na základě multiplicity GET parametrů,
        nikoli o přímé měření struktury querysetu. Předpokládá se, že filtry odesílají
        každou hodnotu jako samostatný výskyt parametru (``?pole=1&pole=2``), jak to dělá
        ``forms.SelectMultiple``. Filtr, který by více hodnot kódoval do jednoho parametru
        (například oddělené čárkou), by tato kontrola nezachytila.

        Do součinu se nezapočítávají parametry stránkování, řazení a CSRF token
        (``page``, ``sort``, ``per_page``, ``csrfmiddlewaretoken``).

        :return: ``True`` pokud součin nepřekročí ``cache_filter_value_product_limit``.
        """
        ignored = {"page", "sort", "per_page", "csrfmiddlewaretoken"}
        product = 1
        for key in self.request.GET:
            if key in ignored:
                continue
            count = len(self.request.GET.getlist(key))
            if count > 1:
                product *= count
                if product > self.cache_filter_value_product_limit:
                    logger.debug(
                        "core.views.SearchListView._is_query_cacheable.cache_skipped",
                        extra={
                            "key": key,
                            "product": product,
                            "limit": self.cache_filter_value_product_limit,
                        },
                    )
                    return False
        return True

    def get_queryset(self):
        """
        Vrací queryset výsledků vyhledávání podle zadaných filtrů.

        Cacheops cache se zapíná pouze pro filtry, které projdou kontrolou
        ``_is_query_cacheable``. U rozsáhlých kombinací hodnot dotaz proběhne bez cache.

        :return: Vrací proměnná ``qs``.
        """
        qs = super().get_queryset()
        if self._is_query_cacheable():
            qs.cache()
        return qs

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        """
        Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

        :param request: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``get()``.
        """
        return super().get(request, *args, **kwargs)


class StahnoutDataHistorickaView(LoginRequiredMixin, View):
    """Třída pohledu pro stažení historické verze souboru nebo metadat z Fedory"""

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
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
        :param model_name: Název modelu používaný pro cílení operace.
        :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get()``.
        :param timestamp: Časový údaj použitý při filtrování nebo výpočtu.

            :return: Vrací proměnná ``response``.
            :raises Http404: Vyvolá se při splnění podmínky ``Model is None``.
        """
        Model = self.MODEL_MAP.get(model_name)
        if Model is None:
            raise Http404

        def context_processor(content):
            """
            Provádí operaci context processor.

            :param content: Textový nebo strukturální vstup `content` používaný při sestavení nebo zpracování obsahu.
            """
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
    """Implementuje komponentu ``CheckUserAuthentication`` v rámci aplikace."""

    def get(self, request, *args, **kwargs):
        """
        Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

        :param request: Parametr ``request`` předává se do volání ``JsonResponse()``, pracuje se s atributy ``user``, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        return JsonResponse({"is_authenticated": request.user.is_authenticated})


@login_required
@require_http_methods(["POST"])
def post_ajax_get_pas_and_pian_limit(request):
    """
    Funkce pohledu pro získaní heatmapy.

    :param request: Parametr ``request`` se předává do volání ``loads()``, ``get_pas_from_envelope()``, pracuje se s atributy ``body``.

        :return: Vrací výsledek volání ``JsonResponse()``.
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


@login_required
@require_http_methods(["POST"])
def post_ajax_get_list_map_data(request, layer):
    """
    Funkce pohledu pro datovou vrstvu mapy v záložce filtru výpisu.

    Vrací prvky daného workflow (``layer``) v aktuálním výřezu mapy ve stejném kontraktu jako
    :func:`post_ajax_get_pas_and_pian_limit` – tj. ``{"points"|"heat", "algorithm", "count"}`` –
    aby klient mohl znovupoužít stávající vykreslování. Nad ``LIMIT_PRVKU_ZOBRAZENI_HEATMAP`` se
    přepíná na heatmapu. Vrstva je pouze orientační; vlastní filtrování tabulky zajišťuje
    serverový filtr ``geom_filter``.

    :param request: HTTP požadavek s tělem ``{"bounds": {...}, "zoom": int}``.
    :param layer: Identifikátor datové vrstvy (``"pas"`` | ``"projekt"`` | ``"akce"`` | ``"lokalita"`` | ``"3d"``).

        :return: Vrací výsledek volání ``JsonResponse()``.
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
        bounds = body["bounds"]
        zoom = body["zoom"]
        params = [
            bounds["topLeft"]["lng"],
            bounds["bottomLeft"]["lat"],
            bounds["bottomRight"]["lng"],
            bounds["topRight"]["lat"],
            zoom,
        ]
        base_qs, type_label, geom_field = get_list_map_records_in_envelope(layer, bounds, request)
    except (json.JSONDecodeError, KeyError, TypeError):
        return JsonResponse({"error": "Invalid request body"}, status=400)
    if base_qs is None:
        logger.warning("core.views.post_ajax_get_list_map_data.unknown_layer", extra={"layer": layer})
        return JsonResponse({"points": [], "algorithm": "detail", "count": 0}, status=200)

    points_qs = base_qs.values("ident_cely", type=Value(type_label)).annotate(geom=AsWKT(geom_field))
    num = points_qs.count()

    if layer == "3d" or num < LIMIT_PRVKU_ZOBRAZENI_HEATMAP:
        return JsonResponse({"points": list(points_qs), "algorithm": "detail", "count": num}, status=200)

    if layer == "pas":
        heats = get_heatmap_pas(*params)
        back = [
            {"id": str(cid), "pocet": heat["count"], "geom": heat["geometry"].replace(", ", ",")}
            for cid, heat in enumerate(heats, start=1)
        ]
    elif layer in ("akce", "lokalita"):
        heats = get_heatmap_pian(*params)
        back = [
            {"id": str(cid), "pocet": heat["count"], "geom": heat["geometry"].replace(", ", ",")}
            for cid, heat in enumerate(heats, start=1)
        ]
    else:  # projekt
        lngs = [bounds[c]["lng"] for c in ("topLeft", "topRight", "bottomRight", "bottomLeft")]
        lats = [bounds[c]["lat"] for c in ("topLeft", "topRight", "bottomRight", "bottomLeft")]
        west, east = min(lngs), max(lngs)
        south, north = min(lats), max(lats)
        heats = get_heatmap_project(east, north, west, south, zoom) or []
        back = [
            {
                "id": str(cid),
                "pocet": heat["pocet"],
                "geom": "POINT({} {})".format(*json.loads(heat["geom_geojson"])["coordinates"]),
            }
            for cid, heat in enumerate(heats, start=1)
        ]
    return JsonResponse({"heat": back, "algorithm": "heat", "count": len(back)}, status=200)


def check_soubor_vazba(typ_vazby, ident, id_zaznamu):
    """
    Ověří soubor vazba.

    :param typ_vazby: Parametr ``typ_vazby`` ovlivňuje větvení podmínek.
    :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.
    :param id_zaznamu: Parametr ``id_zaznamu`` předává se do volání ``filter()``.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        :raises ZaznamSouborNotmatching: Vyvolá se při splnění podmínky ``soubor.count() > 0``.
    """
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
    """Implementuje komponentu ``ReadTempValueView`` v rámci aplikace."""

    def get(self, request):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` pracuje se s atributy ``GET``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
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
            # Vrátí JSON odpověď se stavem 403 (zakázáno).
            return JsonResponse({"error": "Access to 'export_' prefixed keys is forbidden"}, status=403)


class DeleteTempValueView(View):
    """Implementuje komponentu ``DeleteTempValueView`` v rámci aplikace."""

    def get(self, request):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` pracuje se s atributy ``GET``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        r = RedisConnector.get_connection()
        temp_name = request.GET.get("temp_name", "")
        if temp_name.startswith("export_"):
            r.delete(temp_name)
            logger.debug("core.views.ResetTempValueView.get.result", extra={"value": temp_name})
            return JsonResponse({"result": "success"})
        else:
            # Vrátí JSON odpověď se stavem 403 (zakázáno).
            return JsonResponse({"error": "Access to 'export_' prefixed keys is forbidden"}, status=403)


class AbortDownloadUpdateTempValueView(View):
    """Implementuje komponentu ``AbortDownloadUpdateTempValueView`` v rámci aplikace."""

    def get(self, request):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` pracuje se s atributy ``GET``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        r = RedisConnector.get_connection()
        temp_name = request.GET.get("temp_name", "")
        if temp_name.startswith("export_"):
            r.set(temp_name + "_stat", -1, ex=3500)
            logger.debug("core.views.AbortDownloadUpdateTempValueView.get.result", extra={"value": temp_name})
            return JsonResponse({"result": "success"})
        else:
            # Vrátí JSON odpověď se stavem 403 (zakázáno).
            return JsonResponse({"error": "Access to 'export_' prefixed keys is forbidden"}, status=403)


class RosettaFileLevelMixinWithBackup(RosettaFileLevelMixin):
    """Třída podledu pro práci s prekladmi doplnena o backup osubory."""

    @cached_property
    def po_file_path(self):
        """
        Podle URL parametrů `kwargs` odvodí a vrátí cestu k `.po` souboru,

        který se má zobrazit nebo upravit.

        Pokud soubor neexistuje, vyvolá chybu 404.

            :return: Vrací proměnná ``path``.
            :raises Http404: Vyvolá se při zpracování zachycené výjimky typu ``IndexError``.
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
    """Třída pohledu pro import překladových souborů."""

    template_name = "rosetta/import_form.html"
    form_class = TranslationImportForm

    def form_valid(self, form):
        """
        Provádí operaci form valid.

        :param form: Parametr ``form`` pracuje se s atributy ``cleaned_data``.

            :return: Vrací výsledek volání ``redirect()``.
        """
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
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
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
        """
        Zpracuje uploaded file.

        :param f: Pomocný stream/objekt používaný interně funkcí.
        """
        with open(self.po_file_path, "wb+") as destination:
            for chunk in f.chunks():
                destination.write(chunk)


class TranslationFileListWithBackupView(TranslationFileListView):
    """Třída pohledu pro zobrazení prekladových souboru s backup souborami."""

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
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
    """Třída pohledu pro zobrazení formulaře s prekladmi i pro backup soubory"""

    def get_context_data(self, **kwargs):
        """
        Vrací context data.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

            :return: Vrací proměnná ``context``.
        """
        context = super(TranslationFormWithBackupView, self).get_context_data(**kwargs)
        po_filename = self.po_file_path.split("/")[-1]
        context["po_filename"] = po_filename
        context["rosetta_i18n_write"] = self.po_file_is_writable and "_backup_" not in po_filename
        return context


class TranslationFileDownloadBackup(RosettaFileLevelMixinWithBackup, LoginRequiredMixin, TranslationFileDownload):
    """Třída pohledu pro stahování prekladových souboru is backup souborami."""

    def get(self, request, *args, **kwargs):
        """
        Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

            :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``response``, výsledek volání ``HttpResponseRedirect()``.
        """
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
    """Třída pohledu pro smazání backup prekladových souboru."""

    template_name = "core/transakce_modal.html"

    def get(self, request, *args, **kwargs):
        """
        Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

            :return: Vrací výsledek volání ``render_to_response()``.
        """
        context = {
            "object_identification": self.po_file_path.split("/")[-1],
            "title": _("core.views.translationFileSmazatbackup.title.text"),
            "id_tag": "smazat-translation-form",
            "button": _("core.views.translationFileSmazatbackup.submitButton.text"),
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``post``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
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
    Třída pohledu pro zobrazení prometheus metrik doplněna o mixin pro filtrování IP adres.
    """

    def get(self, request, *args, **kwargs):
        """
        Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

        :param request: Parametr ``request`` předává se do volání ``ExportToDjangoView()``, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

            :return: Vrací výsledek volání ``ExportToDjangoView()``.
        """
        return ExportToDjangoView(request)


class ApplicationRestartView(LoginRequiredMixin, View):
    """Třída pohledu pro restartovani uwsgi aplikace."""

    http_method_names = ["post"]

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        """
        Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

        :param request: Parametr ``request`` pracuje se s atributy ``user``, ``META``, ovlivňuje větvení podmínek.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``redirect()``.
            :raises PermissionDenied: Vyvolá se při splnění podmínky ``request.user.hlavni_role.id != ROLE_ADMIN_ID``.
        """
        if request.user.hlavni_role.id != ROLE_ADMIN_ID:
            raise PermissionDenied
        try:
            import uwsgi

            uwsgi.reload()  # Jednoduché volání restartu aplikace.
            messages.add_message(self.request, messages.SUCCESS, APPLICATION_RESTART_SUCCESS)
        except Exception as e:
            logger.debug("core.views.ApplicationRestartView.exception", extra={"exception": e})
            messages.add_message(self.request, messages.ERROR, APPLICATION_RESTART_ERROR)
        referer = request.META.get("HTTP_REFERER")
        fallback_url = "/admin"
        if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts=settings.ALLOWED_HOSTS):
            # Ověření referenční URL.
            try:
                validator = URLValidator()
                validator(referer)
            except ValidationError:
                referer = fallback_url
        else:
            referer = fallback_url
        # Přesměrování na referer nebo záložní URL.
        return redirect(referer)


class DataImportProgress(LoginRequiredMixin, View):
    """Implementuje komponentu ``DataImportProgress`` v rámci aplikace."""

    def get(self, request, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
        :param kwargs: Parametr ``kwargs`` pracuje se s atributy ``get``.

            :return: Vrací výsledek volání ``JsonResponse()``.
            :raises PermissionDenied: Vyvolá se při splnění podmínky ``not request.user.is_superuser``.
        """
        if not request.user.is_superuser:
            raise PermissionDenied
        job_id = kwargs.get("job_id")
        redis_connector = RedisConnector().get_connection_decode()
        try:
            record_count_raw = redis_connector.get(f"import_data_count_{job_id}") or 0
            record_count = int(record_count_raw)
            import_data_progress_files = int(redis_connector.get(f"import_data_progress_files_{job_id}") or 0)
            status_message = redis_connector.get(f"import_data_status_message_{job_id}")
            stopped = redis_connector.get(f"import_data_stop_{job_id}") is not None

            import_data_primary_keys = json.loads(redis_connector.get(f"import_data_primary_keys_{job_id}") or "{}")
            progress_ids = redis_connector.lrange(f"import_data_progress_ids_{job_id}", 0, -1)
            progress_details = redis_connector.lrange(f"import_data_progress_details_{job_id}", 0, -1)
            serialized_results = dict(zip(progress_ids, progress_details))
            serialized_results_files = json.loads(redis_connector.get(f"import_data_files_{job_id}") or "[]")
            import_history_record_result = json.loads(
                redis_connector.get(f"import_data_history_record_result_{job_id}") or "{}"
            )
            import_fedora_update_result = json.loads(redis_connector.get(f"import_fedora_result_{job_id}") or "{}")

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
                "history_record_result": import_history_record_result,
                "fedora_update_result": import_fedora_update_result,
                "status": status,
                "serialized_results_files": serialized_results_files,
                "status_message": status_message or _("core.templates.admin.import_data.starting"),
            }
        except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
            progress_response = {
                "status": "unknown",
                "status_message": _("core.views.dataImportProgress.unknown_import_status"),
            }
        return JsonResponse(progress_response)


class DataImportStop(LoginRequiredMixin, View):
    """Implementuje komponentu ``DataImportStop`` v rámci aplikace."""

    def get(self, request, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
        :param kwargs: Parametr ``kwargs`` pracuje se s atributy ``get``.

            :return: Vrací výsledek volání ``JsonResponse()``.
            :raises PermissionDenied: Vyvolá se při splnění podmínky ``not request.user.is_superuser``.
        """
        if not request.user.is_superuser:
            raise PermissionDenied
        job_id = kwargs.get("job_id")
        redis_connector = RedisConnector().get_connection_decode()
        redis_connector.set(f"import_data_stop_{job_id}", 1)
        return JsonResponse({"result": "ok"})


class DataImportProgressReportView(LoginRequiredMixin, View):
    """Exportuje výsledky importu dat jako soubor Excel."""

    def get(self, request, **kwargs):
        """
        Sestaví a vrátí Excel report s výsledky validace a průběhu importu.

        :param request: HTTP požadavek, ověřuje se právo superuživatele.
        :param kwargs: Obsahuje ``job_id`` identifikující danou importní úlohu.
        :return: Soubor Excel (``application/vnd.openxmlformats-officedocument.spreadsheetml.sheet``) ke stažení.
        :raises PermissionDenied: Vyvolá se, pokud přihlášený uživatel není superuživatel.
        """
        if not request.user.is_superuser:
            raise PermissionDenied
        job_id = kwargs.get("job_id")
        redis_connector = RedisConnector().get_connection_decode()

        validation_results = json.loads(redis_connector.get(f"import_data_validation_results_{job_id}") or "[]")
        primary_keys = json.loads(redis_connector.get(f"import_data_primary_keys_{job_id}") or "{}")
        progress_ids = redis_connector.lrange(f"import_data_progress_ids_{job_id}", 0, -1)
        progress_details = redis_connector.lrange(f"import_data_progress_details_{job_id}", 0, -1)
        serialized_results = dict(zip(progress_ids, progress_details))
        history_record_result = json.loads(redis_connector.get(f"import_data_history_record_result_{job_id}") or "{}")
        fedora_update_result = json.loads(redis_connector.get(f"import_fedora_result_{job_id}") or "{}")

        def build_row(item):
            """
            Sestaví řádek reportu z jednoho záznamu výsledku validace.

            :param item: Slovník s daty validačního výsledku záznamu importu.
            :return: Slovník s přeloženými názvy sloupců a hodnotami pro export do Excelu.
            """
            i = item["item_order"]
            return {
                _("core.templates.admin.import_data.import_order"): i + 1,
                _("core.templates.admin.import_data.fila_name"): item.get("file_name", ""),
                _("core.templates.admin.import_data.primary_key_import"): item.get("primary_key_import", ""),
                _("core.templates.admin.import_data.primary_key_database"): primary_keys.get(str(i), ""),
                _("core.templates.admin.validation_result"): item.get("validation_result", ""),
                _("core.templates.admin.status"): serialized_results.get(str(i), ""),
                _("core.templates.admin.import_data.history_record_result"): history_record_result.get(str(i), ""),
                _("core.templates.admin.import_data.fedora_update_result"): ", ".join(
                    fedora_update_result.get(str(i), [])
                ),
            }

        rows = [build_row(item) for item in validation_results]

        df = pandas.DataFrame(rows)
        output = BytesIO()
        with pandas.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Import")
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="import_report_{job_id}.xlsx"'
        return response


class DataImportStart(LoginRequiredMixin, View):
    """Implementuje komponentu ``DataImportStart`` v rámci aplikace."""

    def post(self, request, **kwargs):
        """
        Spustí Celery task pro import dat.

        :param request: Parametr ``request`` předává se do volání ``delay()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
        :param kwargs: Parametr ``kwargs`` pracuje se s atributy ``get``.

            :return: Vrací výsledek volání ``JsonResponse()``.
            :raises PermissionDenied: Vyvolá se při splnění podmínky ``not request.user.is_superuser``.
        """
        if not request.user.is_superuser:
            raise PermissionDenied
        if not is_maintenance_in_progress():
            return JsonResponse(
                {
                    "result": "error",
                    "status_message": _("core.templates.admin.import_data.not_maintenance"),
                },
                status=403,
            )
        job_id = kwargs.get("job_id")
        from cron import tasks

        redis_connector = RedisConnector.get_connection_decode()
        if redis_connector.get(f"import_data_valid_{job_id}") != "1":
            return JsonResponse(
                {
                    "result": "error",
                    "status_message": _("core.templates.admin.import_data.invalid_records"),
                },
                status=422,
            )
        lock_token = secrets.token_hex(16)
        if not RedisConnector.acquire_import_lock(redis_connector, lock_token, tasks.IMPORT_DATA_RUNNING_TTL_SECONDS):
            return JsonResponse(
                {
                    "result": "already_running",
                    "status_message": _("core.templates.admin.import_data.import_is_running"),
                },
                status=409,
            )
        try:
            tasks.run_data_import.delay(job_id, request.user.id, lock_token)
        except Exception:
            RedisConnector.release_import_lock(redis_connector, lock_token)
            raise
        return JsonResponse({"result": "ok"})
