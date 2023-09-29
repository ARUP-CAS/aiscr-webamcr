import json
import logging
import mimetypes
import zlib

from django.urls import reverse
from django.utils.html import format_html

import core.message_constants as mc
import requests
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
from django_tables2_column_shifter.tables import ColumnShiftTableBootstrap4
from heslar.models import RuianKatastr
from pian.models import Pian

logger = logging.getLogger(__name__)


def get_mime_type(file_name):
    """
    Funkce pro získaní mime typu pro soubor.
    """
    mime_type = mimetypes.guess_type(file_name)[0]
    # According to RFC 4180 csv is text/csv
    if file_name.endswith(".csv"):
        mime_type = "text/csv"
    return mime_type


def calculate_crc_32(file):
    """
    Počítá crc32 ze souboru (int32), transformuje ho na string a doplňuje ho na 13 znaků.
    """
    prev = 0
    for eachLine in file:
        prev = zlib.crc32(eachLine, prev)
    checksum = "%d" % (prev & 0xFFFFFFFF)
    return checksum.zfill(13)


def get_cadastre_from_point(point):
    """
    Funkce pro získaní katastru z bodu geomu.
    """
    query = (
        "select id, nazev_stary from public.ruian_katastr where "
        "ST_Contains(hranice,ST_GeomFromText('POINT (%s %s)',4326) ) and aktualni='t' limit 1"
    )
    try:
        katastr = RuianKatastr.objects.raw(query, [point[0], point[1]])[0]
        logger.debug("core.utils.get_cadastre_from_point.start",
                     extra={"point_0": point[0], "point_1": point[1], "katastr": katastr})
        return katastr
    except IndexError:
        logger.error("core.utils.get_cadastre_from_point.error", extra={"point": point})
        return None


def get_cadastre_from_point_with_geometry(point):
    """
    Funkce pro získaní katastru s geometrií z bodu geomu.
    """
    query = (
        "select id, nazev_stary,ST_AsText(definicni_bod) AS db, ST_AsText(hranice) AS hranice from public.ruian_katastr where "
        "ST_Contains(hranice,ST_GeomFromText('POINT (%s %s)',4326) ) and aktualni='t' limit 1"
    )
    try:
        logger.debug("core.utils.get_cadastre_from_point.start", extra={"point_0": point[0], "point_1": point[1]})
        cursor = connection.cursor()
        cursor.execute(query, [point[0], point[1]])
        line = cursor.fetchone()
        return [line[1], line[2], line[3]]
    except IndexError:
        logger.error("core.utils.get_cadastre_from_point_with_geometry.error", extra={"point": point})
        return None


def get_centre_point(bod, geom):
    """
    Funkce pro získani stredového bodu z bodu a geomu.
    """
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
        elif isinstance(geom[0][0][0], tuple):
            for i in range(0, len(geom)-1):
                [x0, x1, xlength] = [
                    x0 + geom[0][0][i][0],
                    x1 + geom[0][0][i][1],
                    len(geom)-1,
                ]
        else:
            for i in range(0, len(geom[0])-1):
                [x0, x1, xlength] = [
                    x0 + geom[0][i][0],
                    x1 + geom[0][i][1],
                    len(geom[0])-1,
                ]
        bod.lat = x1 / xlength
        bod.lng = x0 / xlength
        return [bod, geom]
    except Exception as e:
        logger.error("core.utils.get_cadastre_from_point_with_geometry.error", extra={"e": e})


def get_all_pians_with_akce(ident_cely):
    """
    Funkce pro získaní všech pianů s akci.
    """
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
        logger.debug("core.utils.get_all_pians_with_akce.exception", extra={"e": e})
        return None


def update_main_katastr_within_ku(ident_cely, ku_nazev_stary):
    """
    Funkce pro update katastru u akce podle katastrálního území.
    """
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
    """
    Funkce pro update katastru u akce a lokalit.
    """
    logger.debug("core.utils.update_all_katastr_within_akce_or_lokalita.start")
    akce_ident_cely = ident_cely.split("-D")[0]
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
    logger.debug("core.utils.update_all_katastr_within_akce_or_lokalita.end")


def get_centre_from_akce(katastr, pian):
    """
    Funkce pro bodu, geomu a presnosti z akce.
    """
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
        logger.error("core.utils.get_centre_from_akce.error", extra={"katastr": katastr, "pian": pian})
        return None


def get_points_from_envelope(left, bottom, right, top):
    """
    Funkce pro získaní projektů a jeho geomu podle čtverce.
    """
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
        logger.debug("core.utils.get_centre_from_akce.no_points",
                     extra={"left": left, "bottom": bottom, "right": right, "top": top})
        return None


def get_all_pians_with_dj(ident_cely, lat, lng):
    """
    Funkce pro získaní pianů s DJ podle ident_cely DJ a souradnic.
    """
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
        logger.debug("core.utils.get_all_pians_with_dj.no_pians")
        return None


def get_num_pians_from_envelope(left, bottom, right, top):
    """
    Funkce pro získaní počtu pianů ze čtverce.
    """
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
        logger.debug("core.utils.get_num_pians_from_envelope.no_points",
                     extra={"left": left, "bottom": bottom, "right": right, "top": top})
        return None


def get_pians_from_envelope(left, bottom, right, top, ident_cely):
    """
    Funkce pro získaní pianů ze čtverce.
    """
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
        logger.debug("core.utils.get_pians_from_envelope.no_points",
                     extra={"left": left, "bottom": bottom, "right": right, "top": top})
        return None


def get_num_projects_from_envelope(left, bottom, right, top):
    """
    Funkce pro získaní počtu projektů ze čtverce.
    """
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
        logger.debug("core.utils.get_num_projects_from_envelope.no_points",
                     extra={"left": left, "bottom": bottom, "right": right, "top": top})
        return None


def get_projects_from_envelope(left, bottom, right, top):
    """
    Funkce pro získaní projektů ze čtverce.
    """
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
        logger.debug("core.utils.get_projects_from_envelope.no_points",
                     extra={"left": left, "bottom": bottom, "right": right, "top": top})
        return None


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_heatmap_pian(left, bottom, right, top, zoom):
    """
    Funkce pro získaní heat mapy pianů ze čtverce.
    """
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
        logger.debug("core.utils.get_heatmap_pian.no_heatmap",
                     extra={"left": left, "bottom": bottom, "right": right, "top": top})
        return None


def get_heatmap_pian_density(left, bottom, right, top, zoom):
    """
    Funkce pro získaní heat mapy hustoty pianů ze čtverce.
    """
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
        logger.debug("core.utils.get_heatmap_pian_density.no_heatmap",
                     extra={"left": left, "bottom": bottom, "right": right, "top": top})
        return None


def get_heatmap_project(left, bottom, right, top, zoom):
    """
    Funkce pro získaní heat mapy projektů ze čtverce.
    """
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
        logger.debug("core.utils.get_heatmap_project.no_heatmap",
                     extra={"left": left, "bottom": bottom, "right": right, "top": top})
        return None


def get_heatmap_project_density(left, bottom, right, top, zoom):
    """
    Funkce pro získaní heat mapy hustoty projektů ze čtverce.
    """
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
        logger.debug("core.utils.get_heatmap_project_density.no_heatmap",
                     extra={"left": left, "bottom": bottom, "right": right, "top": top})
        return None


def get_validation_messages(text):
    """
    Funkce pro získaní textu validační chyby.
    """
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
    """
    Funkce pro transformaci na wgs84.
    """
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
        r = requests.post(url, data=query, headers=headers)
        body = json.loads(r.text)["Coordinates"].split(" ")
        return [body[0], body[1]]
    except IndexError:
        logger.error("core.utils.get_transform_towgs84.transformation_error")
        return None


def get_multi_transform_towgs84(jtsk_points):
    """
    Funkce pro transformaci více jtsk bodů na wgs84.
    """
    logger.debug("core.utils.get_multi_transform_towgs84.start")

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
        r = requests.post(url, data=query, headers=headers)
        points = []
        for line in r.text.split("\n"):
            if len(line) > 5:
                p = line.split("\t")[1].split(" ")
                logger.debug("core.utils.get_multi_transform_towgs84.finished", extra={"p": p})
                points.append([p[0], p[1]])

        return points
    except IndexError:
        logger.error("core.utils.get_multi_transform_towgs84.transformation_error")
        return None


def get_message(az, message):
    """
    Funkce pro získaní textu správy podle záznamu.
    """
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


class SearchTable(ColumnShiftTableBootstrap4):
    """
    Základní setup pro tabulky používané v aplikaci. 
    Obsahuje metódu na získaní sloupců které mají byt zobrazeny.
    """

    columns_to_hide = []
    app = None

    def get_column_default_show(self):
        self.column_default_show = list(self.columns.columns.keys())
        if "vychozi_skryte_sloupce" not in self.request.session:
            self.request.session["vychozi_skryte_sloupce"] = {}
        if self.app in self.request.session["vychozi_skryte_sloupce"]:
            columns_to_hide = set(
                self.request.session["vychozi_skryte_sloupce"][self.app]
            )
        else:
            columns_to_hide = self.columns_to_hide
            self.request.session["vychozi_skryte_sloupce"][self.app] = columns_to_hide
        for column in columns_to_hide:
            if column is not None and column in self.column_default_show:
                self.column_default_show.remove(column)
        return super(SearchTable, self).get_column_default_show()

    def render_nahled(self, value, record):
        """
        Metóda pro správne zobrazení náhledu souboru.
        """
        record: SamostatnyNalez
        if record.soubory.soubory.count() > 0:
            soubor = record.soubory.soubory.first()
        else:
            soubor = None
        if soubor is not None:
            soubor_url = reverse("core:download_file", args=(soubor.id,))
            return format_html(
                '<img src="{}" class="image-nahled" data-toggle="modal" data-target="#soubor-modal">',
                soubor_url,
            )
        return ""
