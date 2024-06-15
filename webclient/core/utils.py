import json
import logging
import mimetypes
import os
import django
import tempfile
import glob

import core.message_constants as mc
import requests
from arch_z.models import ArcheologickyZaznam, ArcheologickyZaznamKatastr
from django.contrib.gis.db.models.functions import PointOnSurface ,Centroid
from django.conf import ENVIRONMENT_VARIABLE, settings
from django.apps import apps
from django.core.cache import caches

from core.message_constants import (
    VALIDATION_EMPTY,
    VALIDATION_LINE_LENGTH,
    VALIDATION_NOT_MULTIPART,
    VALIDATION_NOT_SIMPLE,
    VALIDATION_NOT_VALID,
)
from heslar.hesla_dynamicka import TYP_DJ_KATASTR
from dj.models import DokumentacniJednotka
from django.db import connection
from django.urls import reverse
from django.utils.html import format_html
from django_tables2_column_shifter.tables import ColumnShiftTableBootstrap4
from heslar.models import RuianKatastr
from pian.models import Pian
from core.constants import ZAPSANI_AZ, ZAPSANI_DOK, ZAPSANI_PROJ, ZAPSANI_SN
from rosetta.conf import settings as rosetta_settings

logger = logging.getLogger(__name__)
cache = caches[rosetta_settings.ROSETTA_CACHE_NAME]


class CannotFindCadasterCentre(Exception):
    pass


def file_validate_epsg(epsg):
    if epsg == '4326' or epsg == 4326:
        return True
    else:
        return False

def balanced_parentheses(expression):    
    stack = 0   
    for char in expression:
        if char == '(' :
            stack+=1       
        elif char == ')':
            if stack == 0:
                return False
            stack-=1
    if stack != 0:
        return False              
    return True

def file_validate_geometry(lower_geom):
    """
    Funkce pro validaci řetězce s WKT geometrií.
    """
    if not isinstance(lower_geom, str):
        return [False,'Not string']
    geom=" ".join(lower_geom.upper().split())
    geom=geom.replace(" (", "(") 

    if geom=='':
        return [False,'Empty string']
    elif not geom.startswith(('POINT(', 'LINESTRING(', 'POLYGON(')):
        return [False,geom.split('(')[0]+' is not supported']
    elif not balanced_parentheses(geom):
        return [False,'Unclosed parentheses']
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
            if len(larray)>1:
                for l in larray:
                    p=l.strip().split(" ")
                    try:
                        if len(p)==2 and float(p[0]) and float(p[1]):
                            continue
                        else:
                            return [False,"Linestring is not valid"]
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
                if len(larray)>2:
                    for l in larray:
                        p=l.strip().split(" ")
                        try:
                            if len(p)==2 and float(p[0]) and float(p[1]):
                                continue
                            else:
                                return [False,"Polygon is not valid"]
                        except:
                            return [False,"Polygon is not valid"]
                    return [True,"Polygon is valid"]
                else:
                    return [False,"Polygon is not valid"]
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

def get_cadastre_from_point(point):
    """
    Funkce pro získaní katastru z bodu geomu.
    """
    query = (
        "select id, nazev from public.ruian_katastr where "
        "ST_Contains(hranice,ST_GeomFromText('POINT (%s %s)',4326) ) limit 1"
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
        "select id, nazev,ST_AsText(definicni_bod) AS db, ST_AsText(hranice) AS hranice from public.ruian_katastr where "
        "ST_Contains(hranice,ST_GeomFromText('POINT (%s %s)',4326) ) limit 1"
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
        " (SELECT A.id,A.ident_cely,ST_AsText(A.geom) as geometry, A.dj,katastr.nazev AS katastr_nazev, katastr.id as ku_id"
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
        "(select pian.id,pian.ident_cely,ST_AsText(pian.geom) as geometry,dj.ident_cely as dj, katastr.nazev AS katastr_nazev, katastr.id as ku_id"
        " from public.pian pian"
        " left join public.dokumentacni_jednotka dj on pian.id=dj.pian  and dj.ident_cely LIKE %s"
        " left join public.ruian_katastr katastr ON ST_Intersects(katastr.hranice,pian.geom)"
        " where dj.ident_cely IS NOT NULL"
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


def update_main_katastr_within_ku(ident_cely: str, katastr: RuianKatastr):
    """
    Funkce pro update katastru u akce podle katastrálního území.
    """
    akce_ident_cely = ident_cely.split("-D")[0]

    query_update_archz = (
        "update PUBLIC.archeologicky_zaznam set hlavni_katastr="
        " (select id from public.ruian_katastr where id=%s)"
        " where ident_cely = %s and typ_zaznamu IN('L')"
    )
    cursor = connection.cursor()
    cursor.execute(query_update_archz, [katastr.pk, akce_ident_cely])


def update_all_katastr_within_akce_or_lokalita(dj, fedora_transaction):
    """
    Funkce pro update katastru u akce a lokalit.
    """
    logger.debug("core.utils.update_all_katastr_within_akce_or_lokalita.start")
    if dj.typ.id == TYP_DJ_KATASTR:
        dj.katastry.set([])
    else:        
        akce_ident_cely = dj.archeologicky_zaznam.ident_cely        
        hlavni_id = None        
        ostatni_id = []
        for line in get_all_pians_with_akce(akce_ident_cely):
            if hlavni_id is None:
                hlavni_id = line["dj_katastr_id"]
            elif hlavni_id != line["dj_katastr_id"] and line["dj_katastr_id"] not in ostatni_id:
                ostatni_id.append(line["dj_katastr_id"])

        zaznam = ArcheologickyZaznam.objects.filter(ident_cely=akce_ident_cely).first()
        if zaznam:                 
            if hlavni_id is not None:
                zaznam.hlavni_katastr_id = hlavni_id            
            zaznam.katastry.set(ostatni_id)  
            zaznam.active_transaction = fedora_transaction
            zaznam.save()
    logger.debug("core.utils.update_all_katastr_within_akce_or_lokalita.end")


def get_pians_from_akce(katastr: RuianKatastr, akce_ident_cely):
    """
    Funkce pro bodu, geomu a presnosti z akce.
    """
    logger.debug("core.utils.get_pians_from_akce.start",
                 extra={"katastr": katastr, "akce_ident_cely": akce_ident_cely})
    query = (
        "select id,ST_Y(definicni_bod) AS lat, ST_X(definicni_bod) as lng,ST_AsText(ST_Envelope(hranice)) as bbox "
        " from public.ruian_katastr where "
        " id=%s"
    )
    bod_ku = RuianKatastr.objects.raw(query, [katastr.pk])[0]
    pians = []    
    try:
        if len(akce_ident_cely) > 1:
            akce=akce_ident_cely.split("-D")[0]
            DJs = (DokumentacniJednotka.objects.annotate(pian__centroid=PointOnSurface("pian__geom"))
                       .filter(ident_cely__istartswith=akce).order_by('ident_cely'))
            for dj in DJs:
                logger.debug("core.utils.get_pians_from_akce.loop_dj",
                                extra={"dj_ident_cely": dj.ident_cely, "pian": getattr(dj.pian, "ident_cely", None)})
                if dj.pian and dj.pian.geom:
                    bod = dj.pian__centroid  
                    pians.append({
                        "lat": str(bod[1]),
                        "lng": str(bod[0]),
                        "zoom": 12 if dj.typ.id==TYP_DJ_KATASTR else 17,
                        "geom": "" if dj.typ.id==TYP_DJ_KATASTR else str(dj.pian.geom).split(";")[1].replace(", ", ","),  
                        "presnost": str(dj.pian.presnost.zkratka),
                        "pian_ident_cely": str(dj.pian.ident_cely),
                        "color": 'gold' if akce_ident_cely == dj.ident_cely  else  'green',
                        "bbox" : str(bod_ku.bbox) if dj.typ.id==TYP_DJ_KATASTR else "",
                        "DJ_ident_cely" : dj.ident_cely_safe,
                    }) 

        if len(pians)==0:    
            
            bod = [bod_ku.lat, bod_ku.lng]
            pians.append({
                        "lat": str(bod_ku.lat),
                        "lng": str(bod_ku.lng),
                        "zoom": '12',
                        "geom": '',
                        "presnost": 4,
                        "pian_ident_cely": '',
                        "color": 'green' ,
                        "bbox" : str(bod_ku.bbox),
                    }) 
           
        return pians
    except IndexError as err:
        logger.error(
            "core.utils.get_pians_from_akce.error",
            extra={"katastr": katastr, "akce_ident_cely": akce_ident_cely, "err": err, "bod": bod},
        )
        raise CannotFindCadasterCentre()


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
            "core.utils.get_projects_from_envelope.no_points", extra={"ident_cely": ident_cely})
        return None


def get_num_projects_from_envelope(left, bottom, right, top, p1, p2, p3, p46, p78, request):
    """
    Funkce pro získaní počtu projektů ze čtverce.
    Bez pristupnosti
    """
    from django.contrib.gis.geos import Polygon
    from django.db.models import Q
    from projekt.models import Projekt
    from projekt.views import ProjektPermissionFilterMixin

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

    perm_object = ProjektPermissionFilterMixin()
    perm_object.request = request
    perm_object.typ_zmeny_lookup = ZAPSANI_PROJ

    try:
        return perm_object.check_filter_permission(queryset).count()
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
    from projekt.views import ProjektPermissionFilterMixin

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

    perm_object = ProjektPermissionFilterMixin()
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
                )
                .distinct()
                .values_list("pian__id", flat=True)
            ))
            # FIltering bbox is disabled-because of caching add .filter(Q(pian__geom__within=Polygon.from_bbox([right, top, left, bottom])))
        if d:
            pians.extend(d)
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

    pian_queryset = Pian.objects.filter(
        Q(geom__within=Polygon.from_bbox([right, top, left, bottom]))
        | Q(geom__intersects=Polygon.from_bbox([right, top, left, bottom]))
    )
    perm_object = PianPermissionFilterMixin()
    perm_object.request = request

    pian_filtered = perm_object.check_filter_permission(pian_queryset, p.actionChoices.mapa_pian)

    try:
        return pian_filtered.annotate(centroid=Centroid("geom"))
        #return DokumentacniJednotka.objects.filter(pian__in=pian_filtered).count()
    except IndexError:
        logger.debug(
            "core.utils.get_num_pian_from_envelope.no_points",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_pian_from_envelope(left, bottom, right, top,zoom, request):
    """
    Funkce pro získaní pianů ze čtverce.
    @janhnat zohlednit pristupnost - done
    musi zohlednit pristupnost [mapa_pian]
    """

    from django.contrib.gis.geos import Polygon      
    from core.constants import  ROLE_ARCHEOLOG_ID, ROLE_BADATEL_ID, PIAN_POTVRZEN      
    from heslar.hesla import HESLAR_PIAN_PRESNOST   
    from heslar.models import Heslar
    from heslar.hesla_dynamicka import PRISTUPNOST_BADATEL_ID, PRISTUPNOST_ARCHEOLOG_ID, PRISTUPNOST_ANONYM_ID
    from django.db import connection
    bbox=Polygon.from_bbox([right, top, left, bottom])    
    presnost=Heslar.objects.filter(nazev_heslare__id=HESLAR_PIAN_PRESNOST).first().id-1    
    
    querysum = f'''select sum(p.count) from amcr_heat_pian_l2 p where "p"."st_centroid" &&	ST_MakeEnvelope({left},{bottom},{right}, {top} ,4326)'''
   
    query=f'''select  p.ident_cely as "ident_cely",	p.presnost-{presnost} as "presnost",'pian' as "type", ST_AsText(p.geom) as "geom",ST_AsText(ST_PointOnSurface(p.geom)) as "centroid" from pian p where ST_Intersects("p"."geom",ST_GeomFromText('{bbox}', 4326)) '''
    if request.user.hlavni_role.id==ROLE_BADATEL_ID:
        query1=f''' and ( exists ( select 1 from historie h where h.vazba = p.historie and h.uzivatel = {request.user.id} and h.typ_zmeny = 'PI01' ) or exists ( select 1 from dokumentacni_jednotka dj where dj.pian = p.id and exists ( select 1 from archeologicky_zaznam az where az.id = dj.archeologicky_zaznam and exists ( select 1 from historie h2 where h2.vazba = az.historie and h2.uzivatel = {request.user.id} and h2.typ_zmeny = 'AZ01') ) ) or (exists ( select 1 from dokumentacni_jednotka dj1 where dj1.pian = p.id and exists ( select 1 from archeologicky_zaznam az where az.id = dj1.archeologicky_zaznam and az.pristupnost in ({PRISTUPNOST_ANONYM_ID}, {PRISTUPNOST_BADATEL_ID}) ) ) and p.stav ={PIAN_POTVRZEN} ))  '''
        query+=query1       
    elif request.user.hlavni_role.id==ROLE_ARCHEOLOG_ID:
        query2=f''' and ( exists (  select 1 from historie h where h.vazba = p.historie and h.organizace_snapshot_id = {request.user.organizace_id} and h.typ_zmeny = 'PI01' ) or exists (  select 1 from dokumentacni_jednotka dj where dj.pian = p.id and exists ( select 1 from archeologicky_zaznam az where az.id = dj.archeologicky_zaznam and exists ( select 1 from historie h2 where h2.vazba = az.historie and h2.organizace_snapshot_id = {request.user.organizace_id} and h2.typ_zmeny = 'AZ01' ) ) ) or exists (  select 1 from dokumentacni_jednotka dj where dj.pian = p.id and exists ( select 1 from archeologicky_zaznam az where az.id = dj.archeologicky_zaznam and exists ( select 1 from akce a1 where a1.archeologicky_zaznam = az.id and exists ( select 1 from projekt p1 where p1.id = a1.projekt and p1.organizace = {request.user.organizace_id} ) ) ) ) or (exists (  select 1 from dokumentacni_jednotka dj1 where dj1.pian = p.id and exists ( select 1 from archeologicky_zaznam az where az.id = dj1.archeologicky_zaznam and az.pristupnost in ({PRISTUPNOST_ANONYM_ID}, {PRISTUPNOST_BADATEL_ID}, {PRISTUPNOST_ARCHEOLOG_ID}) ) ) and p.stav = {PIAN_POTVRZEN}  )) '''
        query+=query2              

    pians=None
    with connection.cursor() as cursor:
            cursor.execute(querysum)
            result = cursor.fetchone() 
            count = int(result[0]) if result[0] is not None else 0            
            if count<5000 or zoom>13:
                cursor.execute(query)
                pians = dictfetchall(cursor)
                count=len(pians)
    
    return pians,count 
    

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


def find_pos_with_backup(lang, project_apps=True, django_apps=False, third_party_apps=False):
    """
    scans a couple possible repositories of gettext catalogs for the given
    language code

    """

    paths = []

    # project/locale
    if settings.SETTINGS_MODULE:
        parts = settings.SETTINGS_MODULE.split('.')
    else:
        # if settings.SETTINGS_MODULE is None, we are probably in "test" mode
        # and override_settings() was used
        # see: https://code.djangoproject.com/ticket/25911
        parts = os.environ.get(ENVIRONMENT_VARIABLE).split('.')
    project = __import__(parts[0], {}, {}, [])
    abs_project_path = os.path.normpath(os.path.abspath(os.path.dirname(project.__file__)))
    if project_apps:
        if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(project.__file__), 'locale'))):
            paths.append(os.path.abspath(os.path.join(os.path.dirname(project.__file__), 'locale')))
        if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(project.__file__), '..', 'locale'))):
            paths.append(os.path.abspath(os.path.join(os.path.dirname(project.__file__), '..', 'locale')))

    case_sensitive_file_system = True
    tmphandle, tmppath = tempfile.mkstemp()
    if os.path.exists(tmppath.upper()):
        # Case insensitive file system.
        case_sensitive_file_system = False

    # django/locale
    if django_apps:
        django_paths = cache.get('rosetta_django_paths')
        if django_paths is None:
            django_paths = []
            for root, dirnames, filename in os.walk(os.path.abspath(os.path.dirname(django.__file__))):
                if 'locale' in dirnames:
                    django_paths.append(os.path.join(root, 'locale'))
                    continue
            cache.set('rosetta_django_paths', django_paths, 60 * 60)
        paths = paths + django_paths
    # settings
    for localepath in settings.LOCALE_PATHS:
        if os.path.isdir(localepath):
            paths.append(localepath)

    # project/app/locale
    for app_ in apps.get_app_configs():
        if rosetta_settings.EXCLUDED_APPLICATIONS and app_.name in rosetta_settings.EXCLUDED_APPLICATIONS:
            continue

        app_path = app_.path
        # django apps
        if 'contrib' in app_path and 'django' in app_path and not django_apps:
            continue

        # third party external
        if not third_party_apps and abs_project_path not in app_path:
            continue

        # local apps
        if not project_apps and abs_project_path in app_path:
            continue

        if os.path.exists(os.path.abspath(os.path.join(app_path, 'locale'))):
            paths.append(os.path.abspath(os.path.join(app_path, 'locale')))
        if os.path.exists(os.path.abspath(os.path.join(app_path, '..', 'locale'))):
            paths.append(os.path.abspath(os.path.join(app_path, '..', 'locale')))

    ret = set()
    langs = [lang]
    if u'-' in lang:
        _l, _c = map(lambda x: x.lower(), lang.split(u'-', 1))
        langs += [u'%s_%s' % (_l, _c), u'%s_%s' % (_l, _c.upper()), u'%s_%s' % (_l, _c.capitalize())]
    elif u'_' in lang:
        _l, _c = map(lambda x: x.lower(), lang.split(u'_', 1))
        langs += [u'%s-%s' % (_l, _c), u'%s-%s' % (_l, _c.upper()), u'%s_%s' % (_l, _c.capitalize())]

    paths = map(os.path.normpath, paths)
    paths = list(set(paths))
    for path in paths:
        # Exclude paths
        if path not in rosetta_settings.ROSETTA_EXCLUDED_PATHS:
            for lang_ in langs:
                dirname = os.path.join(path, lang_, 'LC_MESSAGES')
                for fn in rosetta_settings.POFILENAMES:
                    filename = os.path.join(dirname, fn)
                    abs_path = os.path.abspath(filename)
                    # On case insensitive filesystems (looking at you, MacOS)
                    # compare the lowercase absolute path of the po file
                    # to all lowercased paths already collected.
                    # This is not an issue on sane filesystems
                    if not case_sensitive_file_system:
                        if filename.lower() in [p.lower() for p in ret]:
                            continue
                    if os.path.isfile(abs_path):
                        ret.add(abs_path)
                pattern = os.path.join(dirname, "django_backup_*.po")
                matching_files = glob.glob(pattern)
                if matching_files:
                    for file_path in matching_files:
                        abs_path = os.path.abspath(file_path)
                        if not case_sensitive_file_system:
                            if file_path.lower() in [p.lower() for p in ret]:
                                continue
                        if os.path.isfile(abs_path):
                            ret.add(abs_path)
    return list(sorted(ret))


def replace_last(source_string, old, new):
    index = source_string.rfind(old)
    if index != -1:
        start_part = source_string[:index]
        replace_part = source_string[index:index + len(old)].replace(old, new)
        end_part = source_string[index + len(old):]
        return start_part + replace_part + end_part
    return source_string
