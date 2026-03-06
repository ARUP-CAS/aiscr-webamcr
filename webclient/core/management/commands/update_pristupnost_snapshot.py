import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro aktualizaci snímku přístupnosti projektů.

    Tento příkaz prochází všechny projekty a aktualizuje jejich pole pristupnost_snapshot
    pomocí metody set_pristupnost(). Projekty jsou zpracovávány v dávkách pro optimalizaci
    výkonu a zamezení přílišnému zatížení databáze.

    Parametry:
    - --batch-size: Velikost dávky pro zpracování (výchozí: 100)

    Poznámka:
    - Pro projekty je dočasně potlačen signál (suppress_signal=True) aby nedošlo k nežádoucím vedlejším efektům během hromadné aktualizace

    Příklady použití::

    python manage.py update_pristupnost_snapshot
    python manage.py update_pristupnost_snapshot --batch-size 200
    python manage.py update_pristupnost_snapshot --batch-size 50
    """

    help = _("core.management.commands.update_pristupnost_snapshot.Command.help")

    def add_arguments(self, parser):
        """
        Provádí operaci add arguments.

        :param parser: Parametr ``parser`` pracuje se s atributy ``add_argument``.
        """
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help=_("core.management.commands.update_pristupnost_snapshot.Command.add_arguments.batch_size_help"),
        )

    def handle(self, *args, **options):
        """
        Zpracuje hodnotu. v aplikaci.

        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``handle``.
        :param options: Parametr ``options`` slouží jako vstup pro logiku funkce ``handle``.
        """
        from projekt.models import Projekt

        batch_size = options["batch_size"]

        logger.debug(
            "core.management.commands.update_pristupnost_snapshot.start",
            extra={"batch_size": batch_size},
        )

        projekt_count = Projekt.objects.all().count()
        batch_count = projekt_count // batch_size + 1

        self.stdout.write(
            _("core.management.commands.update_pristupnost_snapshot.total_projects") + " " + str(projekt_count)
        )
        self.stdout.write(_("core.management.commands.update_pristupnost_snapshot.batch_size") + " " + str(batch_size))
        self.stdout.write(
            _("core.management.commands.update_pristupnost_snapshot.batch_count") + " " + str(batch_count)
        )
        self.stdout.write("")
        self.stdout.write(_("core.management.commands.update_pristupnost_snapshot.processing_projects"))

        processed_count = 0

        for i in range(batch_count):
            self.stdout.write(
                "\r"
                + _("core.management.commands.update_pristupnost_snapshot.batch")
                + " "
                + str(i + 1)
                + " / "
                + str(batch_count),
                ending="",
            )

            with transaction.atomic():
                projekty = list(Projekt.objects.order_by("id")[i * batch_size : (i + 1) * batch_size])

                for projekt in projekty:
                    projekt.suppress_signal = True
                    projekt.set_pristupnost()

                Projekt.objects.bulk_update(projekty, ["pristupnost_snapshot"])
                processed_count += len(projekty)

        self.stdout.write("")
        logger.debug(
            "core.management.commands.update_pristupnost_snapshot.end",
            extra={"processed": processed_count, "batch_size": batch_size},
        )

        self.stdout.write(
            self.style.SUCCESS(
                "\n"
                + _("core.management.commands.update_pristupnost_snapshot.finished_updated")
                + " "
                + str(processed_count)
            )
        )
