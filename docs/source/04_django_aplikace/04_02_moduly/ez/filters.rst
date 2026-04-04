EZ filtry
=========

Definice filtrů.

Třídy
------

.. py:class:: ExterniZdrojFilter

   Třída pro základní filtrování externího zdroju a jejich potomků.

   **Metody:**

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` předává se do volání ``filter_queryset()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací proměnná ``queryset``.


   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle názvu, edice, sborníku, časopisu, isbn, issn, roku vydání a poznámek.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (nevyužit přímo, předán Django filtersetem).
      - ``value``: Hledaný řetězec, podle nějž se filtruje ve více textových polích externího zdroje.

      **Návratová hodnota:**

      Vrací výsledek volání ``filter()``.


   .. py:method:: filter_akce_ident()

      Metoda pro filtrování podle identu celý akce.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (nevyužit přímo, předán Django filtersetem).
      - ``value``: Hledaný identifikátor akce, podle nějž se filtruje přes propojené archeologické záznamy typu akce.

      **Návratová hodnota:**

      Vrací výsledek volání ``filter()``.


   .. py:method:: filter_lokalita_ident()

      Metoda pro filtrování podle identu celý lokality.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (nevyužit přímo, předán Django filtersetem).
      - ``value``: Hledaný identifikátor lokality, podle nějž se filtruje přes propojené archeologické záznamy typu lokalita.

      **Návratová hodnota:**

      Vrací výsledek volání ``filter()``.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``get``.



.. py:class:: ExterniZdrojFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``form``: Parametr ``form`` se předává do volání ``__init__()``.


