import glob
import logging
import mimetypes
import os
import tempfile
import uuid
from datetime import datetime

import core.message_constants as mc
import django
import pytz
from arch_z.models import ArcheologickyZaznam
from core.constants import EPSG_WGS84, LIMIT_PRVKU_ZOBRAZENI_HEATMAP, ZAPSANI_AZ, ZAPSANI_DOK, ZAPSANI_PROJ, ZAPSANI_SN
from core.coordTransform import transform_geom_to_sjtsk, transform_geom_to_wgs84
from dj.models import DokumentacniJednotka
from django.apps import apps
from django.conf import ENVIRONMENT_VARIABLE, settings
from django.contrib.gis.db.models.functions import AsGeoJSON, PointOnSurface
from django.core.cache import caches
from django.db import connection, connections
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _
from django_tables2_column_shifter.tables import ColumnShiftTableBootstrap4
from heslar.hesla_dynamicka import TYP_DJ_KATASTR
from heslar.models import RuianKatastr
from pian.models import Pian
from rosetta.conf import settings as rosetta_settings

logger = logging.getLogger(__name__)
cache = caches[rosetta_settings.ROSETTA_CACHE_NAME]


class CannotFindCadasterCentre(Exception):
    """Třída `CannotFindCadasterCentre` v modulu `webclient.core.utils`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    pass


def file_validate_epsg(epsg):
    """Funkce `file_validate_epsg` v modulu `webclient.core.utils`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param epsg: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    if epsg == "4326":
        return True
    elif epsg == "5514":
        return True
    else:
        return False


def balanced_parentheses(expression):
    """Funkce `balanced_parentheses` v modulu `webclient.core.utils`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param expression: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    stack = 0
    for char in expression:
        if char == "(":
            stack += 1
        elif char == ")":
            if stack == 0:
                return False
            stack -= 1
    if stack != 0:
        return False
    return True


def load_database_translation_strings():
    """Funkce `load_database_translation_strings` v modulu `webclient.core.utils`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    :return: Výsledek odpovídající účelu volání.
    """
    return [
        _("pian.posgtres.importovatPian.check.unsupportedEPSG"),
        _("pian.posgtres.importovatPian.check.wrongGeometry"),
        _("pian.posgtres.importovatPian.check.dimension"),
        _("pian.posgtres.importovatPian.check.BBox"),
        _("pian.posgtres.importovatPian.check.geometryNotSimple"),
        _("pian.posgtres.importovatPian.check.geometryIsEmpty"),
        _("pian.posgtres.importovatPian.check.geometryIsMultipart"),
        _("pian.posgtres.importovatPian.check.tooFewPoints"),
        _("pian.posgtres.importovatPian.check.segmentsTooShort"),
    ]


def validate_and_split_geometry(geom):
    """
    Funkce pro validaci řetězce s WKT geometrií.
    """

    new_rows = []
    if not isinstance(geom.iloc[2], str) or geom.iloc[2] == "":
        geom["result"] = _("pian.views.importovatPianView.check.wrongGeometry")
        new_rows.append(geom)
        return new_rows
    query = """
WITH geom_to_insert AS (
    SELECT ST_GeomFromText(%s, %s) AS geom
),
dumped AS (
    SELECT (ST_Dump(geom)).geom AS geom
    FROM geom_to_insert
),
validated AS (
    SELECT
        g.geom,
        ST_GeometryType(g.geom) AS geom_type,
        ST_AsText(g.geom) AS wkt,
        CASE
            WHEN ST_NumGeometries(g.geom) > 1 THEN 'pian.posgtres.importovatPian.check.geometryIsMultipart'
            ELSE validategeom(ST_AsText(g.geom), %s)
        END AS validation_result
    FROM dumped g
),
rings AS (
    SELECT
        v.validation_result,
        ST_AsText((ST_DumpRings(v.geom)).geom) AS ring,
        v.geom_type
    FROM validated v
    WHERE v.geom_type = 'ST_Polygon'
),
others AS (
    SELECT
        v.validation_result,
        ST_AsText(v.geom) AS ring,
        v.geom_type
    FROM validated v
    WHERE v.geom_type != 'ST_Polygon'
)
SELECT * FROM rings
UNION ALL
SELECT * FROM others;
"""
    cursor = connections["urgent"].cursor()
    try:
        cursor.execute(query, [geom.iloc[2], geom.iloc[1], geom.iloc[1]])
    except Exception as e:
        logger.debug("core.utils.file_validate_geometry.exception", extra={"error": e})
        geom["result"] = _("pian.views.importovatPianView.check.wrongGeometry")
        new_rows.append(geom)
        return new_rows
    rows = cursor.fetchall()
    for index, row in enumerate(rows):
        new_geom = geom.copy()
        new_geom.iloc[2] = row[1]
        if len(rows) > 1:
            new_geom.iloc[0] = f"{geom.iloc[0]}_{index + 1}"
        if row[0] != "valid":
            new_geom["result"] = _(row[0])
            new_rows.append(new_geom)
            return new_rows
        try:
            if geom.iloc[1] == "4326":
                geom_jtsk = transform_geom_to_sjtsk(row[1])
                cursor.execute(query, [geom_jtsk[0], "5514", "5514"])
            else:
                geom_wgs = transform_geom_to_wgs84(row[1])
                cursor.execute(query, [geom_wgs[0], "4326", "4326"])
            row_trans = cursor.fetchone()
            if row_trans[0] != "valid":
                new_geom["result"] = _(row_trans[0])
                new_rows.append(new_geom)
                return new_rows
        except Exception as e:
            logger.debug("core.utils.file_validate_geometry.transformException", extra={"error": e})
            new_geom["result"] = _("pian.views.importovatPianView.check.wrongGeometry")
            new_rows.append(new_geom)
            return new_rows
        new_geom["result"] = True
        new_rows.append(new_geom)
    return new_rows


def get_mime_type(file_name):
    """
    Funkce pro získaní mime typu pro soubor.
    """
    mime_type = mimetypes.guess_type(file_name)[0]
    # Podle RFC 4180 je MIME typ CSV `text/csv`.
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
            extra={"X": point[0], "Y": point[1], "katastr": katastr},
        )
        return katastr
    except IndexError:
        logger.warning("core.utils.get_cadastre_from_point.error", extra={"X": point[0], "Y": point[1]})
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
            extra={"X": point[0], "Y": point[1]},
        )
        cursor = connection.cursor()
        cursor.execute(query, [point[0], point[1]])
        line = cursor.fetchone()
        return [line[1], line[2], line[3]]
    except IndexError:
        logger.error(
            "core.utils.get_cadastre_from_point_with_geometry.error",
            extra={"geom": point},
        )
        return None


def get_all_pians_with_akce(ident_cely):
    """
    Funkce pro získaní všech pianů s akci.
    """
    query = """
        (SELECT A.id,
              A.ident_cely,
              ST_AsText(A.geom) AS geometry,
              A.dj,
              katastr.nazev AS katastr_nazev,
              katastr.id AS ku_id
        FROM public.ruian_katastr katastr
        JOIN
         (SELECT pian.id,
                 pian.ident_cely,
                 CASE
                     WHEN ST_GeometryType(pian.geom) = 'ST_LineString' THEN st_centroid(pian.geom)
                     WHEN ST_GeometryType(pian.geom) = 'ST_LineString' THEN st_lineinterpolatepoint(pian.geom, 0.5)
                     ELSE st_centroid(pian.geom)
                 END AS geom,
                 dj.ident_cely AS dj
          FROM public.pian pian
          JOIN public.dokumentacni_jednotka dj ON pian.id=dj.pian
          AND dj.ident_cely LIKE %s
          WHERE dj.ident_cely IS NOT NULL) AS A ON ST_Intersects(katastr.hranice, geom)
        ORDER BY A.dj,
                katastr.nazev
        LIMIT 1)
        UNION ALL
        (SELECT pian.id,
              pian.ident_cely,
              ST_AsText(pian.geom) AS geometry,
              dj.ident_cely AS dj,
              katastr.nazev AS katastr_nazev,
              katastr.id AS ku_id
        FROM public.pian pian
        LEFT JOIN public.dokumentacni_jednotka dj ON pian.id=dj.pian
        AND dj.ident_cely LIKE %s
        LEFT JOIN public.ruian_katastr katastr ON ST_Intersects(katastr.hranice, pian.geom)
        WHERE dj.ident_cely IS NOT NULL
        ORDER BY dj.ident_cely,
                katastr_nazev
        LIMIT 990)
        """
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
        logger.debug("core.utils.get_all_pians_with_akce.exception", extra={"error": e})
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
        pass
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
    logger.debug("core.utils.get_pians_from_akce.start", extra={"katastr": katastr, "ident_cely": akce_ident_cely})
    query = (
        "select id,ST_Y(definicni_bod) AS lat, ST_X(definicni_bod) as lng,ST_AsText(ST_Envelope(hranice)) as bbox "
        " from public.ruian_katastr where "
        " id=%s"
    )
    bod_ku = RuianKatastr.objects.raw(query, [katastr.pk])[0]
    pians = []
    try:
        if len(akce_ident_cely) > 1:
            akce = akce_ident_cely.split("-D")[0]
            DJs = (
                DokumentacniJednotka.objects.annotate(pian__centroid=PointOnSurface("pian__geom"))
                .filter(ident_cely__istartswith=akce)
                .order_by("ident_cely")
            )
            for dj in DJs:
                logger.debug(
                    "core.utils.get_pians_from_akce.loop_dj",
                    extra={"ident_cely": dj.ident_cely, "pian": getattr(dj.pian, "ident_cely", None)},
                )
                if dj.pian and dj.pian.geom:
                    bod = dj.pian__centroid
                    pians.append(
                        {
                            "lat": str(bod[1]),
                            "lng": str(bod[0]),
                            "zoom": 12 if dj.typ.id == TYP_DJ_KATASTR else 17,
                            "geom": (
                                ""
                                if dj.typ.id == TYP_DJ_KATASTR
                                else str(dj.pian.geom).split(";")[1].replace(", ", ",")
                            ),
                            "presnost": str(dj.pian.presnost.zkratka),
                            "pian_ident_cely": str(dj.pian.ident_cely),
                            "color": "gold" if akce_ident_cely == dj.ident_cely else "green",
                            "bbox": str(bod_ku.bbox) if dj.typ.id == TYP_DJ_KATASTR else "",
                            "DJ_ident_cely": dj.ident_cely_safe,
                        }
                    )

        if len(pians) == 0:

            bod = [bod_ku.lat, bod_ku.lng]
            pians.append(
                {
                    "lat": str(bod_ku.lat),
                    "lng": str(bod_ku.lng),
                    "zoom": "12",
                    "geom": "",
                    "presnost": 4,
                    "pian_ident_cely": "",
                    "color": "green",
                    "bbox": str(bod_ku.bbox),
                }
            )

        return pians
    except IndexError as err:
        logger.error(
            "core.utils.get_pians_from_akce.error",
            extra={"katastr": katastr, "ident_cely": akce_ident_cely, "error": err, "value": bod},
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
        pians = Pian.objects.raw(query, [ident_cely[0 : ident_cely.rindex("-")] + "%", lat, lng])
        return pians
    except Exception:
        logger.debug("core.utils.get_dj_pians_centroid.no_pians")
        return None


def get_num_pians_from_envelope(left, bottom, right, top):
    """
    Funkce pro získaní počtu pianů ze čtverce.
    """
    query = "select count(*) from public.pian pian where " "pian.geom && ST_MakeEnvelope(%s, %s, %s, %s,4326) limit 1"
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
        logger.debug("core.utils.get_projects_from_envelope.no_points", extra={"ident_cely": ident_cely})
        return None


def get_num_projects_from_envelope(left, bottom, right, top, stavy, request):
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


def get_projects_from_envelope(left, bottom, right, top, stavy, request):
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
    queryset = Projekt.objects.filter(c1).filter(c2).filter(Q(stav__in=stavy))

    perm_object = ProjektPermissionFilterMixin()
    perm_object.request = request
    perm_object.typ_zmeny_lookup = ZAPSANI_PROJ

    try:
        return (
            perm_object.check_filter_permission(queryset)
            .annotate(geom_geojson=AsGeoJSON("geom"))
            .values("id", "ident_cely", "geom_geojson", "stav")
        )
    except IndexError:
        logger.debug(
            "core.utils.get_projects_from_envelope.no_points",
            extra={"left": left, "bottom": bottom, "right": right, "top": top},
        )
        return None


def get_project_pas_from_envelope(left, bottom, right, top, ident_cely):
    """
    Funkce pro získaní pas projekt ze čtverce.
    """
    from django.db.models import Q
    from pas.models import SamostatnyNalez

    c1 = Q(geom__isnull=False)
    c3 = Q(projekt__ident_cely=ident_cely)
    queryset = SamostatnyNalez.objects.filter(c3).filter(c1)
    # Filtrování bbox je kvůli cache vypnuté; pro zapnutí přidejte .filter(c2).
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
    @janhnat zohlednit pristupnost - zohledneno v ProjectPasFromEnvelopeView
    Funkce pro získaní pianů projektu ze čtverce.
    """
    from arch_z.models import Akce
    from dj.models import DokumentacniJednotka
    from django.db.models import Q

    q1 = Akce.objects.filter(projekt__ident_cely=ident_cely).only("archeologicky_zaznam__ident_cely")

    pians = []
    d = None
    for i in q1:
        d = list(
            (
                DokumentacniJednotka.objects.filter(Q(ident_cely__istartswith=i.archeologicky_zaznam.ident_cely))
                .distinct()
                .values_list("pian__id", flat=True)
            )
        )
        # Filtrování bbox je kvůli cache vypnuté; pro zapnutí přidejte .filter(Q(pian__geom__within=Polygon.from_bbox([right, top, left, bottom]))).
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


def get_3d_from_envelope(left, bottom, right, top, request):
    """
    @janhnat zohlednit pristupnost - zohledneno v ProjectPianFromEnvelopeView
    Funkce pro získaní 3d ze čtverce.
    Bez pristupnosti
    """
    from core.views import PermissionFilterMixin
    from django.contrib.gis.geos import Polygon
    from django.db.models import Q
    from dokument.models import DokumentExtraData

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
    from core.models import Permissions as p
    from core.views import PermissionFilterMixin
    from django.contrib.gis.geos import Polygon
    from django.db.models import Q
    from pas.models import SamostatnyNalez

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


def get_pas_from_envelope(bounds, request):
    """
    Funkce pro získaní pas ze čtverce.
    @janhnat zohlednit pristupnost - done
    musi zohlednit pristupnost [mapa_pas]
    """
    from core.models import Permissions as p
    from core.views import PermissionFilterMixin
    from django.contrib.gis.geos import Polygon
    from django.db.models import Q
    from pas.models import SamostatnyNalez

    c1 = Q(geom__isnull=False)
    c2 = Q(
        geom__within=Polygon(
            (
                (bounds["bottomLeft"]["lng"], bounds["bottomLeft"]["lat"]),
                (bounds["bottomRight"]["lng"], bounds["bottomRight"]["lat"]),
                (bounds["topRight"]["lng"], bounds["topRight"]["lat"]),
                (bounds["topLeft"]["lng"], bounds["topLeft"]["lat"]),
                (bounds["bottomLeft"]["lng"], bounds["bottomLeft"]["lat"]),
            )
        )
    )

    queryset = SamostatnyNalez.objects.filter(c2).filter(c1)
    perm_object = PermissionFilterMixin()
    perm_object.request = request
    perm_object.typ_zmeny_lookup = ZAPSANI_SN

    try:
        return perm_object.check_filter_permission(queryset, p.actionChoices.mapa_pas).only("id", "ident_cely", "geom")
    except IndexError:
        logger.debug("core.utils.get__pas_from_envelope.no_points")
        return None


def get_pian_from_envelope(bounds, zoom, request):
    """
    Funkce pro získaní pianů ze čtverce.
    @janhnat zohlednit pristupnost - done
    musi zohlednit pristupnost [mapa_pian]
    """

    from core.constants import PIAN_POTVRZEN, ROLE_ARCHEOLOG_ID, ROLE_BADATEL_ID
    from django.db import connection
    from heslar.hesla import HESLAR_PIAN_PRESNOST
    from heslar.hesla_dynamicka import PRISTUPNOST_ANONYM_ID, PRISTUPNOST_ARCHEOLOG_ID, PRISTUPNOST_BADATEL_ID
    from heslar.models import Heslar

    bbox = """POLYGON((%s %s, %s %s, %s %s, %s %s, %s %s))"""
    bbox_query_params = [
        bounds["bottomLeft"]["lng"],
        bounds["bottomLeft"]["lat"],
        bounds["bottomRight"]["lng"],
        bounds["bottomRight"]["lat"],
        bounds["topRight"]["lng"],
        bounds["topRight"]["lat"],
        bounds["topLeft"]["lng"],
        bounds["topLeft"]["lat"],
        bounds["bottomLeft"]["lng"],
        bounds["bottomLeft"]["lat"],
    ]
    presnost = Heslar.objects.filter(nazev_heslare__id=HESLAR_PIAN_PRESNOST).first().id - 1

    querysum = f"""select sum(p.count) from amcr_heat_pian_l2 p where "p"."st_centroid" && ST_GeomFromText('{bbox}', {EPSG_WGS84})"""

    query = f"""select  p.ident_cely as "ident_cely", p.presnost-{presnost} as "presnost",'pian' as "type", ST_AsText(p.geom) as "geom",ST_AsText(ST_PointOnSurface(p.geom)) as "centroid" from pian p where ST_Intersects("p"."geom",ST_GeomFromText('{bbox}', {EPSG_WGS84}))"""
    if request.user.hlavni_role.id == ROLE_BADATEL_ID:
        query1 = f""" and (exists (select 1 from historie h where h.vazba = p.historie and h.uzivatel = {request.user.id} and h.typ_zmeny = 'PI01') or exists (select 1 from dokumentacni_jednotka dj where dj.pian = p.id and exists (select 1 from archeologicky_zaznam az where az.id = dj.archeologicky_zaznam and exists (select 1 from historie h2 where h2.vazba = az.historie and h2.uzivatel = {request.user.id} and h2.typ_zmeny = 'AZ01'))) or (exists (select 1 from dokumentacni_jednotka dj1 where dj1.pian = p.id and exists (select 1 from archeologicky_zaznam az where az.id = dj1.archeologicky_zaznam and az.pristupnost in ({PRISTUPNOST_ANONYM_ID}, {PRISTUPNOST_BADATEL_ID}))) and p.stav ={PIAN_POTVRZEN})) """
        query += query1
    elif request.user.hlavni_role.id == ROLE_ARCHEOLOG_ID:
        query2 = f""" and (exists (select 1 from historie h where h.vazba = p.historie and h.organizace_snapshot_id = {request.user.organizace_id} and h.typ_zmeny = 'PI01') or exists (select 1 from dokumentacni_jednotka dj where dj.pian = p.id and exists (select 1 from archeologicky_zaznam az where az.id = dj.archeologicky_zaznam and exists (select 1 from historie h2 where h2.vazba = az.historie and h2.organizace_snapshot_id = {request.user.organizace_id} and h2.typ_zmeny = 'AZ01'))) or exists (select 1 from dokumentacni_jednotka dj where dj.pian = p.id and exists (select 1 from archeologicky_zaznam az where az.id = dj.archeologicky_zaznam and exists (select 1 from akce a1 where a1.archeologicky_zaznam = az.id and exists (select 1 from projekt p1 where p1.id = a1.projekt and p1.organizace = {request.user.organizace_id})))) or (exists (select 1 from dokumentacni_jednotka dj1 where dj1.pian = p.id and exists (select 1 from archeologicky_zaznam az where az.id = dj1.archeologicky_zaznam and az.pristupnost in ({PRISTUPNOST_ANONYM_ID}, {PRISTUPNOST_BADATEL_ID}, {PRISTUPNOST_ARCHEOLOG_ID}))) and p.stav = {PIAN_POTVRZEN}))"""
        query += query2

    pians = None
    with connection.cursor() as cursor:
        cursor.execute(querysum, bbox_query_params)
        result = cursor.fetchone()
        count = int(result[0]) if result[0] is not None else 0
        if count < LIMIT_PRVKU_ZOBRAZENI_HEATMAP * 2 or zoom > 7:
            cursor.execute(query, bbox_query_params)
            pians = dictfetchall(cursor)
            count = len(pians)

    return pians, count


def get_dj_akce_for_pian(pian_ident_cely, request):
    """
    Funkce pro pro ziskani dj/akce pro pian_ident_cely
    """
    from core.views import PermissionFilterMixin
    from django.db.models import Q

    queryset = DokumentacniJednotka.objects.filter(Q(pian__geom__isnull=False)).filter(
        Q(pian__ident_cely=pian_ident_cely)
    )
    perm_object = PermissionFilterMixin()
    perm_object.request = request
    perm_object.typ_zmeny_lookup = ZAPSANI_AZ
    arch_zaznamy = ArcheologickyZaznam.objects.filter(dokumentacni_jednotky_akce__in=queryset)

    try:
        return queryset.filter(archeologicky_zaznam__in=perm_object.check_filter_permission(arch_zaznamy)).values(
            "ident_cely", "archeologicky_zaznam__ident_cely"
        )
    except IndexError:
        logger.debug(
            "core.utils.get_dj_akce_for_pian.no_records",
            extra={"ident_cely": pian_ident_cely},
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


def get_heatmap_project(left, bottom, right, top, zoom):
    """
    Funkce pro získaní heat mapy projektů ze čtverce.
    """
    query = "select count*30 as pocet, ST_AsGeoJSON(st_centroid) as geom_geojson from amcr_heat_projekt_l2"
    query_zoom = (
        "select count*30 as pocet, ST_AsGeoJSON(st_centroid) as geom_geojson from amcr_heat_projekt_lx2 "
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


def get_message(az, message):
    """
    Funkce pro získaní textu správy podle záznamu.
    """
    return str(
        getattr(
            mc,
            str(dict(ArcheologickyZaznam.CHOICES)[az.typ_zaznamu].upper() + "_" + message),
        )
    )


class SearchTable(ColumnShiftTableBootstrap4):
    """
    Základní setup pro tabulky používané v aplikaci.
    Obsahuje metodu na získaní sloupců které mají byt zobrazeny.
    """

    columns_to_hide = []
    app = None
    column_excluded = ["ident_cely"]

    def get_column_default_show(self):
        """Funkce `SearchTable.get_column_default_show` v modulu `webclient.core.utils`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        self.column_default_show = list(set(self.columns.columns.keys()) - set(self.columns_to_hide))
        return super(SearchTable, self).get_column_default_show()

    def render_nahled(self, value, record):
        """
        Metoda pro správně zobrazení náhledu souboru.
        """
        from pas.models import SamostatnyNalez

        record: SamostatnyNalez
        if record.soubory.soubory.count() > 0:
            soubor = record.soubory.soubory.first()
        else:
            soubor = None
        if soubor is not None:
            from core.models import Soubor

            soubor: Soubor
            soubor_url = reverse(
                "core:download_thumbnail",
                args=(
                    "pas",
                    record.ident_cely,
                    soubor.id,
                ),
            )
            return format_html(
                '<img src="{}" class="image-nahled" data-toggle="modal" data-target="#soubor-modal" '
                'style="opacity:0" onload="this.style.opacity=100">',
                soubor_url,
            )
        return ""

    def get_all_idents(self):
        """
        Vrátí seznam identifikátorů záznamů tabulky.
        """
        return ",".join([record.record.ident_cely for record in self.paginated_rows])


def find_pos_with_backup(lang, project_apps=True, django_apps=False, third_party_apps=False):
    """
    scans a couple possible repositories of gettext catalogs for the given
    language code

    """

    paths = []

    # project/locale
    if settings.SETTINGS_MODULE:
        parts = settings.SETTINGS_MODULE.split(".")
    else:
        # Pokud je `settings.SETTINGS_MODULE` None, pravděpodobně běží testovací režim.
        # a bylo použito `override_settings()`.
        # Viz: https://code.djangoproject.com/ticket/25911
        parts = os.environ.get(ENVIRONMENT_VARIABLE).split(".")
    project = __import__(parts[0], {}, {}, [])
    abs_project_path = os.path.normpath(os.path.abspath(os.path.dirname(project.__file__)))
    if project_apps:
        if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(project.__file__), "locale"))):
            paths.append(os.path.abspath(os.path.join(os.path.dirname(project.__file__), "locale")))
        if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(project.__file__), "..", "locale"))):
            paths.append(os.path.abspath(os.path.join(os.path.dirname(project.__file__), "..", "locale")))

    case_sensitive_file_system = True
    tmphandle, tmppath = tempfile.mkstemp()
    if os.path.exists(tmppath.upper()):
        # Souborový systém nerozlišuje velikost písmen.
        case_sensitive_file_system = False

    # django/locale
    if django_apps:
        django_paths = cache.get("rosetta_django_paths")
        if django_paths is None:
            django_paths = []
            for root, dirnames, filename in os.walk(os.path.abspath(os.path.dirname(django.__file__))):
                if "locale" in dirnames:
                    django_paths.append(os.path.join(root, "locale"))
                    continue
            cache.set("rosetta_django_paths", django_paths, 60 * 60)
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
        if "contrib" in app_path and "django" in app_path and not django_apps:
            continue

        # third party external
        if not third_party_apps and abs_project_path not in app_path:
            continue

        # local apps
        if not project_apps and abs_project_path in app_path:
            continue

        if os.path.exists(os.path.abspath(os.path.join(app_path, "locale"))):
            paths.append(os.path.abspath(os.path.join(app_path, "locale")))
        if os.path.exists(os.path.abspath(os.path.join(app_path, "..", "locale"))):
            paths.append(os.path.abspath(os.path.join(app_path, "..", "locale")))

    ret = set()
    langs = [lang]
    if "-" in lang:
        _l, _c = map(lambda x: x.lower(), lang.split("-", 1))
        langs += ["%s_%s" % (_l, _c), "%s_%s" % (_l, _c.upper()), "%s_%s" % (_l, _c.capitalize())]
    elif "_" in lang:
        _l, _c = map(lambda x: x.lower(), lang.split("_", 1))
        langs += ["%s-%s" % (_l, _c), "%s-%s" % (_l, _c.upper()), "%s_%s" % (_l, _c.capitalize())]

    paths = map(os.path.normpath, paths)
    paths = list(set(paths))
    for path in paths:
        # Exclude paths
        if path not in rosetta_settings.ROSETTA_EXCLUDED_PATHS:
            for lang_ in langs:
                dirname = os.path.join(path, lang_, "LC_MESSAGES")
                for fn in rosetta_settings.POFILENAMES:
                    filename = os.path.join(dirname, fn)
                    abs_path = os.path.abspath(filename)
                    # On case insensitive filesystems (looking at you, MacOS)
                    # Porovná absolutní cestu k PO souboru v malých písmenech.
                    # to all lowercased paths already collected.
                    # Na běžných souborových systémech to nepředstavuje problém.
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
    """Funkce `replace_last` v modulu `webclient.core.utils`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param source_string: Vstupní hodnota používaná při zpracování.
    :param old: Vstupní hodnota používaná při zpracování.
    :param new: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    index = source_string.rfind(old)
    if index != -1:
        start_part = source_string[:index]
        replace_part = source_string[index : index + len(old)].replace(old, new)
        end_part = source_string[index + len(old) :]
        return start_part + replace_part + end_part
    return source_string


class SessionIdentifier:
    """Třída `SessionIdentifier` v modulu `webclient.core.utils`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, request):
        """Funkce `SessionIdentifier.__init__` v modulu `webclient.core.utils`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.cache_key = self._generate_session_key(request)

    def _generate_session_key(self, request):
        """Funkce `SessionIdentifier._generate_session_key` v modulu `webclient.core.utils`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param request: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if "session_uuid" not in request.session:
            request.session["session_uuid"] = str(uuid.uuid4())  # Vytvoří unikátní ID
            request.session.modified = True
        return f"session_{request.session['session_uuid']}_key"

    def clear_cached_files(self):
        """Funkce `SessionIdentifier.clear_cached_files` v modulu `webclient.core.utils`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        cache.delete(f"{self.cache_key}_files")

    def set_ident(self, ident_cely, timeout=3600):
        """Funkce `SessionIdentifier.set_ident` v modulu `webclient.core.utils`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param ident_cely: Vstupní hodnota používaná při zpracování.
        :param timeout: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        old_ident_cely = self.get_ident()
        if old_ident_cely != ident_cely:
            self.clear_cached_files()
        cache.set(self.cache_key, ident_cely, timeout)

    def get_ident(self):
        """Funkce `SessionIdentifier.get_ident` v modulu `webclient.core.utils`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        return cache.get(self.cache_key, None)

    def add_file_reference(self, ident, timeout=3600):
        """Funkce `SessionIdentifier.add_file_reference` v modulu `webclient.core.utils`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param ident: Vstupní hodnota používaná při zpracování.
        :param timeout: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        files = cache.get(f"{self.cache_key}_files", set())
        files.add(ident)
        cache.set(f"{self.cache_key}_files", files, timeout)

    def file_exists(self, ident):
        """Funkce `SessionIdentifier.file_exists` v modulu `webclient.core.utils`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param ident: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        files = cache.get(f"{self.cache_key}_files", set())
        if ident in files:
            return True
        return False

    def remove_file_reference(self, ident):
        """Funkce `SessionIdentifier.remove_file_reference` v modulu `webclient.core.utils`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param ident: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        files = cache.get(f"{self.cache_key}_files", set())
        if ident in files:
            files.remove(ident)
            cache.set(f"{self.cache_key}_files", files)

    def get_cached_files(self):
        """Funkce `SessionIdentifier.get_cached_files` v modulu `webclient.core.utils`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        files = cache.get(f"{self.cache_key}_files", set())
        return files

    def set_project_ownership(self, ident_cely, timeout=7200):
        """
        Uloží vlastnictví projektu pro anonymního uživatele do Redis.
        Používá se pro ověření, že anonymní uživatel může nahrávat soubory pouze k projektu, který sám vytvořil.

        Args:
            ident_cely: identifikátor projektu
            timeout: timeout v sekundách (defaultně 2 hodiny)
        """
        from core.connectors import RedisConnector

        r = RedisConnector.get_connection_decode()
        key = f"anonymous_project_owner_{self.cache_key}"
        r.set(key, ident_cely, ex=timeout)

    def verify_project_ownership(self, ident_cely):
        """
        Ověří, zda anonymní uživatel vlastní daný projekt.

        Args:
            ident_cely: identifikátor projektu

        Returns:
            bool: True pokud uživatel vlastní projekt, jinak False
        """
        from core.connectors import RedisConnector

        r = RedisConnector.get_connection_decode()
        key = f"anonymous_project_owner_{self.cache_key}"
        stored_ident = r.get(key)
        return stored_ident == ident_cely


def get_set_maintenance_in_cache():
    """
    Funkce pro získání nastavení údržby z cache.
    """
    maintenance = cache.get("maintenance")
    if maintenance is None:
        from core.models import OdstavkaSystemu

        odstavka = OdstavkaSystemu.objects.filter(
            info_od__lte=datetime.today(),
            status=True,
        ).order_by("-datum_odstavky", "-cas_odstavky")
        if odstavka.count() > 0:
            maintenance = odstavka[0]
            cache.set("maintenance", maintenance, settings.AUTO_LOGOUT.get("MAINTENANCE_CACHE_TIMEOUT", 600))
        else:
            cache.set("maintenance", False, settings.AUTO_LOGOUT.get("MAINTENANCE_CACHE_TIMEOUT", 600))
            maintenance = False
    return maintenance


def is_maintenance_in_progress():
    """
    Funkce pro zjištění, zda je údržba v průběhu.
    """
    maintenance = get_set_maintenance_in_cache()
    if maintenance:
        if get_timezone().localize(
            datetime.combine(maintenance.datum_odstavky, maintenance.cas_odstavky)
        ) <= datetime.now(get_timezone()):
            return True
    return False


def get_timezone():
    """
    Funkce pro získání časového pásma z nastavení.
    """
    try:
        return pytz.timezone(settings.TIME_ZONE)
    except Exception as err:
        logger.error("core.utils.get_timezone.error", extra={"error": err, "value": settings.TIME_ZONE})
        return pytz.timezone("Europe/Prague")
