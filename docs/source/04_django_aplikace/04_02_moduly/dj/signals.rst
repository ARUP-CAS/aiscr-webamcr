DJ signály
==========

Definice signálů.

Funkce
------

.. py:function:: save_dokumentacni_jednotka(sender, instance, created)

   Metoda pro vytvoření pianu z katastru arch záznamu.

   Metoda se volá po uložením DJ.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param created: Příznak, zda byla instance právě vytvořena.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: pre_delete_dokumentacni_jednotka(sender, instance)

   Provádí operaci pre delete dokumentacni jednotka.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: delete_dokumentacni_jednotka(sender, instance)

   Odstraní dokumentacni jednotka.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
