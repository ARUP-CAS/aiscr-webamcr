Skript test_deploy_readiness.py
===============================

Automaticky generovaná dokumentace skriptu ``scripts/test_deploy_readiness.py``.

Přehled modulu
--------------

Izolované testy připravenosti nasazení a předání chyb.

Třídy
------

.. py:class:: DeploymentReadinessTest

   Spouští wrapper s náhradami všech vnějších operací.

   **Metody:**

   .. py:method:: setUp()

      Připraví izolovaný adresář nasazení a náhradní příkazy.

   .. py:method:: run_wrapper()

      Spustí wrapper s náhradami a krátkým limitem čekání.

      :param scenario: Simulovaný stav služby a kontejneru.
      :param failure: Případné selhání předběžného kroku.
      :return: Výsledek podprocesu s návratovým kódem a výstupem.

   .. py:method:: test_healthy_new_candidate_records_tag()

      Zdravý nový kandidát se zaznamená jako poslední úspěšná verze.

   .. py:method:: test_missing_unhealthy_stale_and_wrong_candidates_preserve_tag()

      Neověřený nebo nesprávný kandidát předchozí verzi nepřepíše.

   .. py:method:: test_failed_prerequisites_preserve_tag()

      Selhání předběžného kroku ponechá předchozí úspěšnou verzi.


.. py:class:: DeploymentHelperFailureTest

   Ověří předání chyb nasazovacího pomocníka bez použití Dockeru.

   **Metody:**

   .. py:method:: setUp()

      Připraví izolovaný adresář a náhrady příkazů.

   .. py:method:: run_helper()

      Spustí pomocný skript s nastaveným simulovaným selháním.

      :param failure: Typ chyby, kterou má náhradní Docker vrátit.
      :param arguments: Argumenty nasazovacího skriptu.
      :return: Výsledek podprocesu s návratovým kódem a výstupem.

   .. py:method:: test_remove_failure_is_nonzero()

      Chyba odstranění stacku vrátí nenulový kód.

   .. py:method:: test_network_pull_and_deploy_failures_are_nonzero()

      Chyby sítě, stažení a nasazení se předají volajícímu.

   .. py:method:: test_success_remains_zero()

      Úspěšné nasazení zachová nulový návratový kód.


.. py:class:: WebImagePolicyGateTest

   Ověří umístění kontroly matice v sestavovaném runtime obrazu.

   **Metody:**

   .. py:method:: test_runtime_checks_packaged_application_before_publication()

      Runtime vrstva spouští kontrolu po kopírování aplikace a před startem.


Funkce
------

.. py:function:: executable(path, content)

   Vytvoří náhradní příkaz v izolovaném dočasném adresáři.

   :param path: Cesta k vytvořenému souboru.
   :param content: Tělo náhradního shellového příkazu.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_deploy_readiness.py
   :language: python
   :linenos:
