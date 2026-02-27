DJ signály
==========

Definice signálů.

Funkce
------

.. py:function:: save_dokumentacni_jednotka(sender, instance, created)

   Metoda pro vytvoření pianu z katastru arch záznamu.
   Metoda se volá po uložením DJ.

.. py:function:: pre_delete_dokumentacni_jednotka(sender, instance)

   Provádí operaci pre delete dokumentacni jednotka.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: delete_dokumentacni_jednotka(sender, instance)

   Odstraní dokumentacni jednotka.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek operace odstranění.
