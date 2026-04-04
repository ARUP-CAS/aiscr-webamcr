NEIDENTAKCE views
=================

Definice views.

Třídy
------

.. py:class:: NeidentAkceEditView

   Třída pohledu pro editaci neident akce pomocí modalu.

   **Metody:**

   .. py:method:: get_form_kwargs()

      Vrací form kwargs.

      **Návratová hodnota:**

      Vrací proměnná ``kwargs``.


   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: get_success_url()

      Vrací success url.

      **Návratová hodnota:**

      Vrací výsledek volání ``reverse()``.


   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``post()``.
      - ``args``: Parametr ``args`` se předává do volání ``post()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``post()``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.


   .. py:method:: form_valid()

      Zpracuje platný formulář editace neidentifikované akce a zobrazí zprávu o úspěchu.

      **Parametry:**

      - ``form``: Validovaný formulář editace.

      **Návratová hodnota:**

      Vrací výsledek volání ``form_valid()``.


   .. py:method:: form_invalid()

      Zpracuje neplatný formulář editace neidentifikované akce a zobrazí chybovou zprávu.

      **Parametry:**

      - ``form``: Nevalidní formulář s chybami.

      **Návratová hodnota:**

      Vrací výsledek volání ``form_invalid()``.


