NOTIFIKACE_PROJEKTY tasks
=========================

Modul tasks.

Funkce
------

.. py:function:: get_project_type_notification(projekt_type)

   Vrací project type notification.

   :param projekt_type: Název nebo typ ``projekt_type`` používaný pro volbu cílové logiky.

.. py:function:: check_hlidaci_pes(projekt_id)

   Task pro celery pro skontrolování jestli je nastavený hlídací pes.

   :param projekt_id: Identifikátor ``projekt_id`` používaný pro dohledání cílového záznamu.
