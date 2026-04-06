KOMPONENTA signály
==================

Definice signálů.

Funkce
------

.. py:function:: komponenta_save(sender, instance)

   Aktualizuje metadata nadřazeného záznamu (dokumentu nebo arch. záznamu) po uložení komponenty.

   :param sender: Třída modelu, která signál vyslala.
   :param instance: Ukládaná instance komponenty.
   :param kwargs: Další parametry signálu.

.. py:function:: komponenta_delete(sender, instance)

   Aktualizuje metadata nadřazeného záznamu (dokumentu nebo arch. záznamu) po smazání komponenty.

   :param sender: Třída modelu, která signál vyslala.
   :param instance: Smazaná instance komponenty.
   :param kwargs: Další parametry signálu.
