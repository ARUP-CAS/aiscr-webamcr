FEDORA_MANAGEMENT decorators
============================

Modul decorators.

Funkce
------

.. py:function:: handle_fedora_error(view_func, additional_exceptions)

   Zpracuje fedora error.

   :param view_func: View funkce obalená dekorátorem nebo middlewarem.
   :param additional_exceptions: Číselná hodnota ``additional_exceptions`` použitá při výpočtu nebo transformaci.

   :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``decorator``, výsledek volání ``decorator()``.
