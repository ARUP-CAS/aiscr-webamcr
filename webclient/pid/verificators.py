from urllib.parse import quote

import requests

DOI_API_URL = "https://doi.org/api/handles/"
ORCID_API_URL = "https://pub.orcid.org/v3.0/"
ROR_API_URL = "https://api.ror.org/organizations/"
WIKIDATA_API_URL = "https://www.wikidata.org/wiki/"


def verify_doi(doi):
    """Zajišťuje logiku funkce ``verify_doi``.
    
    :param doi: Vstupní hodnota parametru ``doi`` použitého při zpracování.
    :return: Návratová hodnota funkce po zpracování vstupních dat.
    """
    encoded_doi = quote(doi)
    response = requests.get(f"{DOI_API_URL}{encoded_doi}")
    return response.status_code == 200


def verify_orcid(orcid):
    """Zajišťuje logiku funkce ``verify_orcid``.
    
    :param orcid: Vstupní hodnota parametru ``orcid`` použitého při zpracování.
    :return: Návratová hodnota funkce po zpracování vstupních dat.
    """
    headers = {"Accept": "application/json"}
    response = requests.get(f"{ORCID_API_URL}{orcid}", headers=headers)
    return response.status_code == 200


def verify_ror(ror):
    """Zajišťuje logiku funkce ``verify_ror``.
    
    :param ror: Vstupní hodnota parametru ``ror`` použitého při zpracování.
    :return: Návratová hodnota funkce po zpracování vstupních dat.
    """
    response = requests.get(f"{ROR_API_URL}{ror}")
    return response.status_code == 200


def verify_wikidata(wikidata):
    """Zajišťuje logiku funkce ``verify_wikidata``.
    
    :param wikidata: Vstupní hodnota parametru ``wikidata`` použitého při zpracování.
    :return: Návratová hodnota funkce po zpracování vstupních dat.
    """
    if wikidata.startswith("https://www.wikidata.org/entity/"):
        wikidata = wikidata.replace("https://www.wikidata.org/entity/", "")
    response = requests.get(f"{WIKIDATA_API_URL}{wikidata}")
    return response.status_code == 200
