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

      :param request: Parametr ``request`` předává se do volání ``get_response()``, ``_resolve_view_info()``, pracuje se s atributy ``get_full_path``, ``user``.

      :return: Vrací proměnná ``response``.
      :raises Exception: Vyvolá se při zpracování zachycené výjimky typu ``Exception``.

   .. py:method:: get_request_url()

      Vrací request url.

      :return: Vrací výsledek volání ``getattr()``.

   .. py:method:: get_user_id()

      Vrací user id.

      :return: Vrací výsledek volání ``getattr()``.


Funkce
------

.. py:function:: get_slow_request_settings()

   Vrací slow request settings.

   :return: Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, float.

.. py:function:: _resolve_view_info(request)

   Vrátí dict s informacemi o view: view_name, view_module, kwargs.

   :param request: Parametr ``request`` předává se do volání ``resolve()``, pracuje se s atributy ``path_info``.
   :return: Vrací hodnotu typu ``dict`` (slovník).
