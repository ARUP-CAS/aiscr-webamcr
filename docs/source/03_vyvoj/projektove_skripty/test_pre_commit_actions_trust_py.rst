Skript test_pre_commit_actions_trust.py
=======================================

Automaticky generovaná dokumentace skriptu ``scripts/test_pre_commit_actions_trust.py``.

Přehled modulu
--------------

Ověří neměnné odkazy na GitHub Actions a zachování jejich aktualizací.

Třídy
------

.. py:class:: ActionReferenceTests

   Záměrně poškodí odkazy a ověří odmítnutí i přesnou diagnostiku.

   **Metody:**

   .. py:method:: workflow()

      Sestaví malý workflow s jedním krokem.

      :param reference: Testovaný obsah položky ``uses``.
      :param comment: Text za odkazem na stejném řádku.
      :return: Zdroj YAML se známým číslem řádku volání.

   .. py:method:: test_rejects_mutable_or_malformed_references()

      Tagy, větve, zkrácené či nehexadecimální SHA musí selhat.

   .. py:method:: test_requires_full_release_comment()

      Samotné SHA a komentáře bez úplné verze nejsou přijaty.

   .. py:method:: test_accepts_pins_subpaths_quoted_values_and_local_calls()

      Podporuje subpath akcí, uvozovky i lokální reusable workflow.

   .. py:method:: test_ignores_comments_and_shell_uses_text()

      Zakomentované kroky a podobný text v shellu nejsou závislosti.

   .. py:method:: test_reusable_workflow_jobs_are_checked()

      Externí reusable volání nezmizí při kontrole pouze kroků.

   .. py:method:: test_flow_mapping_comment_is_not_a_quoted_string()

      Verze v jiném řetězci nenahradí skutečný komentář vydání.

   .. py:method:: test_repository_action_references()

      Zkontroluje aktivní volání ve všech YAML workflow repozitáře.

   .. py:method:: test_shared_flow_comment_is_rejected_for_steps_and_reusable_jobs()

      Jeden komentář nesmí označit verzi dvou odlišných volání na řádku.

   .. py:method:: test_duplicate_mapping_keys_fail_before_reference_traversal()

      Duplicitní uses, jobs ani steps nesmí skrýt druhou závislost.

   .. py:method:: test_dependabot_update_contract()

      Zachová týdenní aktualizace do test a obě existující skupiny.

   .. py:method:: test_registry_covers_retained_third_party_actions()

      Nová third-party závislost bez záznamu registru neprojde kontrolou.

   .. py:method:: test_retained_scanning_and_signing_calls()

      Převod pinů zachová dvě Trivy volání a instalátor Cosign.


.. py:class:: SSHTestCase

   Připraví izolované prostředí pro skutečný agent a náhrady síťových operací.

   **Metody:**

   .. py:method:: setUp()

      Připraví dočasný klíč a náhrady pouze vzdálených operací.

   .. py:method:: write_tool()

      Vytvoří klienta, který místo síťového připojení ověří identitu agenta.

      :param name: Název příkazu v izolovaném PATH.
      :param body: Shellové tělo testovací náhrady.

   .. py:method:: run_shell()

      Spustí shell bez zděděného uživatelského agenta a vzdálené sítě.

      :param script: Skutečný blok workflow nebo kontrolní shellový příkaz.
      :param values: Proměnné předané pouze tomuto testovacímu kroku.
      :return: Výsledek procesu s odděleným stdout a stderr.

   .. py:method:: release_agent()

      Ukončí pouze testem vytvořený agent i při selhání assertion.

   .. py:method:: agent_environment()

      Načte proměnné, které by GitHub přenesl do samostatného kroku.

      :return: Socket a PID načtené ze skutečného souboru GITHUB_ENV.

   .. py:method:: workflow_script()

      Izoluje known_hosts a nahradí vstupy bez změny řízení SSH kroku.

      :param script: Zdroj shellového kroku se vstupy GitHub Actions.
      :return: Blok workflow se syntetickým hostem a dočasnou cestou known_hosts.

   .. py:method:: assert_agent_stopped()

      Ověří nedostupnost zaznamenaného socketu po skutečném úklidu.


.. py:class:: SSHAgentTests

   Spustí skutečný agent a shell workflow s izolovanými SSH/SCP klienty.

   **Metody:**

   .. py:method:: test_identity_survives_ssh_and_scp_steps_then_cleanup()

      Klíč s CRLF funguje pro SSH a obě SCP volání bez opětovného načtení.

   .. py:method:: test_invalid_key_fails_without_persisting_or_logging_it()

      Neplatný klíč zastaví inicializaci a trap odstraní vytvořený agent.

   .. py:method:: test_cleanup_after_remote_or_result_failure()

      Stejný always cleanup ukončí agent po chybě SSH i SCP.

   .. py:method:: test_cleanup_is_safe_when_setup_did_not_run()

      Chyba VPN před inicializací nesmí poškodit cizí agent.


.. py:class:: SummaryResultTests

   Ověří skutečné zpracování vzdáleného souhrnu bez spuštění jeho obsahu.

   **Metody:**

   .. py:method:: setUp()

      Připraví agenta a SCP, které kopíruje přesné bajty testovacího souhrnu.

   .. py:method:: execute_result()

      Stáhne souhrn a spustí nezměněné tělo výsledkového kroku.

      :param content: Bajty simulovaného vzdáleného souboru.
      :return: Výsledek skutečného shellu s izolovanými SCP operacemi.

   .. py:method:: assert_summary_rejected()

      Ověří neúspěch bez spuštění canary a bez částečně zapsaného výsledku.

      :param content: Neplatné bajty souhrnu předané skutečnému kroku.
      :return: Neúspěšný výsledek shellu pro následnou kontrolu úklidu.

   .. py:method:: test_valid_counts_preserve_reporting_and_normalize_decimal_outputs()

      Pořadí, konce řádků i úvodní nuly zachovají číselné výsledky a tabulku.

   .. py:method:: test_malformed_or_binary_summaries_leave_existing_results_untouched()

      Chybějící, duplicitní, neznámé a nečíselné záznamy selžou celé.

   .. py:method:: test_commands_and_substitutions_cannot_run_or_publish_partial_counts()

      Příkazy připojené k platným počtům ani substituce nespustí canary.

   .. py:method:: test_summary_rejection_still_allows_unconditional_agent_cleanup()

      Neúspěšné čtení výsledků ponechá always úklidu možnost ukončit agenta.


.. py:class:: DeploymentAgentTests

   Ověří omezení klíče a celý životní cyklus agenta v jediném deployment kroku.

   **Metody:**

   .. py:method:: test_deployment_key_is_step_scoped_and_agent_stops_on_every_exit()

      Úspěch, chyba SSH i neplatný klíč zachovají výsledek a uvolní agent.


.. py:class:: WorkflowInputTests

   Spustí validaci a dvě shellové interpretace transportu bez připojení k serveru.

   **Metody:**

   .. py:method:: setUp()

      Nahradí vzdálený host lokálním POSIX shellem a zaznamená argumenty příkazů.

   .. py:method:: operations()

      Načte záznamy s NUL oddělovači, které zachovávají i uvozovky a nové řádky.

      :return: Dvojice názvu operace a původních argumentů v pořadí volání.

   .. py:method:: test_validation_precedes_connection_and_uses_the_same_input_environment()

      Konfigurace nepředá neveřejné vstupy do zdroje shellu a validuje před VPN.

   .. py:method:: test_tag_normalization_preserves_valid_releases_and_rejects_shell_syntax()

      Tagy se normalizují jako data a škodlivý obsah se nevykoná před kontrolou.

   .. py:method:: test_invalid_test_inputs_stop_before_remote_execution()

      Neplatné režimy, boolean a čísla ukončí workflow před spuštěním SSH.

   .. py:method:: test_all_modes_and_optional_deployment_keep_their_remote_arguments()

      Skutečný vzdálený skript obdrží všechny argumenty a zachová tři režimy testů.

   .. py:method:: test_reference_names_are_literal_through_both_shells()

      Uvozovky a substituce ve validním názvu reference zůstanou jediným argumentem.

   .. py:method:: test_deployment_transport_preserves_source_and_tag_arguments()

      Deployment předá normalizovaný tag a oba zdroje beze změny přes vzdálený shell.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_pre_commit_actions_trust.py
   :language: python
   :linenos:
