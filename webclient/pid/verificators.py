from urllib.parse import quote

import requests

DOI_API_URL = "https://doi.org/api/handles/"
ORCID_API_URL = "https://pub.orcid.org/v3.0/"
ROR_API_URL = "https://api.ror.org/organizations/"
WIKIDATA_API_URL = "https://www.wikidata.org/wiki/"


def verify_doi(doi):
    """Funkce `verify_doi` v modulu `webclient.pid.verificators`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param doi: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    encoded_doi = quote(doi)
    response = requests.get(f"{DOI_API_URL}{encoded_doi}")
    return response.status_code == 200


def verify_orcid(orcid):
    """Funkce `verify_orcid` v modulu `webclient.pid.verificators`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param orcid: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    headers = {"Accept": "application/json"}
    response = requests.get(f"{ORCID_API_URL}{orcid}", headers=headers)
    return response.status_code == 200


def verify_ror(ror):
    """Funkce `verify_ror` v modulu `webclient.pid.verificators`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param ror: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    response = requests.get(f"{ROR_API_URL}{ror}")
    return response.status_code == 200


def verify_wikidata(wikidata):
    """Funkce `verify_wikidata` v modulu `webclient.pid.verificators`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param wikidata: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    if wikidata.startswith("https://www.wikidata.org/entity/"):
        wikidata = wikidata.replace("https://www.wikidata.org/entity/", "")
    response = requests.get(f"{WIKIDATA_API_URL}{wikidata}")
    return response.status_code == 200
