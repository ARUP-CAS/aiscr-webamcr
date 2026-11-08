"""Seed login news-feed settings once for each database."""

import json
import warnings

from django.db import migrations
from django.utils import timezone


_GROUP = "news_feed"
_MIN_CACHE_TTL = 600
_DEFAULTS = {
    "news_feed_block_height": 300,
    "news_feed_base_url": "https://arup-cas.github.io/aiscr-news/feed/amcr",
    "news_feed_languages": ["cs", "en"],
    "news_feed_cache_ttl": 3600,
    "news_feed_cache_key_prefix": "news_feed",
    "news_feed_timeout": 10.0,
    "news_feed_warning_rate_limit": 3600,
}
_PERIODIC_TASK_NAME = "load-news-feed"
_PERIODIC_TASK_PATH = "cron.tasks.load_news_feed"


def seed_news_feed_settings(apps, schema_editor):
    """Create missing settings and the initial database-backed Beat schedule."""
    CustomAdminSettings = apps.get_model("core", "CustomAdminSettings")
    db_alias = schema_editor.connection.alias
    manager = CustomAdminSettings.objects.using(db_alias)

    for item_id, default in _DEFAULTS.items():
        value = json.dumps(default) if isinstance(default, list) else str(default)
        if not manager.filter(item_group=_GROUP, item_id=item_id).exists():
            manager.create(item_group=_GROUP, item_id=item_id, value=value)

    existing_urls = manager.filter(item_group=_GROUP, item_id="news_feed_base_url").values_list(
        "value", flat=True
    )
    if any(value.rstrip("/") != _DEFAULTS["news_feed_base_url"] for value in existing_urls):
        warnings.warn(
            "An existing login news-feed URL differs from the new default; it was preserved. "
            "Review it in CustomAdminSettings.",
            RuntimeWarning,
            stacklevel=2,
        )

    ttl_values = list(
        manager.filter(item_group=_GROUP, item_id="news_feed_cache_ttl").values_list(
            "value", flat=True
        )
    )
    try:
        ttl = int(ttl_values[0]) if len(ttl_values) == 1 else _DEFAULTS["news_feed_cache_ttl"]
        if ttl < _MIN_CACHE_TTL:
            ttl = _DEFAULTS["news_feed_cache_ttl"]
    except (TypeError, ValueError):
        ttl = _DEFAULTS["news_feed_cache_ttl"]

    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTasks = apps.get_model("django_celery_beat", "PeriodicTasks")
    interval_seconds = max(540, ttl - 60)
    interval = (
        IntervalSchedule.objects.using(db_alias)
        .filter(every=interval_seconds, period="seconds")
        .order_by("pk")
        .first()
    )
    if interval is None:
        interval = IntervalSchedule.objects.using(db_alias).create(every=interval_seconds, period="seconds")
    PeriodicTask.objects.using(db_alias).update_or_create(
        name=_PERIODIC_TASK_NAME,
        defaults={
            "task": _PERIODIC_TASK_PATH,
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
    PeriodicTasks.objects.using(db_alias).update_or_create(
        ident=1, defaults={"last_update": timezone.now()}
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0034_odstavkasystemu_texts"),
        ("django_celery_beat", "0019_alter_periodictasks_options"),
    ]

    operations = [migrations.RunPython(seed_news_feed_settings, migrations.RunPython.noop)]
