ARCH_Z validators
=================

Modul validators.

Funkce
------

.. py:function:: datum_max_1_mesic_v_budoucnosti(value)

   Metoda pro validaci dátumu měsíc do budoucnosti.

   **Parametry:**

   - ``value``: Parametr ``value`` ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací proměnná ``value``.

   **Výjimky:**

   - ``forms.ValidationError``: Vyvolá se při splnění podmínky ``value > datetime.date.today() + datetime.timedelta(days=30)``.

