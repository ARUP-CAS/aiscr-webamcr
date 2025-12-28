import logging

import pandas as pd
from core.repository_connector import FedoraRepositoryConnector
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro vytvoření chybějících náhledů ze CSV souboru.

    Tento příkaz načte CSV soubor obsahující seznam souborů (cesty v Fedora repozitáři)
    a pro každý záznam zkontroluje a případně vygeneruje chybějící náhledy.

    CSV soubor musí obsahovat sloupec "record" s cestami k souborům.

    Argumenty:
        csv_file: Cesta k CSV souboru se seznamem souborů

    Formát CSV souboru:
        record
        /path/to/file1
        /path/to/file2
        /path/to/file3

    Příklady použití:
        python manage.py create_missing_thumbnail /tmp/missing_thumbs.csv
        python manage.py create_missing_thumbnail /var/data/files.csv
    """

    help = "Vytvoření chybějících náhledů ze CSV souboru"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Cesta k CSV souboru se seznamem souborů (sloupec 'record')",
        )

    def handle(self, *args, **options):
        csv_file = options["csv_file"]

        logger.debug(
            "core.management.commands.create_missing_thumbnail.start",
            extra={"csv_file": csv_file},
        )

        from core.models import Soubor

        try:
            sheet = pd.read_csv(csv_file, sep=",")
        except Exception as e:
            logger.error(
                "core.management.commands.create_missing_thumbnail.csv_read_error",
                extra={"csv_file": csv_file, "error": str(e)},
            )
            self.stdout.write(self.style.ERROR(f"Chyba při čtení CSV souboru: {str(e)}"))
            return

        total = len(sheet)
        success_count = 0
        error_count = 0

        self.stdout.write(f"Zpracovává se {total} záznamů z CSV souboru...")

        for index, row in sheet.iterrows():
            # Show progress
            if index % max(total // 100, 1) == 0:
                percentage = round(index / total * 100)
                self.stdout.write(f"\rProgress: {percentage}%", ending="")

            try:
                soubor = Soubor.objects.get(path=row["record"])
                FedoraRepositoryConnector.generate_thumb_for_single_file(soubor.pk)
                success_count += 1
            except Soubor.DoesNotExist:
                error_count += 1
                error_msg = f"Soubor s cestou '{row['record']}' nebyl nalezen v databázi"
                logger.warning(
                    "core.management.commands.create_missing_thumbnail.file_not_found",
                    extra={"path": row["record"]},
                )
                self.stdout.write(self.style.WARNING(f"\n{error_msg}"))
            except Exception as err:
                error_count += 1
                logger.error(
                    "core.management.commands.create_missing_thumbnail.error",
                    extra={"path": row["record"], "error": str(err)},
                )
                self.stdout.write(self.style.ERROR(f"\nChyba: {row['record']} - {err}"))

        # Final newline after progress indicator
        self.stdout.write("")

        logger.debug(
            "core.management.commands.create_missing_thumbnail.end",
            extra={"total": total, "success": success_count, "errors": error_count},
        )

        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Dokončeno s chybami. Úspěšně zpracováno: {success_count}/{total}, Chyby: {error_count}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Dokončeno. Úspěšně vygenerovány náhledy pro {success_count}/{total} souborů")
            )
