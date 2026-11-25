Skript test_pre_commit_execution_pipeline.py
============================================

Automaticky generovaná dokumentace skriptu ``scripts/test_pre_commit_execution_pipeline.py``.

Přehled modulu
--------------

Integrovaný lokální průchod workflow, nasazením, runnerem a čtením výsledků.

Třídy
------

.. py:class:: ExecutionPipelineTests

   Spojí skutečné skripty a producer/consumer s náhradou služeb a manage.py.

   **Metody:**

   .. py:method:: route_docker_exec()

      Přesměruje právě jednu větev izolovaného Dockeru do testovacího runneru.

      :param docker: Zdroj skutečné náhrady Dockeru z deployment fixture.
      :return: Stejná náhrada s jedinou přesměrovanou větví.

   .. py:method:: setUp()

      Připraví skutečné procesy a agent, provozní příkazy však zůstanou náhradami.

   .. py:method:: guarded_shell()

      Ověří izolaci nástrojů před lokálním i emulovaným vzdáleným krokem.

      :param script: Skutečný blok workflow.
      :param values: Proměnné izolovaného pokusu.
      :return: Výsledek shellového kroku.

   .. py:method:: test_docker_stub_drift_fails_at_setup()

      Chybějící či opakovaná větev zastaví přípravu místo pozdějšího selhání.

   .. py:method:: test_missing_unexecutable_and_shadowed_stubs_stop_before_commands()

      Nefunkční náhrada nesmí propustit lokální ani vzdálený provozní příkaz.

   .. py:method:: test_full_attempt_chain_and_failure_matrix()

      Provede reálnou cestu a ověří přípravu, stavy, identitu, artefakty i cleanup.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_pre_commit_execution_pipeline.py
   :language: python
   :linenos:
