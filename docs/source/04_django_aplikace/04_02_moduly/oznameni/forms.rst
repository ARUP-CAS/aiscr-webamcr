OZNAMENI formuláře
==================

Definice formulářů.

Třídy
------

.. py:class:: DateRangeField

   Třída pro správnu práci s date range.

   **Metody:**

   .. py:method:: to_python()

      Provádí operaci to python.

      :param value: Parametr ``value`` předává se do volání ``isinstance()``, pracuje se s atributy ``split``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``value``, výsledek volání ``DateRange()``.
      :raises ValidationError: Vyvolá se při splnění podmínky ``from_date is None or to_date is None``; nebo při zpracování zachycené výjimky typu ``Exception``.


.. py:class:: DateRangeWidget

   Třída pro správně zobrazení date range.

   **Metody:**

   .. py:method:: format_value()

      Provádí operaci format value.

      :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``str()``, pracuje se s atributy ``lower``, ``upper``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: None, hodnotu podle větve zpracování, výsledek volání ``str()``.


.. py:class:: OznamovatelForm

   Hlavní formulář pro vytvoření oznámení oznamovatelem.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.


.. py:class:: OznamovatelProjektForm

   Hlavní formulář pro vytvoření oznámení.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy a přidá pole optimistického zamykání do layoutu.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: OznamovatelProjektCreateForm

   Hlavní formulář pro vytvoření oznámení.

   **Metody:**

   .. py:method:: clean_send_mail()

      Provádí operaci clean send mail.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: ProjektOznameniForm

   Hlavní formulář pro editaci a doplňení oznamovatele do projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.


.. py:class:: FormWithCaptcha

   Hlavní formulář pro captchu.

