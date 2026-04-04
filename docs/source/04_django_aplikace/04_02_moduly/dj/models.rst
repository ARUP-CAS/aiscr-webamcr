DJ modely
=========

Definice modelů.

Třídy
------

.. py:class:: DokumentacniJednotka

   Databázový model dokumentační jednotky.

   **Metody:**

   .. py:method:: get_absolute_url()

      Metoda pro získání absolutní URL archeologického záznamu pro dokumentační jednotku.

      **Návratová hodnota:**

      Vrací výsledek volání ``reverse()``.


   .. py:method:: ident_cely_safe()

      Vrátí identifikátor dokumentační jednotky s pomlčkami nahrazenými podtržítky (vhodný pro HTML atributy).

      **Návratová hodnota:**

      Vrací výsledek volání ``replace()``.


   .. py:method:: has_adb()

      Metoda pro ověření, jestli dokumentační jednotka má ADB.

      **Návratová hodnota:**

      Vrací proměnná ``has_adb``.


   .. py:method:: get_permission_object()

      Vrací permission object.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: initial_pian()

      Vrátí objekt Pian na základě initial_pian_id (líné načtení).

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get()``, None.


