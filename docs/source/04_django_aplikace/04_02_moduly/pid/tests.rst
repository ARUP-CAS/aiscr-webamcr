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


.. py:class:: WikiDataAutocompleteViewApiCallTest

   Testy metody ``api_call`` a pomocných metod třídy ``WikiDataAutocompleteView``.

   **Metody:**

   .. py:method:: test_exact_qid_routes_to_item_lookup()

      Dotaz tvořený pouze identifikátorem ``Q`` se ověří přes ``_get_item_result``.

      :param mock_item: Mock pro ``_get_item_result``.
      :param mock_search: Mock pro ``_search_humans``.

   .. py:method:: test_free_text_with_embedded_qid_routes_to_name_search()

      Volný text obsahující ``Q`` s číslicemi se vyhledává podle jména, ne podle identifikátoru.

      :param mock_item: Mock pro ``_get_item_result``.
      :param mock_search: Mock pro ``_search_humans``.

   .. py:method:: test_entity_url_routes_to_item_lookup()

      URL entity Wikidata se převede na identifikátor a ověří přes ``_get_item_result``.

      :param mock_item: Mock pro ``_get_item_result``.
      :param mock_search: Mock pro ``_search_humans``.

   .. py:method:: test_empty_query_returns_empty_list()

      Prázdný dotaz vrátí prázdný seznam bez volání backendu.

      :param mock_item: Mock pro ``_get_item_result``.
      :param mock_search: Mock pro ``_search_humans``.

   .. py:method:: test_whitespace_only_query_returns_empty_list()

      Dotaz tvořený jen mezerami vrátí prázdný seznam bez volání backendu.

      :param mock_item: Mock pro ``_get_item_result``.
      :param mock_search: Mock pro ``_search_humans``.

   .. py:method:: test_search_language_request_error_returns_empty_list()

      Chyba spojení při vyhledávání vrátí prázdný seznam místo výjimky.

   .. py:method:: test_search_language_non_dict_payload_returns_empty_list()

      Neslovníková JSON odpověď vyhledávání vrátí prázdný seznam místo výjimky.

   .. py:method:: test_item_is_human_request_error_returns_false()

      Chyba spojení při ověření výroku ``P31`` se vyhodnotí jako ``False``.

   .. py:method:: test_check_availability_raises_on_connection_error()

      Kontrola dostupnosti propaguje chybu spojení volajícímu.

      :param mock_get: Mock pro ``requests.get``.

   .. py:method:: test_check_availability_raises_on_http_error()

      Kontrola dostupnosti vyhazuje výjimku při chybovém stavovém kódu.

      :param mock_get: Mock pro ``requests.get``.

   .. py:method:: test_check_availability_passes_on_success()

      Kontrola dostupnosti při úspěšné odpovědi nevyhazuje výjimku.

      :param mock_get: Mock pro ``requests.get``.


.. py:class:: DedupGeoLocationsTest

   Testy deterministického odstranění duplicit v ``geoLocations``.

   Původní implementace používala ``list(set(...))``. Iterační pořadí množiny závisí na hashích
   řetězců, které Python randomizuje pro každý proces, takže každý uWSGI i Celery worker
   generoval pro tentýž záznam jiné pořadí prvků a v OCFL vznikaly zbytečné verze.

   **Metody:**

   .. py:method:: _misto()

      Sestaví lokalizaci obsahující pouze ``geoLocationPlace``.

      :param nazev: Textový popis polohy vkládaný do ``geoLocationPlace``.
      :return: Lokalizace ve tvaru ``frozenset`` odpovídajícím ``serialize_geom``.

   .. py:method:: _bod()

      Sestaví lokalizaci s popisem polohy i souřadnicemi.

      :param nazev: Textový popis polohy vkládaný do ``geoLocationPlace``.
      :param sirka: Zeměpisná šířka centroidu geometrie.
      :param delka: Zeměpisná délka centroidu geometrie.
      :return: Lokalizace ve tvaru ``frozenset`` odpovídajícím ``serialize_geom``.

   .. py:method:: test_odstrani_duplicity()

      Shodné lokalizace se ve výsledku objeví jen jednou.

   .. py:method:: test_poradi_nezavisi_na_poradi_vstupu()

      Výsledek je stejný bez ohledu na pořadí, v jakém lokalizace přišly z databáze.

   .. py:method:: test_poradi_je_stabilni_i_pro_lokalizace_se_souradnicemi()

      Stabilní pořadí platí i pro lokalizace s vnořeným ``geoLocationPoint``.

   .. py:method:: test_vnorene_souradnice_jsou_prevedeny_na_slovnik()

      Vnořený ``frozenset`` souřadnic je ve výstupu převeden na slovník.

   .. py:method:: test_prazdny_vstup()

      Prázdná kolekce vrátí prázdný seznam.


.. py:class:: GetFormatsTest

   Testy deterministického pořadí prvků ``formats`` v metadatech dokumentu.

   **Metody:**

   .. py:method:: _formats()

      Zavolá ``_get_formats`` nad serializerem s podvrženými soubory.

      :param mimetypy: Seznam mimetypů souborů navázaných na dokument.
      :return: Seznam formátů vrácený metodou ``_get_formats``.

   .. py:method:: test_formaty_jsou_serazene()

      Mimetypy jsou vráceny abecedně seřazené, nikoli v pořadí množiny.

   .. py:method:: test_poradi_nezavisi_na_poradi_souboru()

      Stejná sada mimetypů dá stejný výsledek bez ohledu na pořadí souborů.

   .. py:method:: test_duplicitni_mimetypy_se_neopakuji()

      Více souborů se shodným mimetypem se ve ``formats`` objeví jen jednou.

   .. py:method:: test_bez_souboru_vraci_prazdny_seznam()

      Dokument bez souborů nemá žádné formáty.

