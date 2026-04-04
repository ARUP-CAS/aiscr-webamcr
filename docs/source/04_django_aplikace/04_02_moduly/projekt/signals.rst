PROJEKT signály
===============

Definice signálů.

Funkce
------

.. py:function:: projekt_pre_save(sender, instance)

   Metoda pro volání dílčích metod pro nastavení projektu pred uložením.

   **Parametry:**

   - ``sender``: Parametr ``sender`` se předává do volání ``create_projekt_vazby()``, ``change_termin_odevzdani_NZ()``.
   - ``instance``: Parametr ``instance`` předává se do volání ``create_projekt_vazby()``, ``change_termin_odevzdani_NZ()``, pracuje se s atributy ``stav``, ``_state``, ovlivňuje větvení podmínek.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``projekt_pre_save``.


.. py:function:: change_termin_odevzdani_NZ(sender, instance)

   Metoda pro nastavení terminu odevzdání NZ.

   **Parametry:**

   - ``sender``: Parametr ``sender`` pracuje se s atributy ``objects``, ``DoesNotExist``.
   - ``instance``: Parametr ``instance`` předává se do volání ``get()``, ``debug()``, pracuje se s atributy ``pk``, ``termin_odevzdani_nz``, ovlivňuje větvení podmínek.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``change_termin_odevzdani_NZ``.


.. py:function:: create_projekt_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb projektu.

   Metoda se volá pred uložením projektu.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``create_projekt_vazby``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``pk``, ``historie``, ovlivňuje větvení podmínek.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``create_projekt_vazby``.


.. py:function:: projekt_pre_delete(sender, instance)

   Provádí operaci projekt pre delete.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``projekt_pre_delete``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``initial_dokumenty``, ovlivňuje větvení podmínek.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``projekt_pre_delete``.

   **Výjimky:**

   - ``Exception``: Vyvolá se při splnění podmínky ``instance.soubory and instance.soubory.soubory.exists()``.


.. py:function:: projekt_post_save(sender, instance)

   Metoda pro odeslání emailu hlídacího psa pri založení projektu.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``projekt_post_save``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, ``getattr()``, pracuje se s atributy ``ident_cely``, ``active_transaction``, ovlivňuje větvení podmínek.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``projekt_post_save``.

