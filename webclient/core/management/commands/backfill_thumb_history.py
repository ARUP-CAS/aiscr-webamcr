import logging

from core.constants import NAHRANI_DISTRIBUCE, UPDATE_DISTRIBUCE
from core.repository_connector import FedoraRepositoryConnector
from django.core.management.base import BaseCommand
from heslar import hesla_dynamicka
from historie.models import Historie
from uzivatel.models import User

logger = logging.getLogger(__name__)

# Kontejnery náhledů, které se pro soubor generují a evidují jako distribuce.
THUMB_DISTRIBUTIONS = ("thumb", "thumb-large")


class Command(BaseCommand):
    """
    Django management příkaz pro doplnění historie náhledů existujících souborů.

    Náhledy vznikaly dřív, než se pro ně zapisovala historie distribucí, takže u nich chybí
    záznamy ``DIST01``/``DIST11``. Příkaz projde soubory, u každého načte verze kontejnerů
    ``thumb`` a ``thumb-large`` z Fedory (``fcr:versions``) a doplní historii: ``DIST01`` pro
    nejstarší verzi a ``DIST11`` pro každou další, zvlášť pro každý kontejner. Datum změny se
    nastavuje na čas příslušné verze, aby pořadí odpovídalo skutečnosti.

    Příkaz je idempotentní — soubory, které už pro daný náhled historii mají, přeskočí.

    Příklady použití::

        python manage.py backfill_thumb_history
        python manage.py backfill_thumb_history --dry-run
        python manage.py backfill_thumb_history --limit 500
    """

    help = "Doplní historii (DIST01/DIST11) k náhledům souborů podle verzí kontejnerů ve Fedoře."

    def add_arguments(self, parser):
        """
        Registruje příkazové argumenty.

        :param parser: Argumentový parser pro přidání nových parametrů příkazu.
        """
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Pouze zobrazí, kolik záznamů historie by vzniklo, nic neuloží.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximální počet zpracovaných souborů.",
        )

    def handle(self, *args, **options):
        """
        Projde soubory a doplní chybějící historii náhledů podle verzí ve Fedoře.

        :param args: Poziční argumenty příkazu (nepoužívá se).
        :param options: Pojmenované argumenty (dry_run, limit) z příkazové řádky.
        """
        from core.models import Soubor

        dry_run = options["dry_run"]
        limit = options["limit"]

        uzivatel = User.objects.filter(pk=hesla_dynamicka.ADMIN_USER).first()
        if uzivatel is None:
            self.stdout.write(self.style.ERROR("Uživatel ADMIN_USER nebyl nalezen, historii nelze zapsat."))
            return

        qs = (
            Soubor.objects.exclude(path__isnull=True)
            .exclude(historie__isnull=True)
            .select_related("vazba", "historie")
            .order_by("pk")
        )
        if limit is not None:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(f"Nalezeno {total} souborů ke kontrole.")
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run: žádné změny nebudou uloženy."))

        created_count = 0
        skipped_count = 0
        error_count = 0

        for index, soubor in enumerate(qs.iterator(chunk_size=100)):
            if total and index % max(total // 20, 1) == 0:
                self.stdout.write(f"\r{round(index / total * 100)}%", ending="")
            try:
                related_record = soubor.vazba.navazany_objekt
                if related_record is None or not soubor.repository_uuid:
                    skipped_count += 1
                    continue
                connector = FedoraRepositoryConnector(related_record, None)
                for distribution in THUMB_DISTRIBUTIONS:
                    if soubor.historie.historie_set.filter(
                        typ_zmeny__in=(NAHRANI_DISTRIBUCE, UPDATE_DISTRIBUCE), poznamka=distribution
                    ).exists():
                        skipped_count += 1
                        continue
                    versions = connector.get_historie_distribution(soubor.repository_uuid, distribution)
                    if not versions:
                        continue
                    versions = sorted(versions, key=lambda version: version["datetime"])
                    for order, version in enumerate(versions):
                        created_count += 1
                        if dry_run:
                            continue
                        # ``datum_zmeny`` má auto_now_add, čas verze se proto nastaví až po uložení.
                        record = Historie.objects.create(
                            typ_zmeny=NAHRANI_DISTRIBUCE if order == 0 else UPDATE_DISTRIBUCE,
                            uzivatel=uzivatel,
                            vazba=soubor.historie,
                            poznamka=distribution,
                        )
                        Historie.objects.filter(pk=record.pk).update(datum_zmeny=version["datetime"])
            except Exception as err:
                error_count += 1
                logger.error(
                    "core.management.commands.backfill_thumb_history.error",
                    extra={"pk": soubor.pk, "error": str(err)},
                )
                self.stdout.write(self.style.ERROR(f"\nChyba u souboru pk={soubor.pk}: {err}"))

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Souborů:            {total}")
        self.stdout.write(f"Záznamů historie:   {created_count}")
        self.stdout.write(f"Přeskočeno náhledů: {skipped_count}")
        self.stdout.write(f"Chyby:              {error_count}")
        self.stdout.write("=" * 50)
