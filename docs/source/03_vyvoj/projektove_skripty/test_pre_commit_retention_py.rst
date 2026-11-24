Skript test_pre_commit_retention.py
===================================

Automaticky generovaná dokumentace skriptu ``scripts/test_pre_commit_retention.py``.

Přehled modulu
--------------

Regrese omezené historie, živých zámků a hranic mazání výstupu testů.

Třídy
------

.. py:class:: RetentionTests

   Maže pouze vlastní dočasné adresáře; externí data chrání canary.

   **Metody:**

   .. py:method:: setUp()

      Připraví explicitní soukromý kořen všech testovacích dat.

   .. py:method:: attempt()

      Založí vlastní pokus a případně publikuje terminální stav.

      :param identity: Identita pokusu.
      :param state: Terminální stav nebo None pro přerušený pokus.
      :return: Adresář pokusu.

   .. py:method:: age()

      Nastaví stáří pouze vlastnímu adresáři a jeho souborům.

      :param directory: Vlastní dočasný pokus.
      :param timestamp: Požadovaný čas poslední aktivity.

   .. py:method:: test_latest_ten_finished_attempts_include_failures_and_noops()

      Normální, neúspěšné i prázdné terminální pokusy sdílí limit deseti.

   .. py:method:: test_thirty_day_boundary_and_unknown_ownership()

      Přerušené pokusy vyžadují třicet dní i ověřené neaktivní vlastnictví.

   .. py:method:: test_active_old_attempt_is_protected_across_processes()

      Skutečný zámek jiného procesu chrání i pokus starší než třicet dní.

   .. py:method:: test_current_attempt_is_protected_and_cleanup_failure_is_visible()

      Aktuální pokus se nemaže; chyba mazání zachová data a vrátí neúspěch.

   .. py:method:: test_symlinks_and_reparse_points_cannot_remove_external_canary()

      Odkaz uvnitř kandidáta ani odkaz místo kandidáta neopustí kořen.

   .. py:method:: test_runner_retention_failure_preserves_nonzero_and_original_test_failure()

      Chyba retence nezaloží úspěch ani nepřepíše původní neúspěšné počty.

   .. py:method:: test_legacy_terminal_history_is_recognized_without_accepting_old_counts()

      Vlastněný terminální záznam verze 1 lze uklidit při migraci historie.

   .. py:method:: test_redirected_runs_or_lease_root_is_rejected()

      Junction nebo symlink v hranici úložiště zabrání práci s cizí cestou.

   .. py:method:: test_unrelated_and_invalid_terminal_data_remain_intact()

      Neznámý adresář či poškozená metadata nezískají oprávnění k mazání.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_pre_commit_retention.py
   :language: python
   :linenos:
