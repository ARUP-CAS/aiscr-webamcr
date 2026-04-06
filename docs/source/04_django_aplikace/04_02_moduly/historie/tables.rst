HISTORIE tables
===============

Modul tables.

Třídy
------

.. py:class:: HistorieTable

   Definuje tabulku pro zobrazení historie změn.

   **Metody:**

   .. py:method:: render_uzivatel_custom()

      Vyrenderuje uzivatel custom.

      :param record: Parametr ``record`` pracuje se s atributy ``uzivatel``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: str, výsledek volání ``display_name()``.


.. py:class:: SimpleHistoryTable

   Implementuje komponentu ``SimpleHistoryTable`` v rámci aplikace.


.. py:class:: FedoraHistorieTable

   Definuje tabulku verzí metadat a souborů z Fedory na stránce historie.

   **Metody:**

   .. py:method:: render_uzivatel()

      Vyrenderuje uzivatel. v aplikaci.

      :param record: Parametr ``record`` předává se do volání ``filter()``, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, výsledek volání ``display_name()``.

   .. py:method:: render_url()

      Vyrenderuje url. v aplikaci.

      :param value: Hodnota URL sloupce.
      :param record: Slovník záznamu tabulky obsahující URL ke stažení.

          :return: Vrací výsledek volání ``format_html()``.

   .. py:method:: value_url()

      Vrátí absolutní URL záznamu Fedory včetně hostname pro export tabulky.

      :param value: Hodnota URL sloupce.
      :param record: Slovník záznamu tabulky obsahující relativní URL.

          :return: Vrací hodnotu podle větve zpracování.

