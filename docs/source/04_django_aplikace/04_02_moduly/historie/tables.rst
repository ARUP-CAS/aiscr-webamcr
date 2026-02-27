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

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: SimpleHistoryTable

   Implementuje komponentu ``SimpleHistoryTable`` v rámci aplikace.


.. py:class:: FedoraHistorieTable

   Definuje tabulku verzí metadat a souborů z Fedory na stránce historie.

   **Metody:**

   .. py:method:: render_uzivatel()

      Vyrenderuje uzivatel.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: render_url()

      Vyrenderuje url.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: value_url()

      Provádí operaci value url.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

