NOTIFIKACE_PROJEKTY views
=========================

Definice views.

Třídy
------

.. py:class:: PesListView

   Třída pohledu pro zobrazení listu hlídacích psů.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: PesCreateView

   Třída pohledu pro vytvořené hlídacího psa.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``PesFormset()``, ``PesNotificationsForm()``, pracuje se s atributy ``POST``, ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``redirect()``.


.. py:class:: PesSmazatView

   Třída pohledu pro smazání hlídacího psa pomocí modalu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_object_identification()

      Vrací object identification.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``filter()``, ``add_message()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``JsonResponse()``.

