import logging

from core.models import Soubor
from core.news_feed_config import (
    FETCH_SETTING_IDS,
    NEWS_FEED_BLOCK_HEIGHT_CACHE_KEY,
    NEWS_FEED_GROUP,
    get_news_feed_config,
    invalidate_news_feed_config_cache,
)
from core.repository_connector import FedoraTransaction
from core.setting_models import CustomAdminSettings
from django.core.cache import caches
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=CustomAdminSettings, weak=False)
def news_feed_settings_capture_previous_identity(sender, instance, raw=False, **kwargs):
    """Zachová původní identitu nastavení před jeho uložením.

    :param sender: Model, který vyslal signál.
    :param instance: Ukládaná instance nastavení.
    :param raw: Příznak načítání surových dat, při kterém se změna ignoruje.
    :param kwargs: Další argumenty signálu.
    """
    instance._news_feed_previous = None
    if raw or not instance.pk:
        return
    instance._news_feed_previous = (
        CustomAdminSettings.objects.filter(pk=instance.pk).values("item_group", "item_id", "value").first()
    )


def _apply_news_feed_setting_change(previous, current):
    """Apply cache and task changes after a news-feed setting transaction commits."""
    old_group, old_id, old_value = previous if previous else (None, None, None)
    new_group, new_id, new_value = current if current else (None, None, None)
    old_relevant = old_group == NEWS_FEED_GROUP
    new_relevant = new_group == NEWS_FEED_GROUP
    if not (old_relevant or new_relevant):
        return

    invalidate_news_feed_config_cache()
    caches["default"].delete(NEWS_FEED_BLOCK_HEIGHT_CACHE_KEY)
    changed_ids = set()
    if old_relevant and (not new_relevant or old_id != new_id or old_value != new_value):
        changed_ids.add(old_id)
    if new_relevant and (not old_relevant or old_id != new_id or old_value != new_value):
        changed_ids.add(new_id)

    try:
        config = get_news_feed_config(force_refresh=True)
    except Exception:
        logger.exception("Could not read news-feed configuration after a committed setting change.")
        return

    if "news_feed_cache_ttl" in changed_ids:
        try:
            from core.news_feed_scheduler import reconcile_news_feed_schedule

            reconcile_news_feed_schedule()
        except Exception:
            logger.exception("Could not reconcile the news-feed periodic schedule after a TTL change.")

    if not changed_ids.intersection(FETCH_SETTING_IDS):
        return

    for language in config.languages:
        fresh_key, _last_good_key = config.cache_keys(language)
        caches["default"].delete(fresh_key)

    try:
        from cron.tasks import load_news_feed

        load_news_feed.delay(languages=list(config.languages))
    except Exception:
        logger.exception("Could not dispatch the asynchronous news-feed refresh after a committed setting change.")


@receiver(post_save, sender=CustomAdminSettings, weak=False)
def news_feed_settings_saved(sender, instance, raw=False, **kwargs):
    """Naplánuje reakci na uložené nastavení zpráv po potvrzení transakce.

    :param sender: Model, který vyslal signál.
    :param instance: Uložená instance nastavení.
    :param raw: Příznak načítání surových dat, při kterém se změna ignoruje.
    :param kwargs: Další argumenty signálu.
    """
    if raw:
        return
    previous = instance._news_feed_previous
    previous_identity = (previous["item_group"], previous["item_id"], previous["value"]) if previous else None
    current = (instance.item_group, instance.item_id, instance.value)
    if not (previous_identity and previous_identity[0] == NEWS_FEED_GROUP) and current[0] != NEWS_FEED_GROUP:
        return
    transaction.on_commit(lambda: _apply_news_feed_setting_change(previous_identity, current))


@receiver(post_delete, sender=CustomAdminSettings, weak=False)
def news_feed_settings_deleted(sender, instance, **kwargs):
    """Naplánuje reakci na smazání nastavení zpráv po potvrzení transakce.

    :param sender: Model, který vyslal signál.
    :param instance: Smazaná instance nastavení.
    :param kwargs: Další argumenty signálu.
    """
    if instance.item_group != NEWS_FEED_GROUP:
        return
    previous = (instance.item_group, instance.item_id, instance.value)
    transaction.on_commit(lambda: _apply_news_feed_setting_change(previous, None))


@receiver(pre_save, sender=Soubor, weak=False)
def soubor_get_rozsah(sender, instance, **kwargs):
    """
    Určí počet stran/snímků souboru (PDF, TIF) a uloží jej do ``rozsah``.

    :param sender: Model ``Soubor``, který signál vyslal.
    :param instance: Instancia ``Soubor`` předaná k uložení.
    :param kwargs: Dodatečné argumenty signálu.
    """
    instance.rozsah = instance.calculate_rozsah()


@receiver(post_save, sender=Soubor, weak=False)
def soubor_save_update_record_metadata(sender, instance: Soubor, **kwargs):
    """
    Aktualizuje metadata nadřazeného archeologického záznamu po uložení souboru.

    :param sender: Model ``Soubor``, který signál vyslal.
    :param instance: Instancia ``Soubor`` která byla uložena.
    :param kwargs: Dodatečné argumenty signálu.
    """
    logger.debug(
        "cron.signals.soubor_save_update_record_metadata.start",
        extra={"option": instance.close_active_transaction_when_finished},
    )
    if not instance.suppress_signal:
        fedora_transaction: FedoraTransaction = instance.active_transaction
        if (
            instance.vazba is not None
            and isinstance(instance.vazba.navazany_objekt, ModelWithMetadata)
            and instance.suppress_signal is False
        ):
            instance.vazba.navazany_objekt.save_metadata(
                fedora_transaction, close_transaction=instance.close_active_transaction_when_finished
            )
            logger.debug(
                "cron.signals.soubor_save_update_record_metadata.save_metadata",
                extra={
                    "transaction": getattr(fedora_transaction, "uid", ""),
                    "ident_cely": getattr(instance, "ident_cely", ""),
                },
            )
        elif instance.close_active_transaction_when_finished:
            fedora_transaction.mark_transaction_as_closed()
    logger.debug("cron.signals.soubor_save_update_record_metadata.no_action")


@receiver(pre_delete, sender=Soubor, weak=False)
def soubor_delete_connections(sender, instance: Soubor, **kwargs):
    """
    Odstraní historii záznamu spojené se souborem před jeho fyzickým smazáním.

    :param sender: Model ``Soubor``, který signál vyslal.
    :param instance: Instancia ``Soubor`` určená ke smazání.
    :param kwargs: Dodatečné argumenty signálu.
    """
    logger.debug("cron.signals.soubor_delete_connections.start", extra={"instance": instance.pk})
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
    logger.debug("cron.signals.soubor_delete_connections.end", extra={"instance": instance.pk})


@receiver(post_delete, sender=Soubor, weak=False)
def soubor_delete_update_metadata(sender, instance: Soubor, **kwargs):
    """
    Aktualizuje metadata nadřazeného archeologického záznamu po smazání souboru.

    :param sender: Model ``Soubor``, který signál vyslal.
    :param instance: Instancia ``Soubor`` která byla smazána.
    :param kwargs: Dodatečné argumenty signálu.
    """
    logger.debug("cron.signals.soubor_delete_update_metadata.start", extra={"instance": instance.pk})
    if instance.suppress_signal is True:
        logger.debug("cron.signals.soubor_delete_update_metadata.suppress_signal", extra={"instance": instance.pk})
        return
    if instance.vazba is not None and isinstance(instance.vazba.navazany_objekt, ModelWithMetadata):
        fedora_transaction = instance.active_transaction
        instance.vazba.navazany_objekt.save_metadata(
            fedora_transaction, close_transaction=instance.close_active_transaction_when_finished
        )
        logger.debug(
            "cron.signals.soubor_delete_update_metadata.save_metadata",
            extra={"transaction": transaction, "ident_cely": getattr(instance, "ident_cely", "")},
        )
    logger.debug("cron.signals.soubor_delete_update_metadata.no_action", extra={"instance": instance.pk})
