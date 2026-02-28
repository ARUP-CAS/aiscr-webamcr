OZNAMENI views
==============

Definice views.

Třídy
------

.. py:class:: OznameniView

   Implementuje komponentu ``OznameniView`` v rámci aplikace.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: OznameniZapsatView

   Třída pohledu pro 1. stranu oznámení.

   **Metody:**

   .. py:method:: post()

      Funkce pohledu pro oznámení. Oznámení je dvoustupňové.

      V prvém kroku uživatel zadává údaje a v druhém je potvrzuje a případně uploaduje soubory.

      :param request: Popis parametru ``request``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.


.. py:class:: OznameniDokumentaceView

   Třída pohledu pro 2. stranu oznámení.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.


.. py:class:: OznameniPotvrzeniView

   Třída pohledu pro potvrzení oznámení.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.


.. py:class:: OznamovatelCreateView

   Třída pohledu pro vytvoření oznamovatele pomocí modalu.

   **Metody:**

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

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci oznamovatele.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: post_poi2kat(request)

   Funkce pohledu pro získaní katastru podle bodu pro oznámení.

   :param request: Popis parametru ``request``.
