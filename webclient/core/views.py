import logging
import mimetypes
import os

from core.constants import (
    DOKUMENT_RELATION_TYPE,
    OTHER_DOCUMENT_FILES,
    OTHER_PROJECT_FILES,
    PHOTO_DOCUMENTATION,
    PROJEKT_RELATION_TYPE,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
)
from core.message_constants import ZAZNAM_SE_NEPOVEDLO_SMAZAT, ZAZNAM_USPESNE_SMAZAN
from core.models import Soubor
from core.utils import calculate_crc_32, get_mime_type
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import is_safe_url
from django.views.decorators.http import require_http_methods
from dokument.models import Dokument
from pas.models import SamostatnyNalez
from projekt.models import Projekt
from uzivatel.models import User

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def index(request):

    return render(request, "core/index.html")


@login_required
@require_http_methods(["POST", "GET"])
def delete_file(request, pk):
    s = get_object_or_404(Soubor, pk=pk)
    if request.method == "POST":
        s.path.delete()
        items_deleted = s.delete()
        if not items_deleted:
            # Not sure if 404 is the only correct option
            logger.debug("Soubor " + str(items_deleted) + " nebyl smazan.")
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
        else:
            logger.debug("Byl smazán soubor: " + str(items_deleted))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
        next_url = request.POST.get("next")
        if next_url:
            if is_safe_url(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
                logger.warning("Redirect to URL " + str(next_url) + " is not safe!!")
                response = redirect(next_url)
            else:
                response = redirect("core:home")
        else:
            response = redirect("core:home")
        return response
    else:
        return render(request, "core/delete_file.html", {"soubor": s})


@login_required
@require_http_methods(["GET"])
def download_file(request, pk):
    soubor = get_object_or_404(Soubor, id=pk)
    path = os.path.join(settings.MEDIA_ROOT, soubor.path.name)
    if os.path.exists(path):
        content_type = mimetypes.guess_type(soubor.path.name)[
            0
        ]  # Use mimetypes to get file type
        response = HttpResponse(soubor.path, content_type=content_type)
        response["Content-Length"] = str(len(soubor.path))
        response["Content-Disposition"] = "inline; filename=" + os.path.basename(
            soubor.nazev
        )
        return response
    else:
        logger.debug(
            "File " + str(soubor.nazev) + " does not exists at location " + str(path)
        )
    raise Http404


@login_required
@require_http_methods(["GET"])
def upload_file_projekt(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    return render(
        request,
        "core/upload_file.html",
        {"ident_cely": ident_cely, "back_url": projekt.get_absolute_url()},
    )


@login_required
@require_http_methods(["GET"])
def upload_file_dokument(request, ident_cely):
    d = get_object_or_404(Dokument, ident_cely=ident_cely)
    return render(
        request,
        "core/upload_file.html",
        {"ident_cely": ident_cely, "back_url": d.get_absolute_url()},
    )


@login_required
@require_http_methods(["GET"])
def upload_file_samostatny_nalez(request, ident_cely):
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    return render(
        request,
        "core/upload_file.html",
        {"ident_cely": ident_cely, "back_url": sn.get_absolute_url()},
    )


@require_http_methods(["POST"])
def post_upload(request):
    logger.debug("Uploading file to object: " + request.POST["objectID"])
    projects = Projekt.objects.filter(ident_cely=request.POST["objectID"])
    documents = Dokument.objects.filter(ident_cely=request.POST["objectID"])
    finds = SamostatnyNalez.objects.filter(ident_cely=request.POST["objectID"])
    typ_souboru = ""
    if projects.exists():
        objekt = projects[0]
        typ_souboru = OTHER_PROJECT_FILES
    elif documents.exists():
        objekt = documents[0]
        typ_souboru = OTHER_DOCUMENT_FILES
    elif finds.exists():
        objekt = finds[0]
        typ_souboru = PHOTO_DOCUMENTATION
    else:
        return JsonResponse(
            {
                "error": "Nelze pripojit soubor k neexistujicimu objektu "
                + request.POST["objectID"]
            },
            status=500,
        )
    soubor = request.FILES.get("file")
    if soubor:
        checksum = calculate_crc_32(soubor)
        # After calculating checksum, must move pointer to the beginning
        soubor.file.seek(0)
        old_name = soubor.name
        soubor.name = checksum + "_" + soubor.name
        s = Soubor(
            path=soubor,
            vazba=objekt.soubory,
            nazev=soubor.name,
            # Short name is new name without checksum
            nazev_zkraceny=old_name,
            nazev_puvodni=old_name,
            vlastnik=get_object_or_404(User, email="amcr@arup.cas.cz"),
            mimetype=get_mime_type(old_name),
            size_bytes=soubor.size,
            typ_souboru=typ_souboru,
        )
        duplikat = Soubor.objects.filter(nazev=s.nazev).order_by("pk")
        if not duplikat.exists():
            logger.debug("Saving file object: " + str(s))
            s.save()
            return JsonResponse({"filename": s.nazev_zkraceny, "id": s.pk}, status=200)
        else:
            logger.warning("File already exists on the server. Saving copy" + str(s))
            s.save()
            # Find parent record and send it to the user
            parent_ident = ""
            if duplikat[0].vazba.typ_vazby == PROJEKT_RELATION_TYPE:
                parent_ident = duplikat[0].vazba.projekt_souboru.ident_cely
            if duplikat[0].vazba.typ_vazby == DOKUMENT_RELATION_TYPE:
                parent_ident = duplikat[0].vazba.dokument_souboru.ident_cely
            if duplikat[0].vazba.typ_vazby == SAMOSTATNY_NALEZ_RELATION_TYPE:
                parent_ident = duplikat[0].vazba.samostatny_nalez_souboru.ident_cely
            return JsonResponse(
                {
                    "duplicate": "Soubor sme uložili, ale soubor stejným jménem a obsahem na servru již existuje a je připojen k záznamu "
                    + parent_ident
                    + ". Skontrolujte prosím duplicitu."
                },
                status=200,
            )
    else:
        logger.warning("No file attached to the announcement form.")

    return JsonResponse({"error": "Soubor se nepovedlo nahrát."}, status=500)
