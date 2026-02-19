OZNAMENI views
==============

Definice views.

Třídy
------

.. py:class:: OznameniView

   Popis není k dispozici.

   **Metody:**

   .. py:method:: dispatch()


.. py:class:: OznameniZapsatView

   Třída pohledu pro 1. stranu oznámení.

   **Metody:**

   .. py:method:: post()

      Funkce pohledu pro oznámení. Oznámení je dvoustupňové.
      V prvém kroku uživatel zadává údaje a v druhém je potvrzuje a případně uploaduje soubory.

   .. py:method:: get()


.. py:class:: OznameniDokumentaceView

   Třída pohledu pro 2. stranu oznámení.

   **Metody:**

   .. py:method:: post()

   .. py:method:: get()


.. py:class:: OznameniPotvrzeniView

   Třída pohledu pro potvrzení oznámení.

   **Metody:**

   .. py:method:: get()


.. py:class:: OznamovatelCreateView

   Třída pohledu pro vytvoření oznamovatele pomocí modalu.

   **Metody:**

   .. py:method:: get_context_data()

   .. py:method:: get()

   .. py:method:: post()


Funkce
------

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci oznamovatele.

.. py:function:: post_poi2kat(request)

   Funkce pohledu pro získaní katastru podle bodu pro oznámení.
