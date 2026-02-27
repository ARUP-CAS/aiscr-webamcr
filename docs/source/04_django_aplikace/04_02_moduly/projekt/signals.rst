PROJEKT signály
===============

Definice signálů.

Funkce
------

.. py:function:: projekt_pre_save(sender, instance)

   Metoda pro volání dílčích metod pro nastavení projektu pred uložením.

.. py:function:: change_termin_odevzdani_NZ(sender, instance)

   Metoda pro nastavení terminu odevzdání NZ.

.. py:function:: create_projekt_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb projektu.
   Metoda se volá pred uložením projektu.

.. py:function:: projekt_pre_delete(sender, instance)

   Provádí operaci projekt pre delete.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: projekt_post_save(sender, instance)

   Metoda pro odeslání emailu hlídacího psa pri založení projektu.
