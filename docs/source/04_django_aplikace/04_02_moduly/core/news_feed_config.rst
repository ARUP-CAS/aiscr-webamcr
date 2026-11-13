CORE news_feed_config
=====================

Modul news_feed_config.

Přehled modulu
--------------

Runtime configuration for the login news feed.

Třídy
------

.. py:class:: NewsFeedConfig

   Immutable parsed configuration shared by web and worker processes.

   **Metody:**

   .. py:method:: fetch_fingerprint()

      Vypočítá otisk nastavení ovlivňujících načítání zpráv.

      :return: SHA-256 otisk konfigurace načítání.

   .. py:method:: cache_identity()

      Určí identitu zdroje pro oddělení položek v cache.

      :return: Zkrácený otisk URL zdroje.

   .. py:method:: cache_keys()

      Sestaví klíče čerstvých a posledních platných zpráv.

      :param language: Jazyk zpráv uložených pod danými klíči.
      :return: Dvojice klíčů pro čerstvé a poslední platné zprávy.


Funkce
------

.. py:function:: _positive_integer(value)

   Popis není k dispozici.

.. py:function:: _parse_base_url(value)

   Popis není k dispozici.

.. py:function:: _parse_languages(value)

   Popis není k dispozici.

.. py:function:: _parse_timeout(value)

   Popis není k dispozici.

.. py:function:: _parse_cache_prefix(value)

   Popis není k dispozici.

.. py:function:: parse_news_feed_value(item_id, value)

   Převede a ověří hodnotu nastavení zpráv.

   :param item_id: Identifikátor určující způsob převodu.
   :param value: Textová hodnota nastavení k převodu.

.. py:function:: validate_news_feed_setting(instance)

   Ověří administrátorské nastavení zpráv a odmítne neplatné hodnoty.

   :param instance: Ukládaná instance administrátorského nastavení.

.. py:function:: _default_config()

   Popis není k dispozici.

.. py:function:: get_news_feed_config(force_refresh)

   Načte konfiguraci zpráv a neplatné hodnoty nahradí výchozími.

   :param force_refresh: Při pravdivé hodnotě obejde uložený snímek konfigurace.
   :return: Aktuální nebo dočasně uložená konfigurace zpráv.

.. py:function:: invalidate_news_feed_config_cache()

   Invalidate the parsed configuration shared by all application processes.

.. py:function:: get_news_feed_cache_keys(language, config)

   Sestaví klíče cache zpráv podle zdroje a jazyka.

   :param language: Jazyk zpráv v cache.
   :param config: Použitá konfigurace; pokud chybí, načte se aktuální.
   :return: Klíče čerstvých a posledních platných zpráv.

.. py:function:: fetch_configuration_fingerprint(config)

   Určí otisk nastavení používaných při načítání zpráv.

   :param config: Použitá konfigurace; pokud chybí, načte se aktuální.
   :return: Otisk nastavení načítání zpráv.
