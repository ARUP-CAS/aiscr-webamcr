PAS filtry
==========

Definice filtrů.

Třídy
------

.. py:class:: SamostatnyNalezFilter

   Třída pro zakladní filtrování samostatného nálezu a jejich potomků.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: filter_queryset()

      Filtruje queryset.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: filter_obdobi()

      Metoda pro filtrování podle období.

   .. py:method:: filter_druh_nalezu()

      Metoda pro filtrování podle druhu nálezu.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle lokalizace, poznámek a evidenčního čísla.

   .. py:method:: filter_by_oblast()

      Metoda pro filtrování podle oblasti.


.. py:class:: UzivatelSpolupraceFilter

   Třída pro zakladní filtrování uživatelské spolupráce a jejich potomků.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: filter_queryset()

      Filtruje queryset.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: SamostatnyNalezFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: UzivatelSpolupraceFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

