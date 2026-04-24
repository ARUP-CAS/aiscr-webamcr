import io
import logging

from core.repository_connector import FedoraRepositoryConnector
from django.core.management.base import BaseCommand
from PIL import Image
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro doplnění chybějícího pole ``rozsah`` u souborů v DB.

    Prochází záznamy ``Soubor`` kde ``rozsah IS NULL`` a pro každý soubor
    stáhne binární obsah z Fedora repozitáře, spočítá počet stran (PDF) nebo
    snímků (TIF) a uloží hodnotu do DB bez spuštění Fedora transakcí.

    Příklady použití::

        python manage.py fix_soubor_rozsah
        python manage.py fix_soubor_rozsah --dry-run
        python manage.py fix_soubor_rozsah --limit 500
    """

    help = "Doplní chybějící rozsah (počet stran/snímků) u souborů s rozsah IS NULL."

    def add_arguments(self, parser):
        """
        Registruje příkazové argumenty.

        :param parser: Argumentový parser pro přidání nových parametrů příkazu.
        """
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Pouze zobrazí kolik záznamů by bylo opraveno, nic neuloží.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximální počet zpracovaných souborů.",
        )

    def handle(self, *args, **options):
        """
        Prochází soubory s chybějícím rozsahem a doplní jej z Fedora repozitáře.

        :param args: Poziční argumenty příkazu (nepoužívá se).
        :param options: Pojmenované argumenty (dry_run, limit) ze příkazového řádku.
        """
        from core.models import Soubor

        dry_run = options["dry_run"]
        limit = options["limit"]

        qs = Soubor.objects.filter(rozsah__isnull=True).exclude(path__isnull=True)
        if limit:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(f"Nalezeno {total} souborů s chybějícím rozsahem.")
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run: žádné změny nebudou uloženy."))
            return

        success_count = 0
        fallback_count = 0
        error_count = 0

        for index, soubor in enumerate(qs.iterator(chunk_size=100)):
            if index % max(total // 20, 1) == 0:
                self.stdout.write(f"\r{round(index / total * 100)}%", ending="")

            try:
                related_record = soubor.vazba.navazany_objekt
                conn = FedoraRepositoryConnector(related_record, None)
                rep_bin_file = conn.get_binary_file(soubor.repository_uuid)

                if rep_bin_file is None:
                    error_count += 1
                    logger.error(
                        "core.management.commands.fix_soubor_rozsah.binary_not_found",
                        extra={"pk": soubor.pk, "path": soubor.path},
                    )
                    self.stdout.write(
                        self.style.ERROR(f"\nSoubor nenalezen v repozitari pk={soubor.pk}: {soubor.path}")
                    )
                    continue

                content: io.BytesIO = rep_bin_file.content
                nazev = soubor.nazev.lower()
                if nazev.endswith(".pdf"):
                    try:
                        reader = PdfReader(content)
                        rozsah = len(reader.pages)
                    except Exception:
                        rozsah = 1
                        fallback_count += 1
                elif nazev.endswith(".tif"):
                    try:
                        img = Image.open(content)
                        rozsah = img.n_frames  # type: ignore[attr-defined]
                    except Exception:
                        rozsah = 1
                        fallback_count += 1
                else:
                    rozsah = 1

                Soubor.objects.filter(pk=soubor.pk).update(rozsah=rozsah)
                success_count += 1
                logger.info(
                    "core.management.commands.fix_soubor_rozsah.updated",
                    extra={"pk": soubor.pk, "rozsah": rozsah},
                )

            except Exception as err:
                error_count += 1
                logger.error(
                    "core.management.commands.fix_soubor_rozsah.error",
                    extra={"pk": soubor.pk, "error": str(err)},
                )
                self.stdout.write(self.style.ERROR(f"\nChyba u souboru pk={soubor.pk}: {err}"))

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Celkem:   {total}")
        self.stdout.write(f"Úspěšně:  {success_count}")
        self.stdout.write(f"Fallback: {fallback_count}")
        self.stdout.write(f"Chyby:    {error_count}")
        self.stdout.write("=" * 50)

        if error_count > 0:
            self.stdout.write(self.style.WARNING(f"Dokončeno s {error_count} chybami."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Dokončeno. Opraveno {success_count} souborů."))
