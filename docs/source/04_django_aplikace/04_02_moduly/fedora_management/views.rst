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

      :param record: Záznam, který funkce čte nebo upravuje.
      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.
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

      :param record: Záznam, který funkce čte nebo upravuje.
      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

