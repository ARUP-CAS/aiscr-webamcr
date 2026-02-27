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

      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: IPWhitelistMixin

   Implementuje komponentu ``IPWhitelistMixin`` v rámci aplikace.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

