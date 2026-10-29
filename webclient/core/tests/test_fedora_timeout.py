"""
Testy timeoutů HTTP požadavků do Fedory (#4454).

Bez timeoutu visel požadavek do zaseknuté Fedory neomezeně dlouho a držel uWSGI worker
i otevřenou DB transakci. Timeout musí dostat každý požadavek a jeho vypršení se musí
převést na výjimku, kterou zachytí existující chybové větve (rollback DB i Fedory).
Zápis obsahu souborů a commit transakce mají delší read timeout, aby upload nespadl.
"""

from unittest import mock

import requests
from core.repository_connector import (
    _CONTENT_REQUEST_TYPES,
    FedoraNoResponseError,
    FedoraRepositoryConnector,
    FedoraRequestType,
    FedoraTransaction,
    FedoraTransactionCommitFailedError,
    FedoraTransactionOperation,
)
from django.test import SimpleTestCase, override_settings
from uzivatel.models import User

TIMEOUTY = {"FEDORA_CONNECT_TIMEOUT": 5.0, "FEDORA_READ_TIMEOUT": 300.0, "FEDORA_CONTENT_READ_TIMEOUT": 3600.0}
URL = "http://fcrepo:8080/rest/AMCR/record/X-M-000023036"


@override_settings(**TIMEOUTY)
class SendRequestTimeoutTest(SimpleTestCase):
    """Testy timeoutu v ``FedoraRepositoryConnector._send_request``."""

    def _make_connector(self):
        record = mock.Mock(ident_cely="X-M-000023036")
        transaction = FedoraTransaction(
            main_record=record, transaction_user=User(ident_cely="U-000001"), uid="fake-txn-uid"
        )
        return FedoraRepositoryConnector(record, transaction=transaction)

    def _send(self, request_type, **session_kwargs):
        """Odešle požadavek přes mockovanou session a vrátí ``(session, výsledek)``."""
        connector = self._make_connector()
        session = mock.Mock(**session_kwargs)
        with mock.patch.object(connector, "_get_session", return_value=session):
            return session, connector._send_request(URL, request_type, data="x")

    def test_metadata_maji_vychozi_timeout(self):
        """Zápis metadat dostane výchozí ``(connect, read)``."""
        session, _ = self._send(FedoraRequestType.UPDATE_METADATA, **{"put.return_value.status_code": 204})
        self.assertEqual(session.put.call_args.kwargs["timeout"], (5.0, 300.0))

    def test_get_ma_vychozi_timeout(self):
        """GET dostane výchozí timeout."""
        session, _ = self._send(FedoraRequestType.GET_METADATA, **{"get.return_value.status_code": 200})
        self.assertEqual(session.get.call_args.kwargs["timeout"], (5.0, 300.0))

    def test_obsah_souboru_ma_dlouhy_timeout(self):
        """
        Každý zápis obsahu (soubor, náhledy, distribuce) dostane ``FEDORA_CONTENT_READ_TIMEOUT``;
        ``CREATE_BINARY_FILE_CONTENT`` měl dřív natvrdo 10 s.
        """
        for request_type in _CONTENT_REQUEST_TYPES:
            with self.subTest(request_type=request_type):
                session, _ = self._send(
                    request_type,
                    **{"post.return_value.status_code": 201, "put.return_value.status_code": 201},
                )
                volani = session.post.call_args or session.put.call_args
                self.assertEqual(volani.kwargs["timeout"], (5.0, 3600.0))

    def test_zalozeni_kontejneru_souboru_nema_dlouhy_timeout(self):
        """``CREATE_BINARY_FILE`` posílá jen RDF s autorem, obsah jde až v ``CREATE_BINARY_FILE_CONTENT``."""
        session, _ = self._send(FedoraRequestType.CREATE_BINARY_FILE, **{"post.return_value.status_code": 201})
        self.assertEqual(session.post.call_args.kwargs["timeout"], (5.0, 300.0))

    def test_mazani_ma_timeout(self):
        """DELETE (dřív bez timeoutu) dostane výchozí timeout."""
        session, _ = self._send(FedoraRequestType.DELETE_CONTAINER, **{"delete.return_value.status_code": 204})
        self.assertEqual(session.delete.call_args.kwargs["timeout"], (5.0, 300.0))

    def test_read_timeout_zapisu_je_fedora_no_response_error(self):
        """
        ``ReadTimeout`` není potomkem ``ConnectionError``; musí přesto skončit jako
        ``FedoraNoResponseError``, aby ho zachytil ``handle_fedora_error`` a ``ErrorMiddleware``.
        """
        with self.assertRaises(FedoraNoResponseError) as ctx:
            self._send(FedoraRequestType.METADATA_UPDATE_RDF_DATA, **{"patch.side_effect": requests.ReadTimeout()})
        self.assertIsNotNone(ctx.exception.fedora_transaction)

    def test_read_timeout_get_vraci_none(self):
        """Vypršení GET se chová jako ostatní síťové chyby GET: výsledek ``None``."""
        _, result = self._send(FedoraRequestType.GET_METADATA, **{"get.side_effect": requests.ReadTimeout()})
        self.assertIsNone(result)

    def test_kontrola_smazani_ma_timeout_a_prevadi_chybu(self):
        """
        Klasifikační kontrola před zápisem nového záznamu posílá vlastní GET mimo ``_send_request``;
        musí mít timeout a vypršení skončit ``FedoraNoResponseError`` místo obecné chyby 500.
        """
        session = mock.Mock(**{"get.side_effect": requests.ReadTimeout()})
        with mock.patch.object(FedoraRepositoryConnector, "_get_session", return_value=session):
            with self.assertLogs("core.repository_connector", level="ERROR"):
                with self.assertRaises(FedoraNoResponseError):
                    FedoraRepositoryConnector.check_container_deleted_or_not_exists("X-M-000023036", "projekt")
        self.assertEqual(session.get.call_args.kwargs["timeout"], (5.0, 300.0))


@override_settings(**TIMEOUTY)
class TransactionRequestTimeoutTest(SimpleTestCase):
    """Testy timeoutu vytvoření, commitu a rollbacku Fedora transakce."""

    def _transaction(self):
        return FedoraTransaction(
            main_record=mock.Mock(ident_cely="X-M-000023036"),
            transaction_user=User(ident_cely="U-000001"),
            uid="fake-txn-uid",
        )

    def _send(self, transaction, operation, session):
        with mock.patch("core.repository_connector._get_fedora_session", return_value=session), mock.patch.object(
            transaction, "_save_transaction_result_to_redis"
        ) as save:
            transaction._send_transaction_request(operation)
        return save

    def test_commit_ma_dlouhy_timeout(self):
        """Commit přesouvá obsah do OCFL, proto má timeout jako zápis obsahu."""
        session = mock.Mock(**{"put.return_value.status_code": 204})
        self._send(self._transaction(), FedoraTransactionOperation.COMMIT, session)
        self.assertEqual(session.put.call_args.kwargs["timeout"], (5.0, 3600.0))

    def test_rollback_ma_vychozi_timeout(self):
        """Rollback dostane výchozí timeout."""
        session = mock.Mock(**{"delete.return_value.status_code": 204})
        self._send(self._transaction(), FedoraTransactionOperation.ROLLBACK, session)
        self.assertEqual(session.delete.call_args.kwargs["timeout"], (5.0, 300.0))

    def test_timeout_commitu_je_commit_failed_error(self):
        """Vypršení commitu skončí ``FedoraTransactionCommitFailedError`` a výsledek se neuloží jako commitnutý."""
        transaction = self._transaction()
        session = mock.Mock(**{"put.side_effect": requests.ReadTimeout("timed out")})
        with mock.patch("core.repository_connector._get_fedora_session", return_value=session), mock.patch.object(
            transaction, "_save_transaction_result_to_redis"
        ) as save, self.assertLogs("core.repository_connector", level="ERROR"):
            with self.assertRaises(FedoraTransactionCommitFailedError):
                transaction._send_transaction_request(FedoraTransactionOperation.COMMIT)
        save.assert_not_called()

    def test_timeout_rollbacku_je_v_chybe_oznacen(self):
        """Selhání rollbacku vyvolá stejnou výjimku jako commit, zpráva ale nese název operace."""
        transaction = self._transaction()
        session = mock.Mock(**{"delete.side_effect": requests.ReadTimeout("timed out")})
        with mock.patch("core.repository_connector._get_fedora_session", return_value=session), self.assertLogs(
            "core.repository_connector", level="ERROR"
        ):
            with self.assertRaisesRegex(FedoraTransactionCommitFailedError, "^ROLLBACK: "):
                transaction._send_transaction_request(FedoraTransactionOperation.ROLLBACK)

    def test_timeout_vytvoreni_transakce_je_fedora_no_response_error(self):
        """Vypršení při zakládání transakce skončí ``FedoraNoResponseError`` jako výpadek spojení."""
        session = mock.Mock(**{"post.side_effect": requests.ReadTimeout()})
        with mock.patch("core.repository_connector._get_fedora_session", return_value=session):
            with self.assertRaises(FedoraNoResponseError):
                FedoraTransaction()
        self.assertEqual(session.post.call_args.kwargs["timeout"], (5.0, 300.0))
