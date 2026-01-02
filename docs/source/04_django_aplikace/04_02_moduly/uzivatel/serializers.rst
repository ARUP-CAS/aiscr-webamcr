UZIVATEL serializers
====================

Definice serializérů.

Třídy
------

.. py:class:: UserSerializer

   Serializer pro info o uživately.

   **Metody:**

   .. py:method:: get_osoba()

      Metoda pro správně vrácení hodnot o osobe.

   .. py:method:: to_representation()

      Override reprezentace do dict pro správně zobrazení label.

