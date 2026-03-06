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

      :param record: Záznam, který funkce čte nebo upravuje.


.. py:class:: SimpleHistoryTable

   Implementuje komponentu ``SimpleHistoryTable`` v rámci aplikace.


.. py:class:: FedoraHistorieTable

   Definuje tabulku verzí metadat a souborů z Fedory na stránce historie.

   **Metody:**

   .. py:method:: render_uzivatel()

      Vyrenderuje uzivatel. v aplikaci.

      :param record: Záznam, který funkce čte nebo upravuje.

   .. py:method:: render_url()

      Vyrenderuje url. v aplikaci.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :param record: Záznam, který funkce čte nebo upravuje.

   .. py:method:: value_url()

      Provádí operaci value url.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :param record: Záznam, který funkce čte nebo upravuje.

