NOTIFIKACE_PROJEKTY tasks
=========================

Modul tasks.

Funkce
------

.. py:function:: get_project_type_notification(projekt_type)

   Vrací project type notification.

   **Parametry:**

   - ``projekt_type``: Parametr ``projekt_type`` předává se do volání ``get()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací výsledek volání ``get()``.


.. py:function:: check_hlidaci_pes(projekt_id)

   Task pro celery pro skontrolování jestli je nastavený hlídací pes.

   **Parametry:**

   - ``projekt_id``: Identifikátor ``projekt_id`` používaný pro dohledání cílového záznamu.

   **Návratová hodnota:**

   Vrací výsledek volání ``send_ep02()``.

