CRON tasks
==========

Modul tasks.

Třídy
------

.. py:class:: SouborMissingRepositoryUuidError

   Vyvoláno při pokusu o UPDATE binárního souboru, jehož ``repository_uuid`` je None.

   Indikuje poškozená data: záznam ``Soubor`` existuje v DB, ale nemá přiřazený
   Fedora UUID, tedy binární soubor v repositáři neexistuje nebo nebyl nikdy nahrán.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param soubor_pk: Primární klíč záznamu ``Soubor`` s chybějícím ``repository_uuid``.
      :param nazev: Název souboru, u nějž chybí ``repository_uuid``.


.. py:class:: ImportLockLostError

   Vyvoláno, když ``refresh_import_lock`` zjistí, že importní lock byl ztracen.

   Použito jako sentinel, aby vnější ``except Exception`` v ``run_data_import`` mohl
   rozlišit ztrátu zámku od ostatních selhání během importu dat a nepřepsal
   konkrétní status message ``failed_lock_lost``.


Funkce
------

.. py:function:: send_notifications_enz()

   Každý den zkontrolovat a případně odeslat upozornění uživatelům na základě pole projekt.datum_odevzdani_NZ,

   pokud je projekt ve stavu <P5 a zároveň:
   -- pokud [dnes] + 90 dní = datum_odevzdani_NZ => email E-NZ-01
   -- pokud [dnes] - 1 den = datum_odevzdani_NZ => email E-NZ-02

.. py:function:: send_notification_enz03()

   Kontrola a odeslání emailů E-NZ-03 pro akce čekající na archivaci déle než 90 dní.

.. py:function:: send_notifications_en()

   Každý den kontrola a odeslání emailů E-N-01 a E-N-02

.. py:function:: delete_personal_data_canceled_projects()

   Rok po zrušení projektu nahradit související údaje v tabulce oznamovatel řetězcem “RRRR-MM-DD: údaj odstraněn”,

   kromě pole projekt.oznamovatel + odstranit projektovou dokumentaci a vytvořit log (jako při archivaci projektu).

.. py:function:: delete_reporter_data_ten_years()

   Deset let po zápisu projektu smazat související záznam z tabulky oznamovatel + odstranit projektovou dokumentaci

   a vytvořit log (jako při archivaci projektu).

.. py:function:: change_document_accessibility()

   Každý den změnit přístupnost dokumentů, u kterých datum_zverejneni<=[dnes], a to na přístupnost stanovenou

   v hesláři organizace (podle vazby dokument.organizace), ale nikdy ne na vyšší přístupnost, než má nejlépe
   přístupný připojený archeologický záznam (tj. když mají připojené AZ C a D, bude mít dokument nejvýše C).

.. py:function:: delete_unsubmited_projects()

   Každý den smazat projekty ve stavu -1, které vznikly před více než 12 hodinami.

.. py:function:: cancel_old_projects()

   Každý den převést na P8 projekty v P1 starší tří let, které mají plánované datum zahájení více než rok

   v minulosti. Do poznámky ke zrušení uvést “Automatické zrušení projektů starších tří let, u kterých již
   nelze očekávat zahájení.”

.. py:function:: update_snapshot_fields()

   Aktualizuje snapshot fields.

.. py:function:: update_all_redis_snapshots(rewrite_existing, classes)

   Aktualizuje Redis snapshots pro všechny nebo vybrané třídy modelů.

   :param rewrite_existing: Pokud je ``True``, přepíše i existující záznamy v Redis. Výchozí hodnota je ``False``.
   :param classes: Volitelný seznam tříd modelů, pro které se mají Redis snapshot záznamy aktualizovat.
       Pokud není zadán, použijí se výchozí třídy
       (Akce, Projekt, Dokument, Lokalita, ExterniZdroj, UzivatelSpoluprace, SamostatnyNalez).

.. py:function:: update_single_redis_snapshot(class_name, record_pk)

   Aktualizuje single redis snapshot.

   :param class_name: Parametr ``class_name`` předává se do volání ``error()``, ovlivňuje větvení podmínek.
   :param record_pk: Identifikátor ``record_pk`` používaný pro dohledání cílového záznamu.

.. py:function:: update_materialized_views()

   Aktualizuje materialized views.

.. py:function:: write_value_to_redis(key, value)

   Zapíše value to redis.

   :param key: Textový název nebo klíč ``key`` používaný v rámci operace.
   :param value: Parametr ``value`` předává se do volání ``set()``, vstupuje do návratové hodnoty.

   :return: Vrací n-tici.

.. py:function:: call_digiarchiv_update_task()

   Zavolá URL digiarchívu pro spuštění aktualizace dat.

.. py:function:: run_data_import(job_id, user_id, lock_token)

   Spustí data import.

   :param job_id: Identifikátor objektu ``job``.
   :param user_id: Identifikátor objektu ``user``.
   :param lock_token: Token pro ověření vlastnictví importního zámku v Redis.

   Možné hodnoty Redis klíče ``import_data_status_message_{job_id}``:

   .. list-table::
       :header-rows: 1
       :widths: 35 65

       * - Hodnota stavu
         - Situace, kdy se stav nastaví
       * - ``cron.tasks.run_data_import.failed_lock_lost``
         - Import už běžel, ale při obnově Redis locku se zjistí, že task lock ztratil.
       * - ``cron.tasks.run_data_import.failed_lock_acquisition``
         - Task na začátku nezíská nebo neobnoví importní lock, takže import nepokračuje.
       * - ``cron.tasks.run_data_import.importing_record_data {n}/{total}``
         - Během hlavní fáze importu dat, před zpracováním jednotlivého záznamu.
       * - ``cron.tasks.run_data_import.stopped_by_user``
         - Uživatel zastavil import přes ``import_data_stop_{job_id}``.
       * - ``cron.tasks.run_data_import.failed_during_data_import``
         - Selže zpracování datového záznamu, databázová transakce nebo hlavní fáze importu dat.
       * - ``cron.tasks.run_data_import.creating_history_records``
         - Hlavní import dat doběhl bez chyby a začíná fáze vytváření historie.
       * - ``cron.tasks.run_data_import.creating_history_records {n}/{total}``
         - Během fáze historie, před vytvořením konkrétního historického záznamu.
       * - ``cron.tasks.run_data_import.failed_during_history``
         - Selže vytvoření některého záznamu historie.
       * - ``cron.tasks.run_data_import.updating_fedora_records``
         - Historie doběhla bez chyby a začíná fáze aktualizace Fedora metadat.
       * - ``cron.tasks.run_data_import.updating_fedora_records {n}/{total}``
         - Během aktualizace jednotlivých Fedora záznamů.
       * - ``cron.tasks.run_data_import.failed_during_fedora``
         - Selže uložení metadat do Fedory pro některý z dotčených záznamů.
       * - ``cron.tasks.run_data_import.finalizing``
         - Fedora fáze doběhla bez chyby a import přechází do finální fáze.
       * - ``cron.tasks.run_data_import.file_import.validating_directory_settings``
         - Před importem binárních souborů se kontroluje konfigurace importního adresáře.
       * - ``cron.tasks.run_data_import.import_directory_not_configured``
         - Import souborů je potřeba, ale chybí nebo je neplatná konfigurace ``DIRECTORY_PATH``.
       * - ``cron.tasks.run_data_import.file_import.connected``
         - Konfigurace importního adresáře je validní a začíná příprava importu souborů.
       * - ``cron.tasks.run_data_import.importing_file {n}/{total}: {filename} ({ident_cely})``
         - Během importu konkrétního binárního souboru.
       * - ``cron.tasks.run_data_import.cannot_read_from_directory``
         - Při importu souborů nastane chyba čtení z adresáře nebo zpracování souboru.
       * - ``cron.tasks.run_data_import.finished``
         - Import doběhl úspěšně, nebyl zastaven a nebyla nastavena chyba.

   :raises ValueError: Vyvolá se při splnění podmínky ``isinstance(record, Model)``; nebo s textem
       "Missing required DIRECTORY_PATH setting".
