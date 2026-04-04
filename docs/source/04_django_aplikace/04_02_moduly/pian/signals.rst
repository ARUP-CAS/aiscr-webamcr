PIAN signály
============

Definice signálů.

Funkce
------

.. py:function:: create_pian_vazby(sender, instance)

   Metoda pro vytvoření historických vazeb pianu.

   Metoda se volá pred uložením záznamu.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``create_pian_vazby``.
   - ``instance``: Parametr ``instance`` pracuje se s atributy ``pk``, ``historie``, ovlivňuje větvení podmínek.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``create_pian_vazby``.


.. py:function:: pian_save_metadata(sender, instance)

   Metoda pro vytvoření historických vazeb pianu.

   Metoda se volá pred uložením záznamu.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``pian_save_metadata``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, ``save_metadata()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``pian_save_metadata``.


.. py:function:: samostatny_nalez_okres_delete_repository_container(sender, instance)

   Provádí operaci samostatny nalez okres delete repository container.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``samostatny_nalez_okres_delete_repository_container``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``samostatny_nalez_okres_delete_repository_container``.

