HISTORIE views
==============

Definice views.

Třídy
------

.. py:class:: HistorieListView

   Třída pohledu pro zobrazení historie záznamu.
   Třída se dědí pro jednotlivá historie.

   **Metody:**

   .. py:method:: get_lookup_value()

      Vrátí hodnotu z URL podle lookup_kwarg.

   .. py:method:: prepare_queryset()

      Potomek může přepsat pro vlastní řazení nebo dodatečné filtry.
      :param qs: Hodnota parametru ``qs`` použitého touto operací.

   .. py:method:: add_extra_context()

      Potomek může přepsat a doplnit další hodnoty do contextu.
      :param context: Hodnota parametru ``context`` použitého touto operací.

   .. py:method:: get_queryset()

      Vrací queryset historie po aplikaci výchozího řazení a filtrů.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_header_config()

      Potomek musí vrátit {'url': ..., 'icon': ..., 'text': ...}
      :param context: Hodnota parametru ``context`` použitého touto operací.

   .. py:method:: add_fedora_history()

      Pokud potomek definuje fedora_model, automaticky se načte
      metadata historie z Fedory a přidá se druhá tabulka fedora_table.

      :param context: Hodnota parametru ``context`` použitého touto operací.

   .. py:method:: get_table()

      Vrací tabulku historie naplněnou připraveným querysetem.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: render_to_response()

      Vyrenderuje to response.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :param response_kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: ProjektHistorieListView

   Třída pohledu pro zobrazení historie projektu.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: AkceHistorieListView

   Třída pohledu pro zobrazení historie akcí.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: DokumentHistorieListView

   Třida pohledu pro zobrazení historie dokumentů.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: add_extra_context()

      Provádí operaci add extra context.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: SamostatnyNalezHistorieListView

   Třida pohledu pro zobrazení historie samostatných nálezů.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: SpolupraceHistorieListView

   Třida pohledu pro zobrazení historie spolupráce.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: SouborHistorieListView

   Třida pohledu pro zobrazení historie souborů.

   **Metody:**

   .. py:method:: prepare_queryset()

      Provádí operaci prepare queryset.

      :param qs: Vstupní hodnota ``qs`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: add_extra_context()

      Provádí operaci add extra context.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: LokalitaHistorieListView

   Třida pohledu pro zobrazení historie lokalit.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: UzivatelHistorieListView

   Třida pohledu pro zobrazení historie uživatele.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: ExterniZdrojHistorieListView

   Třida pohledu pro zobrazení historie externích zdrojů.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: PianHistorieListView

   Třida pohledu pro zobrazení historie Pianu.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: PianLokalitaHistorieListView

   Třida pohledu pro zobrazení historie Pianu.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: AdbHistorieListView

   Třida pohledu pro zobrazení historie ADB.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

