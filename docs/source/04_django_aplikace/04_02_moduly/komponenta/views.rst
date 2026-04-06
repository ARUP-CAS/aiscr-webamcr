KOMPONENTA views
================

Definice views.

Funkce
------

.. py:function:: detail(request, typ_vazby, ident_cely)

   Zpracuje uložení editace komponenty a souvisejících nálezových formulářů.

   :param request: HTTP požadavek s daty editace komponenty.
   :param typ_vazby: Typ vazby, který určuje návratovou URL po uložení.
   :param ident_cely: Identifikátor upravované komponenty.

       :return: Vrací proměnná ``response``.

.. py:function:: zapsat(request, typ_vazby, dj_ident_cely)

   Vytvoří novou komponentu pro dokumentační jednotku nebo část dokumentu.

   :param request: HTTP požadavek obsahující data nově zakládané komponenty.
   :param typ_vazby: Typ vazby určující, zda jde o dokument nebo dokumentační jednotku.
   :param dj_ident_cely: Identifikátor cílové dokumentační jednotky nebo části dokumentu.

       :return: Vrací proměnná ``response``.

.. py:function:: smazat(request, typ_vazby, ident_cely)

   Odstraní komponentu a vrátí cílovou URL pro následný redirect.

   :param request: HTTP požadavek; při POST provádí vlastní smazání komponenty.
   :param typ_vazby: Typ vazby předaný URL konfigurací.
   :param ident_cely: Identifikátor mazané komponenty.

       :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
