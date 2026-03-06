HESLAR hesla_dynamicka
======================

Modul hesla_dynamicka.

Funkce
------

.. py:function:: get_settings(item_group, item_id)

   Vrací settings. v aplikaci.

   :param item_group: Doménový objekt `item_group`, se kterým funkce pracuje.
   :param item_id: Identifikátor objektu ``item``.

.. py:function:: get_id_from_database(table, heslo, ident_cely, heslarDB)

   Vrátí ID položky hesláře podle mapování nebo výchozího identifikátoru.

   :param table: Název nebo typ ``table`` používaný pro volbu cílové logiky.
   :param heslo: Heslo ``heslo`` používané při vytváření nebo aktualizaci účtu.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
   :param heslarDB: Číselná nebo geometrická hodnota `heslarDB` použitá při výpočtu nebo transformaci.
   :return: Vrací výsledek operace.

.. py:function:: load_constants(model, constant_name, CONSTANTS, COMPOSITE_CONSTANTS)

   Načte constants. v aplikaci.

   :param model: Název nebo typ ``model`` používaný pro volbu cílové logiky.
   :param constant_name: Textový název nebo klíč ``constant_name`` používaný v rámci operace.
   :param CONSTANTS: Mapa základních konstant používaných při inicializaci hesláře.
   :param COMPOSITE_CONSTANTS: Mapa složených konstant používaných při inicializaci hesláře.
