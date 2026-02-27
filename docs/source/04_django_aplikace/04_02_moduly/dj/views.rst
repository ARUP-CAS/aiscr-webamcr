DJ views
========

Definice views.

Třídy
------

.. py:class:: ChangeKatastrView

   Třída pohledu pro editaci katastru dokumentační jednotky.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


Funkce
------

.. py:function:: detail(request, typ_vazby, ident_cely)

   Funkce pohledu pro editaci dokumentační jednotky a ADB.

.. py:function:: zapsat(request, arch_z_ident_cely)

   Funkce pohledu pro vytvoření dokumentační jednotky.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání dokumentační jednotky.
