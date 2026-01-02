NOTIFIKACE_PROJEKTY views
=========================

Definice views.

Třídy
------

.. py:class:: PesListView

   Třída pohledu pro zobrazení listu hlídacích psů.

   **Metody:**

   .. py:method:: get_context_data()


.. py:class:: PesCreateView

   Třída pohledu pro vytvořené hlídacího psa.

   **Metody:**

   .. py:method:: post()


.. py:class:: PesSmazatView

   Třída pohledu pro smazání hlídacího psa pomocí modalu.

   **Metody:**

   .. py:method:: get_zaznam()

   .. py:method:: get_object_identification()

   .. py:method:: get_context_data()

   .. py:method:: get()

   .. py:method:: post()

