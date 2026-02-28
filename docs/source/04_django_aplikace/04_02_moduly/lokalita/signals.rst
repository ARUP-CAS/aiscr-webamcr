LOKALITA signály
================

Definice signálů.

Funkce
------

.. py:function:: save_lokalita_snapshot(sender, instance)

   Uloží lokalita snapshot.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: save_lokalita_redis_snapshot(sender, instance)

   Uloží lokalita redis snapshot.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: delete_lokalita(sender, instance)

   Odstraní lokalita. v aplikaci.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
