"""Tests for the database-backed news-feed Beat interval."""

from core.news_feed_config import NewsFeedConfig
from core.news_feed_scheduler import reconcile_news_feed_schedule
from django.test import TestCase
from django_celery_beat.models import IntervalSchedule, PeriodicTask, PeriodicTasks


class NewsFeedSchedulerTest(TestCase):
    """Ensures TTL changes reconcile the task row and wake DatabaseScheduler."""

    def config(self, ttl):
        """Sestaví konfiguraci zpráv se zadanou dobou platnosti.

        :param ttl: Doba platnosti zpráv v sekundách.
        """
        return NewsFeedConfig(
            block_height=300,
            base_url="https://arup-cas.github.io/aiscr-news/feed/amcr",
            languages=("cs", "en"),
            cache_ttl=ttl,
            cache_key_prefix="news_feed",
            timeout=10.0,
            warning_rate_limit=3600,
        )

    def test_ttl_reconciles_interval_and_scheduler_timestamp(self):
        """Ověří aktualizaci intervalu úlohy a oznámení plánovači."""
        reconcile_news_feed_schedule(self.config(600))
        task = PeriodicTask.objects.get(name="load-news-feed")
        self.assertEqual(task.interval.every, 540)
        self.assertEqual(task.interval.period, IntervalSchedule.SECONDS)
        self.assertIsNotNone(PeriodicTasks.last_change())

        reconcile_news_feed_schedule(self.config(660))
        task.refresh_from_db()
        self.assertEqual(task.interval.every, 600)
        self.assertEqual(PeriodicTask.objects.filter(name="load-news-feed").count(), 1)
