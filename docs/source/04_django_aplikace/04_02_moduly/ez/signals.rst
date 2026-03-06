EZ signály
==========

Definice signálů.

Funkce
------

.. py:function:: create_ez_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb externího zdroje.

   Metoda se volá pred uložením záznamu.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: externi_zdroj_save_metadata(sender, instance)

   Provádí operaci externi zdroj save metadata.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: delete_externi_zdroj_repository_container(sender, instance)

   Odstraní externi zdroj repository container.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
