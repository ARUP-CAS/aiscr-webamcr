from abc import ABC, abstractmethod
from typing import Dict, List

from core.constants import AZ_STAV_ARCHIVOVANY
from django.core.exceptions import ObjectDoesNotExist
from dokument.models import Dokument, DokumentCast
from heslar.hesla_dynamicka import PRISTUPNOST_ANONYM_ID
from heslar.models import RuianKatastr
from komponenta.models import Komponenta
from uzivatel.models import Organizace, Osoba


class ModelSerializer(ABC):
    def __init__(self, object):
        self.object = object

    @abstractmethod
    def serialize_publish(self):
        pass


class PartialSerializer(ABC):
    def __init__(self, object):
        self.object = object

    def serialize_publish(self):
        pass


def format_katastr_place(katastr: RuianKatastr):
    return f"{katastr.nazev}, {katastr.okres.nazev}, {katastr.okres.kraj.nazev}, Czech Republic"


def serialize_geom(geom=None, place: str | None = None) -> frozenset:
    serialized_geom = {}
    if geom:
        serialized_geom.update({"pointLatitude": geom.Y, "pointLongitude": geom.X})
    if place:
        if isinstance(place, str):
            serialized_geom["geoLocationPlace"] = place
        if isinstance(place, RuianKatastr):
            serialized_geom["geoLocationPlace"] = format_katastr_place(place)
    return frozenset(serialized_geom.items())


def serialize_organizace(organizace: Organizace):
    serialized_organizace = {"name": organizace.nazev}
    if organizace.ror:
        serialized_organizace["affiliationIdentifier"] = f"https://ror.org/{organizace.ro}"
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

    def _serialize_contributors(self):
        contributors = []
        if self.object.let and self.object.let.pozorovatel:
            contributors.append(serialize_osoba(self.object.let.pozorovatel, self.object.let.organizace))
        for cast in self.object.casti.all():
            cast: DokumentCast
            try:
                if cast.neident_akce and cast.neident_akce.vedouci:
                    contributors.append(serialize_osoba(cast.neident_akce.vedouci))
            except ObjectDoesNotExist:
                pass
            if cast.archeologicky_zaznam.akce and cast.archeologicky_zaznam.akce.hlavni_vedouci:
                contributors.append(
                    serialize_osoba(
                        cast.archeologicky_zaznam.akce.hlavni_vedouci, cast.archeologicky_zaznam.akce.organizace
                    )
                )
            if cast.projekt and cast.projekt.vedouci_projektu:
                contributors.append(serialize_osoba(cast.projekt.vedouci_projektu, cast.projekt.organizace))
            for vedouci in cast.archeologicky_zaznam.akce.akcevedouci_set.all():
                contributors.append(serialize_osoba(vedouci, cast.archeologicky_zaznam.akce.organizace))
        return contributors

    def _serialize_dates(self):
        dates = []
        if self.object.extra_data and self.object.extra_data.datum_vzniku:
            dates.append({"date": self.object.extra_data.datum_vzniku, "dateType": "Created"})
        if self.object.historie:
            updated_dates = [
                {"date": date.datum_zmeny, "dateType": "Updated"} for date in self.object.historie.historie_set.all()
            ]
            dates.extend(updated_dates)
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
        if self.object.extra_data.geom:
            geo_locations.append(serialize_geom(self.object.extra_data.geom))
        for cast in self.object.casti.all():
            if cast.neident_akce and cast.neident_akce.katastr:
                geo_locations.append(serialize_geom(cast.neident_akce.katastr.definicni_bod, cast.neident_akce.katastr))
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

    def _serialize_subjects(self):
        first_item = frozenset(
            {
                "subject": "History and Archaeology",
                "valueUri": "http://dd.eionet.europa.eu/vocabulary/eurostat/fos07/FOS601",
                "schemeUri": "http://dd.eionet.europa.eu/vocabulary/eurostat/fos07/",
                "subjectScheme": "Field of science and technology classification (FOS 2007)",
            }.items()
        )
        serialized_subjects = [
            first_item,
        ]
        serialized_subjects += [serialize_subject(posudek) for posudek in self.object.posudky.all()]
        serialized_subjects += [serialize_subject(osoba, "vypis_cely") for osoba in self.object.osoby.all()]
        if self.object.has_extra_data():
            serialized_subjects += [serialize_subject(self.object.extra_data.udalost_typ)]
        serialized_subjects += [serialize_subject(komp.obdobi) for komp in self.object.get_komponenty()]
        serialized_subjects += [serialize_subject(komp.areal) for komp in self.object.get_komponenty()]
        for komp in self.object.get_komponenty(AZ_STAV_ARCHIVOVANY):
            komp: Komponenta
            serialized_subjects += [serialize_subject(aktivita) for aktivita in komp.aktivity.all()]
            serialized_subjects += [serialize_subject(objekt.druh) for objekt in komp.objekty.all()]
            serialized_subjects += [serialize_subject(objekt.specifikace) for objekt in komp.objekty.all()]
            serialized_subjects += [serialize_subject(predmet.druh) for predmet in komp.predmety.all()]
            serialized_subjects += [serialize_subject(predmet.specifikace) for predmet in komp.predmety.all()]
        serialized_subjects += [
            serialize_subject(cast.archeologicky_zaznam.akce.hlavni_typ)
            for cast in self.object.casti.all()
            if cast.archeologicky_zaznam and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
        ]
        serialized_subjects += [
            serialize_subject(cast.archeologicky_zaznam.akce.hlavni_typ)
            for cast in self.object.casti.all()
            if cast.archeologicky_zaznam and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
        ]
        serialized_subjects += [
            serialize_subject(cast.archeologicky_zaznam.akce.vedlejsi_typ)
            for cast in self.object.casti.all()
            if cast.archeologicky_zaznam and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
        ]
        try:
            serialized_subjects += [
                serialize_subject(cast.archeologicky_zaznam.lokalita.typ_lokality)
                for cast in self.object.casti.all()
                if cast.archeologicky_zaznam
                and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
                and cast.archeologicky_zaznam.lokalita
            ]
        except ObjectDoesNotExist:
            pass
        try:
            serialized_subjects += [
                serialize_subject(cast.archeologicky_zaznam.lokalita.druh)
                for cast in self.object.casti.all()
                if cast.archeologicky_zaznam
                and cast.archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
                and cast.archeologicky_zaznam.lokalita
            ]
        except ObjectDoesNotExist:
            pass
        serialized_subjects = [dict(item) for item in set(serialized_subjects)]
        return serialized_subjects

    def serialize_publish(self):
        return {
            "data": {
                "type": "dois",
                "attributes": {
                    "event": "publish",
                    "alternateIdentifiers": [
                        {
                            "alternateIdentifierType": "Local accession number",
                            "alternateIdentifier": self.object.ident_cely,
                        },
                        *(
                            [
                                {
                                    "alternateIdentifierType": "Original label",
                                    "alternateIdentifier": self.object.oznaceni_originalu,
                                }
                            ]
                            if self.object.oznaceni_originalu
                            else []
                        ),
                    ],
                },
                "creators": [
                    serialize_osoba(author.autor, self.object.organizace)
                    for author in self.object.dokumentautor_set.all()
                ],
                "titles": [
                    {
                        "lang": "en",
                        "title": f"AMCR {self.object.ident_cely} – {self.object.typ_dokumentu.heslo_en}",
                    },
                    {
                        "lang": "cs",
                        "title": f"AMCR {self.object.ident_cely} – {self.object.typ_dokumentu.heslo}",
                        "titleType": "TranslatedTitle",
                    },
                ],
                "publisher": {
                    "lang": "en",
                    "name": "Archaeological Information System of the Czech Republic",
                    "schemeUri": "https://ror.org/",
                    "publisherIdentifier": "https://ror.org/xxx",  # doplnit
                    "publisherIdentifierScheme": "ROR",
                },
                "container": {
                    "type": "DataRepository",
                    "title": "Archaeological Map of the Czech Republic",
                    "identifier": "https://www.re3data.org/repository/r3d100013576",
                    "identifierType": "re3data",
                },
                "publicationYear": self.object.rok_vzniku,
                "subjects": self._serialize_subjects(),
                "contributors": self._serialize_contributors(),
                "dates": self._serialize_dates(),
                "language": self.object.jazyky.first(),
                "types": {
                    "resourceType": self.object.typ_dokumentu.heslo_en,
                    "resourceTypeGeneral": self.object.typ_dokumentu.heslar_odkaz.filter(zdroj="DataCite")
                    .filter(nazev_kodu="resourceTypeGeneral")
                    .first()
                    .kod,
                },
                "relatedIdentifiers": [],
                "sizes": [
                    f"{sum([soubor.size_mb for soubor in self.object.soubory.soubory.all()])} MB",
                    f"{sum([soubor.rozsah for soubor in self.object.soubory.soubory.all()])} pages",
                ]
                if self.object.soubory.soubory.exists()
                else [],
                "formats": list(set([soubor.mimetype for soubor in self.object.soubory.soubory.all()])),
                "version": self.object.historie.historie_set.last().datum_zmeny,
                "rightsList": [
                    {
                        "rights": self.object.licence.heslo_en,
                        "rightsUri": self.object.licence.heslar_odkaz.filter(zdroj="SPDX").first().uri,
                        "schemeUri": self.object.licence.heslar_odkaz.filter(zdroj="SPDX").first().uri,
                        "rightsIdentifier": self.object.licence.heslar_odkaz.filter(zdroj="SPDX").first().kod,
                        "rightsIdentifierScheme": self.object.licence.heslar_odkaz.filter(zdroj="SPDX").first().zdroj,
                    }
                ],
                "descriptions": self._serialize_descriptions(),
                "geoLocations": self._serialize_geo_locations(),
                "url": "",
            }
        }
