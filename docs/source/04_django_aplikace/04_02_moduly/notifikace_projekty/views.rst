NOTIFIKACE_PROJEKTY views
=========================

Definice views.

Třídy
------

.. py:class:: PesListView

   Třída pohledu pro zobrazení listu hlídacích psů.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: PesCreateView

   Třída pohledu pro vytvořené hlídacího psa.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: PesSmazatView

   Třída pohledu pro smazání hlídacího psa pomocí modalu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_object_identification()

      Vrací object identification.

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

