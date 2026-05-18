CORE logging_filters
====================

Modul logging_filters.

Třídy
------

.. py:class:: UserLogFilter

   Implementuje komponentu ``UserLogFilter`` v rámci aplikace.

   **Metody:**

   .. py:method:: filter()

      Filtruje hodnotu. v aplikaci.

      :param record: Parametr ``record`` pracuje se s atributy ``url``, ``user_id``.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


.. py:class:: DroppedTestDatabaseFilter

   Potlačí log Internal Server Error vznikající při klonování testovací DB mezi Selenium testy.

   Race condition: server-side handler stále dokončuje request, zatímco ``setUp`` dalšího testu
   už zavolal ``clone_Database`` (pg_terminate_backend + DROP DATABASE). Reconnect pak selže
   na ``database "..." does not exist`` — výsledkem je kosmetický 500 v logu, který neovlivňuje
   výsledek testu.

   **Metody:**

   .. py:method:: filter()

      Vyhodnotí, zda log záznam ponechat.

      :param record: Záznam loggeru; čte se atribut ``exc_info`` a zpráva navázané výjimky.

      :return: Vrací ``False`` pro chybu reconnectu na zahozenou testovací DB, jinak ``True``.

