NOTIFIKACE_PROJEKTY tasks
=========================

Modul tasks.

Funkce
------

.. py:function:: get_project_type_notification(projekt_type)

   Vrací project type notification.

   :param projekt_type: Parametr ``projekt_type`` předává se do volání ``get()``, vstupuje do návratové hodnoty.

       :return: Vrací výsledek volání ``get()``.

.. py:function:: check_hlidaci_pes(projekt_id)

   Task pro celery pro skontrolování jestli je nastavený hlídací pes.

   :param projekt_id: Identifikátor ``projekt_id`` používaný pro dohledání cílového záznamu.

       :return: Vrací výsledek volání ``send_ep02()``.
