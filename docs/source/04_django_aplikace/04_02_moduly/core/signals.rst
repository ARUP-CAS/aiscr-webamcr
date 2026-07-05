CORE signály
============

Definice signálů.

Funkce
------

.. py:function:: soubor_get_rozsah(sender, instance)

   Určí počet stran/snímků souboru (PDF, TIF) a uloží jej do ``rozsah``.

   :param sender: Model ``Soubor``, který signál vyslal.
   :param instance: Instancia ``Soubor`` předaná k uložení.
   :param kwargs: Dodatečné argumenty signálu.

.. py:function:: soubor_save_update_record_metadata(sender, instance)

   Aktualizuje metadata nadřazeného archeologického záznamu po uložení souboru.

   :param sender: Model ``Soubor``, který signál vyslal.
   :param instance: Instancia ``Soubor`` která byla uložena.
   :param kwargs: Dodatečné argumenty signálu.

.. py:function:: soubor_delete_connections(sender, instance)

   Odstraní historii záznamu spojené se souborem před jeho fyzickým smazáním.

   :param sender: Model ``Soubor``, který signál vyslal.
   :param instance: Instancia ``Soubor`` určená ke smazání.
   :param kwargs: Dodatečné argumenty signálu.

.. py:function:: soubor_delete_update_metadata(sender, instance)

   Aktualizuje metadata nadřazeného archeologického záznamu po smazání souboru.

   :param sender: Model ``Soubor``, který signál vyslal.
   :param instance: Instancia ``Soubor`` která byla smazána.
   :param kwargs: Dodatečné argumenty signálu.
