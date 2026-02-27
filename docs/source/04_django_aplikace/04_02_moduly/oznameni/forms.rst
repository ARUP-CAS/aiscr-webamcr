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

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: DateRangeWidget

   Třída pro správně zobrazení date range.

   **Metody:**

   .. py:method:: format_value()

      Provádí operaci format value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: OznamovatelForm

   Hlavní formulář pro vytvoření oznámení oznamovatelem.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: OznamovatelProjektForm

   Hlavní formulář pro vytvoření oznámení.


.. py:class:: OznamovatelProjektCreateForm

   Hlavní formulář pro vytvoření oznámení.

   **Metody:**

   .. py:method:: clean_send_mail()

      Provádí operaci clean send mail.

      :return: Vrací výsledek provedené operace.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: ProjektOznameniForm

   Hlavní formulář pro editaci a doplňení oznamovatele do projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: FormWithCaptcha

   Hlavní formulář pro captchu.

