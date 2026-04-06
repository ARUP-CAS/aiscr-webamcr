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

      Vrací identifikátor snímku v Redis.

      :return: Redis klíč snímku.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

      :return: Vrací n-tici.

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

