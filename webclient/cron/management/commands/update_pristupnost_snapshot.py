import logging

from django.core.management.base import BaseCommand
from django.db import transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro aktualizaci snímku přístupnosti projektů.

    Tento příkaz prochází všechny projekty a aktualizuje jejich pole pristupnost_snapshot
    pomocí metody set_pristupnost(). Projekty jsou zpracovávány v dávkách pro optimalizaci
    výkonu a zamezení přílišnému zatížení databáze.

    Parametry:
        --batch-size: Velikost dávky pro zpracování (výchozí: 100)

    Poznámka:
        Pro projekty je dočasně potlačen signál (suppress_signal=True) aby nedošlo
        k nežádoucím vedlejším efektům během hromadné aktualizace.

    Příklady použití:
        python manage.py update_pristupnost_snapshot
        python manage.py update_pristupnost_snapshot --batch-size 200
        python manage.py update_pristupnost_snapshot --batch-size 50
    """

    help = "Aktualizace snímku přístupnosti pro všechny projekty"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Velikost dávky pro zpracování (výchozí: 100)",
        )

    def handle(self, *args, **options):
        from projekt.models import Projekt

        batch_size = options["batch_size"]

        logger.debug(
            "cron.management.commands.update_pristupnost_snapshot.start",
            extra={"batch_size": batch_size},
        )

        projekt_count = Projekt.objects.all().count()
        batch_count = projekt_count // batch_size + 1

        self.stdout.write(f"Celkový počet projektů: {projekt_count}")
        self.stdout.write(f"Velikost dávky: {batch_size}")
        self.stdout.write(f"Počet dávek: {batch_count}")
        self.stdout.write("")
        self.stdout.write("Zpracovávám projekty...")

        processed_count = 0

        for i in range(batch_count):
            self.stdout.write(f"\rDávka {i + 1} / {batch_count}", ending="")

            with transaction.atomic():
                projekty = list(Projekt.objects.order_by("id")[i * batch_size : (i + 1) * batch_size])

                for projekt in projekty:
                    projekt.suppress_signal = True
                    projekt.set_pristupnost()

                Projekt.objects.bulk_update(projekty, ["pristupnost_snapshot"])
                processed_count += len(projekty)

        self.stdout.write("")
        logger.debug(
            "cron.management.commands.update_pristupnost_snapshot.end",
            extra={"processed": processed_count, "batch_size": batch_size},
        )

        self.stdout.write(self.style.SUCCESS(f"\nDokončeno. Aktualizováno {processed_count} projektů"))
