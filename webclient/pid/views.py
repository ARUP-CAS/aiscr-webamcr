# flake8: noqa: E201, E202
import asyncio
import concurrent.futures
import re
import unicodedata
from urllib.parse import quote

import httpx
import requests
from arch_z.models import ArcheologickyZaznam
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
from pid.exceptions import DoiWriteError
from SPARQLWrapper import JSON, SPARQLWrapper


class ApiView(autocomplete.Select2ListView):
    """Implementuje komponentu ``ApiView`` v rámci aplikace."""

    API_URL = None
    CACHE_PREFIX = None
    r = RedisConnector().get_connection()

    def __init__(self, **kwargs):
        """
        Inicializuje instanci třídy.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super().__init__(**kwargs)

    @classmethod
    def _get_value_from_cache(cls, key):
        """
        Vrací value from cache.

        :param key: Textový název nebo klíč ``key`` používaný v rámci operace.
        :return: Načtená data odpovídající zadaným vstupům.
        """
        cached_value = cls.r.get(f"{cls.CACHE_PREFIX}_{key}")
        if cached_value:
            return [key, cached_value.decode("utf-8")]

    @classmethod
    def _save_value_to_cache(cls, key, value):
        """
               Uloží value to cache.

               :param key: Textový název nebo klíč ``key`` používaný v rámci operace.
               :param value: Parametr ``value`` předává se do volání ``set()``.
        :return: Výstup funkce odpovídající implementované logice.
        """
        cls.r.set(f"{cls.CACHE_PREFIX}_{key}", value)

    @classmethod
    def api_call(cls, q, use_cache=False):
        """
        Zavolá API dotaz pro autocomplete (abstraktní metoda).

        :param q: Vyhledávací dotaz od uživatele.
        :param use_cache: Zda používat mezipaměť výsledků.
        """
        pass

    def get(self, request, *args, **kwargs):
        """
        Vrací JSON odpověď s autocomplete výsledky.

        Při dotazu tvořeném jen mezerami vrátí prázdný seznam výsledků.

        :param request: HTTP požadavek ze strany klienta.
        :param args: Poziční argumenty z URL.
        :param kwargs: Pojmenované argumenty z URL.
        :return: JSON odpověď s výsledky.
        """
        if self.q and str(self.q).strip():
            results = self.get_list()
            results = self.autocomplete_results(results)
            return JsonResponse({"results": results})
        else:
            return JsonResponse({"results": []})

    def autocomplete_results(self, results):
        """
        Transformuje výsledky API na formát autocomplete (id, text).

        :param results: Výsledky vrácené API voláním.
        :return: Seznam tuples (id, text) pro autocomplete.
        """
        return [dict(id=x, text=y) for x, y in results]

    def get_list(self):
        """
        Vrací list. v aplikaci.

        :return: Vrací výsledek volání ``api_call()``.
        """
        return self.api_call(self.q)


class DoiAutocompleteView(LoginRequiredMixin, ApiView):
    """Implementuje komponentu ``DoiAutocompleteView`` v rámci aplikace."""

    API_URL = settings.DATACITE_URL
    CACHE_PREFIX = "DOI"
    # Přísný tvar: prefix 10., registrant 4–9 číslic, lomítko, sufix bez bílých znaků (\S+).
    # Nevyhovují např. některé starší DOI s kratším registrantem — ty jdou jen přes paralelní hledání.
    CROSSREF_DOI_REGEX = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)
    DATACITE_LUCENE_SPECIAL_CHARS = frozenset(r'+-=&|><!(){}[]^"~*?:\/')
    HTTP_TIMEOUT = 5

    @staticmethod
    def _datacite_token_for_quoted_lucene(token: str) -> str:
        """
        Escapuje znaky v tokenu vkládaném do Lucene fráze v uvozovkách.

        :param token: Část uživatelského dotazu.
        :return: Řetězec bezpečný pro vložení do ``"...*token*..."``.
        """
        return token.replace("\\", "\\\\").replace('"', '\\"')

    @classmethod
    def _datacite_record_label(cls, record) -> str:
        """
        Vrátí zobrazený název záznamu DataCite nebo ID záznamu.

        Ošetřuje záznamy bez ``attributes``, bez ``titles`` nebo s prázdným seznamem titulků
        a nekanonické typy polí v odpovědi API.

        :param record: Položka z pole ``data`` odpovědi API.
        :return: Titulek, případně DOI z ``id``; prázdný řetězec, pokud nelze nic odvodit.
        """
        if not isinstance(record, dict):
            return ""
        attrs = record.get("attributes")
        if not isinstance(attrs, dict):
            attrs = {}
        titles = attrs.get("titles")
        if not isinstance(titles, list):
            titles = []
        title = None
        if titles:
            first = titles[0]
            if isinstance(first, dict):
                title = first.get("title")
        doi_id = record.get("id")
        return title or doi_id or ""

    @classmethod
    def _crossref_item_display_title(cls, item) -> str:
        """
        Vrátí zobrazený název z položky odpovědi CrossRef ``/works`` (objekt v ``items``).

        :param item: Slovník s poli ``title`` a ``DOI`` dle API (DOI se v odpovědi předpokládá vždy).
        :return: První textový titulek, jinak řetězec DOI.
        """
        if not isinstance(item, dict):
            return ""
        raw = item.get("title")
        if isinstance(raw, list) and raw:
            first = raw[0]
            if isinstance(first, str) and first.strip():
                return first.strip()
        doi = item.get("DOI")
        if isinstance(doi, str):
            return doi.strip()
        return ""

    @classmethod
    async def _api_call_data_cite(cls, q):
        """
        Vyhledá DOI v DataCite API podle názvu.

        Dotaz je rozdělen na tokeny podle mezer. Tokeny obsahující rezervované znaky
        Lucene (např. ``-``, ``:``, ``(``) jsou obaleny uvozovkami, aby byly interpretovány
        doslovně. Ostatní tokeny jsou ponechány bez uvozovek. Tokeny jsou spojeny operátorem
        ``AND``, takže všechna slova musí být přítomna v názvu, ale nemusí být sousední.
        U každé položky ve ``data`` se předpokládá neprázdné pole ``id`` (DOI).

        :param q: Vyhledávací dotaz (název nebo část názvu publikace).
        :return: Seznam [DOI, název] párů.
        """
        clauses = []
        for token in q.split():
            if any(c in cls.DATACITE_LUCENE_SPECIAL_CHARS for c in token):
                safe = cls._datacite_token_for_quoted_lucene(token)
                clauses.append(f'titles.title:"*{safe}*"')
            else:
                clauses.append(f"titles.title:*{token}*")
        if not clauses:
            return []
        params = {
            "query": " AND ".join(clauses),
        }
        results = []
        try:
            async with httpx.AsyncClient(timeout=cls.HTTP_TIMEOUT) as client:
                response = await client.get(cls.API_URL, params=params)
        except httpx.RequestError:
            return []
        if response.status_code == 200:
            try:
                data = response.json().get("data", [])
            except ValueError:
                return []
            for record in data:
                if not isinstance(record, dict):
                    continue
                doi_id = record.get("id")
                label = cls._datacite_record_label(record) or doi_id
                results.append([doi_id, f"{label} ({doi_id})"])
        return results

    @classmethod
    async def _api_call_data_cite_doi(cls, q):
        """
        Vyhledá DOI v DataCite API pomocí přímého DOI vzoru.

        U každé položky ve ``data`` se předpokládá neprázdné pole ``id`` (DOI).

        :param q: Vyhledávací dotaz (DOI nebo část DOI).
        :return: Seznam [DOI, název] párů.
        """
        if not q or not q.strip():
            return []
        params = {
            "query": f"doi:*{q.upper()}*",
        }
        results = []
        try:
            async with httpx.AsyncClient(timeout=cls.HTTP_TIMEOUT) as client:
                response = await client.get(cls.API_URL, params=params)
        except httpx.RequestError:
            return []
        if response.status_code == 200:
            try:
                data = response.json().get("data", [])
            except ValueError:
                return []
            for record in data:
                if not isinstance(record, dict):
                    continue
                doi_id = record.get("id")
                label = cls._datacite_record_label(record) or doi_id
                results.append([doi_id, f"{label} ({doi_id})"])
        return results

    @classmethod
    def _api_call_cross_ref_doi(cls, q):
        """
        Vyhledá DOI v CrossRef API pomocí přímého DOI.

        U objektu ``message`` (jedna práce i položky ve výsledném seznamu) se předpokládá vždy pole ``DOI``.
        Záložní vyhledávání podle názvu se záměrně neprovádí — DOI jako dotaz pro ``query.title``
        vrací nesouvisející výsledky z CrossRef a blokuje dotaz na DataCite.

        :param q: Vyhledávací dotaz (DOI).
        :return: Seznam [DOI, název] párů, nebo prázdný seznam pokud DOI v CrossRef neexistuje.
        """
        q = (q or "").strip()
        if not q:
            return []
        doi_path = quote(q, safe="")
        base_url = f"https://api.crossref.org/works/{doi_path}"
        try:
            response = requests.get(base_url, timeout=cls.HTTP_TIMEOUT)
        except requests.RequestException:
            return []
        if response.status_code == 200:
            try:
                payload = response.json()
            except ValueError:
                return []
            msg = payload.get("message") or {}
            doi_id = msg.get("DOI")
            title = cls._crossref_item_display_title(msg) or doi_id
            return [[doi_id, f"{title} ({doi_id})"]]
        return []

    @classmethod
    async def _api_call_cross_ref_title(cls, q):
        """
        Vyhledá DOI v CrossRef API pomocí názvu publikace.

        U položek v ``message.items`` se předpokládá vždy pole ``DOI``.

        :param q: Vyhledávací dotaz (název publikace).
        :return: Seznam [DOI, název] párů.
        """
        params = {"query.title": q}
        results = []
        try:
            async with httpx.AsyncClient(timeout=cls.HTTP_TIMEOUT) as client:
                response = await client.get("https://api.crossref.org/works", params=params)
        except httpx.RequestError:
            return []
        if response.status_code == 200:
            try:
                body = response.json()
            except ValueError:
                return []
            payload = body.get("message") or {}
            for record in payload.get("items", []):
                if not isinstance(record, dict):
                    continue
                doi = record.get("DOI")
                label = cls._crossref_item_display_title(record) or doi
                results.append([doi, f"{label} ({doi})"])
        return results

    @classmethod
    def _doi_item_exists(cls, doi: str) -> list:
        """
        Ověří existenci DOI pomocí HTTP HEAD požadavku.

        :param doi: Řetězec DOI předaný z ``api_call`` po shodě vstupu s ``CROSSREF_DOI_REGEX``.
        :return: Seznam [DOI, DOI] pokud existuje, jinak prázdný seznam.
        """
        doi_clean = (doi or "").strip()
        if not doi_clean:
            return []
        path = quote(doi_clean, safe="")
        url = f"https://doi.org/{path}"
        try:
            resp = requests.head(url, allow_redirects=True, timeout=cls.HTTP_TIMEOUT)
        except requests.RequestException:
            return []
        if resp.status_code < 400:
            return [[doi_clean, doi_clean]]
        else:
            return []

    @classmethod
    def api_call(cls, q, use_cache=False):
        """
        Vyhledá DOI v CrossRef a DataCite API.

        Dotaz je na začátku ořezán funkcí ``str.strip()``; prázdný řetězec vrátí prázdný seznam
        bez volání externích služeb. Ověření existence přes ``doi.org`` (``_doi_item_exists``)
        proběhne jen pro vstup odpovídající ``CROSSREF_DOI_REGEX``.

        :param q: Vyhledávací dotaz.
        :param use_cache: Parametr se kvůli shodné signatuře s ``ApiView.api_call`` předává z
            ``PidAutocompleteField``, ale u této třídy se **nepoužívá** (mezipaměť Redis se nečte ani neukládá).
        :return: Seznam [DOI, název] párů.
        """
        q = (q or "").strip()
        if not q:
            return []
        if cls.CROSSREF_DOI_REGEX.match(q):
            results = cls._api_call_cross_ref_doi(q)
        else:
            results = []
        if not results:
            is_doi = bool(cls.CROSSREF_DOI_REGEX.match(q))

            async def _fetch_all():
                tasks = [cls._api_call_data_cite_doi(q), cls._api_call_data_cite(q)]
                if not is_doi:
                    tasks.append(cls._api_call_cross_ref_title(q))
                gathered = await asyncio.gather(*tasks)
                return gathered[0], gathered[1], gathered[2] if not is_doi else []

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    doi_results, title_results, crossref_results = pool.submit(asyncio.run, _fetch_all()).result()
            else:
                doi_results, title_results, crossref_results = asyncio.run(_fetch_all())
            results = doi_results + title_results + crossref_results
        if cls.CROSSREF_DOI_REGEX.match(q) and not any(
            i and len(i) > 0 and i[0] is not None and str(i[0]).lower() == q.lower() for i in results
        ):
            results = cls._doi_item_exists(q) + results
        seen = set()
        results = [r for r in results if not (r[0] in seen or seen.add(r[0]))]
        return results


class OrcidAutocompleteView(ApiView):
    """Implementuje komponentu ``OrcidAutocompleteView`` v rámci aplikace."""

    API_URL = "https://pub.orcid.org/v3.0/expanded-search"
    HEADERS = {"Accept": "application/json", "User-Agent": "Python-Requests"}
    CACHE_PREFIX = "ORCID"

    @classmethod
    def api_call(cls, q, use_cache=True):
        """
        Vyhledá výzkumné pracovníky v ORCID API.

        :param q: Vyhledávací dotaz.
        :param use_cache: Zda používat cache.
        :return: Seznam [ORCID ID, jméno] párů.
        """
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
    """Implementuje komponentu ``RorAutocompleteView`` v rámci aplikace."""

    API_URL = "https://api.ror.org/organizations"
    HEADERS = {"Accept": "application/json", "User-Agent": "Python-Requests"}

    @classmethod
    def api_call(cls, q, use_cache=False):
        """
        Vyhledá organizace v ROR API.

        :param q: Vyhledávací dotaz.
        :param use_cache: Zda používat cache.
        :return: Seznam [ROR ID, jméno] párů.
        """
        params = {
            "query": q,
        }

        result_list = []
        response = requests.get(cls.API_URL, headers=cls.HEADERS, params=params)

        if response.status_code == 200:
            data = response.json()

            for result in data.get("items", []):
                ror_id = result.get("id", "")
                name = ""
                for item in result.get("names", []):
                    if (
                        (item.get("lang") in ("en", "cs") or item.get("lang") is None)
                        and item.get("value")
                        and ("label" in item.get("types") or "ror_display" in item.get("types"))
                    ):
                        name = item.get("value")
                        break
                result_list.append([ror_id, f"{name} ({ror_id})"])
        return result_list


class WikiDataAutocompleteView(LoginRequiredMixin, ApiView):
    """Implementuje komponentu ``WikiDataAutocompleteView`` v rámci aplikace."""

    API_URL = "https://query.wikidata.org/sparql"
    CACHE_PREFIX = "WIKIDATA"
    ID_REGEX = re.compile(r".*Q\d+")

    @classmethod
    def api_call(cls, q, use_cache=False):
        """
        Vyhledá osoby v WikiData SPARQL API.

        :param q: Vyhledávací dotaz.
        :param use_cache: Zda používat cache.
        :return: Seznam [WikiData ID, jméno] párů.
        """
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
                SELECT DISTINCT ?item ?itemLabel
                WHERE {{
                  VALUES ?lang {{ "en" "cs" }}
                  SERVICE wikibase:mwapi {{
                    bd:serviceParam wikibase:endpoint "www.wikidata.org";
                                   wikibase:api "EntitySearch";
                                   mwapi:search "{q}";
                                   mwapi:language ?lang;
                                   wikibase:limit "50".
                    ?item wikibase:apiOutputItem mwapi:item.
                  }}
                  ?item wdt:P31 wd:Q5. 
                  SERVICE wikibase:label {{
                    bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en,cs".
                  }}
                }}
            """

        # Inicializace klienta SPARQL dotazování.
        sparql = SPARQLWrapper(cls.API_URL)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)

        result_list = []
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            id = result["item"]["value"]
            if "/" in id:
                id = id.split("/")[-1]
            if (title := result["itemLabel"]["value"]) and title != id and title != "Q":
                title = f"{title} ({id})"
            else:
                title = id
            result_list.append([id, title])
        return result_list


class ContinuePidProcessing(AdminRecordProcessingView):
    """Implementuje komponentu ``ContinuePidProcessing`` v rámci aplikace."""

    @staticmethod
    def _perform_client_action(record, attribute_name, publish_callable_method, set_callable_method=None):
        """
        Provede akci na záznamu a publikuje do DataCite.

        :param record: Záznam k publikaci (Lokalita, SamostatnyNalez nebo Dokument).
        :param attribute_name: Atribut záznamu pro uložení DOI.
        :param publish_callable_method: Callable pro publikaci.
        :param set_callable_method: Callable pro nastavení stavu.
        :return: DOI nebo chybová zpráva.
        """
        try:
            result = publish_callable_method()
            if set_callable_method:
                set_callable_method()
                record.save()
                if isinstance(record, ArcheologickyZaznam):
                    record.lokalita.active_transaction = record.active_transaction
                    record.lokalita.save()
            return result.get("data", {}).get("id")
        except DoiWriteError as e:
            return (
                f"{_('core.admin.FedoraCustomAdminSite.unexpected_error')}: {e.response_text}, "
                f"{_('core.admin.FedoraCustomAdminSite.request_url')}: {e.request_url}"
            )

    def process_record(self, record, result, **kwargs):
        """
        Zpracuje záznam pro publikaci/skrytí/smazání PID.

        :param record: Záznam k publikaci.
        :param result: Výsledek formuláře.
        :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.
        :param kwargs: Parametr ``kwargs`` pracuje se s atributy ``get``.

            :return: Vrací proměnná ``result``.
        """
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
        return result
