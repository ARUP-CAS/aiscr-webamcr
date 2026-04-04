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

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.



.. py:class:: PesCreateView

   Třída pohledu pro vytvořené hlídacího psa.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``PesFormset()``, ``PesNotificationsForm()``, pracuje se s atributy ``POST``, ``user``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      **Návratová hodnota:**

      Vrací výsledek volání ``redirect()``.



.. py:class:: PesSmazatView

   Třída pohledu pro smazání hlídacího psa pomocí modalu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: get_object_identification()

      Vrací object identification.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací výsledek volání ``render_to_response()``.


   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``filter()``, ``add_message()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.


