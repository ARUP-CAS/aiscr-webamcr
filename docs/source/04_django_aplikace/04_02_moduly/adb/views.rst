ADB views
=========

Definice views.

Funkce
------

.. py:function:: zapsat(request, dj_ident_cely)

   Pohled pro vytvoření novího ADB.

   Pred uložením do DB se vytvoří relace na DB, nový ident celý je vygenerovaný a sm5 je přidané.
   Po úspešném uložení je uživatel presměrován na pohled detailu DJ.

   :param request: Popis parametru ``request``.
   :param dj_ident_cely: Popis parametru ``dj_ident_cely``.

.. py:function:: smazat(request, ident_cely)

   Pohled pro smazání ADB.

   Po úspešném smazání je uživatel presměrován na pohled detailu DJ.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: smazat_vb(request, ident_cely)

   Pohled pro smazání VB.

   Po úspešném smazání je uživatel presměrován na next_url z requestu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.
