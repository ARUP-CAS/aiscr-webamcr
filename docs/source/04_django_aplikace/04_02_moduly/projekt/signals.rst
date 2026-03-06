PROJEKT signály
===============

Definice signálů.

Funkce
------

.. py:function:: projekt_pre_save(sender, instance)

   Metoda pro volání dílčích metod pro nastavení projektu pred uložením.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: change_termin_odevzdani_NZ(sender, instance)

   Metoda pro nastavení terminu odevzdání NZ.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: create_projekt_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb projektu.

   Metoda se volá pred uložením projektu.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: projekt_pre_delete(sender, instance)

   Provádí operaci projekt pre delete.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: projekt_post_save(sender, instance)

   Metoda pro odeslání emailu hlídacího psa pri založení projektu.

   :param sender: Třída modelu, která signal vyvolala.
   :param instance: Instance modelu, které se operace týká.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
