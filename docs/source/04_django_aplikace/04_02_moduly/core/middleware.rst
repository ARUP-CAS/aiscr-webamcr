CORE middleware
===============

Modul middleware.

Třídy
------

.. py:class:: PermissionMiddleware

   Middleware třída užívaná pro kontrolu oprávnení.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param get_response: Textový nebo strukturální vstup `get_response` používaný při sestavení nebo zpracování obsahu.

   .. py:method:: __call__()

      Provádí operaci call.

      :param request: Parametr ``request`` předává se do volání ``get_response()``.

      :return: Vrací proměnná ``response``.

   .. py:method:: process_view()

      Metoda pro kontrolu oprvávnení pro každý view.

      :param request: Parametr ``request`` se předává do volání ``append()``, ``check_concrete_permission()``, pracuje se s atributy ``user``, ``resolver_match``, ovlivňuje větvení podmínek.
      :param view_func: View funkce obalená dekorátorem nebo middlewarem.
      :param view_args: Dodatečné argumenty předané voláním.
      :param view_kwargs: Dodatečné argumenty předané voláním.

      :raises PermissionDenied: Vyvolá se při splnění podmínky ``any(tested)``.


.. py:class:: ErrorMiddleware

   Implementuje komponentu ``ErrorMiddleware`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param get_response: Textový nebo strukturální vstup `get_response` používaný při sestavení nebo zpracování obsahu.

   .. py:method:: __call__()

      Provádí operaci call.

      :param request: Parametr ``request`` předává se do volání ``get_response()``.

      :return: Vrací proměnná ``response``.

   .. py:method:: process_exception()

      Provádí operaci process exception.

      :param request: Parametr ``request`` předává se do volání ``render()``, vstupuje do návratové hodnoty.
      :param exception: Číselná hodnota ``exception`` použitá při výpočtu nebo transformaci.

      :return: Vrací výsledek volání ``render()``.


.. py:class:: StatusMessageMiddleware

   Implementuje komponentu ``StatusMessageMiddleware`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param get_response: Textový nebo strukturální vstup `get_response` používaný při sestavení nebo zpracování obsahu.

   .. py:method:: __call__()

      Provádí operaci call.

      :param request: Parametr ``request`` předává se do volání ``get_response()``.

      :return: Vrací proměnná ``response``.

   .. py:method:: _show_message()

      Provádí operaci show message.

      :param value: Parametr ``value`` předává se do volání ``int()``, pracuje se s atributy ``decode``, ovlivňuje větvení podmínek.
      :param request: Parametr ``request`` předává se do volání ``add_message()``.
      :param redis_key: Textový název nebo klíč ``redis_key`` používaný v rámci operace.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: process_view()

      Provádí operaci process view.

      :param request: Parametr ``request`` předává se do volání ``findall()``, ``get_transaction_redis_key()``, pracuje se s atributy ``path``, ``user``.
      :param view_func: View funkce obalená dekorátorem nebo middlewarem.
      :param view_args: Dodatečné argumenty předané voláním.
      :param view_kwargs: Dodatečné argumenty předané voláním.

