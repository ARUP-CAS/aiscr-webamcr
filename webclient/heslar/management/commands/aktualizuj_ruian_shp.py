"""
Django management příkaz ``aktualizuj_ruian_shp``.

Spouští plnou synchronizaci heslářů RÚIAN ze **dvojice** lokálních souborů:

* **SHP** ``1.zip`` (státní polygony krajů/okresů/KÚ, ~241 MB) –
  https://services.cuzk.gov.cz/shp/stat/epsg-5514/1.zip
* **VFR** ``YYYYMMDD_ST_UZSZ.xml.zip`` (autoritativní definiční body, ~4.5 MB) –
  https://services.cuzk.gov.cz/vfr/<RRRRMM>/<RRRRMMDD>_ST_UZSZ.xml.zip nebo
  https://vdp.cuzk.gov.cz/vdp/ruian/vymennyformat?crKopie=on&casovyRozsah=U&upStatAzZsj=on&uzemniPrvky=ST&dsZakladni=on&datovaSada=Z&vyZakladni=on&vyber=vyZakladni&kodOrp=&search=

Operátor stáhne oba soubory (typicky ručně přes ``wget``) do
``/vol/data-migrace/`` a předá cesty argumenty ``--shp`` a ``--uzsz``.

Syncer (:func:`heslar.ruian_sync.syncer.sync_full`) je sdílený.
Pro běžný plný sync je preferován tento command (jen 2 soubory ~245 MB
namísto tisíců souborů v alternativních zdrojích).

Pro denní inkrementální změny používej :func:`cron.tasks.sync_ruian_changes`
s VFR variantou ``ZKSH`` – beze změny, není dotčeno.

Příklady použití::

    python manage.py aktualizuj_ruian_shp \\
        --shp /vol/data-migrace/1.zip \\
        --uzsz /vol/data-migrace/20260228_ST_UZSZ.xml.zip \\
        --valid-to 2026-02-28

    # Vstup může být i rozbalený adresář s SHP layery
    python manage.py aktualizuj_ruian_shp \\
        --shp /home/admin/ARUP/Katastry/ \\
        --uzsz /vol/data-migrace/20260228_ST_UZSZ.xml.zip \\
        --valid-to 2026-02-28
"""

import logging
import traceback
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.translation import gettext as _
from heslar.models import RuianSyncRun
from heslar.ruian_sync import ShpUzszSource
from heslar.ruian_sync import syncer as ruian_syncer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro plný sync heslářů RÚIAN ze SHP + UZSZ.

    Příkaz otevře předané SHP a UZSZ soubory přes :class:`ShpUzszSource`,
    založí ``RuianSyncRun(mode=full, source="shp_uzsz")`` ve stavu
    ``running`` a deleguje aplikaci dat na sdílený
    :func:`heslar.ruian_sync.syncer.sync_full`. Při úspěchu nastaví
    ``status="success"``, při výjimce uloží traceback do ``error``
    a vrátí exit code 1.

    Cesta k UZSZ se uloží do ``RuianSyncRun.note`` (pole ``source_path``
    nese SHP cestu, protože je primárním nositelem polygonů).
    """

    help = _("heslar.management.commands.aktualizuj_ruian_shp.Command.help")

    def add_arguments(self, parser):
        """
        Registruje argumenty příkazu.

        :param parser: Argumentový parser pro přidání parametrů.
        """
        parser.add_argument(
            "--shp",
            type=str,
            required=True,
            help=_("heslar.management.commands.aktualizuj_ruian_shp.Command.add_arguments.shp_help"),
        )
        parser.add_argument(
            "--uzsz",
            type=str,
            required=True,
            help=_("heslar.management.commands.aktualizuj_ruian_shp.Command.add_arguments.uzsz_help"),
        )
        parser.add_argument(
            "--valid-to",
            type=str,
            required=True,
            help=_("heslar.management.commands.aktualizuj_ruian_shp.Command.add_arguments.valid_to_help"),
        )

    def handle(self, *args, **options):
        """
        Vykoná plnou synchronizaci heslářů RÚIAN ze SHP + UZSZ.

        :param args: Standardní pozicovaný argument managementu.
        :param options: Slovník s argumenty (``shp``, ``uzsz``, ``valid_to``).

        :raises CommandError: Pokud některá vstupní cesta neexistuje nebo
            ``--valid-to`` má neplatný formát.
        """
        shp_path = Path(options["shp"])
        uzsz_path = Path(options["uzsz"])
        if not shp_path.exists():
            raise CommandError(f"SHP cesta neexistuje: {shp_path}")
        if not uzsz_path.exists():
            raise CommandError(f"UZSZ cesta neexistuje: {uzsz_path}")

        try:
            valid_to = datetime.strptime(options["valid_to"], "%Y-%m-%d").date()
        except ValueError as exc:
            raise CommandError(f"Neplatný formát --valid-to (očekáván YYYY-MM-DD): {exc}")

        logger.debug(
            "heslar.management.commands.aktualizuj_ruian_shp.handle.start",
            extra={
                "shp": str(shp_path),
                "uzsz": str(uzsz_path),
                "valid_to": valid_to.isoformat(),
            },
        )

        source = ShpUzszSource(shp_path=shp_path, uzsz_path=uzsz_path)

        initial_note_parts = [f"uzsz={uzsz_path.name}"]

        run = RuianSyncRun.objects.create(
            mode=RuianSyncRun.MODE_FULL,
            source=source.source_id,
            triggered_by=RuianSyncRun.TRIGGER_MANAGE,
            source_path=str(shp_path),
            data_valid_to=valid_to,
            variant="SHP_UZSZ",
            note=", ".join(initial_note_parts),
        )
        self.stdout.write(self.style.NOTICE(f"Vytvořen RuianSyncRun #{run.pk} (running)..."))
        self.stdout.write(f"  SHP:  {shp_path}")
        self.stdout.write(f"  UZSZ: {uzsz_path}")
        self.stdout.write(f"  valid_to: {valid_to.isoformat()}")

        try:
            ruian_syncer.sync_full(source=source, run=run)
        except Exception as exc:  # noqa: BLE001 — záměrně chytáme vše a logujeme
            run.error = traceback.format_exc()
            run.status = RuianSyncRun.STATUS_FAILED
            run.finished_at = timezone.now()
            run.save(update_fields=["error", "status", "finished_at"])
            logger.error(
                "heslar.management.commands.aktualizuj_ruian_shp.handle.error",
                extra={"run_id": run.pk, "error": str(exc)},
            )
            raise CommandError(f"Synchronizace selhala – RuianSyncRun #{run.pk}: {exc}")

        run.refresh_from_db()
        run.status = RuianSyncRun.STATUS_SUCCESS
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "finished_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Synchronizace dokončena. RuianSyncRun #{run.pk}: "
                f"kraj +{run.kraj_upserts}/-{run.kraj_deletes}, "
                f"okres +{run.okres_upserts}/-{run.okres_deletes}, "
                f"katastr +{run.katastr_upserts}/-{run.katastr_deletes}, "
                f"přepočítáno: AZ {run.affected_az}, projekt {run.affected_projekt}, SN {run.affected_sn}."
            )
        )
