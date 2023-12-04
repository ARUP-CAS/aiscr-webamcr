import json
import html
import logging
import mimetypes
import os
import re
from io import StringIO, BytesIO
from PIL import Image

import unicodedata
from django.core.files.uploadedfile import TemporaryUploadedFile
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import TemplateView



from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse, StreamingHttpResponse, FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django_auto_logout.utils import now, seconds_until_idle_time_end

from adb.models import Adb, VyskovyBod
from arch_z.models import ArcheologickyZaznam
from core.constants import (
    D_STAV_ARCHIVOVANY,
    DOKUMENT_RELATION_TYPE,
    PROJEKT_RELATION_TYPE,
    PROJEKT_STAV_ARCHIVOVANY,
    ROLE_ADMIN_ID,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
    SN_ARCHIVOVANY,
    ROLE_BADATEL_ID, 
    ROLE_ARCHEOLOG_ID, 
    ROLE_ARCHIVAR_ID
)
from core.forms import CheckStavNotChangedForm
from core.message_constants import (
    DOKUMENT_NEKDO_ZMENIL_STAV,
    PROJEKT_NEKDO_ZMENIL_STAV,
    SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV,
    SPATNY_ZAZNAM_ZAZNAM_VAZBA,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_USPESNE_SMAZAN,
)
from core.models import Soubor
from core.repository_connector import RepositoryBinaryFile, FedoraRepositoryConnector
from core.utils import (
    calculate_crc_32,
    get_mime_type,
    get_multi_transform_towgs84,
    get_transform_towgs84,
    get_message,
)
from dokument.models import Dokument, get_dokument_soubor_name
from ez.models import ExterniZdroj
from pas.models import SamostatnyNalez
from pian.models import Pian
from projekt.models import Projekt
from uzivatel.models import User
from django_tables2.export import ExportMixin
from datetime import datetime
from heslar.hesla import HESLAR_PRISTUPNOST

from heslar.models import Heslar
from .exceptions import ZaznamSouborNotmatching
from .models import Permissions, PermissionsSkip
from historie.models import Historie

from core.ident_cely import get_record_from_ident
from core.models import Permissions
from historie.models import Historie
from heslar.hesla_dynamicka import PRISTUPNOST_BADATEL_ID, PRISTUPNOST_ARCHEOLOG_ID, PRISTUPNOST_ARCHIVAR_ID, PRISTUPNOST_ANONYM_ID

from core.utils import (
    get_num_pass_from_envelope,
    get_num_pian_from_envelope,
    get_pas_from_envelope,
    get_pian_from_envelope,
    get_heatmap_pas,
    get_heatmap_pas_density,
    get_heatmap_pian,
)

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def index(request):
    "Funkce podledu pro zobrazení hlavní stránky."
    return render(request, "core/index.html")


@login_required
@require_http_methods(["POST", "GET"])
def delete_file(request, typ_vazby, ident_cely, pk):
    """
    Funkce pohledu pro smazání souboru. Funkce maže jak záznam v DB tak i soubor na disku.
    """
    s = get_object_or_404(Soubor, pk=pk)
    try:
        check_soubor_vazba(typ_vazby, ident_cely, pk)
    except ZaznamSouborNotmatching as e:
        logger.debug(e)
        messages.add_message(
                        request, messages.ERROR, SPATNY_ZAZNAM_ZAZNAM_VAZBA
                    )
        return redirect(request.GET.get("next"))
    if request.method == "POST":
        s.deleted_by_user = request.user
        items_deleted: Soubor = s.delete()
        if not items_deleted:
            # Not sure if 404 is the only correct option
            logger.debug("core.views.delete_file.not_deleted", extra={"file": s})
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
            return JsonResponse({"messages": django_messages}, status=400)
        else:
            logger.debug("core.views.delete_file.deleted", extra={"items_deleted": items_deleted})
            connector = FedoraRepositoryConnector(s.vazba.navazany_objekt)
            if not request.POST.get("dropzone", False):
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
                connector.delete_binary_file(s)
            else:
                connector.delete_binary_file_completely(s)
        next_url = request.POST.get("next")
        if next_url:
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
                response = next_url
            else:
                logger.warning("core.views.delete_file.redirect_not_safe", extra={"next_url": next_url})
                response = reverse("core:home")
        else:
            response = reverse("core:home")
        return JsonResponse({"redirect": response})
    else:
        context = {
            "object": s,
            "title": _("core.views.delete_file.title.text"),
            "id_tag": "smazat-soubor-form",
            "button": _("core.views.smazat.submitButton.text"),
        }
        return render(request, "core/transakce_modal.html", context)


class DownloadFile(LoginRequiredMixin, View):
    thumb = False
    @staticmethod
    def _preprocess_image(file_content: BytesIO) -> BytesIO:
        return file_content

    def get(self, request, typ_vazby, ident_cely, pk, *args, **kwargs):
        try:
            check_soubor_vazba(typ_vazby, ident_cely, pk)
        except ZaznamSouborNotmatching as e:
            logger.debug(e)
            messages.add_message(
                            request, messages.ERROR, SPATNY_ZAZNAM_SOUBOR_VAZBA
                        )
            return redirect(request.GET.get("next"))
        soubor: Soubor = get_object_or_404(Soubor, id=pk)
        rep_bin_file: RepositoryBinaryFile = soubor.get_repository_content(thumb=self.thumb)
        if soubor.repository_uuid is not None:
            # content_type = mimetypes.guess_type(soubor.path.name)[0]  # Use mimetypes to get file type
            content = self._preprocess_image(rep_bin_file.content)
            response = FileResponse(content, filename=soubor.nazev)
            content.seek(0)
            response["Content-Length"] = content.getbuffer().nbytes
            content.seek(0)
            response["Content-Disposition"] = (
                    f"attachment; filename={soubor.nazev}"
            )
            return response

        if soubor.path is not None:
            path = os.path.join(settings.MEDIA_ROOT, soubor.path)
            if os.path.exists(path):
                content_type = mimetypes.guess_type(soubor.nazev)[
                    0
                ]  # Use mimetypes to get file type
                response = HttpResponse(soubor.path, content_type=content_type)
                response["Content-Length"] = str(len(soubor.path))
                response["Content-Disposition"] = (
                        "attachment; filename=" + soubor.nazev
                )
                return response
            else:
                logger.debug("core.views.download_file.not_exists", extra={"soubor_name": soubor.nazev, "path": path})
        else:
            logger.debug("core.views.download_file.path_is_none", extra={"soubor_name": soubor.nazev, "pk": pk})
        return HttpResponse("")


class DownloadThumbnail(DownloadFile):
    thumb = True


@login_required
@require_http_methods(["GET"])
def upload_file_projekt(request, ident_cely):
    """
    Funkce pohledu pro zobrazení stránky pro upload souboru k projektu.
    """
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav == PROJEKT_STAV_ARCHIVOVANY:
        raise PermissionDenied()
    return render(
        request,
        "core/upload_file.html",
        {"ident_cely": ident_cely, "back_url": projekt.get_absolute_url()},
    )


@login_required
@require_http_methods(["GET"])
def upload_file_dokument(request, ident_cely):
    """
    Funkce pohledu pro zobrazení stránky pro upload souboru k dokumentu.
    """
    d = get_object_or_404(Dokument, ident_cely=ident_cely)
    if d.stav == D_STAV_ARCHIVOVANY:
        raise PermissionDenied()
    return render(
        request,
        "core/upload_file.html",
        {"ident_cely": ident_cely, "back_url": d.get_absolute_url()},
    )


@login_required
@require_http_methods(["GET"])
def update_file(request, typ_vazby, ident_cely, file_id):
    """
    Funkce pohledu pro zobrazení stránky pro upload souboru.
    """
    try:
        check_soubor_vazba(typ_vazby, ident_cely, file_id)
    except ZaznamSouborNotmatching as e:
        logger.debug(e)
        messages.add_message(
                        request, messages.ERROR, SPATNY_ZAZNAM_SOUBOR_VAZBA
                    )
        return redirect(request.GET.get("next"))
        
    ident_cely = ""
    back_url = request.GET.get("next")
    return render(
        request,
        "core/upload_file.html",
        {"ident_cely": ident_cely, "back_url": back_url, "file_id": file_id, "typ_vazby":typ_vazby},
    )


@login_required
@require_http_methods(["GET"])
def upload_file_samostatny_nalez(request, ident_cely):
    """
    Funkce pohledu pro zobrazení stránky pro upload souboru k samostatnému nálezu.
    """
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if sn.stav == SN_ARCHIVOVANY:
        raise PermissionDenied()
    return render(
        request,
        "core/upload_file.html",
        {"ident_cely": ident_cely, "back_url": sn.get_absolute_url()},
    )

class uploadFileView(LoginRequiredMixin, TemplateView):
    """
    Třída pohledu pro zobrazení stránky s uploadem souboru.
    """
    template_name = "core/upload_file.html"
    http_method_names = ["get"]

    def get_zaznam(self):
        self.typ_vazby = self.kwargs.get("typ_vazby")
        self.ident = self.kwargs.get("ident_cely")
        if self.typ_vazby == "pas":
            return get_object_or_404(SamostatnyNalez, ident_cely=self.ident)
        elif self.typ_vazby == "dokument":
            return get_object_or_404(Dokument, ident_cely=self.ident)
        elif self.typ_vazby == "model3d":
            return get_object_or_404(Dokument, ident_cely=self.ident)
        else:
            return get_object_or_404(Projekt, ident_cely=self.ident)

    def get_context_data(self, **kwargs):
        zaznam = self.get_zaznam()
        context = {
            "ident_cely": self.ident,
            "back_url": zaznam.get_absolute_url(),
            "typ_vazby": self.typ_vazby,
        }
        return context


@require_http_methods(["POST"])
def post_upload(request):
    """
    Funkce pohledu pro upload souboru a k navázaní ke správnemu záznamu.
    """
    update = "fileID" in request.POST
    s = None
    if not update:
        logger.debug("core.views.post_upload.start", extra={"objectID": request.POST.get("objectID", None)})
        projekt = Projekt.objects.filter(ident_cely=request.POST["objectID"])
        dokument = Dokument.objects.filter(ident_cely=request.POST["objectID"])
        samostatny_nalez = SamostatnyNalez.objects.filter(ident_cely=request.POST["objectID"])
        if projekt.exists():
            objekt = projekt[0]
            new_name = get_projekt_soubor_name(request.FILES.get("file").name)
        elif dokument.exists():
            objekt = dokument[0]
            new_name = get_dokument_soubor_name(objekt, request.FILES.get("file").name)
        elif samostatny_nalez.exists():
            objekt = samostatny_nalez[0]
            new_name = get_finds_soubor_name(objekt, request.FILES.get("file").name)
        else:
            return JsonResponse(
                {
                    "error": "Nelze pripojit soubor k neexistujicimu objektu "
                    + request.POST["objectID"]
                },
                status=500,
            )
        if new_name is False:
            return JsonResponse(
                {
                    "error": f"Nelze pripojit soubor k objektu {request.POST['objectID']}. Objekt ma prilozen soubor s nejvetsim moznym nazvem"
                },
                status=500,
            )
    else:
        logger.debug("core.views.post_upload.updating", extra={"fileID": request.POST["fileID"]})
        s = get_object_or_404(Soubor, id=request.POST["fileID"])
        logger.debug("core.views.post_upload.update", extra={"s": s.pk})
        objekt = s.vazba.navazany_objekt
        new_name = s.nazev
    soubor: TemporaryUploadedFile = request.FILES.get("file")
    soubor.seek(0)
    soubor_data = BytesIO(soubor.read())
    rep_bin_file = None
    if soubor:
        checksum = calculate_crc_32(soubor)
        if not update:
            conn = FedoraRepositoryConnector(objekt)
            mimetype = get_mime_type(soubor.name)
            rep_bin_file = conn.save_binary_file(new_name, get_mime_type(soubor.name), soubor_data)
            sha_512 = rep_bin_file.sha_512
            s = Soubor(
                vazba=objekt.soubory,
                nazev=new_name,
                # Short name is new name without checksum
                mimetype=mimetype,
                size_mb=rep_bin_file.size_mb,
                path=rep_bin_file.url_without_domain,
                sha_512=sha_512,
            )
            conn.validate_file_sha_512(s)
            duplikat = Soubor.objects.filter(sha_512=sha_512).order_by("pk")
            if not duplikat.exists():
                logger.debug("core.views.post_upload.saving", extra={"s": s})
                s.save()
                if not request.user.is_authenticated:
                    user_admin = User.objects.filter(email="amcr@arup.cas.cz").first()
                    s.zaznamenej_nahrani(user_admin)
                else:
                    s.zaznamenej_nahrani(request.user)
                return JsonResponse(
                    {"filename": s.nazev, "id": s.pk}, status=200
                )
            else:
                logger.warning("core.views.post_upload.already_exists", extra={"s": s})
                s.save()
                if not request.user.is_authenticated:
                    user_admin = User.objects.filter(email="amcr@arup.cas.cz").first()
                    s.zaznamenej_nahrani(user_admin)
                else:
                    s.zaznamenej_nahrani(request.user)
                # Find parent record and send it to the user
                parent_ident = duplikat.first().vazba.navazany_objekt.ident_cely \
                    if duplikat.first().vazba.navazany_objekt is not None else ""
                return JsonResponse(
                    {
                        "duplicate": _(
                            "core.views.post_upload.duplikat.text1"
                        )
                        + parent_ident
                        + ". "
                        + _("core.views.post_upload.duplikat.text2"),
                        "filename": s.nazev,
                        "id": s.pk,
                    },
                    status=200,
                )
        else:
            __, file_extension = os.path.splitext(soubor.name)
            if s is None:
                return JsonResponse(
                    {"error": f"Chyba při zpracování souboru"},
                    status=500,
                )
            if s.vazba.typ_vazby is None:
                return JsonResponse(
                    {"error": f"Chybí vazba souboru"},
                    status=500,
                )
            conn = FedoraRepositoryConnector(objekt)
            mimetype = get_mime_type(soubor.name)
            if s.repository_uuid is not None:
                extension = soubor.name.split(".")[-1]
                old_name = ".".join(s.nazev.split(".")[:-1])
                new_name = f'{old_name}.{extension}'
                rep_bin_file = conn.update_binary_file(new_name, get_mime_type(soubor.name),
                                                       soubor_data, s.repository_uuid)
                logger.debug("core.views.post_upload.update", extra={"pk": s.pk, "new_name": new_name})
                s.nazev = new_name
                s.size_mb = rep_bin_file.size_mb
                s.mimetype = mimetype
                s.sha_512 = rep_bin_file.sha_512
                s.save()
                s.zaznamenej_nahrani_nove_verze(request.user, new_name)
                conn.validate_file_sha_512(s)
            if rep_bin_file is not None:
                duplikat = (
                    Soubor.objects.filter(sha_512=rep_bin_file.sha_512)
                    .filter(~Q(id=s.id))
                    .order_by("pk")
                )
                if duplikat.count() > 0:
                    parent_ident = duplikat.first().vazba.navazany_objekt.ident_cely \
                        if duplikat.first().vazba.navazany_objekt is not None else ""
                    return JsonResponse(
                        {
                            "duplicate": _(
                                "core.views.post_upload.duplikat2.text1"
                            )
                            + parent_ident
                            + ". "
                            + str(_("core.views.post_upload.duplikat2.text2")),
                            "filename": s.nazev,
                            "id": s.pk,
                        },
                        status=200,
                    )
                else:
                    return JsonResponse(
                        {"filename": s.nazev, "id": s.pk}, status=200
                    )
            else:
                logger.warning("core.views.post_upload.rep_bin_file_is_none")
                return JsonResponse({"error": "Soubor se nepovedlo nahrát."}, status=500)
    else:
        logger.warning("core.views.post_upload.no_file")
    return JsonResponse({"error": "Soubor se nepovedlo nahrát."}, status=500)


def get_finds_soubor_name(find, filename, add_to_index=1):
    """
    Funkce pro získaní jména souboru pro samostatný nález.
    """
    my_regex = (
        r"^\d+_" + re.escape(find.ident_cely.replace("-", "")) + r"(F\d{2}\.\w+)$"
    )
    files = find.soubory.soubory.all().filter(nazev__iregex=my_regex)
    if not files.exists():
        return (find.ident_cely.replace("-", "") + "F01") + os.path.splitext(filename)[
            1
        ]
    else:
        list_last_char = []
        for file in files:
            split_file = os.path.splitext(file.nazev)
            list_last_char.append(split_file[0][-2:])
        last_char = max(list_last_char)
        if last_char != "99" or add_to_index == 0:
            return (
                find.ident_cely.replace("-", "")
                + "F"
                + str(int(last_char) + add_to_index).zfill(2)
                + os.path.splitext(filename)[1]
            )
        else:
            logger.warning("core.views.get_finds_soubor_name.cannot_upload",
                           extra={"file": filename, "list_last_char": list_last_char})
            return False


def get_projekt_soubor_name(file_name):
    """
    Funkce pro získaní jména souboru pro projekt.
    """
    split_file = os.path.splitext(file_name)
    nfkd_form = unicodedata.normalize("NFKD", split_file[0])
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return re.sub("[^A-Za-z0-9_]", "_", only_ascii) + split_file[1]
    # potrebne odstranit constraint soubor_filepath_key


def check_stav_changed(request, zaznam):
    """
    Funkce pro oveření jestli se zmenil stav záznamu pri uložení formuláře oproti jeho načtení.
    """
    logger.debug("core.views.check_stav_changed.start", extra={"zaznam_id": zaznam.pk})
    if request.method == "POST":
        # TODO BR-A-5
        form_check = CheckStavNotChangedForm(data=request.POST, db_stav=zaznam.stav)
        if form_check.is_valid():
            pass
        else:
            if "State_changed" in str(form_check.errors):
                if isinstance(zaznam, SamostatnyNalez):
                    messages.add_message(
                        request, messages.ERROR, SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV
                    )
                    logger.debug("core.views.check_stav_changed.state_changed.error",
                                 extra={"reason": SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV,
                                        "form_check_errors": str(form_check.errors)})
                elif isinstance(zaznam, ArcheologickyZaznam):
                    messages.add_message(
                        request,
                        messages.ERROR,
                        get_message(zaznam, "NEKDO_ZMENIL_STAV"),
                    )
                    logger.debug("core.views.check_stav_changed.state_changed.error",
                                 extra={"reason": get_message(zaznam, "NEKDO_ZMENIL_STAV"),
                                        "form_check_errors": str(form_check.errors)})
                elif isinstance(zaznam, Dokument):
                    messages.add_message(
                        request, messages.ERROR, DOKUMENT_NEKDO_ZMENIL_STAV
                    )
                    logger.debug("core.views.check_stav_changed.state_changed.error",
                                 extra={"reason": DOKUMENT_NEKDO_ZMENIL_STAV,
                                        "form_check_errors": str(form_check.errors)})
                elif isinstance(zaznam, Projekt):
                    messages.add_message(
                        request, messages.ERROR, PROJEKT_NEKDO_ZMENIL_STAV
                    )
                    logger.debug("core.views.check_stav_changed.state_changed.error",
                                 extra={"reason": PROJEKT_NEKDO_ZMENIL_STAV,
                                        "form_check_errors": str(form_check.errors)})
                return True

    else:
        # check if stav zaznamu is same in DB as was on detail page entered from
        if request.GET.get("sent_stav", False) and str(
            request.GET.get("sent_stav")
        ) != str(zaznam.stav):
            sent_stav = str(request.GET.get("sent_stav"))
            zaznam_stav = str(zaznam.stav)
            if isinstance(zaznam, SamostatnyNalez):
                messages.add_message(
                    request, messages.ERROR, SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV
                )
                logger.debug("core.views.check_stav_changed.sent_stav.error",
                             extra={"reason": SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV, "zaznam_stav": zaznam_stav,
                                    "sent_stav": sent_stav})
            elif isinstance(zaznam, ArcheologickyZaznam):
                messages.add_message(
                    request, messages.ERROR, get_message(zaznam, "NEKDO_ZMENIL_STAV")
                )
                logger.debug("core.views.check_stav_changed.sent_stav.error",
                             extra={"reason": get_message(zaznam, "NEKDO_ZMENIL_STAV"), "zaznam_stav": zaznam_stav,
                                    "sent_stav": sent_stav})
            elif isinstance(zaznam, Dokument):
                messages.add_message(
                    request, messages.ERROR, DOKUMENT_NEKDO_ZMENIL_STAV
                )
                logger.debug("core.views.check_stav_changed.sent_stav.error",
                             extra={"reason": DOKUMENT_NEKDO_ZMENIL_STAV, "zaznam_stav": zaznam_stav,
                                    "sent_stav": sent_stav})
            elif isinstance(zaznam, Projekt):
                messages.add_message(request, messages.ERROR, PROJEKT_NEKDO_ZMENIL_STAV)
                logger.debug("core.views.check_stav_changed.sent_stav.error",
                             extra={"reason": PROJEKT_NEKDO_ZMENIL_STAV, "zaznam_stav": zaznam_stav,
                                    "sent_stav": sent_stav})
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
        return redirect(object.get_absolute_url())
    else:
        messages.error(
            request, _("core.views.redirectView.identnotmatchingregex.message.text")
        )
        return redirect("core:home")

# for prolonging session ajax call
@login_required
@require_http_methods(["GET"])
def prolong_session(request):
    """
    Funkce pohledu pro prodloužení prihlášení.
    """
    options = getattr(settings, "AUTO_LOGOUT")
    current_time = now()
    session_time = seconds_until_idle_time_end(
        request, options["IDLE_TIME"], current_time
    )
    return JsonResponse(
        {"session_time": session_time},
        status=200,
    )


@login_required
@require_http_methods(["POST"])
def tr_wgs84(request):
    """
    Funkce pohledu pro transformaci souradnic na wsg84.
    """
    body = json.loads(request.body.decode("utf-8"))
    [c_x2, c_x1] = get_transform_towgs84(body["c_x1"], body["c_x2"])
    if c_x1 is not None:
        return JsonResponse(
            {"x1": c_x1, "x2": c_x2},
            status=200,
        )
    else:
        return JsonResponse({"x1": "", "x2": ""}, status=200)

 
 

@login_required
@require_http_methods(["POST"])
def tr_mwgs84(request):
    """
    Funkce pohledu pro transformaci na wsg84.
    """
    body = json.loads(request.body.decode("utf-8"))["points"]
    points = get_multi_transform_towgs84(body)
    if points is not None:
        return JsonResponse(
            {"points": points},
            status=200,
        )
    else:
        return JsonResponse({"points": None}, status=200)


class ExportMixinDate(ExportMixin):
    """
    Mixin pro získaní názvu exportovaného souboru.
    """
    def get_export_filename(self, export_format):
        now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        return "{}{}.{}".format(self.export_name, now, export_format)

class PermissionFilterMixin():
    permission_model_lookup = ""
    typ_zmeny_lookup = ""
    
    def check_filter_permission(self, qs, action=None):
        if action:
            permissions = Permissions.objects.filter(
                main_role=self.request.user.hlavni_role,
                address_in_app=self.request.resolver_match.route,
                action=action
            )
        else:    
            permissions = Permissions.objects.filter(
                    main_role=self.request.user.hlavni_role,
                    address_in_app=self.request.resolver_match.route,
                )
        if permissions.count()>0:
            for idx, perm in enumerate(permissions):
                if idx == 0:
                    new_qs = self.filter_by_permission(qs, perm)
                else:
                    new_qs = self.filter_by_permission(qs, perm).exclude(pk__in=new_qs.values("pk")) | new_qs

            perm_skips = list(PermissionsSkip.objects.filter(user=self.request.user).values_list("ident_list",flat=True))
            if len(perm_skips) > 0:
                if "spoluprace/vyber" in perm.address_in_app:
                    ident_key = self.permission_model_lookup + "id__in"
                    perm_skips_list = [id for id in perm_skips[0].split(",") if id.isdigit()]
                else:
                    ident_key = self.permission_model_lookup + "ident_cely__in"
                    perm_skips_list = perm_skips[0].split(",")
                filterdoc = {ident_key:perm_skips_list}
                if perm.status:
                    filterdoc.update(self.add_status_lookup(perm))
                qs = new_qs | qs.filter(**filterdoc)
            else:
                qs = new_qs
        return qs
    
    def filter_by_permission(self, qs, permission):
        filterdoc = {}
        if not permission.base:
            logger.debug("no base")
            return qs.none()
        if permission.status:
            filterdoc.update(self.add_status_lookup(permission))
        if permission.ownership:
            filterdoc.update(self.add_ownership_lookup(permission.ownership,qs))
        qs = qs.filter(**filterdoc)
        if permission.accessibility:
            qs = self.add_accessibility_lookup(permission,qs)

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
            operator_str = ["__gte","__lte"]
        else:
            operator_str = ""
            status = subed_status[0]
        if isinstance(operator_str, list):
            i = 0
            for operator in operator_str:
                str_oper = self.permission_model_lookup + "stav" + operator    
                filterdoc.update(
                    {
                        str_oper:subed_status[i]
                    }
                )
                i-=1
        else:
            str_oper = self.permission_model_lookup + "stav" + operator_str    
            filterdoc.update(
                {
                    str_oper:status
                }
            )
        return filterdoc
    
    def add_ownership_lookup(self, ownership, qs=None):
        filter_historie = {"typ_zmeny":self.typ_zmeny_lookup,"uzivatel":self.request.user}
        filtered_my = set(Historie.objects.filter(**filter_historie).values_list("pk", flat=True))
        if ownership == Permissions.ownershipChoices.our:
            filter_historie = {"typ_zmeny":self.typ_zmeny_lookup, "uzivatel__organizace":self.request.user.organizace}
            filtered_our = set(Historie.objects.filter(**filter_historie).values_list("pk", flat=True))
            filtered = filtered_my.union(filtered_our)
        else:
            filtered = filtered_my
        historie_key = self.permission_model_lookup + "historie__historie__pk__in"
        filterdoc = {historie_key:filtered}
        return filterdoc
    
    def add_accessibility_lookup(self,permission, qs):
        group_to_accessibility={
            ROLE_BADATEL_ID: PRISTUPNOST_BADATEL_ID,
            ROLE_ARCHEOLOG_ID: PRISTUPNOST_ARCHEOLOG_ID,
            ROLE_ARCHIVAR_ID:PRISTUPNOST_ARCHIVAR_ID ,
            ROLE_ADMIN_ID:PRISTUPNOST_ARCHIVAR_ID ,
        }
        qs_ownership = set(qs.filter(**self.add_ownership_lookup(permission.accessibility)).values_list("pk", flat=True))
        accessibility_key = self.permission_model_lookup+"pristupnost__in"
        accessibilities = Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST, razeni__lte=Heslar.objects.filter(id=group_to_accessibility.get(self.request.user.hlavni_role.id)).values_list("razeni",flat=True))
        filter = {accessibility_key:accessibilities}
        qs_access = set(qs.filter(**filter).values_list("pk", flat=True))
        qs_set = qs_access.union(qs_ownership)
        return qs.filter(pk__in=qs_set)

class SearchListView(ExportMixin, LoginRequiredMixin, SingleTableMixin, FilterView, PermissionFilterMixin):
    """
    Třída pohledu pro tabulky záznamů, která je použita jako základ pro jednotlivé pohledy.
    """
    template_name = "search_list.html"
    paginate_by = 100
    allow_empty = True
    export_formats = ["csv", "json", "xlsx"]
    app = "core"
    toolbar = "toolbar_akce.html"
    
    def init_translations(self):
        self.page_title = _("core.views.AkceListView.page_title.text")
        self.search_sum = _("core.views.AkceListView.search_sum.text")
        self.pick_text = _("core.views.AkceListView.pick_text.text")
        self.hasOnlyVybrat_header = _("core.views.AkceListView.hasOnlyVybrat_header.text")
        self.hasOnlyVlastnik_header = _("core.views.AkceListView.hasOnlyVlastnik_header.text")
        self.hasOnlyArchive_header = _("core.views.AkceListView.hasOnlyArchive_header.text")
        self.hasOnlyPotvrdit_header = _("core.views.AkceListView.hasOnlyPotvrdit_header.text")
        self.default_header = _("core.views.AkceListView.default_header.text")
        self.toolbar_name = _("core.views.AkceListView.toolbar_name.text")
        self.toolbar_label = _("core.views.AkceListView.toolbar_label.text")

    def get_paginate_by(self, queryset):
        return self.request.GET.get("per_page", self.paginate_by)
    
    def _get_sort_params(self):
        sort_params = self.request.GET.getlist('sort')
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
        context["default_header"] = self.default_header
        context["toolbar_name"] = self.toolbar_name
        context["toolbar_label"] = self.toolbar_label
        context["sort_params"] = self._get_sort_params()
        logger.debug(context)
        return context
    

class SearchListChangeColumnsView(LoginRequiredMixin, View):
    """
    Třída pohledu pro změnu zobrazení sloupcu u tabulky.
    """
    def post(self, request, *args, **kwargs):
        if "vychozi_skryte_sloupce" not in request.session:
            request.session["vychozi_skryte_sloupce"] = {}
        app = json.loads(request.body.decode("utf8"))["app"]
        sloupec = html.escape(json.loads(request.body.decode("utf8"))["sloupec"])
        zmena = json.loads(request.body.decode("utf8"))["zmena"]
        if app not in request.session["vychozi_skryte_sloupce"]:
            request.session["vychozi_skryte_sloupce"][app] = []
        skryte_sloupce = request.session["vychozi_skryte_sloupce"][app]
        if zmena == "zobraz":
            try:
                skryte_sloupce.remove(sloupec)
                request.session.modified = True
                return HttpResponse("Odebrano ze skrytych %s" % sloupec)
            except ValueError:
                logger.error("core.SearchListChangeColumnsView.post..odebrat_sloupec_z_vychozich.error",
                             extra={"sloupec": sloupec})
                HttpResponse(f"Nelze odebrat sloupec {sloupec}", status=400)
        else:
            skryte_sloupce.append(sloupec)
            request.session.modified = True
        return HttpResponse(f"{_('core.views.SearchListChangeColumnsView.response')} {sloupec}")



class StahnoutMetadataIdentCelyView(LoginRequiredMixin, View):
    def get(self, request, model_name, ident_cely):
        if model_name == "pian":
            record: Pian = Pian.objects.get(ident_cely=ident_cely)
        elif model_name == "projekt":
            record: Projekt = Projekt.objects.get(ident_cely=ident_cely)
        elif model_name == "archeologicky_zaznam":
            record: ArcheologickyZaznam = ArcheologickyZaznam.objects.get(ident_cely=ident_cely)
        elif model_name == "adb":
            record: Adb = Adb.objects.get(ident_cely=ident_cely)
        elif model_name == "dokument":
            record: Dokument = Dokument.objects.get(ident_cely=ident_cely)
        elif model_name == "samostatny_nalez":
            record: SamostatnyNalez = SamostatnyNalez.objects.get(ident_cely=ident_cely)
        elif model_name == "externi_zdroj":
            record: ExterniZdroj = ExterniZdroj.objects.get(ident_cely=ident_cely)
        else:
            raise Http404
        metadata = record.metadata

        def context_processor(content):
            yield content

        response = StreamingHttpResponse(context_processor(metadata), content_type="text/xml")
        response['Content-Disposition'] = 'attachment; filename="metadata.xml"'
        return response


@login_required
@require_http_methods(["POST"])
def post_ajax_get_pas_and_pian_limit(request):
    """
    Funkce pohledu pro získaní heatmapy.
    """
    body = json.loads(request.body.decode("utf-8"))
    params= [
            body["southEast"]["lng"],
            body["northWest"]["lat"],
            body["northWest"]["lng"],
            body["southEast"]["lat"],
            body["zoom"]
            ]
    num1 =  get_num_pass_from_envelope(*params[0:4],request)
    num2 =  get_num_pian_from_envelope(*params[0:4],request)
    req_pian=body["pian"]
    req_pas=body["pas"]
    logger.debug("pas.views.post_ajax_get_pas_and_pian_limit.num", extra={"num": num1+num2})
    num=0
    if req_pas:
        num=num+num1

    if req_pian:
        num=num+num2

    if num< 5000:
        back = []
        remove_duplicity = []

        if req_pas:
            pases = get_pas_from_envelope(*params[0:4],request)
            for pas in pases:
                if pas.id not in remove_duplicity:
                    remove_duplicity.append(pas.id)
                    back.append(
                        {
                            "id": pas.id,
                            "ident_cely": pas.ident_cely,
                            "geom": pas.geom.wkt.replace(", ", ","),
                            "type": "pas"
                        }
                    )

        if req_pian:    
            pians = get_pian_from_envelope(*params[0:4],request)    
            for pian in pians:
                if pian["pian__id"] not in remove_duplicity:
                    remove_duplicity.append(pian["pian__id"])
                    back.append(
                        
                        {
                            "id": pian["pian__id"],
                            "ident_cely": pian["pian__ident_cely"],
                            "geom": pian["pian__geom"].wkt.replace(", ", ",")
                            if num<500
                            else pian["pian__centroid"].wkt.replace(", ", ","),
                            "dj": pian["ident_cely"],
                            "presnost": pian["pian__presnost__zkratka"],
                            "type": "pian"
                        
                        }
                    )
        if num > 0:
            return JsonResponse({"points": back, "algorithm": "detail","count":num}, status=200)
        else:
            return JsonResponse({"points": [], "algorithm": "detail","count":0}, status=200)
    else:
        density = get_heatmap_pas_density(*params)
        logger.debug("pas.views.post_ajax_get_pas_and_pian_limit.density", extra={"density": density})

        heats = []
        if req_pas:
            heats=heats+get_heatmap_pas(*params)
        if req_pian:
            heats=heats+get_heatmap_pian(*params)
        back = []
        cid = 0
        for heat in heats:
            cid += 1
            back.append(
                {
                    "id": str(cid),
                    "pocet": heat["count"],
                    "density": 0,
                    "geom": heat["geometry"].replace(", ", ","),
                }
            )
        if len(heats) > 0:
            return JsonResponse({"heat": back, "algorithm": "heat","count":len(heats)}, status=200)
        else:
            return JsonResponse({"heat": [], "algorithm": "heat","count":len(heats)}, status=200)


def check_soubor_vazba(typ_vazby, ident, id_zaznamu):
    if typ_vazby == 'model3d' or typ_vazby == 'dokument':
        soubor = get_object_or_404(Dokument, ident_cely=ident).soubory.soubory.filter(pk=id_zaznamu)
    elif typ_vazby == 'pas':
        soubor = get_object_or_404(SamostatnyNalez, ident_cely=ident).soubory.soubory.filter(pk=id_zaznamu)
    elif typ_vazby == 'projekt':
        soubor = get_object_or_404(Projekt, ident_cely=ident).soubory.soubory.filter(pk=id_zaznamu)
    if soubor.count() > 0:
        return True
    else:
        raise ZaznamSouborNotmatching
