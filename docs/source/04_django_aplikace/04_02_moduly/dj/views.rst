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

      :return: Načtená data odpovídající zadaným vstupům.

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

   :param request: Aktuální HTTP request předaný view/funkci.
   :param typ_vazby: Název nebo typ ``typ_vazby`` používaný pro volbu cílové logiky.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: zapsat(request, arch_z_ident_cely)

   Funkce pohledu pro vytvoření dokumentační jednotky.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param arch_z_ident_cely: Identifikátor ``arch_z_ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání dokumentační jednotky.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
