HESLAR hesla_dynamicka
======================

Modul hesla_dynamicka.

Funkce
------

.. py:function:: get_settings(item_group, item_id)

   Vrací settings. v aplikaci.

   **Parametry:**

   - ``item_group``: Parametr ``item_group`` předává se do volání ``filter()``.
   - ``item_id``: Identifikátor objektu ``item``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``loads()``, slovník.


.. py:function:: get_id_from_database(table, heslo, ident_cely, heslarDB)

   Vrátí ID položky hesláře podle mapování nebo výchozího identifikátoru.

   **Parametry:**

   - ``table``: Parametr ``table`` pracuje se s atributy ``objects``, vstupuje do návratové hodnoty.
   - ``heslo``: Heslo ``heslo`` používané při vytváření nebo aktualizaci účtu.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``filter()``, ``error()``, vstupuje do návratové hodnoty.
   - ``heslarDB``: Parametr ``heslarDB`` se předává do volání ``filter()``, ``error()``, ovlivňuje větvení podmínek.

   **Návratová hodnota:**

   Vrací výsledek operace.


.. py:function:: load_constants(model, constant_name, CONSTANTS, COMPOSITE_CONSTANTS)

   Načte constants. v aplikaci.

   **Parametry:**

   - ``model``: Parametr ``model`` předává se do volání ``update()``, ``get_id_from_database()``.
   - ``constant_name``: Textový název nebo klíč ``constant_name`` používaný v rámci operace.
   - ``CONSTANTS``: Mapa základních konstant používaných při inicializaci hesláře.
   - ``COMPOSITE_CONSTANTS``: Mapa složených konstant používaných při inicializaci hesláře.

