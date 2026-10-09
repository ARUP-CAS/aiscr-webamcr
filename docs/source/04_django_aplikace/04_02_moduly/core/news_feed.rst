CORE news_feed
==============

Modul news_feed.

Přehled modulu
--------------

Klient a cache novinkového kanálu pro načítání a zpracování novinek ze služby aiscr-news.

Modul zajišťuje načítání dat novinkového kanálu ze služby aiscr-news
a jejich převod do standardizovaného formátu pro použití ve webové
aplikaci AMČR.

Data kanálu se načítají z repozitáře aiscr-news a považují se za
důvěryhodný obsah. Pole html se vykresluje jako důvěryhodné HTML,
protože je generuje a publikuje kontrolovaný repozitář aiscr-news.

Třídy
------

.. py:class:: NewsItem

   Představuje jednu novinku z kanálu.

   **Metody:**

   .. py:method:: __post_init__()

      Inicializuje seznam autorů, pokud není definován.

      :return: None.


.. py:class:: NewsFeedClient

   Klient pro načítání a zpracování dat novinkového kanálu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje klienta novinkového kanálu.

      :param base_url: Základní URL pro načítání dat kanálu ze služby aiscr-news.
      :param timeout: Časový limit požadavku v sekundách.

   .. py:method:: fetch_feed()

      Načte a zpracuje novinkový kanál pro zadaný jazyk.

      Načte kanál ze služby aiscr-news a převede jej na seznam
      objektů NewsItem.

      :param language: Kód jazyka kanálu (např. "cs" nebo "en").
      :return: Seznam objektů NewsItem.
      :raises NewsFeedError: Pokud kanál nelze načíst nebo zpracovat.

   .. py:method:: _parse_feed()

      Zpracuje data kanálu na objekty NewsItem.

      :param data: Zpracovaná JSON data kanálu.
      :return: Seznam objektů NewsItem.
      :raises NewsFeedError: Pokud data nejsou platný slovník.

   .. py:method:: _parse_item()

      Zpracuje jednu položku z dat kanálu.

      :param item_data: Data jedné novinky.
      :return: Objekt NewsItem, nebo None, pokud položku nelze zpracovat.


.. py:class:: NewsFeedError

   Výjimka vyvolaná při selhání operací novinkového kanálu.


.. py:class:: NewsFeedCache

   Cache obalující klienta novinkového kanálu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje cache novinkového kanálu.

      :param client: Instance NewsFeedClient, která se obaluje.
      :param cache_key_prefix: Prefix klíčů cache.
      :param default_ttl: Výchozí doba platnosti v sekundách pro čerstvé kopie.
      :param stale_ttl: Doba platnosti v sekundách pro zastaralé kopie.
      :param block_height: Výška sbaleného bloku novinek v pixelech.

   .. py:method:: get_feed()

      Vrátí novinkový kanál s využitím cache, je-li k dispozici.

      Uplatňuje strategii čerstvé kopie přednostně:
      1. Pokusí se získat čerstvou kopii z cache
      2. Pokud vypršela nebo chybí, načte kanál ze služby
      3. Pokud načtení selže, vrátí poslední úspěšnou kopii (zastaralou kopii)

      :param language: Kód jazyka kanálu.
      :return: Seznam novinek, nebo prázdný seznam, pokud nejsou dostupné.

   .. py:method:: set_stale()

      Uloží zastaralou kopii do cache.

      :param language: Kód jazyka kanálu.
      :param feed: Seznam novinek, který se uloží do cache jako zastaralý.

