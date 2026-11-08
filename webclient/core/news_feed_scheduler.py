"""Reconciliation helpers for the database-backed login news-feed schedule."""

from core.news_feed_config import NewsFeedConfig, get_news_feed_config
from core.setting_models import CustomAdminSettings
from django.db import transaction
from django_celery_beat.models import IntervalSchedule, PeriodicTask, PeriodicTasks

NEWS_FEED_PERIODIC_TASK_NAME = "load-news-feed"
NEWS_FEED_TASK_PATH = "cron.tasks.load_news_feed"


def reconcile_news_feed_schedule(config: NewsFeedConfig | None = None) -> PeriodicTask:
    """Nastaví interval obnovy zpráv a upozorní databázový plánovač.

    :param config: Konfigurace intervalu; pokud chybí, načte se aktuální.
    :return: Vytvořená nebo aktualizovaná periodická úloha.
    """
    with transaction.atomic():
        if config is None:
            # Serialize concurrent admin callbacks on the current TTL row and
            # read its committed value while holding the lock. This prevents an
            # older callback from overwriting a newer interval.
            CustomAdminSettings.objects.select_for_update().filter(
                item_group="news_feed", item_id="news_feed_cache_ttl"
            ).order_by("pk").first()
            config = get_news_feed_config(force_refresh=True)

        interval_seconds = max(540, config.cache_ttl - 60)
        intervals = IntervalSchedule.objects.filter(
            every=interval_seconds,
            period=IntervalSchedule.SECONDS,
        ).order_by("pk")
        interval = intervals.first()
        if interval is None:
            interval = IntervalSchedule.objects.create(
                every=interval_seconds,
                period=IntervalSchedule.SECONDS,
            )

        task, _created = PeriodicTask.objects.update_or_create(
            name=NEWS_FEED_PERIODIC_TASK_NAME,
            defaults={
                "task": NEWS_FEED_TASK_PATH,
                "interval": interval,
                "crontab": None,
                "solar": None,
                "clocked": None,
                "args": "[]",
                "kwargs": "{}",
                "enabled": True,
                "one_off": False,
            },
        )
        PeriodicTasks.update_changed()
        return task
