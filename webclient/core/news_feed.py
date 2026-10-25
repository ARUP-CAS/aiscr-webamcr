"""
Data model novinkového kanálu.

Modul definuje dataclass NewsItem pro reprezentaci položky novinkového kanálu.
Tato třída je používána pro standardizaci struktury novinek z externího zdroje.

Data kanálu se načítají z repozitáře aiscr-news a považují se za
důvěryhodný obsah. Pole html se vykresluje jako důvěryhodné HTML,
protože je generuje a publikuje kontrolovaný repozitář aiscr-news.

Bezpečnostní upozornění: HTML obsah je sanitizován pomocí knihovny bleach
pro odstranění potenciálně nebezpečných prvků (scripty, event handlers atd.).
Pokud se zdroj kanálu změní nebo zdrojní repozitář nebude kontrolován,
je nutné přezkoumat konfiguraci sanitizace.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import bleach
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils.translation import gettext, gettext_noop

logger = logging.getLogger(__name__)

# Výchozí název neplatné položky; překlad probíhá při načítání kanálu pro jeho jazyk.
TITLE_PLACEHOLDER = gettext_noop("core.news_feed.invalid_item_title")

# Konfigurace sanitizace HTML pomocí bleach
ALLOWED_TAGS = [
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "br",
    "hr",
    "a",
    "strong",
    "em",
    "b",
    "i",
    "u",
    "strike",
    "s",
    "del",
    "ins",
    "ul",
    "ol",
    "li",
    "blockquote",
    "pre",
    "code",
    "img",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "span",
    "div",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "*": ["class"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


# Rate limiting for warnings to avoid log flooding
_warning_cache = {}


def _log_warning_rate_limited(slug: Optional[str], message: str):
    """Logs a warning only once per hour for the same slug."""
    if not slug:
        logger.warning(message)
        return

    current_time = datetime.now()
    last_logged = _warning_cache.get(slug)

    if last_logged is None or (current_time - last_logged).total_seconds() > settings.NEWS_FEED_WARNING_RATE_LIMIT:
        logger.warning(message)
        _warning_cache[slug] = current_time


@dataclass
class NewsItem:
    """Představuje jednu novinku z kanálu."""

    title: str
    excerpt: str
    date: Optional[datetime] = None
    html: Optional[str] = None
    badge: Optional[str] = None
    image: Optional[str] = None
    authors: Optional[str] = None


def get_news_feed_cache_keys(language: str) -> tuple[str, str]:
    """Vrátí klíče čerstvé a zastaralé kopie kanálu pro daný jazyk.

    :param language: Jazykový kód novinkového kanálu.
    :return: Dvojice klíčů cache pro čerstvou a zastaralou kopii kanálu.
    """
    cache_key = f"{settings.NEWS_FEED_CACHE_KEY_PREFIX}:{language}"
    return cache_key, f"{cache_key}:stale"


def _parse_item(item_data: dict) -> NewsItem:
    """Parsuje jeden záznam novinky.

    Pokud chybí nebo je neplatný datum, název nebo úvodní text, použije se
    překladovaný placeholder pro název a pole excerpt i date zůstanou prázdná.
    Položka se ponechá a v případě problému do logu se zapíše varování.
    """
    slug = item_data.get("slug")

    date = None
    try:
        date_str = item_data.get("date")
        if date_str:
            date = datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        _log_warning_rate_limited(slug, f"Neplatné datum položky novinek: {date_str}")

    title = item_data.get("title")
    excerpt = item_data.get("excerpt")

    if (
        not date
        or not isinstance(title, str)
        or not title.strip()
        or not isinstance(excerpt, str)
        or not excerpt.strip()
    ):
        _log_warning_rate_limited(
            slug,
            f"Položka novinek '{slug}' má chybějící nebo neplatný údaj; " f"použito placeholder '{TITLE_PLACEHOLDER}'.",
        )
        return NewsItem(
            title=gettext(TITLE_PLACEHOLDER),
            excerpt="",
            date=None,
        )

    return NewsItem(
        title=title,
        excerpt=excerpt,
        date=date,
        html=sanitize_html(item_data.get("html")),
        badge=item_data.get("badge"),
        image=item_data.get("image"),
        authors=_process_authors(item_data.get("authors", [])),
    )


def _parse_feed(data):
    """Zpracuje data kanálu na seznam novinek."""
    if not isinstance(data, dict):
        raise ValueError("News feed response must be a JSON object.")

    items_list = data.get("items")
    if not isinstance(items_list, list):
        raise ValueError("News feed response must contain an items list.")

    items = []
    for item_data in items_list:
        if not isinstance(item_data, dict):
            raise ValueError("Every news feed item must be a JSON object.")
        items.append(_parse_item(item_data))
    return items


def sanitize_html(html: str) -> str:
    """
    Sanitize HTML using bleach library.

    Removes potentially dangerous HTML elements while preserving safe content.
    This is used to sanitize HTML from the news feed before rendering.

    :param html: Raw HTML string from the feed
    :return: Sanitized HTML string
    """
    if not html:
        return ""

    # Remove script/style tags and their content using an HTML parser
    # This is more robust than regex for handling malformed HTML
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()
    html = str(soup)

    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )


def _process_authors(authors_data):
    """Inicializuje seznam autorů."""
    if not isinstance(authors_data, list):
        return ""

    authors_list = []
    for author in authors_data:
        if isinstance(author, dict):
            name = author.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            name = name.strip()
            role = author.get("role")
            role = role.strip() if isinstance(role, str) else ""
            authors_list.append(f"{name} ({role})" if role else name)
        elif isinstance(author, str) and author.strip():
            authors_list.append(author.strip())
    return ", ".join(authors_list)
