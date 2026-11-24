"""Nedestruktivní kontrola zdrojové matice a pokrytí URL."""

from pathlib import Path

from core.permission_validation import PermissionPolicyError, validate_permission_file
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """Ověří matici oprávnění, aniž by zapisoval do databáze."""

    help = "Zkontroluje zdrojovou matici oprávnění a pokrytí rout."
    requires_system_checks = []

    def add_arguments(self, parser):
        """Umožní ověřit i alternativní CSV nebo XLSX soubor.

        :param parser: Parser argumentů příkazu Django.
        """
        parser.add_argument(
            "--file",
            type=Path,
            default=None,
            help="Cesta k úplné CSV nebo XLSX matici; výchozí je verzovaný CSV soubor.",
        )

    def handle(self, *args, **options):
        """Vypíše všechny chyby a při neplatné matici vrátí nenulový stav.

        :param args: Poziční argumenty příkazu předané Djangem.
        :param options: Pojmenované argumenty příkazu včetně cesty k matici.
        """
        source = options["file"] or Path(settings.BASE_DIR) / "core/resources/uzivatelska_prava.csv"
        try:
            with source.open("rb") as docfile:
                sheet, records = validate_permission_file(docfile)
        except (OSError, PermissionPolicyError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(
            self.style.SUCCESS(f"Matice oprávnění je platná ({len(sheet)} řádků, {len(records)} pravidel).")
        )
