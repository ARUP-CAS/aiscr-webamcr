LOKALITA signály
================

Definice signálů.

Funkce
------

.. py:function:: save_lokalita_snapshot(sender, instance)

   Uloží lokalita snapshot.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: save_lokalita_redis_snapshot(sender, instance)

   Uloží lokalita redis snapshot.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: delete_lokalita(sender, instance)

   Odstraní lokalita. v aplikaci.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
