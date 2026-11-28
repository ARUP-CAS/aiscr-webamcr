Skript test_pre_commit_selenium_lifecycle.py
============================================

Automaticky generovaná dokumentace skriptu ``scripts/test_pre_commit_selenium_lifecycle.py``.

Přehled modulu
--------------

Ověří skutečné metody Selenium lifecycle bez databází, prohlížeče či Fedory.

Třídy
------

.. py:class:: SeleniumLifecycleTests

   Spustí skutečné metody nad unittest lifecycle a paměťovými závislostmi.

   **Metody:**

   .. py:method:: fixture()

      Sestaví testovací případ s produkčními metodami načtenými přes AST.

      :param remote: Použít vzdálenou větev vytváření driveru.
      :param write_error: Simulovat chybu zápisu tabulky.
      :param read_error: Simulovat chybu čtení tabulky.
      :param setup_error: Místo chyby setUp: ``clone`` při klonování databáze, ``driver`` při vytváření
          driveru, ``after`` po jeho vytvoření, nebo None bez chyby.
      :param setup_skip: Přeskočit test výjimkou SkipTest na začátku setUp.
      :param body_error: Simulovat assertion failure aktuálního testu.
      :param base_error: Simulovat chybu základního teardown.
      :return: Případ, driver, zapsané řádky a seznam událostí.

   .. py:method:: test_normal_cleanup_once_for_both_driver_types()

      Normální běh uzavře každý typ driveru právě jednou.

   .. py:method:: test_workbook_failure_still_cleans_driver_and_base()

      Chyba čtení či zápisu neobejde cleanup a zůstane viditelná.

   .. py:method:: test_setup_failure_after_creation_releases_session()

      Pozdější chyba setUp uvolní již vytvořenou session.

   .. py:method:: test_setup_failure_records_one_error_row()

      Chyba setUp před vytvořením driveru, při něm i po něm zapíše jediný řádek ERROR.

   .. py:method:: test_setup_skip_writes_no_row()

      Test přeskočený v setUp nezapíše řádek ani chybu.

   .. py:method:: test_workbook_error_is_not_masked_by_base_teardown_error()

      Druhá chyba základního úklidu nepřepíše původní chybu tabulky.

   .. py:method:: test_previous_results_do_not_change_current_classification()

      Cizí ERROR ani FAIL nezmění vlastní výsledek aktuálního testu.


.. py:class:: CustomResultTests

   Ověří číslování výsledků u chyb, které nemají vlastní testovací případ.

   **Metody:**

   .. py:method:: custom_result()

      Načte produkční ``CustomTextTestResult`` přes AST bez Django nastavení.

   .. py:method:: test_class_setup_error_keeps_the_result_usable()

      Chyba setUpClass nemá číslo testu a nesmí přerušit zápis výsledku.

   .. py:method:: test_numbered_failure_keeps_its_prefix()

      Běžný neúspěšný test si ponechá číslo z průběhu běhu.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_pre_commit_selenium_lifecycle.py
   :language: python
   :linenos:
