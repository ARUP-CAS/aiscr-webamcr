import logging

from cron.tasks import write_value_to_redis
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro zápis hodnoty do Redis.

    Tento příkaz předá klíč a hodnotu do sdíleného cron tasku, který
    provede zápis do Redis (asynchronně s nízkou prioritou).

    Parametry:
        - key: Redis klíč
        - value: Hodnota, která se pod klíčem uloží

    Příklady použití::

        python manage.py write_value_to_redis foo bar
    """

    help = _("core.management.commands.write_value_to_redis.Command.help")

    def add_arguments(self, parser):
        """Zpracuje volání ``Command.add_arguments`` v rámci modulu ``webclient.core.management.commands.write_value_to_redis``."""
        parser.add_argument(
            "key",
            type=str,
            help=_("core.management.commands.write_value_to_redis.Command.add_arguments.key_help"),
        )
        parser.add_argument(
            "value",
            type=str,
            help=_("core.management.commands.write_value_to_redis.Command.add_arguments.value_help"),
        )

    def handle(self, *args, **kwargs):
        """Provádí funkci ``Command.handle`` v rámci modulu ``webclient.core.management.commands.write_value_to_redis``."""
        logger.debug("core.management.commands.write_value_to_redis.start")
        key = kwargs["key"]
        value = kwargs["value"]
        write_value_to_redis.apply_async([key, value], priority=0)
        logger.debug("core.management.commands.write_value_to_redis.end", extra={"key": key, "value": value})
