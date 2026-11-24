Skript test_pre_commit_execution.py
===================================

Automaticky generovaná dokumentace skriptu ``scripts/test_pre_commit_execution.py``.

Přehled modulu
--------------

Regrese skutečných výsledků runneru a protokolu jednotlivých pokusů.

Třídy
------

.. py:class:: ExecutionTests

   Ověří procesní stav, dokončený výstup a oddělené výsledky pokusů.

   **Metody:**

   .. py:method:: setUp()

      Připraví pouze dočasné soubory bez Django či služeb.

   .. py:method:: attempt()

      Připraví úplný výsledek přes produkční publikační funkci.

      :param identity: Identita testovacího pokusu.
      :param mode: Režim výběru.
      :param number: Číslo testu.
      :param state: Stav výsledku.
      :param code: Výsledek procesu.
      :param counts: Počty testů.
      :return: Adresář pokusu a záznam výsledku.

   .. py:method:: test_crash_zero_missing_and_inconsistent_results_fail()

      Traceback ani chybějící či rozporný souhrn nezaloží úspěch.

   .. py:method:: test_complete_success_failures_and_unexpected_success()

      Úplné souhrny respektují nativní výsledek včetně unexpected successes.

   .. py:method:: test_readers_finish_in_console_and_file_modes()

      Dokončení procesu před koncem čtení nezkrátí zachycený výstup.

   .. py:method:: test_migration_failure_stops_tests_and_publishes_error()

      Chyba migrace nepustí testy a nevytvoří úspěšné nulové počty.

   .. py:method:: test_capture_failure_reaps_child_and_unwritable_log_does_not_start_it()

      Chyba čtení ukončí vlastní proces; neotevřitelný log jej vůbec nespustí.

   .. py:method:: test_runner_crash_does_not_publish_passing_counts()

      Chyba startu procesu dostane error místo completed s nulou.

   .. py:method:: test_runner_diagnostics_hide_explicit_and_secret_backed_roots()

      Pokus lze sledovat podle identity bez zveřejnění cesty z konfigurace.

   .. py:method:: test_failures_before_attempt_creation_hide_sensitive_exceptions()

      Chyba inicializace, konfigurace či adresáře nezveřejní hodnotu výjimky.

   .. py:method:: test_runner_error_stages_and_metadata_hide_sensitive_exceptions()

      Provozní chyby zachovají fázi a nepropustí citlivý text do konzole ani JSON.

   .. py:method:: test_failed_error_publication_does_not_escape_or_disclose_exception()

      Druhá chyba publikace zachová neúspěch bez tracebacku s citlivou cestou.

   .. py:method:: test_runner_publishes_completed_pass_and_failure()

      Dokončené testy zachovají skutečný status a zveřejní aktuální počty.

   .. py:method:: test_selective_workbook_keeps_unselected_tests()

      Aktuální artefakt je nový, ale příští výběr nepřijde o dřívější testy.

   .. py:method:: test_selection_preserves_previous_workbook_and_reports_noop()

      No-op má novou identitu a stará tabulka zůstane vstupem výběru.

   .. py:method:: test_missing_and_malformed_selection_fail()

      Chybějící nebo neplatný vstup výběru není no-op.

   .. py:method:: test_attempts_are_unique_and_cannot_escape()

      Opakování má jiný adresář; stejný pokus ani cesta se nepřepíše.

   .. py:method:: test_stale_mixed_and_incomplete_results_are_rejected()

      Platný starý souhrn, jiné identity i změněné soubory jsou odmítnuty.

   .. py:method:: test_required_workbook_and_interrupted_publication_fail()

      Chybějící tabulka ani přerušený zápis nevytvoří dokončený výsledek.

   .. py:method:: test_manifest_schema_and_duplicate_keys_fail()

      Názvy cest, duplicitní klíče a typy nelze podvrhnout jako metadata.

   .. py:method:: test_runner_publishes_new_spreadsheet_and_rejects_failed_write()

      Selenium běh vyžaduje tabulku tohoto pokusu, nikoli starou kopii.

   .. py:method:: test_summary_validation_is_non_evaluating()

      Celý souhrn má právě dva desetinné záznamy a nepřipouští příkazy.

   .. py:method:: test_summary_read_is_bounded_before_allocation()

      Odmítne velký proud po nejvýše 4097 bajtech a přijme přesnou hranici.

   .. py:method:: test_explicit_categories_cross_runner_and_result_consumer()

      Skips a očekávaná selhání nezvýší PASSED ani nezničí platný zero/zero běh.

   .. py:method:: test_counter_consistency_and_legacy_rejection()

      Neplatné typy, kategorie či stará verze neprojdou do nového výsledku.

   .. py:method:: test_all_mode_aliases_and_mutual_exclusion_remain_compatible()

      Bez příznaku i s -a/--all se volí vsechny a konfliktní režimy se odmítnou.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_pre_commit_execution.py
   :language: python
   :linenos:
