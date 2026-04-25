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

      :param get_response: Callable ze WSGI řetězce middleware, který vrátí response.

   .. py:method:: __call__()

      Zpracovává příchozí HTTP požadavek a kontroluje oprávnění uživatele.

      :param request: HTTP požadavek ze strany klienta.
      :return: HTTP response vygenerovaná aplikací.

   .. py:method:: process_view()

      Metoda pro kontrolu oprvávnení pro každý view.

      :param request: Parametr ``request`` se předává do volání ``append()``, ``check_concrete_permission()``, pracuje se s atributy ``user``, ``resolver_match``, ovlivňuje větvení podmínek.
      :param view_func: View funkce obalená dekorátorem nebo middlewarem.
      :param view_args: Dodatečné argumenty předané voláním.
      :param view_kwargs: Dodatečné argumenty předané voláním.

      :raises PermissionDenied: Vyvolá se při splnění podmínky ``any(tested)``.


.. py:class:: ErrorMiddleware

   Implementuje komponentu pro zachycení a zpracování chyb (ErrorMiddleware) v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param get_response: Callable ze WSGI řetězce middleware, který vrátí response.

   .. py:method:: __call__()

      Zpracovává příchozí HTTP požadavek.

      :param request: HTTP požadavek ze strany klienta.
      :return: HTTP response vygenerovaná aplikací.

   .. py:method:: process_exception()

      Zachycuje a zpracovává Fedora a databázové výjimky během zpracování požadavku.

      :param request: HTTP požadavek pro vykreslení chybové stránky.
      :param exception: Vyvolená výjimka během zpracování požadavku.
      :return: HTML error response nebo None pokud jde o neznámou výjimku.


.. py:class:: InactiveUserMiddleware

   Middleware detekující deaktivovaného uživatele s aktivní session.

   Před předáním požadavku do řetězce middleware zkontroluje, zda session
   obsahuje ID uživatele, který byl mezitím deaktivován. Pokud ano, session
   se zruší a uživatel je přesměrován na přihlašovací stránku s varovnou hláškou.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje middleware.

      :param get_response: Callable z middleware řetězce,
                           který zpracuje požadavek a vrátí response.

   .. py:method:: __call__()

      Zpracovává příchozí HTTP požadavek.

      :param request: HTTP požadavek ze strany klienta.
      :return: HTTP response vygenerovaná aplikací.

   .. py:method:: process_view()

      Před zpracováním požadavku ověří, zda uživatel v session není deaktivován.

      Pokud session obsahuje ID neaktivního uživatele, session se zruší a
      uživatel je přesměrován na přihlašovací stránku.

      :param request: Instance ``HttpRequest``.
      :param view_func: View funkce, kterou se chystá aplikace volat.
      :param view_args: Poziční argumenty pro view funkci.
      :param view_kwargs: Pojmenované argumenty pro view funkci.
      :return: přesměrování na login nebo žádná akce.


.. py:class:: StatusMessageMiddleware

   Middleware pro zobrazení stavových zpráv z Fedora transakcí skrze Redis.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param get_response: Callable ze WSGI řetězce middleware, který vrátí response.

   .. py:method:: __call__()

      Zpracovává příchozí HTTP požadavek.

      :param request: HTTP požadavek ze strany klienta.
      :return: HTTP response vygenerovaná aplikací.

   .. py:method:: _show_message()

      Zobrazí stavovou zprávu uživateli na základě výsledku Fedora transakce.

      :param value: Kódová hodnota stavu transakce z Redis (COMMITED nebo FAILED).
      :param request: HTTP požadavek pro přidání zprávy do session.
      :param redis_key: Klíč v Redis pro načtení stavových zpráv a smazání záznamu.

   .. py:method:: process_view()

      Detekuje a zobrazuje stavové zprávy Fedora transakcí pro AMČR identifikátory v URL.

      :param request: HTTP požadavek obsahující cestu s potenciálním AMČR identifikátorem.
      :param view_func: View funkce, kterou se chystá aplikace volat.
      :param view_args: Poziční argumenty pro view funkci.
      :param view_kwargs: Pojmenované argumenty pro view funkci.

