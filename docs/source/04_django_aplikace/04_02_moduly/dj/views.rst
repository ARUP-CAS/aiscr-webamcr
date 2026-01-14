DJ views
========

Definice views.

Třídy
------

.. py:class:: ChangeKatastrView

   Třída pohledu pro editaci katastru dokumentační jednotky.

   **Metody:**

   .. py:method:: get_zaznam()

   .. py:method:: get_context_data()

   .. py:method:: get()

   .. py:method:: post()


Funkce
------

.. py:function:: detail(request, typ_vazby, ident_cely)

   Funkce pohledu pro editaci dokumentační jednotky a ADB.

.. py:function:: zapsat(request, arch_z_ident_cely)

   Funkce pohledu pro vytvoření dokumentační jednotky.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání dokumentační jednotky.
