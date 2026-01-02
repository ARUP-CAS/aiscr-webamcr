import logging

import pandas as pd
from core.repository_connector import FedoraRepositoryConnector
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro generování náhledů souborů.

    Tento příkaz zpracuje dávku souborů a pro každý soubor zkontroluje,
    zda existují náhledy v Fedora repozitáři. Pokud náhledy neexistují,
    vygeneruje je ze zdrojového souboru.

    Parametry (vzájemně se vylučují):
        --pks: Seznam primárních klíčů souborů (odděleno mezerami)
        --range: Rozsah primárních klíčů ve formátu "start end"
        --csv: Cesta k CSV souboru s listem cest v sloupci "record" (repository path)

    Poznámka:
        Musí být zadán právě jeden z parametrů --pks, --range, nebo --csv.
        Náhledy jsou generovány pouze pro obrazové formáty podporované systémem.

    Příklady použití:
        python manage.py generate_thumbs --pks 1 2 3
        python manage.py generate_thumbs --range 100 200
        python manage.py generate_thumbs --range 1 1000
        python manage.py generate_thumbs --csv /tmp/missing_thumbs.csv
    """

    help = _("core.management.commands.generate_thumbs.Command.help")

    def add_arguments(self, parser):
        parser.add_argument(
            "--pks",
            nargs="+",
            type=int,
            help=_("core.management.commands.generate_thumbs.Command.add_arguments.pks_help"),
        )
        parser.add_argument(
            "--range",
            nargs=2,
            type=int,
            metavar=("START", "END"),
            help=_("core.management.commands.generate_thumbs.Command.add_arguments.range_help"),
        )
        parser.add_argument(
            "--csv",
            type=str,
            help=_("core.management.commands.generate_thumbs.Command.add_arguments.csv_help"),
        )

    def handle(self, *args, **options):
        pks = options.get("pks")
        pk_range = options.get("range")
        csv_file = options.get("csv")

        from core.models import Soubor

        success_count = 0
        error_count = 0

        sources_selected = [src for src in [pks, pk_range, csv_file] if src]
        if len(sources_selected) > 1:
            raise CommandError(_("core.management.commands.generate_thumbs.Command.handle.multiple_sources_error"))
        if len(sources_selected) == 0:
            raise CommandError(_("core.management.commands.generate_thumbs.Command.handle.missing_params_error"))

        if csv_file:
            logger.debug(
                "core.management.commands.generate_thumbs.start",
                extra={"type": "csv", "csv_file": csv_file},
            )
            try:
                sheet = pd.read_csv(csv_file, sep=",")
            except Exception as err:
                logger.error(
                    "core.management.commands.generate_thumbs.csv_read_error",
                    extra={"csv_file": csv_file, "error": str(err)},
                )
                self.stdout.write(
                    self.style.ERROR(
                        _("core.management.commands.generate_thumbs.Command.handle.csv_read_error") + str(err)
                    )
                )
                return

            total = len(sheet)
            self.stdout.write(
                _("core.management.commands.generate_thumbs.Command.handle.processing_total") + " " + str(total)
            )

            for index, row in sheet.iterrows():
                if total > 0 and index % max(total // 100, 1) == 0:
                    percentage = round(index / total * 100)
                    self.stdout.write(
                        "\r"
                        + _("core.management.commands.generate_thumbs.Command.handle.progress")
                        + " "
                        + str(percentage)
                        + "%",
                        ending="",
                    )

                try:
                    item = Soubor.objects.get(path=row["record"])
                except Soubor.DoesNotExist:
                    error_count += 1
                    logger.warning(
                        "core.management.commands.generate_thumbs.file_not_found",
                        extra={"path": row["record"]},
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            "\n"
                            + _("core.management.commands.generate_thumbs.Command.handle.file_not_found")
                            + " "
                            + str(row["record"])
                        )
                    )
                    continue

                try:
                    FedoraRepositoryConnector.generate_thumb_for_single_file(item)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(
                        "core.management.commands.generate_thumbs.error",
                        extra={"pk": item.pk, "error": str(e)},
                    )
                    self.stdout.write(
                        self.style.ERROR(
                            "\n"
                            + _("core.management.commands.generate_thumbs.Command.handle.error_prefix")
                            + " "
                            + str(item.pk)
                            + ": "
                            + str(e)
                        )
                    )

            self.stdout.write("")
        else:
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

            queryset = Soubor.objects.filter(pk__in=records).order_by("pk")
            total = queryset.count()

            self.stdout.write(
                _("core.management.commands.generate_thumbs.Command.handle.processing_total") + " " + str(total)
            )

            for index, item in enumerate(queryset, 1):
                try:
                    FedoraRepositoryConnector.generate_thumb_for_single_file(item)
                    success_count += 1
                    if index % 10 == 0 or index == total:
                        self.stdout.write(
                            _("core.management.commands.generate_thumbs.Command.handle.processed")
                            + " "
                            + str(index)
                            + "/"
                            + str(total)
                        )
                except Exception as e:
                    error_count += 1
                    logger.error(
                        "core.management.commands.generate_thumbs.error",
                        extra={"pk": item.pk, "error": str(e)},
                    )
                    self.stdout.write(
                        self.style.ERROR(
                            _("core.management.commands.generate_thumbs.Command.handle.error_prefix")
                            + " "
                            + str(item.pk)
                            + ": "
                            + str(e)
                        )
                    )

        logger.debug(
            "core.management.commands.generate_thumbs.end",
            extra={"count": total, "success": success_count, "errors": error_count},
        )

        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    _("core.management.commands.generate_thumbs.Command.handle.finished_with_errors")
                    + str(success_count)
                    + ", "
                    + _("core.management.commands.generate_thumbs.Command.handle.errors")
                    + str(error_count)
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    _("core.management.commands.generate_thumbs.Command.handle.finished_success") + str(success_count)
                )
            )
