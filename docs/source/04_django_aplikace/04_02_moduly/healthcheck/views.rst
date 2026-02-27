HEALTHCHECK views
=================

Definice views.

Třídy
------

.. py:class:: HealthCheckView

   Implementuje komponentu ``HealthCheckView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :return: Vrací načtená data odpovídající vstupním parametrům.


Funkce
------

.. py:function:: check_status()

   Ověří status.

   :return: Vrací výsledek ověření nebo validačního pravidla.
