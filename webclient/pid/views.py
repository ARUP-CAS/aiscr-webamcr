# flake8: noqa: E201, E202
import re
import unicodedata

import requests
from arch_z.models import ArcheologickyZaznam
from cacheops import invalidate_all
from core.connectors import RedisConnector
from core.constants import AZ_STAV_ARCHIVOVANY, D_STAV_ARCHIVOVANY, SN_ARCHIVOVANY
from core.repository_connector import FedoraTransaction
from dal import autocomplete
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.translation import gettext as _
from dokument.models import Dokument
from fedora_management.views import AdminRecordProcessingView
from pas.models import SamostatnyNalez
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
    def api_call(cls, q, use_cache=True):
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

            expanded_result = data.get("expanded-result", None)
            if expanded_result:
                for result in expanded_result:
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
        if not q:
            return []
        if q.startswith("https://www.wikidata.org/entity/"):
            q = q.replace("https://www.wikidata.org/entity/", "")
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
            q = unicodedata.normalize("NFKD", q)
            query = f"""
                SELECT ?item ?itemLabel
                WHERE {{
                  {{ ?item rdfs:label "{q}"@en }}
                  UNION
                  {{ ?item rdfs:label "{q}"@cs }}
                  SERVICE wikibase:label {{
                    bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en,cs"
                  }}
                }}
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


class ContinuePidProcessing(AdminRecordProcessingView):
    @staticmethod
    def _perform_client_action(record, attribute_name, publish_callable_method, set_callable_method=None):
        result = publish_callable_method()
        if set_callable_method:
            set_callable_method()
            record.save()
        return result.get("data", {}).get("id")

    def process_record(self, record, result, **kwargs):
        fedora_transaction = FedoraTransaction()
        record.active_transaction = fedora_transaction
        performed_action = kwargs.get("performed_action")
        if isinstance(record, Dokument):
            if performed_action == "post_publish":
                if not record.doi and record.stav == D_STAV_ARCHIVOVANY:
                    result["result"] = self._perform_client_action(record, "doi", record.doi_publish, record.set_doi)
                    result["detail"] = record.doi_url
                else:
                    result["result"] = _("core.admin.FedoraCustomAdminSite.post_publish.cannot_be_done")
            elif performed_action == "put_publish":
                if record.doi and record.stav == D_STAV_ARCHIVOVANY:
                    result["result"] = self._perform_client_action(record, "doi", record.doi_publish)
                    result["detail"] = record.doi_url
                else:
                    result["result"] = _("core.admin.FedoraCustomAdminSite.post_publish.cannot_be_done")
            elif performed_action == "hide":
                if record.doi and record.stav != D_STAV_ARCHIVOVANY:
                    result["result"] = self._perform_client_action(record, "doi", record.doi_hide)
                    result["detail"] = record.doi_url
                else:
                    result["result"] = _("core.admin.FedoraCustomAdminSite.post_publish.cannot_be_done")
            elif performed_action == "update":
                if record.doi:
                    result["result"] = self._perform_client_action(record, "doi", record.doi_update)
                    result["detail"] = record.doi_url
                else:
                    result["result"] = _("core.admin.FedoraCustomAdminSite.post_publish.cannot_be_done")
        elif isinstance(record, ArcheologickyZaznam) and record.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA:
            if performed_action == "post_publish":
                if not record.lokalita.igsn and record.stav == AZ_STAV_ARCHIVOVANY:
                    result["result"] = self._perform_client_action(
                        record, "igsn", record.lokalita.igsn_publish, record.lokalita.set_igsn
                    )
                    result["detail"] = record.lokalita.igsn_url
                else:
                    result["result"] = _("core.admin.FedoraCustomAdminSite.post_publish.cannot_be_done")
            elif performed_action == "put_publish":
                if record.lokalita.igsn and record.stav == AZ_STAV_ARCHIVOVANY:
                    result["result"] = self._perform_client_action(record, "igsn", record.lokalita.igsn_publish)
                    result["detail"] = record.lokalita.igsn_url
                else:
                    result["result"] = _("core.admin.FedoraCustomAdminSite.post_publish.cannot_be_done")
            elif performed_action == "hide":
                if record.lokalita.igsn and record.stav != AZ_STAV_ARCHIVOVANY:
                    result["result"] = self._perform_client_action(record, "igsn", record.lokalita.igsn_hide)
                    result["detail"] = record.lokalita.igsn_url
                else:
                    result["result"] = _("core.admin.FedoraCustomAdminSite.post_publish.cannot_be_done")
            elif performed_action == "update":
                if record.lokalita.igsn:
                    result["result"] = self._perform_client_action(record, "igsn", record.lokalita.igsn_update)
                    result["detail"] = record.lokalita.igsn_url
                else:
                    result["result"] = _("core.admin.FedoraCustomAdminSite.post_publish.cannot_be_done")
        elif isinstance(record, SamostatnyNalez):
            if performed_action == "post_publish":
                if not record.igsn and record.stav == SN_ARCHIVOVANY:
                    result["result"] = self._perform_client_action(record, "igsn", record.igsn_publish, record.set_igsn)
                    result["detail"] = record.igsn_url
                else:
                    result["result"] = _("core.admin.FedoraCustomAdminSite.post_publish.cannot_be_done")
            elif performed_action == "put_publish":
                if record.igsn and record.stav == SN_ARCHIVOVANY:
                    result["result"] = self._perform_client_action(record, "igsn", record.igsn_publish)
                    result["detail"] = record.igsn_url
                else:
                    result["result"] = _("core.admin.FedoraCustomAdminSite.post_publish.cannot_be_done")
            elif performed_action == "hide":
                if record.igsn and record.stav != SN_ARCHIVOVANY:
                    result["result"] = self._perform_client_action(record, "igsn", record.igsn_hide)
                    result["detail"] = record.igsn_url
                else:
                    result["result"] = _("core.admin.FedoraCustomAdminSite.post_publish.cannot_be_done")
            elif performed_action == "update":
                if record.igsn:
                    result["result"] = self._perform_client_action(record, "igsn", record.igsn_update)
                    result["detail"] = record.igsn_url
                else:
                    result["result"] = _("core.admin.FedoraCustomAdminSite.post_publish.cannot_be_done")
        else:
            result["result"] = _("core.admin.FedoraCustomAdminSite.cannot_load_record")
        fedora_transaction.mark_transaction_as_closed()
        invalidate_all()
        return result
