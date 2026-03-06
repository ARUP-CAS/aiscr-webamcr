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

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_readonly_fields``.
      :param obj: Parametr ``obj`` ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, atribut objektu.

