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

      **Parametry:**

      - ``obj``: Parametr ``obj`` předává se do volání ``str()``, pracuje se s atributy ``osoba``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací slovník.


   .. py:method:: to_representation()

      Override reprezentace do dict pro správně zobrazení label.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``get_attribute()``.

      **Návratová hodnota:**

      Vrací proměnná ``ret``.


