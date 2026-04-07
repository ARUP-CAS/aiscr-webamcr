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

      :return: Vrací proměnná ``kwargs``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get_success_url()

      Vrací success url.

      :return: Vrací výsledek volání ``reverse()``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``post()``.
      :param args: Parametr ``args`` se předává do volání ``post()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``post()``.

      :return: Vrací výsledek volání ``JsonResponse()``.

   .. py:method:: form_valid()

      Zpracuje platný formulář editace neidentifikované akce a zobrazí zprávu o úspěchu.

      :param form: Validovaný formulář editace.

      :return: Vrací výsledek volání ``form_valid()``.

   .. py:method:: form_invalid()

      Zpracuje neplatný formulář editace neidentifikované akce a zobrazí chybovou zprávu.

      :param form: Nevalidní formulář s chybami.

      :return: Vrací výsledek volání ``form_invalid()``.

