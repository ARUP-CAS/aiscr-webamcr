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
      :return: Vrací výsledek provedené operace.


.. py:class:: OznameniZapsatView

   Třída pohledu pro 1. stranu oznámení.

   **Metody:**

   .. py:method:: post()

      Funkce pohledu pro oznámení. Oznámení je dvoustupňové.
      V prvém kroku uživatel zadává údaje a v druhém je potvrzuje a případně uploaduje soubory.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: OznameniDokumentaceView

   Třída pohledu pro 2. stranu oznámení.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: OznameniPotvrzeniView

   Třída pohledu pro potvrzení oznámení.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: OznamovatelCreateView

   Třída pohledu pro vytvoření oznamovatele pomocí modalu.

   **Metody:**

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

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci oznamovatele.

.. py:function:: post_poi2kat(request)

   Funkce pohledu pro získaní katastru podle bodu pro oznámení.
