NALEZ signály
=============

Definice signálů.

Funkce
------

.. py:function:: delete_nalez_objekt(sender, instance)

   Odstraní nalez objekt.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_nalez_objekt``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``hasattr()``, pracuje se s atributy ``pk``, ``active_transaction``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_nalez_objekt``.

.. py:function:: delete_nalez_predmet(sender, instance)

   Odstraní nalez predmet.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_nalez_predmet``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``hasattr()``, pracuje se s atributy ``pk``, ``active_transaction``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_nalez_predmet``.
