EZ signály
==========

Definice signálů.

Funkce
------

.. py:function:: create_ez_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb externího zdroje.

   Metoda se volá pred uložením záznamu.

   :param sender: Třída modelu, který signál vyslal (ExterniZdroj).
   :param instance: Instance externího zdroje, pro niž se vytváří historická vazba při prvním uložení.
   :param kwargs: Dodatečné argumenty předávané signálem Django.

.. py:function:: externi_zdroj_save_metadata(sender, instance)

   Po uložení externího zdroje invaliduje cache a uloží metadata do Fedory, pokud není potlačen signál.

   :param sender: Třída modelu, který signál vyslal (ExterniZdroj).
   :param instance: Uložená instance externího zdroje, jejíž metadata se synchronizují s úložištěm.
   :param kwargs: Dodatečné argumenty předávané signálem Django.

.. py:function:: delete_externi_zdroj_repository_container(sender, instance)

   Odstraní externi zdroj repository container.

   :param sender: Třída modelu, který signál vyslal (ExterniZdroj).
   :param instance: Instance externího zdroje, který je před smazáním odstraněn z úložiště Fedora spolu s jeho externími odkazy a historií.
   :param kwargs: Dodatečné argumenty předávané signálem Django.
