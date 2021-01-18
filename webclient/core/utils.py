import logging
import mimetypes

from heslar.models import RuianKatastr

logger = logging.getLogger(__name__)


def get_mime_type(file_name):
    mime_type = mimetypes.guess_type(file_name)[0]
    # According to RFC 4180 csv is text/csv
    if file_name.endswith(".csv"):
        mime_type = "text/csv"
    return mime_type


def get_cadastre_from_point(point):
    query = (
        "select id, nazev from public.ruian_katastr where "
        "ST_Contains(hranice,ST_GeomFromText('POINT (%s %s)',4326) ) and aktualni='t' limit 1"
    )
    try:
        katastr = RuianKatastr.objects.raw(query, [point[0], point[1]])[0]
        return katastr
    except IndexError:
        logger.debug("Could not find cadastre for pont: " + str(point))
        return None
