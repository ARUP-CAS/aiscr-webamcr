CORE log_middleware
===================

Modul log_middleware.

Třídy
------

.. py:class:: LogMiddleware

   Middleware, který: v aplikaci.

   - ukládá do thread-local: url, user_id
   - měří duration a zapisuje strukturovaný log po odpovědi

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param get_response: Textový nebo strukturální vstup `get_response` používaný při sestavení nebo zpracování obsahu.

   .. py:method:: __call__()

      Provádí operaci call.

      :param request: Django HTTP požadavek použitý při zpracování.

   .. py:method:: get_request_url()

      Vrací request url.

   .. py:method:: get_user_id()

      Vrací user id.


Funkce
------

.. py:function:: get_slow_request_settings()

   Vrací slow request settings.

.. py:function:: _resolve_view_info(request)

   Vrátí dict s informacemi o view: view_name, view_module, kwargs.
