import json
import logging
import mimetypes
import zlib

import core.message_constants as mc
import requests
import structlog
from arch_z.models import ArcheologickyZaznam
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

logger = logging.getLogger(__name__)
logger_s = structlog.get_logger(__name__)


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
        logger.error("Could not find cadastre for point: " + str(point))
        return None


def get_cadastre_from_point_with_geometry(point):
    query = (
        "select id, nazev_stary,ST_AsText(definicni_bod) AS db, ST_AsText(hranice) AS hranice from public.ruian_katastr where "
        "ST_Contains(hranice,ST_GeomFromText('POINT (%s %s)',4326) ) and aktualni='t' limit 1"
    )
    try:
        logger.debug([point[0], point[1]])
        cursor = connection.cursor()
        cursor.execute(query, [point[0], point[1]])
        line = cursor.fetchone()
        return [line[1], line[2], line[3]]
    except IndexError:
        logger.error("Could not find cadastre for ponit: " + str(point))
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


def get_all_pians_with_akce(ident_cely):
    query = (
        " (SELECT A.id,A.ident_cely,ST_AsText(A.geom) as geometry, A.dj,katastr.nazev_stary AS katastr_nazev, katastr.id as ku_id"
        " FROM public.ruian_katastr katastr "
        " JOIN ( SELECT pian.id,pian.ident_cely, "
        "  CASE "
        "  WHEN ST_GeometryType(pian.geom) = 'ST_LineString' THEN st_centroid(pian.geom)  "
        "  WHEN ST_GeometryType(pian.geom) = 'ST_LineString' THEN st_lineinterpolatepoint(pian.geom,0.5)"
        "  ELSE st_centroid(pian.geom) END AS geom,"
        " dj.ident_cely as dj"
        " from public.pian pian "
        " join public.dokumentacni_jednotka dj on pian.id=dj.pian  and dj.ident_cely LIKE %s"
        " WHERE dj.ident_cely IS NOT NULL ) AS A ON ST_Intersects(katastr.hranice,geom)"
        " ORDER BY A.ident_cely "
        " LIMIT 1 )"
        " union all "
        "(select pian.id,pian.ident_cely,ST_AsText(pian.geom) as geometry,dj.ident_cely as dj, katastr.nazev_stary AS katastr_nazev, katastr.id as ku_id"
        " from public.pian pian"
        " left join public.dokumentacni_jednotka dj on pian.id=dj.pian  and dj.ident_cely LIKE %s"
        " left join public.ruian_katastr katastr ON ST_Intersects(katastr.hranice,pian.geom)"
        " where dj.ident_cely IS NOT NULL"
        " and katastr.aktualni=true"
        " order by dj.ident_cely, katastr_nazev"
        " limit 990)"
    )
    try:
        cursor = connection.cursor()
        cursor.execute(query, [ident_cely + "-%", ident_cely + "-%"])
        back = []
        for line in cursor.fetchall():
            back.append(
                {
                    "id": line[0],
                    "pian_ident_cely": line[1],
                    "pian_geom": line[2],
                    "dj": line[3],
                    "dj_katastr": line[4],
                    "dj_katastr_id": line[5],
                }
            )
        return back

    except Exception as e:
        logger.debug(e)
        return None


def update_main_katastr_within_ku(ident_cely, ku_nazev_stary):
    akce_ident_cely = ident_cely.split("-D")[0]

    query_update_archz = (
        "update PUBLIC.archeologicky_zaznam set hlavni_katastr="
        " (select id from public.ruian_katastr where nazev_stary=%s and aktualni='t' limit 1)"
        " where ident_cely = %s and typ_zaznamu IN('L')"
    )

    try:
        if len(ku_nazev_stary) > 2:
            cursor = connection.cursor()
            cursor.execute(query_update_archz, [ku_nazev_stary, akce_ident_cely])
    except IndexError:
        return None


def update_all_katastr_within_akce_or_lokalita(ident_cely):
    logger_s.debug("core.utils.update_all_katastr_within_akce_or_lokalita.start")
    akce_ident_cely = ident_cely.split("-D")[0]
    # logger.debug("dj.ident_cely %s", [ident_cely])
    # logger.debug("akce.ident_cely %s", [akce_ident_cely])
    hlavni_name = ""
    hlavni_id = None
    ostatni_name = []
    ostatni_id = []
    for line in get_all_pians_with_akce(akce_ident_cely):
        if hlavni_id == None:
            hlavni_id = line["dj_katastr_id"]
            hlavni_name = line["dj_katastr"]
        elif (
            hlavni_name != line["dj_katastr"] and line["dj_katastr"] not in ostatni_name
        ):
            ostatni_name.append(line["dj_katastr"])
            ostatni_id.append(line["dj_katastr_id"])
    ostatni_name = sorted(ostatni_name)
    # ostatni_id = sorted(ostatni_id)

    query_select_archz = (
        "select  id from PUBLIC.archeologicky_zaznam "
        " where typ_zaznamu IN('A','L') and ident_cely = %s limit 1"
    )
    query_update_archz = (
        "update PUBLIC.archeologicky_zaznam set hlavni_katastr=%s where id = %s"
    )
    query_select_other = (
        "select katastr_id from PUBLIC.archeologicky_zaznam_katastr "
        " where archeologicky_zaznam_id=%s and katastr_id in %s"
    )
    query_insert_other = "insert into PUBLIC.archeologicky_zaznam_katastr(archeologicky_zaznam_id,katastr_id)  values(%s,%s)"
    query_delete_other = "delete from PUBLIC.archeologicky_zaznam_katastr where archeologicky_zaznam_id=%s and katastr_id not in %s"
    try:
        cursor = connection.cursor()
        cursor.execute(query_select_archz, [akce_ident_cely])
        zaznam_id = cursor.fetchone()[0]
        if len(str(zaznam_id)) > 0:
            if hlavni_id != None:
                cursor.execute(query_update_archz, [hlavni_id, zaznam_id])
            if len(ostatni_id):
                cursor.execute(query_select_other, [zaznam_id, tuple(ostatni_id)])
                ostatni_already_inserted = []
                for ostatni_inserted in cursor.fetchall():
                    ostatni_already_inserted.append(ostatni_inserted[0])
                for ostatni_one in ostatni_id:
                    if int(ostatni_one) not in ostatni_already_inserted:
                        cursor.execute(query_insert_other, [zaznam_id, ostatni_one])
            if len(ostatni_id) == 0:  # HotFix for delete DML
                ostatni_id.append(0)
            cursor.execute(query_delete_other, [zaznam_id, tuple(ostatni_id)])
    except IndexError:
        return None
    logger_s.debug("core.utils.update_all_katastr_within_akce_or_lokalita.end")


def get_centre_from_akce(katastr, pian):
    query = (
        "select id,ST_Y(definicni_bod) AS lat, ST_X(definicni_bod) as lng "
        " from public.ruian_katastr where "
        " upper(nazev_stary)=upper(%s) and aktualni='t' limit 1"
    )
    try:
        bod = RuianKatastr.objects.raw(query, [katastr])[0]
        geom = ""
        presnost = 4
        bod.zoom = 14
        if len(pian) > 1:
            dj = DokumentacniJednotka.objects.get(ident_cely=pian)
            if dj.pian and dj.pian.geom:
                [bod, geom] = get_centre_point(bod, dj.pian.geom)
                presnost = dj.pian.presnost.zkratka
        return [bod, geom, presnost]
    except IndexError:
        logger.error("Could not find cadastre: " + str(katastr) + " with pian: " + pian)
        return None


def get_points_from_envelope(left, bottom, right, top):
    from projekt.models import Projekt

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
        "select pian.id,pian.ident_cely,"
        " ST_AsText(pian.geom) as geometry,"
        " ST_AsText(st_centroid(pian.geom)) as centroid, "
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


def get_num_projects_from_envelope(left, bottom, right, top):
    query = (
        "select count(*) from public.projekt p where "
        "p.geom && ST_MakeEnvelope(%s, %s, %s, %s,4326) limit 1"
    )
    try:
        # num = Pian.objects.raw(query, [left, bottom, right, top])
        cursor = connection.cursor()
        cursor.execute(query, [left, bottom, right, top])
        return cursor.fetchone()[0]
    except IndexError:
        logger.debug("No points in rectangle: %s,%s,%s,%s", left, bottom, right, top)
        return None


def get_projects_from_envelope(left, bottom, right, top):
    from projekt.models import Projekt

    query = (
        "select p.id,p.ident_cely,ST_AsText(p.geom) as geometry "
        "from public.projekt p "
        "where p.geom is not null and "
        "p.geom && ST_MakeEnvelope(%s, %s, %s, %s,4326) limit 8000"
    )
    try:
        pians = Projekt.objects.raw(query, [left, bottom, right, top])
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


def get_heatmap_pian(left, bottom, right, top, zoom):
    query = "select count, ST_AsText(st_centroid) as geometry from amcr_heat_pian_l2"
    query_zoom = (
        "select count*3 as count, ST_AsText(st_centroid) as geometry "
        "from amcr_heat_pian_lx2 where st_centroid && ST_MakeEnvelope(%s, %s, %s, %s,4326)"
    )
    try:
        # num = Pian.objects.raw(query, [left, bottom, right, top])
        cursor = connection.cursor()
        if zoom > 12:
            cursor.execute(query_zoom, [left, bottom, right, top])
        else:
            cursor.execute(query)
        return dictfetchall(cursor)
    except IndexError:
        logger.debug("No heatmap in rectangle: %s,%s,%s,%s", left, bottom, right, top)
        return None


def get_heatmap_pian_density(left, bottom, right, top, zoom):
    query = "select max(count) from amcr_heat_pian_l2"
    query_zoom = "select max(count) from amcr_heat_pian_lx2 where st_centroid && ST_MakeEnvelope(%s, %s, %s, %s,4326)"
    try:
        # num = Pian.objects.raw(query, [left, bottom, right, top])
        cursor = connection.cursor()
        if zoom > 12:
            cursor.execute(query_zoom, [left, bottom, right, top])
        else:
            cursor.execute(query)
        return cursor.fetchone()[0]
    except IndexError:
        logger.debug("No heatmap in rectangle: %s,%s,%s,%s", left, bottom, right, top)
        return None


def get_heatmap_project(left, bottom, right, top, zoom):
    query = "select count*30 as count, ST_AsText(st_centroid) as geometry from amcr_heat_projekt_l2"
    query_zoom = (
        "select count*30 as count, ST_AsText(st_centroid) as geometry from amcr_heat_projekt_lx2 "
        "where st_centroid && ST_MakeEnvelope(%s, %s, %s, %s,4326)"
    )
    try:
        # num = Pian.objects.raw(query, [left, bottom, right, top])
        cursor = connection.cursor()
        if zoom > 12:
            cursor.execute(query_zoom, [left, bottom, right, top])
        else:
            cursor.execute(query)
        return dictfetchall(cursor)
    except IndexError:
        logger.debug("No heatmap in rectangle: %s,%s,%s,%s", left, bottom, right, top)
        return None


def get_heatmap_project_density(left, bottom, right, top, zoom):
    query = "select max(count) from amcr_heat_projekt_l2"
    query_zoom = (
        "select max(count) from amcr_heat_projekt_lx2 "
        "where st_centroid && ST_MakeEnvelope(%s, %s, %s, %s,4326)"
    )
    try:
        # num = Pian.objects.raw(query, [left, bottom, right, top])
        cursor = connection.cursor()
        if zoom > 12:
            cursor.execute(query_zoom, [left, bottom, right, top])
        else:
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


def get_transform_towgs84(cy, cx):
    url = "https://geoportal.cuzk.cz/(S(k10mxdjzq1pv5tkgcghghohf))/WCTSHandlerhld.ashx"

    query = (
        "source=Coordinates&"
        "sourceSRS=urn%3Aogc%3Adef%3Acrs%2Ccrs%3AEPSG%3A%3A2065%2Ccrs%3AEPSG%3A%3A5705&"
        "targetSRS=urn%3Aogc%3Adef%3Acrs%3AEPSG%3A%3A4979&"
        "sourceXYorder=yx&"
        "targetXYorder=xy&"
        "sourceSixtiethView=false&"
        "targetSixtiethView=false&"
        "coordinates=" + str(cy) + "+" + str(cx) + "+300"
        "&time=2022-05-20"
    )

    headers = {
        "Host": "geoportal.cuzk.cz",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "content-type": "application/x-www-form-urlencoded",
        "x-requested-with": "XMLHttpRequest",
        "Origin": "https://geoportal.cuzk.cz",
        "Connection": "keep-alive",
        "Referer": "https://geoportal.cuzk.cz/(S(k10mxdjzq1pv5tkgcghghohf))/Default.aspx?head_tab=sekce-01-gp&mode=TextMeta&text=wcts&menu=19",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
    }
    try:
        # logger.debug(url)
        # logger.debug(query)
        r = requests.post(url, data=query, headers=headers)
        # logger.debug(r.status_code)
        # logger.debug(r.text)
        body = json.loads(r.text)["Coordinates"].split(" ")
        return [body[0], body[1]]
    except IndexError:
        logger.error("Error during transformation")
        return None


def get_multi_transform_towgs84(jtsk_points):
    logger.debug("get_multi_transform_towgs84")

    url = "https://geoportal.cuzk.cz/(S(k10mxdjzq1pv5tkgcghghohf))/WCTSHandlerhld.ashx"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Content-Type": "multipart/form-data; boundary=amcr-multipart-block",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "iframe",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }
    query = (
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="source"\r\n\r\nFile\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="sourceSRS"\r\n\r\nurn:ogc:def:crs,crs:EPSG::2065,crs:EPSG::5705\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="targetSRS"\r\n\r\nurn:ogc:def:crs:EPSG::4979\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="sourceXYorder"\r\n\r\nyx\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="targetXYorder"\r\n\r\nxy\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="sourceSixtiethView"\r\n\r\nfalse\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="targetSixtiethView"\r\n\r\false\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="time"\r\n\r\n2022-05-20\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="wcts_fileType"\r\n\r\ntext\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="wcts_file1"; filename="test.souradnice2.txt"\r\n'
        "Content-Type: text/plain\r\n\r\n"
    )
    incr = 0
    for p in jtsk_points:
        incr += 1
        query = (
            query
            + "PP"
            + str(incr)
            + "     "
            + str(p[0])
            + "    "
            + str(p[1])
            + "    300\r\n"
        )  # "TB02     646860.290    1060814.217    669.262   nepovinný popis\r\n" \
    query = query + "--amcr-multipart-block--\r\n"

    try:
        # logger.debug(url)
        # logger.debug(query)
        r = requests.post(url, data=query, headers=headers)
        # logger.debug(r.status_code)
        points = []
        for line in r.text.split("\n"):
            if len(line) > 5:
                p = line.split("\t")[1].split(" ")
                logger.debug(p)
                points.append([p[0], p[1]])

        return points
    except IndexError:
        logger.error("Error during transformation")
        return None


def get_message(az, message):
    return str(
        getattr(
            mc,
            str(
                dict(ArcheologickyZaznam.CHOICES)[az.typ_zaznamu].upper()
                + "_"
                + message
            ),
        )
    )
