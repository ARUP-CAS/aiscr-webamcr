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

      **Parametry:**

      - ``get_response``: Textový nebo strukturální vstup `get_response` používaný při sestavení nebo zpracování obsahu.


   .. py:method:: __call__()

      Zpracuje požadavek a zaznamenává informace o volání (URL, uživatel, čas, výjimky).

      **Parametry:**

      - ``request``: Objekt požadavku Django.

      **Návratová hodnota:**

      Objekt odpovědi Django.

      **Výjimky:**

      - ``Exception``: Jakákoliv výjimka zachycená během zpracování.


   .. py:method:: get_request_url()

      Vrací request url.

      **Návratová hodnota:**

      Vrací výsledek volání ``getattr()``.


   .. py:method:: get_user_id()

      Vrací user id.

      **Návratová hodnota:**

      Vrací výsledek volání ``getattr()``.



Funkce
------

.. py:function:: get_slow_request_settings()

   Vrací slow request settings.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, float.


.. py:function:: _get_anonymous()

   Vrací identifikátor anonymního uživatele z cache nebo databáze.

   **Návratová hodnota:**

   Identifikátor uživatele (ident_cely) nebo řetězec "anonymous".


.. py:function:: _resolve_view_info(request)

   Vrátí dict s informacemi o view: view_name, view_module, kwargs.

   **Parametry:**

   - ``request``: Parametr ``request`` předává se do volání ``resolve()``, pracuje se s atributy ``path_info``.

   **Návratová hodnota:**

   Vrací hodnotu typu ``dict`` (slovník).

