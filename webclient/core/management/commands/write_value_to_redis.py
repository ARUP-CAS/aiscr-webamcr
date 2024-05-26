import logging
import random
import string

from django.core.management.base import BaseCommand

from cron.tasks import write_value_to_redis

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("key", type=str)
        parser.add_argument("value", type=str)

    def handle(self, *args, **kwargs):
        logger.debug("core.views.update_snapshot_fields.start")
        characters = string.ascii_letters + string.digits
        key = kwargs["key"]
        value = kwargs["value"]
        write_value_to_redis.apply_async([key, value])
        logger.debug("core.views.update_snapshot_fields.end", extra={"key": key, "value": value})
