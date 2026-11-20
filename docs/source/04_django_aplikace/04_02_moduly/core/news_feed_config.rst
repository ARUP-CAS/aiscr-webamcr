CORE news_feed_config
=====================

Modul news_feed_config.

Přehled modulu
--------------

Nastavení novinkového kanálu přihlašovací stránky za běhu aplikace.

Třídy
------

.. py:class:: NewsFeedConfig

   Neměnný snímek ověřeného nastavení novinek sdílený webovými procesy a pracovníky Celery.

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

   Převede hodnotu nastavení novinek na kladné celé číslo.

   :param value: Textová hodnota číselného nastavení.
   :return: Celé číslo větší než nula.
   :raises ValueError: Pokud hodnotu nelze převést nebo není kladná.

.. py:function:: _parse_base_url(value)

   Ověří adresář kanálu na důvěryhodném hostiteli a sjednotí zápis URL.

   :param value: HTTPS URL adresáře kanálu bez přihlašovacích údajů, dotazu a fragmentu.
   :return: URL s důvěryhodným hostitelem a bez koncového lomítka.
   :raises ValueError: Pokud URL nesplňuje omezení důvěryhodného zdroje.

.. py:function:: _parse_languages(value)

   Převede JSON seznam jazyků novinek na ověřenou n-tici kódů.

   :param value: Neprázdné JSON pole jedinečných jazykových kódů podporovaných aplikací.
   :return: N-tice jazykových kódů ve vstupním pořadí.
   :raises ValueError: Pokud JSON nebo seznam jazyků není platný.

.. py:function:: _parse_timeout(value)

   Ověří časový limit požadavku na novinkový kanál.

   :param value: Textový zápis časového limitu v sekundách.
   :return: Kladný konečný časový limit jako desetinné číslo.
   :raises ValueError: Pokud hodnota není kladné konečné číslo.

.. py:function:: _parse_cache_prefix(value)

   Ověří prefix klíčů cache novinek a odstraní okolní bílé znaky.

   :param value: Prefix o délce 1 až 64 znaků začínající písmenem nebo číslicí.
   :return: Prefix obsahující pouze písmena ASCII, číslice, dvojtečky, podtržítka a pomlčky.
   :raises ValueError: Pokud prefix nesplňuje požadovanou délku nebo formát.

.. py:function:: parse_news_feed_value(item_id, value)

   Převede a ověří hodnotu nastavení zpráv.

   :param item_id: Identifikátor určující způsob převodu.
   :param value: Textová hodnota nastavení k převodu.
   :return: Ověřená hodnota podle identifikátoru: celé číslo pro výšku, TTL a interval varování,
       řetězec pro URL a prefix cache, n-tice jazykových kódů nebo desetinný časový limit.
   :raises ValueError: Pokud identifikátor není podporován nebo hodnota nesplňuje jeho formát a omezení.

.. py:function:: validate_news_feed_setting(instance)

   Ověří administrátorské nastavení zpráv a odmítne neplatné hodnoty.

   :param instance: Ukládaná instance administrátorského nastavení.

.. py:function:: _default_config()

   Sestaví snímek výchozího nastavení novinek bez čtení databáze.

   :return: Výchozí konfigurace s neměnnou n-ticí jazykových kódů.

.. py:function:: get_news_feed_config(force_refresh)

   Načte konfiguraci zpráv a neplatné hodnoty nahradí výchozími.

   :param force_refresh: Při pravdivé hodnotě obejde uložený snímek konfigurace.
   :return: Aktuální nebo dočasně uložená konfigurace zpráv.

.. py:function:: invalidate_news_feed_config_cache()

   Změní generaci cache nastavení novinek sdílenou všemi procesy aplikace.

.. py:function:: get_news_feed_cache_keys(language, config)

   Sestaví klíče cache zpráv podle zdroje a jazyka.

   :param language: Jazyk zpráv v cache.
   :param config: Použitá konfigurace; pokud chybí, načte se aktuální.
   :return: Klíče čerstvých a posledních platných zpráv.

.. py:function:: fetch_configuration_fingerprint(config)

   Určí otisk nastavení používaných při načítání zpráv.

   :param config: Použitá konfigurace; pokud chybí, načte se aktuální.
   :return: Otisk nastavení načítání zpráv.
