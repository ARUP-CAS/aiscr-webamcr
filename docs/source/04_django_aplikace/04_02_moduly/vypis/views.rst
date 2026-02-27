VYPIS views
===========

Definice views.

Třídy
------

.. py:class:: VypisView

   Implementuje komponentu ``VypisView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: VypisOnlyView

   Implementuje komponentu ``VypisOnlyView`` v rámci aplikace.


.. py:class:: VypisListView

   Implementuje komponentu ``VypisListView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


Funkce
------

.. py:function:: add_section_data(instance, section, fields, sections_data, iterator, user)

   Provádí operaci add section data.

   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param section: Vstupní hodnota ``section`` pro danou operaci.
   :param fields: Vstupní hodnota ``fields`` pro danou operaci.
   :param sections_data: Vstupní hodnota ``sections_data`` pro danou operaci.
   :param iterator: Vstupní hodnota ``iterator`` pro danou operaci.
   :param user: Vstupní hodnota ``user`` pro danou operaci.
   :return: Vrací výsledek provedené operace.
