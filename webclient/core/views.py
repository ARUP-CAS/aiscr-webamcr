import logging
import mimetypes
import os
import re
import unicodedata
from string import ascii_uppercase as letters

from arch_z.models import ArcheologickyZaznam
from core.constants import (
    DOKUMENT_RELATION_TYPE,
    OTHER_DOCUMENT_FILES,
    OTHER_PROJECT_FILES,
    PHOTO_DOCUMENTATION,
    PROJEKT_RELATION_TYPE,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
    D_STAV_ARCHIVOVANY,
    PROJEKT_STAV_ARCHIVOVANY,
    SN_ARCHIVOVANY,
)
from core.forms import CheckStavNotChangedForm
from core.message_constants import (
    DOKUMENT_NEKDO_ZMENIL_STAV,
    SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_USPESNE_SMAZAN,
    AKCI_NEKDO_ZMENIL_STAV,
    PROJEKT_NEKDO_ZMENIL_STAV
    )
from core.models import Soubor
from core.utils import calculate_crc_32, get_mime_type
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import is_safe_url
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext as _
from dokument.models import Dokument
from pas.models import SamostatnyNalez
from projekt.models import Projekt
from uzivatel.models import User
from django.core.exceptions import PermissionDenied
from django_auto_logout.utils import now, seconds_until_idle_time_end
from django.conf import settings


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
        response["Content-Disposition"] = (
            "attachment; filename=" + soubor.nazev_zkraceny
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
def update_file(request, file_id):
    ident_cely = ""
    back_url = ""
    soubor = get_object_or_404(Soubor, id=file_id)
    return render(
        request,
        "core/upload_file.html",
        {"ident_cely": ident_cely, "back_url": back_url, "file_id": file_id},
    )


@login_required
@require_http_methods(["GET"])
def upload_file_samostatny_nalez(request, ident_cely):
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
    update = "fileID" in request.POST
    if not update:
        logger.debug("Uploading file to object: " + request.POST["objectID"])
        projects = Projekt.objects.filter(ident_cely=request.POST["objectID"])
        documents = Dokument.objects.filter(ident_cely=request.POST["objectID"])
        finds = SamostatnyNalez.objects.filter(ident_cely=request.POST["objectID"])
        if projects.exists():
            objekt = projects[0]
            typ_souboru = OTHER_PROJECT_FILES
            new_name = get_projekt_soubor_name(request.FILES.get("file").name)
        elif documents.exists():
            objekt = documents[0]
            typ_souboru = OTHER_DOCUMENT_FILES
            new_name = get_dokument_soubor_name(objekt, request.FILES.get("file").name)
        elif finds.exists():
            objekt = finds[0]
            typ_souboru = PHOTO_DOCUMENTATION
            new_name = get_finds_soubor_name(objekt, request.FILES.get("file").name)
        else:
            return JsonResponse(
                {
                    "error": "Nelze pripojit soubor k neexistujicimu objektu "
                    + request.POST["objectID"]
                },
                status=500,
            )
        if new_name == False:
            return JsonResponse(
                {
                    "error": f"Nelze pripojit soubor k objektu {request.POST['objectID']}. Objekt ma prilozen soubor s nejvetsim moznym nazvem"
                },
                status=500,
            )
    else:
        logger.debug("Updating file for soubor " + request.POST["fileID"])
        s = get_object_or_404(Soubor, id=request.POST["fileID"])
    soubor = request.FILES.get("file")
    if soubor:
        checksum = calculate_crc_32(soubor)
        # After calculating checksum, must move pointer to the beginning
        soubor.file.seek(0)
        if not update:
            old_name = soubor.name
            soubor.name = checksum + "_" + soubor.name
            s = Soubor(
                path=soubor,
                vazba=objekt.soubory,
                nazev=checksum + "_" + new_name,
                # Short name is new name without checksum
                nazev_zkraceny=new_name,
                nazev_puvodni=old_name,
                vlastnik=get_object_or_404(User, email="amcr@arup.cas.cz"),
                mimetype=get_mime_type(old_name),
                size_bytes=soubor.size,
                typ_souboru=typ_souboru,
            )
            duplikat = Soubor.objects.filter(nazev__contains=checksum).order_by("pk")
            if not duplikat.exists():
                logger.debug("Saving file object: " + str(s))
                s.save()
                s.zaznamenej_nahrani(request.user)
                return JsonResponse({"filename": s.nazev_zkraceny, "id": s.pk}, status=200)
            else:
                logger.warning("File already exists on the server. Saving copy" + str(s))
                s.save()
                s.zaznamenej_nahrani(request.user)
                # Find parent record and send it to the user
                parent_ident = ""
                if duplikat[0].vazba.typ_vazby == PROJEKT_RELATION_TYPE:
                    parent_ident = duplikat[0].vazba.projekt_souboru.ident_cely
                if duplikat[0].vazba.typ_vazby == DOKUMENT_RELATION_TYPE:
                    parent_ident = duplikat[0].vazba.dokument_souboru.ident_cely
                if duplikat[0].vazba.typ_vazby == SAMOSTATNY_NALEZ_RELATION_TYPE:
                    logger.debug(duplikat[0].vazba.samostatny_nalez_souboru)
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
            logger.debug(f"Saving file to object: {s.pk}")
            s.path = soubor
            s.size_bytes = soubor.size
            s.save()
            return JsonResponse({"filename": s.nazev_zkraceny, "id": s.pk}, status=200)
    else:
        logger.warning("No file attached to the announcement form.")

    return JsonResponse({"error": "Soubor se nepovedlo nahrát."}, status=500)

def get_dokument_soubor_name(dokument, filename):
    my_regex = r"^\d*_" + re.escape(dokument.ident_cely.replace("-","")) + r"[A-Z]?\..*$"
    files = dokument.soubory.soubory.all().filter(nazev__iregex=my_regex)
    if not files.exists():
        return dokument.ident_cely.replace("-","")+os.path.splitext(filename)[1]
    else:
        filtered_files=files.filter(nazev__iregex=r"[A-Z]\..*$")
        if filtered_files.exists():
            list_last_char = []
            for file in filtered_files:
                split_file = os.path.splitext(file.nazev)
                list_last_char.append(split_file[0][-1])
            last_char=max(list_last_char)
            logger.debug(last_char)
            if last_char != "Z":
                return (dokument.ident_cely.replace("-","")+letters[(letters.index(last_char)+1)]+os.path.splitext(filename)[1])
            else:
                logger.error("Neni mozne nahrat soubor. Soubor s poslednim moznym Nazvem byl uz nahran.")
                return False

        else:
            return (dokument.ident_cely.replace("-","")+"A")


def get_finds_soubor_name(find, filename):
    my_regex = r"^\d*_" + re.escape(find.ident_cely.replace("-","")) + r"F\d{2}\..*$"
    files = find.soubory.soubory.all().filter(nazev__iregex=my_regex)
    if not files.exists():
        return (find.ident_cely.replace("-","")+"F01")+os.path.splitext(filename)[1]
    else:
        list_last_char = []
        for file in files:
            split_file = os.path.splitext(file.nazev)
            list_last_char.append(split_file[0][-2:])
        logger.debug(list_last_char)
        logger.debug(files)
        last_char=max(list_last_char)
        if last_char != "99":
            return find.ident_cely.replace("-","")+"F"+ str(int(last_char)+1).zfill(2)+os.path.splitext(filename)[1]
        else:
            logger.error("Neni mozne nahrat soubor. Soubor s poslednim moznym Nazvem byl uz nahran.")
            return False

def get_projekt_soubor_name(file_name):
    split_file = os.path.splitext(file_name)
    nfkd_form = unicodedata.normalize('NFKD', split_file[0])
    only_ascii = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return (re.sub('[^A-Za-z0-9_]', '_', only_ascii)+split_file[1])
    # potrebne odstranit constraint soubor_filepath_key

    
def check_stav_changed(request, zaznam):
    if request.method == "POST":
        # TODO BR-A-5
        form_check = CheckStavNotChangedForm(data=request.POST, db_stav=zaznam.stav)
        if form_check.is_valid():
            pass
        else:
            if "State_changed" in str(form_check.errors):
                if isinstance(zaznam, SamostatnyNalez):
                    messages.add_message(request, messages.ERROR, SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV)
                elif isinstance(zaznam, ArcheologickyZaznam):
                    messages.add_message(request, messages.ERROR, AKCI_NEKDO_ZMENIL_STAV)
                elif isinstance(zaznam, Dokument):
                    messages.add_message(request, messages.ERROR, DOKUMENT_NEKDO_ZMENIL_STAV)
                elif isinstance(zaznam, Projekt):
                    messages.add_message(request, messages.ERROR, PROJEKT_NEKDO_ZMENIL_STAV)
                return True

    else:
        # check if stav zaznamu is same in DB as was on detail page entered from
        if request.GET.get('sent_stav', False) and str(request.GET.get('sent_stav'))!= str(zaznam.stav):
            if isinstance(zaznam, SamostatnyNalez):
                messages.add_message(request, messages.ERROR, SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV)
            elif isinstance(zaznam, ArcheologickyZaznam):
                messages.add_message(request, messages.ERROR, AKCI_NEKDO_ZMENIL_STAV)
            elif isinstance(zaznam, Dokument):
                    messages.add_message(request, messages.ERROR, DOKUMENT_NEKDO_ZMENIL_STAV)
            elif isinstance(zaznam, Projekt):
                messages.add_message(request, messages.ERROR, PROJEKT_NEKDO_ZMENIL_STAV)
            return True
    
    return False

@login_required
@require_http_methods(["GET"])
def redirect_ident_view(request, ident_cely):
    if bool(re.fullmatch("(C|M|X-C|X-M)-\d{9}", ident_cely)):
        logger.debug("regex match for project with ident %s", ident_cely)
        return redirect("projekt:detail", ident_cely=ident_cely)
    if bool(re.fullmatch("(C|M|X-C|X-M)-\d{9}A", ident_cely)):
        logger.debug("regex match for archeologicka akce with ident %s", ident_cely)
        return redirect("arch_z:detail", ident_cely=ident_cely)
    if bool(re.fullmatch("(C|M|X-C|X-M)-(TX|DD)-\d{9}", ident_cely)):
        logger.debug("regex match for dokument with ident %s", ident_cely)
        return redirect("dokument:detail", ident_cely=ident_cely)
    if bool(re.fullmatch("(C|M|X-C|X-M)-(3D)-\d{9}", ident_cely)):
        logger.debug("regex match for dokument 3D with ident %s", ident_cely)
        return redirect("dokument:detail-model-3D", ident_cely=ident_cely)
    if bool(re.fullmatch("(C|M|X-C|X-M)-\d{9}-N\d{5}", ident_cely)):
        logger.debug("regex match for Samostatny nalez with ident %s", ident_cely)
        return redirect("pas:detail", ident_cely=ident_cely)

    messages.error(request, _("core.redirectView.identnotmatchingregex.message.text"))
    return redirect("core:home")

# for prolonging session ajax call
@login_required
@require_http_methods(["GET"])
def prolong_session(request):
    options = getattr(settings, "AUTO_LOGOUT")
    current_time = now()
    session_time = seconds_until_idle_time_end(
        request, options["IDLE_TIME"], current_time
    )
    return JsonResponse(
        {"session_time": session_time},
        status=200,
    )
