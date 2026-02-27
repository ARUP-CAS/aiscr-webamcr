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
        """Funkce `Command.handle` v modulu `webclient.core.management.commands.update_snapshot_fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param args: Vstupní hodnota používaná při zpracování.
        :param options: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        logger.debug("core.management.commands.update_snapshot_fields.start")
        update_snapshot_fields()
        logger.debug("core.management.commands.update_snapshot_fields.end")
