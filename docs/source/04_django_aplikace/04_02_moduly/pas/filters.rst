PAS filtry
==========

Definice filtrů.

Třídy
------

.. py:class:: SamostatnyNalezFilter

   Třída pro základní filtrování samostatného nálezu a jejich potomků.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: filter_queryset()

   .. py:method:: filter_obdobi()

      Metoda pro filtrování podle období.

   .. py:method:: filter_druh_nalezu()

      Metoda pro filtrování podle druhu nálezu.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle lokalizace, poznámek a evidenčního čísla.

   .. py:method:: filter_by_oblast()

      Metoda pro filtrování podle oblasti.


.. py:class:: UzivatelSpolupraceFilter

   Třída pro základní filtrování uživatelské spolupráce a jejich potomků.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: filter_queryset()


.. py:class:: SamostatnyNalezFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: UzivatelSpolupraceFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

