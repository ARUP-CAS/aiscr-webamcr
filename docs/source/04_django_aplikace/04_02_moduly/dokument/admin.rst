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

      **Parametry:**

      - ``request``: HTTP požadavek ze strany administrátora.
      - ``obj``: Objekt v editaci (None při vytváření).

      **Návratová hodnota:**

      Tuple polí určených jako readonly.


