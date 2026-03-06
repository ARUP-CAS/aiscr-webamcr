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

   .. py:method:: __call__()

   .. py:method:: get_request_url()

   .. py:method:: get_user_id()


Funkce
------

.. py:function:: get_slow_request_settings()

   Popis není k dispozici.

.. py:function:: _get_anonymous()

   Popis není k dispozici.

.. py:function:: _resolve_view_info(request)

   Vrátí dict s informacemi o view: view_name, view_module, kwargs.
