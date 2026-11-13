"""Login-view tests for cached feed content and live height configuration."""

from unittest.mock import patch

from core.news_feed_config import get_news_feed_cache_keys, get_news_feed_config, invalidate_news_feed_config_cache
from core.setting_models import CustomAdminSettings
from django.core.cache import caches
from django.test import RequestFactory, TestCase, override_settings
from uzivatel.views import UserLoginView


@override_settings(
    CACHES={
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "news-feed-login-tests"}
    }
)
class NewsFeedLoginViewTest(TestCase):
    """Ensures login uses cache and sees committed block-height changes."""

    def setUp(self):
        """Připraví izolovaný stav pro test nastavení zpráv."""
        caches["default"].clear()
        CustomAdminSettings.objects.filter(item_group="news_feed").delete()
        CustomAdminSettings.objects.bulk_create(
            [CustomAdminSettings(item_group="news_feed", item_id="news_feed_block_height", value="420")]
        )

    def render_context(self):
        """Sestaví kontext přihlašovací stránky pro český jazyk."""
        request = RequestFactory().get("/login/")
        request.LANGUAGE_CODE = "cs"
        view = UserLoginView()
        view.setup(request)
        with patch("uzivatel.views.LoginView.get_context_data", return_value={}):
            return view.get_context_data()

    @patch("cron.tasks.requests.get")
    def test_login_reads_cached_feed_and_current_height_without_http(self, get):
        """Ověří čtení zpráv z cache a aktuální výšky bez HTTP požadavku.

        :param get: Náhrada HTTP požadavku na zdroj zpráv.
        """
        config = get_news_feed_config(force_refresh=True)
        fresh_key, _last_good_key = get_news_feed_cache_keys("cs", config)
        feed = ["cached item"]
        caches["default"].set(fresh_key, feed, 3600)

        context = self.render_context()

        self.assertEqual(context["news_feed"], feed)
        self.assertEqual(context["news_feed_block_height"], 420)
        get.assert_not_called()

        CustomAdminSettings.objects.filter(item_id="news_feed_block_height").update(value="480")
        invalidate_news_feed_config_cache()
        self.assertEqual(self.render_context()["news_feed_block_height"], 480)
        get.assert_not_called()

    def test_previous_source_last_good_content_is_not_used_after_source_change(self):
        """Ověří, že po změně zdroje nejsou použity jeho staré zprávy."""
        old_source = "https://arup-cas.github.io/aiscr-news/feed/old"
        new_source = "https://arup-cas.github.io/aiscr-news/feed/new"
        CustomAdminSettings.objects.bulk_create(
            [CustomAdminSettings(item_group="news_feed", item_id="news_feed_base_url", value=old_source)]
        )
        invalidate_news_feed_config_cache()
        old_config = get_news_feed_config(force_refresh=True)
        _old_fresh_key, old_last_good_key = get_news_feed_cache_keys("cs", old_config)
        caches["default"].set(old_last_good_key, ["old source content"], None)

        CustomAdminSettings.objects.filter(item_id="news_feed_base_url").update(value=new_source)
        invalidate_news_feed_config_cache()

        self.assertEqual(self.render_context()["news_feed"], [])

    def test_same_source_last_good_copy_is_used_when_fresh_copy_is_missing(self):
        """Ověří použití posledních platných zpráv při chybějící čerstvé kopii."""
        config = get_news_feed_config(force_refresh=True)
        _fresh_key, last_good_key = get_news_feed_cache_keys("cs", config)
        caches["default"].set(last_good_key, ["last-good item"], None)

        self.assertEqual(self.render_context()["news_feed"], ["last-good item"])
