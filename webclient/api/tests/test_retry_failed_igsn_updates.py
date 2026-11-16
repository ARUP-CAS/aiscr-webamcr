"""Jednotkové testy management příkazu ``retry_failed_igsn_updates`` (#4523)."""

from io import StringIO
from unittest import mock

from core.constants import API_REQUEST_LOG_IGSN_STATUS_FAILED, API_REQUEST_LOG_IGSN_STATUS_RETRY_PENDING
from django.core.management import call_command
from django.test import SimpleTestCase

ROWS = [
    {"samostatny_nalez_id": 1, "samostatny_nalez__ident_cely": "C-202009779-N00001", "pocet": 2},
    {"samostatny_nalez_id": 2, "samostatny_nalez__ident_cely": "C-202009779-N00002", "pocet": 1},
]


@mock.patch("django.db.transaction.atomic")
@mock.patch("cron.tasks.schedule_samostatny_nalez_igsn_retry", return_value=True)
@mock.patch("pas.models.SamostatnyNalez.objects")
@mock.patch("api.models.ApiRequestLog.objects")
class RetryFailedIgsnUpdatesTest(SimpleTestCase):
    """Ověřuje výběr selhaných záznamů, jejich přepnutí na ``retry_pending`` a plánování úloh."""

    @staticmethod
    def _priprav(log_objects, nalez_objects, rows, reset_count=3):
        """
        Nastaví mocky querysetů tak, aby výběr vrátil zadané řádky.

        :param log_objects: Mock ``ApiRequestLog.objects``.
        :param nalez_objects: Mock ``SamostatnyNalez.objects``.
        :param rows: Řádky agregace podle nálezu.
        :param reset_count: Počet záznamů vrácený z ``update``.

        :return: Mock querysetu selhaných záznamů.
        """
        entries = log_objects.filter.return_value
        entries.filter.return_value = entries
        entries.values.return_value.annotate.return_value.order_by.return_value = rows
        entries.update.return_value = reset_count
        nalezy = [
            mock.Mock(pk=row["samostatny_nalez_id"], ident_cely=row["samostatny_nalez__ident_cely"]) for row in rows
        ]
        nalez_objects.filter.return_value.order_by.return_value = nalezy
        return entries

    @staticmethod
    def _spust(*args):
        """
        Spustí příkaz a vrátí jeho výstup.

        :param args: Argumenty příkazu.

        :return: Text vypsaný na standardní výstup.
        """
        out = StringIO()
        call_command("retry_failed_igsn_updates", *args, stdout=out)
        return out.getvalue()

    def test_resets_failed_entries_and_schedules_one_task_per_record(
        self, log_objects, nalez_objects, schedule, _atomic
    ):
        """
        Výchozí běh přepne selhané záznamy na ``retry_pending`` a naplánuje jednu úlohu na nález bez prodlevy.

        :param log_objects: Mock ``ApiRequestLog.objects``.
        :param nalez_objects: Mock ``SamostatnyNalez.objects``.
        :param schedule: Mock ``schedule_samostatny_nalez_igsn_retry``.
        :param _atomic: Mock ``transaction.atomic``.
        """
        entries = self._priprav(log_objects, nalez_objects, ROWS)
        output = self._spust()

        log_objects.filter.assert_called_once_with(
            igsn_status=API_REQUEST_LOG_IGSN_STATUS_FAILED, samostatny_nalez__isnull=False
        )
        entries.filter.assert_called_with(samostatny_nalez_id__in=[1, 2])
        entries.update.assert_called_once_with(igsn_status=API_REQUEST_LOG_IGSN_STATUS_RETRY_PENDING)
        self.assertEqual(schedule.call_count, 2)
        for call in schedule.call_args_list:
            self.assertEqual(call.kwargs, {"countdown": 0})
        self.assertIn("naplánováno 2", output)

    def test_ident_limits_selection(self, log_objects, nalez_objects, schedule, _atomic):
        """
        Volba ``--ident`` omezí výběr na zadané nálezy.

        :param log_objects: Mock ``ApiRequestLog.objects``.
        :param nalez_objects: Mock ``SamostatnyNalez.objects``.
        :param schedule: Mock ``schedule_samostatny_nalez_igsn_retry``.
        :param _atomic: Mock ``transaction.atomic``.
        """
        entries = self._priprav(log_objects, nalez_objects, ROWS[:1], reset_count=2)
        self._spust("--ident", "C-202009779-N00001")

        entries.filter.assert_any_call(samostatny_nalez__ident_cely__in=["C-202009779-N00001"])
        self.assertEqual(schedule.call_count, 1)

    def test_dry_run_changes_nothing(self, log_objects, nalez_objects, schedule, _atomic):
        """
        ``--dry-run`` vypíše dotčené nálezy, ale nic nepřepne ani nenaplánuje.

        :param log_objects: Mock ``ApiRequestLog.objects``.
        :param nalez_objects: Mock ``SamostatnyNalez.objects``.
        :param schedule: Mock ``schedule_samostatny_nalez_igsn_retry``.
        :param _atomic: Mock ``transaction.atomic``.
        """
        entries = self._priprav(log_objects, nalez_objects, ROWS)
        output = self._spust("--dry-run")

        self.assertIn("C-202009779-N00001: 2", output)
        self.assertIn("C-202009779-N00002: 1", output)
        entries.update.assert_not_called()
        schedule.assert_not_called()

    def test_nothing_to_retry(self, log_objects, nalez_objects, schedule, _atomic):
        """
        Bez selhaných záznamů příkaz jen oznámí, že není co opakovat.

        :param log_objects: Mock ``ApiRequestLog.objects``.
        :param nalez_objects: Mock ``SamostatnyNalez.objects``.
        :param schedule: Mock ``schedule_samostatny_nalez_igsn_retry``.
        :param _atomic: Mock ``transaction.atomic``.
        """
        entries = self._priprav(log_objects, nalez_objects, [])
        output = self._spust()

        self.assertIn("Žádné selhané aktualizace IGSN", output)
        entries.update.assert_not_called()
        schedule.assert_not_called()
