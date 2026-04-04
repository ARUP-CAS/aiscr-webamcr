NEIDENTAKCE signály
===================

Definice signálů.

Funkce
------

.. py:function:: neident_akce_post_save(sender, instance)

   Uloží metadata nadřazeného dokumentu po uložení neidentifikované akce.

   :param sender: Třída modelu, která signál vyslala.
   :param instance: Ukládaná instance neidentifikované akce.
   :param kwargs: Další parametry signálu.

.. py:function:: neident_akce_post_delete(sender, instance)

   Aktualizuje metadata nadřazeného dokumentu po smazání neidentifikované akce.

   :param sender: Třída modelu, která signál vyslala.
   :param instance: Smazaná instance neidentifikované akce.
   :param kwargs: Další parametry signálu.
