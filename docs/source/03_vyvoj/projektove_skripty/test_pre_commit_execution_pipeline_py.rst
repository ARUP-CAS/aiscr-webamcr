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

   .. py:method:: setUp()

      Připraví skutečné procesy a agent, provozní příkazy však zůstanou náhradami.

   .. py:method:: test_full_attempt_chain_and_failure_matrix()

      Provede reálnou cestu a ověří přípravu, stavy, identitu, artefakty i cleanup.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_pre_commit_execution_pipeline.py
   :language: python
   :linenos:
