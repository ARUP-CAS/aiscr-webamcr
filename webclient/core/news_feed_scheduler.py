"""Reconciliation helpers for the database-backed login news-feed schedule."""

import logging

from core.news_feed_config import NewsFeedConfig, get_news_feed_config
from core.setting_models import CustomAdminSettings
from django.db import transaction
from django_celery_beat.models import IntervalSchedule, PeriodicTask

logger = logging.getLogger(__name__)

NEWS_FEED_PERIODIC_TASK_NAME = "load-news-feed"
NEWS_FEED_TASK_PATH = "cron.tasks.load_news_feed"


def reconcile_news_feed_schedule(config: NewsFeedConfig | None = None) -> PeriodicTask:
    """Sladí interval úlohy s TTL a zachová ostatní nastavení operátora.

    Vlastní neintervalový plán, cizí úlohu a neplatný plán ponechá beze změny.
    Při shodném intervalu úlohu neukládá a neupozorňuje plánovač.

    :param config: Snímek konfigurace pro izolované testy. Produkční volání jej
        nepředává, aby se aktuální hodnota načetla pod zámkem databázového řádku.
    :return: Vytvořená, aktualizovaná nebo beze změny zachovaná periodická úloha.
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
        task = PeriodicTask.objects.select_for_update().filter(name=NEWS_FEED_PERIODIC_TASK_NAME).first()
        if task is not None:
            if task.task != NEWS_FEED_TASK_PATH:
                logger.warning("News-feed schedule name is owned by another task; preserving it.")
                return task
            schedule_ids = (task.interval_id, task.crontab_id, task.solar_id, task.clocked_id)
            if sum(value is not None for value in schedule_ids) != 1:
                logger.warning("News-feed task has an invalid schedule selection; preserving it.")
                return task
            if task.interval_id is None:
                return task
            if task.interval.every == interval_seconds and task.interval.period == IntervalSchedule.SECONDS:
                return task

        interval = (
            IntervalSchedule.objects.filter(every=interval_seconds, period=IntervalSchedule.SECONDS)
            .order_by("pk")
            .first()
        )
        if interval is None:
            interval = IntervalSchedule.objects.create(every=interval_seconds, period=IntervalSchedule.SECONDS)

        if task is None:
            task, _created = PeriodicTask.objects.get_or_create(
                name=NEWS_FEED_PERIODIC_TASK_NAME,
                defaults={"task": NEWS_FEED_TASK_PATH, "interval": interval, "enabled": True},
            )
            return task
        task.interval = interval
        task.save(update_fields=["interval", "date_changed"])
        return task
