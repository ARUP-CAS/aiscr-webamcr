from urllib.parse import quote

import requests

DOI_API_URL = "https://doi.org/api/handles/"
ORCID_API_URL = "https://pub.orcid.org/v3.0/"
ROR_API_URL = "https://api.ror.org/organizations/"
WIKIDATA_API_URL = "https://www.wikidata.org/wiki/"


def verify_doi(doi):
    """
    Provádí operaci verify doi.

    :param doi: Textová hodnota `doi` používaná pro vyhledání, pojmenování nebo hlášení stavu.
    """
    encoded_doi = quote(doi)
    response = requests.get(f"{DOI_API_URL}{encoded_doi}")
    return response.status_code == 200


def verify_orcid(orcid):
    """
    Provádí operaci verify orcid.

    :param orcid: Číselná nebo geometrická hodnota `orcid` použitá při výpočtu nebo transformaci.
    """
    headers = {"Accept": "application/json"}
    response = requests.get(f"{ORCID_API_URL}{orcid}", headers=headers)
    return response.status_code == 200


def verify_ror(ror):
    """
    Provádí operaci verify ror.

    :param ror: Textová hodnota `ror` používaná pro vyhledání, pojmenování nebo hlášení stavu.
    """
    response = requests.get(f"{ROR_API_URL}{ror}")
    return response.status_code == 200


def verify_wikidata(wikidata):
    """
    Provádí operaci verify wikidata.

    :param wikidata: Kolekce ``wikidata`` zpracovávaná touto funkcí.
    """
    if wikidata.startswith("https://www.wikidata.org/entity/"):
        wikidata = wikidata.replace("https://www.wikidata.org/entity/", "")
    response = requests.get(f"{WIKIDATA_API_URL}{wikidata}")
    return response.status_code == 200
