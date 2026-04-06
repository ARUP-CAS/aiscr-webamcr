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

      :param obj: Parametr ``obj`` předává se do volání ``str()``, pracuje se s atributy ``osoba``, vstupuje do návratové hodnoty.

          :return: Vrací slovník.

   .. py:method:: to_representation()

      Override reprezentace do dict pro správně zobrazení label.

      :param instance: Parametr ``instance`` předává se do volání ``get_attribute()``.

          :return: Vrací proměnná ``ret``.

