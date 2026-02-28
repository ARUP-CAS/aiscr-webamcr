import logging

from core.management.commands.utils.file_storage import save_single_file_from_storage_impl
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro uložení jednotlivého souboru ze storage.

    Tento příkaz načte soubor z lokálního úložiště podle jeho primárního klíče,
    provede kontroly (MIME type, antivirus), a uloží jej do Fedora repozitáře
    včetně aktualizace metadat v databázi.

    Argumenty:
    - pk: Primární klíč záznamu souboru v databázi
    - storage_path: Cesta k adresáři obsahujícímu soubory

    Parametry:
    - --save-thumbs: Generovat náhledy pro obrazové soubory
    - --disable-antivirus: Přeskočit antivirovou kontrolu

    Příklady použití:

    Hostitelský adresář ``/home/migrace`` je v Docker YAML namapovaný na ``/vol/data-migrace``,
    proto se uvnitř kontejneru používá cesta ``/vol/data-migrace``::

    python manage.py save_single_file_from_storage 123 /vol/data-migrace/files
    python manage.py save_single_file_from_storage 456 /vol/data-migrace/storage --save-thumbs
    """

    help = _("core.management.commands.save_single_file_from_storage.Command.help")

    def add_arguments(self, parser):
        """
        Provádí operaci add arguments.

        :param parser: Vstupní hodnota ``parser`` pro danou operaci.
        """
        parser.add_argument(
            "pk",
            type=int,
            help=_("core.management.commands.save_single_file_from_storage.Command.add_arguments.pk_help"),
        )
        parser.add_argument(
            "storage_path",
            type=str,
            help=_("core.management.commands.save_single_file_from_storage.Command.add_arguments.storage_path_help"),
        )
        parser.add_argument(
            "--save-thumbs",
            action="store_true",
            help=_("core.management.commands.save_single_file_from_storage.Command.add_arguments.save_thumbs_help"),
        )
        parser.add_argument(
            "--disable-antivirus",
            action="store_true",
            help=_(
                "core.management.commands.save_single_file_from_storage.Command.add_arguments.disable_antivirus_help"
            ),
        )

    def handle(self, *args, **options):
        """
        Zpracuje hodnotu. v aplikaci.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param options: Dodatečné pojmenované argumenty předané voláním.
        """
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
        self.stdout.write(
            self.style.SUCCESS(
                _("core.management.commands.save_single_file_from_storage.finished_success") + " " + str(pk)
            )
        )
