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


.. py:class:: VypisOnlyView

   Implementuje komponentu ``VypisOnlyView`` v rámci aplikace.


.. py:class:: VypisListView

   Implementuje komponentu ``VypisListView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


Funkce
------

.. py:function:: add_section_data(instance, section, fields, sections_data, iterator, user)

   Provádí operaci add section data.

   :param instance: Instance modelu, které se operace týká.
   :param section: Doménový objekt `section`, se kterým funkce pracuje.
   :param fields: Záznam/objekt ``fields``, který funkce čte, validuje nebo upravuje.
   :param sections_data: Kolekce ``sections_data`` zpracovávaná touto funkcí.
   :param iterator: Číselná nebo geometrická hodnota `iterator` použitá při výpočtu nebo transformaci.
   :param user: Uživatel, v jehož kontextu se operace provádí.
