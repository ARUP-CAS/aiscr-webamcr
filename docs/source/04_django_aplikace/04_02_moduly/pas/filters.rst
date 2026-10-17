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

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``get``.

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Parametr ``queryset`` předává se do volání ``filter_queryset()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

      :return: Vrací proměnná ``queryset``.

   .. py:method:: filter_obdobi()

      Filtruje samostatné nálezy podle období.

      :param queryset: Soubor záznamů k filtrování
      :param name: Název pole pro filtrování
      :param value: Hodnota pro filtrování

      :return: Vrací filtrovaný ``queryset``

   .. py:method:: filter_druh_nalezu()

      Filtruje samostatné nálezy podle typu.

      :param queryset: Soubor záznamů k filtrování
      :param name: Název pole pro filtrování
      :param value: Hodnota pro filtrování

      :return: Vrací filtrovaný ``queryset``

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle lokalizace, poznámek a evidenčního čísla.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_popisne_udaje``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``filter()``.

   .. py:method:: filter_by_oblast()

      Metoda pro filtrování podle oblasti.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_by_oblast``.
      :param value: Parametr ``value`` ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``filter()``, proměnná ``queryset``.

   .. py:method:: filter_organizace_nalezu()

      Filtruje nálezy, u kterých je některá ze zvolených organizací organizací projektu nebo cílovou organizací nálezu.

      Podmínka odpovídá vlastnictví nálezu organizací (viz ``PasPermissionFilterMixin.add_ownership_lookup``).

      :param queryset: Queryset samostatných nálezů, který se dále zužuje.
      :param name: Název filtru (nepoužívá se).
      :param value: Seznam zvolených organizací.

      :return: Queryset nálezů, kde ``projekt__organizace`` nebo ``predano_organizace`` je mezi zvolenými organizacemi;
          při nevyplněném filtru nezměněný ``queryset``.


.. py:class:: UzivatelSpolupraceFilter

   Třída pro základní filtrování uživatelské spolupráce a jejich potomků.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``get``.

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Parametr ``queryset`` předává se do volání ``filter_queryset()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

      :return: Vrací proměnná ``queryset``.


.. py:class:: SamostatnyNalezFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Parametr ``form`` se předává do volání ``__init__()``.


.. py:class:: UzivatelSpolupraceFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Parametr ``form`` se předává do volání ``__init__()``.

