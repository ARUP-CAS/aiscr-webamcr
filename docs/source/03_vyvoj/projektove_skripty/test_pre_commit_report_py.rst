Skript test_pre_commit_report.py
================================

Automaticky generovaná dokumentace skriptu ``scripts/test_pre_commit_report.py``.

Přehled modulu
--------------

Regresní testy skutečných staged diffů a společného vykreslení reportů CI.

Třídy
------

.. py:class:: ReportTests

   Ověří názvy souborů, provedené operace, publikaci a hlášení selhání.

   **Metody:**

   .. py:method:: setUp()

      Připraví dočasný adresář testu s úklidem spravovaným unittestem.

   .. py:method:: assert_shared_reports()

      Ověří stejné údaje a seznam změn v každém ze tří výstupů.

      :param record: Snapshot testovaného běhu použitý k vykreslení všech reportů.

   .. py:method:: test_modified_added_deleted_renamed_and_binary_paths()

      Protokol Gitu s NUL zachová názvy a obě strany přejmenování.

   .. py:method:: test_real_index_snapshot_survives_commit()

      Report po publikaci stále obsahuje přesně index před commitem.

   .. py:method:: test_all_surfaces_share_documentation_only_changes()

      PR pouze s dokumentací nesmí tvrdit změny pinů, formátování či kontejnerů.

   .. py:method:: test_pins_and_docs_are_both_reported()

      Report zahrne soubory z obou fází společného zpracování.

   .. py:method:: test_no_changes_and_skipped_documentation()

      Provedení operace neznamená, že změnila soubor.

   .. py:method:: test_publication_failure_and_unresolved_hooks()

      Publikace změn nesmí skrytě převést selhané kontroly na úspěšné.

   .. py:method:: test_processing_failure_has_no_success_or_published_claim()

      Selhání kompilace je odlišeno od úspěšného prázdného diffu.

   .. py:method:: test_processing_failure_does_not_capture_partial_changes()

      Selhání před stage nesmí nabídnout částečně zpracované soubory.

   .. py:method:: test_check_command_fails_for_processing_hooks_and_publication()

      Požadovaný check selže při každém sledovaném typu selhání.

   .. py:method:: test_markdown_paths_and_diagnostics_cannot_close_fences()

      Nedůvěryhodné názvy a logy zůstanou ve všech reportech doslovné.


Funkce
------

.. py:function:: record_fixture()

   Připraví dokončený běh bez služeb Gitu nebo GitHubu.

   :return: Snapshot úspěšného běhu bez změn, diagnostiky a opravného PR.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_pre_commit_report.py
   :language: python
   :linenos:
