"""Testy aplikace PID."""

from unittest.mock import AsyncMock, patch

from django.test import TestCase
from pid.views import DoiAutocompleteView


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
