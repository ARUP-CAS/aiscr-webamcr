ADB signály
===========

Definice signálů.

Funkce
------

.. py:function:: adb_save_metadata(sender, instance, created)

   Provádí operaci adb save metadata.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param created: Příznak, zda byla instance právě vytvořena.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: vyskovy_bod_save_metadata(sender, instance)

   Provádí operaci vyskovy bod save metadata.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: adb_delete_repository_container(sender, instance)

   Provádí operaci adb delete repository container.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: vyskovy_bod_delete_repository_container(sender, instance)

   Provádí operaci vyskovy bod delete repository container.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
