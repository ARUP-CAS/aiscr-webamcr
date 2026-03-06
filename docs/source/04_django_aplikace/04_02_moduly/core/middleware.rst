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

      :param request: Django HTTP požadavek použitý při zpracování.

   .. py:method:: process_view()

      Metoda pro kontrolu oprvávnení pro každý view.

      :param request: Aktuální HTTP request předaný view/funkci.
      :param view_func: View funkce obalená dekorátorem nebo middlewarem.
      :param view_args: Dodatečné argumenty předané voláním.
      :param view_kwargs: Dodatečné argumenty předané voláním.


.. py:class:: ErrorMiddleware

   Implementuje komponentu ``ErrorMiddleware`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param get_response: Textový nebo strukturální vstup `get_response` používaný při sestavení nebo zpracování obsahu.

   .. py:method:: __call__()

      Provádí operaci call.

      :param request: Django HTTP požadavek použitý při zpracování.

   .. py:method:: process_exception()

      Provádí operaci process exception.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param exception: Číselná hodnota ``exception`` použitá při výpočtu nebo transformaci.


.. py:class:: StatusMessageMiddleware

   Implementuje komponentu ``StatusMessageMiddleware`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param get_response: Textový nebo strukturální vstup `get_response` používaný při sestavení nebo zpracování obsahu.

   .. py:method:: __call__()

      Provádí operaci call.

      :param request: Django HTTP požadavek použitý při zpracování.

   .. py:method:: _show_message()

      Provádí operaci show message.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :param request: Django HTTP požadavek použitý při zpracování.
      :param redis_key: Textový název nebo klíč ``redis_key`` používaný v rámci operace.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: process_view()

      Provádí operaci process view.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param view_func: View funkce obalená dekorátorem nebo middlewarem.
      :param view_args: Dodatečné argumenty předané voláním.
      :param view_kwargs: Dodatečné argumenty předané voláním.

