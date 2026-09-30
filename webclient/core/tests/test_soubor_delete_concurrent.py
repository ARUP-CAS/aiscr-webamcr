"""
Testy souběžného mazání souboru (issue #4174).

Když se stejný soubor smaže ve dvou oknech téměř současně, druhý (pomalejší) request narazí
ve Fedoře na už smazaný zdroj a dostane chybovou odpověď mimo 2xx/409 (v hlášeném případě 403).
Konektor ji ověří dotazem mimo transakci a pokud soubor opravdu chybí (404/410), vyvolá
``FedoraBinaryFileAlreadyDeletedError`` bez ERROR logu; ostatní chyby zůstávají ``FedoraError``.
Views ``delete_file_DZ`` a ``delete_file`` novou výjimku ošetří odpovědí 400, obecnou ``FedoraError``
propustí dál a výjimka vždy opustí ``transaction.atomic`` blok, aby se odrolovalo smazání v DB.
DB i Fedora jsou mockované, testy nepotřebují běžící databázi ani Fedoru.
"""

import json
from unittest import mock

import requests
from core.repository_connector import (
    FedoraBinaryFileAlreadyDeletedError,
    FedoraError,
    FedoraRepositoryConnector,
    FedoraTransaction,
    FedoraTransactionStatus,
    FedoraUpdatedByAnotherTransactionError,
)
from core.views import delete_file, delete_file_DZ
from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, SimpleTestCase
from uzivatel.models import User


class _RecordingAtomic:
    """Náhrada za ``transaction.atomic`` – zaznamená výjimku, se kterou se opouští blok, a nepotlačí ji."""

    def __init__(self):
        self.exit_exc_type = None

    def __call__(self, *args, **kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.exit_exc_type = exc_type
        return False


class _DeleteViewTestMixin:
    """Společné sestavení requestu a mocků pro testy mazacích views."""

    url = "/soubor/smazat/projekt/X-M-000023036/834816"

    def _soubor(self):
        soubor = mock.Mock()
        soubor.pk = 834816
        soubor.vazba.navazany_objekt = mock.Mock(ident_cely="X-M-000023036")
        return soubor

    def _request(self):
        request = RequestFactory().post(self.url)
        request.user = mock.Mock(is_authenticated=True, pk=1)
        request.session = {"session_uuid": "abc"}
        request._messages = FallbackStorage(request)
        return request

    def _run(self, view, delete_method, delete_side_effect=None):
        soubor = self._soubor()
        request = self._request()
        ft = mock.Mock(uid="tx1", status=FedoraTransactionStatus.ACTIVE)
        connector = mock.Mock()
        if delete_side_effect is not None:
            getattr(connector, delete_method).side_effect = delete_side_effect
        session_identifier = mock.Mock()
        session_identifier.get_ident.return_value = "X-M-000023036"
        session_identifier.file_exists.return_value = True
        atomic = _RecordingAtomic()
        self.last_request, self.last_atomic = request, atomic
        soubor_model = mock.Mock()
        soubor_model.objects.filter.return_value.exists.return_value = False
        with mock.patch("core.views.SessionIdentifier", return_value=session_identifier), mock.patch(
            "core.views.get_object_or_404", return_value=soubor
        ), mock.patch("core.views.check_soubor_vazba"), mock.patch(
            "core.views.FedoraTransaction", return_value=ft
        ), mock.patch(
            "core.views.FedoraRepositoryConnector", return_value=connector
        ), mock.patch(
            "core.views.transaction.atomic", atomic
        ), mock.patch(
            "core.views.Soubor", soubor_model
        ):
            response = view(request, "projekt", "X-M-000023036", 834816)
        return response, soubor, ft, connector, atomic


class DeleteFileDZViewTest(_DeleteViewTestMixin, SimpleTestCase):
    """Testy řídicího toku view ``delete_file_DZ`` (POST) – úspěch a chybové větve."""

    def _run_dz(self, delete_side_effect=None):
        return self._run(delete_file_DZ, "delete_binary_file_completely", delete_side_effect)

    def test_post_success(self):
        """Úspěšné smazání: JSON success, transakce se uzavře commitem."""
        response, soubor, ft, connector, atomic = self._run_dz()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)["success"])
        soubor.delete.assert_called_once()
        connector.delete_binary_file_completely.assert_called_once_with(soubor)
        ft.mark_transaction_as_closed.assert_called_once()
        ft.rollback_transaction.assert_not_called()

    def test_post_another_transaction_error(self):
        """409 z Fedory: JSON success=False 400, rollback a odrolování smazání v DB."""
        err = FedoraUpdatedByAnotherTransactionError("url", "conflict", 409)
        response, soubor, ft, connector, atomic = self._run_dz(delete_side_effect=err)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(json.loads(response.content)["success"])
        ft.rollback_transaction.assert_called_once()
        self.assertIs(atomic.exit_exc_type, FedoraUpdatedByAnotherTransactionError)

    def test_post_already_deleted(self):
        """Soubor mezitím smazal souběžný request: JSON success=False 400, ne 500, DB smazání odrolováno."""
        err = FedoraBinaryFileAlreadyDeletedError("url", "Forbidden", 403)
        with self.assertNoLogs("core.views", level="ERROR"):
            response, soubor, ft, connector, atomic = self._run_dz(delete_side_effect=err)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(json.loads(response.content)["success"])
        ft.rollback_transaction.assert_called_once()
        self.assertIs(atomic.exit_exc_type, FedoraBinaryFileAlreadyDeletedError)

    def test_post_other_fedora_error_propagates(self):
        """Jiná chyba Fedory se nemaskuje: výjimka projde ven a opustí atomic blok (rollback DB)."""
        err = FedoraError("url", "Unauthorized", 401)
        with self.assertRaises(FedoraError):
            self._run_dz(delete_side_effect=err)
        self.assertIs(self.last_atomic.exit_exc_type, FedoraError)


class DeleteFileViewTest(_DeleteViewTestMixin, SimpleTestCase):
    """Testy řídicího toku view ``delete_file`` (POST) – úspěch a chybové větve."""

    def _run_file(self, delete_side_effect=None):
        return self._run(delete_file, "delete_binary_file", delete_side_effect)

    def test_post_success(self):
        """Úspěšné smazání: JSON s přesměrováním, transakce se uzavře commitem."""
        response, soubor, ft, connector, atomic = self._run_file()
        self.assertEqual(response.status_code, 200)
        self.assertIn("redirect", json.loads(response.content))
        connector.delete_binary_file.assert_called_once_with(soubor)
        ft.mark_transaction_as_closed.assert_called_once()
        self.assertIsNone(atomic.exit_exc_type)

    def test_post_another_transaction_error(self):
        """409 z Fedory: JSON success=False 400, rollback a odrolování smazání v DB."""
        err = FedoraUpdatedByAnotherTransactionError("url", "conflict", 409)
        response, soubor, ft, connector, atomic = self._run_file(delete_side_effect=err)
        self.assertEqual(response.status_code, 400)
        ft.rollback_transaction.assert_called_once()
        self.assertIs(atomic.exit_exc_type, FedoraUpdatedByAnotherTransactionError)

    def test_post_already_deleted(self):
        """Soubor mezitím smazal souběžný request: JSON success=False 400, ne 500, bez hlášky o úspěchu."""
        err = FedoraBinaryFileAlreadyDeletedError("url", "Gone", 410)
        with self.assertNoLogs("core.views", level="ERROR"):
            response, soubor, ft, connector, atomic = self._run_file(delete_side_effect=err)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(json.loads(response.content)["success"])
        ft.rollback_transaction.assert_called_once()
        self.assertIs(atomic.exit_exc_type, FedoraBinaryFileAlreadyDeletedError)
        levels = [m.level for m in self.last_request._messages]
        self.assertNotIn(messages.SUCCESS, levels)
        self.assertIn(messages.ERROR, levels)

    def test_post_other_fedora_error_propagates(self):
        """Jiná chyba Fedory se nemaskuje: výjimka projde ven z view."""
        err = FedoraError("url", "Unauthorized", 401)
        with self.assertRaises(FedoraError):
            self._run_file(delete_side_effect=err)
        self.assertIs(self.last_atomic.exit_exc_type, FedoraError)


class DeleteBinaryFileConnectorTest(SimpleTestCase):
    """Testy rozpoznání už smazaného binárního souboru v ``FedoraRepositoryConnector._send_request``."""

    def _make_connector(self):
        record = mock.Mock(ident_cely="X-M-000023036")
        transaction_user = User(ident_cely="U-000001")
        transaction = FedoraTransaction(main_record=record, transaction_user=transaction_user, uid="fake-txn-uid")
        return FedoraRepositoryConnector(record, transaction=transaction)

    def _response(self, status_code):
        return mock.Mock(status_code=status_code, text="HTTP Status %s" % status_code, headers={})

    def _delete(self, method, delete_status, get_status=None, get_side_effect=None):
        """Zavolá mazací metodu konektoru s mockovanou session; poslední session uloží do ``last_session``."""
        connector = self._make_connector()
        soubor = mock.Mock(repository_uuid="f8d0deae-b291-4629-89e4-c60306c902aa", pk=834816)
        session = mock.Mock()
        session.delete.return_value = self._response(delete_status)
        session.patch.return_value = self._response(delete_status)
        if get_side_effect is not None:
            session.get.side_effect = get_side_effect
        else:
            session.get.return_value = self._response(get_status)
        self.last_session = session
        with mock.patch.object(connector, "_get_session", return_value=session), mock.patch.object(
            connector.transaction, "rollback_transaction"
        ) as rollback:
            getattr(connector, method)(soubor)
        return session, rollback

    def test_delete_completely_forbidden_but_gone(self):
        """403 na DELETE a 410 na ověřovací GET: FedoraBinaryFileAlreadyDeletedError bez ERROR logu."""
        with self.assertNoLogs("core.repository_connector", level="ERROR"):
            with self.assertRaises(FedoraBinaryFileAlreadyDeletedError):
                self._delete("delete_binary_file_completely", 403, get_status=410)

    def test_delete_completely_not_found_on_check(self):
        """Ověřovací GET vrátí 404: soubor už není, FedoraBinaryFileAlreadyDeletedError."""
        with self.assertRaises(FedoraBinaryFileAlreadyDeletedError):
            self._delete("delete_binary_file_completely", 403, get_status=404)

    def test_soft_delete_on_gone_file(self):
        """PATCH (``delete_binary_file``) na soubor, který mezitím úplně smazal jiný request."""
        with self.assertRaises(FedoraBinaryFileAlreadyDeletedError):
            self._delete("delete_binary_file", 410, get_status=410)

    def test_delete_forbidden_and_file_exists(self):
        """403 na DELETE, ale soubor ve Fedoře pořád je: obecná FedoraError a ERROR log."""
        with self.assertLogs("core.repository_connector", level="ERROR"):
            with self.assertRaises(FedoraError) as ctx:
                self._delete("delete_binary_file_completely", 403, get_status=200)
        self.assertNotIsInstance(ctx.exception, FedoraBinaryFileAlreadyDeletedError)

    def test_delete_error_and_check_fails(self):
        """Ověřovací GET selže na síti: nelze potvrdit smazání, obecná FedoraError."""
        with self.assertRaises(FedoraError) as ctx:
            self._delete(
                "delete_binary_file_completely", 500, get_side_effect=requests.exceptions.ConnectionError("down")
            )
        self.assertNotIsInstance(ctx.exception, FedoraBinaryFileAlreadyDeletedError)

    def test_check_without_transaction_header(self):
        """Ověřovací GET jde mimo Fedora transakci (bez ``Atomic-ID``), ta je už odvolaná."""
        with self.assertRaises(FedoraBinaryFileAlreadyDeletedError):
            self._delete("delete_binary_file_completely", 403, get_status=410)
        delete_headers = self.last_session.delete.call_args.kwargs["headers"]
        self.assertIn("Atomic-ID", delete_headers)
        get_call = self.last_session.get.call_args
        self.assertEqual(get_call.args[0], self.last_session.delete.call_args.args[0])
        self.assertNotIn("headers", get_call.kwargs)

    def test_conflict_is_not_checked(self):
        """409 zůstává FedoraUpdatedByAnotherTransactionError a ověřovací GET se neposílá."""
        connector = self._make_connector()
        soubor = mock.Mock(repository_uuid="uuid", pk=1)
        session = mock.Mock()
        session.delete.return_value = self._response(409)
        with mock.patch.object(connector, "_get_session", return_value=session), mock.patch.object(
            connector.transaction, "rollback_transaction"
        ):
            with self.assertRaises(FedoraUpdatedByAnotherTransactionError):
                connector.delete_binary_file_completely(soubor)
        session.get.assert_not_called()
