KOMPONENTA signály
==================

Definice signálů.

Funkce
------

.. py:function:: komponenta_save(sender, instance)

   Aktualizuje metadata nadřazeného záznamu (dokumentu nebo arch. záznamu) po uložení komponenty.

   **Parametry:**

   - ``sender``: Třída modelu, která signál vyslala.
   - ``instance``: Ukládaná instance komponenty.
   - ``kwargs``: Další parametry signálu.


.. py:function:: komponenta_delete(sender, instance)

   Aktualizuje metadata nadřazeného záznamu (dokumentu nebo arch. záznamu) po smazání komponenty.

   **Parametry:**

   - ``sender``: Třída modelu, která signál vyslala.
   - ``instance``: Smazaná instance komponenty.
   - ``kwargs``: Další parametry signálu.

