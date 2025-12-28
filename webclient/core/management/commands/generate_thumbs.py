import logging

from core.repository_connector import FedoraRepositoryConnector
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro generování náhledů souborů.

    Tento příkaz zpracuje dávku souborů a pro každý soubor zkontroluje,
    zda existují náhledy v Fedora repozitáři. Pokud náhledy neexistují,
    vygeneruje je ze zdrojového souboru.

    Parametry:
        --pks: Seznam primárních klíčů souborů (odděleno mezerami)
        --range: Rozsah primárních klíčů ve formátu "start end"

    Poznámka:
        Musí být zadán buď --pks nebo --range, ne oba současně.
        Náhledy jsou generovány pouze pro obrazové formáty podporované systémem.

    Příklady použití:
        python manage.py generate_thumbs --pks 1 2 3
        python manage.py generate_thumbs --range 100 200
        python manage.py generate_thumbs --range 1 1000
    """

    help = "Generování náhledů pro soubory v Fedora repozitáři"

    def add_arguments(self, parser):
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

    def handle(self, *args, **options):
        pks = options.get("pks")
        pk_range = options.get("range")

        # Validate that either pks or range is provided, but not both
        if pks and pk_range:
            raise CommandError("Nelze použít --pks a --range současně. Zvolte pouze jeden parametr.")
        if not pks and not pk_range:
            raise CommandError("Musí být zadán buď --pks nebo --range.")

        # Prepare records list
        if pks:
            records = pks
            logger.debug(
                "core.management.commands.generate_thumbs.start",
                extra={"count": len(records), "type": "pks"},
            )
        else:
            records = range(pk_range[0], pk_range[1] + 1)
            logger.debug(
                "core.management.commands.generate_thumbs.start",
                extra={"count": len(records), "type": "range"},
            )

        # Process files
        from core.models import Soubor

        queryset = Soubor.objects.filter(pk__in=records).order_by("pk")
        total = queryset.count()

        self.stdout.write(f"Zpracovává se {total} souborů pro generování náhledů...")

        success_count = 0
        error_count = 0

        for index, item in enumerate(queryset, 1):
            try:
                FedoraRepositoryConnector.generate_thumb_for_single_file(item)
                success_count += 1
                if index % 10 == 0 or index == total:
                    self.stdout.write(f"Zpracováno {index}/{total} souborů")
            except Exception as e:
                error_count += 1
                logger.error(
                    "core.management.commands.generate_thumbs.error",
                    extra={"pk": item.pk, "error": str(e)},
                )
                self.stdout.write(self.style.ERROR(f"Chyba při generování náhledu pro soubor PK {item.pk}: {str(e)}"))

        logger.debug(
            "core.management.commands.generate_thumbs.end",
            extra={"count": total, "success": success_count, "errors": error_count},
        )

        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f"Dokončeno s chybami. Úspěšně zpracováno: {success_count}, Chyby: {error_count}")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Dokončeno. Úspěšně vygenerovány náhledy pro {success_count} souborů")
            )
