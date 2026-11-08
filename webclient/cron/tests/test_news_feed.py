"""Focused tests for asynchronous news-feed loading and source isolation."""

from unittest.mock import Mock, patch

from core.news_feed_config import get_news_feed_config
from core.setting_models import CustomAdminSettings
from cron.tasks import load_news_feed
from django.core.cache import caches
from django.test import TestCase, override_settings


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "news-feed-task-tests"}}
)
class LoadNewsFeedTest(TestCase):
    """Checks fetch settings, stale results, and same-source fallback behavior."""

    def setUp(self):
        """Připraví izolovaný stav pro test nastavení zpráv."""
        caches["default"].clear()

    @staticmethod
    def set_setting(item_id, value):
        """Uloží hodnotu vybraného nastavení zpráv.

        :param item_id: Identifikátor nastavení zpráv.
        :param value: Hodnota uložená do nastavení.
        """
        CustomAdminSettings.objects.update_or_create(
            item_group="news_feed",
            item_id=item_id,
            defaults={"value": value},
        )

    @patch("cron.tasks.requests.get")
    def test_success_uses_dynamic_url_timeout_ttl_and_cache_keys(self, get):
        """Ověří načtení zpráv s aktuální URL a uložením do příslušné cache.

        :param get: Náhrada HTTP požadavku na zdroj zpráv.
        """
        self.set_setting("news_feed_base_url", "https://arup-cas.github.io/aiscr-news/feed/custom")
        self.set_setting("news_feed_cache_ttl", "600")
        response = Mock()
        response.json.return_value = {"items": []}
        get.return_value = response

        self.assertTrue(load_news_feed.run())

        get.assert_any_call("https://arup-cas.github.io/aiscr-news/feed/custom/cs.json", timeout=10.0)
        config = get_news_feed_config(force_refresh=True)
        fresh_key, _last_good_key = config.cache_keys("cs")
        self.assertEqual(caches["default"].get(fresh_key), [])

    @patch("cron.tasks.requests.get")
    def test_empty_feed_does_not_replace_last_good_copy(self, get):
        """Ověří zachování poslední platné kopie při prázdném kanálu.

        :param get: Náhrada HTTP požadavku na zdroj zpráv.
        """
        config = get_news_feed_config(force_refresh=True)
        fresh_key, last_good_key = config.cache_keys("cs")
        previous = ["previous-item"]
        caches["default"].set(last_good_key, previous, None)
        response = Mock()
        response.json.return_value = {"items": []}
        get.return_value = response

        self.assertTrue(load_news_feed.run(languages=["cs"]))

        self.assertEqual(caches["default"].get(fresh_key), [])
        self.assertEqual(caches["default"].get(last_good_key), previous)

    @patch("cron.tasks.requests.get")
    def test_old_fetch_cannot_publish_under_new_configuration(self, get):
        """Ověří, že starý požadavek nezveřejní data po změně konfigurace.

        :param get: Náhrada HTTP požadavku na zdroj zpráv.
        """
        self.set_setting("news_feed_languages", '["cs"]')
        response = Mock()
        response.json.return_value = {"items": []}

        def change_source_during_request(*_args, **_kwargs):
            self.set_setting("news_feed_base_url", "https://arup-cas.github.io/aiscr-news/feed/new")
            return response

        get.side_effect = change_source_during_request
        old_config = get_news_feed_config(force_refresh=True)

        self.assertTrue(load_news_feed.run())

        old_fresh, _old_last_good = old_config.cache_keys("cs")
        self.assertIsNone(caches["default"].get(old_fresh))

    @patch("cron.tasks.requests.get", side_effect=TimeoutError("timeout"))
    @patch.object(load_news_feed, "retry", side_effect=RuntimeError("retry requested"))
    def test_failed_fetch_retries_without_replacing_same_source_last_good(self, retry, _get):
        """Ověří opakování neúspěšného načtení a zachování poslední platné kopie.

        :param retry: Náhrada pro opakování úlohy.
        :param _get: Náhrada HTTP požadavku vyvolávající chybu.
        """
        config = get_news_feed_config(force_refresh=True)
        _fresh_key, last_good_key = config.cache_keys("cs")
        previous = ["previous-item"]
        caches["default"].set(last_good_key, previous, None)

        with self.assertRaisesRegex(RuntimeError, "retry requested"):
            load_news_feed.run()

        self.assertEqual(caches["default"].get(last_good_key), previous)
        retry.assert_called_once()

    @patch("cron.tasks.requests.get")
    @patch.object(load_news_feed, "retry", side_effect=RuntimeError("retry requested"))
    def test_invalid_json_is_retried(self, retry, get):
        """Ověří opakování načtení při neplatném JSON.

        :param retry: Náhrada pro opakování úlohy.
        :param get: Náhrada HTTP požadavku na zdroj zpráv.
        """
        response = Mock()
        response.json.side_effect = ValueError("invalid JSON")
        get.return_value = response

        with self.assertRaisesRegex(RuntimeError, "retry requested"):
            load_news_feed.run(languages=["cs"])

        retry.assert_called_once()
