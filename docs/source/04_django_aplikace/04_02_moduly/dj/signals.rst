DJ signály
==========

Definice signálů.

Funkce
------

.. py:function:: save_dokumentacni_jednotka(sender, instance, created)

   Metoda pro vytvoření pianu z katastru arch záznamu.

   Metoda se volá po uložením DJ.

   :param sender: Třída modelu, která signál vyslala.
   :param instance: Ukládaná instance dokumentační jednotky.
   :param created: True pokud byl záznam právě vytvořen, False při aktualizaci.
   :param kwargs: Další parametry signálu.

.. py:function:: pre_delete_dokumentacni_jednotka(sender, instance)

   Zpracuje odpojení pianu a jeho případné smazání před smazáním dokumentační jednotky.

   :param sender: Třída modelu, která signál vyslala.
   :param instance: Mazaná instance dokumentační jednotky.
   :param kwargs: Další parametry signálu.

.. py:function:: delete_dokumentacni_jednotka(sender, instance)

   Odstraní dokumentacni jednotka.

   :param sender: Třída modelu, která signál vyslala.
   :param instance: Smazaná instance dokumentační jednotky.
   :param kwargs: Další parametry signálu.
