PID tests
=========

Modul tests.

Přehled modulu
--------------

Testy aplikace PID.

Třídy
------

.. py:class:: DoiAutocompleteViewApiCallTest

   Testy metody ``api_call`` třídy ``DoiAutocompleteView``.

   **Metody:**

   .. py:method:: test_title_search_returns_doi_wildcard_results_first()

      Výsledky DOI wildcard dotazu jsou vráceny jako první.

      :param mock_doi: Mock pro ``_api_call_data_cite_doi``.
      :param mock_title: Mock pro ``_api_call_data_cite``.
      :param mock_crossref: Mock pro ``_api_call_cross_ref_title``.
      :param mock_exists: Mock pro ``_doi_item_exists``.

   .. py:method:: test_title_search_result_order_doi_then_title_then_crossref()

      Pořadí výsledků: DOI wildcard, DataCite název, CrossRef název.

      :param mock_doi: Mock pro ``_api_call_data_cite_doi``.
      :param mock_title: Mock pro ``_api_call_data_cite``.
      :param mock_crossref: Mock pro ``_api_call_cross_ref_title``.
      :param mock_exists: Mock pro ``_doi_item_exists``.

   .. py:method:: test_duplicates_are_removed_keeping_first_occurrence()

      Duplicitní DOI jsou odstraněna; zachová se první výskyt.

      :param mock_doi: Mock pro ``_api_call_data_cite_doi``.
      :param mock_title: Mock pro ``_api_call_data_cite``.
      :param mock_crossref: Mock pro ``_api_call_cross_ref_title``.
      :param mock_exists: Mock pro ``_doi_item_exists``.

   .. py:method:: test_doi_format_input_uses_crossref_doi_path()

      Vstup ve formátu DOI volá ``_api_call_cross_ref_doi`` a přeskočí async volání.

      :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
      :param mock_dc_title: Mock pro ``_api_call_data_cite``.
      :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
      :param mock_cr_doi: Mock pro ``_api_call_cross_ref_doi``.
      :param mock_exists: Mock pro ``_doi_item_exists``.

   .. py:method:: test_doi_format_with_no_crossref_result_falls_back_to_async()

      Pokud ``_api_call_cross_ref_doi`` vrátí prázdný seznam, provedou se async volání.

      :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
      :param mock_dc_title: Mock pro ``_api_call_data_cite``.
      :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
      :param mock_cr_doi: Mock pro ``_api_call_cross_ref_doi``.
      :param mock_exists: Mock pro ``_doi_item_exists``.

   .. py:method:: test_doi_item_exists_prepended_when_exact_doi_not_in_results()

      Pokud výsledky neobsahují přesné DOI, je zavoláno ``_doi_item_exists`` a výsledek přidán na začátek.

      :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
      :param mock_dc_title: Mock pro ``_api_call_data_cite``.
      :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
      :param mock_exists: Mock pro ``_doi_item_exists``.

   .. py:method:: test_empty_query_returns_empty_list()

      Prázdný nebo jen mezerami tvořený dotaz vrátí prázdný seznam bez volání backendu.

      :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
      :param mock_dc_title: Mock pro ``_api_call_data_cite``.
      :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
      :param mock_exists: Mock pro ``_doi_item_exists``.

   .. py:method:: test_none_query_returns_empty_list()

      ``None`` jako dotaz vrátí prázdný seznam bez volání backendu.

      :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
      :param mock_dc_title: Mock pro ``_api_call_data_cite``.
      :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
      :param mock_exists: Mock pro ``_doi_item_exists``.

