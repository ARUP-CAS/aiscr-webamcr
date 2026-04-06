LOKALITA filtry
===============

Definice filtrů.

Třídy
------

.. py:class:: LokalitaFilter

   Třída pro základní filtrování lokality a jejich potomků.

   **Metody:**

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Parametr ``queryset`` předává se do volání ``filter_queryset()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

          :return: Vrací proměnná ``queryset``.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle názvu, popisu, uživatelského označení a poznámek.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_popisne_udaje``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: LokalitaFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Parametr ``form`` se předává do volání ``__init__()``.

