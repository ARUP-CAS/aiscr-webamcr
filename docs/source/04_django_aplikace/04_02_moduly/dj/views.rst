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

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Další klíčové argumenty předané do základní třídy.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: HTTP GET požadavek.
      - ``args``: Poziční argumenty.
      - ``kwargs``: Klíčové argumenty předané do ``get_context_data()``.

      **Návratová hodnota:**

      Vrací výsledek volání ``render_to_response()``.


   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      **Parametry:**

      - ``request``: HTTP POST požadavek s daty formuláře pro změnu katastru.
      - ``args``: Poziční argumenty.
      - ``kwargs``: Klíčové argumenty.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



Funkce
------

.. py:function:: detail(request, typ_vazby, ident_cely)

   Funkce pohledu pro editaci dokumentační jednotky a ADB.

   **Parametry:**

   - ``request``: HTTP požadavek s daty formuláře DJ.
   - ``typ_vazby``: Typ vazby dokumentační jednotky (DJ nebo dokument).
   - ``ident_cely``: Identifikátor dokumentační jednotky.

   **Návratová hodnota:**

   Vrací proměnná ``response``.


.. py:function:: zapsat(request, arch_z_ident_cely)

   Funkce pohledu pro vytvoření dokumentační jednotky.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``CreateDJForm()``, ``add_message()``, pracuje se s atributy ``POST``, ``user``.
   - ``arch_z_ident_cely``: Identifikátor ``arch_z_ident_cely`` používaný pro dohledání cílového záznamu.

   **Návratová hodnota:**

   Vrací proměnná ``redirect``.


.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání dokumentační jednotky.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``create_transaction()``, ``add_message()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``warning()``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

