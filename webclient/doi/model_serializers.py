from abc import ABC, abstractmethod
from typing import Dict, List

from arch_z.models import AkceVedouci, ArcheologickyZaznam, ExterniOdkaz
from core.constants import ARCHIVACE_AZ, ARCHIVACE_SN, AZ_STAV_ARCHIVOVANY, D_STAV_ARCHIVOVANY, EZ_STAV_POTVRZENY
from dj.models import DokumentacniJednotka
from django.core.exceptions import ObjectDoesNotExist
from dokument.models import Dokument, DokumentCast
from heslar.hesla_dynamicka import PRISTUPNOST_ANONYM_ID
from heslar.models import RuianKatastr
from komponenta.models import Komponenta
from lokalita.models import Lokalita
from pas.models import SamostatnyNalez
from uzivatel.models import Organizace, Osoba

from webclient.settings.base import DIGIARCHIV_URL

AIS_AMCR = Organizace.objects.get(ident_cely="ORG-000091")


class ModelSerializer(ABC):
    def __init__(self, object):
        self.object = object

    @abstractmethod
    def _get_creators(self):
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
    def _get_title(self, language: str):
        pass

    @abstractmethod
    def _serialize_alternate_identifiers(self):
        return [
            {
                "alternateIdentifierType": "Local accession number",
                "alternateIdentifier": self.object.ident_cely,
            },
        ]

    @abstractmethod
    def _serialize_contributors(self):
        pass

    def _serialize_creators(self):
        return [serialize_osoba(author.autor, self.object.organizace) for author in self._get_creators()]

    @abstractmethod
    def _serialize_dates(self):
        dates = []
        if self.object.historie:
            updated_dates = [
                {"date": date.datum_zmeny, "dateType": "Updated"} for date in self.object.historie.historie_set.all()
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
                "relatedIdentifier": "<OAPI_link><ident_cely>",
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

    def serialize_publish(self):
        return {
            "data": {
                "type": "dois",
                "attributes": {
                    "event": "publish",
                    "doi": f"{self._get_prefix()}/{self.object.ident_cely}",
                    "alternateIdentifiers": self._serialize_alternate_identifiers(),
                },
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
                    "publisherIdentifier": f"https://ror.org/{AIS_AMCR.ror}",  # doplnit
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
                    f"{sum([soubor.size_mb for soubor in self.object.soubory.soubory.all()])} MB",
                    f"{sum([soubor.rozsah for soubor in self.object.soubory.soubory.all()])} pages",
                ]
                if self.object.soubory.soubory.exists()
                else [],
                "formats": set([soubor.mimetype for soubor in self.object.soubory.soubory.all()])
                if self.object.soubory.soubory.exists()
                else [],
                "version": self.object.historie.historie_set.last().datum_zmeny,
                "rightsList": self._serialize_rights_list(),
                "descriptions": self._serialize_descriptions(),
                "geoLocations": self._serialize_geo_locations(),
                "url": "",
            }
        }


class PartialSerializer(ABC):
    def __init__(self, object):
        self.object = object

    def serialize_publish(self):
        pass


def format_katastr_place(katastr: RuianKatastr):
    return f"{katastr.nazev}, {katastr.okres.nazev}, {katastr.okres.kraj.nazev}, Czech Republic"


def serialize_creator_contributor(autor: Osoba):
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


def serialize_osoba(osoba: Osoba, organizace: Organizace | None = None) -> Dict:
    serialized_object = {
        "name": osoba.vypis_cely if not osoba.anonym else ":unkn",
        "nameType": "Personal",
        "givenName": osoba.jmeno if not osoba.anonym else " ",
        "familyName": osoba.prijmeni if not osoba.anonym else " ",
        "affiliation": [serialize_organizace(organizace)] if organizace and not organizace.general else [],
        "nameIdentifiers": [
            {
                "schemeUri": "<OAPI_link>",
                "nameIdentifier": "<OAPI_link><dokumentautor_set.autor.ident_cely>",
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
    return serialized_object


def serialize_subject(serialized_object, subject_attr="heslo_en"):
    if serialized_object is None:
        return frozenset()
    output = {
        "subject": getattr(serialized_object, subject_attr),
        "valueUri": f"<OAPI_link>{serialized_object.ident_cely}",
        "schemeUri": "<OAPI_link>",
        "subjectScheme": "AMCR Vocabulary",
    }
    return frozenset(output.items())


class DokumentSerializer(ModelSerializer):
    def __init__(self, object: Dokument):
        super().__init__(object)
        self.object: Dokument

    def _get_creators(self):
        return self.object.dokumentautor_set.all()

    def _get_language(self):
        return self.object.jazyky.first()

    def _get_publication_year(self):
        return self.object.rok_vzniku

    def _get_prefix(self):
        return ""

    def _get_title(self, language: str):
        return {
            "en": f"AMCR {self.object.ident_cely} – {self.object.typ_dokumentu.heslo_en}",
            "cs": f"AMCR {self.object.ident_cely} – {self.object.typ_dokumentu.heslo}",
        }[language]

    def _serialize_alternate_identifiers(self):
        alternate_identifiers = super()._serialize_alternate_identifiers()
        if self.object.oznaceni_originalu:
            alternate_identifiers.append(
                {
                    "alternateIdentifierType": "Original label",
                    "alternateIdentifier": self.object.oznaceni_originalu,
                }
            )
        return alternate_identifiers

    def _serialize_contributors(self):
        contributors = []
        if self.object.let and self.object.let.pozorovatel:
            contributors.append(serialize_osoba(self.object.let.pozorovatel, self.object.let.organizace))
        for cast in self.object.casti.all():
            cast: DokumentCast
            try:
                if cast.neident_akce and cast.neident_akce.vedouci:
                    for vedouci in cast.neident_akce.vedouci.all():
                        contributors.append(serialize_osoba(vedouci))
            except ObjectDoesNotExist:
                pass
            if cast.archeologicky_zaznam:
                try:
                    if cast.archeologicky_zaznam.akce.hlavni_vedouci:
                        contributors.append(
                            serialize_osoba(
                                cast.archeologicky_zaznam.akce.hlavni_vedouci, cast.archeologicky_zaznam.akce.organizace
                            )
                        )
                    for akce_vedouci in cast.archeologicky_zaznam.akce.akcevedouci_set.all():
                        akce_vedouci: AkceVedouci
                        contributors.append(serialize_osoba(akce_vedouci.vedouci, akce_vedouci.organizace))
                except ObjectDoesNotExist:
                    pass
            if cast.projekt and cast.projekt.vedouci_projektu:
                contributors.append(serialize_osoba(cast.projekt.vedouci_projektu, cast.projekt.organizace))
        return contributors

    def _serialize_dates(self):
        dates = super()._serialize_dates()
        try:
            if self.object.extra_data and self.object.extra_data.datum_vzniku:
                dates.append({"date": self.object.extra_data.datum_vzniku, "dateType": "Created"})
        except ObjectDoesNotExist:
            pass
        return dates

    def _serialize_descriptions(self):
        descriptions = []
        if self.object.popis:
            descriptions.append({"lang": "cs", "description": self.object.popis, "descriptionType": "Abstract"})
        if self.object.poznamka:
            descriptions.append({"lang": "cs", "description": self.object.poznamka, "descriptionType": "TechnicalInfo"})
        return descriptions

    def _serialize_geo_locations(self):
        geo_locations: List[frozenset] = []
        try:
            if self.object.extra_data.geom:
                geo_locations.append(serialize_geom(self.object.extra_data.geom))
        except ObjectDoesNotExist:
            pass
        for cast in self.object.casti.all():
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
        if self.object.soubory.soubory.exists():
            related_identifiers.append(
                {
                    "relationType": "HasPart",
                    "relatedIdentifier": "<soubory.url>",
                    "resourceTypeGeneral": "Dataset",
                    "relatedIdentifierType": "URL",
                }
            )
        if self.object.let:
            related_identifiers.append(
                {
                    "relationType": "IsDerivedFrom",
                    "relatedIdentifier": f"{DIGIARCHIV_URL}{self.object.let.ident_cely}",
                    "resourceTypeGeneral": "Event",
                    "relatedIdentifierType": "URL",
                }
            )
        for cast in self.object.casti.all():
            cast: DokumentCast
            if cast.archeologicky_zaznam and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY:
                if cast.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
                    related_identifiers.append(
                        {
                            "relationType": "Documents",
                            "relatedIdentifier": f"{DIGIARCHIV_URL}{cast.archeologicky_zaznam.ident_cely}",
                            "resourceTypeGeneral": "Event",
                            "relatedIdentifierType": "URL",
                        }
                    )
                elif cast.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA:
                    related_identifiers.append(
                        {
                            "relationType": "Documents",
                            "relatedIdentifier": f"{DIGIARCHIV_URL}{cast.archeologicky_zaznam.lokalita.igsn}",
                            "resourceTypeGeneral": "PhysicalObject",
                            "relatedIdentifierType": "IGSN",
                        }
                    )
            elif cast.projekt:
                related_identifiers.append(
                    {
                        "relationType": "Documents",
                        "relatedIdentifier": f"{DIGIARCHIV_URL}{cast.projekt.ident_cely}",
                        "resourceTypeGeneral": "Event",
                        "relatedIdentifierType": "URL",
                    }
                )
        return related_identifiers

    def _serialize_rights_list(self):
        if self.object.licence:
            serialized_rights = {"rights": self.object.licence.heslo_en}
            spdx_query = self.object.licence.heslar_odkaz.filter(zdroj="SPDX")
            if spdx_query.exists():
                serialized_rights["rightsUri"] = self.object.licence.heslar_odkaz.filter(zdroj="SPDX").first().uri
                serialized_rights["schemeUri"] = (
                    self.object.licence.heslar_odkaz.filter(zdroj="SPDX").first().scheme_uri
                )
                serialized_rights["rightsIdentifier"] = (
                    self.object.licence.heslar_odkaz.filter(zdroj="SPDX").first().kod
                )
                serialized_rights["rightsIdentifierScheme"] = (
                    self.object.licence.heslar_odkaz.filter(zdroj="SPDX").first().zdroj
                )
            return [
                serialized_rights,
            ]
        return []

    def _serialize_subjects(self):
        serialized_subjects = super()._serialize_subjects()
        serialized_subjects += [serialize_subject(posudek) for posudek in self.object.posudky.all()]
        serialized_subjects += [serialize_subject(osoba, "vypis_cely") for osoba in self.object.osoby.all()]
        if self.object.has_extra_data():
            serialized_subjects += [serialize_subject(self.object.extra_data.udalost_typ)]
        serialized_subjects += [serialize_subject(komp.obdobi) for komp in self.object.get_komponenty()]
        serialized_subjects += [serialize_subject(komp.areal) for komp in self.object.get_komponenty()]
        serialized_subjects += _serialize_komponenty_m2n_fields(self.object.get_komponenty(AZ_STAV_ARCHIVOVANY))

        for cast in self.object.casti.all():
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
        serialized_subjects = [dict(item) for item in set(serialized_subjects)]
        return serialized_subjects

    def _serialize_types(self):
        serialized_types = {"resourceType": self.object.typ_dokumentu.heslo_en}
        resource_type_query = self.object.typ_dokumentu.heslar_odkaz.filter(zdroj="DataCite").filter(
            nazev_kodu="resourceTypeGeneral"
        )
        if resource_type_query.exists():
            serialized_types["resourceTypeGeneral"] = resource_type_query.first().kod
        return serialized_types


class SamostatnyNalezSerializer(ModelSerializer):
    def __init__(self, object: SamostatnyNalez):
        super().__init__(object)
        self.object: SamostatnyNalez

    def _get_creators(self):
        return [self.object.nalezce]

    def _get_prefix(self):
        return ""

    def _get_publication_year(self):
        return self.object.historie.historie_set.filter(typ_zmeny=ARCHIVACE_SN).first().datum_zmeny.year

    def _get_title(self, language: str):
        return {
            "en": f"AMCR {self.object.ident_cely} – {self.object.druh_nalezu.heslo_en} ({self.object.specifikace.heslo_en}), {self.object.obdobi.heslo_en}",
            "cs": f"AMCR {self.object.ident_cely} – {self.object.druh_nalezu.heslo} ({self.object.specifikace.heslo}), {self.object.obdobi.heslo}",
        }[language]

    def _serialize_alternate_identifiers(self):
        alternate_identifiers = super()._serialize_alternate_identifiers()
        if self.object.oznaceni_originalu:
            alternate_identifiers.append(
                {
                    "alternateIdentifierType": "Find inventory number",
                    "alternateIdentifier": self.object.evidencni_cislo,
                }
            )
        return alternate_identifiers

    def _serialize_contributors(self):
        contributors = [serialize_osoba(self.object.let.pozorovatel, self.object.projekt.vedouci_projektu)]
        if self.object.organizace and not self.object.organizace.general:
            contributors.append(serialize_organizace(self.object.organizace))
        return contributors

    def _serialize_dates(self):
        dates = super()._serialize_dates()
        dates.append({"date": self.object.datum_nalezu, "dateType": "Collected"})
        return dates

    def _serialize_descriptions(self):
        descriptions = [{"lang": "en", "description": "Collected by field survey.", "descriptionType": "Methods"}]
        if self.object.poznamka:
            descriptions.append({"lang": "cs", "description": self.object.poznamka, "descriptionType": "Abstract"})
        if self.object.okolnosti:
            descriptions.append(
                {
                    "lang": "cs",
                    "description": f"Finding context: {self.object.okolnosti.heslo_en}",
                    "descriptionType": "Abstract",
                }
            )
        if self.object.okolnosti:
            descriptions.append(
                {"lang": "cs", "description": f"Finding depth: {self.object.hloubka} cm", "descriptionType": "Abstract"}
            )
        if self.object.pocet:
            descriptions.append(
                {"lang": "cs", "description": f"Number of finds: {self.object.pocet}", "descriptionType": "Abstract"}
            )
        return descriptions

    def _serialize_geo_locations(self):
        geo_locations: List[frozenset] = []
        if self.object.pristupnost.pk == PRISTUPNOST_ANONYM_ID and self.object.geom:
            geo_locations.append(serialize_geom(self.object.geom))
        if self.object.pristupnost.pk == PRISTUPNOST_ANONYM_ID and self.object.katastr:
            geo_locations.append(serialize_geom(place=self.object.katastr))
        return geo_locations

    def _serialize_related_identifiers(self):
        related_identifiers = super()._serialize_related_identifiers()
        if self.object.soubory.soubory.exists():
            related_identifiers.append(
                {
                    "relationType": "IsDocumentedBy",
                    "relatedIdentifier": "<soubory.url>",
                    "resourceTypeGeneral": "Image",
                    "relatedIdentifierType": "URL",
                }
            )
        related_identifiers.append(
            {
                "relationType": "IsDerivedFrom",
                "relatedIdentifier": f"{DIGIARCHIV_URL}{self.object.projekt.ident_cely}",
                "resourceTypeGeneral": "Event",
                "relatedIdentifierType": "URL",
            }
        )

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
        serialized_subjects += [serialize_subject(posudek) for posudek in self.object.obdobi]
        serialized_subjects += [serialize_subject(posudek) for posudek in self.object.druh_nalezu]
        serialized_subjects += [serialize_subject(posudek) for posudek in self.object.specifikace]
        return serialized_subjects

    def _serialize_types(self):
        return {"resourceType": "archaeological find", "resourceTypeGeneral": "PhysicalObject"}


class LokalitaSerializer(ModelSerializer):
    def __init__(self, object: Lokalita):
        super().__init__(object)
        self.object: Lokalita

    def _get_creators(self):
        pass

    def _serialize_contributors(self):
        pass

    def _serialize_dates(self):
        pass

    def _serialize_descriptions(self):
        descriptions = [
            {
                "lang": "en",
                "description": "Authoritative summary record of archaeological finds and observations corresponding to a specific site with characteristic archaeological manifestation and presumed past functional context.",
                "descriptionType": "Methods",
            }
        ]
        if self.object.popis and self.object.pristupnost.pk == PRISTUPNOST_ANONYM_ID:
            descriptions.append({"lang": "cs", "description": self.object.popis, "descriptionType": "Abstract"})
        if self.object.zachovalost:
            descriptions.append(
                {
                    "lang": "cs",
                    "description": f"State of preservation: {self.object.zachovalost.heslo_en}",
                    "descriptionType": "Abstract",
                }
            )
        if self.object.jistota:
            descriptions.append(
                {
                    "lang": "cs",
                    "description": f"Level of confidence: {self.object.jistota.heslo_en}",
                    "descriptionType": "Abstract",
                }
            )
        if self.object.poznamka:
            descriptions.append(
                {"lang": "cs", "description": {self.object.poznamka}, "descriptionType": "TechnicalInfo"}
            )
        return descriptions

    def _get_externi_odkaz_query(self):
        return self.object.archeologicky_zaznam.externi_odkazy.filter(
            externi_zdroj__typ__heslar_odkaz__zdroj="DataCite"
        ).filter(externi_zdroj__typ_heslar_odkaz__nazev_kodu="resourceTypeGeneral")

    def _serialize_geo_locations(self):
        geo_locations: List[frozenset] = []
        if self.object.pristupnost.pk == PRISTUPNOST_ANONYM_ID:
            dok_query = self.object.archeologicky_zaznam.dokumentacni_jednotky_akce
            if dok_query.exists():
                dok: DokumentacniJednotka = dok_query.first()
                geo_locations.append(serialize_geom(dok.pian, self.object.katastr))
        geo_locations_dict = [dict(item) for item in list(set(geo_locations))]
        return geo_locations_dict

    def _get_prefix(self):
        return ""

    def _get_publication_year(self):
        return self.object.historie.historie_set.filter(typ_zmeny=ARCHIVACE_AZ).first().datum_zmeny.year

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
            "en": f"AMCR {self.object.ident_cely} – {self.object.druh.heslo_en} {self.object.nazev * self.object.pristupnost.pk == PRISTUPNOST_ANONYM_ID}",
            "cs": f"AMCR {self.object.ident_cely} – {self.object.druh.heslo} {self.object.nazev * self.object.pristupnost.pk == PRISTUPNOST_ANONYM_ID}",
        }[language]

    def _serialize_alternate_identifiers(self):
        alternate_identifiers = super()._serialize_alternate_identifiers()
        if self.object.uzivatelske_oznaceni:
            alternate_identifiers.append(
                {
                    "alternateIdentifierType": "External identifier",
                    "alternateIdentifier": self.object.uzivatelske_oznaceni,
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
            self.object.archeologicky_zaznam.casti_dokumentu.filter(
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
                        "relatedIdentifier": f"{DIGIARCHIV_URL}{externi_odkaz.externi_zdroj.ident_cely}",
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
                    "creators": (
                        serialize_creator_contributor(ea.autor) for ea in externi_zdroj.externizdrojautor_set.all()
                    ),
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
                    (serialize_creator_contributor(ea.editor) for ea in externi_zdroj.externizdrojeditor_set.all()),
                )
                related_items.append(related_item)
        return related_items

    def _serialize_subjects(self):
        serialized_subjects = super()._serialize_subjects()
        try:
            if self.object.archeologicky_zaznam and self.object.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY:
                serialized_subjects.append(serialize_subject(self.object.archeologicky_zaznam.lokalita.druh))
        except ObjectDoesNotExist:
            pass
        serialized_subjects += [serialize_subject(komp.obdobi) for komp in self.object.get_komponenty()]
        serialized_subjects += [serialize_subject(komp.areal) for komp in self.object.get_komponenty()]
        serialized_subjects += _serialize_komponenty_m2n_fields(self.object.get_komponenty(AZ_STAV_ARCHIVOVANY))
        return serialized_subjects

    def _serialize_types(self):
        return {"resourceType": "archaeological site", "resourceTypeGeneral": "PhysicalObject"}

    def serialize_publish(self):
        publish = super().serialize_publish()
        publish["data"]["attributes"]["relatedItems"] = self._serialize_related_items()
