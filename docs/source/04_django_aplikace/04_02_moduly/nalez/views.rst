NALEZ views
===========

Definice views.

Funkce
------

.. py:function:: smazat_nalez(request, typ_vazby, typ, ident_cely)

   Funkce pohledu pro smazání nálezu předmětu nebo objektu pomocí modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``FedoraTransaction()``, ``add_message()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``typ_vazby``: Parametr ``typ_vazby`` slouží jako vstup pro logiku funkce ``smazat_nalez``.
   - ``typ``: Parametr ``typ`` ovlivňuje větvení podmínek.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``debug()``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: proměnná ``response``, výsledek volání ``render()``.


.. py:function:: edit_nalez(request, typ_vazby, komp_ident_cely)

   Funkce pohledu pro zapsání editace nálezu předmětu a objektu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``NalezObjektFormset()``, ``NalezPredmetFormset()``, pracuje se s atributy ``POST``, ``user``.
   - ``typ_vazby``: Parametr ``typ_vazby`` slouží jako vstup pro logiku funkce ``edit_nalez``.
   - ``komp_ident_cely``: Identifikátor ``komp_ident_cely`` používaný pro dohledání cílového záznamu.

   **Návratová hodnota:**

   Vrací proměnná ``response``.

