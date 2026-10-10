"""
Klient a cache novinkového kanálu pro načítání a zpracování novinek ze služby aiscr-news.

Modul zajišťuje načítání dat novinkového kanálu ze služby aiscr-news
a jejich převod do standardizovaného formátu pro použití ve webové
aplikaci AMČR.

Data kanálu se načítají z repozitáře aiscr-news a považují se za
důvěryhodný obsah. Pole html se vykresluje jako důvěryhodné HTML,
protože je generuje a publikuje kontrolovaný repozitář aiscr-news.
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
    """Představuje jednu novinku z kanálu."""

    date: datetime
    title: str
    excerpt: str
    html: Optional[str] = None
    badge: Optional[str] = None
    image: Optional[str] = None
    authors: Optional[str] = None


class NewsFeedClient:
    """Klient pro načítání a zpracování dat novinkového kanálu."""

    def __init__(
        self,
        base_url: str,
        timeout: int,
    ):
        """
        Inicializuje klienta novinkového kanálu.

        :param base_url: Základní URL pro načítání dat kanálu ze služby aiscr-news.
        :param timeout: Časový limit požadavku v sekundách.
        """
        self.base_url = base_url
        self.timeout = timeout

    def process_authors(self, authors_data: list[dict]) -> str:
        """
        Inicializuje seznam autorů.

        :param authors_data: Seznam autorů z kanálu.
        :return: Seznam autorů jako řetězec, oddělený čárkami, nebo prázdný řetězec, pokud nejsou autoři k dispozici.
        """
        if authors_data is None:
            return ""
        elif isinstance(authors_data, list) and len(authors_data) > 0:
            # Zajistí, aby autoři byli seznam řetězců (z kanálu přicházejí jako slovníky).
            authors_list = []
            for author in authors_data:
                if isinstance(author, dict):
                    name = author.get("name", "")
                    role = author.get("role", "")
                    authors_list.append(f"{name} ({role})" if role else name)
                else:
                    authors_list.append(str(author))
            return ", ".join(authors_list)
        else:
            return ""

    def fetch_feed(self, language: str = "cs") -> list[NewsItem]:
        """
        Načte a zpracuje novinkový kanál pro zadaný jazyk.

        Načte kanál ze služby aiscr-news a převede jej na seznam
        objektů NewsItem.

        :param language: Kód jazyka kanálu (např. "cs" nebo "en").
        :return: Seznam objektů NewsItem.
        :raises NewsFeedError: Pokud kanál nelze načíst nebo zpracovat.
        """
        try:
            # Adresa kanálu obsahuje prefix /amcr/
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
        Zpracuje data kanálu na objekty NewsItem.

        :param data: Zpracovaná JSON data kanálu.
        :return: Seznam objektů NewsItem.
        :raises json.JSONDecodeError: Pokud data nejsou platný slovník.
        """
        # Ověří, že data jsou slovník (ošetření poškozeného, ale syntakticky platného JSON).
        if not isinstance(data, dict):
            logger.warning(f"Feed data is not a dictionary: {type(data).__name__}: {data}")
            raise json.JSONDecodeError("Feed data is not a dictionary", str(data), 0)

        # Ověří, že položky jsou seznam.
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
        Zpracuje jednu položku z dat kanálu.

        :param item_data: Data jedné novinky.
        :return: Objekt NewsItem, nebo None, pokud položku nelze zpracovat.
        """
        try:
            # Ověří, že item_data je slovník (ošetření poškozeného, ale syntakticky platného JSON).
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
            authors = self.process_authors(item_data.get("authors", []))
            return NewsItem(
                date=date,
                title=title,
                excerpt=excerpt,
                html=html,
                badge=badge,
                image=image,
                authors=authors if authors else [],
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse item: {item_data}, error: {e}")
            return None


class NewsFeedError(Exception):
    """Výjimka vyvolaná při selhání operací novinkového kanálu."""

    pass


class NewsFeedCache:
    """Cache obalující klienta novinkového kanálu."""

    def __init__(self, client: NewsFeedClient, default_ttl: int, cache_key_prefix: str = "news_feed"):
        """
        Inicializuje cache novinkového kanálu.

        :param client: Instance NewsFeedClient, která se obaluje.
        :param cache_key_prefix: Prefix klíčů cache.
        :param default_ttl: Výchozí doba platnosti v sekundách pro čerstvé kopie.
        """
        self.client = client
        self.cache_key_prefix = cache_key_prefix
        self.default_ttl = default_ttl

    def get_feed(self, language: str = "cs") -> list:
        """
        Vrátí novinkový kanál s využitím cache, je-li k dispozici.

        Uplatňuje strategii čerstvé kopie přednostně:
        1. Pokusí se získat čerstvou kopii z cache
        2. Pokud vypršela nebo chybí, načte kanál ze služby
        3. Pokud načtení selže, vrátí poslední úspěšnou kopii (zastaralou kopii)

        :param language: Kód jazyka kanálu.
        :return: Seznam novinek, nebo prázdný seznam, pokud nejsou dostupné.
        """
        cache_key = f"{self.cache_key_prefix}:{language}"

        # Pokusí se získat čerstvou kopii z cache
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for {cache_key}")
            return cached

        # Zásah do cache minul - pokusí se načíst ze služby
        stale_key = f"{cache_key}:stale"
        try:
            logger.debug(f"Cache miss for {cache_key}, fetching from feed service")
            feed = self.client.fetch_feed(language)
            cache.set(cache_key, feed, self.default_ttl)
            self.set_stale(stale_key, feed)
            logger.info(f"Fresh feed fetched and cached for {cache_key}")
            return feed
        except NewsFeedError as e:
            logger.warning(f"Failed to fetch news feed: {e}")

            # Pokusí se získat zastaralou kopii z cache
            stale_feed = cache.get(stale_key)
            if stale_feed is not None:
                logger.info(f"Using stale copy from cache for {cache_key}")
                return stale_feed

            logger.warning(f"No stale copy available for {cache_key}")
            return []

    def set_stale(self, stale_key: str, feed: list = None) -> None:
        """
        Uloží zastaralou kopii do cache.

        :param stale_key: Klíč cache pro zastaralou kopii.
        :param feed: Seznam novinek, který se uloží do cache jako zastaralý.
        """
        if feed is not None:
            cache.set(stale_key, feed, None)  # Zastaralá kopie nemá časový limit
            logger.info(f"Stale copy set for {stale_key}")
