import datetime
import logging
from datetime import date

from adb.models import Adb, Kladysm5
from arch_z.models import ArcheologickyZaznam
from core.constants import IDENTIFIKATOR_DOCASNY_PREFIX
from core.exceptions import (
    MaximalIdentNumberError,
    NelzeZjistitRaduError,
    NeocekavanaRadaError,
    PianNotInKladysm5Error,
)
from django.contrib.gis.db.models.functions import Centroid
from django.contrib.gis.geos import LineString, Point, Polygon
from dokument.models import Dokument
from heslar.models import HeslarDokumentTypMaterialRada, RuianKatastr
from projekt.models import Projekt

logger = logging.getLogger(__name__)


def get_region_from_cadastre(cadastre: RuianKatastr) -> str:
    return cadastre.okres.kraj.rada_id


def get_ident_consecutive_number(region: str, year: int) -> int:
    matching_string = region + "-" + str(year)
    projects = (
        Projekt.objects.filter(ident_cely__contains=matching_string)
        .exclude(ident_cely__contains=IDENTIFIKATOR_DOCASNY_PREFIX)
        .order_by("-ident_cely")
    )
    # Projects ordered descending will have the ident with the largest consecutive number
    if projects:
        perm, region, year, number = projects[0].parse_ident_cely()
        number = int(number) + 1
    else:
        number = 1
    return number


def get_permanent_project_ident(project: Projekt) -> str:
    current_year = datetime.datetime.now().year
    region = get_region_from_cadastre(project.hlavni_katastr)
    number = get_ident_consecutive_number(region, current_year)
    return region + "-" + str(current_year) + "{0}".format(number).zfill(5)


def get_temporary_project_ident(project: Projekt, region: str) -> str:
    if project.id is not None:
        year = datetime.datetime.now().year
        id_number = "{0}".format(str(project.id)).zfill(5)[-5:]
        return "X-" + region + "-" + str(year) + id_number
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
            return None
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


def get_dokument_ident(temporary, rada, region):
    if rada == "TX" or rada == "DD":
        # [region] - [řada] - [rok][pětimístné pořadové číslo dokumentu pro region-rok-radu]
        start = ""
        if temporary:
            start = IDENTIFIKATOR_DOCASNY_PREFIX
        d = Dokument.objects.filter(
            ident_cely__regex="^"
            + start
            + region
            + "-"
            + rada
            + "-"
            + str(date.today().year)
            + "\\d{5}$"
        ).order_by("-ident_cely")
        if d.count() == 0:
            return start + region + "-" + rada + "-" + str(date.today().year) + "00001"
        else:
            return (
                start
                + region
                + "-"
                + rada
                + "-"
                + str(date.today().year)
                + str(int(d[0].ident_cely[-5:]) + 1).zfill(5)
            )
    else:
        raise NeocekavanaRadaError("Neocekavana rada dokumentu: " + rada)


def get_cast_dokumentu_ident(dokument: Dokument) -> str:
    MAXIMUM: int = 99
    max_count = 0
    for d in dokument.casti.all():
        last_digits = int(d.ident_cely[-2:])
        if max_count < last_digits:
            max_count = last_digits
    new_ident = dokument.ident_cely
    if max_count < MAXIMUM:
        ident = new_ident + "-D" + str(max_count + 1).zfill(2)
        return ident
    else:
        logger.error("Maximal number of dokument parts is 99.")
        return None


def get_dj_ident(event: ArcheologickyZaznam) -> str:
    MAXIMAL_EVENT_DJS: int = 99
    max_count = 0
    for dj in event.dokumentacni_jednotky.all():
        last_digits = int(dj.ident_cely[-2:])
        if max_count < last_digits:
            max_count = last_digits
    event_ident = event.ident_cely
    if max_count < MAXIMAL_EVENT_DJS:
        ident = event_ident + "-D" + str(max_count + 1).zfill(2)
        return ident
    else:
        logger.error("Maximal number of DJs is 99.")
        return None


def get_komponenta_ident(event: ArcheologickyZaznam) -> str:
    MAXIMAL_EVENT_DJS: int = 99
    max_count = 0
    for dj in event.dokumentacni_jednotky.all():
        for komponenta in dj.komponenty.komponenty.all():
            last_digits = int(komponenta.ident_cely[-2:])
            if max_count < last_digits:
                max_count = last_digits
    event_ident = event.ident_cely
    if max_count < MAXIMAL_EVENT_DJS:
        ident = event_ident + "-K" + str(max_count + 1).zfill(2)
        return ident
    else:
        logger.error("Maximal number of Komponentas is 99.")
        return None


def get_sm_from_point(point):
    mapovy_list = Kladysm5.objects.filter(geom__contains=point)
    if mapovy_list.count() == 1:
        return mapovy_list
    else:
        logger.error(
            "Nelze priradit mapovy list Kladysm5 pianu geometrie. Nula nebo >1 vysledku!"
        )
        raise PianNotInKladysm5Error(point)


def get_adb_ident(pian) -> str:
    # Get map list
    point = None
    if type(pian.geom) == LineString:
        point = pian.geom.interpolate(0.5)
    elif type(pian.geom) == Point:
        point = pian.geom
    elif type(pian.geom) == Polygon:
        point = Centroid(pian.geom)
    else:
        logger.error("Neznamy typ geometrie" + str(type(pian.geom)))
        return None, None
    sm5 = get_sm_from_point(point)[0]
    MAXIMAL_ADBS: int = 9999
    max_count = 0
    for adb in Adb.objects.all():
        last_digits = int(adb.ident_cely[-4:])
        if max_count < last_digits:
            max_count = last_digits
    if max_count < MAXIMAL_ADBS:
        ident = "ADB-" + sm5.mapno + "-" + str(max_count + 1).zfill(4)
        return ident, sm5
    else:
        logger.error("Maximal number of ADBs is 9999.")
        raise MaximalIdentNumberError(max_count)
