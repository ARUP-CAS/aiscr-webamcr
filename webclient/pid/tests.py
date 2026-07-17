"""Testy aplikace PID."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import requests
from django.test import TestCase
from pid.views import DoiAutocompleteView, WikiDataAutocompleteView


class DoiAutocompleteViewApiCallTest(TestCase):
    """Testy metody ``api_call`` třídy ``DoiAutocompleteView``."""

    @patch.object(DoiAutocompleteView, "_doi_item_exists", return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock)
    def test_title_search_returns_doi_wildcard_results_first(self, mock_doi, mock_title, mock_crossref, mock_exists):
        """
        Výsledky DOI wildcard dotazu jsou vráceny jako první.

        :param mock_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_title: Mock pro ``_api_call_data_cite``.
        :param mock_crossref: Mock pro ``_api_call_cross_ref_title``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        mock_doi.return_value = [["10.1/aaa", "Title A (10.1/aaa)"], ["10.1/bbb", "Title B (10.1/bbb)"]]

        results = DoiAutocompleteView.api_call("some title")

        self.assertEqual(results[0][0], "10.1/aaa")
        self.assertEqual(results[1][0], "10.1/bbb")
        mock_exists.assert_not_called()

    @patch.object(DoiAutocompleteView, "_doi_item_exists", return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock)
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock)
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock)
    def test_title_search_result_order_doi_then_title_then_crossref(
        self, mock_doi, mock_title, mock_crossref, mock_exists
    ):
        """
        Pořadí výsledků: DOI wildcard, DataCite název, CrossRef název.

        :param mock_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_title: Mock pro ``_api_call_data_cite``.
        :param mock_crossref: Mock pro ``_api_call_cross_ref_title``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        mock_doi.return_value = [["10.1/doi", "DOI result (10.1/doi)"]]
        mock_title.return_value = [["10.1/title", "Title result (10.1/title)"]]
        mock_crossref.return_value = [["10.1/crossref", "CrossRef result (10.1/crossref)"]]

        results = DoiAutocompleteView.api_call("enclosure Babina")

        self.assertEqual([r[0] for r in results], ["10.1/doi", "10.1/title", "10.1/crossref"])

    @patch.object(DoiAutocompleteView, "_doi_item_exists", return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock)
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock)
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock)
    def test_duplicates_are_removed_keeping_first_occurrence(self, mock_doi, mock_title, mock_crossref, mock_exists):
        """
        Duplicitní DOI jsou odstraněna; zachová se první výskyt.

        :param mock_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_title: Mock pro ``_api_call_data_cite``.
        :param mock_crossref: Mock pro ``_api_call_cross_ref_title``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        mock_doi.return_value = [["10.1/dup", "From DOI (10.1/dup)"]]
        mock_title.return_value = [["10.1/dup", "From Title (10.1/dup)"], ["10.1/unique", "Unique (10.1/unique)"]]
        mock_crossref.return_value = []

        results = DoiAutocompleteView.api_call("some title")

        dois = [r[0] for r in results]
        self.assertEqual(dois.count("10.1/dup"), 1)
        self.assertEqual(results[0], ["10.1/dup", "From DOI (10.1/dup)"])

    @patch.object(DoiAutocompleteView, "_doi_item_exists", return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_doi")
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock, return_value=[])
    def test_doi_format_input_uses_crossref_doi_path(
        self, mock_dc_doi, mock_dc_title, mock_cr_title, mock_cr_doi, mock_exists
    ):
        """
        Vstup ve formátu DOI volá ``_api_call_cross_ref_doi`` a přeskočí async volání.

        :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_dc_title: Mock pro ``_api_call_data_cite``.
        :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
        :param mock_cr_doi: Mock pro ``_api_call_cross_ref_doi``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        mock_cr_doi.return_value = [["10.1234/abc", "Found (10.1234/abc)"]]

        results = DoiAutocompleteView.api_call("10.1234/abc")

        mock_cr_doi.assert_called_once_with("10.1234/abc")
        mock_dc_doi.assert_not_called()
        self.assertEqual(results[0][0], "10.1234/abc")

    @patch.object(DoiAutocompleteView, "_doi_item_exists", return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_doi")
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock, return_value=[])
    def test_doi_format_with_no_crossref_result_falls_back_to_async(
        self, mock_dc_doi, mock_dc_title, mock_cr_title, mock_cr_doi, mock_exists
    ):
        """
        Pokud ``_api_call_cross_ref_doi`` vrátí prázdný seznam, provedou se async volání.

        :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_dc_title: Mock pro ``_api_call_data_cite``.
        :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
        :param mock_cr_doi: Mock pro ``_api_call_cross_ref_doi``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        mock_cr_doi.return_value = []

        DoiAutocompleteView.api_call("10.1234/unknown")

        mock_dc_doi.assert_called_once()

    @patch.object(DoiAutocompleteView, "_doi_item_exists")
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock, return_value=[])
    def test_doi_item_exists_prepended_when_exact_doi_not_in_results(
        self, mock_dc_doi, mock_dc_title, mock_cr_title, mock_exists
    ):
        """
        Pokud výsledky neobsahují přesné DOI, je zavoláno ``_doi_item_exists`` a výsledek přidán na začátek.

        :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_dc_title: Mock pro ``_api_call_data_cite``.
        :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        mock_exists.return_value = [["10.1234/exact", "10.1234/exact"]]

        results = DoiAutocompleteView.api_call("10.1234/exact")

        self.assertEqual(results[0][0], "10.1234/exact")
        mock_exists.assert_called_once_with("10.1234/exact")

    @patch.object(DoiAutocompleteView, "_doi_item_exists", return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock, return_value=[])
    def test_empty_query_returns_empty_list(self, mock_dc_doi, mock_dc_title, mock_cr_title, mock_exists):
        """
        Prázdný nebo jen mezerami tvořený dotaz vrátí prázdný seznam bez volání backendu.

        :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_dc_title: Mock pro ``_api_call_data_cite``.
        :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        results = DoiAutocompleteView.api_call("   ")

        self.assertEqual(results, [])
        mock_dc_doi.assert_not_called()
        mock_dc_title.assert_not_called()
        mock_cr_title.assert_not_called()
        mock_exists.assert_not_called()

    @patch.object(DoiAutocompleteView, "_doi_item_exists", return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock, return_value=[])
    def test_none_query_returns_empty_list(self, mock_dc_doi, mock_dc_title, mock_cr_title, mock_exists):
        """
        ``None`` jako dotaz vrátí prázdný seznam bez volání backendu.

        :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_dc_title: Mock pro ``_api_call_data_cite``.
        :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        results = DoiAutocompleteView.api_call(None)

        self.assertEqual(results, [])
        mock_dc_doi.assert_not_called()
        mock_dc_title.assert_not_called()
        mock_cr_title.assert_not_called()
        mock_exists.assert_not_called()


class WikiDataAutocompleteViewApiCallTest(TestCase):
    """Testy metody ``api_call`` a pomocných metod třídy ``WikiDataAutocompleteView``."""

    @patch.object(WikiDataAutocompleteView, "_search_humans", new_callable=AsyncMock)
    @patch.object(WikiDataAutocompleteView, "_get_item_result")
    def test_exact_qid_routes_to_item_lookup(self, mock_item, mock_search):
        """
        Dotaz tvořený pouze identifikátorem ``Q`` se ověří přes ``_get_item_result``.

        :param mock_item: Mock pro ``_get_item_result``.
        :param mock_search: Mock pro ``_search_humans``.
        """
        mock_item.return_value = [["Q868", "Aristotelés (Q868)"]]

        results = WikiDataAutocompleteView.api_call(" Q868 ")

        self.assertEqual(results, [["Q868", "Aristotelés (Q868)"]])
        mock_item.assert_called_once_with("Q868")
        mock_search.assert_not_called()

    @patch.object(WikiDataAutocompleteView, "_search_humans", new_callable=AsyncMock, return_value=[])
    @patch.object(WikiDataAutocompleteView, "_get_item_result")
    def test_free_text_with_embedded_qid_routes_to_name_search(self, mock_item, mock_search):
        """
        Volný text obsahující ``Q`` s číslicemi se vyhledává podle jména, ne podle identifikátoru.

        :param mock_item: Mock pro ``_get_item_result``.
        :param mock_search: Mock pro ``_search_humans``.
        """
        WikiDataAutocompleteView.api_call("Aristoteles Q868")

        mock_item.assert_not_called()
        mock_search.assert_called_once()

    @patch.object(WikiDataAutocompleteView, "_search_humans", new_callable=AsyncMock)
    @patch.object(WikiDataAutocompleteView, "_get_item_result", return_value=[])
    def test_entity_url_routes_to_item_lookup(self, mock_item, mock_search):
        """
        URL entity Wikidata se převede na identifikátor a ověří přes ``_get_item_result``.

        :param mock_item: Mock pro ``_get_item_result``.
        :param mock_search: Mock pro ``_search_humans``.
        """
        WikiDataAutocompleteView.api_call("https://www.wikidata.org/entity/Q868")

        mock_item.assert_called_once_with("Q868")
        mock_search.assert_not_called()

    @patch.object(WikiDataAutocompleteView, "_search_humans", new_callable=AsyncMock)
    @patch.object(WikiDataAutocompleteView, "_get_item_result")
    def test_empty_query_returns_empty_list(self, mock_item, mock_search):
        """
        Prázdný dotaz vrátí prázdný seznam bez volání backendu.

        :param mock_item: Mock pro ``_get_item_result``.
        :param mock_search: Mock pro ``_search_humans``.
        """
        results = WikiDataAutocompleteView.api_call("")

        self.assertEqual(results, [])
        mock_item.assert_not_called()
        mock_search.assert_not_called()

    def test_search_language_request_error_returns_empty_list(self):
        """Chyba spojení při vyhledávání vrátí prázdný seznam místo výjimky."""
        client = SimpleNamespace(get=AsyncMock(side_effect=httpx.RequestError("boom")))

        results = asyncio.run(WikiDataAutocompleteView._search_language(client, "test", "cs"))

        self.assertEqual(results, [])

    def test_search_language_non_dict_payload_returns_empty_list(self):
        """Neslovníková JSON odpověď vyhledávání vrátí prázdný seznam místo výjimky."""
        response = SimpleNamespace(status_code=200, json=lambda: ["unexpected"])
        client = SimpleNamespace(get=AsyncMock(return_value=response))

        results = asyncio.run(WikiDataAutocompleteView._search_language(client, "test", "cs"))

        self.assertEqual(results, [])

    def test_item_is_human_request_error_returns_false(self):
        """Chyba spojení při ověření výroku ``P31`` se vyhodnotí jako ``False``."""
        client = SimpleNamespace(get=AsyncMock(side_effect=httpx.RequestError("boom")))

        result = asyncio.run(WikiDataAutocompleteView._item_is_human(client, "Q868"))

        self.assertFalse(result)

    @patch("pid.views.requests.get")
    def test_check_availability_raises_on_connection_error(self, mock_get):
        """Kontrola dostupnosti propaguje chybu spojení volajícímu.

        :param mock_get: Mock pro ``requests.get``.
        """
        mock_get.side_effect = requests.ConnectionError("boom")

        with self.assertRaises(requests.RequestException):
            WikiDataAutocompleteView.check_availability()

    @patch("pid.views.requests.get")
    def test_check_availability_raises_on_http_error(self, mock_get):
        """Kontrola dostupnosti vyhazuje výjimku při chybovém stavovém kódu.

        :param mock_get: Mock pro ``requests.get``.
        """
        response = requests.Response()
        response.status_code = 503
        mock_get.return_value = response

        with self.assertRaises(requests.RequestException):
            WikiDataAutocompleteView.check_availability()

    @patch("pid.views.requests.get")
    def test_check_availability_passes_on_success(self, mock_get):
        """Kontrola dostupnosti při úspěšné odpovědi nevyhazuje výjimku.

        :param mock_get: Mock pro ``requests.get``.
        """
        response = requests.Response()
        response.status_code = 200
        mock_get.return_value = response

        WikiDataAutocompleteView.check_availability()
        mock_get.assert_called_once()
