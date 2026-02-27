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

      :param get_response: Vstupní hodnota ``get_response`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: __call__()

      Provádí operaci call.

      :param request: Django HTTP požadavek použitý při zpracování.
      :return: Vrací výsledek provedené operace.

   .. py:method:: process_view()

      Metoda pro kontrolu oprvávnení pro každý view.


.. py:class:: ErrorMiddleware

   Implementuje komponentu ``ErrorMiddleware`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param get_response: Vstupní hodnota ``get_response`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: __call__()

      Provádí operaci call.

      :param request: Django HTTP požadavek použitý při zpracování.
      :return: Vrací výsledek provedené operace.

   .. py:method:: process_exception()

      Provádí operaci process exception.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param exception: Vstupní hodnota ``exception`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: StatusMessageMiddleware

   Implementuje komponentu ``StatusMessageMiddleware`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param get_response: Vstupní hodnota ``get_response`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: __call__()

      Provádí operaci call.

      :param request: Django HTTP požadavek použitý při zpracování.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _show_message()

      Provádí operaci show message.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :param request: Django HTTP požadavek použitý při zpracování.
      :param redis_key: Vstupní hodnota ``redis_key`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: process_view()

      Provádí operaci process view.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param view_func: Vstupní hodnota ``view_func`` pro danou operaci.
      :param view_args: Vstupní hodnota ``view_args`` pro danou operaci.
      :param view_kwargs: Vstupní hodnota ``view_kwargs`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

