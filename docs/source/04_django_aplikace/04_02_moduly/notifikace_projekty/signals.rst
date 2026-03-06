NOTIFIKACE_PROJEKTY signály
===========================

Definice signálů.

Funkce
------

.. py:function:: pes_save(sender, instance)

   Provádí operaci pes save.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``pes_save``.
   :param instance: Parametr ``instance`` předává se do volání ``getattr()``, ``on_commit()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``pes_save``.

.. py:function:: pes_delete(sender, instance)

   Provádí operaci pes delete.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``pes_delete``.
   :param instance: Parametr ``instance`` předává se do volání ``getattr()``, ``on_commit()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``pes_delete``.
