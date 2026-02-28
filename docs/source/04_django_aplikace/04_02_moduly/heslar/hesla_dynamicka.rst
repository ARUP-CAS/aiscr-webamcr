HESLAR hesla_dynamicka
======================

Modul hesla_dynamicka.

Funkce
------

.. py:function:: get_settings(item_group, item_id)

   Vrací settings. v aplikaci.

   :param item_group: Vstupní hodnota ``item_group`` pro danou operaci.
   :param item_id: Identifikátor objektu ``item``.

.. py:function:: get_id_from_database(table, heslo, ident_cely, heslarDB)

   Vrátí ID položky hesláře podle mapování nebo výchozího identifikátoru.

   :param table: Popis parametru ``table``.
   :param heslo: Popis parametru ``heslo``.
   :param ident_cely: Popis parametru ``ident_cely``.
   :param heslarDB: Popis parametru ``heslarDB``.
   :return: Vrací výsledek operace.

.. py:function:: load_constants(model, constant_name, CONSTANTS, COMPOSITE_CONSTANTS)

   Načte constants. v aplikaci.

   :param model: Vstupní hodnota ``model`` pro danou operaci.
   :param constant_name: Vstupní hodnota ``constant_name`` pro danou operaci.
   :param CONSTANTS: Vstupní hodnota ``CONSTANTS`` pro danou operaci.
   :param COMPOSITE_CONSTANTS: Vstupní hodnota ``COMPOSITE_CONSTANTS`` pro danou operaci.
