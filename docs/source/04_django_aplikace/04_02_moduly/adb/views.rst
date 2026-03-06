ADB views
=========

Definice views.

Funkce
------

.. py:function:: zapsat(request, dj_ident_cely)

   Pohled pro vytvoření novího ADB.

   Pred uložením do DB se vytvoří relace na DB, nový ident celý je vygenerovaný a sm5 je přidané.
   Po úspešném uložení je uživatel presměrován na pohled detailu DJ.

   :param request: Parametr ``request`` se předává do volání ``CreateADBForm()``, ``add_message()``, pracuje se s atributy ``POST``, ``user``.
   :param dj_ident_cely: Identifikátor ``dj_ident_cely`` používaný pro dohledání cílového záznamu.

   :return: Vrací výsledek volání ``redirect()``.
   :raises DJNemaPianError: Vyvolá se při splnění podmínky ``not dj.pian``.

.. py:function:: smazat(request, ident_cely)

   Pohled pro smazání ADB.

   Po úspešném smazání je uživatel presměrován na pohled detailu DJ.

   :param request: Parametr ``request`` se předává do volání ``create_transaction()``, ``render()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``warning()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``response``, výsledek volání ``render()``.

.. py:function:: smazat_vb(request, ident_cely)

   Pohled pro smazání VB.

   Po úspešném smazání je uživatel presměrován na next_url z requestu.

   :param request: Parametr ``request`` se předává do volání ``FedoraTransaction()``, ``render()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``warning()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``response``, výsledek volání ``render()``.
