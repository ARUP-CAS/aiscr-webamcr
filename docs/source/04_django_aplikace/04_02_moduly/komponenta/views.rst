KOMPONENTA views
================

Definice views.

Funkce
------

.. py:function:: detail(request, typ_vazby, ident_cely)

   Zpracuje uložení editace komponenty a souvisejících nálezových formulářů.

   **Parametry:**

   - ``request``: HTTP požadavek s daty editace komponenty.
   - ``typ_vazby``: Typ vazby, který určuje návratovou URL po uložení.
   - ``ident_cely``: Identifikátor upravované komponenty.

   **Návratová hodnota:**

   Vrací proměnná ``response``.


.. py:function:: zapsat(request, typ_vazby, dj_ident_cely)

   Vytvoří novou komponentu pro dokumentační jednotku nebo část dokumentu.

   **Parametry:**

   - ``request``: HTTP požadavek obsahující data nově zakládané komponenty.
   - ``typ_vazby``: Typ vazby určující, zda jde o dokument nebo dokumentační jednotku.
   - ``dj_ident_cely``: Identifikátor cílové dokumentační jednotky nebo části dokumentu.

   **Návratová hodnota:**

   Vrací proměnná ``response``.


.. py:function:: smazat(request, typ_vazby, ident_cely)

   Odstraní komponentu a vrátí cílovou URL pro následný redirect.

   **Parametry:**

   - ``request``: HTTP požadavek; při POST provádí vlastní smazání komponenty.
   - ``typ_vazby``: Typ vazby předaný URL konfigurací.
   - ``ident_cely``: Identifikátor mazané komponenty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

