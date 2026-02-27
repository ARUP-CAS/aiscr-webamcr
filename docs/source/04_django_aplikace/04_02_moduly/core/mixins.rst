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


.. py:class:: IPWhitelistMixin

   Mixin pro filtrování IP adres. Používá se pro PrometheusMetrics a HealthCheck.
   Dovolí přístup pouze z lokálních adres.

   **Metody:**

   .. py:method:: dispatch()

