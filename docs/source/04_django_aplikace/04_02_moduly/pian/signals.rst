PIAN signály
============

Definice signálů.

Funkce
------

.. py:function:: create_pian_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb pianu.

   Metoda se volá pred uložením záznamu.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: pian_save_metadata(sender, instance)

   Metoda pro vytvoření historických vazeb pianu.

   Metoda se volá pred uložením záznamu.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: samostatny_nalez_okres_delete_repository_container(sender, instance)

   Provádí operaci samostatny nalez okres delete repository container.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
