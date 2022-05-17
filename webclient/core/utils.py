import logging
import mimetypes
import zlib

from core.message_constants import (
    VALIDATION_EMPTY,
    VALIDATION_LINE_LENGTH,
    VALIDATION_NOT_MULTIPART,
    VALIDATION_NOT_SIMPLE,
    VALIDATION_NOT_VALID,
)
from dj.models import DokumentacniJednotka
from django.db import connection
from heslar.models import RuianKatastr
from pian.models import Pian
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
        "select id, nazev_stary from public.ruian_katastr where "
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


def get_centre_point(bod, geom):
    try:
        [x0, x1, xlength] = [0.0, 0.0, 1]
        bod.zoom = 17
        if isinstance(geom[0], float):
            [x0, x1, xlength] = [geom[0], geom[1], 1]
        elif isinstance(geom[0][0], float):
            for i in range(0, len(geom)):
                [x0, x1, xlength] = [
                    x0 + geom[i][0],
                    x1 + geom[i][1],
                    len(geom),
                ]
        else:
            for i in range(0, len(geom[0])):
                [x0, x1, xlength] = [
                    x0 + geom[0][i][0],
                    x1 + geom[0][i][1],
                    len(geom[0]),
                ]
        bod.lat = x1 / xlength
        bod.lng = x0 / xlength
        return [bod, geom]
    except Exception as e:
        logger.error("Pian error: " + e)


def get_centre_from_akce(katastr, pian):
    query = (
        "select id,ST_Y(definicni_bod) AS lat, ST_X(definicni_bod) as lng "
        " from public.ruian_katastr where "
        " upper(nazev_stary)=upper(%s) and aktualni='t' limit 1"
    )
    try:
        bod = RuianKatastr.objects.raw(query, [katastr])[0]
        geom = ""
        bod.zoom = 14
        if len(pian) > 1:
            dj = DokumentacniJednotka.objects.get(ident_cely=pian)
            if dj.pian and dj.pian.geom:
                [bod, geom] = get_centre_point(bod, dj.pian.geom)
        return [bod, geom]
    except IndexError:
        logger.error("Could not find cadastre: " + str(katastr) + " with pian: " + pian)
        return None


def get_points_from_envelope(left, bottom, right, top):
    query = (
        "select id,ident_cely,ST_Y(geom) AS lat, ST_X(geom) as lng "
        " from public.projekt where "
        "geom && ST_MakeEnvelope(%s, %s, %s, %s,4326)  limit 100"
    )
    try:
        projekty = Projekt.objects.raw(query, [left, bottom, right, top])
        return projekty
    except IndexError:
        logger.debug("No points in rectangle: %s,%s,%s,%s", left, bottom, right, top)
        return None


def get_all_pians_with_dj(ident_cely, lat, lng):
    query = (
        "select pian.id,pian.ident_cely,ST_AsText(pian.geom) as geometry,dj.ident_cely as dj from public.pian pian "
        " left join public.dokumentacni_jednotka dj on pian.id=dj.pian  and dj.ident_cely like %s "
        "where pian.geom is not null "
        " and abs(ST_Y(ST_Centroid(pian.geom))-%s)<0.1 and abs(ST_X(ST_Centroid(pian.geom))-%s)<0.1"
        " limit 20000"
    )
    try:
        pians = Pian.objects.raw(
            query, [ident_cely[0 : ident_cely.rindex("-")] + "%", lat, lng]
        )
        return pians
    except Exception:
        logger.debug("No pians")
        return None


def get_num_pians_from_envelope(left, bottom, right, top):
    query = (
        "select count(*) from public.pian pian where "
        "pian.geom && ST_MakeEnvelope(%s, %s, %s, %s,4326) limit 1"
    )
    try:
        # num = Pian.objects.raw(query, [left, bottom, right, top])
        cursor = connection.cursor()
        cursor.execute(query, [left, bottom, right, top])
        return cursor.fetchone()[0]
    except IndexError:
        logger.debug("No points in rectangle: %s,%s,%s,%s", left, bottom, right, top)
        return None


def get_pians_from_envelope(left, bottom, right, top, ident_cely):
    query = (
        "select pian.id,pian.ident_cely,ST_AsText(pian.geom) as geometry,"
        " dj.ident_cely as dj,pian.presnost as presnost "
        " from public.pian pian "
        " left join public.dokumentacni_jednotka dj on pian.id=dj.pian  and dj.ident_cely like %s "
        "where pian.geom is not null and "
        "pian.geom && ST_MakeEnvelope(%s, %s, %s, %s,4326) limit 8000"
    )
    try:
        try:
            ident_cely = ident_cely + "%"
        except ValueError:
            ident_cely = ""

        pians = Pian.objects.raw(query, [ident_cely, left, bottom, right, top])
        return pians
    except IndexError:
        logger.debug("No points in rectangle: %s,%s,%s,%s", left, bottom, right, top)
        return None


# CREATE TABLE amcr_clusters_table AS
# WITH query AS (
# select st_clusterkmeans(geom,500) OVER() cid, geom from pian LIMIT 6000
# )
# SELECT cid,  COUNT(*),st_centroid(st_union(geom)) FROM query GROUP BY cid
def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_heat_map(left, bottom, right, top):
    query = "select cid, count, ST_AsText(st_centroid) as geometry from amcr_clusters_table2"
    try:
        # num = Pian.objects.raw(query, [left, bottom, right, top])
        cursor = connection.cursor()
        cursor.execute(query)
        return dictfetchall(cursor)
    except IndexError:
        logger.debug("No heatmap in rectangle: %s,%s,%s,%s", left, bottom, right, top)
        return None


def get_heat_map_density(left, bottom, right, top):
    query = "select max(count) from amcr_clusters_table2"
    try:
        # num = Pian.objects.raw(query, [left, bottom, right, top])
        cursor = connection.cursor()
        cursor.execute(query)
        return cursor.fetchone()[0]
    except IndexError:
        logger.debug("No heatmap in rectangle: %s,%s,%s,%s", left, bottom, right, top)
        return None


def get_validation_messages(text):
    if text == "Not valid":
        return VALIDATION_NOT_VALID
    elif text == "Geometry is empty":
        return VALIDATION_EMPTY
    elif text == "Geometry is not simple":
        return VALIDATION_NOT_SIMPLE
    elif text == "Geometry is multipart":
        return VALIDATION_NOT_MULTIPART
    elif text == "Min. legth of line excesed":
        return VALIDATION_LINE_LENGTH
    elif text == "Parse error":
        return VALIDATION_NOT_VALID
    else:
        return text
