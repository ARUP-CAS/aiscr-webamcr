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

      Vrací seznam polí, která jsou v administraci jen pro čtení.

      :param request: HTTP požadavek ze strany administrátora.
      :param obj: Objekt v editaci (None při vytváření).
      :return: Tuple polí určených jako readonly.

