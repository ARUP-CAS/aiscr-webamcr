PAS signály
===========

Definice signálů.

Funkce
------

.. py:function:: create_dokument_vazby(sender, instance)

   Metoda pro vytvoření historických a souborových vazeb samostatnýho náleze.

   Metoda se volá pred uložením záznamu.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: save_metadata_samostatny_nalez(sender, instance, created)

   Uloží metadata samostatny nalez.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param created: Příznak, zda byla instance právě vytvořena.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: dokument_delete_container_soubor_vazby(sender, instance)

   Provádí operaci dokument delete container soubor vazby.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: save_uzivatel_spoluprce(sender, instance)

   Uloží uzivatel spoluprce.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: delete_uzivatel_spoluprce_connections(sender, instance)

   Odstraní uzivatel spoluprce connections.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
