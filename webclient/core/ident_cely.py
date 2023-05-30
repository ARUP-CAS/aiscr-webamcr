import logging
from datetime import date
from django.db import connection

from adb.models import Adb, Kladysm5, AdbSekvence
from arch_z.models import ArcheologickyZaznam
from core.constants import IDENTIFIKATOR_DOCASNY_PREFIX
from core.exceptions import (
    MaximalIdentNumberError,
    NelzeZjistitRaduError,
    NeocekavanaRadaError,
    NeznamaGeometrieError,
    PianNotInKladysm5Error,
    MaximalEventCount,
)
from django.contrib.gis.db.models.functions import Centroid
from django.contrib.gis.geos import LineString, Point, Polygon
from dokument.models import Dokument
from heslar.models import HeslarDokumentTypMaterialRada
from pas.models import SamostatnyNalez
from pian.models import Pian
from projekt.models import Projekt

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
    id_number = "{0}".format(str(get_next_sequence("projekt_xident_seq"))).zfill(9)
    return "X-" + region + "-" + id_number
    

def get_project_event_ident(project: Projekt) -> str:
    """
    Metóda pro výpočet identu projektové akce.

    Logika složení je: ident_cely projektu + písmeno abecedy v postoupnosti od A po Z
    Pri prekročení maxima čísla sekvence (99999) se vráti uživateli na web chybová hláška.
    Příklad: "M-202100034A"
    """
    MAXIMAL_PROJECT_EVENTS: int = 26
    if project.ident_cely:
        predicate = project.ident_cely + "%"
        q = "select id, ident_cely from public.archeologicky_zaznam where ident_cely like %s order by ident_cely desc"
        idents = ArcheologickyZaznam.objects.raw(q, [predicate])
        if len(idents) < MAXIMAL_PROJECT_EVENTS:
            if idents:
                last_ident = idents[0].ident_cely
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
    Metóda pro získaní rady dokumentu podle typu a materiálu dokumentu.
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
    Metóda pro výpočet dočasného identu dokumentu.

    Logika složení je: "X-" + region (M alebo C) + "-" + řada (TX/DD/3D) + "-" 9 místne číslo (id ze sequence dokument_xident_seq doplněno na 9 čísel nulama)
    Příklad: "X-M-TX-000000034"
    """
    sequence = "{0}".format(str(get_next_sequence("dokument_xident_seq"))).zfill(9)
    prefix = str(
            IDENTIFIKATOR_DOCASNY_PREFIX + region + rada + "-"
        )
    return prefix + sequence


def get_cast_dokumentu_ident(dokument: Dokument) -> str:
    """
    Metóda pro výpočet identu části dokumentu.

    Logika složení je: ident_cely dokumentu + "-D" + poradové číslo části per dokument doplněno na 3 číslice nulama.
    Pri prekročení maxima DJ u dokumentu (999) se vráti uživateli na web chybová hláška.
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
    Metóda pro výpočet identu dokumentační jednotky akce.

    Logika složení je: ident_cely arch záznamu + "-D" + pořadové číslo DJ per arch záznam doplněno na 2 číslice nulama.
    Pri prekročení maxima DJ u arch záznamu (99) se vráti uživateli na web chybová hláška.
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


def get_komponenta_ident(zaznam) -> str:
    """
    Metóda pro výpočet identu komponenty DJ a dokument části.

    Logika složení je: ident_cely arch záznamu anebo dokumentu + "-D" + pořadové číslo komponenty per záznam doplněno na 3 číslice nulama.
    Pri prekročení maxima komponent u záznamu (999) se vráti uživateli na web chybová hláška.
    Příklad: "M-202100034A-K001", "M-DD-202100034-K001"
    """
    MAXIMAL_KOMPONENTAS: int = 999
    last_digit_count = 3
    max_count = 0
    if isinstance(zaznam, ArcheologickyZaznam):
        for dj in zaznam.dokumentacni_jednotky_akce.all():
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
    Metóda pro výpočet dočasného identu pianu.

    Logika složení je: "N-" + číslo zm50 (bez "-") + "-" + 9 místne číslo ze sekvence pian_xident_seq doplňeno na 9 číslic.
    Příklad: "N-1224-000123456"
    """
    prefix = "N-" + str(zm50.cislo).replace("-", "").zfill(4) + "-"
    sequence = "{0}".format(str(get_next_sequence("pian_xident_seq"))).zfill(9)
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
    perm_ident_cely = record_list + "-" + "{0}".format(sequence.sekvence).zfill(6)
    # Loop through all of the idents that have been imported
    while True:
        if Adb.objects.filter(ident_cely=perm_ident_cely).exists():
            sequence.sekvence += 1
            logger.warning("core.ident_cely.get_adb_ident.already_exists",
                           extra={"perm_ident_cely": perm_ident_cely, "sequence": sequence.sekvence})
            perm_ident_cely = (
                record_list + "-" + "{0}".format(sequence.sekvence).zfill(6)
            )
        else:
            break
    if sequence.sekvence < MAXIMAL_ADBS:
        ident = perm_ident_cely
        sequence.sekvence += 1
        sequence.save()
        return ident, sm5
    else:
        logger.error("core.ident_cely.get_adb_ident.max_adbs_error", extra={"maximal_adbs": MAXIMAL_ADBS})
        raise MaximalIdentNumberError(sequence.sekvence)


def get_temp_lokalita_ident(typ, region, lokalita):
    """
    Metóda pro výpočet dočasného identu lokality.

    Logika složení je: "X-" + region (M anebo C) + "-" + typ + 9 místne číslo ze sekvence lokalita_xident_seq doplňeno na 9 číslic.
    
    Příklad: "X-M-L000123456"
    """
    prefix = str(IDENTIFIKATOR_DOCASNY_PREFIX + region + "-" + typ)
    sequence = "{0}".format(str(get_next_sequence("lokalita_xident_seq"))).zfill(9)
    return prefix + sequence

def get_temp_akce_ident(region):
    """
    Metóda pro výpočet dočasného identu samostatný akce.

    Logika složení je: "X-" + region (M anebo C) + "-9" + 9 místne číslo ze sekvence akce_xident_seq doplňeno na 9 číslic -A.
    
    Příklad: "X-M-9000123456A"
    """
    id_number = "{0}".format(str(get_next_sequence("akce_xident_seq"))).zfill(9)
    return str(IDENTIFIKATOR_DOCASNY_PREFIX + region + "-9" + id_number + "A")

def get_temp_ez_ident():
    """
    Metóda pro výpočet dočasného identu externího zdroje.

    Logika složení je: "X-BIB" + 9 místne číslo ze sekvence externi_zdroj_xident_seq doplňeno na 9 číslic.
    
    Příklad: "X-BIB-000123456"
    """
    id_number = "{0}".format(str(get_next_sequence("externi_zdroj_xident_seq"))).zfill(9)
    return str(IDENTIFIKATOR_DOCASNY_PREFIX + "BIB-" + id_number)