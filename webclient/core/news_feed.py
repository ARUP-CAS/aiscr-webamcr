"""
News feed client and cache for fetching and parsing news from aiscr-news.

This module provides functionality to fetch news feed data from the
aiscr-news service and transform it into a standardized format for
use in the AMČR web application.

The feed data is fetched from the aiscr-news repository and is
considered trusted content. The html field is rendered as trusted
HTML because it is generated and published by the controlled
aiscr-news repository.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """Represents a single news item from the feed."""

    date: datetime
    title: str
    excerpt: str
    url: str = ""
    html: Optional[str] = None
    badge: Optional[str] = None
    image: Optional[str] = None
    authors: list[dict] = None

    def __post_init__(self):
        """
        Inicializuje seznam autorů, pokud není definován.

        :return: None.
        """
        if self.authors is None:
            self.authors = ""
        elif isinstance(self.authors, list) and len(self.authors) > 0:
            # Ensure authors is a list of strings (authors come as dicts from feed)
            logger.debug(f"Parsing authors: {self.authors[0]}")
            authors_list = []
            for author in self.authors:
                if isinstance(author, dict):
                    name = author.get("name", "")
                    role = author.get("role", "")
                    authors_list.append(f"{name} ({role})" if role else name)
                else:
                    authors_list.append(str(author))
            self.authors = ", ".join(authors_list)
        else:
            self.authors = ""


class NewsFeedClient:
    """Client for fetching and parsing news feed data."""

    def __init__(
        self,
        base_url: str = "https://raw.githubusercontent.com/ARUP-CAS/aiscr-news/main",
        timeout: int = 10,
    ):
        """
        Initialize the news feed client.

        :param base_url: Base URL for fetching feed data from aiscr-news.
        :param timeout: Request timeout in seconds.
        """
        self.base_url = base_url
        self.timeout = timeout

    def fetch_feed(self, language: str = "cs") -> list[NewsItem]:
        """
        Fetch and parse the news feed for the specified language.

        Fetches the feed from aiscr-news and transforms it into a
        list of NewsItem objects.

        :param language: Language code for the feed (e.g., "cs" or "en").
        :return: List of NewsItem objects.
        :raises NewsFeedError: If the feed cannot be fetched or parsed.
        """
        try:
            # Use /amcr/ prefix in the feed endpoint
            feed_url = f"{self.base_url}/{language}.json"
            response = requests.get(feed_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return self._parse_feed(data)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch news feed from {feed_url}: {e}")
            raise NewsFeedError(f"Failed to fetch news feed: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in news feed: {e}")
            raise NewsFeedError(f"Invalid JSON in news feed: {e}")

    def _parse_feed(self, data: Any) -> list[NewsItem]:
        """
        Parse the feed data into NewsItem objects.

        :param data: Parsed JSON data from the feed.
        :return: List of NewsItem objects.
        :raises NewsFeedError: If data is not a valid dictionary.
        """
        # Validate that data is a dictionary (handle malformed but valid JSON)
        if not isinstance(data, dict):
            logger.warning(f"Feed data is not a dictionary: {type(data).__name__}: {data}")
            raise json.JSONDecodeError("Feed data is not a dictionary", str(data), 0)

        # Validate that items is a list
        items_list = data.get("items")
        if not isinstance(items_list, list):
            logger.warning(f"Feed items is not a list: {type(items_list).__name__}: {items_list}")
            raise json.JSONDecodeError("Feed items is not a list", str(items_list), 0)

        items = []
        for item_data in items_list:
            item = self._parse_item(item_data)
            if item:
                items.append(item)
        return items

    def _parse_item(self, item_data: dict[str, Any]) -> Optional[NewsItem]:
        """
        Parse a single item from the feed data.

        :param item_data: Data for a single news item.
        :return: NewsItem object or None if the item cannot be parsed.
        """
        try:
            # Ensure item_data is a dict (handle malformed but valid JSON)
            if not isinstance(item_data, dict):
                logger.warning(f"Item is not a dictionary: {item_data}")
                return None

            date_str = item_data.get("date")
            if not date_str:
                logger.warning(f"Item missing date: {item_data}")
                return None

            date = datetime.fromisoformat(date_str)

            title = item_data.get("title", "")
            excerpt = item_data.get("excerpt", "")
            html = item_data.get("html")
            badge = item_data.get("badge")
            image = item_data.get("image")
            authors = item_data.get("authors", [])
            url = item_data.get("url", "")

            return NewsItem(
                date=date,
                title=title,
                excerpt=excerpt,
                html=html,
                badge=badge,
                image=image,
                authors=authors if authors else [],
                url=url,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse item: {item_data}, error: {e}")
            return None


class NewsFeedError(Exception):
    """Exception raised when news feed operations fail."""

    pass


class NewsFeedCache:
    """Cache wrapper for the news feed client."""

    def __init__(
        self,
        client: NewsFeedClient,
        cache_key_prefix: str = "news_feed",
        default_ttl: int = 300,
        stale_ttl: int = 600,
        block_height: int = None,
    ):
        """
        Initialize the news feed cache.

        :param client: NewsFeedClient instance to wrap.
        :param cache_key_prefix: Prefix for cache keys.
        :param default_ttl: Default time-to-live in seconds for fresh copies.
        :param stale_ttl: Time-to-live in seconds for stale copies.
        :param block_height: Height of collapsed news block in pixels.
        """
        self.client = client
        self.cache_key_prefix = cache_key_prefix
        self.default_ttl = default_ttl
        self.stale_ttl = stale_ttl
        self.block_height = block_height

    def get_feed(self, language: str = "cs") -> list:
        """
        Get the news feed, using cache if available.

        Implements a fresh-copy-first strategy:
        1. Try to get a fresh copy from cache
        2. If expired or missing, fetch from the feed service
        3. If fetch fails, return the last successful copy (stale copy)

        :param language: Language code for the feed.
        :return: List of news items, or empty list if unavailable.
        """
        cache_key = f"{self.cache_key_prefix}:{language}"

        # Try to get fresh copy from cache
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for {cache_key}")
            return cached

        # Cache miss - try to fetch from feed service
        try:
            logger.debug(f"Cache miss for {cache_key}, fetching from feed service")
            feed = self.client.fetch_feed(language)
            cache.set(cache_key, feed, self.default_ttl)
            self.set_stale(language, feed)
            logger.info(f"Fresh feed fetched and cached for {cache_key}")
            return feed
        except NewsFeedError as e:
            logger.warning(f"Failed to fetch news feed: {e}")

            # Try to get stale copy from cache
            stale_key = f"{cache_key}:stale"
            stale_feed = cache.get(stale_key)
            if stale_feed is not None:
                logger.info(f"Using stale copy from cache for {cache_key}")
                return stale_feed

            logger.warning(f"No stale copy available for {cache_key}")
            return []
        except (AttributeError, TypeError) as e:
            # Handle malformed but valid JSON (e.g., list instead of dict, scalar instead of list)
            logger.error(f"Malformed JSON in news feed (not a mapping): {e}")

            # Try to get stale copy from cache instead of raising an error
            stale_key = f"{cache_key}:stale"
            stale_feed = cache.get(stale_key)
            if stale_feed is not None:
                logger.info(f"Using stale copy from cache for {cache_key} due to malformed JSON")
                return stale_feed

            logger.warning(f"No stale copy available for {cache_key} due to malformed JSON")
            return []

    def set_stale(self, language: str = "cs", feed: list = None) -> None:
        """
        Set a stale copy in the cache.

        :param language: Language code for the feed.
        :param feed: List of news items to cache as stale.
        """
        cache_key = f"{self.cache_key_prefix}:{language}:stale"
        if feed is not None:
            cache.set(cache_key, feed, self.stale_ttl)
            logger.info(f"Stale copy set for {cache_key}")
