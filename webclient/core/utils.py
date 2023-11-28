import json
import logging
import mimetypes
import zlib

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
from django.urls import reverse
from django.utils.html import format_html
from django_tables2_column_shifter.tables import ColumnShiftTableBootstrap4
from heslar.models import RuianKatastr
from pian.models import Pian
from core.constants import ZAPSANI_AZ, ZAPSANI_DOK, ZAPSANI_PROJ, ZAPSANI_SN

logger = logging.getLogger(__name__)

def file_validate_epsg(epsg):
    if epsg=='4326' or epsg==4326:
        return True
    else:
        return False

def file_validate_geometry(lower_geom):
    geom=lower_geom.upper().strip()
    geom=geom.replace("POINT (", "POINT(") 
    geom=geom.replace("LINESTRING (", "LINESTRING(") 
    geom=geom.replace("POLYGON (", "POLYGON(") 

    if "MULTI" in geom:
        return [False,'Multigeometries are not supported']
    else:
        if "POINT(" in geom:
            try:
                p=geom.split("POINT(")[1].split(")")[0].split(" ")
                if (len(p)==2 or len(p)==3) and float(p[0]) and float(p[1]):
                    return [True, "Point geometry is valid"]
                else:
                    return [False,"Point is not valid"]
            except:
                return [False,"Point is not valid"]
        elif "LINESTRING(" in geom:
            larray=geom.split("LINESTRING(")[1].split(")")[0].split(",")
            if len(larray[0])>0:
                for l in larray:
                    p=l.strip().split(" ")
                    try:
                        if len(p)==2 and float(p[0]) and float(p[1]):
                            continue
                    except:
                        return [False,"Linestring is not valid"]
                return [True,"Linestring is valid"]
            else:
                return [False,"Linestring is not valid"]
        elif "POLYGON(" in geom:
            if " (" in geom or ",(" in geom:
                return [False,"Polygon with innerbound is not supported"]
            else:
                larray=geom.split("POLYGON((")[1].split("))")[0].split(",")
                for l in larray:
                    p=l.strip().split(" ")
                    try:
                        if len(p)==2 and float(p[0]) and float(p[1]):
                            continue
                    except:
                        return [False,"Polygon is not valid"]
                return [True,"Polygon is valid"]
        else:
            return [False,"Polygon is not valid"]
            
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
        logger.debug(
            "core.utils.get_cadastre_from_point.start",
            extra={"point_0": point[0], "point_1": point[1], "katastr": katastr},
        )
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
        logger.debug(
            "core.utils.get_cadastre_from_point.start",
            extra={"point_0": point[0], "point_1": point[1]},
        )
        cursor = connection.cursor()
        cursor.execute(query, [point[0], point[1]])
        line = cursor.fetchone()
        return [line[1], line[2], line[3]]
    except IndexError:
        logger.error(
            "core.utils.get_cadastre_from_point_with_geometry.error",
            extra={"point": point},
        )
        return None

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
    from django.contrib.gis.db.models.functions import Centroid
    query = (
        "select id,ST_Y(definicni_bod) AS lat, ST_X(definicni_bod) as lng "
        " from public.ruian_katastr where "
        " upper(nazev_stary)=upper(%s) and aktualni='t' limit 1"
    )
    try:
        bod_ku = RuianKatastr.objects.raw(query, [katastr])[0]
        bod=[bod_ku.lat,bod_ku.lng]
        geom = ""
        presnost = 4
        zoom = 14
        if len(pian) > 1:
            dj = DokumentacniJednotka.objects.annotate(pian__centroid=Centroid("pian__geom")).get(ident_cely=pian)
            if dj.pian and dj.pian.geom:
                bod = dj.pian__centroid
                bod =[bod[1],bod[0]]
                zoom = 17
                geom = dj.pian.geom
                presnost = dj.pian.presnost.zkratka
        return [bod, geom, presnost,zoom]
    except IndexError:
        logger.error(
            "core.utils.get_centre_from_akce.error",
            extra={"katastr": katastr, "pian": pian},
        )
        return None


def get_dj_pians_centroid(ident_cely, lat, lng):
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
        logger.debug("core.utils.get_dj_pians_centroid.no_pians")
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
        logger.debug(
            "core.utils.get_num_pians_from_envelope.no_points",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_dj_pians_from_envelope(left, bottom, right, top, ident_cely):
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
        logger.debug(
            "core.utils.get_dj_pians_from_envelope.no_points",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_projekt_stav_label(stav):
    from core.constants import (
        PROJEKT_STAV_ARCHIVOVANY,
        PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
        PROJEKT_STAV_OZNAMENY,
        PROJEKT_STAV_PRIHLASENY,
        PROJEKT_STAV_UKONCENY_V_TERENU,
        PROJEKT_STAV_UZAVRENY,
        PROJEKT_STAV_ZAHAJENY_V_TERENU,
        PROJEKT_STAV_ZAPSANY,
        PROJEKT_STAV_ZRUSENY,
    )

    if stav == PROJEKT_STAV_ZAPSANY:
        return "P1"
    elif stav == PROJEKT_STAV_PRIHLASENY:
        return "P2"
    elif stav == PROJEKT_STAV_ZAHAJENY_V_TERENU:
        return "P3"
    elif PROJEKT_STAV_UKONCENY_V_TERENU <= stav <= PROJEKT_STAV_ARCHIVOVANY:
        return "P4-P6"
    elif PROJEKT_STAV_NAVRZEN_KE_ZRUSENI <= stav <= PROJEKT_STAV_ZRUSENY:
        return "P7-P8"
    else:
        return "P0"


def get_project_geom(ident_cely):
    """
    Funkce pro získaní geometrie projekt.
    Bez pristupnosti
    """
    from django.db.models import Q
    from projekt.models import Projekt

    c1 = Q(geom__isnull=False)
    c3 = Q(ident_cely=ident_cely)
    queryset = Projekt.objects.filter(c1).filter(c3)
    try:
        return queryset.only("id", "ident_cely", "geom", "stav")
    except IndexError:
        logger.debug(
            "core.utils.get_projects_from_envelope.no_points",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_num_projects_from_envelope(left, bottom, right, top, p1, p2, p3, p46, p78, request):
    """
    Funkce pro získaní počtu projektů ze čtverce.
    Bez pristupnosti
    """
    from django.contrib.gis.geos import Polygon
    from django.db.models import Q
    from projekt.models import Projekt
    from core.views import PermissionFilterMixin

    c1 = Q(geom__isnull=False)
    c2 = Q(geom__within=Polygon.from_bbox([right, top, left, bottom]))
    stavy=[]
    if p1: stavy.append(1)
    if p2: stavy.append(2)
    if p3: stavy.append(3)
    if p46: 
        stavy.append(4)
        stavy.append(5)
        stavy.append(6)
    if p78: 
        stavy.append(7)
        stavy.append(8)
    queryset = Projekt.objects.filter(c1).filter(c2).filter(Q(stav__in=stavy)).count()

    perm_object = PermissionFilterMixin()
    perm_object.request = request
    perm_object.typ_zmeny_lookup = ZAPSANI_PROJ

    try:
        return perm_object.check_filter_permission(queryset)
    except IndexError:
        logger.debug(
            "core.utils.get_num_projects_from_envelope.no_points",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_projects_from_envelope(left, bottom, right, top, p1, p2, p3, p46, p78, request):
    """
    Funkce pro získaní projektů ze čtverce.
    Bez pristupnosti
    """
    from django.contrib.gis.geos import Polygon
    from django.db.models import Q
    from projekt.models import Projekt
    from core.views import PermissionFilterMixin

    c1 = Q(geom__isnull=False)
    c2 = Q(geom__within=Polygon.from_bbox([right, top, left, bottom]))
    stavy=[]
    if p1: stavy.append(1)
    if p2: stavy.append(2)
    if p3: stavy.append(3)
    if p46: 
        stavy.append(4)
        stavy.append(5)
        stavy.append(6)
    if p78: 
        stavy.append(7)
        stavy.append(8)
    queryset = Projekt.objects.filter(c1).filter(c2).filter(Q(stav__in=stavy))

    perm_object = PermissionFilterMixin()
    perm_object.request = request
    perm_object.typ_zmeny_lookup = ZAPSANI_PROJ

    try:
        return perm_object.check_filter_permission(queryset).only("id", "ident_cely", "geom", "stav")
    except IndexError:
        logger.debug(
            "core.utils.get_projects_from_envelope.no_points",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_project_pas_from_envelope(left, bottom, right, top, ident_cely):
    """
    Funkce pro získaní pas projekt ze čtverce.
    @janhnat zohlednit pristupnost - zohledneno v ProjectPasFromEnvelopeView
    """
    from django.contrib.gis.geos import Polygon
    from django.db.models import Q
    from pas.models import SamostatnyNalez

    c1 = Q(geom__isnull=False)
    c2 = Q(geom__within=Polygon.from_bbox([right, top, left, bottom]))
    c3 = Q(projekt__ident_cely=ident_cely)
    queryset = SamostatnyNalez.objects.filter(c3).filter(c1)
    # FIltering bbox is disabled-because of caching add .filter(c2)
    try:
        return queryset.only("id", "ident_cely", "geom")
    except IndexError:
        logger.debug(
            "core.utils.get_project_pas_from_envelope.no_points",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_project_pian_from_envelope(left, bottom, right, top, ident_cely):
    """
    Funkce pro získaní pianů projektu ze čtverce.
    @janhnat zohlednit pristupnost - zohledneno v ProjectPianFromEnvelopeView
    """
    from arch_z.models import Akce
    from dj.models import DokumentacniJednotka
    from django.contrib.gis.geos import Polygon
    from django.db.models import Q

    q1 = Akce.objects.filter(projekt__ident_cely=ident_cely).only(
        "archeologicky_zaznam__ident_cely"
    )

    pians = []
    d = None
    for i in q1:
        d = list(
                (
                DokumentacniJednotka.objects.filter(
                    Q(ident_cely__istartswith=i.archeologicky_zaznam.ident_cely)
                    | Q(pian__geom__crosses=Polygon.from_bbox([right, top, left, bottom]))
                )
                .distinct()
                .values_list("pian", flat=True)
            ))
            # FIltering bbox is disabled-because of caching add .filter(Q(pian__geom__within=Polygon.from_bbox([right, top, left, bottom])))
        if pians:
            pians.append(d)
        else:
            pians = d
    try:  
        return Pian.objects.filter(pk__in=pians)
    except IndexError:
        logger.debug(
            "core.utils.get_project_pian_from_envelope.no_points",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_3d_from_envelope(left, bottom, right, top,request):
    """
    Funkce pro získaní 3d ze čtverce.
    Bez pristupnosti
    """
    from django.contrib.gis.geos import Polygon
    from django.db.models import Q
    from dokument.models import DokumentExtraData
    from core.views import PermissionFilterMixin

    c1 = Q(geom__isnull=False)
    c2 = Q(geom__within=Polygon.from_bbox([right, top, left, bottom]))
    queryset = DokumentExtraData.objects.filter(c1).filter(c2)
    perm_object = PermissionFilterMixin()
    perm_object.request = request
    perm_object.typ_zmeny_lookup = ZAPSANI_DOK

    try:
        return perm_object.check_filter_permission(queryset).values("dokument__id", "dokument__ident_cely", "geom")
    except IndexError:
        logger.debug(
            "core.utils.get_3d_from_envelope.no_points",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_num_pass_from_envelope(left, bottom, right, top, request):
    """
    Funkce pro získaní počtu pas ze čtverce.
    @janhnat zohlednit pristupnost - done
    musi zohlednit pristupnost [mapa_pas]
    """
    from django.contrib.gis.geos import Polygon
    from django.db.models import Q
    from pas.models import SamostatnyNalez
    from core.views import PermissionFilterMixin
    from core.models import Permissions as p

    c1 = Q(geom__isnull=False)
    c2 = Q(geom__within=Polygon.from_bbox([right, top, left, bottom]))
    queryset = SamostatnyNalez.objects.filter(c1).filter(c2)
    perm_object = PermissionFilterMixin()
    perm_object.request = request
    perm_object.typ_zmeny_lookup = ZAPSANI_SN

    try:
        return perm_object.check_filter_permission(queryset, p.actionChoices.mapa_pas).count()
    except IndexError:
        logger.debug(
            "core.utils.get_num_pas_from_envelope.no_points",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_pas_from_envelope(left, bottom, right, top, request):
    """
    Funkce pro získaní pas ze čtverce.
    @janhnat zohlednit pristupnost - done
    musi zohlednit pristupnost [mapa_pas]
    """
    from django.contrib.gis.geos import Polygon
    from django.db.models import Q
    from pas.models import SamostatnyNalez
    from core.views import PermissionFilterMixin
    from core.models import Permissions as p

    c1 = Q(geom__isnull=False)
    c2 = Q(geom__within=Polygon.from_bbox([right, top, left, bottom]))
    queryset = SamostatnyNalez.objects.filter(c2).filter(c1)
    perm_object = PermissionFilterMixin()
    perm_object.request = request
    perm_object.typ_zmeny_lookup = ZAPSANI_SN

    try:
        return perm_object.check_filter_permission(queryset, p.actionChoices.mapa_pas).only("id", "ident_cely", "geom")
    except IndexError:
        logger.debug(
            "core.utils.get__pas_from_envelope.no_points",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_num_pian_from_envelope(left, bottom, right, top, request):
    """
    Funkce pro získaní počtu pianu ze čtverce.
    @janhnat zohlednit pristupnost - done
    musi zohlednit pristupnost [mapa_pian]
    """
    from dj.models import DokumentacniJednotka
    from django.contrib.gis.geos import Polygon
    from django.db.models import Q
    from pian.views import PianPermissionFilterMixin
    from core.models import Permissions as p

    queryset = DokumentacniJednotka.objects.filter(
        Q(pian__geom__within=Polygon.from_bbox([right, top, left, bottom]))
        | Q(pian__geom__intersects=Polygon.from_bbox([right, top, left, bottom]))
    )
    perm_object = PianPermissionFilterMixin()
    perm_object.request = request

    try:
        return perm_object.check_filter_permission(queryset, p.actionChoices.mapa_pian).count()
    except IndexError:
        logger.debug(
            "core.utils.get_num_pian_from_envelope.no_points",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_pian_from_envelope(left, bottom, right, top, request):
    """
    Funkce pro získaní pianů ze čtverce.
    @janhnat zohlednit pristupnost - done
    musi zohlednit pristupnost [mapa_pian]
    """
    from dj.models import DokumentacniJednotka
    from django.contrib.gis.db.models.functions import Centroid
    from django.contrib.gis.geos import Polygon
    from django.db.models import Q
    from pian.views import PianPermissionFilterMixin
    from core.models import Permissions as p

    queryset = (
        DokumentacniJednotka.objects.filter(
            Q(pian__geom__within=Polygon.from_bbox([right, top, left, bottom]))
            | Q(pian__geom__intersects=Polygon.from_bbox([right, top, left, bottom]))
        )
        .annotate(pian__centroid=Centroid("pian__geom"))
        .distinct()
    )
    perm_object = PianPermissionFilterMixin()
    perm_object.request = request

    try:
        return perm_object.check_filter_permission(queryset, p.actionChoices.mapa_pian)[:10000].values(
            "pian__id",
            "pian__ident_cely",
            "pian__geom",
            "pian__presnost__zkratka",
            "ident_cely",
            "pian__centroid",
        )
    except IndexError:
        logger.debug(
            "core.utils.get_pian_from_envelope.no_points",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None

def get_dj_akce_for_pian(pian_ident_cely,request):
    """
    Funkce pro pro ziskani dj/akce pro pian_ident_cely
    """
    from django.db.models import Q
    from core.views import PermissionFilterMixin
    queryset = DokumentacniJednotka.objects.filter(Q(pian__geom__isnull=False)).filter(Q(pian__ident_cely=pian_ident_cely))
    perm_object = PermissionFilterMixin()
    perm_object.request = request
    perm_object.typ_zmeny_lookup = ZAPSANI_AZ
    arch_zaznamy = ArcheologickyZaznam.objects.filter(dokumentacni_jednotky_akce__in=queryset)

    try:
        return queryset.filter(archeologicky_zaznam__in=perm_object.check_filter_permission(arch_zaznamy)).values("ident_cely", "archeologicky_zaznam__ident_cely")
    except IndexError:
        logger.debug(
            "core.utils.get_dj_akce_for_pian.no_records",
            extra={"pian_ident_cely": pian_ident_cely},
        )
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
        logger.debug(
            "core.utils.get_heatmap_pian.no_heatmap",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
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
        logger.debug(
            "core.utils.get_heatmap_pian_density.no_heatmap",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_heatmap_pas(left, bottom, right, top, zoom):
    """
    Funkce pro získaní heat mapy pass ze čtverce.
    """
    query = "select count, ST_AsText(st_centroid) as geometry from amcr_heat_pas_l2"
    query_zoom = (
        "select count*3 as count, ST_AsText(st_centroid) as geometry "
        "from amcr_heat_pas_lx2 where st_centroid && ST_MakeEnvelope(%s, %s, %s, %s,4326)"
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
        logger.debug(
            "core.utils.get_heatmap_pas.no_heatmap",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_heatmap_pas_density(left, bottom, right, top, zoom):
    """
    Funkce pro získaní heat mapy hustoty pass ze čtverce.
    """
    query = "select max(count) from amcr_heat_pas_l2"
    query_zoom = "select max(count) from amcr_heat_pas_lx2 where st_centroid && ST_MakeEnvelope(%s, %s, %s, %s,4326)"
    try:
        # num = Pian.objects.raw(query, [left, bottom, right, top])
        cursor = connection.cursor()
        if zoom > 12:
            cursor.execute(query_zoom, [left, bottom, right, top])
        else:
            cursor.execute(query)
        return cursor.fetchone()[0]
    except IndexError:
        logger.debug(
            "core.utils.get_heatmap_pas_density.no_heatmap",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
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
        logger.debug(
            "core.utils.get_heatmap_project.no_heatmap",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
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
        logger.debug(
            "core.utils.get_heatmap_project_density.no_heatmap",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
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


def get_transform_towgs84(x1, x2):
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
        "coordinates=" + str(x1) + "+" + str(x2) + "+300"
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
                logger.debug(
                    "core.utils.get_multi_transform_towgs84.finished", extra={"p": p}
                )
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
        from pas.models import SamostatnyNalez

        record: SamostatnyNalez
        if record.soubory.soubory.count() > 0:
            soubor = record.soubory.soubory.first()
        else:
            soubor = None
        if soubor is not None:
            soubor_url = reverse(
                "core:download_thumbnail",
                args=(
                    "pas",
                    record.ident_cely,
                    soubor.id,
                ),
            )
            return format_html(
                '<img src="{}" class="image-nahled" data-toggle="modal" data-target="#soubor-modal">',
                soubor_url,
            )
        return ""
