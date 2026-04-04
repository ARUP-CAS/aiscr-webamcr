DJ signály
==========

Definice signálů.

Funkce
------

.. py:function:: save_dokumentacni_jednotka(sender, instance, created)

   Metoda pro vytvoření pianu z katastru arch záznamu.

   Metoda se volá po uložením DJ.

   **Parametry:**

   - ``sender``: Třída modelu, která signál vyslala.
   - ``instance``: Ukládaná instance dokumentační jednotky.
   - ``created``: True pokud byl záznam právě vytvořen, False při aktualizaci.
   - ``kwargs``: Další parametry signálu.


.. py:function:: pre_delete_dokumentacni_jednotka(sender, instance)

   Zpracuje odpojení pianu a jeho případné smazání před smazáním dokumentační jednotky.

   **Parametry:**

   - ``sender``: Třída modelu, která signál vyslala.
   - ``instance``: Mazaná instance dokumentační jednotky.
   - ``kwargs``: Další parametry signálu.


.. py:function:: delete_dokumentacni_jednotka(sender, instance)

   Odstraní dokumentacni jednotka.

   **Parametry:**

   - ``sender``: Třída modelu, která signál vyslala.
   - ``instance``: Smazaná instance dokumentační jednotky.
   - ``kwargs``: Další parametry signálu.

