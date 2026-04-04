PAS filtry
==========

Definice filtrů.

Třídy
------

.. py:class:: SamostatnyNalezFilter

   Třída pro základní filtrování samostatného nálezu a jejich potomků.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``get``.


   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` předává se do volání ``filter_queryset()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací proměnná ``queryset``.


   .. py:method:: filter_obdobi()

      Filtruje samostatné nálezy podle období.

      **Parametry:**

      - ``queryset``: Soubor záznamů k filtrování
      - ``name``: Název pole pro filtrování
      - ``value``: Hodnota pro filtrování

      **Návratová hodnota:**

      Vrací filtrovaný ``queryset``


   .. py:method:: filter_druh_nalezu()

      Filtruje samostatné nálezy podle typu.

      **Parametry:**

      - ``queryset``: Soubor záznamů k filtrování
      - ``name``: Název pole pro filtrování
      - ``value``: Hodnota pro filtrování

      **Návratová hodnota:**

      Vrací filtrovaný ``queryset``


   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle lokalizace, poznámek a evidenčního čísla.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_popisne_udaje``.
      - ``value``: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``filter()``.


   .. py:method:: filter_by_oblast()

      Metoda pro filtrování podle oblasti.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_by_oblast``.
      - ``value``: Parametr ``value`` ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``filter()``, proměnná ``queryset``.



.. py:class:: UzivatelSpolupraceFilter

   Třída pro základní filtrování uživatelské spolupráce a jejich potomků.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``get``.


   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` předává se do volání ``filter_queryset()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací proměnná ``queryset``.



.. py:class:: SamostatnyNalezFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``form``: Parametr ``form`` se předává do volání ``__init__()``.



.. py:class:: UzivatelSpolupraceFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``form``: Parametr ``form`` se předává do volání ``__init__()``.


