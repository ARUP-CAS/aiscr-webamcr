EZ signály
==========

Definice signálů.

Funkce
------

.. py:function:: create_ez_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb externího zdroje.
   Metoda se volá pred uložením záznamu.

.. py:function:: externi_zdroj_save_metadata(sender, instance)

   Provádí operaci externi zdroj save metadata.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: delete_externi_zdroj_repository_container(sender, instance)

   Odstraní externi zdroj repository container.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek operace odstranění.
