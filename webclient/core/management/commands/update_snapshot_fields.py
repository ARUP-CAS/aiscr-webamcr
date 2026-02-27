import logging

from cron.tasks import update_snapshot_fields
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro spuštění aktualizace snapshot fields.

    Tento příkaz spustí sdílený cron task ``update_snapshot_fields``, který
    provede potřebné přepočty a uložení snapshot hodnot do databáze.

    Poznámka:
        - Příkaz nespouští aktualizaci synchronně, ale předává úlohu do asynchronního cron systému
        - Snapshot fields zahrnují předpočítané hodnoty pro optimalizaci výkonu

    Příklady použití::

        python manage.py update_snapshot_fields
    """

    help = _("core.management.commands.update_snapshot_fields.Command.help")

    def handle(self, *args, **options):
        """Zpracuje hodnotu.
        
        :param args: Dodatečné poziční argumenty předané voláním.
        :param options: Dodatečné pojmenované argumenty předané voláním.
        :return: Vrací výsledek provedené operace."""
        logger.debug("core.management.commands.update_snapshot_fields.start")
        update_snapshot_fields()
        logger.debug("core.management.commands.update_snapshot_fields.end")
