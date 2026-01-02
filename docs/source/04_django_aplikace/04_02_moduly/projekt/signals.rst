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

   Popis není k dispozici.

.. py:function:: projekt_post_save(sender, instance)

   Metoda pro odeslání emailu hlídacího psa pri založení projektu.
