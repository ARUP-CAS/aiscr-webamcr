OZNAMENI formuláře
==================

Definice formulářů.

Třídy
------

.. py:class:: DateRangeField

   Třída pro správnu práci s date range.

   **Metody:**

   .. py:method:: to_python()


.. py:class:: DateRangeWidget

   Třída pro správně zobrazení date range.

   **Metody:**

   .. py:method:: format_value()


.. py:class:: OznamovatelForm

   Hlavní formulář pro vytvoření oznámení oznamovatelem.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: OznamovatelProjektForm

   Hlavní formulář pro vytvoření oznámení.


.. py:class:: OznamovatelProjektCreateForm

   Hlavní formulář pro vytvoření oznámení.

   **Metody:**

   .. py:method:: clean_send_mail()

   .. py:method:: __init__()


.. py:class:: ProjektOznameniForm

   Hlavní formulář pro editaci a doplňení oznamovatele do projektu.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: FormWithCaptcha

   Hlavní formulář pro captchu.
