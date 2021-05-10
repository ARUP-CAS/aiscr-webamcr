import logging
import mimetypes
import zlib

from heslar.models import RuianKatastr
from projekt.models import Projekt

logger = logging.getLogger(__name__)


def get_mime_type(file_name):
    mime_type = mimetypes.guess_type(file_name)[0]
    # According to RFC 4180 csv is text/csv
    if file_name.endswith(".csv"):
        mime_type = "text/csv"
    return mime_type


def calculate_crc_32(file):
    prev = 0
    for eachLine in file:
        prev = zlib.crc32(eachLine, prev)
    checksum = "%d" % (prev & 0xFFFFFFFF)
    return checksum


def get_cadastre_from_point(point):
    query = (
        "select id, nazev from public.ruian_katastr where "
        "ST_Contains(hranice,ST_GeomFromText('POINT (%s %s)',4326) ) and aktualni='t' limit 1"
    )
    try:
        katastr = RuianKatastr.objects.raw(query, [point[0], point[1]])[0]
        logger.debug(
            "Point: "
            + str(point[0])
            + ", "
            + str(point[1])
            + " cadastre: "
            + str(type(katastr))
        )
        return katastr
    except IndexError:
        logger.error("Could not find cadastre for pont: " + str(point))
        return None


def get_points_from_envelope(left, bottom, right, top):
    query = (
        "select id,ident_cely,ST_Y(geom) AS lat, ST_X(geom) as lng from public.projekt where "
        "geom && ST_MakeEnvelope(%s, %s, %s, %s,4326)  limit 100"
    )
    try:
        projekty = Projekt.objects.raw(query, [left, bottom, right, top])
        return projekty
    except IndexError:
        logger.debug("No points in rectangle: %s,%s,%s,%s", left, bottom, right, top)
        return None
