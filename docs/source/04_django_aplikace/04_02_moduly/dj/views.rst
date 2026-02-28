DJ views
========

Definice views.

Třídy
------

.. py:class:: ChangeKatastrView

   Třída pohledu pro editaci katastru dokumentační jednotky.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


Funkce
------

.. py:function:: detail(request, typ_vazby, ident_cely)

   Funkce pohledu pro editaci dokumentační jednotky a ADB.

   :param request: Popis parametru ``request``.
   :param typ_vazby: Popis parametru ``typ_vazby``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: zapsat(request, arch_z_ident_cely)

   Funkce pohledu pro vytvoření dokumentační jednotky.

   :param request: Popis parametru ``request``.
   :param arch_z_ident_cely: Popis parametru ``arch_z_ident_cely``.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání dokumentační jednotky.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.
