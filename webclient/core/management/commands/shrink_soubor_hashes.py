import json
import logging

from core.models import Soubor
from django.core.management.base import BaseCommand
from django.db import transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro migraci hashů souborů na placeholdery (issue #3967).

    Hromadně přepíše ``soubor.sha_512`` (a volitelně ``size_mb``) na hodnoty
    placeholderu příslušného mimetype; jeden ``UPDATE`` na mimetype (hash placeholderu
    je fixní pro celý mimetype). Týká se jen **aktuálních** souborů (řádky s ``/file/``
    v ``path``); soft-smazané a historické verze nemají v Django DB záznam — jejich
    hash opravuje přímo OCFL nástroj ``scripts/fedora_ocfl_shrink/ocfl_shrink.py``.

    Režim ``--verify`` ověří, že DB odpovídá manifestu placeholderů (bez zápisu).

    Příklady použití::

        python manage.py shrink_soubor_hashes --placeholder-manifest placeholder_manifest.json
        python manage.py shrink_soubor_hashes --placeholder-manifest placeholder_manifest.json --verify
    """

    help = "Hromadný update soubor.sha_512 na placeholdery dle placeholder_manifest.json."

    def add_arguments(self, parser):
        """
        Registruje příkazové argumenty.

        :param parser: Argumentový parser pro přidání nových parametrů příkazu.
        """
        parser.add_argument(
            "--placeholder-manifest",
            required=True,
            help="Cesta k placeholder_manifest.json (mimetype -> {sha512, size, file}).",
        )
        parser.add_argument(
            "--update-size",
            action="store_true",
            default=False,
            help="Při hromadném update přepsat i size_mb podle velikosti placeholderu.",
        )
        parser.add_argument(
            "--verify",
            action="store_true",
            default=False,
            help="Ověří, že soubor.sha_512 odpovídá manifestu (žádný zápis).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Pouze zobrazí, co by se stalo, nic neuloží.",
        )

    def handle(self, *args, **options):
        """
        Spustí hromadný update hashů nebo ověření dle argumentů.

        :param args: Poziční argumenty příkazu (nepoužívá se).
        :param options: Pojmenované argumenty ze příkazového řádku.
        """
        with open(options["placeholder_manifest"], "r", encoding="utf-8") as handle:
            manifest = json.load(handle)

        if options["verify"]:
            self._verify(manifest)
        else:
            self._bulk_update(manifest, options["update_size"], options["dry_run"])

    def _bulk_update(self, manifest, update_size, dry_run):
        """
        Hromadně přepíše ``sha_512`` (a volitelně ``size_mb``) podle manifestu placeholderů.

        :param manifest: Mapa ``mimetype -> {sha512, size, ...}``.
        :param update_size: Zda přepsat i ``size_mb``.
        :param dry_run: Pokud ``True``, nic neuloží.
        """
        total = 0
        self.stdout.write(f"Mimetypů v manifestu: {len(manifest)}.")
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run: žádné změny nebudou uloženy."))

        with transaction.atomic():
            for mimetype, entry in sorted(manifest.items()):
                # Jen soubory se skutečnou binárkou ve Fedoře (path s /file/) — přesně
                # ty, kterým OCFL nástroj nahradil orig; řádky bez binárky se netýkají.
                qs = Soubor.objects.filter(mimetype=mimetype, path__contains="/file/")
                count = qs.count()
                if count == 0:
                    continue
                fields = {"sha_512": entry["sha512"]}
                if update_size:
                    fields["size_mb"] = round(entry["size"] / (1024 * 1024), 10)
                self.stdout.write(f"  {mimetype}: {count} souborů -> sha_512={entry['sha512'][:12]}")
                if not dry_run:
                    qs.update(**fields)
                    logger.info(
                        "core.management.commands.shrink_soubor_hashes.updated",
                        extra={"mimetype": mimetype, "count": count, "sha_512": entry["sha512"]},
                    )
                total += count
            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write("=" * 50)
        action = "Bylo by aktualizováno" if dry_run else "Aktualizováno"
        self.stdout.write(self.style.SUCCESS(f"{action} {total} souborů."))

    def _verify(self, manifest):
        """
        Ověří, že ``soubor.sha_512`` odpovídá hashům v manifestu placeholderů.

        :param manifest: Mapa ``mimetype -> {sha512, ...}``.
        """
        mismatches = 0
        checked = 0
        for mimetype, entry in sorted(manifest.items()):
            qs = Soubor.objects.filter(mimetype=mimetype, path__contains="/file/")
            count = qs.count()
            if count == 0:
                continue
            bad = qs.exclude(sha_512=entry["sha512"]).count()
            checked += count
            if bad:
                mismatches += bad
                self.stdout.write(self.style.ERROR(f"  {mimetype}: {bad}/{count} souborů má jiný sha_512."))
            else:
                self.stdout.write(f"  {mimetype}: {count} OK.")

        self.stdout.write("=" * 50)
        if mismatches:
            self.stdout.write(self.style.ERROR(f"Neshod: {mismatches} z {checked} kontrolovaných souborů."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Vše v pořádku ({checked} souborů odpovídá manifestu)."))
