FEDORA_MANAGEMENT views
=======================

Definice views.

Třídy
------

.. py:class:: AdminRecordProcessingView

   Implementuje komponentu ``AdminRecordProcessingView`` v rámci aplikace.

   **Metody:**

   .. py:method:: process_record()

      Provádí operaci process record.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :param result: Vstupní hodnota ``result`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ContinueMedataProcessing

   Implementuje komponentu ``ContinueMedataProcessing`` v rámci aplikace.

   **Metody:**

   .. py:method:: process_record()

      Provádí operaci process record.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :param result: Vstupní hodnota ``result`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

