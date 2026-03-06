HESLAR hesla_dynamicka
======================

Modul hesla_dynamicka.

Funkce
------

.. py:function:: get_settings(item_group, item_id)

   Vrací settings. v aplikaci.

   :param item_group: Parametr ``item_group`` předává se do volání ``filter()``.
   :param item_id: Identifikátor objektu ``item``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``loads()``, slovník.

.. py:function:: get_id_from_database(table, heslo, ident_cely, heslarDB)

   Vrátí ID položky hesláře podle mapování nebo výchozího identifikátoru.

   :param table: Parametr ``table`` pracuje se s atributy ``objects``, vstupuje do návratové hodnoty.
   :param heslo: Heslo ``heslo`` používané při vytváření nebo aktualizaci účtu.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``filter()``, ``error()``, vstupuje do návratové hodnoty.
   :param heslarDB: Parametr ``heslarDB`` se předává do volání ``filter()``, ``error()``, ovlivňuje větvení podmínek.
   :return: Vrací výsledek operace.

.. py:function:: load_constants(model, constant_name, CONSTANTS, COMPOSITE_CONSTANTS)

   Načte constants. v aplikaci.

   :param model: Parametr ``model`` předává se do volání ``update()``, ``get_id_from_database()``.
   :param constant_name: Textový název nebo klíč ``constant_name`` používaný v rámci operace.
   :param CONSTANTS: Mapa základních konstant používaných při inicializaci hesláře.
   :param COMPOSITE_CONSTANTS: Mapa složených konstant používaných při inicializaci hesláře.
