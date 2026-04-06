from urllib.parse import quote

import requests

DOI_API_URL = "https://doi.org/api/handles/"
ORCID_API_URL = "https://pub.orcid.org/v3.0/"
ROR_API_URL = "https://api.ror.org/organizations/"
WIKIDATA_API_URL = "https://www.wikidata.org/wiki/"


def verify_doi(doi):
    """
    Ověří existenci DOI identifikátoru dotazem na API doi.org.

    :param doi: Řetězec s DOI identifikátorem, který má být ověřen.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
    """
    encoded_doi = quote(doi)
    response = requests.get(f"{DOI_API_URL}{encoded_doi}")
    return response.status_code == 200


def verify_orcid(orcid):
    """
    Ověří existenci ORCID identifikátoru dotazem na veřejné ORCID API.

    :param orcid: Řetězec s ORCID identifikátorem, který má být ověřen.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
    """
    headers = {"Accept": "application/json"}
    response = requests.get(f"{ORCID_API_URL}{orcid}", headers=headers)
    return response.status_code == 200


def verify_ror(ror):
    """
    Ověří existenci ROR identifikátoru organizace dotazem na ROR API.

    :param ror: Řetězec s ROR identifikátorem, který má být ověřen.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
    """
    response = requests.get(f"{ROR_API_URL}{ror}")
    return response.status_code == 200


def verify_wikidata(wikidata):
    """
    Ověří existenci položky Wikidata dotazem na stránku daného záznamu.

    :param wikidata: Řetězec s identifikátorem nebo URL záznamu Wikidata, který má být ověřen.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
    """
    if wikidata.startswith("https://www.wikidata.org/entity/"):
        wikidata = wikidata.replace("https://www.wikidata.org/entity/", "")
    response = requests.get(f"{WIKIDATA_API_URL}{wikidata}")
    return response.status_code == 200
