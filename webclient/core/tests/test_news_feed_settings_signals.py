"""Tests for transaction-aware login news-feed setting changes."""

from unittest.mock import patch

from core.news_feed_config import NEWS_FEED_BLOCK_HEIGHT_CACHE_KEY, NEWS_FEED_CONFIG_CACHE_KEY
from core.setting_models import CustomAdminSettings
from django.core.cache import caches
from django.db import transaction
from django.test import TestCase, override_settings


@override_settings(
    CACHES={
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "news-feed-signal-tests"}
    }
)
class NewsFeedSettingsSignalTest(TestCase):
    """Ensures committed changes invalidate only feed-specific runtime state."""

    def setUp(self):
        """Připraví izolovaný stav pro test nastavení zpráv."""
        caches["default"].clear()

    def create_without_signal(self, item_id, value):
        """Připraví nastavení bez spuštění následných akcí signálu.

        :param item_id: Identifikátor nastavení zpráv.
        :param value: Hodnota uložená do nastavení.
        """
        existing = CustomAdminSettings.objects.filter(item_group="news_feed", item_id=item_id).first()
        if existing:
            CustomAdminSettings.objects.filter(pk=existing.pk).update(value=value)
            existing.refresh_from_db()
            return existing
        return CustomAdminSettings.objects.bulk_create(
            [CustomAdminSettings(item_group="news_feed", item_id=item_id, value=value)]
        )[0]

    @patch("cron.tasks.load_news_feed.delay")
    def test_height_change_invalidates_legacy_cache_without_refresh(self, dispatch):
        """Ověří zneplatnění cache výšky bez spuštění obnovy zpráv.

        :param dispatch: Náhrada pro spuštění asynchronní obnovy.
        """
        setting = self.create_without_signal("news_feed_block_height", "300")
        cache = caches["default"]
        cache.set(NEWS_FEED_CONFIG_CACHE_KEY, "old-config")
        cache.set(NEWS_FEED_BLOCK_HEIGHT_CACHE_KEY, "300")
        with self.captureOnCommitCallbacks(execute=True):
            setting.value = "420"
            setting.save()

        self.assertIsNone(cache.get(NEWS_FEED_CONFIG_CACHE_KEY))
        self.assertIsNone(cache.get(NEWS_FEED_BLOCK_HEIGHT_CACHE_KEY))
        dispatch.assert_not_called()

    @patch("cron.tasks.load_news_feed.delay")
    def test_committed_fetch_setting_change_dispatches_current_languages(self, dispatch):
        """Ověří spuštění obnovy aktuálních jazyků po potvrzení změny.

        :param dispatch: Náhrada pro spuštění asynchronní obnovy.
        """
        setting = self.create_without_signal("news_feed_base_url", "https://arup-cas.github.io/aiscr-news/feed/old")
        caches["default"].set("unrelated:redis:value", "keep")
        with self.captureOnCommitCallbacks(execute=True):
            setting.value = "https://arup-cas.github.io/aiscr-news/feed/new"
            setting.save()

        dispatch.assert_called_once_with(languages=["cs", "en"])

    @patch("cron.tasks.load_news_feed.delay")
    def test_new_fetch_setting_dispatches_after_commit(self, dispatch):
        """Ověří spuštění obnovy po potvrzení nového nastavení zdroje.

        :param dispatch: Náhrada pro spuštění asynchronní obnovy.
        """
        CustomAdminSettings.objects.filter(item_group="news_feed", item_id="news_feed_base_url").delete()
        with self.captureOnCommitCallbacks(execute=True):
            CustomAdminSettings.objects.create(
                item_group="news_feed",
                item_id="news_feed_base_url",
                value="https://arup-cas.github.io/aiscr-news/feed/new",
            )

        dispatch.assert_called_once_with(languages=["cs", "en"])

    @patch("cron.tasks.load_news_feed.delay")
    def test_renamed_fetch_setting_uses_previous_and_saved_identities(self, dispatch):
        """Ověří reakci na přejmenování nastavení podle obou identit.

        :param dispatch: Náhrada pro spuštění asynchronní obnovy.
        """
        setting = self.create_without_signal("news_feed_base_url", "https://arup-cas.github.io/aiscr-news/feed/custom")
        caches["default"].set("unrelated:redis:value", "keep")
        with self.captureOnCommitCallbacks(execute=True):
            setting.item_id = "news_feed_test_renamed"
            setting.value = "feed_other"
            setting.save()

        dispatch.assert_called_once_with(languages=["cs", "en"])
        self.assertEqual(caches["default"].get("unrelated:redis:value"), "keep")

    @patch("cron.tasks.load_news_feed.delay")
    def test_rolled_back_change_does_not_dispatch_or_invalidate(self, dispatch):
        """Ověří zachování cache a vynechání obnovy po vrácení transakce.

        :param dispatch: Náhrada pro spuštění asynchronní obnovy.
        """
        cache = caches["default"]
        cache.set(NEWS_FEED_CONFIG_CACHE_KEY, "still-valid")
        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    CustomAdminSettings.objects.create(
                        item_group="news_feed",
                        item_id="news_feed_base_url",
                        value="https://arup-cas.github.io/aiscr-news/feed/new",
                    )
                    raise RuntimeError("rollback")
            except RuntimeError:
                pass

        self.assertEqual(cache.get(NEWS_FEED_CONFIG_CACHE_KEY), "still-valid")
        dispatch.assert_not_called()

    @patch("cron.tasks.load_news_feed.delay")
    def test_rename_out_of_news_feed_invalidates_previous_identity(self, dispatch):
        """Ověří zneplatnění původního nastavení při přesunu do jiné skupiny.

        :param dispatch: Náhrada pro spuštění asynchronní obnovy.
        """
        setting = self.create_without_signal("news_feed_base_url", "https://arup-cas.github.io/aiscr-news/feed/old")
        with self.captureOnCommitCallbacks(execute=True):
            setting.item_group = "other_group"
            setting.save()

        dispatch.assert_called_once_with(languages=["cs", "en"])

    @patch("cron.tasks.load_news_feed.delay")
    def test_deleting_feed_source_setting_dispatches_refresh(self, dispatch):
        """Ověří spuštění obnovy po smazání nastavení zdroje.

        :param dispatch: Náhrada pro spuštění asynchronní obnovy.
        """
        setting = self.create_without_signal("news_feed_base_url", "https://arup-cas.github.io/aiscr-news/feed/custom")
        with self.captureOnCommitCallbacks(execute=True):
            setting.delete()

        dispatch.assert_called_once_with(languages=["cs", "en"])

    @patch("core.news_feed_scheduler.reconcile_news_feed_schedule")
    @patch("cron.tasks.load_news_feed.delay")
    def test_ttl_change_reconciles_schedule_and_dispatches(self, dispatch, reconcile):
        """Ověří aktualizaci plánovače a spuštění obnovy po změně TTL.

        :param dispatch: Náhrada pro spuštění asynchronní obnovy.
        :param reconcile: Náhrada pro aktualizaci plánovače.
        """
        setting = self.create_without_signal("news_feed_cache_ttl", "3600")
        with self.captureOnCommitCallbacks(execute=True):
            setting.value = "600"
            setting.save()

        reconcile.assert_called_once_with()
        dispatch.assert_called_once_with(languages=["cs", "en"])
