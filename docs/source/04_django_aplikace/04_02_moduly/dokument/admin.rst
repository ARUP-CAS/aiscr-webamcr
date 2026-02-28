DOKUMENT admin
==============

Konfigurace Django admin.

Třídy
------

.. py:class:: DokumentWithMetadataAdmin

   Implementuje komponentu ``DokumentWithMetadataAdmin`` v rámci aplikace.


.. py:class:: LetAdmin

   Admin část pro správu modelu Let.

   **Metody:**

   .. py:method:: get_readonly_fields()

      Vrací readonly fields.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.

