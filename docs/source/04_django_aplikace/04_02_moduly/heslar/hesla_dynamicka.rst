HESLAR hesla_dynamicka
======================

Modul hesla_dynamicka.

Funkce
------

.. py:function:: get_settings(item_group, item_id)

   Vrací settings.

   :param item_group: Vstupní hodnota ``item_group`` pro danou operaci.
   :param item_id: Identifikátor objektu ``item``.
   :return: Vrací načtená data odpovídající vstupním parametrům.

.. py:function:: get_id_from_database(table, heslo, ident_cely, heslarDB)

   Vrátí ID položky hesláře podle mapování nebo výchozího identifikátoru.

.. py:function:: load_constants(model, constant_name, CONSTANTS, COMPOSITE_CONSTANTS)

   Načte constants.

   :param model: Vstupní hodnota ``model`` pro danou operaci.
   :param constant_name: Vstupní hodnota ``constant_name`` pro danou operaci.
   :param CONSTANTS: Vstupní hodnota ``CONSTANTS`` pro danou operaci.
   :param COMPOSITE_CONSTANTS: Vstupní hodnota ``COMPOSITE_CONSTANTS`` pro danou operaci.
   :return: Vrací načtená data odpovídající vstupním parametrům.
