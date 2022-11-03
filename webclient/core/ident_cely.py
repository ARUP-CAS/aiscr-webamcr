import datetime
import logging
from datetime import date

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


def get_temporary_project_ident(project: Projekt, region: str) -> str:
    if project.id is not None:
        id_number = "{0}".format(str(project.id)).zfill(9)
        return "X-" + region + "-" + id_number
    else:
        logger.error("Could not assign temporary identifier to project with Null ID")
        return None


def get_project_event_ident(project: Projekt) -> str:
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
            logger.error("Maximal number of project events is 26.")
            raise MaximalEventCount(MAXIMAL_PROJECT_EVENTS)
    else:
        logger.error("Project is missing ident_cely")
        return None


def get_dokument_rada(typ, material):
    instances = HeslarDokumentTypMaterialRada.objects.filter(
        dokument_typ=typ, dokument_material=material
    )
    if len(instances) == 1:
        return instances[0].dokument_rada
    else:
        logger.error(
            "Nelze priradit radu k dokumentu. Neznama/nejednoznacna kombinace typu {} a materialu. {}".format(
                typ.id, material.id
            )
        )
        raise NelzeZjistitRaduError()


def get_temp_dokument_ident(rada, region):
    MAXIMAL: int = 99999
    if rada == "TX" or rada == "DD" or rada == "3D":
        # [region] - [řada] - [rok][pětimístné pořadové číslo dokumentu pro region-rok-radu]
        prefix = str(
            IDENTIFIKATOR_DOCASNY_PREFIX
            + region
            + "-"
            + rada
            + "-"
            + str(date.today().year)
        )
        d = Dokument.objects.filter(
            ident_cely__regex="^" + prefix + "\\d{5}$"
        ).order_by("-ident_cely")
        if d.filter(ident_cely=str(prefix + "00001")).count() == 0:
            return prefix + "00001"
        else:
            # temp number from empty spaces
            sequence = d[d.count() - 1].ident_cely[-5:]
            logger.warning(sequence)
            while True:
                if d.filter(ident_cely=prefix + sequence).exists():
                    old_sequence = sequence
                    sequence = str(int(sequence) + 1).zfill(5)
                    logger.warning(
                        "Ident "
                        + prefix
                        + old_sequence
                        + " already exists, trying next number "
                        + str(sequence)
                    )
                else:
                    break
            if int(sequence) >= MAXIMAL:
                logger.error(
                    "Maximal number of temporary document ident is "
                    + str(MAXIMAL)
                    + "for given region and rada"
                )
                raise MaximalIdentNumberError(MAXIMAL)
            return prefix + sequence
    else:
        # TODO dodelat dalsi rady
        raise NeocekavanaRadaError("Neocekavana rada dokumentu: " + rada)


def get_cast_dokumentu_ident(dokument: Dokument) -> str:
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
        logger.error("Maximal number of dokument parts is" + str(MAXIMUM))
        raise MaximalIdentNumberError(max_count)


def get_dj_ident(event: ArcheologickyZaznam) -> str:
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
        logger.error("Maximal number of DJs is " + str(MAXIMAL_EVENT_DJS))
        raise MaximalIdentNumberError(max_count)


def get_komponenta_ident(event: ArcheologickyZaznam) -> str:
    MAXIMAL_KOMPONENTAS: int = 999
    last_digit_count = 3
    max_count = 0
    for dj in event.dokumentacni_jednotky_akce.all():
        for komponenta in dj.komponenty.komponenty.all():
            last_digits = int(komponenta.ident_cely[-last_digit_count:])
            if max_count < last_digits:
                max_count = last_digits
    event_ident = event.ident_cely
    if max_count < MAXIMAL_KOMPONENTAS:
        ident = event_ident + "-K" + str(max_count + 1).zfill(last_digit_count)
        return ident
    else:
        logger.error("Maximal number of el komponentas is " + str(MAXIMAL_KOMPONENTAS))
        raise MaximalIdentNumberError(max_count)


# nikde nepouzite
def get_dokument_komponenta_ident(dokument: Dokument) -> str:
    MAXIMAL_KOMPONENTAS: int = 999
    last_digit_count = 3
    max_count = 0
    for dc in dokument.casti.all():
        for komponenta in dc.komponenty.komponenty.all():
            last_digits = int(komponenta.ident_cely[-last_digit_count:])
            if max_count < last_digits:
                max_count = last_digits
    ident = dokument.ident_cely
    if max_count < MAXIMAL_KOMPONENTAS:
        ident = ident + "-K" + str(max_count + 1).zfill(last_digit_count)
        return ident
    else:
        logger.error("Maximal number of el komponentas is " + str(MAXIMAL_KOMPONENTAS))
        raise MaximalIdentNumberError(max_count)


def get_sm_from_point(point):
    mapovy_list = Kladysm5.objects.filter(geom__contains=point)
    if mapovy_list.count() == 1:
        return mapovy_list
    else:
        logger.error(
            "Nelze priradit mapovy list Kladysm5 pianu geometrie. Nula nebo >1 vysledku!"
        )
        raise PianNotInKladysm5Error(point)


def get_temporary_pian_ident(zm50) -> str:
    MAXIMAL_PIANS: int = 999999
    last_digit_count = 6
    max_count = 0
    start = "N-" + str(zm50.cislo).replace("-", "").zfill(4) + "-"
    pian = (
        Pian.objects.filter(ident_cely__startswith=start).all().order_by("-ident_cely")
    )
    if (
        pian.filter(ident_cely=str(start + str("1").zfill(last_digit_count))).count()
        == 0
    ):
        return start + str("1").zfill(last_digit_count)
    else:
        # temp number from empty spaces
        sequence = pian[pian.count() - 1].ident_cely[-last_digit_count:]
        logger.warning(sequence)
        while True:
            if pian.filter(ident_cely=start + sequence).exists():
                old_sequence = sequence
                sequence = str(int(sequence) + 1).zfill(last_digit_count)
                logger.warning(
                    "Ident "
                    + start
                    + old_sequence
                    + " already exists, trying next number "
                    + str(sequence)
                )
            else:
                break
        if int(sequence) >= MAXIMAL_PIANS:
            logger.error(
                "Maximal number of temporary document ident is "
                + str(MAXIMAL_PIANS)
                + "for given region and rada"
            )
            raise MaximalIdentNumberError(MAXIMAL_PIANS)
        return start + sequence


def get_sn_ident(projekt: Projekt) -> str:
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
        logger.error("Maximal number of SN is " + str(MAXIMAL_FINDS))
        raise MaximalIdentNumberError(max_count)


def get_adb_ident(pian: Pian) -> str:
    # Get map list
    # Format: [ADB]-[sm5.mapno]-[NUMBER]
    MAXIMAL_ADBS: int = 999999
    point = None
    if type(pian.geom) == LineString:
        point = pian.geom.interpolate(0.5)
    elif type(pian.geom) == Point:
        point = pian.geom
    elif type(pian.geom) == Polygon:
        point = Centroid(pian.geom)
    else:
        logger.error("Neznamy typ geometrie" + str(type(pian.geom)))
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
            logger.warning(
                "Ident "
                + perm_ident_cely
                + " already exists, trying next number "
                + str(sequence.sekvence)
            )
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
        logger.error("Maximal number of ADBs is " + str(MAXIMAL_ADBS))
        raise MaximalIdentNumberError(sequence.sekvence)


def get_temp_lokalita_ident(typ, region):
    MAXIMAL: int = 9999999
    # [region] - [řada] - [rok][pětimístné pořadové číslo dokumentu pro region-rok-radu]
    prefix = str(IDENTIFIKATOR_DOCASNY_PREFIX + region + "-" + typ)
    l = ArcheologickyZaznam.objects.filter(
        ident_cely__regex="^" + prefix + "\\d{7}$",
        typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA,
    ).order_by("-ident_cely")
    if l.filter(ident_cely=str(prefix + "0000001")).count() == 0:
        return prefix + "0000001"
    else:
        # temp number from empty spaces
        idents = list(l.values_list("ident_cely", flat=True).order_by("ident_cely"))
        idents = [sub.replace(prefix, "") for sub in idents]
        idents = [sub.lstrip("0") for sub in idents]
        idents = [eval(i) for i in idents]
        start = idents[0]
        end = idents[-1]
        missing = sorted(set(range(start, end + 1)).difference(idents))
        logger.debug(missing[0])
        if missing[0] >= MAXIMAL:
            logger.error(
                "Maximal number of temporary document ident is "
                + str(MAXIMAL)
                + "for given region and rada"
            )
            raise MaximalIdentNumberError(MAXIMAL)
        sequence = str(missing[0]).zfill(7)
        return prefix + sequence
