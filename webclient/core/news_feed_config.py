"""Runtime configuration for the login news feed."""

import hashlib
import json
import logging
import math
import re
import uuid
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

NEWS_FEED_GROUP = "news_feed"
NEWS_FEED_CONFIG_CACHE_KEY = "news_feed:configuration:v1"
NEWS_FEED_CONFIG_GENERATION_KEY = "news_feed:configuration:generation:v1"
NEWS_FEED_CONFIG_CACHE_TTL = 60
NEWS_FEED_BLOCK_HEIGHT_CACHE_KEY = "news_feed_block_height:v1"
NEWS_FEED_MIN_CACHE_TTL = 600

NEWS_FEED_DEFAULTS = {
    "news_feed_block_height": 300,
    "news_feed_base_url": "https://arup-cas.github.io/aiscr-news/feed/amcr",
    "news_feed_languages": ["cs", "en"],
    "news_feed_cache_ttl": 3600,
    "news_feed_cache_key_prefix": "news_feed",
    "news_feed_timeout": 10.0,
    "news_feed_warning_rate_limit": 3600,
}

FETCH_SETTING_IDS = frozenset(
    {
        "news_feed_base_url",
        "news_feed_languages",
        "news_feed_cache_ttl",
        "news_feed_cache_key_prefix",
        "news_feed_timeout",
    }
)

_CACHE_PREFIX_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:_-]{0,63}$")
_TRUSTED_FEED_HOST = "arup-cas.github.io"


@dataclass(frozen=True)
class NewsFeedConfig:
    """Immutable parsed configuration shared by web and worker processes."""

    block_height: int
    base_url: str
    languages: tuple[str, ...]
    cache_ttl: int
    cache_key_prefix: str
    timeout: float
    warning_rate_limit: int

    def fetch_fingerprint(self) -> str:
        """Vypočítá otisk nastavení ovlivňujících načítání zpráv.

        :return: SHA-256 otisk konfigurace načítání.
        """
        data = {
            "base_url": self.base_url,
            "languages": self.languages,
            "cache_ttl": self.cache_ttl,
            "cache_key_prefix": self.cache_key_prefix,
            "timeout": self.timeout,
        }
        encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def cache_identity(self) -> str:
        """Určí identitu zdroje pro oddělení položek v cache.

        :return: Zkrácený otisk URL zdroje.
        """
        return hashlib.sha256(self.base_url.encode("utf-8")).hexdigest()[:16]

    def cache_keys(self, language: str) -> tuple[str, str]:
        """Sestaví klíče čerstvých a posledních platných zpráv.

        :param language: Jazyk zpráv uložených pod danými klíči.
        :return: Dvojice klíčů pro čerstvé a poslední platné zprávy.
        """
        source_key = f"{self.cache_key_prefix}:{self.cache_identity()}:{language}"
        return f"{source_key}:{self.fetch_fingerprint()[:16]}", f"{source_key}:last-good"


def _positive_integer(value: str) -> int:
    result = int(value)
    if result <= 0:
        raise ValueError("must be a positive integer")
    return result


def _parse_base_url(value: str) -> str:
    value = value.strip().rstrip("/")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname != _TRUSTED_FEED_HOST
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
        or parsed.query
        or parsed.fragment
        or not parsed.path.startswith("/aiscr-news/feed/")
    ):
        raise ValueError("must be an HTTPS URL under the trusted AMCR feed directory")
    return urlunsplit(("https", _TRUSTED_FEED_HOST, parsed.path.rstrip("/"), "", ""))


def _parse_languages(value: str) -> tuple[str, ...]:
    parsed = json.loads(value)
    if not isinstance(parsed, list) or not parsed:
        raise ValueError("must be a non-empty JSON array")
    languages = [code for code, _label in settings.LANGUAGES]
    if any(not isinstance(item, str) or item not in languages for item in parsed):
        raise ValueError("contains an unsupported language")
    if len(set(parsed)) != len(parsed):
        raise ValueError("contains duplicate languages")
    return tuple(parsed)


def _parse_timeout(value: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError("must be a positive finite number")
    return result


def _parse_cache_prefix(value: str) -> str:
    value = value.strip()
    if not _CACHE_PREFIX_RE.fullmatch(value):
        raise ValueError("must be 1-64 letters, digits, colon, underscore, or hyphen")
    return value


def parse_news_feed_value(item_id: str, value: str):
    """Převede a ověří hodnotu nastavení zpráv.

    :param item_id: Identifikátor určující způsob převodu.
    :param value: Textová hodnota nastavení k převodu.
    """
    if item_id == "news_feed_block_height":
        return _positive_integer(value)
    if item_id == "news_feed_base_url":
        return _parse_base_url(value)
    if item_id == "news_feed_languages":
        return _parse_languages(value)
    if item_id == "news_feed_cache_ttl":
        result = _positive_integer(value)
        if result < NEWS_FEED_MIN_CACHE_TTL:
            raise ValueError(f"must be at least {NEWS_FEED_MIN_CACHE_TTL} seconds")
        return result
    if item_id == "news_feed_cache_key_prefix":
        return _parse_cache_prefix(value)
    if item_id == "news_feed_timeout":
        return _parse_timeout(value)
    if item_id == "news_feed_warning_rate_limit":
        return _positive_integer(value)
    raise ValueError(f"unsupported news-feed setting: {item_id}")


def validate_news_feed_setting(instance) -> None:
    """Ověří administrátorské nastavení zpráv a odmítne neplatné hodnoty.

    :param instance: Ukládaná instance administrátorského nastavení.
    """
    if instance.item_group != NEWS_FEED_GROUP:
        return
    if instance.item_id not in NEWS_FEED_DEFAULTS:
        raise ValidationError({"item_id": "Unsupported setting for the news_feed group."})
    from core.setting_models import CustomAdminSettings

    duplicates = CustomAdminSettings.objects.filter(item_group=NEWS_FEED_GROUP, item_id=instance.item_id)
    if instance.pk:
        duplicates = duplicates.exclude(pk=instance.pk)
    if duplicates.exists():
        raise ValidationError({"item_id": "A setting with this news-feed identifier already exists."})
    raw_value = instance.value
    if instance.item_id == "news_feed_languages" and isinstance(raw_value, list):
        raw_value = json.dumps(raw_value)
    try:
        parse_news_feed_value(instance.item_id, raw_value)
    except (ValueError, TypeError, json.JSONDecodeError) as err:
        raise ValidationError({"value": str(err)}) from err


def _default_config() -> NewsFeedConfig:
    return NewsFeedConfig(
        block_height=NEWS_FEED_DEFAULTS["news_feed_block_height"],
        base_url=NEWS_FEED_DEFAULTS["news_feed_base_url"],
        languages=tuple(NEWS_FEED_DEFAULTS["news_feed_languages"]),
        cache_ttl=NEWS_FEED_DEFAULTS["news_feed_cache_ttl"],
        cache_key_prefix=NEWS_FEED_DEFAULTS["news_feed_cache_key_prefix"],
        timeout=NEWS_FEED_DEFAULTS["news_feed_timeout"],
        warning_rate_limit=NEWS_FEED_DEFAULTS["news_feed_warning_rate_limit"],
    )


def get_news_feed_config(force_refresh: bool = False) -> NewsFeedConfig:
    """Načte konfiguraci zpráv a neplatné hodnoty nahradí výchozími.

    :param force_refresh: Při pravdivé hodnotě obejde uložený snímek konfigurace.
    :return: Aktuální nebo dočasně uložená konfigurace zpráv.
    """
    cache = caches["default"]
    cache.add(NEWS_FEED_CONFIG_GENERATION_KEY, uuid.uuid4().hex, timeout=None)
    generation = cache.get(NEWS_FEED_CONFIG_GENERATION_KEY)
    if generation is None:
        generation = uuid.uuid4().hex
        cache.set(NEWS_FEED_CONFIG_GENERATION_KEY, generation, timeout=None)
    config_cache_key = f"{NEWS_FEED_CONFIG_CACHE_KEY}:{generation}"
    if not force_refresh:
        cached = cache.get(config_cache_key)
        if isinstance(cached, NewsFeedConfig):
            return cached

    from core.setting_models import CustomAdminSettings

    rows = CustomAdminSettings.objects.filter(item_group=NEWS_FEED_GROUP).values_list("item_id", "value")
    values = {}
    duplicates = set()
    for item_id, value in rows:
        if item_id in values:
            duplicates.add(item_id)
        values[item_id] = value

    parsed = {}
    defaults = _default_config()
    field_names = {
        "news_feed_block_height": "block_height",
        "news_feed_base_url": "base_url",
        "news_feed_languages": "languages",
        "news_feed_cache_ttl": "cache_ttl",
        "news_feed_cache_key_prefix": "cache_key_prefix",
        "news_feed_timeout": "timeout",
        "news_feed_warning_rate_limit": "warning_rate_limit",
    }
    for item_id, field_name in field_names.items():
        default_value = getattr(defaults, field_name)
        if item_id in duplicates:
            logger.error("Multiple news feed settings found for %s; using default.", item_id)
            parsed[field_name] = default_value
            continue
        if item_id not in values:
            logger.warning("News feed setting %s is missing; using default.", item_id)
            parsed[field_name] = default_value
            continue
        try:
            parsed[field_name] = parse_news_feed_value(item_id, values[item_id])
        except (ValueError, TypeError, json.JSONDecodeError) as err:
            logger.warning("Invalid news feed setting %s (%s); using default.", item_id, err)
            parsed[field_name] = default_value

    config = NewsFeedConfig(**parsed)
    cache.set(config_cache_key, config, NEWS_FEED_CONFIG_CACHE_TTL)
    return config


def invalidate_news_feed_config_cache() -> None:
    """Invalidate the parsed configuration shared by all application processes."""
    cache = caches["default"]
    cache.set(NEWS_FEED_CONFIG_GENERATION_KEY, uuid.uuid4().hex, timeout=None)
    cache.delete(NEWS_FEED_CONFIG_CACHE_KEY)


def get_news_feed_cache_keys(language: str, config: NewsFeedConfig | None = None) -> tuple[str, str]:
    """Sestaví klíče cache zpráv podle zdroje a jazyka.

    :param language: Jazyk zpráv v cache.
    :param config: Použitá konfigurace; pokud chybí, načte se aktuální.
    :return: Klíče čerstvých a posledních platných zpráv.
    """
    return (config or get_news_feed_config()).cache_keys(language)


def fetch_configuration_fingerprint(config: NewsFeedConfig | None = None) -> str:
    """Určí otisk nastavení používaných při načítání zpráv.

    :param config: Použitá konfigurace; pokud chybí, načte se aktuální.
    :return: Otisk nastavení načítání zpráv.
    """
    return (config or get_news_feed_config()).fetch_fingerprint()
