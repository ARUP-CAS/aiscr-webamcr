"""Jednotkové testy opakování aktualizace IGSN samostatného nálezu na pozadí (#4523)."""

from unittest import mock

import requests
from celery.exceptions import Retry
from core.constants import (
    API_REQUEST_LOG_IGSN_STATUS_FAILED,
    API_REQUEST_LOG_IGSN_STATUS_RETRY_PENDING,
    API_REQUEST_LOG_IGSN_STATUS_UPDATED,
    IGSN_RETRY_MAX_DELAY,
    IGSN_RETRY_MAX_RETRIES,
    SN_ARCHIVOVANY,
)
from cron.tasks import (
    IGSN_UPDATE_NON_RETRYABLE,
    IGSN_UPDATE_RETRYABLE,
    IGSN_UPDATE_SUCCESS,
    igsn_retry_delay,
    retry_samostatny_nalez_igsn_update,
    schedule_samostatny_nalez_igsn_retry,
    update_samostatny_nalez_igsn,
)
from django.test import SimpleTestCase
from pid.exceptions import DoiConnectionError, DoiWriteError

SN_PK = 42


def _nalez(stav=SN_ARCHIVOVANY, igsn="10.82442/C-202009779-N00001", side_effect=None):
    """
    Vytvoří mock samostatného nálezu.

    :param stav: Stav nálezu.
    :param igsn: Hodnota IGSN (``None`` = nález bez IGSN).
    :param side_effect: Výjimka, kterou vyhodí ``igsn_update``.

    :return: Mock ``SamostatnyNalez``.
    """
    nalez = mock.Mock(pk=SN_PK, ident_cely="C-202009779-N00001", stav=stav, igsn=igsn)
    nalez.igsn_update.side_effect = side_effect
    return nalez


class UpdateSamostatnyNalezIgsnTest(SimpleTestCase):
    """Ověřuje třídění výsledku aktualizace IGSN na úspěch, opakovatelnou a neopakovatelnou chybu."""

    def _vysledek(self, side_effect):
        """
        Spustí aktualizaci IGSN s danou výjimkou a vrátí její výsledek.

        :param side_effect: Výjimka vyhozená z ``igsn_update`` nebo ``None``.

        :return: Výsledek :func:`update_samostatny_nalez_igsn`.
        """
        nalez = _nalez(side_effect=side_effect)
        outcome, _err = update_samostatny_nalez_igsn(nalez)
        nalez.igsn_update.assert_called_once_with(True, True)
        return outcome

    def test_success(self):
        """Aktualizace bez výjimky je úspěch a volá se s kontrolou stavových kódů."""
        self.assertEqual(self._vysledek(None), IGSN_UPDATE_SUCCESS)

    def test_connection_error_on_existence_check_is_retryable(self):
        """Nedostupné DataCite při ověření existence (síťová chyba i odpověď 5xx) se opakuje."""
        self.assertEqual(self._vysledek(DoiConnectionError(None, "timeout", "url")), IGSN_UPDATE_RETRYABLE)
        self.assertEqual(self._vysledek(DoiConnectionError(503, "down", "url")), IGSN_UPDATE_RETRYABLE)

    def test_network_error_on_update_is_retryable(self):
        """Síťová chyba při zápisu (nezabalená ``requests`` výjimka) se opakuje."""
        self.assertEqual(self._vysledek(requests.ConnectionError("reset")), IGSN_UPDATE_RETRYABLE)

    def test_rate_limit_and_server_errors_are_retryable(self):
        """Odpovědi zápisu 429 a 5xx se opakují."""
        for status_code in (429, 500, 503):
            with self.subTest(status_code=status_code):
                self.assertEqual(self._vysledek(DoiWriteError(status_code, "", "url")), IGSN_UPDATE_RETRYABLE)

    def test_client_errors_are_not_retryable(self):
        """Odpovědi zápisu 4xx včetně 401 a 403 se neopakují."""
        for status_code in (401, 403, 422):
            with self.subTest(status_code=status_code):
                self.assertEqual(self._vysledek(DoiWriteError(status_code, "", "url")), IGSN_UPDATE_NON_RETRYABLE)


class IgsnRetryDelayTest(SimpleTestCase):
    """Ověřuje exponenciálně rostoucí a shora omezenou prodlevu mezi pokusy."""

    def test_delay_doubles_from_base(self):
        """Prodlevy před 1. až 4. pokusem jsou 60, 120, 240 a 480 s."""
        self.assertEqual([igsn_retry_delay(n) for n in range(1, 5)], [60, 120, 240, 480])

    def test_delay_is_capped(self):
        """Žádná prodleva v rámci všech pokusů nepřekročí maximum, poslední pokusy na něm zůstanou."""
        delays = [igsn_retry_delay(n) for n in range(1, IGSN_RETRY_MAX_RETRIES + 2)]
        self.assertLessEqual(max(delays), IGSN_RETRY_MAX_DELAY)
        self.assertEqual(delays[-1], IGSN_RETRY_MAX_DELAY)


@mock.patch("cron.tasks.ApiRequestLog.objects.filter")
@mock.patch("cron.tasks.SamostatnyNalez.objects.filter")
class RetrySamostatnyNalezIgsnUpdateTest(SimpleTestCase):
    """Ověřuje průběh úlohy opakování, plánování dalších pokusů a zápis výsledku do ``ApiRequestLog``."""

    def _spust(self, retries=0):
        """
        Spustí tělo úlohy synchronně s daným počtem již provedených opakování.

        :param retries: Hodnota ``self.request.retries``.
        """
        retry_samostatny_nalez_igsn_update.push_request(retries=retries)
        try:
            retry_samostatny_nalez_igsn_update.run("SamostatnyNalez", SN_PK)
        finally:
            retry_samostatny_nalez_igsn_update.pop_request()

    def _assert_log_status(self, log_filter, igsn_status):
        """
        Ověří, že se čekající záznamy logu nálezu nastavily na daný stav.

        :param log_filter: Mock ``ApiRequestLog.objects.filter``.
        :param igsn_status: Očekávaný nový stav.
        """
        log_filter.assert_called_once_with(
            samostatny_nalez_id=SN_PK, igsn_status=API_REQUEST_LOG_IGSN_STATUS_RETRY_PENDING
        )
        log_filter.return_value.update.assert_called_once_with(igsn_status=igsn_status)

    def test_success_marks_log_updated(self, sn_filter, log_filter):
        """
        Úspěšná aktualizace nastaví čekajícím záznamům stav ``updated`` a neplánuje další pokus.

        :param sn_filter: Mock ``SamostatnyNalez.objects.filter``.
        :param log_filter: Mock ``ApiRequestLog.objects.filter``.
        """
        sn_filter.return_value.first.return_value = _nalez()
        self._spust()
        self._assert_log_status(log_filter, API_REQUEST_LOG_IGSN_STATUS_UPDATED)

    def test_retryable_failure_schedules_retry_with_growing_delay(self, sn_filter, log_filter):
        """
        Opakovatelná chyba naplánuje další pokus s prodlevou dalšího pokusu a log nemění.

        :param sn_filter: Mock ``SamostatnyNalez.objects.filter``.
        :param log_filter: Mock ``ApiRequestLog.objects.filter``.
        """
        sn_filter.return_value.first.return_value = _nalez(side_effect=DoiConnectionError(None, "timeout", "url"))
        for retries, expected in ((0, 120), (1, 240), (2, 480)):
            with self.subTest(retries=retries), mock.patch.object(
                retry_samostatny_nalez_igsn_update, "retry", side_effect=Retry()
            ) as retry:
                with self.assertRaises(Retry):
                    self._spust(retries=retries)
                self.assertEqual(retry.call_args.kwargs["countdown"], expected)
        log_filter.assert_not_called()

    def test_retry_delay_never_exceeds_cap(self, sn_filter, log_filter):
        """
        I u posledního povoleného opakování zůstane prodleva na maximu.

        :param sn_filter: Mock ``SamostatnyNalez.objects.filter``.
        :param log_filter: Mock ``ApiRequestLog.objects.filter``.
        """
        sn_filter.return_value.first.return_value = _nalez(side_effect=DoiWriteError(503, "", "url"))
        with mock.patch.object(retry_samostatny_nalez_igsn_update, "retry", side_effect=Retry()) as retry:
            with self.assertRaises(Retry):
                self._spust(retries=IGSN_RETRY_MAX_RETRIES - 1)
        self.assertEqual(retry.call_args.kwargs["countdown"], IGSN_RETRY_MAX_DELAY)

    def test_non_retryable_failure_stops_and_marks_failed(self, sn_filter, log_filter):
        """
        Neopakovatelná chyba (422) ukončí úlohu bez dalšího pokusu, zaloguje chybu a nastaví ``failed``.

        :param sn_filter: Mock ``SamostatnyNalez.objects.filter``.
        :param log_filter: Mock ``ApiRequestLog.objects.filter``.
        """
        sn_filter.return_value.first.return_value = _nalez(side_effect=DoiWriteError(422, "invalid", "url"))
        with mock.patch.object(retry_samostatny_nalez_igsn_update, "retry") as retry, self.assertLogs(
            "cron.tasks", level="ERROR"
        ) as logs:
            self._spust()
        retry.assert_not_called()
        self.assertIn("retry_samostatny_nalez_igsn_update.failed", logs.output[0])
        self._assert_log_status(log_filter, API_REQUEST_LOG_IGSN_STATUS_FAILED)

    def test_exhausted_retries_stop_and_mark_failed(self, sn_filter, log_filter):
        """
        Po vyčerpání opakování úloha skončí, zaloguje chybu a nastaví ``failed``.

        :param sn_filter: Mock ``SamostatnyNalez.objects.filter``.
        :param log_filter: Mock ``ApiRequestLog.objects.filter``.
        """
        sn_filter.return_value.first.return_value = _nalez(side_effect=DoiConnectionError(None, "timeout", "url"))
        with mock.patch.object(retry_samostatny_nalez_igsn_update, "retry") as retry, self.assertLogs(
            "cron.tasks", level="ERROR"
        ):
            self._spust(retries=IGSN_RETRY_MAX_RETRIES)
        retry.assert_not_called()
        self._assert_log_status(log_filter, API_REQUEST_LOG_IGSN_STATUS_FAILED)

    def test_record_not_needing_update_sends_nothing(self, sn_filter, log_filter):
        """
        Smazaný nález, nález mimo SN4 nebo bez IGSN se neodesílá a čekající záznamy dostanou ``failed``.

        :param sn_filter: Mock ``SamostatnyNalez.objects.filter``.
        :param log_filter: Mock ``ApiRequestLog.objects.filter``.
        """
        for nalez in (None, _nalez(stav=SN_ARCHIVOVANY - 1), _nalez(igsn=None)):
            with self.subTest(nalez=nalez):
                sn_filter.return_value.first.return_value = nalez
                log_filter.reset_mock()
                with self.assertLogs("cron.tasks", level="ERROR"):
                    self._spust()
                if nalez is not None:
                    nalez.igsn_update.assert_not_called()
                self._assert_log_status(log_filter, API_REQUEST_LOG_IGSN_STATUS_FAILED)


class ScheduleSamostatnyNalezIgsnRetryTest(SimpleTestCase):
    """Ověřuje plánování úlohy opakování a vynechání, pokud už pro nález čeká."""

    @mock.patch("cron.tasks.retry_samostatny_nalez_igsn_update.apply_async")
    @mock.patch("xml_generator.models.check_if_task_queued", return_value=False)
    def test_schedules_first_attempt_after_base_delay(self, check, apply_async):
        """
        Bez čekající úlohy se naplánuje první pokus s prodlevou 60 s a argumenty ``(class_name, pk)``.

        :param check: Mock ``check_if_task_queued``.
        :param apply_async: Mock ``retry_samostatny_nalez_igsn_update.apply_async``.
        """
        self.assertTrue(schedule_samostatny_nalez_igsn_retry(_nalez()))
        check.assert_called_once_with("SamostatnyNalez", SN_PK, "retry_samostatny_nalez_igsn_update")
        apply_async.assert_called_once_with(["SamostatnyNalez", SN_PK], countdown=60)

    @mock.patch("cron.tasks.retry_samostatny_nalez_igsn_update.apply_async")
    @mock.patch("xml_generator.models.check_if_task_queued", return_value=True)
    def test_skips_when_already_queued(self, _check, apply_async):
        """
        Pokud už úloha pro nález čeká, další se neplánuje.

        :param _check: Mock ``check_if_task_queued``.
        :param apply_async: Mock ``retry_samostatny_nalez_igsn_update.apply_async``.
        """
        self.assertFalse(schedule_samostatny_nalez_igsn_retry(_nalez()))
        apply_async.assert_not_called()

    @mock.patch("cron.tasks.retry_samostatny_nalez_igsn_update.apply_async")
    @mock.patch("xml_generator.models.check_if_task_queued", return_value=False)
    def test_explicit_countdown(self, _check, apply_async):
        """
        Explicitní prodleva (např. 0 pro ruční opakování) se předá beze změny.

        :param _check: Mock ``check_if_task_queued``.
        :param apply_async: Mock ``retry_samostatny_nalez_igsn_update.apply_async``.
        """
        schedule_samostatny_nalez_igsn_retry(_nalez(), countdown=0)
        apply_async.assert_called_once_with(["SamostatnyNalez", SN_PK], countdown=0)
