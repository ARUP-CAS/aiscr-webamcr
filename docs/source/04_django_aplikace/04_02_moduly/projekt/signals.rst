PROJEKT signály
===============

Definice signálů.

Funkce
------

.. py:function:: projekt_pre_save(sender, instance)

   Metoda pro volání dílčích metod pro nastavení projektu pred uložením.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: change_termin_odevzdani_NZ(sender, instance)

   Metoda pro nastavení terminu odevzdání NZ.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: create_projekt_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb projektu.

   Metoda se volá pred uložením projektu.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param kwargs: Popis parametru ``kwargs``.

.. py:function:: projekt_pre_delete(sender, instance)

   Provádí operaci projekt pre delete.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.

.. py:function:: projekt_post_save(sender, instance)

   Metoda pro odeslání emailu hlídacího psa pri založení projektu.

   :param sender: Popis parametru ``sender``.
   :param instance: Popis parametru ``instance``.
   :param kwargs: Popis parametru ``kwargs``.
