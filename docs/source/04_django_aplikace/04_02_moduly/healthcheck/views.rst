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

      **Parametry:**

      - ``request``: HTTP GET požadavek.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



Funkce
------

.. py:function:: check_status()

   Ověří status. v aplikaci.

   **Návratová hodnota:**

   Vrací n-tici.

