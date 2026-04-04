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

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``, pracuje se s atributy ``get``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.

      **Výjimky:**

      - ``Http404``: Vyvolá se s textem "Page not found"; nebo s textem "Model not found".



.. py:class:: VypisOnlyView

   Implementuje komponentu ``VypisOnlyView`` v rámci aplikace.


.. py:class:: VypisListView

   Implementuje komponentu ``VypisListView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``, pracuje se s atributy ``get``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.

      **Výjimky:**

      - ``Http404``: Vyvolá se s textem "Page not found".



Funkce
------

.. py:function:: add_section_data(instance, section, fields, sections_data, iterator, user)

   Provádí operaci add section data.

   **Parametry:**

   - ``instance``: Parametr ``instance`` předává se do volání ``get_permission()``, ``get_sections()``, ovlivňuje větvení podmínek.
   - ``section``: Parametr ``section`` předává se do volání ``debug()``, ``add_section_data()``, ovlivňuje větvení podmínek.
   - ``fields``: Parametr ``fields`` předává se do volání ``isinstance()``, ``add_section_data()``, pracuje se s atributy ``items``, ovlivňuje větvení podmínek.
   - ``sections_data``: Kolekce ``sections_data`` zpracovávaná touto funkcí.
   - ``iterator``: Parametr ``iterator`` ovlivňuje větvení podmínek.
   - ``user``: Parametr ``user`` se předává do volání ``get_permission()``, ``add_section_data()``, ovlivňuje větvení podmínek.

