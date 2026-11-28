Skript test_pre_commit_workflow.py
==================================

Automaticky generovaná dokumentace skriptu ``scripts/test_pre_commit_workflow.py``.

Přehled modulu
--------------

Ověří rozhodování workflow a publikační skripty s neaktivními testovacími službami.

Třídy
------

.. py:class:: BashDiscoveryTests

   Nalezení interpretu funguje i mimo výchozí instalaci Gitu.

   **Metody:**

   .. py:method:: test_git_relative_fallback_unavailable_and_linux()

      Ověří alternativní Git, PATH, odmítnutí WSL a běžný linuxový Bash.


.. py:class:: WorkflowTests

   Ověří skutečný shell a JavaScript místo kopie jejich rozhodovacích pravidel.

   **Metody:**

   .. py:method:: setUp()

      Připraví dočasný adresář testu a ověří dostupnost Bashe.

   .. py:method:: run_shell()

      Spustí skutečný shellový blok workflow v dočasném adresáři.

      :param script: Shellový blok načtený z workflow nebo doplněný testovacími náhradami služeb.
      :param values: Proměnné prostředí přepisující hodnoty pro daný testovací běh.
      :return: Výsledek subprocess s návratovým kódem, standardním výstupem a chybovým výstupem.

   .. py:method:: gate()

      Vyhodnotí režim a zachová čitelný důvod vyloučení.

      :param values: Proměnné události, autora, větví a ručního režimu přepisující výchozí PR do test.
      :return: Slovník výstupů rozhodovacího kroku včetně ``mode``, ``run`` a ``full``.

   .. py:method:: test_automatic_events_and_manual_choices()

      Piny obnoví jen release PR test → main; jiné PR a push do main obnoví dokumentaci bez upgradu.

   .. py:method:: test_release_dependabot_and_generated_branches_remain_noops()

      Lidské aktualizace a ruční výběr nemohou obejít vyloučení automatiky.

   .. py:method:: test_invalid_manual_mode_fails()

      Klienti CLI/API nemohou neúmyslně zvolit nedefinovaný režim.

   .. py:method:: test_compile_script_receives_upgrade_only_in_refresh_mode()

      Ověří skutečný kompilační blok bez spouštění Dockeru či přístupu k PyPI.

   .. py:method:: test_workflow_order_source_ref_and_publication_guards()

      Workflow používá obnovené soubory, zachytí je po hookách a znovu nestageuje.

   .. py:method:: test_hook_log_tail_reaches_capture_and_keeps_last_eighty_lines()

      Skutečný hook shell předá posledních osmdesát řádků i původní kód selhání.

   .. py:method:: publication_fixture()

      Shellové funkce zajistí, že publikace neprovede skutečný zápis do Gitu či GitHubu.

      :param existing: Číslo existujícího opravného PR nebo prázdný řetězec pro vytvoření nového.
      :param fail: Hodnota ``1`` simuluje selhání vytvoření PR; ``0`` ponechá publikaci úspěšnou.
      :param base: Cílová větev simulovaného opravného PR.
      :param is_pr: Řetězec ``true`` pro PR událost nebo ``false`` pro push či ruční běh.
      :return: Výsledek publikačního shellu se zaznamenanými voláními testovacích služeb.

   .. py:method:: test_publisher_creates_then_updates_without_new_branch_identity()

      Opakované běhy upraví existující PR a předají jeho URL reportům.

   .. py:method:: test_publication_failure_does_not_claim_a_fix_pr_url()

      Selhané vytvoření PR nesmí být hlášeno jako úspěšná publikace.

   .. py:method:: test_push_and_manual_publications_target_the_triggering_branch()

      Push na main a ruční běh publikují opravu do větve svého spuštění.

   .. py:method:: test_sticky_comment_updates_existing_bot_comment_or_creates_one()

      Spustí skutečný github-script se stránkováním komentářů a neaktivními zápisy.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_pre_commit_workflow.py
   :language: python
   :linenos:
