ARCH_Z signály
==============

Definice signálů.

Funkce
------

.. py:function:: invalidate_arch_z_related_models()

   Provádí operaci invalidate arch z related models.

   :return: Vrací výsledek provedené operace.

.. py:function:: create_arch_z_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb arch záznamu.
   Metoda se volá pred uložením arch záznamu.

.. py:function:: create_arch_z_metadata(sender, instance)

   Funkce pro aktualizaci metadat archeologického záznamu.

.. py:function:: update_akce_snapshot(sender, instance)

   Aktualizuje akce snapshot.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: create_externi_odkaz_metadata(sender, instance)

   Funkce pro aktualizaci metadat externího odkazu.

.. py:function:: delete_arch_z_repository_container_and_connections(sender, instance)

   Funkce pro aktualizaci metadat archeologického záznamu.

.. py:function:: delete_arch_z_repository_update_connected_records(sender, instance)

   Odstraní arch z repository update connected records.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek operace odstranění.

.. py:function:: delete_externi_odkaz_repository_container(sender, instance)

   Funkce pro aktualizaci metadat archeologického záznamu.
