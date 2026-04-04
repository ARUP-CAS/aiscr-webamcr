CORE middleware
===============

Modul middleware.

Třídy
------

.. py:class:: PermissionMiddleware

   Middleware třída užívaná pro kontrolu oprávnění.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``get_response``: Callable ze WSGI řetězce middleware, který vrátí response.


   .. py:method:: __call__()

      Zpracovává příchozí HTTP požadavek a kontroluje oprávnění uživatele.

      **Parametry:**

      - ``request``: HTTP požadavek ze strany klienta.

      **Návratová hodnota:**

      HTTP response vygenerovaná aplikací.


   .. py:method:: process_view()

      Metoda pro kontrolu oprvávnení pro každý view.

      **Parametry:**

      - ``request``: Parametr ``request`` se předává do volání ``append()``, ``check_concrete_permission()``, pracuje se s atributy ``user``, ``resolver_match``, ovlivňuje větvení podmínek.
      - ``view_func``: View funkce obalená dekorátorem nebo middlewarem.
      - ``view_args``: Dodatečné argumenty předané voláním.
      - ``view_kwargs``: Dodatečné argumenty předané voláním.

      **Výjimky:**

      - ``PermissionDenied``: Vyvolá se při splnění podmínky ``any(tested)``.



.. py:class:: ErrorMiddleware

   Implementuje komponentu pro zachycení a zpracování chyb (ErrorMiddleware) v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``get_response``: Callable ze WSGI řetězce middleware, který vrátí response.


   .. py:method:: __call__()

      Zpracovává příchozí HTTP požadavek.

      **Parametry:**

      - ``request``: HTTP požadavek ze strany klienta.

      **Návratová hodnota:**

      HTTP response vygenerovaná aplikací.


   .. py:method:: process_exception()

      Zachycuje a zpracovává Fedora a databázové výjimky během zpracování požadavku.

      **Parametry:**

      - ``request``: HTTP požadavek pro vykreslení chybové stránky.
      - ``exception``: Vyvolená výjimka během zpracování požadavku.

      **Návratová hodnota:**

      HTML error response nebo None pokud jde o neznámou výjimku.



.. py:class:: InactiveUserMiddleware

   Middleware zachytávající ``ValidationError`` s kódem ``inactive``,
   která může vzniknout při vyhodnocení ``request.user`` u deaktivovaného
   uživatele s stále aktivní session.

   Pokud k této chybě dojde, session se zruší a uživatel je přesměrován
   na přihlašovací stránku s varovnou hláškou.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje middleware.

      **Parametry:**

      - ``get_response``: Callable z middleware řetězce, který zpracuje požadavek a vrátí response.


   .. py:method:: __call__()

      Obalí zpracování požadavku a zachytí ``ValidationError`` s kódem
      ``inactive``, která může vzniknout při vyhodnocení ``request.user``.

      Pokud je chyba zachycena, session se zruší a uživatel je
      přesměrován na přihlašovací stránku.

      **Parametry:**

      - ``request``: Instance ``HttpRequest``.

      **Návratová hodnota:**

      Standardní ``response`` nebo přesměrování na login.



.. py:class:: StatusMessageMiddleware

   Middleware pro zobrazení stavových zpráv z Fedora transakcí skrze Redis.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``get_response``: Callable ze WSGI řetězce middleware, který vrátí response.


   .. py:method:: __call__()

      Zpracovává příchozí HTTP požadavek.

      **Parametry:**

      - ``request``: HTTP požadavek ze strany klienta.

      **Návratová hodnota:**

      HTTP response vygenerovaná aplikací.


   .. py:method:: _show_message()

      Zobrazí stavovou zprávu uživateli na základě výsledku Fedora transakce.

      **Parametry:**

      - ``value``: Kódová hodnota stavu transakce z Redis (COMMITED nebo FAILED).
      - ``request``: HTTP požadavek pro přidání zprávy do session.
      - ``redis_key``: Klíč v Redis pro načtení stavových zpráv a smazání záznamu.


   .. py:method:: process_view()

      Detekuje a zobrazuje stavové zprávy Fedora transakcí pro AMČR identifikátory v URL.

      **Parametry:**

      - ``request``: HTTP požadavek obsahující cestu s potenciálním AMČR identifikátorem.
      - ``view_func``: View funkce, kterou se chystá aplikace volat.
      - ``view_args``: Poziční argumenty pro view funkci.
      - ``view_kwargs``: Pojmenované argumenty pro view funkci.


