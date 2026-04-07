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

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: uzivatel_protected()

      Vrátí textovou reprezentaci uživatele v anonymizované nebo plné podobě.

      :param anonymized: Číselná hodnota ``anonymized`` použitá při výpočtu nebo transformaci.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: save_record_deletion_record()

      Uloží record deletion record.

      :param record: Parametr ``record`` předává se do volání ``hasattr()``, ``isinstance()``, pracuje se s atributy ``deleted_by_user``, ``history_vazba``, ovlivňuje větvení podmínek.

   .. py:method:: set_snapshots()

      Synchronizuje snapshot organizace s aktuální organizací uživatele.


.. py:class:: HistorieVazby

   Databázový model vazeb historie.

   Model se používa k napojení na jednotlivé záznamy.

   **Metody:**

   .. py:method:: __str__()

             Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací výsledek volání ``format()``.

   .. py:method:: get_last_transaction_date()

      Vrátí datum a uživatele poslední transakce požadovaného typu.

      :param transaction_type: Parametr ``transaction_type`` předává se do volání ``isinstance()``, ``filter()``, ovlivňuje větvení podmínek.
      :param anonymized: Číselná hodnota ``anonymized`` použitá při výpočtu nebo transformaci.
      :param user_protected: Parametr ``user_protected`` ovlivňuje větvení podmínek.
      :return: Vrací výsledek operace.

   .. py:method:: get_last_transaction_if_type()

      Vrátí datum, poznámku a uživatele poslední transakce vazby, ale pouze pokud je jejím typem ``transaction_type``.

      :param transaction_type: Typ transakce nebo seznam typů, které se mají kontrolovat.
      :param anonymized: Příznak anonymizace uživatele.
      :param user_protected: Příznak ochrany uživatele.
      :return: Slovník s daty transakce, nebo prázdný slovník pokud poslední transakce není požadovaného typu.

   .. py:method:: navazany_objekt()

      Vrátí objekt navázaný na danou vazbu historie.

      :return: Vrací atribut objektu.

