ADB signály
===========

Definice signálů.

Funkce
------

.. py:function:: adb_save_metadata(sender, instance, created)

   Uloží metadata záznamu ADB do Fedory po jeho uložení.

   :param sender: Třída modelu, která signál vyslala.
   :param instance: Ukládaná instance záznamu ADB.
   :param created: True pokud byl záznam právě vytvořen, False při aktualizaci.
   :param kwargs: Další parametry signálu.

.. py:function:: vyskovy_bod_save_metadata(sender, instance)

   Uloží metadata nadřazeného záznamu ADB po uložení výškového bodu.

   :param sender: Třída modelu, která signál vyslala.
   :param instance: Ukládaná instance výškového bodu.
   :param kwargs: Další parametry signálu.

.. py:function:: adb_delete_repository_container(sender, instance)

   Odstraní kontejner záznamu ADB z Fedory a aktualizuje metadata nadřazeného záznamu.

   :param sender: Třída modelu, která signál vyslala.
   :param instance: Smazaná instance záznamu ADB.
   :param kwargs: Další parametry signálu.

.. py:function:: vyskovy_bod_delete_repository_container(sender, instance)

   Aktualizuje metadata nadřazeného záznamu ADB po smazání výškového bodu.

   :param sender: Třída modelu, která signál vyslala.
   :param instance: Smazaná instance výškového bodu.
   :param kwargs: Další parametry signálu.
