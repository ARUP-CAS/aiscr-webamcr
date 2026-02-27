import logging

from core.management.commands.utils.file_storage import save_single_file_from_storage_impl
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro uložení více souborů ze storage.

    Tento příkaz zpracuje dávku souborů z lokálního úložiště.
    Pro každý soubor provede kontroly (MIME type, antivirus) a uloží jej
    do Fedora repozitáře včetně aktualizace metadat v databázi.

    Argumenty:
        - storage_path: Cesta k adresáři obsahujícímu soubory (každý soubor musí mít název rovný PK záznamu v DB včetně přípony, např. 123.jpg)

    Parametry:
        - --pks: Seznam primárních klíčů souborů (odděleno mezerami)
        - --range: Rozsah primárních klíčů ve formátu "start end"
        - --save-thumbs: Generovat náhledy pro obrazové soubory
        - --disable-antivirus: Přeskočit antivirovou kontrolu

    Poznámka:
        - Musí být zadán buď --pks nebo --range, ne oba současně

    Příklady použití:

        Hostitelský adresář ``/home/migrace`` je v Docker YAML namapovaný na ``/vol/data-migrace``,
        proto se uvnitř kontejneru používá cesta ``/vol/data-migrace``::

            python manage.py save_files_from_storage /vol/data-migrace/files --pks 1 2 3
            python manage.py save_files_from_storage /vol/data-migrace/files --range 100 200
            python manage.py save_files_from_storage /vol/data-migrace/files --pks 10 20 --save-thumbs
    """

    help = _("core.management.commands.save_files_from_storage.Command.help")

    def add_arguments(self, parser):
        """Zpracuje volání ``Command.add_arguments`` v rámci modulu ``webclient.core.management.commands.save_files_from_storage``."""
        parser.add_argument(
            "storage_path",
            type=str,
            help=_("core.management.commands.save_files_from_storage.Command.add_arguments.storage_path_help"),
        )
        parser.add_argument(
            "--pks",
            nargs="+",
            type=int,
            help=_("core.management.commands.save_files_from_storage.Command.add_arguments.pks_help"),
        )
        parser.add_argument(
            "--range",
            nargs=2,
            type=int,
            metavar=("START", "END"),
            help=_("core.management.commands.save_files_from_storage.Command.add_arguments.range_help"),
        )
        parser.add_argument(
            "--save-thumbs",
            action="store_true",
            help=_("core.management.commands.save_files_from_storage.Command.add_arguments.save_thumbs_help"),
        )
        parser.add_argument(
            "--disable-antivirus",
            action="store_true",
            help=_("core.management.commands.save_files_from_storage.Command.add_arguments.disable_antivirus_help"),
        )

    def handle(self, *args, **options):
        """Provádí funkci ``Command.handle`` v rámci modulu ``webclient.core.management.commands.save_files_from_storage``."""
        storage_path = options["storage_path"]
        pks = options.get("pks")
        pk_range = options.get("range")
        save_thumbs = options["save_thumbs"]
        disable_antivirus = options["disable_antivirus"]

        # Ověří, že je zadáno buď `pks`, nebo rozsah, ale ne oboje.
        if pks and pk_range:
            raise CommandError(_("core.management.commands.save_files_from_storage.pks_and_range_error"))
        if not pks and not pk_range:
            raise CommandError(_("core.management.commands.save_files_from_storage.missing_params_error"))

        # Prepare records list
        if pks:
            records = pks
            logger.debug(
                "core.management.commands.save_files_from_storage.start",
                extra={"count": len(records), "storage_path": storage_path, "type": "pks"},
            )
        else:
            records = range(pk_range[0], pk_range[1] + 1)
            logger.debug(
                "core.management.commands.save_files_from_storage.start",
                extra={"count": len(records), "storage_path": storage_path, "type": "range"},
            )

        # Process files
        from core.models import Soubor

        queryset = Soubor.objects.filter(pk__in=records).order_by("pk")
        total = queryset.count()

        self.stdout.write(_("core.management.commands.save_files_from_storage.processing_total") + " " + str(total))

        for index, item in enumerate(queryset, 1):
            try:
                save_single_file_from_storage_impl(item, storage_path, save_thumbs, disable_antivirus)
                if index % 10 == 0 or index == total:
                    self.stdout.write(
                        _("core.management.commands.save_files_from_storage.processed")
                        + " "
                        + str(index)
                        + "/"
                        + str(total)
                    )
            except Exception as e:
                logger.error(
                    "core.management.commands.save_files_from_storage.error",
                    extra={"pk": item.pk, "error": str(e)},
                )
                self.stdout.write(
                    self.style.ERROR(
                        _("core.management.commands.save_files_from_storage.error_prefix")
                        + " "
                        + str(item.pk)
                        + ": "
                        + str(e)
                    )
                )

        logger.debug(
            "core.management.commands.save_files_from_storage.end",
            extra={"count": total, "storage_path": storage_path},
        )
        self.stdout.write(
            self.style.SUCCESS(_("core.management.commands.save_files_from_storage.finished") + " " + str(total))
        )
