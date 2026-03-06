import logging

import pandas as pd
from core.repository_connector import FedoraRepositoryConnector, FedoraTransaction
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro odstranění GPS dat z existujících souborů.

    Tento příkaz načte CSV soubor obsahující seznam souborů (cesty v Fedora repozitáři)
    a pro každý záznam odstraní GPS metadata z obrázků (EXIF data).
    Po odstranění GPS dat je soubor aktualizován v Fedora repozitáři.

    CSV soubor musí obsahovat sloupec "record" s cestami k souborům.

    Argumenty:
    - csv_file: Cesta k CSV souboru se seznamem souborů

    Formát CSV souboru::

    record
    /path/to/image1.jpg
    /path/to/image2.jpg
    /path/to/image3.jpg

    Poznámka:
    - Pouze soubory, které mají GPS data, budou aktualizovány
    - Pro každou aktualizaci se zaznamená nová verze souboru

    Příklady použití:

    Hostitelský adresář ``/home/migrace`` je v Docker YAML namapovaný na ``/vol/data-migrace``,
    proto se uvnitř kontejneru používá cesta ``/vol/data-migrace``::

    python manage.py remove_gps_data /vol/data-migrace/files_with_gps.csv
    python manage.py remove_gps_data /vol/data-migrace/images.csv
    """

    help = _("core.management.commands.remove_gps_data.Command.help")

    def add_arguments(self, parser):
        """
        Provádí operaci add arguments.

        :param parser: Parametr ``parser`` pracuje se s atributy ``add_argument``.
        """
        parser.add_argument(
            "csv_file",
            type=str,
            help=_("core.management.commands.remove_gps_data.Command.add_arguments.csv_file_help"),
        )

    def handle(self, *args, **options):
        """
        Zpracuje hodnotu. v aplikaci.

        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``handle``.
        :param options: Parametr ``options`` slouží jako vstup pro logiku funkce ``handle``.
        """
        csv_file = options["csv_file"]

        logger.debug(
            "core.management.commands.remove_gps_data.start",
            extra={"csv_file": csv_file},
        )

        from core.models import Soubor
        from heslar.hesla_dynamicka import ADMIN_USER
        from uzivatel.models import User
        from xml_generator.models import ModelWithMetadata

        # Načte administrátorského uživatele pro systémové změny.
        try:
            admin_user = User.objects.get(pk=ADMIN_USER)
        except User.DoesNotExist:
            logger.error(
                "core.management.commands.remove_gps_data.admin_user_not_found",
                extra={"admin_user_pk": ADMIN_USER},
            )
            self.stdout.write(
                self.style.ERROR(_("core.management.commands.remove_gps_data.admin_user_not_found") + str(ADMIN_USER))
            )
            return

        # Načte vstupní CSV se seznamem dokumentů.
        try:
            sheet = pd.read_csv(csv_file, sep=",")
        except Exception as e:
            logger.error(
                "core.management.commands.remove_gps_data.csv_read_error",
                extra={"csv_file": csv_file, "error": str(e)},
            )
            self.stdout.write(
                self.style.ERROR(_("core.management.commands.remove_gps_data.csv_read_error") + " " + str(e))
            )
            return

        total = len(sheet)
        success_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(_("core.management.commands.remove_gps_data.processing_total") + " " + str(total))

        for index, row in sheet.iterrows():
            # Show progress
            if index % max(total // 100, 1) == 0:
                percentage = round(index / total * 100)
                self.stdout.write(
                    "\r" + _("core.management.commands.remove_gps_data.progress") + " " + str(percentage) + "%",
                    ending="",
                )

            try:
                record = Soubor.objects.get(path=row["record"])

                related_record: ModelWithMetadata = record.vazba.navazany_objekt
                fedora_transaction = FedoraTransaction()
                record.active_transaction = fedora_transaction
                conn = FedoraRepositoryConnector(related_record, fedora_transaction)

                rep_bin_file = conn.get_binary_file(record.repository_uuid)
                if rep_bin_file:
                    rep_bin_file_new = Soubor.remove_gps_data(rep_bin_file.content)
                    # Ověří, zda byla GPS data opravdu odstraněna (změnil se obsah souboru).
                    if rep_bin_file_new is not rep_bin_file.content:
                        rep_bin_file = conn.update_binary_file(
                            record.nazev, record.mimetype, rep_bin_file_new, record.repository_uuid
                        )
                        record.size_mb = rep_bin_file.size_mb
                        record.sha_512 = rep_bin_file.sha_512
                        record.zaznamenej_nahrani_nove_verze(admin_user, record.nazev)
                        record.save()
                        updated_count += 1
                        logger.info(
                            "core.management.commands.remove_gps_data.file_updated",
                            extra={"path": row["record"], "pk": record.pk},
                        )
                    else:
                        skipped_count += 1
                else:
                    skipped_count += 1
                    logger.warning(
                        "core.management.commands.remove_gps_data.binary_file_not_found",
                        extra={"path": row["record"], "uuid": record.repository_uuid},
                    )

                fedora_transaction.mark_transaction_as_closed()
                success_count += 1

            except Soubor.DoesNotExist:
                error_count += 1
                error_msg = _("core.management.commands.remove_gps_data.file_not_found") + " " + str(row["record"])
                logger.warning(
                    "core.management.commands.remove_gps_data.file_not_found",
                    extra={"path": row["record"]},
                )
                self.stdout.write(self.style.WARNING("\n" + error_msg))
            except Exception as err:
                error_count += 1
                logger.error(
                    "core.management.commands.remove_gps_data.error",
                    extra={"path": row["record"], "error": str(err)},
                )
                self.stdout.write(
                    self.style.ERROR(
                        "\n"
                        + _("core.management.commands.remove_gps_data.error")
                        + " "
                        + str(row["record"])
                        + " - "
                        + str(err)
                    )
                )

        # Závěrečný nový řádek po indikátoru průběhu.
        self.stdout.write("")

        logger.debug(
            "core.management.commands.remove_gps_data.end",
            extra={
                "total": total,
                "success": success_count,
                "updated": updated_count,
                "skipped": skipped_count,
                "errors": error_count,
            },
        )

        # Summary output
        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(_("core.management.commands.remove_gps_data.summary_header"))
        self.stdout.write(_("core.management.commands.remove_gps_data.summary_total") + " " + str(total))
        self.stdout.write(_("core.management.commands.remove_gps_data.summary_success") + " " + str(success_count))
        self.stdout.write(_("core.management.commands.remove_gps_data.summary_updated") + " " + str(updated_count))
        self.stdout.write(_("core.management.commands.remove_gps_data.summary_skipped") + " " + str(skipped_count))
        self.stdout.write(_("core.management.commands.remove_gps_data.summary_errors") + " " + str(error_count))
        self.stdout.write("=" * 50)

        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    "\n"
                    + _("core.management.commands.remove_gps_data.finished_with_errors")
                    + " "
                    + str(updated_count)
                    + ", "
                    + _("core.management.commands.remove_gps_data.errors")
                    + " "
                    + str(error_count)
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n" + _("core.management.commands.remove_gps_data.finished_success") + " " + str(updated_count)
                )
            )
