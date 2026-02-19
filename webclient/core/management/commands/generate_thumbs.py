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
        - --pks: Seznam primárních klíčů souborů (odděleno mezerami)
        - --range: Rozsah primárních klíčů ve formátu "start end"
        - --csv: Cesta k CSV souboru s listem cest v sloupci "record" (repository path)

    Poznámka:
        - Musí být zadán právě jeden z parametrů --pks, --range, nebo --csv
        - Náhledy jsou generovány pouze pro obrazové formáty podporované systémem

    Příklady použití::

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

        # Validate arguments
        provided_options = sum([pks is not None, pk_range is not None, csv_file is not None])
        if provided_options != 1:
            raise CommandError(_("core.management.commands.generate_thumbs.argument_error"))

        logger.debug(
            "core.management.commands.generate_thumbs.start",
            extra={"pks": pks, "range": pk_range, "csv_file": csv_file},
        )

        from core.models import Soubor

        # Determine which soubory to process
        if pks:
            soubory = Soubor.objects.filter(pk__in=pks)
            total = len(pks)
        elif pk_range:
            start_pk, end_pk = pk_range
            soubory = Soubor.objects.filter(pk__gte=start_pk, pk__lte=end_pk)
            total = soubory.count()
        else:  # csv_file
            try:
                sheet = pd.read_csv(csv_file, sep=",")
                soubory = Soubor.objects.filter(path__in=sheet["record"].tolist())
                total = len(sheet)
            except Exception as e:
                logger.error(
                    "core.management.commands.generate_thumbs.csv_read_error",
                    extra={"csv_file": csv_file, "error": str(e)},
                )
                self.stdout.write(
                    self.style.ERROR(_("core.management.commands.generate_thumbs.csv_read_error") + " " + str(e))
                )
                return

        success_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(_("core.management.commands.generate_thumbs.processing_total") + " " + str(total))

        for index, soubor in enumerate(soubory):
            # Show progress
            if index % max(total // 100, 1) == 0:
                percentage = round(index / total * 100)
                self.stdout.write(
                    "\r" + _("core.management.commands.generate_thumbs.progress") + " " + str(percentage) + "%",
                    ending="",
                )

            try:
                related_record = soubor.vazba.navazany_objekt
                conn = FedoraRepositoryConnector(related_record, None)

                # Ověří existenci náhledů.
                both_thumbnails_exist = (
                    conn.get_binary_file(soubor.repository_uuid, thumb_small=True) is not None
                    and conn.get_binary_file(soubor.repository_uuid, thumb_large=True) is not None
                )

                if not both_thumbnails_exist:
                    # Generate thumbnails
                    rep_bin_file = conn.get_binary_file(soubor.repository_uuid)
                    if rep_bin_file:
                        try:
                            conn.save_thumbs(soubor.nazev, rep_bin_file.content, soubor.repository_uuid)
                            success_count += 1
                            logger.info(
                                "core.management.commands.generate_thumbs.thumbs_generated",
                                extra={"pk": soubor.pk, "path": soubor.path},
                            )
                        except Exception as thumb_error:
                            error_count += 1
                            logger.error(
                                "core.management.commands.generate_thumbs.thumb_generation_error",
                                extra={"pk": soubor.pk, "error": str(thumb_error)},
                            )
                    else:
                        skipped_count += 1
                        logger.warning(
                            "core.management.commands.generate_thumbs.binary_file_not_found",
                            extra={"pk": soubor.pk, "uuid": soubor.repository_uuid},
                        )
                else:
                    skipped_count += 1

            except Exception as err:
                error_count += 1
                logger.error(
                    "core.management.commands.generate_thumbs.error",
                    extra={"pk": soubor.pk, "error": str(err)},
                )
                self.stdout.write(
                    self.style.ERROR(
                        "\n"
                        + _("core.management.commands.generate_thumbs.error")
                        + " "
                        + str(soubor.pk)
                        + " - "
                        + str(err)
                    )
                )

        # Závěrečný nový řádek po indikátoru průběhu.
        self.stdout.write("")

        logger.debug(
            "core.management.commands.generate_thumbs.end",
            extra={
                "total": total,
                "success": success_count,
                "skipped": skipped_count,
                "errors": error_count,
            },
        )

        # Summary output
        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(_("core.management.commands.generate_thumbs.summary_header"))
        self.stdout.write(_("core.management.commands.generate_thumbs.summary_total") + " " + str(total))
        self.stdout.write(_("core.management.commands.generate_thumbs.summary_success") + " " + str(success_count))
        self.stdout.write(_("core.management.commands.generate_thumbs.summary_skipped") + " " + str(skipped_count))
        self.stdout.write(_("core.management.commands.generate_thumbs.summary_errors") + " " + str(error_count))
        self.stdout.write("=" * 50)

        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    "\n"
                    + _("core.management.commands.generate_thumbs.finished_with_errors")
                    + " "
                    + str(success_count)
                    + ", "
                    + _("core.management.commands.generate_thumbs.errors")
                    + " "
                    + str(error_count)
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n" + _("core.management.commands.generate_thumbs.finished_success") + " " + str(success_count)
                )
            )
