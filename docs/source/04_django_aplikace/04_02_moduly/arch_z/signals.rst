ARCH_Z signály
==============

Definice signálů.

Funkce
------

.. py:function:: invalidate_arch_z_related_models()

   Zneplatní cache pro modely Akce a Projekt po změně archeologického záznamu.

.. py:function:: create_arch_z_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb arch záznamu.

   Metoda se volá pred uložením arch záznamu.

   :param sender: Třída modelu, která vyslala signál (ArcheologickyZaznam).
   :param instance: Instance archeologického záznamu; pokud nemá primární klíč, vytváří se nová vazba na historii.
   :param kwargs: Dodatečné argumenty předané signálem.

.. py:function:: create_arch_z_metadata(sender, instance)

   Funkce pro aktualizaci metadat archeologického záznamu.

   :param sender: Třída modelu, která vyslala signál (ArcheologickyZaznam).
   :param instance: Instance archeologického záznamu; při změně přístupnosti nebo stavu se aktualizují metadata navázaných PIAN a ADB záznamů.
   :param kwargs: Dodatečné argumenty předané signálem.

.. py:function:: update_akce_snapshot(sender, instance)

   Aktualizuje akce snapshot.

   :param sender: Třída modelu, která vyslala signál (Akce).
   :param instance: Instance akce; spouští aktualizaci Redis snapshotu a při změně projektu aktualizuje metadata projektu.
   :param kwargs: Dodatečné argumenty předané signálem.

.. py:function:: create_externi_odkaz_metadata(sender, instance)

   Funkce pro aktualizaci metadat externího odkazu.

   :param sender: Třída modelu, která vyslala signál (ExterniOdkaz).
   :param instance: Instance externího odkazu; aktualizuje metadata navázaného archeologického záznamu a externího zdroje.
   :param kwargs: Dodatečné argumenty předané signálem.

.. py:function:: delete_arch_z_repository_container_and_connections(sender, instance)

   Funkce pro aktualizaci metadat archeologického záznamu.

   :param sender: Třída modelu, která vyslala signál (ArcheologickyZaznam).
   :param instance: Instance archeologického záznamu; před smazáním odstraňuje komponenty a jejich vazby dokumentačních jednotek.
   :param kwargs: Dodatečné argumenty předané signálem.

.. py:function:: delete_arch_z_repository_update_connected_records(sender, instance)

   Odstraní arch z repository update connected records.

   :param sender: Třída modelu, která vyslala signál (ArcheologickyZaznam).
   :param instance: Instance smazaného archeologického záznamu; aktualizuje metadata navázaného projektu a zaznamenává smazání v repozitáři.
   :param kwargs: Dodatečné argumenty předané signálem.

.. py:function:: delete_externi_odkaz_repository_container(sender, instance)

   Funkce pro aktualizaci metadat archeologického záznamu.

   :param sender: Třída modelu, která vyslala signál (ExterniOdkaz).
   :param instance: Instance smazaného externího odkazu; aktualizuje metadata navázaného archeologického záznamu a externího zdroje.
   :param kwargs: Dodatečné argumenty předané signálem.
