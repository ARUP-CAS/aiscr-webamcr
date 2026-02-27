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
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: uzivatel_protected()

      Vrátí textovou reprezentaci uživatele v anonymizované nebo plné podobě.

   .. py:method:: save_record_deletion_record()

      Uloží record deletion record.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: set_snapshots()

      Synchronizuje snapshot organizace s aktuální organizací uživatele.


.. py:class:: HistorieVazby

   Databázový model vazeb historie.

   Model se používa k napojení na jednotlivé záznamy.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_last_transaction_date()

      Vrátí datum a uživatele poslední transakce požadovaného typu.

   .. py:method:: navazany_objekt()

      Vrátí objekt navázaný na danou vazbu historie.

