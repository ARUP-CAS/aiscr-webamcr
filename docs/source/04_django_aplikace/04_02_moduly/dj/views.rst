DJ views
========

Definice views.

Třídy
------

.. py:class:: ChangeKatastrView

   Třída pohledu pro editaci katastru dokumentační jednotky.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Další klíčové argumenty předané do základní třídy.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: HTTP GET požadavek.
      :param args: Poziční argumenty.
      :param kwargs: Klíčové argumenty předané do ``get_context_data()``.

      :return: Vrací výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: HTTP POST požadavek s daty formuláře pro změnu katastru.
      :param args: Poziční argumenty.
      :param kwargs: Klíčové argumenty.

      :return: Vrací výsledek volání ``JsonResponse()``.


Funkce
------

.. py:function:: detail(request, typ_vazby, ident_cely)

   Funkce pohledu pro editaci dokumentační jednotky a ADB.

   :param request: HTTP požadavek s daty formuláře DJ.
   :param typ_vazby: Typ vazby dokumentační jednotky (DJ nebo dokument).
   :param ident_cely: Identifikátor dokumentační jednotky.

   :return: Vrací proměnná ``response``.

.. py:function:: zapsat(request, arch_z_ident_cely)

   Funkce pohledu pro vytvoření dokumentační jednotky.

   :param request: Parametr ``request`` se předává do volání ``CreateDJForm()``, ``add_message()``, pracuje se s atributy ``POST``, ``user``.
   :param arch_z_ident_cely: Identifikátor ``arch_z_ident_cely`` používaný pro dohledání cílového záznamu.

   :return: Vrací proměnná ``redirect``.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání dokumentační jednotky.

   :param request: Parametr ``request`` se předává do volání ``create_transaction()``, ``add_message()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``warning()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
