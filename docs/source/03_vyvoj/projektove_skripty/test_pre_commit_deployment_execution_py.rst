Skript test_pre_commit_deployment_execution.py
==============================================

Automaticky generovaná dokumentace skriptu ``scripts/test_pre_commit_deployment_execution.py``.

Přehled modulu
--------------

Regrese skutečných nasazovacích skriptů s úplnou náhradou provozních příkazů.

Třídy
------

.. py:class:: DeploymentExecutionTests

   Ověří statusy a bookkeeping bez skutečného Dockeru, Git změn či serveru.

   **Metody:**

   .. py:method:: setUp()

      Zkopíruje skripty do dočasné kořenové složky a nahradí provozní nástroje.

   .. py:method:: tool()

      Zapíše pouze lokální náhradu příkazu do izolovaného PATH.

      :param name: Název nástroje.
      :param body: Bezpečné tělo náhrady.

   .. py:method:: execute()

      Spustí reálný zkopírovaný skript v bezpečném prostředí.

      :param script: Cesta skriptu pod scripts.
      :param args: Jeho argumenty.
      :param previous_tag: Připravit existující záznam předchozího nasazení.
      :param stdin: Volitelná odpověď na výzvu skriptu.
      :param values: Stav simulovaných příkazů.
      :return: Výsledek procesu.

   .. py:method:: test_required_build_pull_removal_and_deployment_failures_propagate()

      Neúspěch nelze přepsat zprávou o dokončení ani koncovým exit 0.

   .. py:method:: test_swarm_diagnostic_and_shared_dependency_are_required()

      Chyba Swarmu vypíše příčinu a chybějící pomocný soubor zastaví nasazení.

   .. py:method:: test_wrapper_log_rotation_is_bounded_and_preserves_current_log()

      Oba wrappery odstraní pouze staré přímé deployment logy a zachovají tag.

   .. py:method:: test_ci_wrappers_preserve_failure_and_previous_tag()

      Při chybě nasazení se nepustí readiness ani nezmění poslední úspěšný tag.

   .. py:method:: test_ci_wrappers_create_logs_on_first_deployment()

      První nasazení vytvoří logy před jejich úklidem i bez předchozího tagu.

   .. py:method:: test_clone_and_readiness_failure_preserve_previous_tag()

      Klonování a konečná kontrola jsou povinné, jejich chyby zůstanou chybami.

   .. py:method:: test_stack_removal_preserves_command_order_and_distinct_statuses()

      Existence, absence a obě chyby zachovají příkazy, čekání a návratový kód.

   .. py:method:: test_optional_compaction_failure_remains_nonfatal()

      Chyba volitelné kompakce zůstane varováním při úspěšném nasazení.

   .. py:method:: test_web_container_lookup_guards_clone_and_test_launch()

      Oba vstupy spustí podřízený příkaz jen s právě jedním kontejnerem.

   .. py:method:: test_invalid_test_deploy_options_stop_before_docker()

      Neplatný přepínač selže i za platným přepínačem bez účinků Dockeru.

   .. py:method:: test_test_deploy_supported_modes_and_order_remain_intact()

      Výchozí, explicitní a tichý build i pořadí akcí zůstanou platné.

   .. py:method:: assert_no_deployment_setup()

      Ověří, že nevznikly logy, záloha ani záznam o provozním příkazu.

   .. py:method:: test_test_deploy_help_validates_before_operational_setup()

      Platná nápověda funguje bez Swarmu, neplatný požadavek předem selže.

   .. py:method:: test_production_tagged_deployment_and_update_still_execute()

      Produkční -t a -u použijí tag při nasazení a výměně služeb.

   .. py:method:: test_production_invalid_request_stops_before_setup()

      Chybný argument zastaví celý požadavek i za platnou operací.

   .. py:method:: test_production_help_validates_before_setup()

      Nápověda má přednost před platnými operacemi, ne před validací.

   .. py:method:: test_production_operation_order_tag_selection_and_guidance()

      Pořadí operací, společný tag i pokyny bez voleb zůstanou zachovány.

   .. py:method:: test_test_wrapper_propagates_identity_modes_and_child_failure()

      Předání identity a script --return zachovají selhání všech režimů.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_pre_commit_deployment_execution.py
   :language: python
   :linenos:
