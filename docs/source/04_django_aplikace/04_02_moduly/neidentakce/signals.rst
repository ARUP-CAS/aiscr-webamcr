NEIDENTAKCE signály
===================

Definice signálů.

Funkce
------

.. py:function:: neident_akce_post_save(sender, instance)

   Provádí operaci neident akce post save.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: neident_akce_post_delete(sender, instance)

   Provádí operaci neident akce post delete.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
