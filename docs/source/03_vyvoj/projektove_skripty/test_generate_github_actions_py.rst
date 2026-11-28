Skript test_generate_github_actions.py
======================================

Automaticky generovaná dokumentace skriptu ``scripts/test_generate_github_actions.py``.

Přehled modulu
--------------

Regresní testy inventáře GitHub Actions ve společném generátoru dokumentace.

Třídy
------

.. py:class:: GitHubActionsInventoryTests

   Ověří změny vstupů, selhání a zachování ručně psané části stránky.

   **Metody:**

   .. py:method:: setUp()

      Připraví izolovaný projekt bez síťových služeb a aplikace Django.

   .. py:method:: write_workflow()

      Zapíše malý platný workflow s odkazem na známém řádku.

      :param name: Název souboru ve složce workflow.
      :param action: Externí cesta akce včetně případného podadresáře.
      :param commit: Revize použitá v položce ``uses``.
      :param version: Verze v komentáři téhož řádku.
      :return: Cesta zapsaného workflow.

   .. py:method:: generate()

      Obnoví inventář a vrátí výsledný text pro obsahové kontroly.

      :return: Úplný obsah stránky po úspěšném vygenerování.

   .. py:method:: test_inventory_includes_versions_owners_sources_and_distinct_workflow_locations()

      Sdruží stejné vydání a zachová rozdílné verze i podadresáře akcí.

   .. py:method:: inventory_rows()

      Přečte úplné řádky výstupu nezávisle na produkčním průchodu workflow.

      :param text: Vygenerovaná stránka obsahující označený inventář.
      :return: Akce, vlastníci, verze, commity a umístění v pořadí tabulky.

   .. py:method:: test_exact_inventory_includes_external_reusable_jobs_and_excludes_local_calls()

      Pevná očekávání odhalí chybějící reusable volání, neočekávané i duplicitní řádky.

   .. py:method:: test_additions_removals_and_updates_replace_stale_rows()

      Nové i odstraněné workflow změní seznam a nezachovají staré piny.

   .. py:method:: test_local_calls_comments_and_shell_text_are_excluded()

      Lokální volání a text mimo skutečné ``uses`` nevytvoří řádky.

   .. py:method:: test_generation_preserves_authored_sections_and_is_idempotent()

      Druhý běh nemění soubor ani autorský text mimo značky.

   .. py:method:: test_empty_inventory_removes_obsolete_entries()

      Odstranění poslední externí akce nenechá v tabulce starou závislost.

   .. py:method:: test_invalid_reference_fails_without_overwriting_documentation()

      Mutabilní odkaz selže s umístěním ještě před přepsáním inventáře.

   .. py:method:: test_malformed_yaml_reports_its_source()

      Chyba YAML obsahuje soubor a nevytváří nový inventář.

   .. py:method:: test_ambiguous_comments_and_duplicate_keys_preserve_existing_inventory()

      Chybné komentáře ani duplicitní struktura nepřepíší poslední platnou stránku.

   .. py:method:: test_non_scalar_and_multiline_uses_are_rejected()

      Seznam ani víceřádkový scalar neobchází kontrolu pinu a komentáře.

   .. py:method:: test_standard_pre_commit_entry_runs_inventory_and_reports_changes()

      Skutečný vstup generátoru zapojený v hooku vrací 1 při změně a 0 po obnově.

   .. py:method:: test_existing_ci_discovers_dependency_generation_tests()

      Sdílený CI job spouští Actions i JavaScript testy bez zvláštního workflow.

   .. py:method:: test_repository_workflows_refresh_a_stale_inventory()

      Skutečné workflow obnoví zastaralou kopii stránky před běžným CI autofixem.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_generate_github_actions.py
   :language: python
   :linenos:
