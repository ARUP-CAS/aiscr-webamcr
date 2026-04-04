NEIDENTAKCE signály
===================

Definice signálů.

Funkce
------

.. py:function:: neident_akce_post_save(sender, instance)

   Uloží metadata nadřazeného dokumentu po uložení neidentifikované akce.

   **Parametry:**

   - ``sender``: Třída modelu, která signál vyslala.
   - ``instance``: Ukládaná instance neidentifikované akce.
   - ``kwargs``: Další parametry signálu.


.. py:function:: neident_akce_post_delete(sender, instance)

   Aktualizuje metadata nadřazeného dokumentu po smazání neidentifikované akce.

   **Parametry:**

   - ``sender``: Třída modelu, která signál vyslala.
   - ``instance``: Smazaná instance neidentifikované akce.
   - ``kwargs``: Další parametry signálu.

