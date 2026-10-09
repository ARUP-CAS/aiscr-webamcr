CORE news_feed
==============

Modul news_feed.

Přehled modulu
--------------

News feed client and cache for fetching and parsing news from aiscr-news.

This module provides functionality to fetch news feed data from the
aiscr-news service and transform it into a standardized format for
use in the AMČR web application.

The feed data is fetched from the aiscr-news repository and is
considered trusted content. The html field is rendered as trusted
HTML because it is generated and published by the controlled
aiscr-news repository.

Třídy
------

.. py:class:: NewsItem

   Represents a single news item from the feed.

   **Metody:**

   .. py:method:: __post_init__()

      Inicializuje seznam autorů, pokud není definován.

      :return: None.


.. py:class:: NewsFeedClient

   Client for fetching and parsing news feed data.

   **Metody:**

   .. py:method:: __init__()

      Initialize the news feed client.

      :param base_url: Base URL for fetching feed data from aiscr-news.
      :param timeout: Request timeout in seconds.

   .. py:method:: fetch_feed()

      Fetch and parse the news feed for the specified language.

      Fetches the feed from aiscr-news and transforms it into a
      list of NewsItem objects.

      :param language: Language code for the feed (e.g., "cs" or "en").
      :return: List of NewsItem objects.
      :raises NewsFeedError: If the feed cannot be fetched or parsed.

   .. py:method:: _parse_feed()

      Parse the feed data into NewsItem objects.

      :param data: Parsed JSON data from the feed.
      :return: List of NewsItem objects.
      :raises NewsFeedError: If data is not a valid dictionary.

   .. py:method:: _parse_item()

      Parse a single item from the feed data.

      :param item_data: Data for a single news item.
      :return: NewsItem object or None if the item cannot be parsed.


.. py:class:: NewsFeedError

   Exception raised when news feed operations fail.


.. py:class:: NewsFeedCache

   Cache wrapper for the news feed client.

   **Metody:**

   .. py:method:: __init__()

      Initialize the news feed cache.

      :param client: NewsFeedClient instance to wrap.
      :param cache_key_prefix: Prefix for cache keys.
      :param default_ttl: Default time-to-live in seconds for fresh copies.
      :param stale_ttl: Time-to-live in seconds for stale copies.
      :param block_height: Height of collapsed news block in pixels.

   .. py:method:: get_feed()

      Get the news feed, using cache if available.

      Implements a fresh-copy-first strategy:
      1. Try to get a fresh copy from cache
      2. If expired or missing, fetch from the feed service
      3. If fetch fails, return the last successful copy (stale copy)

      :param language: Language code for the feed.
      :return: List of news items, or empty list if unavailable.

   .. py:method:: set_stale()

      Set a stale copy in the cache.

      :param language: Language code for the feed.
      :param feed: List of news items to cache as stale.

