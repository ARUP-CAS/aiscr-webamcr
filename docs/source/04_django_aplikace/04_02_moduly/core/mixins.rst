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

      Ověří, že požadavek pochází z lokální IP adresy (loopback, privátní nebo link-local).

      :param request: Objekt požadavku Django.
      :param args: Poziční argumenty view.
      :param kwargs: Pojmenované argumenty view.
      :return: ``HttpResponseForbidden`` při neoprávněném přístupu, jinak výsledek nadřazené metody ``dispatch``.

