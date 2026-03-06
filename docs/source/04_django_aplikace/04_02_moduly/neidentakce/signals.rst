NEIDENTAKCE signály
===================

Definice signálů.

Funkce
------

.. py:function:: neident_akce_post_save(sender, instance)

   Provádí operaci neident akce post save.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``neident_akce_post_save``.
   :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``dokument_cast``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``neident_akce_post_save``.

.. py:function:: neident_akce_post_delete(sender, instance)

   Provádí operaci neident akce post delete.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``neident_akce_post_delete``.
   :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``dokument_cast``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``neident_akce_post_delete``.
