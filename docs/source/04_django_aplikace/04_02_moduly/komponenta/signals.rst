KOMPONENTA signály
==================

Definice signálů.

Funkce
------

.. py:function:: komponenta_save(sender, instance)

   Provádí operaci komponenta save.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: komponenta_delete(sender, instance)

   Provádí operaci komponenta delete.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
