import logging

from core.management.commands.utils.file_storage import save_single_file_from_storage_impl
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro uložení jednotlivého souboru ze storage.

    Tento příkaz načte soubor z lokálního úložiště podle jeho primárního klíče,
    provede kontroly (MIME type, antivirus), a uloží jej do Fedora repozitáře
    včetně aktualizace metadat v databázi.

    Argumenty:
        pk: Primární klíč záznamu souboru v databázi
        storage_path: Cesta k adresáři obsahujícímu soubory

    Parametry:
        --save-thumbs: Generovat náhledy pro obrazové soubory
        --disable-antivirus: Přeskočit antivirovou kontrolu

    Příklady použití:
        python manage.py save_single_file_from_storage 123 /tmp/files
        python manage.py save_single_file_from_storage 456 /var/storage --save-thumbs
    """

    help = "Uložení jednotlivého souboru ze storage do Fedora repozitáře"

    def add_arguments(self, parser):
        parser.add_argument(
            "pk",
            type=int,
            help="Primární klíč záznamu souboru",
        )
        parser.add_argument(
            "storage_path",
            type=str,
            help="Cesta k adresáři se soubory",
        )
        parser.add_argument(
            "--save-thumbs",
            action="store_true",
            help="Generovat náhledy",
        )
        parser.add_argument(
            "--disable-antivirus",
            action="store_true",
            help="Přeskočit antivirovou kontrolu",
        )

    def handle(self, *args, **options):
        pk = options["pk"]
        storage_path = options["storage_path"]
        save_thumbs = options["save_thumbs"]
        disable_antivirus = options["disable_antivirus"]

        logger.debug(
            "core.management.commands.save_single_file_from_storage.start",
            extra={"pk": pk, "storage_path": storage_path},
        )

        save_single_file_from_storage_impl(pk, storage_path, save_thumbs, disable_antivirus)

        logger.debug(
            "core.management.commands.save_single_file_from_storage.end",
            extra={"pk": pk, "storage_path": storage_path},
        )
        self.stdout.write(self.style.SUCCESS(f"Soubor s PK {pk} byl úspěšně uložen"))
