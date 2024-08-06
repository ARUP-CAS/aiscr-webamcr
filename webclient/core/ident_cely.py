import logging
from typing import Optional

from django.db import connection
import re

from django.shortcuts import get_object_or_404

from adb.models import Adb, Kladysm5, AdbSekvence, VyskovyBod
from arch_z.models import ArcheologickyZaznam
from core.constants import IDENTIFIKATOR_DOCASNY_PREFIX, DOKUMENT_CAST_RELATION_TYPE
from core.exceptions import (
    MaximalIdentNumberError,
    NelzeZjistitRaduError,
    NeznamaGeometrieError,
    PianNotInKladysm5Error,
    MaximalEventCount,
)
from django.contrib.gis.db.models.functions import Centroid
from django.contrib.gis.geos import LineString, Point, Polygon

from core.repository_connector import FedoraTransaction
from dokument.models import Dokument
from heslar.models import HeslarDokumentTypMaterialRada, Heslar
from pas.models import SamostatnyNalez
from pian.models import Pian
from projekt.models import Projekt
from ez.models import ExterniZdroj
from komponenta.models import Komponenta, KomponentaVazby
from dj.models import DokumentacniJednotka
from uzivatel.models import User

logger = logging.getLogger(__name__)

def get_next_sequence(sequence_name: str) -> str:
    query = (
        "select nextval(%s)"
    )
    cursor = connection.cursor()
    cursor.execute(query,[sequence_name])
    return cursor.fetchone()[0]


def get_temporary_project_ident(region: str) -> str:
    """
    Metóda pro výpočet dočasného identu projektu. Přiděluje se pro projekty vytvoření v rámci oznámení.

    Logika složení je: "X-" + region (M anebo C) + "-" + 9 místne číslo (id ze sequence projekt_xident_seq doplněno na 9 čísel nulama)
    Příklad: "X-M-000001234"
    """
    id_number = f"{get_next_sequence('projekt_xident_seq'):09}"
    return "X-" + region + "-" + id_number
    

def get_project_event_ident(project: Projekt) -> Optional[str]:
    """
    Metóda pro výpočet identu projektové akce.

    Logika složení je: ident_cely projektu + písmeno abecedy v posloupnosti od A po Z
    Pri překročení maxima čísla sekvence (99999) se vráti uživateli na web chybová hláška.
    Příklad: "M-202100034A"
    """
    MAXIMAL_PROJECT_EVENTS: int = 26
    if project.ident_cely:
        with connection.cursor() as cursor:
            predicate = project.ident_cely + "%"
            query = "select id, ident_cely from public.archeologicky_zaznam where ident_cely like %s order by ident_cely desc"
            cursor.execute(query, [predicate])
            idents = cursor.fetchall()

            if len(idents) < MAXIMAL_PROJECT_EVENTS:
                if idents:
                    last_ident = idents[0][1]  # Assuming the second column is 'ident_cely'
                    return project.ident_cely + chr(ord(last_ident[-1]) + 1)
                else:
                    return project.ident_cely + "A"
            else:
                logger.error("core.ident_cely.get_project_event_ident.error",
                             extra={"message": "Maximal number of project events is 26."})
                raise MaximalEventCount(MAXIMAL_PROJECT_EVENTS)
    else:
        logger.error("core.ident_cely.get_project_event_ident.error",
                     extra={"message": "Project is missing ident_cely"})
        return None


def get_dokument_rada(typ, material):
    """
    Metoda pro získaní rady dokumentu podle typu a materiálu dokumentu.
    """
    instances = HeslarDokumentTypMaterialRada.objects.filter(
        dokument_typ=typ, dokument_material=material
    )
    if len(instances) == 1:
        return instances[0].dokument_rada
    else:
        logger.error("core.ident_cely.get_dokument_rada.error",
                     extra={"message": "Nelze priradit radu k dokumentu. Neznama/nejednoznacna kombinace "
                                       f"typu {typ.id} a materialu. {material.id}"})
        raise NelzeZjistitRaduError()


def get_temp_dokument_ident(rada, region):
    """
    Metoda pro výpočet dočasného identu dokumentu.

    Logika složení je: "X-" + region (M anebo C) + "-" + řada (TX/DD/3D) + "-" 9 místní číslo (id ze sequence dokument_xident_seq doplněno na 9 čísel nulami)
    Příklad: "X-M-TX-000000034"
    """
    sequence = f"{get_next_sequence('dokument_xident_seq'):09}"
    prefix = str(
            IDENTIFIKATOR_DOCASNY_PREFIX + region + rada + "-"
        )
    return prefix + sequence


def get_cast_dokumentu_ident(dokument: Dokument) -> str:
    """
    Metoda pro výpočet identu části dokumentu.

    Logika složení je: ident_cely dokumentu + "-D" + pořadové číslo části per dokument doplněno na 3 číslice nulami.
    Pri překročení maxima DJ u dokumentu (999) se vráti uživateli na web chybová hláška.
    Příklad: "M-DD-202100034-D001"
    """
    MAXIMUM: int = 999
    last_digit_count = 3
    max_count = 0
    d = dokument.casti.all().order_by("-ident_cely")
    if d.exists():
        max_count = int(d[0].ident_cely[-last_digit_count:])
    doc_ident = dokument.ident_cely
    if max_count < MAXIMUM:
        ident = doc_ident + "-D" + str(max_count + 1).zfill(last_digit_count)
        return ident
    else:
        logger.error("core.ident_cely.get_cast_dokumentu_ident.maximal_number_document_part",
                     extra={"maximum": str(MAXIMUM)})
        raise MaximalIdentNumberError(max_count)


def get_dj_ident(event: ArcheologickyZaznam) -> str:
    """
    Metoda pro výpočet identu dokumentační jednotky akce.

    Logika složení je: ident_cely arch záznamu + "-D" + pořadové číslo DJ per arch záznam doplněno na 2 číslice nulami.
    Pri překročení maxima DJ u arch záznamu (99) se vráti uživateli na web chybová hláška.
    Příklad: "M-202100034A-D01"
    """
    MAXIMAL_EVENT_DJS: int = 99
    dj_last_digit_count = 2
    max_count = 0
    dj = event.dokumentacni_jednotky_akce.all().order_by("-ident_cely")
    if dj.exists():
        max_count = int(dj[0].ident_cely[-dj_last_digit_count:])
    event_ident = event.ident_cely
    if max_count < MAXIMAL_EVENT_DJS:
        ident = event_ident + "-D" + str(max_count + 1).zfill(dj_last_digit_count)
        return ident
    else:
        logger.error("core.ident_cely.get_dj_ident.maximal_number_dj", extra={"maximum": str(MAXIMAL_EVENT_DJS)})
        raise MaximalIdentNumberError(max_count)


def get_komponenta_ident(zaznam, fedora_transaction: FedoraTransaction) -> str:
    """
    Metoda pro výpočet identu komponenty DJ a dokument části.

    Logika složení je: ident_cely arch záznamu anebo dokumentu + "-D" + pořadové číslo komponenty per záznam doplněno na 3 číslice nulama.
    Pri prekročení maxima komponent u záznamu (999) se vráti uživateli na web chybová hláška.
    Příklad: "M-202100034A-K001", "M-DD-202100034-K001"
    """
    MAXIMAL_KOMPONENTAS: int = 999
    last_digit_count = 3
    max_count = 0
    if isinstance(zaznam, ArcheologickyZaznam):
        for dj in zaznam.dokumentacni_jednotky_akce.all():
            dj.active_transaction = fedora_transaction
            if dj.komponenty is None:
                k = KomponentaVazby(typ_vazby=DOKUMENT_CAST_RELATION_TYPE)
                k.save()
                dj.komponenty = k
                dj.save()
            for komponenta in dj.komponenty.komponenty.all():
                last_digits = int(komponenta.ident_cely[-last_digit_count:])
                if max_count < last_digits:
                    max_count = last_digits
    else:
        for dc in zaznam.casti.all():
            if dc.komponenty is not None:
                for komponenta in dc.komponenty.komponenty.all():
                    last_digits = int(komponenta.ident_cely[-last_digit_count:])
                    if max_count < last_digits:
                        max_count = last_digits
    event_ident = zaznam.ident_cely
    if max_count < MAXIMAL_KOMPONENTAS:
        ident = event_ident + "-K" + str(max_count + 1).zfill(last_digit_count)
        return ident
    else:
        logger.error("core.ident_cely.get_komponenta_ident.maximal_number_komponent",
                     extra={"maximum": str(MAXIMAL_KOMPONENTAS)})
        raise MaximalIdentNumberError(max_count)

def get_sm_from_point(point):
    """
    Metóda pro získaní kladu sm5 pro pian z bodu.
    """
    mapovy_list = Kladysm5.objects.filter(geom__contains=point)
    if mapovy_list.count() == 1:
        return mapovy_list
    else:
        logger.error("core.ident_cely.get_sm_from_point.error")
        raise PianNotInKladysm5Error(point)


def get_temporary_pian_ident(zm50) -> str:
    """
    Metoda pro výpočet dočasného identu pianu.

    Logika složení je: "N-" + číslo zm50 (bez "-") + "-" + 9 místní číslo ze sekvence pian_xident_seq doplněno na 9 číslic.
    Příklad: "N-1224-000123456"
    """
    prefix = "N-" + str(zm50.cislo).replace("-", "").zfill(4) + "-"
    sequence = f"{get_next_sequence('pian_xident_seq'):09}"
    return prefix + sequence


def get_sn_ident(projekt: Projekt) -> str:
    """
    Metóda pro výpočet identu samostatního nálezu projektu.

    Logika složení je: ident_cely projektu + "-N" + pořadové číslo SN per projekt doplněno na 5 číslic nulama.
    Pri prekročení maxima SN u projektu (99999) se vráti uživateli na web chybová hláška.
    Příklad: "M-202100034A-N00001"
    """
    MAXIMAL_FINDS: int = 99999
    last_digit_count = 5
    max_count = 0
    nalez = (
        SamostatnyNalez.objects.filter(projekt=projekt).all().order_by("-ident_cely")
    )
    if nalez.exists():
        max_count = int(nalez[0].ident_cely[-last_digit_count:])
    if max_count < MAXIMAL_FINDS:
        ident = projekt.ident_cely + "-N" + str(max_count + 1).zfill(last_digit_count)
        return ident
    else:
        logger.error("core.ident_cely.get_sn_ident.error", extra={"maximal_sn": MAXIMAL_FINDS})
        raise MaximalIdentNumberError(max_count)


def get_adb_ident(pian: Pian) -> str:
    """
    Metóda pro výpočet identu ADB.

    Logika složení je: "ADB-" + mapno pre sm5 + "-" + číslo sekvence z tabulky 'adb_sekvence' (podle kladysm5) doplněno na 6 číslic nulama.
    Pri prekročení maxima sekvence u ADB (999999) se vráti uživateli na web chybová hláška.
    Příklad: "ADB-PRAH43-000012"
    """
    MAXIMAL_ADBS: int = 999999
    point = None
    if type(pian.geom) == LineString:
        point = pian.geom.interpolate(0.5)
    elif type(pian.geom) == Point:
        point = pian.geom
    elif type(pian.geom) == Polygon:
        point = Centroid(pian.geom)
    else:
        logger.error("core.ident_cely.get_adb_ident.error", extra={"type": str(type(pian.geom))})
        raise NeznamaGeometrieError()
    sm5 = get_sm_from_point(point)[0]
    record_list = "ADB-" + sm5.mapno
    try:
        sequence = AdbSekvence.objects.get(kladysm5=sm5)
    except AdbSekvence.DoesNotExist:
        sequence = AdbSekvence.objects.create(kladysm5=sm5, sekvence=1)
    perm_ident_cely = record_list + "-" + f"{sequence.sekvence:06}"
    # Loop through all of the idents that have been imported
    while True:
        if Adb.objects.filter(ident_cely=perm_ident_cely).exists():
            sequence.sekvence += 1
            logger.warning("core.ident_cely.get_adb_ident.already_exists",
                           extra={"perm_ident_cely": perm_ident_cely, "sequence": sequence.sekvence})
            perm_ident_cely = (
                record_list + "-" + f"{sequence.sekvence:06}"
            )
        else:
            break
    if sequence.sekvence < MAXIMAL_ADBS:
        ident = perm_ident_cely
        sequence.sekvence += 1
        sequence.save(using='urgent')
        return ident, sm5
    else:
        logger.error("core.ident_cely.get_adb_ident.max_adbs_error", extra={"maximal_adbs": MAXIMAL_ADBS})
        raise MaximalIdentNumberError(sequence.sekvence)


def get_temp_lokalita_ident(typ, region, lokalita):
    """
    Metóda pro výpočet dočasného identu lokality.

    Logika složení je: "X-" + region (M anebo C) + "-" + typ + 9 místní číslo ze sekvence lokalita_xident_seq doplněno na 9 číslic.
    
    Příklad: "X-M-L000123456"
    """
    prefix = str(IDENTIFIKATOR_DOCASNY_PREFIX + region + "-" + typ)
    sequence = f"{get_next_sequence('lokalita_xident_seq'):09}"
    return prefix + sequence

def get_temp_akce_ident(region):
    """
    Metóda pro výpočet dočasného identu samostatný akce.

    Logika složení je: "X-" + region (M anebo C) + "-9" + 9 místní číslo ze sekvence akce_xident_seq doplněno na 9 číslic -A.
    
    Příklad: "X-M-9000123456A"
    """
    id_number = f"{get_next_sequence('akce_xident_seq'):09}"
    return str(IDENTIFIKATOR_DOCASNY_PREFIX + region + "-9" + id_number + "A")

def get_temp_ez_ident():
    """
    Metóda pro výpočet dočasného identu externího zdroje.

    Logika složení je: "X-BIB" + 9 místní číslo ze sekvence externi_zdroj_xident_seq doplněno na 9 číslic.
    
    Příklad: "X-BIB-000123456"
    """
    id_number = f"{get_next_sequence('externi_zdroj_xident_seq'):09}"
    return str(IDENTIFIKATOR_DOCASNY_PREFIX + "BIB-" + id_number)


def get_heslar_ident():
    """
    Metoda pro výpočet identu hesláře.
    """
    return f"{Heslar.ident_prefix}-{get_next_sequence('heslar_ident_cely_seq'):06}"

def get_uzivatel_ident():
    """
    Metoda pro výpočet identu uživatele.
    """
    return f"U-{get_next_sequence('auth_user_ident_seq'):06}"

def get_organizace_ident():
    """
    Metoda pro výpočet identu organizce.
    """
    return  f"ORG-{get_next_sequence('organizace_ident_seq'):06}"

def get_osoba_ident():
    """
    Metoda pro výpočet identu osoby.
    """
    return  f"OS-{get_next_sequence('osoba_ident_seq'):06}"

def get_record_from_ident(ident_cely):
    """
    Funkce pro získaní záznamu podle ident cely.
    """
    from projekt.models import Projekt
    from dokument.models import Dokument
    from pas.models import SamostatnyNalez


    if bool(re.fullmatch(r"(C|M|X-C|X-M)-\d{9}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.project", extra={"ident_cely": ident_cely})
        return get_object_or_404(Projekt, ident_cely=ident_cely)
    if bool(re.fullmatch(r"(C|M|X-C|X-M)-\d{9}\D{1}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.archeologicka_akce", extra={"ident_cely": ident_cely})
        return get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if bool(re.fullmatch(r"(C|M|X-C|X-M)-9\d{6,9}\D{1}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.samostatna_akce", extra={"ident_cely": ident_cely})
        return get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if bool(re.fullmatch(r"(C|M|X-C|X-M)-(N|L|K)\d{7,9}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.lokalita", extra={"ident_cely": ident_cely})
        return get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if bool(re.fullmatch(r"(BIB|X-BIB)-\d{7,9}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.zdroj", extra={"ident_cely": ident_cely})
        return get_object_or_404(ExterniZdroj, ident_cely=ident_cely)
    if bool(re.fullmatch(r"(C|M|X-C|X-M)-\w{7,10}\D{1}-D\d{2}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.dokumentacni_jednotka", extra={"ident_cely": ident_cely})
        return get_object_or_404(DokumentacniJednotka, ident_cely=ident_cely)
    if bool(re.fullmatch(r"(C|M|X-C|X-M)-(N|L|K)\d{7,9}-D\d{2}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.dokumentacni_jednotka_lokality", extra={"ident_cely": ident_cely})
        return get_object_or_404(DokumentacniJednotka, ident_cely=ident_cely)
    if bool(re.fullmatch(r"(C|M|X-C|X-M)-\w{7,10}\D{1}-K\d{3}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.komponenta_on_dokumentacni_jednotka",
                     extra={"ident_cely": ident_cely})
        return get_object_or_404(Komponenta, ident_cely=ident_cely)
    if bool(re.fullmatch(r"ADB-\D{4}\d{2}-\d{6}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.adb", extra={"ident_cely": ident_cely})
        return get_object_or_404(Adb, ident_cely=ident_cely)
    if bool(re.fullmatch(r"(X-ADB|ADB)-\D{4}\d{2}-\d{4,6}-V\d{4}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.vyskovy_bod", extra={"ident_cely": ident_cely})
        return get_object_or_404(VyskovyBod, ident_cely=ident_cely)
    if bool(re.fullmatch(r"(P|N)-\d{4}-\d{6,9}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.pian", extra={"ident_cely": ident_cely})
        return get_object_or_404(Pian, ident_cely=ident_cely)
    if bool(re.fullmatch(r"(C|M|X-C|X-M)-(3D)-\d{9}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.dokument_3D", extra={"ident_cely": ident_cely})
        return get_object_or_404(Dokument, ident_cely=ident_cely)
    if bool(re.fullmatch(r"(C|M|X-C|X-M)-(3D)-\d{9}-(D|K)\d{3}", ident_cely)) or bool(
        re.fullmatch(r"3D-(C|M|X-C|X-M)-\w{8,10}-\d{1,9}-(D|K)\d{3}", ident_cely)
    ):
        logger.debug("core.ident_cely.get_record_from_ident.obsah_cast_dokumentu_3D", extra={"ident_cely": ident_cely})
        return get_object_or_404(Dokument, ident_cely=ident_cely[:-5])
    if bool(re.fullmatch(r"(C|M|X-C|X-M)-\D{2}-\d{9}", ident_cely)) or bool(
        re.fullmatch(r"(C|M|X-C|X-M)-\w{8,10}-\D{2}-\d{1,9}", ident_cely)
    ):
        logger.debug("core.ident_cely.get_record_from_ident.dokument", extra={"ident_cely": ident_cely})
        return get_object_or_404(Dokument, ident_cely=ident_cely)
    if bool(re.fullmatch(r"(C|M|X-C|X-M)-\D{2}-\d{9}-(D|K)\d{3}", ident_cely)) or bool(
        re.fullmatch(r"(C|M|X-C|X-M)-\w{8,10}-\D{2}-\d{1,9}-(D|K)\d{3}", ident_cely)
    ):
        logger.debug("core.ident_cely.get_record_from_ident.obsah_cast_dokumentu", extra={"ident_cely": ident_cely})
        return get_object_or_404(Dokument, ident_cely=ident_cely[:-5])
    if bool(re.fullmatch(r"(C|M|X-C|X-M)-\d{9}-N\d{5}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.samostatny_nalez", extra={"ident_cely": ident_cely})
        return get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if bool(re.fullmatch(r"(U)-\d{6}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.uzivatel", extra={"ident_cely": ident_cely})
        return get_object_or_404(User, ident_cely=ident_cely)
    if bool(re.fullmatch(r"(LET)-\d{7}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.externi_zdroj", extra={"ident_cely": ident_cely})
        # return redirect("dokument:detail", ident_cely=ident_cely) TO DO redirect
    if bool(re.fullmatch(r"(HES)-\d{6}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.externi_zdroj", extra={"ident_cely": ident_cely})
        # return redirect("dokument:detail", ident_cely=ident_cely) TO DO redirect
    if bool(re.fullmatch(r"(ORG)-\d{6}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.externi_zdroj", extra={"ident_cely": ident_cely})
        # return redirect("dokument:detail", ident_cely=ident_cely) TO DO redirect
    if bool(re.fullmatch(r"(OS)-\d{6}", ident_cely)):
        logger.debug("core.ident_cely.get_record_from_ident.externi_zdroj", extra={"ident_cely": ident_cely})
        # return redirect("dokument:detail", ident_cely=ident_cely) TO DO redirect
    else:
        logger.debug("core.ident_cely.get_record_from_ident.no_match", extra={"ident_cely": ident_cely})
    return None
