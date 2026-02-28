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

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.

   .. py:method:: filter_obdobi()

      Metoda pro filtrování podle období.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_druh_nalezu()

      Metoda pro filtrování podle druhu nálezu.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle lokalizace, poznámek a evidenčního čísla.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_by_oblast()

      Metoda pro filtrování podle oblasti.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.


.. py:class:: UzivatelSpolupraceFilter

   Třída pro zakladní filtrování uživatelské spolupráce a jejich potomků.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.


.. py:class:: SamostatnyNalezFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Vstupní hodnota ``form`` pro danou operaci.


.. py:class:: UzivatelSpolupraceFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Vstupní hodnota ``form`` pro danou operaci.

