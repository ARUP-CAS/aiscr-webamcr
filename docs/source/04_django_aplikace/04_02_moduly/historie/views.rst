HISTORIE views
==============

Definice views.

Třídy
------

.. py:class:: HistorieListView

   Třida pohledu pro zobrazení historie záznamu.
Třída se dědí pro jednotlivá historie.

   **Metody:**

   .. py:method:: get_lookup_value()

      Vrátí hodnotu z URL podle lookup_kwarg.

   .. py:method:: prepare_queryset()

      Potomek může přepsat pro vlastní řazení nebo dodatečné filtry.

   .. py:method:: add_extra_context()

      Potomek může přepsat a doplnit další hodnoty do contextu.

   .. py:method:: get_queryset()

   .. py:method:: get_header_config()

      Potomek musí vrátit {'url': ..., 'icon': ..., 'text': ...}

   .. py:method:: add_fedora_history()

      Pokud potomek definuje fedora_model, automaticky se načte
      metadata historie z Fedory a přidá se druhá tabulka fedora_table.

   .. py:method:: get_table()

   .. py:method:: get_context_data()


.. py:class:: ProjektHistorieListView

   Třida pohledu pro zobrazení historie projektu.

   **Metody:**

   .. py:method:: get_header_config()


.. py:class:: AkceHistorieListView

   Třida pohledu pro zobrazení historie akcií.

   **Metody:**

   .. py:method:: get_header_config()


.. py:class:: DokumentHistorieListView

   Třida pohledu pro zobrazení historie dokumentů.

   **Metody:**

   .. py:method:: get_header_config()

   .. py:method:: add_extra_context()


.. py:class:: SamostatnyNalezHistorieListView

   Třida pohledu pro zobrazení historie samostatných nálezů.

   **Metody:**

   .. py:method:: get_header_config()


.. py:class:: SpolupraceHistorieListView

   Třida pohledu pro zobrazení historie spolupráce.

   **Metody:**

   .. py:method:: get_header_config()


.. py:class:: SouborHistorieListView

   Třida pohledu pro zobrazení historie souborů.

   **Metody:**

   .. py:method:: prepare_queryset()

   .. py:method:: add_extra_context()

   .. py:method:: get_header_config()


.. py:class:: LokalitaHistorieListView

   Třida pohledu pro zobrazení historie lokalit.

   **Metody:**

   .. py:method:: get_header_config()


.. py:class:: UzivatelHistorieListView

   Třida pohledu pro zobrazení historie uživatele.

   **Metody:**

   .. py:method:: get_header_config()


.. py:class:: ExterniZdrojHistorieListView

   Třida pohledu pro zobrazení historie externích zdrojů.

   **Metody:**

   .. py:method:: get_header_config()


.. py:class:: PianHistorieListView

   Třida pohledu pro zobrazení historie Pianu.

   **Metody:**

   .. py:method:: get_header_config()


.. py:class:: PianLokalitaHistorieListView

   Třida pohledu pro zobrazení historie Pianu.

   **Metody:**

   .. py:method:: get_header_config()


.. py:class:: AdbHistorieListView

   Třida pohledu pro zobrazení historie ADB.

   **Metody:**

   .. py:method:: get_header_config()
