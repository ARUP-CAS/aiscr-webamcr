import logging

from cron.tasks import update_snapshot_fields
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro spuštění aktualizace snapshot fields.

    Tento příkaz spustí sdílený cron task ``update_snapshot_fields``, který
    provede potřebné přepočty a uložení snapshot hodnot.

    Příklad použití:
        python manage.py update_snapshot_fields
    """

    help = _("core.management.commands.update_snapshot_fields.Command.help")

    def handle(self, *args, **options):
        logger.debug("core.views.update_snapshot_fields.start")
        update_snapshot_fields()
        logger.debug("core.views.update_snapshot_fields.end")
