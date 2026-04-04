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

      **Parametry:**

      - ``record``: Parametr ``record`` pracuje se s atributy ``uzivatel``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: str, výsledek volání ``display_name()``.



.. py:class:: SimpleHistoryTable

   Implementuje komponentu ``SimpleHistoryTable`` v rámci aplikace.


.. py:class:: FedoraHistorieTable

   Definuje tabulku verzí metadat a souborů z Fedory na stránce historie.

   **Metody:**

   .. py:method:: render_uzivatel()

      Vyrenderuje uzivatel. v aplikaci.

      **Parametry:**

      - ``record``: Parametr ``record`` předává se do volání ``filter()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, výsledek volání ``display_name()``.


   .. py:method:: render_url()

      Vyrenderuje url. v aplikaci.

      **Parametry:**

      - ``value``: Hodnota URL sloupce.
      - ``record``: Slovník záznamu tabulky obsahující URL ke stažení.

      **Návratová hodnota:**

      Vrací výsledek volání ``format_html()``.


   .. py:method:: value_url()

      Vrátí absolutní URL záznamu Fedory včetně hostname pro export tabulky.

      **Parametry:**

      - ``value``: Hodnota URL sloupce.
      - ``record``: Slovník záznamu tabulky obsahující relativní URL.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.


