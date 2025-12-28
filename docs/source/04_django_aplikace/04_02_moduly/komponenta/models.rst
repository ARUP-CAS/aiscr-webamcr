KOMPONENTA modely
=================

Definice modelů.

Třídy
------

.. py:class:: KomponentaVazby

   Class pro db model komponenta vazby.
Model se používa k napojení na jednotlivé záznamy.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: navazany_objekt()


.. py:class:: Komponenta

   Class pro db model komponenty.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: ident_cely_safe()

   .. py:method:: pocet_nalezu()

   .. py:method:: get_absolute_url()

   .. py:method:: get_permission_object()

   .. py:method:: create_transaction()

   .. py:method:: set_transaction_main_record()


.. py:class:: KomponentaAktivita

   Class pro db model komponenta aktivity.

