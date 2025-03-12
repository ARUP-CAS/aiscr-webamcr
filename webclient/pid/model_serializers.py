from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List

from arch_z.models import AkceVedouci, ArcheologickyZaznam, ExterniOdkaz
from core.constants import (
    ARCHIVACE_AZ,
    ARCHIVACE_DOK,
    ARCHIVACE_SN,
    AZ_STAV_ARCHIVOVANY,
    D_STAV_ARCHIVOVANY,
    EZ_STAV_POTVRZENY,
    ODESLANI_AZ,
    ODESLANI_DOK,
    ODESLANI_SN,
    POTVRZENI_SN,
    VRACENI_AZ,
    VRACENI_DOK,
    VRACENI_SN,
    ZAPSANI_AZ,
    ZAPSANI_DOK,
    ZAPSANI_SN,
    ZMENA_AZ,
)
from core.models import Soubor
from dj.models import DokumentacniJednotka
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from dokument.models import Dokument, DokumentCast
from ez.models import ExterniZdroj
from heslar.hesla_dynamicka import (
    DOKUMENT_RADA_DATA_3D,
    JAZYK_NERELEVANTNI,
    ORGANIZACE_OBECNE,
    OSOBA_ANONYM,
    PRISTUPNOST_ANONYM_ID,
)
from heslar.models import RuianKatastr
from historie.models import Historie
from komponenta.models import Komponenta
from lokalita.models import Lokalita
from pas.models import SamostatnyNalez
from uzivatel.models import Heslar, Organizace, Osoba


class ModelSerializer(ABC):
    def __init__(self, record):
        self.record = record

    @staticmethod
    def format_date(date):
        return date.strftime("%Y-%m-%d")

    @staticmethod
    def format_date_time(date_time):
        return date_time.strftime("%Y-%m-%dT%H:%M:%S%z")

    @abstractmethod
    def _get_creators(self):
        pass

    @abstractmethod
    def _get_historie_queryset(self):
        pass

    @abstractmethod
    def get_ident_cely(self):
        pass

    @abstractmethod
    def _get_publication_year(self):
        pass

    def _get_language(self):
        return "cs"

    @abstractmethod
    def _get_prefix(self):
        pass

    @abstractmethod
    def _get_soubory_queryset(self):
        pass

    @abstractmethod
    def _get_title(self, language: str):
        pass

    def _serialize_alternate_identifiers(self):
        result = [
            {
                "alternateIdentifierType": "Local accession number",
                "alternateIdentifier": self.get_ident_cely(),
            }
        ]
        return result

    def _serialize_contributors(self):
        result = [
            {
                "name": "Archaeological Information System of the Czech Republic",
                "nameType": "Organizational",
                "contributorType": "HostingInstitution",
                "lang": "en",
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "https://ror.org/01a7rqj69",
                        "nameIdentifierScheme": "ROR",
                        "schemeUri": "https://ror.org/",
                    }
                ],
            }
        ]
        return result

    @abstractmethod
    def _serialize_creators(self):
        pass

    @abstractmethod
    def _serialize_dates(self):
        pass

    @abstractmethod
    def _serialize_descriptions(self):
        pass

    @abstractmethod
    def _serialize_geolocations(self):
        pass

    def _serialize_related_identifiers(self):
        result = [
            {
                "relationType": "HasMetadata",
                "relatedIdentifier": f"{settings.DIGI_LINKS['OAPI_link']}{self.get_ident_cely()}",
                "relatedIdentifierType": "URL",
                "relatedMetadataScheme": "OAI-PMH",
                "schemeUri": "http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd",
                "schemeType": "XSD",
            }
        ]
        return result

    @abstractmethod
    def _serialize_rightslist(self):
        pass

    def _serialize_subjects(self):
        result = [
            frozenset(
                {
                    "subject": "History and Archaeology",
                    "valueUri": "http://dd.eionet.europa.eu/vocabulary/eurostat/fos07/FOS601",
                    "schemeUri": "http://dd.eionet.europa.eu/vocabulary/eurostat/fos07/",
                    "subjectScheme": "Field of science and technology classification (FOS 2007)",
                    "lang": "en",
                    "classificationCode": "FOS601",
                }.items()
            )
        ]
        return result

    @abstractmethod
    def _serialize_types(self):
        pass

    def serialize_delete(self):
        return {
            "data": {
                "type": "dois",
                "attributes": {
                    "event": "hide",
                    "descriptions": self._serialize_descriptions()
                    + [
                        {
                            "lang": "en",
                            "description": "This record has been removed from the AMCR repository. In justified cases, data can be retrieved from a backup copy by the system administrator on request.",
                            "descriptionType": "TechnicalInfo",
                        }
                    ],
                },
            }
        }

    def serialize_hide(self):
        return {"data": {"type": "dois", "attributes": {"event": "hide"}}}

    def serialize_publish(self):
        data = {
            "data": {
                "type": "dois",
                "attributes": {
                    "event": "publish",
                    "doi": f"{self._get_prefix()}/{self.get_ident_cely()}",
                    "alternateIdentifiers": self._serialize_alternate_identifiers(),
                    "creators": self._serialize_creators(),
                    "titles": [
                        {
                            "lang": "en",
                            "title": self._get_title("en"),
                        },
                        {
                            "lang": "cs",
                            "title": self._get_title("cs"),
                            "titleType": "TranslatedTitle",
                        },
                    ],
                    "publisher": {
                        "lang": "en",
                        "name": "Archaeological Map of the Czech Republic",
                        "schemeUri": "https://www.re3data.org/repository/",
                        "publisherIdentifier": "https://www.re3data.org/repository/r3d100013576",
                        "publisherIdentifierScheme": "re3data",
                    },
                    "publicationYear": self._get_publication_year(),
                    "subjects": self._serialize_subjects(),
                    "contributors": self._serialize_contributors(),
                    "dates": self._serialize_dates(),
                    "language": self._get_language() or "",
                    "types": self._serialize_types(),
                    "relatedIdentifiers": self._serialize_related_identifiers(),
                    "sizes": [
                        f"{sum([soubor.size_mb for soubor in self._get_soubory_queryset().all()])} MB",
                        f"{sum([soubor.rozsah for soubor in self._get_soubory_queryset().all()])} pages",
                    ]
                    if isinstance(self.record, Dokument)
                    and self._get_soubory_queryset()
                    and self._get_soubory_queryset().exists()
                    else [],
                    "formats": list(set([soubor.mimetype for soubor in self._get_soubory_queryset().all()]))
                    if isinstance(self.record, Dokument)
                    and self._get_soubory_queryset()
                    and self._get_soubory_queryset().exists()
                    else [],
                    "version": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "rightsList": self._serialize_rightslist(),
                    "descriptions": self._serialize_descriptions(),
                    "geoLocations": self._serialize_geolocations(),
                    "url": f"{settings.DIGI_LINKS['Digi_archiv_link']}{self.get_ident_cely()}",
                },
            }
        }
        return data

    def serialize_update(self):
        result = self.serialize_publish()
        result["data"]["attributes"].pop("event")
        return result


class PartialSerializer(ABC):
    def __init__(self, record):
        self.record = record

    def serialize_publish(self):
        pass


def convert_geo_location_to_dict(item) -> Dict:
    item = dict(item)
    if "geoLocationPoint" in item:
        item["geoLocationPoint"] = dict(item["geoLocationPoint"])
    return item


def serialize_ez_creator(autor: Osoba) -> Dict[str, str]:
    return {"name": autor.vypis_cely, "givenName": autor.jmeno, "familyName": autor.prijmeni, "nameType": "Personal"}


def serialize_ez_contributor(contributor: Osoba) -> Dict[str, str]:
    return {
        "name": contributor.vypis_cely,
        "givenName": contributor.jmeno,
        "familyName": contributor.prijmeni,
        "nameType": "Personal",
        "contributorType": "Editor",
    }


def serialize_geom(geom=None, katastr: RuianKatastr | None = None, verejne: bool | None = False) -> frozenset:
    serialized_geom = {}
    if geom and verejne:
        serialized_geom.update(
            {
                "geoLocationPoint": frozenset(
                    {"pointLatitude": geom.centroid.y, "pointLongitude": geom.centroid.x}.items()
                )
            }
        )
    if katastr:
        if verejne:
            serialized_geom[
                "geoLocationPlace"
            ] = f"{katastr.nazev}, {katastr.okres.nazev}, {katastr.okres.kraj.nazev}, Czech Republic"
        else:
            serialized_geom["geoLocationPlace"] = f"{katastr.okres.nazev}, {katastr.okres.kraj.nazev}, Czech Republic"
    return frozenset(serialized_geom.items())


def serialize_affiliation(organizace: Organizace):
    serialized_affiliation = {"name": organizace.nazev}
    if organizace.ror:
        serialized_affiliation["affiliationIdentifier"] = organizace.ror
        serialized_affiliation["affiliationIdentifierScheme"] = "ROR"
        serialized_affiliation["schemeUri"] = "https://ror.org/"
    return serialized_affiliation


def serialize_organizace_contributor(organizace: Organizace, contributor_type: str):
    return {
        "name": organizace.nazev,
        "nameType": "Organizational",
        "contributorType": contributor_type,
        "lang": "cs",
        "nameIdentifiers": [
            {
                "nameIdentifier": organizace.ror,
                "nameIdentifierScheme": "ROR",
                "schemeUri": "https://ror.org/",
            }
        ]
        if organizace.ror
        else [],
    }


def serialize_osoba_identifiers(osoba: Osoba):
    result = [
        {
            "schemeUri": settings.DIGI_LINKS["OAPI_link"],
            "nameIdentifier": f"{settings.DIGI_LINKS['OAPI_link']}{osoba.ident_cely}",
            "nameIdentifierScheme": "AMCR",
        }
    ]
    if osoba.orcid:
        result += [{"schemeUri": "https://orcid.org/", "nameIdentifier": osoba.orcid, "nameIdentifierScheme": "ORCID"}]
    if osoba.wikidata:
        result += [
            {
                "schemeUri": "https://www.wikidata.org/entity/",
                "nameIdentifier": osoba.wikidata,
                "nameIdentifierScheme": "Wikidata",
            }
        ]
    return result


def serialize_osoba(osoba: Osoba, organizace: Organizace | None = None, contributor_type: str | None = None) -> Dict:
    serialized_record = {
        "name": osoba.vypis_cely if osoba.pk != OSOBA_ANONYM else ":unkn",
        "nameType": "Personal",
        "givenName": osoba.jmeno if osoba.pk != OSOBA_ANONYM else "",
        "familyName": osoba.prijmeni if osoba.pk != OSOBA_ANONYM else "",
        "affiliation": [serialize_affiliation(organizace)]
        if organizace and organizace.pk not in ORGANIZACE_OBECNE
        else [],
        "nameIdentifiers": serialize_osoba_identifiers(osoba),
    }
    if contributor_type:
        serialized_record["contributorType"] = contributor_type
    return serialized_record


def serialize_subject(serialized_record, subject_attr="heslo_en", lang="en"):
    if serialized_record is None:
        return frozenset()
    output = {
        "subject": getattr(serialized_record, subject_attr),
        "valueUri": f"{settings.DIGI_LINKS['OAPI_link']}{serialized_record.ident_cely}",
        "schemeUri": settings.DIGI_LINKS["OAPI_link"],
        "subjectScheme": "AMCR",
        "lang": lang,
        "classificationCode": serialized_record.ident_cely,
    }
    return frozenset(output.items())


def serialize_subjects_komponenty(komp: Komponenta):
    result = [serialize_subject(komp.obdobi)]
    result += [serialize_subject(komp.areal)]
    result += [serialize_subject(aktivita) for aktivita in komp.aktivity.all()]
    result += [serialize_subject(objekt.druh) for objekt in komp.objekty.all()]
    result += [serialize_subject(objekt.specifikace) for objekt in komp.objekty.all()]
    result += [serialize_subject(predmet.druh) for predmet in komp.predmety.all()]
    result += [serialize_subject(predmet.specifikace) for predmet in komp.predmety.all()]
    return result


def serialize_dates_coverage(datace: Heslar) -> frozenset:
    try:
        result = frozenset(
            {
                "date": f"{datace.datace_obdobi.rok_od_min}/{datace.datace_obdobi.rok_do_max}",
                "dateInformation": datace.heslo_en,
                "dateType": "Coverage",
            }.items()
        )
    except ObjectDoesNotExist:
        result = []
    return result


class DokumentSerializer(ModelSerializer):
    def __init__(self, record: Dokument):
        super().__init__(record)
        self.record: Dokument

    def _get_creators(self):
        return self.record.dokumentautor_set.all()

    def _get_historie_queryset(self):
        return self.record.historie.historie_set

    def get_ident_cely(self):
        return self.record.ident_cely

    def _get_language(self):
        jazyk = self.record.jazyky.exclude(pk=JAZYK_NERELEVANTNI).order_by("razeni").first()
        if jazyk is None:
            return None
        return jazyk.zkratka

    def _get_publication_year(self):
        return self.record.rok_vzniku

    def _get_prefix(self):
        return settings.DOI_PREFIX

    def _get_soubory_queryset(self):
        if self.record.soubory:
            return self.record.soubory.soubory

    def _get_title(self, language: str):
        return {
            "en": f"AMCR {self.get_ident_cely()} – {self.record.typ_dokumentu.heslo_en}",
            "cs": f"AMCR {self.get_ident_cely()} – {self.record.typ_dokumentu.heslo}",
        }[language]

    def _serialize_alternate_identifiers(self):
        alternate_identifiers = super()._serialize_alternate_identifiers()
        if self.record.oznaceni_originalu:
            alternate_identifiers += [
                {
                    "alternateIdentifierType": "Original label",
                    "alternateIdentifier": self.record.oznaceni_originalu,
                }
            ]
        return alternate_identifiers

    def _serialize_contributors(self):
        contributors = super()._serialize_contributors()
        if self.record.let and self.record.let.pozorovatel:
            contributors += [serialize_osoba(self.record.let.pozorovatel, self.record.let.organizace, "ProjectLeader")]
        for cast in self.record.casti.all():
            cast: DokumentCast
            try:
                if cast.neident_akce and cast.neident_akce.vedouci:
                    for vedouci in cast.neident_akce.vedouci.all():
                        contributors += [serialize_osoba(vedouci, contributor_type="ProjectLeader")]
            except ObjectDoesNotExist:
                pass
            if cast.archeologicky_zaznam:
                try:
                    if cast.archeologicky_zaznam.akce.hlavni_vedouci:
                        contributors += [
                            serialize_osoba(
                                cast.archeologicky_zaznam.akce.hlavni_vedouci,
                                cast.archeologicky_zaznam.akce.organizace,
                                "ProjectLeader",
                            )
                        ]
                    for akce_vedouci in cast.archeologicky_zaznam.akce.akcevedouci_set.all():
                        akce_vedouci: AkceVedouci
                        contributors += [
                            serialize_osoba(akce_vedouci.vedouci, akce_vedouci.organizace, "ProjectMember")
                        ]
                except ObjectDoesNotExist:
                    pass
            if cast.projekt and cast.projekt.vedouci_projektu:
                contributors += [
                    serialize_osoba(cast.projekt.vedouci_projektu, cast.projekt.organizace, "ProjectLeader")
                ]
        return contributors

    def _serialize_creators(self):
        return [serialize_osoba(author.autor, self.record.organizace) for author in self._get_creators()]

    def _serialize_dates(self):
        dates = []
        try:
            if self.record.extra_data and self.record.extra_data.datum_vzniku:
                dates += [{"date": self.format_date(self.record.extra_data.datum_vzniku), "dateType": "Created"}]
        except ObjectDoesNotExist:
            pass
        for date in self.record.historie.historie_set.all():
            date: Historie
            if date.typ_zmeny == ZAPSANI_DOK:
                dates += [{"date": self.format_date_time(date.datum_zmeny), "dateType": "Created"}]
            elif date.typ_zmeny == ODESLANI_DOK:
                dates += [{"date": self.format_date_time(date.datum_zmeny), "dateType": "Submitted"}]
            elif date.typ_zmeny == ARCHIVACE_DOK:
                dates += [{"date": self.format_date_time(date.datum_zmeny), "dateType": "Issued"}]
            elif date.typ_zmeny == VRACENI_DOK:
                dates += [{"date": self.format_date_time(date.datum_zmeny), "dateType": "Withdrawn"}]
        dates = [frozenset(d.items()) for d in dates]
        for cast in self.record.casti.all():
            cast: DokumentCast
            if cast.komponenty:
                for komp in cast.komponenty.komponenty.all():
                    komp: Komponenta
                    dates += [serialize_dates_coverage(komp.obdobi)]
            if cast.archeologicky_zaznam:
                for dj in cast.archeologicky_zaznam.dokumentacni_jednotky_akce.all():
                    dj: DokumentacniJednotka
                    for komp in dj.komponenty.komponenty.all():
                        komp: Komponenta
                        dates += [serialize_dates_coverage(komp.obdobi)]
        dates = [dict(item) for item in set(dates) if item]
        return dates

    def _serialize_descriptions(self) -> List[Dict]:
        descriptions = []
        if self.record.popis:
            descriptions.append({"lang": "cs", "description": self.record.popis, "descriptionType": "Abstract"})
        if self.record.poznamka:
            descriptions.append({"lang": "cs", "description": self.record.poznamka, "descriptionType": "TechnicalInfo"})
        return descriptions

    def _serialize_geolocations(self):
        geo_locations: List[frozenset] = []
        try:
            if self.record.extra_data.geom and self.record.rada == DOKUMENT_RADA_DATA_3D:
                geo_locations.append(serialize_geom(self.record.extra_data.geom, verejne=True))
        except ObjectDoesNotExist:
            pass
        for cast in self.record.casti.all():
            cast: DokumentCast
            try:
                if cast.neident_akce and cast.neident_akce.katastr:
                    geo_locations.append(
                        serialize_geom(cast.neident_akce.katastr.definicni_bod, cast.neident_akce.katastr, True)
                    )
            except ObjectDoesNotExist:
                pass
            if cast.projekt and cast.projekt.hlavni_katastr:
                verejne = cast.projekt.pristupnost.pk == PRISTUPNOST_ANONYM_ID
                geo_locations.append(
                    serialize_geom(cast.projekt.hlavni_katastr.definicni_bod, cast.projekt.hlavni_katastr, verejne)
                )
                for katastr in cast.projekt.katastry.all():
                    katastr: RuianKatastr
                    geo_locations.append(serialize_geom(katastr.definicni_bod, katastr, verejne))
            if (
                cast.archeologicky_zaznam
                and cast.archeologicky_zaznam.hlavni_katastr
                and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
            ):
                verejne = cast.archeologicky_zaznam.pristupnost.pk == PRISTUPNOST_ANONYM_ID
                geo_locations.append(
                    serialize_geom(
                        cast.archeologicky_zaznam.hlavni_katastr.definicni_bod,
                        cast.archeologicky_zaznam.hlavni_katastr,
                        verejne,
                    )
                )
                for katastr in cast.archeologicky_zaznam.katastry.all():
                    katastr: RuianKatastr
                    geo_locations.append(serialize_geom(katastr.definicni_bod, katastr, verejne))
        result = [convert_geo_location_to_dict(item) for item in list(set(geo_locations))]
        return result

    def _serialize_related_identifiers(self):
        related_identifiers = super()._serialize_related_identifiers()
        for soubor in self._get_soubory_queryset().all():
            soubor: Soubor
            related_identifiers += [
                {
                    "relationType": "HasPart",
                    "relatedIdentifier": soubor.url,
                    "resourceTypeGeneral": "Dataset",
                    "relatedIdentifierType": "URL",
                }
            ]
        if self.record.let:
            related_identifiers += [
                {
                    "relationType": "Documents",
                    "relatedIdentifier": f"{settings.DIGI_LINKS['Digi_archiv_link']}{self.record.let.ident_cely}",
                    "resourceTypeGeneral": "Project",
                    "relatedIdentifierType": "URL",
                }
            ]
        for cast in self.record.casti.all():
            cast: DokumentCast
            if cast.archeologicky_zaznam and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY:
                if cast.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
                    related_identifiers += [
                        {
                            "relationType": "Documents",
                            "relatedIdentifier": f"{settings.DIGI_LINKS['Digi_archiv_link']}{cast.archeologicky_zaznam.ident_cely}",
                            "resourceTypeGeneral": "Project",
                            "relatedIdentifierType": "URL",
                        }
                    ]
                elif cast.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA:
                    related_identifiers += [
                        {
                            "relationType": "Documents",
                            "relatedIdentifier": cast.archeologicky_zaznam.lokalita.igsn,
                            "resourceTypeGeneral": "PhysicalObject",
                            "relatedIdentifierType": "IGSN",
                        }
                    ]
            elif cast.projekt:
                related_identifiers += [
                    {
                        "relationType": "Documents",
                        "relatedIdentifier": f"{settings.DIGI_LINKS['Digi_archiv_link']}{cast.projekt.ident_cely}",
                        "resourceTypeGeneral": "Project",
                        "relatedIdentifierType": "URL",
                    }
                ]
        return related_identifiers

    def _serialize_rightslist(self):
        result = []
        if self.record.licence:
            serialized_rights = {
                "rights": self.record.licence.heslo_en,
                "lang": "en",
            }
            spdx_query = self.record.licence.heslar_odkaz.filter(zdroj="SPDX").first()
            if spdx_query:
                serialized_rights["rightsUri"] = spdx_query.uri
                serialized_rights["schemeUri"] = spdx_query.scheme_uri
                serialized_rights["rightsIdentifier"] = spdx_query.kod
                serialized_rights["rightsIdentifierScheme"] = spdx_query.zdroj
            result = [serialized_rights]
        return result

    def _serialize_subjects(self):
        serialized_subjects = super()._serialize_subjects()
        serialized_subjects += [serialize_subject(posudek) for posudek in self.record.posudky.all()]
        serialized_subjects += [serialize_subject(osoba, "vypis_cely", "") for osoba in self.record.osoby.all()]
        if self.record.has_extra_data():
            serialized_subjects += [serialize_subject(self.record.extra_data.udalost_typ)]
        for cast in self.record.casti.all():
            cast: DokumentCast
            for komp in cast.komponenty.komponenty.all():
                komp: Komponenta
                serialized_subjects += serialize_subjects_komponenty(komp)
            try:
                if cast.archeologicky_zaznam and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY:
                    serialized_subjects += [serialize_subject(cast.archeologicky_zaznam.akce.hlavni_typ)]
                    serialized_subjects += [serialize_subject(cast.archeologicky_zaznam.akce.vedlejsi_typ)]
                    for dj in cast.archeologicky_zaznam.dokumentacni_jednotky_akce.all():
                        dj: DokumentacniJednotka
                        for komp in dj.komponenty.komponenty.all():
                            komp: Komponenta
                            serialized_subjects += serialize_subjects_komponenty(komp)
            except ObjectDoesNotExist:
                pass
            try:
                if cast.archeologicky_zaznam and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY:
                    serialized_subjects += [serialize_subject(cast.archeologicky_zaznam.lokalita.typ_lokality)]
                    serialized_subjects += [serialize_subject(cast.archeologicky_zaznam.lokalita.druh)]
                    for dj in cast.archeologicky_zaznam.dokumentacni_jednotky_akce.all():
                        dj: DokumentacniJednotka
                        for komp in dj.komponenty.komponenty.all():
                            komp: Komponenta
                            serialized_subjects += [serialize_subject(komp.obdobi)]
                            serialized_subjects += [serialize_subject(komp.areal)]
                            serialized_subjects += serialize_subjects_komponenty(komp)
            except ObjectDoesNotExist:
                pass
        serialized_subjects = [dict(item) for item in set(serialized_subjects) if item]
        return serialized_subjects

    def _serialize_types(self) -> dict:
        resource_type_query = self.record.typ_dokumentu.heslar_odkaz.filter(zdroj="DataCite").filter(
            nazev_kodu="resourceTypeGeneral"
        )
        serialized_types = {}
        if resource_type_query.exists():
            serialized_types["resourceType"] = resource_type_query.first().heslo.heslo_en
            serialized_types["resourceTypeGeneral"] = resource_type_query.first().kod
        else:
            serialized_types["resourceType"] = "Dataset"
            serialized_types["resourceTypeGeneral"] = "Dataset"
        return serialized_types


class SamostatnyNalezSerializer(ModelSerializer):
    def __init__(self, record: SamostatnyNalez):
        super().__init__(record)
        self.record: SamostatnyNalez

    def _get_creators(self):
        pass

    def _get_historie_queryset(self):
        return self.record.historie.historie_set

    def get_ident_cely(self):
        return self.record.ident_cely

    def _get_soubory_queryset(self):
        if self.record.soubory:
            return self.record.soubory.soubory

    def _get_prefix(self):
        return settings.IGSN_PREFIX

    def _get_publication_year(self):
        publication_year_history = self._get_historie_queryset().filter(typ_zmeny=ARCHIVACE_SN)
        if publication_year_history.exists():
            return publication_year_history.first().datum_zmeny.year
        else:
            # DataCite request may be called before the history record is created
            return datetime.now().year

    def _get_title(self, language: str):
        return {
            "en": f"AMCR {self.record.ident_cely} – {self.record.druh_nalezu.heslo_en if self.record.druh_nalezu else ''} ({self.record.specifikace.heslo_en if self.record.specifikace else ''}), {self.record.obdobi.heslo_en if self.record.obdobi else ''}",
            "cs": f"AMCR {self.record.ident_cely} – {self.record.druh_nalezu.heslo if self.record.druh_nalezu else ''} ({self.record.specifikace.heslo if self.record.specifikace else ''}), {self.record.obdobi.heslo if self.record.obdobi else ''}",
        }[language]

    def _serialize_alternate_identifiers(self):
        alternate_identifiers = super()._serialize_alternate_identifiers()
        if self.record.evidencni_cislo:
            alternate_identifiers += [
                {
                    "alternateIdentifierType": "Find inventory number",
                    "alternateIdentifier": self.record.evidencni_cislo,
                }
            ]
        return alternate_identifiers

    def _serialize_contributors(self):
        contributors = super()._serialize_contributors()
        if self.record.projekt.vedouci_projektu and self.record.projekt.organizace:
            contributors += [
                serialize_osoba(self.record.projekt.vedouci_projektu, self.record.projekt.organizace, "ProjectLeader")
            ]
        if self.record.predano_organizace and self.record.predano_organizace.pk not in ORGANIZACE_OBECNE:
            contributors += [serialize_organizace_contributor(self.record.predano_organizace, "DataCurator")]
        return contributors

    def _serialize_creators(self):
        if self.record.nalezce:
            result = [serialize_osoba(self.record.nalezce, self.record.projekt.organizace)]
        else:
            result = []
        return result

    def _serialize_dates(self):
        dates = []
        if self.record.datum_nalezu:
            dates += [{"date": self.format_date(self.record.datum_nalezu), "dateType": "Collected"}]
        for date in self.record.historie.historie_set.all():
            date: Historie
            if date.typ_zmeny == ZAPSANI_SN:
                dates += [{"date": self.format_date_time(date.datum_zmeny), "dateType": "Created"}]
            elif date.typ_zmeny == ODESLANI_SN:
                dates += [{"date": self.format_date_time(date.datum_zmeny), "dateType": "Submitted"}]
            elif date.typ_zmeny == POTVRZENI_SN:
                dates += [{"date": self.format_date_time(date.datum_zmeny), "dateType": "Accepted"}]
            elif date.typ_zmeny == ARCHIVACE_SN:
                dates += [{"date": self.format_date_time(date.datum_zmeny), "dateType": "Issued"}]
            elif date.typ_zmeny == VRACENI_SN:
                dates += [{"date": self.format_date_time(date.datum_zmeny), "dateType": "Withdrawn"}]
        try:
            if self.record.obdobi.datace_obdobi:
                dates += [dict(serialize_dates_coverage(self.record.obdobi))]
        except ObjectDoesNotExist:
            pass
        return dates

    def _serialize_descriptions(self):
        descriptions = [{"lang": "en", "description": "Collected by field survey.", "descriptionType": "Methods"}]
        if self.record.poznamka:
            descriptions.append({"lang": "cs", "description": self.record.poznamka, "descriptionType": "Abstract"})
        if self.record.okolnosti:
            descriptions.append(
                {
                    "lang": "cs",
                    "description": f"Finding context: {self.record.okolnosti.heslo_en}",
                    "descriptionType": "Abstract",
                }
            )
        if self.record.okolnosti:
            descriptions.append(
                {"lang": "cs", "description": f"Finding depth: {self.record.hloubka} cm", "descriptionType": "Abstract"}
            )
        if self.record.pocet:
            descriptions.append(
                {"lang": "cs", "description": f"Number of finds: {self.record.pocet}", "descriptionType": "Abstract"}
            )
        return descriptions

    def _serialize_geolocations(self):
        geo_locations: List[Dict] = []
        if self.record.katastr:
            verejne = self.record.pristupnost.pk == PRISTUPNOST_ANONYM_ID
            geo_locations.append(
                convert_geo_location_to_dict(
                    serialize_geom(self.record.katastr.definicni_bod, self.record.katastr, verejne)
                )
            )
        return geo_locations

    def _serialize_related_identifiers(self):
        related_identifiers = super()._serialize_related_identifiers()
        for soubor in self._get_soubory_queryset().all():
            soubor: Soubor
            related_identifiers += [
                {
                    "relationType": "IsDocumentedBy",
                    "relatedIdentifier": soubor.url,
                    "resourceTypeGeneral": "Image",
                    "relatedIdentifierType": "URL",
                }
            ]
        related_identifiers += [
            {
                "relationType": "IsPartOf",
                "relatedIdentifier": f"{settings.DIGI_LINKS['Digi_archiv_link']}{self.record.projekt.ident_cely}",
                "resourceTypeGeneral": "Project",
                "relatedIdentifierType": "URL",
            }
        ]
        return related_identifiers

    def _serialize_rightslist(self):
        return [
            {
                "rights": "Creative Commons Attribution-NonCommercial 4.0 International",
                "rightsUri": "https://spdx.org/licenses/CC-BY-NC-4.0.html",
                "schemeUri": "https://spdx.org/licenses",
                "rightsIdentifier": "CC-BY-NC-4.0",
                "rightsIdentifierScheme": "SPDX",
                "lang": "en",
            }
        ]

    def _serialize_subjects(self):
        serialized_subjects = super()._serialize_subjects()
        if self.record.obdobi:
            serialized_subjects += [
                serialize_subject(self.record.obdobi),
            ]
        if self.record.druh_nalezu:
            serialized_subjects += [
                serialize_subject(self.record.druh_nalezu),
            ]
        if self.record.specifikace:
            serialized_subjects += [
                serialize_subject(self.record.specifikace),
            ]
        serialized_subjects = [dict(item) for item in serialized_subjects]
        return serialized_subjects

    def _serialize_types(self):
        return {"resourceType": "archaeological object", "resourceTypeGeneral": "PhysicalObject"}


class LokalitaSerializer(ModelSerializer):
    def __init__(self, record: Lokalita):
        super().__init__(record)
        self.record: Lokalita

    def _get_creators(self):
        pass

    def get_ident_cely(self):
        return self.record.archeologicky_zaznam.ident_cely

    def _get_historie_queryset(self):
        return self.record.archeologicky_zaznam.historie.historie_set

    def _get_prefix(self):
        return settings.IGSN_PREFIX

    def _serialize_contributors(self):
        return super()._serialize_contributors()

    def _get_soubory_queryset(self):
        return None

    def _serialize_dates(self) -> List[Dict]:
        dates: List[Dict] = []
        for date in self.record.archeologicky_zaznam.historie.historie_set.all():
            date: Historie
            if date.typ_zmeny == ZAPSANI_AZ:
                dates += [{"date": self.format_date_time(date.datum_zmeny), "dateType": "Created"}]
            elif date.typ_zmeny == ODESLANI_AZ:
                dates += [{"date": self.format_date_time(date.datum_zmeny), "dateType": "Submitted"}]
            elif date.typ_zmeny == ZMENA_AZ:
                dates += [{"date": self.format_date_time(date.datum_zmeny), "dateType": "Updated"}]
            elif date.typ_zmeny == ARCHIVACE_AZ:
                dates += [{"date": self.format_date_time(date.datum_zmeny), "dateType": "Issued"}]
            elif date.typ_zmeny == VRACENI_AZ:
                dates += [{"date": self.format_date_time(date.datum_zmeny), "dateType": "Withdrawn"}]
        dates: List[frozenset] = [frozenset(d.items()) for d in dates]
        for dj in self.record.archeologicky_zaznam.dokumentacni_jednotky_akce.all():
            dj: DokumentacniJednotka
            for komp in dj.komponenty.komponenty.all():
                komp: Komponenta
                dates += [serialize_dates_coverage(komp.obdobi)]
        dates: List[Dict] = [dict(item) for item in set(dates) if item]
        return dates

    def _serialize_descriptions(self):
        descriptions = [
            {
                "lang": "en",
                "description": "Authoritative summary record of archaeological finds and observations corresponding to a specific site with characteristic archaeological manifestation and presumed past functional context.",
                "descriptionType": "Methods",
            }
        ]
        if self.record.popis and self.record.archeologicky_zaznam.pristupnost.pk == PRISTUPNOST_ANONYM_ID:
            descriptions.append({"lang": "cs", "description": self.record.popis, "descriptionType": "Abstract"})
        if self.record.zachovalost:
            descriptions.append(
                {
                    "lang": "cs",
                    "description": f"State of preservation: {self.record.zachovalost.heslo_en}",
                    "descriptionType": "Abstract",
                }
            )
        if self.record.jistota:
            descriptions.append(
                {
                    "lang": "cs",
                    "description": f"Level of confidence: {self.record.jistota.heslo_en}",
                    "descriptionType": "Abstract",
                }
            )
        if self.record.poznamka:
            descriptions.append({"lang": "cs", "description": self.record.poznamka, "descriptionType": "TechnicalInfo"})
        return descriptions

    def _get_externi_odkaz_query(self):
        return self.record.archeologicky_zaznam.externi_odkazy.filter(
            externi_zdroj__typ__heslar_odkaz__zdroj="DataCite"
        ).filter(externi_zdroj__typ__heslar_odkaz__nazev_kodu="resourceTypeGeneral")

    def _serialize_geolocations(self):
        geo_locations: List[frozenset] = []
        verejne = self.record.archeologicky_zaznam.pristupnost.pk == PRISTUPNOST_ANONYM_ID
        geo_locations.append(
            serialize_geom(
                self.record.archeologicky_zaznam.hlavni_katastr.definicni_bod,
                self.record.archeologicky_zaznam.hlavni_katastr,
                verejne,
            )
        )
        for katastr in self.record.archeologicky_zaznam.katastry.all():
            katastr: RuianKatastr
            geo_locations.append(serialize_geom(katastr.definicni_bod, katastr, verejne))
        result = [convert_geo_location_to_dict(item) for item in list(set(geo_locations))]
        return result

    def _get_publication_year(self):
        archivace_history_queryset = self._get_historie_queryset().filter(typ_zmeny=ARCHIVACE_AZ)
        if archivace_history_queryset.exists():
            return archivace_history_queryset.first().datum_zmeny.year
        else:
            # DataCite request may be called before the history record is created
            return datetime.now().year

    def _serialize_rightslist(self):
        return [
            {
                "rights": "Creative Commons Attribution-NonCommercial 4.0 International",
                "rightsUri": "https://spdx.org/licenses/CC-BY-NC-4.0.html",
                "schemeUri": "https://spdx.org/licenses",
                "rightsIdentifier": "CC-BY-NC-4.0",
                "rightsIdentifierScheme": "SPDX",
                "lang": "en",
            }
        ]

    def _get_title(self, language: str):
        return {
            "en": f"AMCR {self.get_ident_cely()} – {self.record.druh.heslo_en} {self.record.nazev * (self.record.archeologicky_zaznam.pristupnost.pk == PRISTUPNOST_ANONYM_ID)}",
            "cs": f"AMCR {self.get_ident_cely()} – {self.record.druh.heslo} {self.record.nazev * (self.record.archeologicky_zaznam.pristupnost.pk == PRISTUPNOST_ANONYM_ID)}",
        }[language]

    def _serialize_alternate_identifiers(self):
        alternate_identifiers = super()._serialize_alternate_identifiers()
        if self.record.archeologicky_zaznam.uzivatelske_oznaceni:
            alternate_identifiers += [
                {
                    "alternateIdentifierType": "External identifier",
                    "alternateIdentifier": self.record.archeologicky_zaznam.uzivatelske_oznaceni,
                }
            ]
        return alternate_identifiers

    def _serialize_creators(self):
        result = [
            {
                "name": "Archaeological Information System of the Czech Republic",
                "nameType": "Organizational",
                "lang": "en",
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "https://ror.org/01a7rqj69",
                        "nameIdentifierScheme": "ROR",
                        "schemeUri": "https://ror.org/",
                    }
                ],
            }
        ]
        return result

    def _serialize_related_identifiers(self):
        related_identifiers = super()._serialize_related_identifiers()
        casti_dokumentu_query = (
            self.record.archeologicky_zaznam.casti_dokumentu.filter(
                dokument__typ_dokumentu__heslar_odkaz__zdroj="DataCite"
            )
        ).filter(dokument__typ_dokumentu__heslar_odkaz__nazev_kodu="resourceTypeGeneral")
        for cast in casti_dokumentu_query:
            cast: DokumentCast
            if cast.dokument.stav == D_STAV_ARCHIVOVANY and cast.dokument.doi:
                related_identifiers += [
                    {
                        "relationType": "IsDocumentedBy",
                        "relatedIdentifier": cast.dokument.doi,
                        "resourceTypeGeneral": cast.dokument.typ_dokumentu.heslar_odkaz.filter(zdroj="DataCite")
                        .filter(nazev_kodu="resourceTypeGeneral")
                        .first()
                        .kod,
                        "relatedIdentifierType": "DOI",
                    }
                ]
        for externi_odkaz in self._get_externi_odkaz_query():
            externi_odkaz: ExterniOdkaz
            if externi_odkaz.externi_zdroj.doi:
                related_identifiers += [
                    {
                        "relationType": "IsPublishedIn",
                        "relatedIdentifier": externi_odkaz.externi_zdroj.doi,
                        "resourceTypeGeneral": externi_odkaz.externi_zdroj.typ.heslar_odkaz.filter(zdroj="DataCite")
                        .filter(nazev_kodu="resourceTypeGeneral")
                        .first()
                        .kod,
                        "relatedIdentifierType": "DOI",
                    }
                ]
            else:
                related_identifiers += [
                    {
                        "relationType": "IsPublishedIn",
                        "relatedIdentifier": f"{settings.DIGI_LINKS['Digi_archiv_link']}{externi_odkaz.externi_zdroj.ident_cely}",
                        "resourceTypeGeneral": externi_odkaz.externi_zdroj.typ.heslar_odkaz.filter(zdroj="DataCite")
                        .filter(nazev_kodu="resourceTypeGeneral")
                        .first()
                        .kod,
                        "relatedIdentifierType": "URL",
                    }
                ]
        return related_identifiers

    def _serialize_related_items(self):
        related_items = []
        for externi_odkaz in self._get_externi_odkaz_query():
            externi_odkaz: ExterniOdkaz
            externi_zdroj: ExterniZdroj = externi_odkaz.externi_zdroj
            if externi_zdroj.stav == EZ_STAV_POTVRZENY:
                related_item = {
                    "relatedItemType": externi_zdroj.typ.heslar_odkaz.filter(zdroj="DataCite")
                    .filter(nazev_kodu="resourceTypeGeneral")
                    .first()
                    .kod,
                    "relationType": "IsPublishedIn",
                }
                if externi_zdroj.doi:
                    related_item["relatedItemIdentifier"] = {
                        "relatedItemIdentifier": externi_zdroj.doi,
                        "relatedItemIdentifierType": "DOI",
                    }
                else:
                    related_item["relatedItemIdentifier"] = {
                        "relatedItemIdentifier": f"{settings.DIGI_LINKS['Digi_archiv_link']}{externi_zdroj.ident_cely}",
                        "relatedItemIdentifierType": "URL",
                    }
                related_item["creators"] = [
                    serialize_ez_creator(ea.autor) for ea in externi_zdroj.externizdrojautor_set.all()
                ]
                related_item["titles"] = [{"title": externi_zdroj.nazev}]
                if externi_zdroj.sbornik_nazev and not externi_zdroj.casopis_denik_nazev:
                    related_item["volume"] = externi_zdroj.sbornik_nazev
                elif externi_zdroj.casopis_denik_nazev and not externi_zdroj.sbornik_nazev:
                    related_item["volume"] = externi_zdroj.casopis_denik_nazev
                if externi_zdroj.casopis_rocnik and not externi_zdroj.datum_rd:
                    related_item["issue"] = externi_zdroj.casopis_rocnik
                elif not externi_zdroj.casopis_rocnik and externi_zdroj.datum_rd:
                    related_item["issue"] = self.format_date(externi_zdroj.datum_rd)
                if externi_zdroj.vydavatel and not externi_zdroj.organizace:
                    related_item["publisher"] = externi_zdroj.vydavatel
                elif not externi_zdroj.vydavatel and externi_zdroj.organizace:
                    related_item["publisher"] = externi_zdroj.organizace
                related_item["publicationYear"] = externi_zdroj.rok_vydani_vzniku
                if externi_zdroj.edice_rada:
                    related_item["edition"] = externi_zdroj.edice_rada
                related_item["contributors"] = [
                    serialize_ez_contributor(ea.editor) for ea in externi_zdroj.externizdrojeditor_set.all()
                ]
                related_items.append(related_item)
        return related_items

    def _serialize_subjects(self):
        serialized_subjects = super()._serialize_subjects()
        if self.record.druh:
            serialized_subjects += [serialize_subject(self.record.druh)]
        for dj in self.record.archeologicky_zaznam.dokumentacni_jednotky_akce.all():
            dj: DokumentacniJednotka
            for komp in dj.komponenty.komponenty.all():
                komp: Komponenta
                serialized_subjects += serialize_subjects_komponenty(komp)
        serialized_subjects = [dict(item) for item in set(serialized_subjects) if item]
        return serialized_subjects

    def _serialize_types(self):
        return {"resourceType": "archaeological site", "resourceTypeGeneral": "PhysicalObject"}

    def serialize_publish(self):
        publish = super().serialize_publish()
        publish["data"]["attributes"]["relatedItems"] = self._serialize_related_items()
        return publish

    def serialize_update(self):
        result = super().serialize_publish()
        result["data"]["attributes"].pop("event")
        result["data"]["attributes"]["relatedItems"] = self._serialize_related_items()
        return result
