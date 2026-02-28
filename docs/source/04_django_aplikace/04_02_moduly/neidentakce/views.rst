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

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_success_url()

      Vrací success url.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.

   .. py:method:: form_invalid()

      Provádí operaci form invalid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.

