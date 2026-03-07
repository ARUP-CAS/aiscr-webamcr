CORE mixins
===========

Modul mixins.

Třídy
------

.. py:class:: ManyToManyRestrictedClassMixin

   Třída pro model pro vytvoření property has_connections.

   Hledá jestli má model nejakou many to many vazbu.

   **Metody:**

   .. py:method:: has_connections()

      Určí, zda connections.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


.. py:class:: IPWhitelistMixin

   Mixin pro filtrování IP adres. Používá se pro PrometheusMetrics a HealthCheck.
   Dovolí přístup pouze z lokálních adres.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``dispatch()``, pracuje se s atributy ``META``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``HttpResponseForbidden()``, výsledek volání ``dispatch()``.

