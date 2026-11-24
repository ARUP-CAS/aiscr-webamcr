import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro opětovné spuštění selhaných aktualizací IGSN z PAS API (#4523).

    Najde samostatné nálezy, které mají v ``ApiRequestLog`` aspoň jeden záznam s ``igsn_status = failed``
    (DataCite změnu odmítl, opakování se vyčerpala nebo úlohu nešlo naplánovat). Těmto záznamům nastaví stav
    ``retry_pending`` a pro každý nález naplánuje bez prodlevy úlohu
    :func:`cron.tasks.retry_samostatny_nalez_igsn_update`, která podle výsledku nastaví ``updated`` nebo
    znovu ``failed``. Hodí se po opravě příčiny, např. přihlašovacích údajů k DataCite.

    Příklady použití::

        python manage.py retry_failed_igsn_updates
        python manage.py retry_failed_igsn_updates --dry-run
        python manage.py retry_failed_igsn_updates --ident C-202009779-N00001 --ident C-202009779-N00002
    """

    help = "Znovu naplánuje aktualizaci IGSN pro samostatné nálezy se záznamem ApiRequestLog ve stavu failed."

    def add_arguments(self, parser):
        """
        Registruje příkazové argumenty.

        :param parser: Argumentový parser pro přidání nových parametrů příkazu.
        """
        parser.add_argument(
            "--ident",
            action="append",
            dest="idents",
            default=None,
            help="ident_cely nálezu, na který se běh omezí; lze zadat vícekrát.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Pouze vypíše dotčené nálezy, nic nezmění ani nenaplánuje.",
        )

    def handle(self, *args, **options):
        """
        Vrátí selhané záznamy logu do stavu ``retry_pending`` a naplánuje pro jejich nálezy aktualizaci IGSN.

        Záznamy se přepnou v jedné databázové transakci; úlohy se plánují až po jejím potvrzení, aby úloha
        nenašla záznamy ještě ve stavu ``failed``. Nález, pro který už úloha ve frontě čeká, se znovu neplánuje.

        :param args: Poziční argumenty příkazu (nepoužívá se).
        :param options: Pojmenované argumenty (``idents``, ``dry_run``) z příkazového řádku.
        """
        from api.models import ApiRequestLog
        from core.constants import API_REQUEST_LOG_IGSN_STATUS_FAILED, API_REQUEST_LOG_IGSN_STATUS_RETRY_PENDING
        from cron.tasks import schedule_samostatny_nalez_igsn_retry
        from pas.models import SamostatnyNalez

        entries = ApiRequestLog.objects.filter(
            igsn_status=API_REQUEST_LOG_IGSN_STATUS_FAILED, samostatny_nalez__isnull=False
        )
        if options["idents"]:
            entries = entries.filter(samostatny_nalez__ident_cely__in=options["idents"])

        per_record = list(
            entries.values("samostatny_nalez_id", "samostatny_nalez__ident_cely")
            .annotate(pocet=Count("id"))
            .order_by("samostatny_nalez__ident_cely")
        )
        if not per_record:
            self.stdout.write("Žádné selhané aktualizace IGSN k opakování.")
            return

        for row in per_record:
            self.stdout.write(f"{row['samostatny_nalez__ident_cely']}: {row['pocet']} záznam(ů) logu ve stavu failed")

        if options["dry_run"]:
            self.stdout.write(f"Dry run: {len(per_record)} nález(ů) by se znovu naplánovalo, nic se nezměnilo.")
            return

        record_pks = [row["samostatny_nalez_id"] for row in per_record]
        with transaction.atomic():
            reset = entries.filter(samostatny_nalez_id__in=record_pks).update(
                igsn_status=API_REQUEST_LOG_IGSN_STATUS_RETRY_PENDING
            )

        scheduled = 0
        for nalez in SamostatnyNalez.objects.filter(pk__in=record_pks).order_by("ident_cely"):
            if schedule_samostatny_nalez_igsn_retry(nalez, countdown=0):
                scheduled += 1
        logger.info(
            "api.management.commands.retry_failed_igsn_updates.done",
            extra={"records": len(record_pks), "entries": reset, "scheduled": scheduled},
        )
        self.stdout.write(
            f"Hotovo: {reset} záznam(ů) logu přepnuto na retry_pending, "
            f"naplánováno {scheduled} úloh(y) pro {len(record_pks)} nález(ů)."
        )
