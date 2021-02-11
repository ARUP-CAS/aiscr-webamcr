import datetime
import logging

from core.constants import IDENTIFIKATOR_DOCASNY_PREFIX
from heslar.models import RuianKatastr
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
