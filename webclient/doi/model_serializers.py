from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List

from arch_z.models import AkceVedouci, ArcheologickyZaznam, ExterniOdkaz
from core.constants import ARCHIVACE_AZ, ARCHIVACE_SN, AZ_STAV_ARCHIVOVANY, D_STAV_ARCHIVOVANY, EZ_STAV_POTVRZENY
from dj.models import DokumentacniJednotka
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from dokument.models import Dokument, DokumentCast
from heslar.hesla_dynamicka import PRISTUPNOST_ANONYM_ID
from heslar.models import RuianKatastr
from komponenta.models import Komponenta
from lokalita.models import Lokalita
from pas.models import SamostatnyNalez
from uzivatel.models import Organizace, Osoba

AIS_AMCR = Organizace.objects.get(ident_cely="ORG-000091")


class ModelSerializer(ABC):
    DELETE_DESCRIPTION_CZ = (
        "Tento záznam byl odstraněn z repozitáře AMČR. V odůvodněných případech lze data na "
        "vyžádání získat od administrátora systému ze záložní kopie."
    )
    DELETE_DESCRIPTION_EN = (
        "This record has been removed from the AMCR repository. In justified cases, data can "
        "be retrieved from a backup copy by the system administrator on request."
    )

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

    def _get_prefix(self):
        return settings.DOI_PREFIX

    @abstractmethod
    def _get_soubory_queryset(self):
        pass

    @abstractmethod
    def _get_title(self, language: str):
        pass

    @abstractmethod
    def _serialize_alternate_identifiers(self):
        return [
            {
                "alternateIdentifierType": "Local accession number",
                "alternateIdentifier": self.get_ident_cely(),
            },
        ]

    @abstractmethod
    def _serialize_contributors(self):
        pass

    def _serialize_creators(self):
        return [serialize_osoba(author.autor, self.record.organizace) for author in self._get_creators()]

    def _serialize_dates(self):
        dates = []
        if self.record.historie:
            updated_dates = [
                {"date": self.format_date_time(date.datum_zmeny), "dateType": "Updated"}
                for date in self.record.historie.historie_set.all()
            ]
            dates.extend(updated_dates)
        return dates

    @abstractmethod
    def _serialize_descriptions(self):
        pass

    @abstractmethod
    def _serialize_geo_locations(self):
        pass

    def _serialize_related_identifiers(self):
        return [
            {
                "relationType": "HasMetadata",
                "relatedIdentifier": f"{settings.DIGI_LINKS['OAPI_link']}{self.get_ident_cely()}",
                "resourceTypeGeneral": "Dataset",
                "relatedIdentifierType": "URL",
            }
        ]

    @abstractmethod
    def _serialize_rights_list(self):
        pass

    def _serialize_subjects(self):
        return [
            frozenset(
                {
                    "subject": "History and Archaeology",
                    "valueUri": "http://dd.eionet.europa.eu/vocabulary/eurostat/fos07/FOS601",
                    "schemeUri": "http://dd.eionet.europa.eu/vocabulary/eurostat/fos07/",
                    "subjectScheme": "Field of science and technology classification (FOS 2007)",
                }.items()
            )
        ]

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
                            "lang": "cs",
                            "description": self.DELETE_DESCRIPTION_CZ,
                            "descriptionType": "TechnicalInfo",
                        },
                        {
                            "lang": "en",
                            "description": self.DELETE_DESCRIPTION_EN,
                            "descriptionType": "TechnicalInfo",
                        },
                    ],
                },
            }
        }

    def serialize_hide(self):
        return {"data": {"type": "dois", "attributes": {"event": "hide"}}}

    def serialize_publish(self):
        return {
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
                        "name": "Archaeological Information System of the Czech Republic",
                        "schemeUri": "https://ror.org/",
                        "publisherIdentifier": f"https://ror.org/{AIS_AMCR.ror}",
                        "publisherIdentifierScheme": "ROR",
                    },
                    "container": {
                        "type": "DataRepository",
                        "title": "Archaeological Map of the Czech Republic",
                        "identifier": "https://www.re3data.org/repository/r3d100013576",
                        "identifierType": "re3data",
                    },
                    "publicationYear": self._get_publication_year(),
                    "subjects": self._serialize_subjects(),
                    "contributors": self._serialize_contributors(),
                    "dates": self._serialize_dates(),
                    "language": self._get_language(),
                    "types": self._serialize_types(),
                    "relatedIdentifiers": self._serialize_related_identifiers(),
                    "sizes": [
                        f"{sum([soubor.size_mb for soubor in self._get_soubory_queryset().all()])} MB",
                        f"{sum([soubor.rozsah for soubor in self._get_soubory_queryset().all()])} pages",
                    ]
                    if self._get_soubory_queryset() and self._get_soubory_queryset().exists()
                    else [],
                    "formats": list(set([soubor.mimetype for soubor in self._get_soubory_queryset().all()]))
                    if self._get_soubory_queryset() and self._get_soubory_queryset().exists()
                    else [],
                    "version": self.format_date_time(self._get_historie_queryset().last().datum_zmeny),
                    "rightsList": self._serialize_rights_list(),
                    "descriptions": self._serialize_descriptions(),
                    "geoLocations": self._serialize_geo_locations(),
                    "url": f"{settings.DIGIARCHIV_URL or 'https://digiarchiv.aiscr.cz/id/'}{self.get_ident_cely()}",
                },
            }
        }

    def serialize_update(self):
        result = self.serialize_publish()
        result["data"]["attributes"].pop("event")
        return result


class PartialSerializer(ABC):
    def __init__(self, record):
        self.record = record

    def serialize_publish(self):
        pass


def format_katastr_place(katastr: RuianKatastr):
    return f"{katastr.nazev}, {katastr.okres.nazev}, {katastr.okres.kraj.nazev}, Czech Republic"


def serialize_creator_contributor(autor: Osoba) -> Dict[str, str]:
    return {
        "name": autor.vypis_cely,
        "givenName": autor.jmeno,
        "familyName": autor.prijmeni,
        "nameType": "Personal",
    }


def serialize_geom(geom=None, place: str | None = None) -> frozenset:
    serialized_geom = {}
    if geom:
        serialized_geom.update({"pointLatitude": geom.centroid.y, "pointLongitude": geom.centroid.x})
    if place:
        if isinstance(place, str):
            serialized_geom["geoLocationPlace"] = place
        if isinstance(place, RuianKatastr):
            serialized_geom["geoLocationPlace"] = format_katastr_place(place)
    return frozenset(serialized_geom.items())


def _serialize_komponenty_m2n_fields(komponenty):
    result = []
    for komp in komponenty:
        komp: Komponenta
        result += [serialize_subject(aktivita) for aktivita in komp.aktivity.all()]
        result += [serialize_subject(objekt.druh) for objekt in komp.objekty.all()]
        result += [serialize_subject(objekt.specifikace) for objekt in komp.objekty.all()]
        result += [serialize_subject(predmet.druh) for predmet in komp.predmety.all()]
        result += [serialize_subject(predmet.specifikace) for predmet in komp.predmety.all()]
    return result


def serialize_organizace(organizace: Organizace):
    serialized_organizace = {"name": organizace.nazev}
    if organizace.ror:
        serialized_organizace["affiliationIdentifier"] = f"https://ror.org/{organizace.ror}"
        serialized_organizace["affiliationIdentifierScheme"] = "ROR"
        serialized_organizace["schemeUri"] = "https://ror.org/"
    return serialized_organizace


def serialize_osoba(osoba: Osoba, organizace: Organizace | None = None, contributor_type: str | None = None) -> Dict:
    serialized_record = {
        "name": osoba.vypis_cely if not osoba.anonym else ":unkn",
        "nameType": "Personal",
        "givenName": osoba.jmeno if not osoba.anonym else " ",
        "familyName": osoba.prijmeni if not osoba.anonym else " ",
        "affiliation": [serialize_organizace(organizace)] if organizace and not organizace.general else [],
        "nameIdentifiers": [
            {
                "schemeUri": settings.DIGI_LINKS["OAPI_link"],
                "nameIdentifier": f"{settings.DIGI_LINKS['OAPI_link']}{osoba.ident_cely}",
                "nameIdentifierScheme": "AMCR Vocabulary",
            },
            *(
                [
                    {
                        "schemeUri": "https://orcid.org",
                        "nameIdentifier": f"https://orcid.org/{osoba.orcid}",
                        "nameIdentifierScheme": "ORCID",
                    }
                ]
                if osoba.orcid
                else []
            ),
            *(
                [
                    {
                        "schemeUri": "https://www.wikidata.org/wiki",
                        "nameIdentifier": f"https://www.wikidata.org/wiki/{osoba.wikidata}",
                        "nameIdentifierScheme": "ORCID",
                    }
                ]
                if osoba.wikidata
                else []
            ),
        ],
    }
    if contributor_type:
        serialized_record["contributorType"] = contributor_type
    return serialized_record


def serialize_subject(serialized_record, subject_attr="heslo_en"):
    if serialized_record is None:
        return frozenset()
    output = {
        "subject": getattr(serialized_record, subject_attr),
        "valueUri": f"{settings.DIGI_LINKS['OAPI_link']}{serialized_record.ident_cely}",
        "schemeUri": settings.DIGI_LINKS["OAPI_link"],
        "subjectScheme": "AMCR Vocabulary",
    }
    return frozenset(output.items())


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
        return self.record.jazyky.first().heslo_en

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
            alternate_identifiers.append(
                {
                    "alternateIdentifierType": "Original label",
                    "alternateIdentifier": self.record.oznaceni_originalu,
                }
            )
        return alternate_identifiers

    def _serialize_contributors(self):
        contributors = []
        if self.record.let and self.record.let.pozorovatel:
            contributors.append(
                serialize_osoba(self.record.let.pozorovatel, self.record.let.organizace, "ProjectLeader")
            )
        for cast in self.record.casti.all():
            cast: DokumentCast
            try:
                if cast.neident_akce and cast.neident_akce.vedouci:
                    for vedouci in cast.neident_akce.vedouci.all():
                        contributors.append(serialize_osoba(vedouci, contributor_type="ProjectLeader"))
            except ObjectDoesNotExist:
                pass
            if cast.archeologicky_zaznam:
                try:
                    if cast.archeologicky_zaznam.akce.hlavni_vedouci:
                        contributors.append(
                            serialize_osoba(
                                cast.archeologicky_zaznam.akce.hlavni_vedouci,
                                cast.archeologicky_zaznam.akce.organizace,
                                "ProjectLeader",
                            )
                        )
                    for akce_vedouci in cast.archeologicky_zaznam.akce.akcevedouci_set.all():
                        akce_vedouci: AkceVedouci
                        contributors.append(
                            serialize_osoba(akce_vedouci.vedouci, akce_vedouci.organizace, "ProjectMember")
                        )
                except ObjectDoesNotExist:
                    pass
            if cast.projekt and cast.projekt.vedouci_projektu:
                contributors.append(
                    serialize_osoba(cast.projekt.vedouci_projektu, cast.projekt.organizace, "ProjectLeader")
                )
        return contributors

    def _serialize_dates(self):
        dates = super()._serialize_dates()
        try:
            if self.record.extra_data and self.record.extra_data.datum_vzniku:
                dates.append({"date": self.record.extra_data.datum_vzniku, "dateType": "Created"})
        except ObjectDoesNotExist:
            pass
        return dates

    def _serialize_descriptions(self) -> List[Dict]:
        descriptions = []
        if self.record.popis:
            descriptions.append({"lang": "cs", "description": self.record.popis, "descriptionType": "Abstract"})
        if self.record.poznamka:
            descriptions.append({"lang": "cs", "description": self.record.poznamka, "descriptionType": "TechnicalInfo"})
        return descriptions

    def _serialize_geo_locations(self):
        geo_locations: List[frozenset] = []
        try:
            if self.record.extra_data.geom:
                geo_locations.append(serialize_geom(self.record.extra_data.geom))
        except ObjectDoesNotExist:
            pass
        for cast in self.record.casti.all():
            try:
                if cast.neident_akce and cast.neident_akce.katastr:
                    geo_locations.append(
                        serialize_geom(cast.neident_akce.katastr.definicni_bod, cast.neident_akce.katastr)
                    )
            except ObjectDoesNotExist:
                pass
            if cast.projekt and cast.projekt.hlavni_katastr and cast.projekt.pristupnost.pk == PRISTUPNOST_ANONYM_ID:
                geo_locations.append(
                    serialize_geom(cast.projekt.hlavni_katastr.definicni_bod, cast.projekt.hlavni_katastr)
                )
                geo_locations.append(serialize_geom(place=cast.projekt.hlavni_katastr))
                for katastr in cast.projekt.katastry.all():
                    if katastr.pk != cast.projekt.hlavni_katastr:
                        geo_locations.append(serialize_geom(katastr.definicni_bod, katastr))
                        geo_locations.append(serialize_geom(place=katastr))
            if (
                cast.archeologicky_zaznam
                and cast.archeologicky_zaznam.hlavni_katastr
                and cast.archeologicky_zaznam.pristupnost.pk == PRISTUPNOST_ANONYM_ID
                and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
            ):
                geo_locations.append(
                    serialize_geom(
                        cast.archeologicky_zaznam.hlavni_katastr.definicni_bod, cast.archeologicky_zaznam.hlavni_katastr
                    )
                )
                geo_locations.append(serialize_geom(place=cast.archeologicky_zaznam.hlavni_katastr))
                for katastr in cast.archeologicky_zaznam.katastry.all():
                    if katastr.pk != cast.archeologicky_zaznam.hlavni_katastr:
                        geo_locations.append(serialize_geom(katastr.definicni_bod, katastr))
                        geo_locations.append(serialize_geom(place=katastr))
        geo_locations_dict = [dict(item) for item in list(set(geo_locations))]
        return geo_locations_dict

    def _serialize_related_identifiers(self):
        related_identifiers = super()._serialize_related_identifiers()
        if self.record.soubory and self.record.soubory.soubory.exists():
            related_identifiers.append(
                {
                    "relationType": "HasPart",
                    "relatedIdentifier": f"{settings.DIGIARCHIV_SERVER_URL}id/{self.get_ident_cely()}",
                    "resourceTypeGeneral": "Dataset",
                    "relatedIdentifierType": "URL",
                }
            )
        if self.record.let:
            related_identifiers.append(
                {
                    "relationType": "IsDerivedFrom",
                    "relatedIdentifier": f"{settings.DIGIARCHIV_URL}{self.record.let.ident_cely}",
                    "resourceTypeGeneral": "Event",
                    "relatedIdentifierType": "URL",
                }
            )
        for cast in self.record.casti.all():
            cast: DokumentCast
            if cast.archeologicky_zaznam and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY:
                if cast.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
                    related_identifiers.append(
                        {
                            "relationType": "Documents",
                            "relatedIdentifier": f"{settings.DIGIARCHIV_URL}{cast.archeologicky_zaznam.ident_cely}",
                            "resourceTypeGeneral": "Event",
                            "relatedIdentifierType": "URL",
                        }
                    )
                elif cast.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA:
                    related_identifiers.append(
                        {
                            "relationType": "Documents",
                            "relatedIdentifier": f"{settings.DIGIARCHIV_URL}{cast.archeologicky_zaznam.lokalita.igsn}",
                            "resourceTypeGeneral": "PhysicalObject",
                            "relatedIdentifierType": "IGSN",
                        }
                    )
            elif cast.projekt:
                related_identifiers.append(
                    {
                        "relationType": "Documents",
                        "relatedIdentifier": f"{settings.DIGIARCHIV_URL}{cast.projekt.ident_cely}",
                        "resourceTypeGeneral": "Event",
                        "relatedIdentifierType": "URL",
                    }
                )
        return related_identifiers

    def _serialize_rights_list(self):
        if self.record.licence:
            serialized_rights = {"rights": self.record.licence.heslo_en}
            spdx_query = self.record.licence.heslar_odkaz.filter(zdroj="SPDX")
            if spdx_query.exists():
                serialized_rights["rightsUri"] = self.record.licence.heslar_odkaz.filter(zdroj="SPDX").first().uri
                serialized_rights["schemeUri"] = (
                    self.record.licence.heslar_odkaz.filter(zdroj="SPDX").first().scheme_uri
                )
                serialized_rights["rightsIdentifier"] = (
                    self.record.licence.heslar_odkaz.filter(zdroj="SPDX").first().kod
                )
                serialized_rights["rightsIdentifierScheme"] = (
                    self.record.licence.heslar_odkaz.filter(zdroj="SPDX").first().zdroj
                )
            return [
                serialized_rights,
            ]
        return []

    def _serialize_subjects(self):
        serialized_subjects = super()._serialize_subjects()
        serialized_subjects += [serialize_subject(posudek) for posudek in self.record.posudky.all()]
        serialized_subjects += [serialize_subject(osoba, "vypis_cely") for osoba in self.record.osoby.all()]
        if self.record.has_extra_data():
            serialized_subjects += [serialize_subject(self.record.extra_data.udalost_typ)]
        serialized_subjects += [serialize_subject(komp.obdobi) for komp in self.record.get_komponenty()]
        serialized_subjects += [serialize_subject(komp.areal) for komp in self.record.get_komponenty()]
        if self.record.get_komponenty(AZ_STAV_ARCHIVOVANY):
            serialized_subjects += _serialize_komponenty_m2n_fields(self.record.get_komponenty(AZ_STAV_ARCHIVOVANY))

        for cast in self.record.casti.all():
            try:
                if cast.archeologicky_zaznam and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY:
                    serialized_subjects.append(serialize_subject(cast.archeologicky_zaznam.akce.hlavni_typ))
                    serialized_subjects.append(serialize_subject(cast.archeologicky_zaznam.akce.vedlejsi_typ))
            except ObjectDoesNotExist:
                pass

            try:
                if cast.archeologicky_zaznam and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY:
                    serialized_subjects.append(serialize_subject(cast.archeologicky_zaznam.lokalita.typ_lokality))
                    serialized_subjects.append(serialize_subject(cast.archeologicky_zaznam.lokalita.druh))
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
            serialized_types["resourceType"] = resource_type_query.first().heslo_en
            serialized_types["resourceTypeGeneral"] = resource_type_query.first().kod
        else:
            serialized_types["resourceType"] = "Dataset"
            serialized_types["resourceTypeGeneral"] = "Dataset"
        return serialized_types

    def serialize_hide(self):
        return {
            "data": {
                "type": "dois",
                "attributes": {
                    "event": "hide",
                    "descriptions": self._serialize_descriptions()
                    + [
                        {
                            "lang": "cs",
                            "description": self.DELETE_DESCRIPTION_CZ,
                            "descriptionType": "TechnicalInfo",
                        },
                        {
                            "lang": "en",
                            "description": self.DELETE_DESCRIPTION_EN,
                            "descriptionType": "TechnicalInfo",
                        },
                    ],
                },
            }
        }


class SamostatnyNalezSerializer(ModelSerializer):
    def __init__(self, record: SamostatnyNalez):
        super().__init__(record)
        self.record: SamostatnyNalez

    def _get_creators(self):
        return [self.record.nalezce]

    def _get_historie_queryset(self):
        return self.record.historie.historie_set

    def get_ident_cely(self):
        return self.record.ident_cely

    def _get_soubory_queryset(self):
        if self.record.soubory:
            return self.record.soubory.soubory

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
            alternate_identifiers.append(
                {
                    "alternateIdentifierType": "Find inventory number",
                    "alternateIdentifier": self.record.evidencni_cislo,
                }
            )
        return alternate_identifiers

    def _serialize_contributors(self):
        return [serialize_osoba(self.record.projekt.vedouci_projektu, self.record.projekt.organizace, "ProjectLeader")]

    def _serialize_creators(self):
        return [serialize_osoba(author, self.record.projekt.organizace) for author in self._get_creators()]

    def _serialize_dates(self):
        dates = super()._serialize_dates()
        dates.append({"date": self.format_date(self.record.datum_nalezu), "dateType": "Collected"})
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

    def _serialize_geo_locations(self):
        geo_locations: List[frozenset] = []
        if self.record.pristupnost.pk == PRISTUPNOST_ANONYM_ID and self.record.geom:
            geo_locations.append(serialize_geom(self.record.geom))
        if self.record.pristupnost.pk == PRISTUPNOST_ANONYM_ID and self.record.katastr:
            geo_locations.append(serialize_geom(place=self.record.katastr))
        geo_locations_dict = [dict(item) for item in list(set(geo_locations))]
        return geo_locations_dict

    def _serialize_related_identifiers(self):
        related_identifiers = super()._serialize_related_identifiers()
        if self.record.soubory.soubory.exists():
            related_identifiers.append(
                {
                    "relationType": "IsDocumentedBy",
                    "relatedIdentifier": f"{settings.DIGIARCHIV_SERVER_URL}id/{self.get_ident_cely()}",
                    "resourceTypeGeneral": "Image",
                    "relatedIdentifierType": "URL",
                }
            )
        related_identifiers.append(
            {
                "relationType": "IsDerivedFrom",
                "relatedIdentifier": f"{settings.DIGIARCHIV_URL}{self.record.projekt.ident_cely}",
                "resourceTypeGeneral": "Event",
                "relatedIdentifierType": "URL",
            }
        )
        return related_identifiers

    def _serialize_rights_list(self):
        return [
            {
                "rights": "Creative Commons Attribution-NonCommercial 4.0 International",
                "rightsUri": "https://spdx.org/licenses/CC-BY-NC-4.0.html",
                "schemeUri": "https://spdx.org/licenses",
                "rightsIdentifier": "CC-BY-NC-4.0",
                "rightsIdentifierScheme": "SPDX",
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
        serialized_subjects = [dict(item) for item in set(serialized_subjects) if item]
        return serialized_subjects

    def _serialize_types(self):
        return {"resourceType": "archaeological find", "resourceTypeGeneral": "PhysicalObject"}


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

    def _serialize_contributors(self):
        contributors = []
        for eo in self.record.archeologicky_zaznam.externi_odkazy.all():
            eo: ExterniOdkaz
            contributors += [serialize_osoba(ed, contributor_type="Personal") for ed in eo.externi_zdroj.editori.all()]
        return contributors

    def _get_soubory_queryset(self):
        if self.record.archeologicky_zaznam.soubory:
            return self.record.archeologicky_zaznam.soubory.soubory

    def _serialize_dates(self):
        dates = []
        if self._get_soubory_queryset():
            updated_dates = [
                {"date": self.format_date_time(date.datum_zmeny), "dateType": "Updated"}
                for date in self._get_soubory_queryset()
            ]
            dates.extend(updated_dates)
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

    def _serialize_geo_locations(self):
        geo_locations: List[frozenset] = []
        if self.record.archeologicky_zaznam.pristupnost.pk == PRISTUPNOST_ANONYM_ID:
            dok_query = self.record.archeologicky_zaznam.dokumentacni_jednotky_akce
            if dok_query.exists():
                dok: DokumentacniJednotka = dok_query.first()
                if dok.pian and dok.pian.geom:
                    geo_locations.append(serialize_geom(dok.pian.geom, self.record.archeologicky_zaznam.hlavni_katastr))
        geo_locations_dict = [dict(item) for item in list(set(geo_locations))]
        return geo_locations_dict

    def _get_publication_year(self):
        archivace_history_queryset = self._get_historie_queryset().filter(typ_zmeny=ARCHIVACE_AZ)
        if archivace_history_queryset.exists():
            return archivace_history_queryset.first().datum_zmeny.year
        else:
            return datetime.now().year

    def _serialize_rights_list(self):
        return [
            {
                "rights": "Creative Commons Attribution-NonCommercial 4.0 International",
                "rightsUri": "https://spdx.org/licenses/CC-BY-NC-4.0.html",
                "schemeUri": "https://spdx.org/licenses",
                "rightsIdentifier": "CC-BY-NC-4.0",
                "rightsIdentifierScheme": "SPDX",
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
            alternate_identifiers.append(
                {
                    "alternateIdentifierType": "External identifier",
                    "alternateIdentifier": self.record.archeologicky_zaznam.uzivatelske_oznaceni,
                }
            )
        return alternate_identifiers

    def _serialize_creators(self):
        return [
            {
                "name": "AIS CR",
                "nameType": "Organizational",
                "nameIdentifiers": [
                    {
                        "affiliationIdentifier": f"https://ror.org/{AIS_AMCR.ident_cely}",
                        "affiliationIdentifierScheme": "ROR",
                        "schemeUri": "https://ror.org/",
                    }
                ],
            }
        ]

    def _serialize_related_identifiers(self):
        related_identifiers = super()._serialize_related_identifiers()
        casti_dokumentu_query = (
            self.record.archeologicky_zaznam.casti_dokumentu.filter(
                dokument__typ_dokumentu__heslar_odkaz__zdroj="DataCite"
            )
        ).filter(dokument__typ_dokumentu__heslar_odkaz__nazev_kodu="resourceTypeGeneral")
        for cast in casti_dokumentu_query:
            cast: DokumentCast
            if cast.dokument.stav == D_STAV_ARCHIVOVANY:
                related_identifiers.append(
                    {
                        "relationType": "IsDocumentedBy",
                        "relatedIdentifier": cast.dokument.doi,
                        "resourceTypeGeneral": cast.dokument.typ_dokumentu.heslar_odkaz.kod,
                        "relatedIdentifierType": "DOI",
                    }
                )
        for externi_odkaz in self._get_externi_odkaz_query():
            externi_odkaz: ExterniOdkaz
            if externi_odkaz.externi_zdroj.doi:
                related_identifiers.append(
                    {
                        "relationType": "IsPublishedIn",
                        "relatedIdentifier": externi_odkaz.externi_zdroj.doi,
                        "resourceTypeGeneral": externi_odkaz.externi_zdroj.typ.heslar_odkaz.kod,
                        "relatedIdentifierType": "DOI",
                    }
                )
                related_identifiers.append(
                    {
                        "relationType": "IsPublishedIn",
                        "relatedIdentifier": f"{settings.DIGIARCHIV_URL}{externi_odkaz.externi_zdroj.ident_cely}",
                        "resourceTypeGeneral": externi_odkaz.externi_zdroj.typ.heslar_odkaz.kod,
                        "relatedIdentifierType": "URL",
                    }
                )
        return related_identifiers

    def _serialize_related_items(self):
        related_items = []
        for externi_odkaz in self._get_externi_odkaz_query():
            externi_odkaz: ExterniOdkaz
            externi_zdroj = externi_odkaz.externi_zdroj
            if externi_zdroj.stav == EZ_STAV_POTVRZENY:
                related_item = {
                    "relatedItemType": externi_zdroj.typ.heslar_odkaz.kod,
                    "relationType": "IsPublishedIn",
                    "relatedItemIdentifier": {
                        "relatedItemIdentifier": externi_zdroj.doi or externi_zdroj.ident_cely,
                        "relatedItemIdentifierType": "DOI",
                    },
                    "creators": [
                        serialize_creator_contributor(ea.autor) for ea in externi_zdroj.externizdrojautor_set.all()
                    ],
                    "titles": externi_zdroj.nazev,
                }
                if externi_zdroj.sbornik_nazev and not externi_zdroj.casopis_denik_nazev:
                    related_item["volume"] = externi_zdroj.sbornik_nazev
                elif externi_zdroj.casopis_denik_nazev and not externi_zdroj.sbornik_nazev:
                    related_item["volume"] = externi_zdroj.casopis_denik_nazev
                if externi_zdroj.casopis_rocnik and not externi_zdroj.datum_rd:
                    related_item["issue"] = externi_zdroj.casopis_rocnik
                elif not externi_zdroj.casopis_rocnik and externi_zdroj.datum_rd:
                    related_item["issue"] = externi_zdroj.datum_rd
                if externi_zdroj.vydavatel and not externi_zdroj.organizace:
                    related_item["publisher"] = externi_zdroj.vydavatel
                elif not externi_zdroj.vydavatel and externi_zdroj.organizace:
                    related_item["publisher"] = externi_zdroj.organizace
                related_item["publicationYear"] = externi_zdroj.rok_vydani_vzniku
                related_item["edition"] = externi_zdroj.edice_rada
                related_item["contributors"] = (
                    [serialize_creator_contributor(ea.editor) for ea in externi_zdroj.externizdrojeditor_set.all()],
                )
                related_items.append(related_item)
        return related_items

    def _serialize_subjects(self):
        serialized_subjects = super()._serialize_subjects()
        try:
            if self.record.archeologicky_zaznam and self.record.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY:
                serialized_subjects.append(serialize_subject(self.record.archeologicky_zaznam.lokalita.druh))
        except ObjectDoesNotExist:
            pass
        serialized_komponenta_data = []
        serialized_komponenta_data += [
            [serialize_subject(komp.obdobi) for komp in dj.komponenty.komponenty.all()]
            for dj in self.record.archeologicky_zaznam.dokumentacni_jednotky_akce.all()
        ]
        serialized_komponenta_data += [
            [serialize_subject(komp.areal) for komp in dj.komponenty.komponenty.all()]
            for dj in self.record.archeologicky_zaznam.dokumentacni_jednotky_akce.all()
        ]
        serialized_komponenta_data += [
            _serialize_komponenty_m2n_fields(dj.komponenty.komponenty.all())
            for dj in self.record.archeologicky_zaznam.dokumentacni_jednotky_akce.all()
        ]
        serialized_subjects = [dict(item) for item in set(serialized_subjects) if item]
        return serialized_subjects

    def _serialize_types(self):
        return {"resourceType": "archaeological site", "resourceTypeGeneral": "PhysicalObject"}

    def serialize_publish(self):
        publish = super().serialize_publish()
        publish["data"]["attributes"]["relatedItems"] = self._serialize_related_items()
        return publish
