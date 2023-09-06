import json
import logging
import mimetypes
import os
import re
from io import StringIO, BytesIO

import unicodedata
from django.core.files.uploadedfile import TemporaryUploadedFile
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View


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
    SAMOSTATNY_NALEZ_RELATION_TYPE,
    SN_ARCHIVOVANY,
)
from core.forms import CheckStavNotChangedForm
from core.message_constants import (
    DOKUMENT_NEKDO_ZMENIL_STAV,
    PROJEKT_NEKDO_ZMENIL_STAV,
    SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV,
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

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def index(request):
    "Funkce podledu pro zobrazení hlavní stránky."
    return render(request, "core/index.html")


@login_required
@require_http_methods(["POST", "GET"])
def delete_file(request, pk):
    """
    Funkce pohledu pro smazání souboru. Funkce maže jak záznam v DB tak i soubor na disku.
    """
    s = get_object_or_404(Soubor, pk=pk)
    if request.method == "POST":
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


@login_required
@require_http_methods(["GET"])
def download_file(request, pk):
    """
    Funkce pohledu pro stažení souboru.
    """
    soubor: Soubor = get_object_or_404(Soubor, id=pk)
    rep_bin_file: RepositoryBinaryFile = soubor.get_repository_content()
    if soubor.repository_uuid is not None:
        # content_type = mimetypes.guess_type(soubor.path.name)[0]  # Use mimetypes to get file type
        response = FileResponse(rep_bin_file.content, filename=soubor.nazev)
        response["Content-Length"] = rep_bin_file.size
        response["Content-Disposition"] = (
                "attachment; filename=" + soubor.nazev
        )
        return response

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
    return HttpResponse("")


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
def update_file(request, typ_vazby, file_id):
    """
    Funkce pohledu pro zobrazení stránky pro upload souboru.
    """
    ident_cely = ""
    back_url = request.GET.get("next")
    soubor = get_object_or_404(Soubor, id=file_id)
    return render(
        request,
        "core/upload_file.html",
        {"ident_cely": ident_cely, "back_url": back_url, "file_id": file_id},
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
                rep_bin_file = conn.update_binary_file(f"{checksum}_{soubor.name}", get_mime_type(soubor.name),
                                                       soubor_data, s.repository_uuid)
                name_without_checksum = soubor.name
                soubor.name = checksum + "_" + new_name
                s.nazev = checksum + "_" + new_name
                logger.debug("core.views.post_upload.update", extra={"pk": s.pk, "new_name": new_name})
                s.nazev = new_name
                s.size_mb = rep_bin_file.size_mb
                s.mimetype = mimetype
                s.sha_512 = rep_bin_file.sha_512
                s.save()
                s.zaznamenej_nahrani_nove_verze(request.user, name_without_checksum)
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
                            + _("core.views.post_upload.duplikat2.text2"),
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
    if bool(re.fullmatch("(C|M|X-C|X-M)-\d{9}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.project", extra={"ident_cely": ident_cely})
        return redirect("projekt:detail", ident_cely=ident_cely)
    if bool(re.fullmatch("(C|M|X-C|X-M)-\d{9}\D{1}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.archeologicka_akce", extra={"ident_cely": ident_cely})
        return redirect("arch_z:detail", ident_cely=ident_cely)
    if bool(re.fullmatch("(C|M|X-C|X-M)-9\d{6,9}\D{1}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.samostatna_akce", extra={"ident_cely": ident_cely})
        return redirect("arch_z:detail", ident_cely=ident_cely)
    if bool(re.fullmatch("(C|M|X-C|X-M)-(N|L|K)\d{7,9}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.lokalita", extra={"ident_cely": ident_cely})
        return redirect("lokalita:detail", slug=ident_cely)
    if bool(re.fullmatch("(BIB|X-BIB)-\d{7,9}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.zdroj", extra={"ident_cely": ident_cely})
        return redirect("ez:detail", slug=ident_cely)
    if bool(re.fullmatch("(C|M|X-C|X-M)-\w{8,10}-D\d{2}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.dokumentacni_jednotka", extra={"ident_cely": ident_cely})
        response = redirect("arch_z:detail", ident_cely=ident_cely[:-4])
        response.set_cookie("show-form", f"detail_dj_form_{ident_cely}", max_age=1000)
        response.set_cookie(
            "set-active",
            f"el_div_dokumentacni_jednotka_{ident_cely.replace('-', '_')}",
            max_age=1000,
        )
        return response
    if bool(re.fullmatch("(C|M|X-C|X-M)-\w{8,10}-K\d{3}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.komponenta_on_dokumentacni_jednotka",
                     extra={"ident_cely": ident_cely})
        response = redirect("arch_z:detail", ident_cely=ident_cely[:-5])
        response.set_cookie(
            "show-form", f"detail_komponenta_form_{ident_cely}", max_age=1000
        )
        response.set_cookie(
            "set-active", f"el_komponenta_{ident_cely.replace('-', '_')}", max_age=1000
        )
        return response
    if bool(re.fullmatch("ADB-\D{4}\d{2}-\d{6}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.adb", extra={"ident_cely": ident_cely})
        adb = get_object_or_404(Adb, ident_cely=ident_cely)
        dj_ident = adb.dokumentacni_jednotka.ident_cely
        response = redirect("arch_z:detail", ident_cely=dj_ident[:-4])
        response.set_cookie("show-form", f"detail_dj_form_{dj_ident}", max_age=1000)
        response.set_cookie(
            "set-active",
            f"el_div_dokumentacni_jednotka_{dj_ident.replace('-', '_')}",
            max_age=1000,
        )
        return response
    if bool(re.fullmatch("(X-ADB|ADB)-\D{4}\d{2}-\d{4,6}-V\d{4}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.vyskovy_bod", extra={"ident_cely": ident_cely})
        vb = get_object_or_404(VyskovyBod, ident_cely=ident_cely)
        dj_ident = vb.adb.dokumentacni_jednotka.ident_cely
        response = redirect("arch_z:detail", ident_cely=dj_ident[:-4])
        response.set_cookie("show-form", f"detail_dj_form_{dj_ident}", max_age=1000)
        response.set_cookie(
            "set-active",
            f"el_div_dokumentacni_jednotka_{dj_ident.replace('-', '_')}",
            max_age=1000,
        )
        return response
    if bool(re.fullmatch("(P|N)-\d{4}-\d{6,9}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.pian", extra={"ident_cely": ident_cely})
        # return redirect("dokument:detail", ident_cely=ident_cely) TO DO redirect
    if bool(re.fullmatch("(C|M|X-C|X-M)-(3D)-\d{9}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.dokument_3D", extra={"ident_cely": ident_cely})
        return redirect("dokument:detail-model-3D", ident_cely=ident_cely)
    if bool(re.fullmatch("(C|M|X-C|X-M)-(3D)-\d{9}-(D|K)\d{3}", ident_cely)) or bool(
        re.fullmatch("3D-(C|M|X-C|X-M)-\w{8,10}-\d{1,9}-(D|K)\d{3}", ident_cely)
    ):
        logger.debug("core.views.redirect_ident_view.obsah_cast_dokumentu_3D", extra={"ident_cely": ident_cely})
        return redirect("dokument:detail-model-3D", ident_cely=ident_cely[:-5])
    if bool(re.fullmatch("(C|M|X-C|X-M)-\D{2}-\d{9}", ident_cely)) or bool(
        re.fullmatch("(C|M|X-C|X-M)-\w{8,10}-\D{2}-\d{1,9}", ident_cely)
    ):
        logger.debug("core.views.redirect_ident_view.dokument", extra={"ident_cely": ident_cely})
        return redirect("dokument:detail", ident_cely=ident_cely)
    if bool(re.fullmatch("(C|M|X-C|X-M)-\D{2}-\d{9}-(D|K)\d{3}", ident_cely)) or bool(
        re.fullmatch("(C|M|X-C|X-M)-\w{8,10}-\D{2}-\d{1,9}-(D|K)\d{3}", ident_cely)
    ):
        logger.debug("core.views.redirect_ident_view.obsah_cast_dokumentu", extra={"ident_cely": ident_cely})
        return redirect("dokument:detail", ident_cely=ident_cely[:-5])
    if bool(re.fullmatch("(C|M|X-C|X-M)-\d{9}-N\d{5}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.samostatny_nalez", extra={"ident_cely": ident_cely})
        logger.debug("regex match for Samostatny nalez with ident %s", ident_cely)
        return redirect("pas:detail", ident_cely=ident_cely)
    if bool(re.fullmatch("(X-BIB|BIB)-\d{7}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.externi_zdroj", extra={"ident_cely": ident_cely})
        # return redirect("dokument:detail", ident_cely=ident_cely) TO DO redirect
    if bool(re.fullmatch("(LET)-\d{7}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.externi_zdroj", extra={"ident_cely": ident_cely})
        # return redirect("dokument:detail", ident_cely=ident_cely) TO DO redirect
    if bool(re.fullmatch("(HES)-\d{6}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.externi_zdroj", extra={"ident_cely": ident_cely})
        # return redirect("dokument:detail", ident_cely=ident_cely) TO DO redirect
    if bool(re.fullmatch("(ORG)-\d{6}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.externi_zdroj", extra={"ident_cely": ident_cely})
        # return redirect("dokument:detail", ident_cely=ident_cely) TO DO redirect
    if bool(re.fullmatch("(OS)-\d{6}", ident_cely)):
        logger.debug("core.views.redirect_ident_view.externi_zdroj", extra={"ident_cely": ident_cely})
        # return redirect("dokument:detail", ident_cely=ident_cely) TO DO redirect

    messages.error(request, _("core.views.redirectView.identnotmatchingregex.message.text"))
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
    [cx, cy] = get_transform_towgs84(body["cy"], body["cx"])
    if cx is not None:
        return JsonResponse(
            {"cx": cx, "cy": cy},
            status=200,
        )
    else:
        return JsonResponse({"cx": "", "cy": ""}, status=200)


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


class SearchListView(ExportMixin, LoginRequiredMixin, SingleTableMixin, FilterView):
    """
    Třída pohledu pro tabulky záznamů, která je použita jako základ pro jednotlivé pohledy.
    """
    template_name = "search_list.html"
    paginate_by = 100
    allow_empty = True
    export_formats = ["csv", "json", "xlsx"]
    page_title = _("core.views.AkceListView.page_title.text")
    app = "core"
    toolbar = "toolbar_akce.html"
    search_sum = _("core.views.AkceListView.search_sum.text")
    pick_text = _("core.views.AkceListView.pick_text.text")
    hasOnlyVybrat_header = _("core.views.AkceListView.hasOnlyVybrat_header.text")
    hasOnlyVlastnik_header = _("core.views.AkceListView.hasOnlyVlastnik_header.text")
    hasOnlyArchive_header = _("core.views.AkceListView.hasOnlyArchive_header.text")
    hasOnlyPotvrdit_header = _("core.views.AkceListView.hasOnlyPotvrdit_header.text")
    default_header = _("core.views.AkceListView.default_header.text")
    toolbar_name = _("core.views.AkceListView.toolbar_name.text")

    def get_paginate_by(self, queryset):
        return self.request.GET.get("per_page", self.paginate_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        return context


class SearchListChangeColumnsView(LoginRequiredMixin, View):
    """
    Třída pohledu pro změnu zobrazení sloupcu u tabulky.
    """
    def post(self, request, *args, **kwargs):
        if "vychozi_skryte_sloupce" not in request.session:
            request.session["vychozi_skryte_sloupce"] = {}
        app = json.loads(request.body.decode("utf8"))["app"]
        sloupec = json.loads(request.body.decode("utf8"))["sloupec"]
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
        return HttpResponse("Pridano do skrytych %s" % sloupec)


class StahnoutMetadataView(LoginRequiredMixin, View):
    def get(self, request, model_name, pk):
        if model_name == "projekt":
            record: Projekt = Projekt.objects.get(pk=pk)
        elif model_name == "archeologicky_zaznam":
            record: ArcheologickyZaznam = ArcheologickyZaznam.objects.get(pk=pk)
        elif model_name == "adb":
            record: Adb = Adb.objects.get(pk=pk)
        elif model_name == "dokument":
            record: Dokument = Dokument.objects.get(pk=pk)
        elif model_name == "samostatny_nalez":
            record: SamostatnyNalez = SamostatnyNalez.objects.get(pk=pk)
        elif model_name == "externi_zdroj":
            record: ExterniZdroj = ExterniZdroj.objects.get(pk=pk)
        else:
            raise Http404
        metadata = record.metadata

        def context_processor(content):
            yield content

        response = StreamingHttpResponse(context_processor(metadata), content_type="text/xml")
        response['Content-Disposition'] = 'attachment; filename="metadata.xml"'
        return response


class StahnoutMetadataIdentCelyView(LoginRequiredMixin, View):
    def get(self, request, model_name, ident_cely):
        if model_name == "pian":
            record: Pian = Pian.objects.get(ident_cely=ident_cely)
        else:
            raise Http404
        metadata = record.metadata

        def context_processor(content):
            yield content

        response = StreamingHttpResponse(context_processor(metadata), content_type="text/xml")
        response['Content-Disposition'] = 'attachment; filename="metadata.xml"'
        return response


