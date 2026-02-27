NOTIFIKACE_PROJEKTY tasks
=========================

Modul tasks.

Funkce
------

.. py:function:: get_project_type_notification(projekt_type)

   Vrací project type notification.

   :param projekt_type: Vstupní hodnota ``projekt_type`` pro danou operaci.
   :return: Vrací načtená data odpovídající vstupním parametrům.

.. py:function:: check_hlidaci_pes(projekt_id)

   Task pro celery pro skontrolování jestli je nastavený hlídací pes.
