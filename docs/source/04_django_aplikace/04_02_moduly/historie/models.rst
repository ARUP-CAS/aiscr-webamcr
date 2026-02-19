HISTORIE modely
===============

Definice modelů.

Třídy
------

.. py:class:: Historie

   Class pro db model historie.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: uzivatel_protected()

   .. py:method:: save_record_deletion_record()

   .. py:method:: set_snapshots()


.. py:class:: HistorieVazby

   Class pro db model historie vazby.
   Model se používa k napojení na jednotlivé záznamy.

   **Metody:**

   .. py:method:: __str__()

   .. py:method:: get_last_transaction_date()

      Metoda pro zjištení datumu posledné transakce daného typu.

   .. py:method:: navazany_objekt()

