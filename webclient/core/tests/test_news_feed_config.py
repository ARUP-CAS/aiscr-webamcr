"""Tests for the central login news-feed configuration reader."""

import json
from importlib import import_module
from types import SimpleNamespace

from core.news_feed_config import (
    NEWS_FEED_DEFAULTS,
    NewsFeedConfig,
    get_news_feed_config,
    parse_news_feed_value,
    validate_news_feed_setting,
)
from core.setting_models import CustomAdminSettings
from django.apps import apps
from django.core.cache import caches
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase, override_settings


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "news-feed-tests"}}
)
class NewsFeedConfigTest(TestCase):
    """Covers defaults, parsing, malformed rows, and stable feed identities."""

    def setUp(self):
        """Připraví izolovaný stav pro test nastavení zpráv."""
        caches["default"].clear()
        CustomAdminSettings.objects.filter(item_group="news_feed").delete()

    def test_missing_rows_use_documented_defaults(self):
        """Ověří výchozí hodnoty při chybějících nastaveních."""
        config = get_news_feed_config(force_refresh=True)

        self.assertEqual(config.block_height, 300)
        self.assertEqual(config.base_url, "https://arup-cas.github.io/aiscr-news/feed/amcr")
        self.assertEqual(config.languages, ("cs", "en"))
        self.assertEqual(config.cache_ttl, 3600)
        self.assertEqual(config.cache_key_prefix, "news_feed")
        self.assertEqual(config.timeout, 10.0)
        self.assertEqual(config.warning_rate_limit, 3600)

    def test_valid_rows_parse_to_runtime_types(self):
        """Ověří převod platných nastavení na používané typy."""
        for item_id, value in NEWS_FEED_DEFAULTS.items():
            if not isinstance(value, str):
                value = json.dumps(value)
            CustomAdminSettings.objects.create(item_group="news_feed", item_id=item_id, value=value)

        config = get_news_feed_config(force_refresh=True)

        self.assertIsInstance(config, NewsFeedConfig)
        self.assertEqual(config.languages, ("cs", "en"))
        self.assertEqual(config.timeout, 10.0)

    def test_malformed_and_duplicate_rows_fall_back_per_setting(self):
        """Ověří výchozí hodnoty pro neplatná a duplicitní nastavení."""
        CustomAdminSettings.objects.create(item_group="news_feed", item_id="news_feed_block_height", value="-2")
        CustomAdminSettings.objects.create(item_group="news_feed", item_id="news_feed_cache_ttl", value="100")
        CustomAdminSettings.objects.create(item_group="news_feed", item_id="news_feed_cache_ttl", value="200")

        with self.assertLogs("core.news_feed_config", level="WARNING"):
            config = get_news_feed_config(force_refresh=True)

        self.assertEqual(config.block_height, 300)
        self.assertEqual(config.cache_ttl, 3600)

    def test_languages_reject_duplicates_and_unsupported_codes(self):
        """Ověří odmítnutí duplicitních a nepodporovaných jazyků."""
        with self.assertRaises(ValueError):
            parse_news_feed_value("news_feed_languages", '["cs", "cs"]')
        with self.assertRaises(ValueError):
            parse_news_feed_value("news_feed_languages", '["cs", "fr"]')

    def test_base_url_is_normalized_and_rejects_other_origins(self):
        """Ověří normalizaci URL a odmítnutí jiných zdrojů."""
        self.assertEqual(
            parse_news_feed_value("news_feed_base_url", "https://arup-cas.github.io/aiscr-news/feed/amcr/"),
            "https://arup-cas.github.io/aiscr-news/feed/amcr",
        )
        with self.assertRaises(ValueError):
            parse_news_feed_value("news_feed_base_url", "http://arup-cas.github.io/aiscr-news/feed/amcr")
        with self.assertRaises(ValueError):
            parse_news_feed_value("news_feed_base_url", "https://example.com/feed")

    def test_source_identity_and_fetch_fingerprint_change_with_source(self):
        """Ověří změnu identity a otisku při změně zdroje."""
        original = get_news_feed_config(force_refresh=True)
        CustomAdminSettings.objects.create(
            item_group="news_feed",
            item_id="news_feed_base_url",
            value="https://arup-cas.github.io/aiscr-news/feed/other",
        )
        changed = get_news_feed_config(force_refresh=True)

        self.assertNotEqual(original.cache_keys("cs"), changed.cache_keys("cs"))
        self.assertNotEqual(original.fetch_fingerprint(), changed.fetch_fingerprint())

    def test_ttl_change_separates_fresh_data_but_keeps_same_source_last_good(self):
        """Ověří oddělení čerstvých dat při zachování posledních platných zpráv po změně TTL."""
        config = get_news_feed_config(force_refresh=True)
        changed_ttl = NewsFeedConfig(
            block_height=config.block_height,
            base_url=config.base_url,
            languages=config.languages,
            cache_ttl=660,
            cache_key_prefix=config.cache_key_prefix,
            timeout=config.timeout,
            warning_rate_limit=config.warning_rate_limit,
        )

        fresh, last_good = config.cache_keys("cs")
        changed_fresh, changed_last_good = changed_ttl.cache_keys("cs")
        self.assertNotEqual(fresh, changed_fresh)
        self.assertEqual(last_good, changed_last_good)
        self.assertNotEqual(last_good, config.cache_keys("en")[1])

    def test_namespace_change_separates_fresh_and_last_good_entries(self):
        """Ověří oddělení obou položek cache při změně prefixu."""
        config = get_news_feed_config(force_refresh=True)
        changed_prefix = NewsFeedConfig(
            block_height=config.block_height,
            base_url=config.base_url,
            languages=config.languages,
            cache_ttl=config.cache_ttl,
            cache_key_prefix="news_feed_alt",
            timeout=config.timeout,
            warning_rate_limit=config.warning_rate_limit,
        )

        self.assertNotEqual(config.cache_keys("cs"), changed_prefix.cache_keys("cs"))


class NewsFeedSettingValidationTest(TestCase):
    """Validates administrator values without involving unrelated setting groups."""

    def setUp(self):
        """Připraví izolovaný stav pro test nastavení zpráv."""
        CustomAdminSettings.objects.filter(item_group="news_feed").delete()

    def test_valid_settings_pass_validation(self):
        """Ověří přijetí platných hodnot nastavení."""
        setting = CustomAdminSettings(item_group="news_feed", item_id="news_feed_languages", value='["cs", "en"]')

        validate_news_feed_setting(setting)

    def test_invalid_settings_are_rejected(self):
        """Ověří odmítnutí neplatných hodnot nastavení."""
        invalid = [
            ("news_feed_base_url", "http://arup-cas.github.io/aiscr-news/feed/amcr"),
            ("news_feed_languages", '["cs", "cs"]'),
            ("news_feed_cache_ttl", "0"),
            ("news_feed_timeout", "NaN"),
            ("news_feed_cache_key_prefix", "invalid prefix"),
            ("unexpected_setting", "value"),
        ]
        for item_id, value in invalid:
            with self.subTest(item_id=item_id), self.assertRaises(ValidationError):
                validate_news_feed_setting(CustomAdminSettings(item_group="news_feed", item_id=item_id, value=value))

    def test_duplicate_administrator_identifier_is_rejected(self):
        """Ověří odmítnutí duplicitního identifikátoru nastavení."""
        CustomAdminSettings.objects.get_or_create(
            item_group="news_feed", item_id="news_feed_cache_ttl", defaults={"value": "3600"}
        )
        with self.assertRaises(ValidationError):
            validate_news_feed_setting(
                CustomAdminSettings(item_group="news_feed", item_id="news_feed_cache_ttl", value="600")
            )


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "news-feed-migration-tests",
        }
    }
)
class SeedNewsFeedSettingsMigrationTest(TestCase):
    """Checks one-time migration seeding preserves existing administrator choices."""

    def test_creates_missing_settings_and_preserves_existing_values(self):
        """Ověří doplnění chybějících nastavení a zachování existujících hodnot."""
        migration = import_module("core.migrations.0035_initialize_news_feed_settings")
        schema_editor = SimpleNamespace(connection=connection)
        CustomAdminSettings.objects.filter(item_group="news_feed").delete()
        CustomAdminSettings.objects.create(item_group="news_feed", item_id="news_feed_block_height", value="420")
        CustomAdminSettings.objects.create(
            item_group="news_feed",
            item_id="news_feed_base_url",
            value="https://arup-cas.github.io/aiscr-news/feed/custom",
        )

        with self.assertWarns(RuntimeWarning):
            migration.seed_news_feed_settings(apps, schema_editor)
        migration.seed_news_feed_settings(apps, schema_editor)

        self.assertEqual(
            CustomAdminSettings.objects.get(item_group="news_feed", item_id="news_feed_block_height").value, "420"
        )
        self.assertEqual(
            CustomAdminSettings.objects.get(item_group="news_feed", item_id="news_feed_base_url").value,
            "https://arup-cas.github.io/aiscr-news/feed/custom",
        )
        self.assertEqual(CustomAdminSettings.objects.filter(item_group="news_feed").count(), 7)
