CORE signály
============

Definice signálů.

Funkce
------

.. py:function:: news_feed_settings_capture_previous_identity(sender, instance, raw)

   Zachová původní identitu nastavení před jeho uložením.

   :param sender: Model, který vyslal signál.
   :param instance: Ukládaná instance nastavení.
   :param raw: Příznak načítání surových dat, při kterém se změna ignoruje.
   :param kwargs: Další argumenty signálu.

.. py:function:: _apply_news_feed_setting_change(previous, current)

   Apply cache and task changes after a news-feed setting transaction commits.

.. py:function:: news_feed_settings_saved(sender, instance, raw)

   Naplánuje reakci na uložené nastavení zpráv po potvrzení transakce.

   :param sender: Model, který vyslal signál.
   :param instance: Uložená instance nastavení.
   :param raw: Příznak načítání surových dat, při kterém se změna ignoruje.
   :param kwargs: Další argumenty signálu.

.. py:function:: news_feed_settings_deleted(sender, instance)

   Naplánuje reakci na smazání nastavení zpráv po potvrzení transakce.

   :param sender: Model, který vyslal signál.
   :param instance: Smazaná instance nastavení.
   :param kwargs: Další argumenty signálu.

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
