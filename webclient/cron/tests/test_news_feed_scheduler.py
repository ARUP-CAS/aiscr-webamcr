"""Testy databázového intervalu obnovy novinek v plánovači Celery Beat."""

from core.news_feed_config import NewsFeedConfig
from core.news_feed_scheduler import reconcile_news_feed_schedule
from django.test import TestCase
from django_celery_beat.models import IntervalSchedule, PeriodicTask, PeriodicTasks


class NewsFeedSchedulerTest(TestCase):
    """Ověří sladění intervalu při změně TTL a upozornění databázového plánovače."""

    def config(self, ttl):
        """Sestaví konfiguraci zpráv se zadanou dobou platnosti.

        :param ttl: Doba platnosti zpráv v sekundách.
        :return: Snímek nastavení novinek se zadanou dobou platnosti a ostatními výchozími hodnotami.
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

    def test_disabled_task_options_and_unchanged_schedule_are_preserved(self):
        """Ověří zachování nastavení operátora a vynechání zbytečného zápisu."""
        task = reconcile_news_feed_schedule(self.config(3600))
        task.enabled = False
        task.args = '["cs"]'
        task.queue = "custom"
        task.save()
        task = reconcile_news_feed_schedule(self.config(600))
        self.assertFalse(task.enabled)
        self.assertEqual(task.args, '["cs"]')
        self.assertEqual(task.queue, "custom")
        self.assertEqual(task.interval.every, 540)
        changed = PeriodicTasks.last_change()
        modified = task.date_changed
        reconcile_news_feed_schedule(self.config(600))
        task.refresh_from_db()
        self.assertEqual(task.date_changed, modified)
        self.assertEqual(PeriodicTasks.last_change(), changed)

    def test_custom_crontab_is_preserved(self):
        """Ověří, že vlastní plán crontab nepřepíše interval."""
        from django_celery_beat.models import CrontabSchedule

        task = reconcile_news_feed_schedule(self.config(3600))
        schedule = CrontabSchedule.objects.create(minute="5", hour="*")
        task.interval = None
        task.crontab = schedule
        task.save()
        task = reconcile_news_feed_schedule(self.config(600))
        self.assertEqual(task.crontab_id, schedule.pk)
        self.assertIsNone(task.interval_id)
