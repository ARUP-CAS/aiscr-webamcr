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

      :return: Vrací vybranou hodnotu z kolekce.

   .. py:method:: prepare_queryset()

      Potomek může přepsat pro vlastní řazení nebo dodatečné filtry.

      :param qs: Queryset/filtr ``qs`` použitý při výběru záznamů.

      :return: Vrací výsledek volání ``order_by()``.

   .. py:method:: add_extra_context()

      Potomek může přepsat a doplnit další hodnoty do contextu.

      :param context: Kolekce ``context`` zpracovávaná touto funkcí.

   .. py:method:: get_queryset()

      Vrací queryset historie po aplikaci výchozího řazení a filtrů.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``none()``, proměnná ``qs``.
      :raises ValueError: Vyvolá se při splnění podmínky ``not self.queryset_filter``.

   .. py:method:: get_header_config()

      Potomek musí vrátit {'url': ..., 'icon': ..., 'text': ...}

      :param context: Kolekce ``context`` zpracovávaná touto funkcí.

   .. py:method:: add_fedora_history()

      Pokud potomek definuje fedora_model, automaticky se načte

      metadata historie z Fedory a přidá se druhá tabulka fedora_table.

      :param context: Kolekce ``context`` zpracovávaná touto funkcí.

   .. py:method:: get_table()

      Vrací tabulku historie naplněnou připraveným querysetem.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_table()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: None, výsledek volání ``get_table()``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: render_to_response()

      Vyrenderuje to response.

      :param context: Parametr ``context`` se předává do volání ``render_to_response()``, pracuje se s atributy ``get``, vstupuje do návratové hodnoty.
      :param response_kwargs: Parametr ``response_kwargs`` se předává do volání ``render_to_response()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``render_to_response()``, výsledek volání ``response()``.


.. py:class:: ProjektHistorieListView

   Třída pohledu pro zobrazení historie projektu.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Parametr ``context`` se předává do volání ``reverse()``, vstupuje do návratové hodnoty.

      :return: Vrací slovník.


.. py:class:: AkceHistorieListView

   Třída pohledu pro zobrazení historie akcí.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Parametr ``context`` se předává do volání ``reverse()``, vstupuje do návratové hodnoty.

      :return: Vrací slovník.


.. py:class:: DokumentHistorieListView

   Třida pohledu pro zobrazení historie dokumentů.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Kontext pohledu obsahující ``ident_cely`` záznamu.

      :return: Vrací slovník.

   .. py:method:: add_extra_context()

      Doplní kontext o typ záznamu (dokument nebo knihovna_3d) podle identifikátoru.

      :param context: Kontext pohledu, do kterého jsou přidány klíče ``typ`` a ``entity``.


.. py:class:: SamostatnyNalezHistorieListView

   Třida pohledu pro zobrazení historie samostatných nálezů.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Parametr ``context`` se předává do volání ``reverse()``, vstupuje do návratové hodnoty.

      :return: Vrací slovník.


.. py:class:: SpolupraceHistorieListView

   Třida pohledu pro zobrazení historie spolupráce.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Kontext pohledu (nevyužíván, odkaz je vždy na seznam spolupráce).

      :return: Vrací slovník.


.. py:class:: SouborHistorieListView

   Třida pohledu pro zobrazení historie souborů.

   **Metody:**

   .. py:method:: prepare_queryset()

      Seřadí queryset záznamů Historie souboru sestupně podle data změny.

      :param qs: Queryset záznamů Historie, který má být seřazen.

      :return: Vrací výsledek volání ``order_by()``.

   .. py:method:: add_extra_context()

      Doplní kontext o informace o projektu a předchozím objektu.

      :param context: Kontext pohledu, do kterého jsou přidány klíče ``projekt``, ``back_ident`` a ``back_model``.

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Parametr ``context`` se předává do volání ``reverse()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: slovník, None.


.. py:class:: LokalitaHistorieListView

   Třida pohledu pro zobrazení historie lokalit.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Parametr ``context`` se předává do volání ``reverse()``, vstupuje do návratové hodnoty.

      :return: Vrací slovník.


.. py:class:: UzivatelHistorieListView

   Třida pohledu pro zobrazení historie uživatele.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Parametr ``context`` slouží jako vstup pro logiku funkce ``get_header_config``.

      :return: Vrací slovník.


.. py:class:: ExterniZdrojHistorieListView

   Třida pohledu pro zobrazení historie externích zdrojů.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací header config.

      :param context: Parametr ``context`` se předává do volání ``reverse()``, vstupuje do návratové hodnoty.

      :return: Vrací slovník.


.. py:class:: PianHistorieListView

   Třida pohledu pro zobrazení historie Pianu.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací konfiguraci záhlaví pro historii Pianu.

      :param context: Kontext pohledu obsahující identifikátory akce a dokumentační jednotky.

      :return: Vrací slovník s URL, ikonou a textem záhlaví.


.. py:class:: PianLokalitaHistorieListView

   Třida pohledu pro zobrazení historie Pianu.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací konfiguraci záhlaví pro historii Pianu lokality.

      :param context: Kontext pohledu obsahující identifikátory lokality a dokumentační jednotky.

      :return: Vrací slovník s URL, ikonou a textem záhlaví.


.. py:class:: AdbHistorieListView

   Třida pohledu pro zobrazení historie ADB.

   **Metody:**

   .. py:method:: get_header_config()

      Vrací konfiguraci záhlaví pro historii ADB.

      :param context: Kontext pohledu obsahující identifikátory akce a dokumentační jednotky.

      :return: Vrací slovník s URL, ikonou a textem záhlaví.

