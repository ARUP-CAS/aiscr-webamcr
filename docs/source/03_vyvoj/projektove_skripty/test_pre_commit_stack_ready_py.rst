Skript test_pre_commit_stack_ready.py
=====================================

Automaticky generovaná dokumentace skriptu ``scripts/test_pre_commit_stack_ready.py``.

Přehled modulu
--------------

Regrese připravenosti stacku s nezávislými JSON odpověďmi Docker CLI.

Třídy
------

.. py:class:: StackReadinessTests

   Ověří zdraví, požadované úlohy, výjimky a selhání čtecích příkazů.

   **Metody:**

   .. py:method:: setUp()

      Připraví minimální kompletní odpovědi jednoho stacku.

   .. py:method:: docker()

      Vrátí jen očekávané čtecí odpovědi, jiné volání odmítne.

      :param args: Argumenty kontrolovaného příkazu.
      :return: Odpověď Docker CLI.

   .. py:method:: test_ready_target_ignores_unrelated_containers()

      Kontrola nevyhledává ani nezahrnuje cizí nezdravé kontejnery.

   .. py:method:: test_starting_unhealthy_and_stopped_are_unready()

      Shodný počet replik nestačí při nezdravém nebo zastaveném kontejneru.

   .. py:method:: test_missing_services_tasks_replicas_and_running_state_fail()

      Prázdná inspekce nebo neúplné repliky nikdy nezaloží připravenost.

   .. py:method:: test_expected_zero_replicas_and_completed_jobs_are_ready()

      Deklarovaná nula a dokončená jednorázová úloha jsou záměrné výjimky.

   .. py:method:: test_inspection_errors_empty_config_and_bad_json_fail()

      Chybující příkaz ani neplatný JSON nesmí být prázdným zdravým výsledkem.

   .. py:method:: test_timeout_rollout_failure_and_no_healthcheck()

      Čekání má konec, rollback není úspěch a absence healthchecku je přípustná.

   .. py:method:: test_stuck_inspection_respects_the_same_deadline()

      Zablokovaný Docker CLI má časový limit, který nepřekročí celkové čekání.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_pre_commit_stack_ready.py
   :language: python
   :linenos:
