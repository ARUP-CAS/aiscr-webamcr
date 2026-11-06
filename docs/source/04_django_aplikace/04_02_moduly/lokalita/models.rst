LOKALITA modely
===============

Definice modelů.

Třídy
------

.. py:class:: Lokalita

   Databázový model lokality.

   **Metody:**

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu podle identu.

      :return: Vrací výsledek volání ``reverse()``.

   .. py:method:: set_igsn()

      Nastaví igsn. v aplikaci.

   .. py:method:: set_snapshots()

      Nastaví snapshots. v aplikaci.

   .. py:method:: sestav_snapshot_katastru()

      Sestaví text ``dalsi_katastry_snapshot`` z názvů katastrů.

      Formát je na jednom místě, aby ho mohla použít i hromadná přegenerace
      v anonymizaci databáze, která názvy načítá pro celou dávku najednou.

      :param nazvy: Názvy dalších katastrů seřazené podle názvu.
      :return: Názvy oddělené ``"; "``, nebo ``None`` pro prázdný seznam.

   .. py:method:: redis_snapshot_id()

      Vrací identifikátor snímku v Redis.

      :return: Redis klíč snímku.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje Redis snapshot tohoto záznamu (deleguje na :meth:`generate_redis_snapshots`).

      :return: N-tice (klíč, data); data jsou ``None``, pokud záznam v databázi neexistuje.

   .. py:method:: generate_redis_snapshots()

      Vygeneruje Redis snapshoty více záznamů jednou tabulkou ``LokalitaTable``.

      Související záznamy zobrazované v tabulce se načítají hromadně (``select_related`` /
      ``prefetch_related``), takže počet dotazů nezávisí na počtu záznamů.

      :param records: Instance modelu, pro které se snapshoty generují.
      :return: Slovník ``{redis_snapshot_id: data}`` pro záznamy nalezené v databázi.

   .. py:method:: _get_igsn_client()

      Vrací instanci igsn lienta.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: igsn_exists()

      Ověří existenci IGSN identifikátoru.

      :return: True pokud IGSN existuje.

   .. py:method:: igsn_delete()

      Smaže IGSN identifikátor.

      :param check_status: Parametr ``check_status`` předává se do volání ``delete_record()``, vstupuje do návratové hodnoty.

      :return: Výsledek volání ``delete_record()``.

   .. py:method:: igsn_hide()

      Skryje IGSN identifikátor.

      :param check_status: Parametr ``check_status`` předává se do volání ``hide_record()``, vstupuje do návratové hodnoty.

      :return: Výsledek volání ``hide_record()``.

   .. py:method:: igsn_publish()

      Publikuje IGSN identifikátor.

      :param check_status: Parametr ``check_status`` předává se do volání ``publish_record()``, vstupuje do návratové hodnoty.

      :return: Výsledek volání ``publish_record()``.

   .. py:method:: igsn_update()

      Aktualizuje IGSN identifikátor.

      :param check_status: Parametr ``check_status`` předává se do volání ``update_record()``, vstupuje do návratové hodnoty.
      :param reload_record: Parametr ``reload_record`` předává se do volání ``update_record()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``update_record()``.

   .. py:method:: igsn_url()

      Vrací IGSN adresu záznamu.

      :return: Vrací výsledek volání ``get_record_url()``.

   .. py:method:: get_by_ident_cely()

      Vyhledá záznam na základě identifikátoru.

      :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get()``, None.

