Skript test_generate_js_libraries.py
====================================

Automaticky generovaná dokumentace skriptu ``scripts/test_generate_js_libraries.py``.

Přehled modulu
--------------

Regresní testy metadat a stability generované tabulky JavaScript závislostí.

Třídy
------

.. py:class:: JavaScriptLibrariesTests

   Zastaralá instalace nesmí dodat metadata k jiné verzi z manifestu.

   **Metody:**

   .. py:method:: setUp()

      Připraví izolovaný projekt s přesným pinem a generovaným blokem dokumentace.

   .. py:method:: install_metadata()

      Zapíše metadata simulované instalace bez stahování či instalace balíčků.

      :param values: Pole package.json přepisující verzi, licenci či URL výchozího balíčku 6.3.5.

   .. py:method:: test_stale_installation_preserves_pinned_homepage_and_license()

      Verze 5.9.3 nesmí přepsat odkaz ani licenci řádku pro pin 6.3.5.

   .. py:method:: test_matching_metadata_regenerates_the_correct_homepage()

      Platná metadata 6.3.5 opraví starý odkaz přímo přes vlastní generátor.

   .. py:method:: test_stale_or_absent_installation_keeps_repeated_generation_stable()

      Bez instalace i se starou verzí zůstane uložená dokumentace při opakování stejná.

   .. py:method:: test_unknown_version_does_not_supply_metadata_and_new_package_gets_npm_link()

      Chybějící instalovaná verze nedodá cizí metadata ani novému řádku bez uloženého odkazu.

   .. py:method:: test_matching_metadata_supports_license_object_and_repository_fallback()

      Shodná verze zachová zpracování staršího formátu licence a URL git repozitáře.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_generate_js_libraries.py
   :language: python
   :linenos:
