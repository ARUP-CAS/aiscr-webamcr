CRON tasks
==========

Modul tasks.

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

.. py:function:: update_all_redis_snapshots(rewrite_existing)

   Aktualizuje all redis snapshots.

   :param rewrite_existing: Číselná hodnota ``rewrite_existing`` použitá při výpočtu nebo transformaci.

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

   Provádí operaci call digiarchiv update task.

.. py:function:: run_data_import(job_id, user_id)

   Spustí data import.

   :param job_id: Identifikátor objektu ``job``.
   :param user_id: Identifikátor objektu ``user``.

   :raises ValueError: Vyvolá se při splnění podmínky ``isinstance(record, Model)``; nebo s textem "Missing required DIRECTORY_PATH setting".
