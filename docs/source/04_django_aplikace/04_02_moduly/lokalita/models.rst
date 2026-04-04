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

      **Návratová hodnota:**

      Vrací výsledek volání ``reverse()``.


   .. py:method:: set_igsn()

      Nastaví igsn. v aplikaci.

   .. py:method:: set_snapshots()

      Nastaví snapshots. v aplikaci.

   .. py:method:: redis_snapshot_id()

      Vrací identifikátor snímku v Redis.

      **Návratová hodnota:**

      Redis klíč snímku.


   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

      **Návratová hodnota:**

      Vrací n-tici.


   .. py:method:: _get_igsn_client()

      Vrací instanci igsn lienta.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: igsn_exists()

      Ověří existenci IGSN identifikátoru.

      **Návratová hodnota:**

      True pokud IGSN existuje.


   .. py:method:: igsn_delete()

      Smaže IGSN identifikátor.

      **Parametry:**

      - ``check_status``: Parametr ``check_status`` předává se do volání ``delete_record()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Výsledek volání ``delete_record()``.


   .. py:method:: igsn_hide()

      Skryje IGSN identifikátor.

      **Parametry:**

      - ``check_status``: Parametr ``check_status`` předává se do volání ``hide_record()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Výsledek volání ``hide_record()``.


   .. py:method:: igsn_publish()

      Publikuje IGSN identifikátor.

      **Parametry:**

      - ``check_status``: Parametr ``check_status`` předává se do volání ``publish_record()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Výsledek volání ``publish_record()``.


   .. py:method:: igsn_update()

      Aktualizuje IGSN identifikátor.

      **Parametry:**

      - ``check_status``: Parametr ``check_status`` předává se do volání ``update_record()``, vstupuje do návratové hodnoty.
      - ``reload_record``: Parametr ``reload_record`` předává se do volání ``update_record()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``update_record()``.


   .. py:method:: igsn_url()

      Vrací IGSN adresu záznamu.

      **Návratová hodnota:**

      Vrací výsledek volání ``get_record_url()``.


   .. py:method:: get_by_ident_cely()

      Vyhledá záznam na základě identifikátoru.

      **Parametry:**

      - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get()``, None.


