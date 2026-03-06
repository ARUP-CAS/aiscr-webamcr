HISTORIE modely
===============

Definice modelů.

Třídy
------

.. py:class:: Historie

   Databázový model pro záznam historie změn.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: uzivatel_protected()

      Vrátí textovou reprezentaci uživatele v anonymizované nebo plné podobě.

      :param anonymized: Číselná hodnota ``anonymized`` použitá při výpočtu nebo transformaci.

   .. py:method:: save_record_deletion_record()

      Uloží record deletion record.

      :param record: Záznam, který funkce čte nebo upravuje.

   .. py:method:: set_snapshots()

      Synchronizuje snapshot organizace s aktuální organizací uživatele.


.. py:class:: HistorieVazby

   Databázový model vazeb historie.

   Model se používa k napojení na jednotlivé záznamy.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

   .. py:method:: get_last_transaction_date()

      Vrátí datum a uživatele poslední transakce požadovaného typu.

      :param transaction_type: Název nebo typ ``transaction_type`` používaný pro volbu cílové logiky.
      :param anonymized: Číselná hodnota ``anonymized`` použitá při výpočtu nebo transformaci.
      :param user_protected: Příznak ``user_protected`` určující průběh nebo rozsah zpracování.
      :return: Vrací výsledek operace.

   .. py:method:: navazany_objekt()

      Vrátí objekt navázaný na danou vazbu historie.

