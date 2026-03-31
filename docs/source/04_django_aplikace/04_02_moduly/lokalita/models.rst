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

   .. py:method:: redis_snapshot_id()

      Provádí operaci redis snapshot id.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

      :return: Vrací n-tici.

   .. py:method:: _get_igsn_client()

      Vrací igsn client.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: igsn_exists()

      Provádí operaci igsn exists.

      :return: Vrací výsledek volání ``check_record_exists()``.

   .. py:method:: igsn_delete()

      Provádí operaci igsn delete.

      :param check_status: Parametr ``check_status`` předává se do volání ``delete_record()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``delete_record()``.

   .. py:method:: igsn_hide()

      Provádí operaci igsn hide.

      :param check_status: Parametr ``check_status`` předává se do volání ``hide_record()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``hide_record()``.

   .. py:method:: igsn_publish()

      Provádí operaci igsn publish.

      :param check_status: Parametr ``check_status`` předává se do volání ``publish_record()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``publish_record()``.

   .. py:method:: igsn_update()

      Provádí operaci igsn update.

      :param check_status: Parametr ``check_status`` předává se do volání ``update_record()``, vstupuje do návratové hodnoty.
      :param reload_record: Parametr ``reload_record`` předává se do volání ``update_record()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``update_record()``.

   .. py:method:: igsn_url()

      Provádí operaci igsn url.

      :return: Vrací výsledek volání ``get_record_url()``.

   .. py:method:: get_by_ident_cely()

      Vrací by ident cely.

      :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get()``, None.

