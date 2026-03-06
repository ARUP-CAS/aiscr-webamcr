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

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.

      :return: Vrací výsledek volání ``JsonResponse()``.


Funkce
------

.. py:function:: check_status()

   Ověří status. v aplikaci.

   :return: Vrací n-tici.
