KOMPONENTA signály
==================

Definice signálů.

Funkce
------

.. py:function:: komponenta_save(sender, instance)

   Provádí operaci komponenta save.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``komponenta_save``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``pk``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``komponenta_save``.

.. py:function:: komponenta_delete(sender, instance)

   Provádí operaci komponenta delete.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``komponenta_delete``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``pk``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``komponenta_delete``.
