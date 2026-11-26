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
      :param deadline: Termín inspekce, který volání zaznamená k ověření.
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

   .. py:method:: test_deadline_is_passed_explicitly_to_every_inspection()

      Termín z čekání dostane každý příkaz a samostatné volání žádný stav nezdědí.


.. py:class:: Python36CompatibilityTests

   Ověří spodní hranici Pythonu 3.6, se kterou skript běží na nasazovacím serveru.

   **Metody:**

   .. py:method:: test_script_uses_only_python36_grammar_modules_and_run_arguments()

      Skutečný skript projde kontrolou a obsahuje kontrolované volání subprocess.run.

   .. py:method:: test_guard_rejects_later_modules_and_run_arguments()

      Kontrola zachytí konstrukce, které na Pythonu 3.6 selžou při importu nebo volání.

   .. py:method:: test_guard_rejects_later_grammar()

      Syntaxe novější než Python 3.6, kterou ast rozpozná, selže už při parsování.


Funkce
------

.. py:function:: python36_violations(source)

   Najde konstrukce, které systémový Python 3.6 nasazovacího serveru nespustí.

   Gramatiku kontroluje ``ast.parse`` s ``feature_version=(3, 6)``. Podle
   dokumentace modulu ``ast`` jde o přibližnou kontrolu a novější interprety
   ji omezují na nejstarší gramatiku, kterou ještě podporují; odmítne tak
   například přiřazovací výrazy, parametry jen pozičně nebo ``match``.
   Importy musí patřit do ``PYTHON36_MODULES`` a volání ``subprocess.run``
   (i přes alias modulu nebo ``from subprocess import run``) smí používat jen
   parametry z ``PYTHON36_RUN_KEYWORDS`` bez rozbalení ``**``.

   :param source: Zdrojový text kontrolovaného skriptu.
   :return: Dvojice seznamu diagnostik ve tvaru ``řádek: popis`` a počtu
       zkontrolovaných volání ``subprocess.run``.
   :raises SyntaxError: Při syntaxi, kterou ``ast`` pro Python 3.6 odmítne.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_pre_commit_stack_ready.py
   :language: python
   :linenos:
