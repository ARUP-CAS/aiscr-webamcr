HESLAR admin
============

Konfigurace Django admin.

Třídy
------

.. py:class:: ObjectWithMetadataAdmin

   Popis není k dispozici.

   **Metody:**

   .. py:method:: metadata()


.. py:class:: HeslarWithMetadataAdmin

   Popis není k dispozici.


.. py:class:: HeslarNazevAdmin

   Admin část pro prohlížení modelu heslař název.
Práva na změnu jsou zakázaná.

   **Metody:**

   .. py:method:: has_add_permission()

   .. py:method:: has_delete_permission()

   .. py:method:: has_change_permission()


.. py:class:: HeslarAdmin

   Admin část pro správu modelu heslař.

   **Metody:**

   .. py:method:: render_change_form()

   .. py:method:: has_change_permission()

   .. py:method:: get_readonly_fields()

   .. py:method:: has_delete_permission()


.. py:class:: HeslarDataceAdmin

   Admin část pro správu modelu heslař datace.

   **Metody:**

   .. py:method:: get_readonly_fields()

   .. py:method:: obdobi_ident_cely()


.. py:class:: HeslarDokumentTypMaterialRadaAdmin

   Admin část pro prohlížení modelu heslař dokument typ material.
Práva na změnu jsou zakázaná.

   **Metody:**

   .. py:method:: has_add_permission()

   .. py:method:: has_delete_permission()

   .. py:method:: has_change_permission()


.. py:class:: HeslarOdkazAdmin

   Admin část pro správu modelu heslař odkaz.

   **Metody:**

   .. py:method:: heslo_ident_cely()


.. py:class:: HeslarHierarchieAdmin

   Admin část pro správu modelu heslař hierarchie.

   **Metody:**

   .. py:method:: heslo_podrazene_ident_cely()


.. py:class:: OsobaAdmin

   Admin část pro správu modelu osob.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: has_delete_permission()

   .. py:method:: get_fields()


.. py:class:: OrganizaceAdmin

   Admin část pro správu modelu organizace.

   **Metody:**

   .. py:method:: has_delete_permission()


.. py:class:: HeslarRuianAdmin

   Popis není k dispozici.

   **Metody:**

   .. py:method:: has_add_permission()

   .. py:method:: has_delete_permission()

   .. py:method:: has_change_permission()


.. py:class:: HeslarRuianKrajAdmin

   Admin část pro správu modelu ruian kraj.


.. py:class:: HeslarRuianOkresAdmin

   Admin část pro správu modelu ruian okres.


.. py:class:: HeslarRuianKatastrAdmin

   Admin část pro správu modelu ruian katastr.

