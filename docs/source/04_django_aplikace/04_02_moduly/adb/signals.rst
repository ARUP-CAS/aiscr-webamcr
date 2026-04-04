ADB signály
===========

Definice signálů.

Funkce
------

.. py:function:: adb_save_metadata(sender, instance, created)

   Uloží metadata záznamu ADB do Fedory po jeho uložení.

   **Parametry:**

   - ``sender``: Třída modelu, která signál vyslala.
   - ``instance``: Ukládaná instance záznamu ADB.
   - ``created``: True pokud byl záznam právě vytvořen, False při aktualizaci.
   - ``kwargs``: Další parametry signálu.


.. py:function:: vyskovy_bod_save_metadata(sender, instance)

   Uloží metadata nadřazeného záznamu ADB po uložení výškového bodu.

   **Parametry:**

   - ``sender``: Třída modelu, která signál vyslala.
   - ``instance``: Ukládaná instance výškového bodu.
   - ``kwargs``: Další parametry signálu.


.. py:function:: adb_delete_repository_container(sender, instance)

   Odstraní kontejner záznamu ADB z Fedory a aktualizuje metadata nadřazeného záznamu.

   **Parametry:**

   - ``sender``: Třída modelu, která signál vyslala.
   - ``instance``: Smazaná instance záznamu ADB.
   - ``kwargs``: Další parametry signálu.


.. py:function:: vyskovy_bod_delete_repository_container(sender, instance)

   Aktualizuje metadata nadřazeného záznamu ADB po smazání výškového bodu.

   **Parametry:**

   - ``sender``: Třída modelu, která signál vyslala.
   - ``instance``: Smazaná instance výškového bodu.
   - ``kwargs``: Další parametry signálu.

