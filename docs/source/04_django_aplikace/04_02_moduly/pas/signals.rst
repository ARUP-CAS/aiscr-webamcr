PAS signály
===========

Definice signálů.

Funkce
------

.. py:function:: create_dokument_vazby(sender, instance)

   Metoda pro vytvoření historických a souborových vazeb samostatnýho náleze.
   Metoda se volá pred uložením záznamu.

.. py:function:: save_metadata_samostatny_nalez(sender, instance, created)

   Uloží metadata samostatny nalez.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param created: Vstupní hodnota ``created`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: dokument_delete_container_soubor_vazby(sender, instance)

   Provádí operaci dokument delete container soubor vazby.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: save_uzivatel_spoluprce(sender, instance)

   Uloží uzivatel spoluprce.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: delete_uzivatel_spoluprce_connections(sender, instance)

   Odstraní uzivatel spoluprce connections.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek operace odstranění.
