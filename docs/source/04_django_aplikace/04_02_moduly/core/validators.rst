CORE validators
===============

Modul validators.

Funkce
------

.. py:function:: validate_phone_number(number)

   Validátor pro ověření telefonního čísla na správny formát.

   **Parametry:**

   - ``number``: Parametr ``number`` se předává do volání ``fullmatch()``, ``info()``, ovlivňuje větvení podmínek.

   **Výjimky:**

   - ``ValidationError``: Vyvolá se při splnění podmínky ``not regex_tel.fullmatch(number)``; nebo při zpracování zachycené výjimky typu ``Exception``.


.. py:function:: validate_date_min_1600(value)

   Validuje date min 1600.

   **Parametry:**

   - ``value``: Parametr ``value`` předává se do volání ``isinstance()``, pracuje se s atributy ``lower``, ``upper``, ovlivňuje větvení podmínek.

   **Výjimky:**

   - ``ValidationError``: Vyvolá se při splnění podmínky ``value.lower <= min_date``; nebo při splnění podmínky ``value.upper <= min_date``.

