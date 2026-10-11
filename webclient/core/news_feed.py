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

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import bleach

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


def _parse_feed(data):
    """Zpracuje data kanálu na seznam novinek."""
    if not isinstance(data, dict):
        return []

    items_list = data.get("items")
    if not isinstance(items_list, list):
        return []

    items = []
    for item_data in items_list:
        if isinstance(item_data, dict):
            # Zpracovat všechny pole přímo z item_data
            items.append(
                NewsItem(
                    date=datetime.fromisoformat(item_data.get("date", "")),
                    title=item_data.get("title", ""),
                    excerpt=item_data.get("excerpt", ""),
                    html=sanitize_html(item_data.get("html")),
                    badge=item_data.get("badge"),
                    image=item_data.get("image"),
                    authors=_process_authors(item_data.get("authors", [])),
                )
            )
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

    # First, remove script tags and their content (bleach doesn't strip content by default)
    import re

    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)

    # Remove style tags and their content
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)

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
    if not authors_data:
        return ""

    if isinstance(authors_data, list) and len(authors_data) > 0:
        authors_list = []
        for author in authors_data:
            if isinstance(author, dict):
                name = author.get("name", "")
                role = author.get("role", "")
                authors_list.append(f"{name} ({role})" if role else name)
            else:
                authors_list.append(str(author))
        return ", ".join(authors_list)
    return ""
