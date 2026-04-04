LOKALITA signály
================

Definice signálů.

Funkce
------

.. py:function:: save_lokalita_snapshot(sender, instance)

   Uloží lokalita snapshot.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_lokalita_snapshot``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``archeologicky_zaznam``, ``set_snapshots``.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_lokalita_snapshot``.


.. py:function:: save_lokalita_redis_snapshot(sender, instance)

   Uloží lokalita redis snapshot.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_lokalita_redis_snapshot``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, ``check_if_task_queued()``, pracuje se s atributy ``archeologicky_zaznam``, ``pk``, ovlivňuje větvení podmínek.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_lokalita_redis_snapshot``.


.. py:function:: delete_lokalita(sender, instance)

   Odstraní lokalita. v aplikaci.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_lokalita``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``archeologicky_zaznam``.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_lokalita``.

