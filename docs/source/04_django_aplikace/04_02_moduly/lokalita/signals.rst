LOKALITA signály
================

Definice signálů.

Funkce
------

.. py:function:: save_lokalita_snapshot(sender, instance)

   Uloží lokalita snapshot.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_lokalita_snapshot``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``archeologicky_zaznam``, ``set_snapshots``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_lokalita_snapshot``.

.. py:function:: save_lokalita_redis_snapshot(sender, instance)

   Uloží lokalita redis snapshot.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_lokalita_redis_snapshot``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``check_if_task_queued()``, pracuje se s atributy ``archeologicky_zaznam``, ``pk``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_lokalita_redis_snapshot``.

.. py:function:: delete_lokalita(sender, instance)

   Odstraní lokalita. v aplikaci.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_lokalita``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``archeologicky_zaznam``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_lokalita``.
