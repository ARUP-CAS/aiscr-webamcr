CORE log_middleware
===================

Modul log_middleware.

Třídy
------

.. py:class:: LogMiddleware

   Middleware, který:
   - ukládá do thread-local: url, user_id
   - měří duration a zapisuje strukturovaný log po odpovědi

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param get_response: Vstupní hodnota ``get_response`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: __call__()

      Provádí operaci call.

      :param request: Django HTTP požadavek použitý při zpracování.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_request_url()

      Vrací request url.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_user_id()

      Vrací user id.

      :return: Vrací načtená data odpovídající vstupním parametrům.


Funkce
------

.. py:function:: get_slow_request_settings()

   Vrací slow request settings.

   :return: Vrací načtená data odpovídající vstupním parametrům.

.. py:function:: _resolve_view_info(request)

   Vrátí dict s informacemi o view: view_name, view_module, kwargs.
