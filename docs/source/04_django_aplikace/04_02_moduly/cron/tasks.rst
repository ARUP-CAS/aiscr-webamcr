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


.. py:class:: SouborMimeUnsupportedError

   Vyvoláno při importu souboru, jehož detekovaný MIME typ aplikace nepodporuje.

   Indikuje MIME typ mimo mapu podporovaných formátů ``Soubor.MIME_TO_EXTENSIONS``.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param nazev: Název importovaného souboru.
      :param mime_type: MIME typ detekovaný z obsahu souboru.


.. py:class:: SouborMimeExtensionMismatchError

   Vyvoláno při importu souboru, jehož přípona neodpovídá MIME typu detekovanému z obsahu.

   Indikuje přejmenovaný soubor (např. JPEG uložený s příponou ``.tif``), jehož import
   by vedl k nekonzistenci mezi názvem a skutečným obsahem souboru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param nazev: Název souboru, u nějž byla zjištěna neshoda.
      :param extension: Přípona odvozená z názvu souboru.
      :param mime_type: MIME typ detekovaný z obsahu souboru.


.. py:class:: SouborMimeNotAllowedError

   Vyvoláno při importu souboru, jehož MIME typ není povolen pro typ navázaného záznamu.

   Whitelisty povolených MIME typů odpovídají kontrole ``Soubor.check_mime_for_url``
   používané při uživatelském uploadu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param nazev: Název importovaného souboru.
      :param mime_type: MIME typ detekovaný z obsahu souboru.
      :param navazany_ident_cely: Identifikátor navázaného záznamu, pro který MIME typ není povolen.


.. py:class:: ImportLockLostError

   Vyvoláno, když ``refresh_import_lock`` zjistí, že importní lock byl ztracen.

   Použito jako sentinel, aby vnější ``except Exception`` v ``run_data_import`` mohl
   rozlišit ztrátu zámku od ostatních selhání během importu dat a nepřepsal
   konkrétní status message ``failed_lock_lost``.


Funkce
------

.. py:function:: translation_value(message_id)

   Zabalí překladové ID (a případné parametry) pro uložení do Redis.

   Pro zprávy bez parametrů vrací přímo ID (plain string) — běžný případ. Pro parametrizované
   zprávy vrací JSON obálku ``{"id": <id>, "params": {...}}``, kterou čtenář rozbalí a interpoluje
   po překladu. Nikdy nevolá ``_()`` — překlad probíhá až na straně čtenáře.

   Pro výjimky, jejichž zpráva je složena za běhu (např. ``str(err)`` z mapperů), použijte
   ``raw=True``: obálka ``{"id": "cron.tasks.run_data_import.error.raw", "params": {"message": ...},
   "raw": true}`` se na čtenáři vrátí doslova bez překladu.

   :param message_id: ID překladového řetězce (dotted key, např.
       ``cron.tasks.run_data_import.finished``).
   :param params: Parametry pro interpolaci přeloženého řetězce (např. ``n``, ``total``). Pro
       výjimku použijte ``raw=True`` a ``message=<str(err)>``.
   :return: Hodnota připravená k zápisu do Redis (ID nebo JSON obálka).

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

.. py:function:: _normalize_import_file_name(name)

   Normalizuje název souboru ze ZIP archivu na formát pro porovnání s mapery.

   :param name: Původní cesta nebo název souboru ze ZIP archivu.
   :return: Název souboru bez adresáře, oříznutý o bílé znaky a převedený na malá písmena.

.. py:function:: _format_import_primary_key(pk)

   Převede primární klíč importovaného záznamu na text pro validační výstup.

   :param pk: Primární klíč z mapperu, typicky slovník složeného klíče nebo skalární hodnota.
   :return: Textová reprezentace klíče vhodná pro zobrazení ve validační tabulce.

.. py:function:: run_data_import_validation(job_id, user_id, lock_token, performed_action)

   Asynchronně zvaliduje nahraný ZIP archiv hromadného importu (viz §4.2 dokumentu #391).

   Task převezme staged ZIP z Redis (chunky ``import_data_file_{job_id}_{i}``, §3.3), projde
   všechny CSV řádky přes mappery (``map`` / ``check_required_fields`` / ``import_validation`` /
   ``create_records``) a inkrementálně zapisuje výsledky do Redis, aby je stránka mohla pollovat.
   Samotný import neprovádí — po úspěšné validaci nechává lock držený a přechází do fáze
   ``awaiting_approval``; při chybě nebo zastavení lock uvolní.

   Kontrakt read-only: ``create_records`` se během validace volá pouze pro serializaci a musí
   zůstat read-only — nesmí volat ``save()``/``delete()`` ani jinak měnit databázi (§4.2).

   Paměťová charakteristika (§8): reassembled komprimovaný blob (~250 MB pro maximální úlohu)
   NENÍ high-water mark workeru. Validační průchod (object-dtype DataFrame + kopie z ``to_dict`` +
   akumulující se seznam ``records``) dosahuje několika GB pro maximální úlohu — worker musí být
   dimenzován na tento peak, ne na ~250 MB komprimovaného blobu.

   :param job_id: Identifikátor importní úlohy (sufix všech per-job Redis klíčů).
   :param user_id: Identifikátor uživatele, který import spustil.
   :param lock_token: Token vlastnictví importního locku, obnovovaný jednou za řádek během validace.
   :param performed_action: Typ akce importu (insert/update/delete) z ``ImportDataAdminForm``.

.. py:function:: run_data_import(job_id, user_id, lock_token)

   Spustí data import.

   :param job_id: Identifikátor objektu ``job``.
   :param user_id: Identifikátor objektu ``user``.
   :param lock_token: Token pro ověření vlastnictví importního zámku v Redis.

   Možné hodnoty Redis klíče ``import_data_status_message_tr_{job_id}`` (ukládá se překladové
   ID, případně obálka ``{id, params}`` pro parametrizované zprávy; překlad provádí až čtenář
   v locale přihlášeného admina — viz ``translation_value`` a ``_translate_status_value``):

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
