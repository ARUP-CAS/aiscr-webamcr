# flake8: noqa: E201, E202

import re

import requests
from core.connectors import RedisConnector
from dal import autocomplete
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from SPARQLWrapper import JSON, SPARQLWrapper


class ApiView(autocomplete.Select2ListView):
    API_URL = None
    CACHE_PREFIX = None
    r = RedisConnector().get_connection()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _get_value_from_cache(cls, key):
        cached_value = cls.r.get(f"{cls.CACHE_PREFIX}_{key}")
        if cached_value:
            return [key, cached_value.decode("utf-8")]

    @classmethod
    def _save_value_to_cache(cls, key, value):
        cls.r.set(f"{cls.CACHE_PREFIX}_{key}", value)

    @classmethod
    def api_call(cls, q, use_cache=False):
        pass

    def get(self, request, *args, **kwargs):
        if self.q:
            results = self.get_list()
            results = self.autocomplete_results(results)
            return JsonResponse({"results": results})
        else:
            return JsonResponse({"results": []})

    def autocomplete_results(self, results):
        return [dict(id=x, text=y) for x, y in results]

    def get_list(self):
        return self.api_call(self.q)


class DoiAutocompleteView(LoginRequiredMixin, ApiView):
    API_URL = settings.DATACITE_URL
    CACHE_PREFIX = "DOI"

    @classmethod
    def api_call(cls, q, use_cache=False):
        params = {
            "query": f"doi:*{q.upper()}*",
        }
        results = []
        response = requests.get(cls.API_URL, params=params)
        if response.status_code == 200:
            response = response.json()
            data = response.get("data", [])
            for record in data:
                title = record.get("attributes").get("titles")[0].get("title") or record.get("id")
                id = record.get("id")
                results.append([id, f"{title} ({id})"])
        return results


class OrcidAutocompleteView(ApiView):
    API_URL = "https://pub.orcid.org/v3.0/expanded-search"
    HEADERS = {"Accept": "application/json", "User-Agent": "Python-Requests"}
    CACHE_PREFIX = "ORCID"

    @classmethod
    def api_call(cls, q, use_cache=False):
        if use_cache:
            cached_value = cls._get_value_from_cache(q)
            if cached_value:
                return [cached_value]

        params = {
            "q": f"{q}",
        }

        result_list = []
        response = requests.get(cls.API_URL, headers=cls.HEADERS, params=params)

        if response.status_code == 200:
            data = response.json()

            for result in data.get("expanded-result", []):
                orcid_id = result.get("orcid-id", "")
                if result.get("family-names") and result.get("given-names"):
                    full_nane = f"{result['family-names']}, {result['given-names']} ({orcid_id})"
                else:
                    full_nane = orcid_id
                result_list.append([orcid_id, full_nane])
                cls._save_value_to_cache(orcid_id, full_nane)
        return result_list


class RorAutocompleteView(LoginRequiredMixin, ApiView):
    API_URL = "https://api.ror.org/organizations"
    HEADERS = {"Accept": "application/json", "User-Agent": "Python-Requests"}

    @classmethod
    def api_call(cls, q, use_cache=False):
        params = {
            "query": q,
        }

        result_list = []
        response = requests.get(cls.API_URL, headers=cls.HEADERS, params=params)

        if response.status_code == 200:
            data = response.json()

            for result in data.get("items", []):
                ror_id = result.get("id", "")
                name = result.get("name", "")
                result_list.append([ror_id, f"{name} ({ror_id})"])
        return result_list


class WikiDataAutocompleteView(LoginRequiredMixin, ApiView):
    API_URL = "https://query.wikidata.org/sparql"
    CACHE_PREFIX = "WIKIDATA"
    ID_REGEX = re.compile(r".*Q\d+")

    @classmethod
    def api_call(cls, q, use_cache=False):
        if cls.ID_REGEX.match(q):
            query = f"""
                SELECT ?item ?itemLabel WHERE {{
                VALUES ?item {{ wd:{q} }}
                ?item wdt:P31 wd:Q5.
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en,cs". }}
                }}
                LIMIT 50
            """
        else:
            query = f"""
                SELECT ?item ?itemLabel WHERE {{
                  ?item wdt:P31 wd:Q5.
                  ?item ?label "{q}"
                  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en,cs". }}
                }}
            LIMIT 10
            """

        # Set up the SPARQL wrapper
        sparql = SPARQLWrapper(cls.API_URL)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)

        result_list = []
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            id = result["item"]["value"]
            if "/" in id:
                id = id.split("/")[-1]
            result_list.append([id, f"{result['itemLabel']['value']} ({id})"])
        return result_list
