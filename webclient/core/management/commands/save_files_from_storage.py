import logging

from core.management.commands.utils.file_storage import save_single_file_from_storage_impl
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro uložení více souborů ze storage.

    Tento příkaz zpracuje dávku souborů z lokálního úložiště.
    Pro každý soubor provede kontroly (MIME type, antivirus) a uloží jej
    do Fedora repozitáře včetně aktualizace metadat v databázi.

    Argumenty:
        storage_path: Cesta k adresáři obsahujícímu soubory

    Parametry:
        --pks: Seznam primárních klíčů souborů (odděleno mezerami)
        --range: Rozsah primárních klíčů ve formátu "start end"
        --save-thumbs: Generovat náhledy pro obrazové soubory
        --disable-antivirus: Přeskočit antivirovou kontrolu

    Poznámka:
        Musí být zadán buď --pks nebo --range, ne oba současně.

    Příklady použití:
        python manage.py save_files_from_storage /tmp/files --pks 1 2 3
        python manage.py save_files_from_storage /tmp/files --range 100 200
        python manage.py save_files_from_storage /tmp/files --pks 10 20 --save-thumbs
    """

    help = "Uložení více souborů ze storage do Fedora repozitáře"

    def add_arguments(self, parser):
        parser.add_argument(
            "storage_path",
            type=str,
            help="Cesta k adresáři se soubory",
        )
        parser.add_argument(
            "--pks",
            nargs="+",
            type=int,
            help="Seznam primárních klíčů souborů",
        )
        parser.add_argument(
            "--range",
            nargs=2,
            type=int,
            metavar=("START", "END"),
            help="Rozsah primárních klíčů (start end)",
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
        storage_path = options["storage_path"]
        pks = options.get("pks")
        pk_range = options.get("range")
        save_thumbs = options["save_thumbs"]
        disable_antivirus = options["disable_antivirus"]

        # Validate that either pks or range is provided, but not both
        if pks and pk_range:
            raise CommandError("Nelze použít --pks a --range současně. Zvolte pouze jeden parametr.")
        if not pks and not pk_range:
            raise CommandError("Musí být zadán buď --pks nebo --range.")

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

        self.stdout.write(f"Zpracovává se {total} souborů...")

        for index, item in enumerate(queryset, 1):
            try:
                save_single_file_from_storage_impl(item, storage_path, save_thumbs, disable_antivirus)
                if index % 10 == 0 or index == total:
                    self.stdout.write(f"Zpracováno {index}/{total} souborů")
            except Exception as e:
                logger.error(
                    "core.management.commands.save_files_from_storage.error",
                    extra={"pk": item.pk, "error": str(e)},
                )
                self.stdout.write(self.style.ERROR(f"Chyba při zpracování souboru PK {item.pk}: {str(e)}"))

        logger.debug(
            "core.management.commands.save_files_from_storage.end",
            extra={"count": total, "storage_path": storage_path},
        )
        self.stdout.write(self.style.SUCCESS(f"Dokončeno. Zpracováno {total} souborů"))
