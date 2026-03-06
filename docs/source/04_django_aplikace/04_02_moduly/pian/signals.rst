PIAN signály
============

Definice signálů.

Funkce
------

.. py:function:: create_pian_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb pianu.

   Metoda se volá pred uložením záznamu.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: pian_save_metadata(sender, instance)

   Metoda pro vytvoření historických vazeb pianu.

   Metoda se volá pred uložením záznamu.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: samostatny_nalez_okres_delete_repository_container(sender, instance)

   Provádí operaci samostatny nalez okres delete repository container.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
