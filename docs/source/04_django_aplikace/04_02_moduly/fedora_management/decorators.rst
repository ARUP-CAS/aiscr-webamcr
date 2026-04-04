FEDORA_MANAGEMENT decorators
============================

Modul decorators.

Funkce
------

.. py:function:: handle_fedora_error(view_func, additional_exceptions)

   Zpracuje fedora error.

   **Parametry:**

   - ``view_func``: View funkce obalená dekorátorem nebo middlewarem.
   - ``additional_exceptions``: Číselná hodnota ``additional_exceptions`` použitá při výpočtu nebo transformaci.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: proměnná ``decorator``, výsledek volání ``decorator()``.

