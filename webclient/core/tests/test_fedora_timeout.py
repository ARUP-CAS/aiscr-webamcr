"""
Testy timeoutů HTTP požadavků do Fedory (#4454).

Bez timeoutu visel požadavek do zaseknuté Fedory neomezeně dlouho a držel uWSGI worker
i otevřenou DB transakci. Timeout musí dostat každý požadavek a jeho vypršení se musí
převést na výjimku, kterou zachytí existující chybové větve (rollback DB i Fedory).
Zápis obsahu souborů a commit transakce mají delší read timeout, aby upload nespadl.
"""

from unittest import mock

import requests
from core.models import Soubor
from core.repository_connector import (
    _CONTENT_REQUEST_TYPES,
    FedoraNoResponseError,
    FedoraRepositoryConnector,
    FedoraRequestType,
    FedoraTransaction,
    FedoraTransactionCommitFailedError,
    FedoraTransactionOperation,
    FedoraTransactionResult,
)
from django.conf import settings
from django.test import SimpleTestCase, override_settings
from uzivatel.models import User

TIMEOUTY = {"FEDORA_CONNECT_TIMEOUT": 10.0, "FEDORA_READ_TIMEOUT": 300.0, "FEDORA_CONTENT_READ_TIMEOUT": 600.0}
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
        self.assertEqual(session.put.call_args.kwargs["timeout"], (10.0, 300.0))

    def test_get_ma_vychozi_timeout(self):
        """GET dostane výchozí timeout."""
        session, _ = self._send(FedoraRequestType.GET_METADATA, **{"get.return_value.status_code": 200})
        self.assertEqual(session.get.call_args.kwargs["timeout"], (10.0, 300.0))

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
                self.assertEqual(volani.kwargs["timeout"], (10.0, 600.0))

    def test_zalozeni_kontejneru_souboru_nema_dlouhy_timeout(self):
        """``CREATE_BINARY_FILE`` posílá jen RDF s autorem, obsah jde až v ``CREATE_BINARY_FILE_CONTENT``."""
        session, _ = self._send(FedoraRequestType.CREATE_BINARY_FILE, **{"post.return_value.status_code": 201})
        self.assertEqual(session.post.call_args.kwargs["timeout"], (10.0, 300.0))

    def test_mazani_ma_timeout(self):
        """DELETE (dřív bez timeoutu) dostane výchozí timeout."""
        session, _ = self._send(FedoraRequestType.DELETE_CONTAINER, **{"delete.return_value.status_code": 204})
        self.assertEqual(session.delete.call_args.kwargs["timeout"], (10.0, 300.0))

    def test_delete_a_patch_overuji_tls_jako_ostatni(self):
        """DELETE a PATCH posílají ``verify=False`` stejně jako ostatní požadavky dispečeru."""
        session, _ = self._send(FedoraRequestType.DELETE_CONTAINER, **{"delete.return_value.status_code": 204})
        self.assertIs(session.delete.call_args.kwargs["verify"], False)
        session, _ = self._send(FedoraRequestType.METADATA_UPDATE_RDF_DATA, **{"patch.return_value.status_code": 204})
        self.assertIs(session.patch.call_args.kwargs["verify"], False)

    def test_read_timeout_zapisu_je_fedora_no_response_error(self):
        """
        ``ReadTimeout`` není potomkem ``ConnectionError``; musí přesto skončit jako
        ``FedoraNoResponseError``, aby ho zachytil ``handle_fedora_error`` a ``ErrorMiddleware``.
        """
        with self.assertRaises(FedoraNoResponseError) as ctx:
            self._send(FedoraRequestType.METADATA_UPDATE_RDF_DATA, **{"patch.side_effect": requests.ReadTimeout()})
        self.assertIsNotNone(ctx.exception.fedora_transaction)

    def test_read_timeout_get_je_fedora_no_response_error(self):
        """
        Vypršení GET skončí ``FedoraNoResponseError`` místo ``None``; s ``None`` volající padali
        na ``AttributeError`` mimo rollback nebo ho brali jako neexistující zdroj.
        """
        with self.assertLogs("core.repository_connector", level="ERROR"):
            with self.assertRaises(FedoraNoResponseError) as ctx:
                self._send(FedoraRequestType.GET_BINARY_FILE_CONTAINER, **{"get.side_effect": requests.ReadTimeout()})
        self.assertIsNotNone(ctx.exception.fedora_transaction)

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
        self.assertEqual(session.get.call_args.kwargs["timeout"], (10.0, 300.0))

    def test_kontrola_smazani_nese_transakci_volajiciho(self):
        """
        Pohledy zakládání záznamu otevřou transakci před kontrolou; chyba ji musí nést,
        aby ``handle_fedora_error`` provedl rollback i ve Fedoře a přesměroval na záznam.
        """
        transaction = self._make_connector().transaction
        session = mock.Mock(**{"get.side_effect": requests.ReadTimeout()})
        with mock.patch.object(FedoraRepositoryConnector, "_get_session", return_value=session):
            with self.assertLogs("core.repository_connector", level="ERROR"):
                with self.assertRaises(FedoraNoResponseError) as ctx:
                    FedoraRepositoryConnector.check_container_deleted_or_not_exists(
                        "X-M-000023036", "projekt", fedora_transaction=transaction
                    )
        self.assertIs(ctx.exception.fedora_transaction, transaction)
        self.assertEqual(ctx.exception.ident_cely, "X-M-000023036")


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
        save = self._send(self._transaction(), FedoraTransactionOperation.COMMIT, session)
        self.assertEqual(session.put.call_args.kwargs["timeout"], (10.0, 600.0))
        save.assert_called_once_with(FedoraTransactionResult.COMMITED)

    def test_odmitnuty_commit_se_neulozi_jako_commitnuty(self):
        """
        Commit, který Fedora odmítne, se v Redisu zapíše jako ``ABORTED``; dřív se ``COMMITED``
        uložilo před kontrolou stavu a uživatel viděl hlášku o úspěšném uložení (#4470).
        """
        transaction = self._transaction()
        session = mock.Mock(**{"put.return_value.status_code": 409, "put.return_value.text": "Conflict"})
        with mock.patch("core.repository_connector._get_fedora_session", return_value=session), mock.patch.object(
            transaction, "_save_transaction_result_to_redis"
        ) as save, self.assertLogs("core.repository_connector", level="ERROR"):
            with self.assertRaises(FedoraTransactionCommitFailedError):
                transaction._send_transaction_request(FedoraTransactionOperation.COMMIT)
        save.assert_called_once_with(FedoraTransactionResult.ABORTED)

    def test_rollback_ma_vychozi_timeout(self):
        """Rollback dostane výchozí timeout."""
        session = mock.Mock(**{"delete.return_value.status_code": 204})
        self._send(self._transaction(), FedoraTransactionOperation.ROLLBACK, session)
        self.assertEqual(session.delete.call_args.kwargs["timeout"], (10.0, 300.0))

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
        self.assertEqual(session.post.call_args.kwargs["timeout"], (10.0, 300.0))


class SouborReadFromFedoraTest(SimpleTestCase):
    """Testy, že výpadek Fedory při čtení náhledu nebo obsahu neshodí vykreslení stránky."""

    def _soubor(self, **patch_kwargs):
        soubor = Soubor(nazev="foto.jpg", path=f"/rest/{settings.FEDORA_SERVER_NAME}/record/X-M-000023036/file/abc")
        return soubor, mock.patch.object(Soubor, "get_repository_content", **patch_kwargs)

    def test_nahled_pri_vypadku_fedory_je_none(self):
        """Náhled se při ``FedoraNoResponseError`` vrátí jako chybějící, detail záznamu se vykreslí."""
        soubor, patch = self._soubor(side_effect=FedoraNoResponseError(URL, "timed out", None))
        with patch, self.assertLogs("core.models", level="WARNING"):
            self.assertIsNone(soubor.small_thumbnail)
            self.assertIsNone(soubor.large_thumbnail)
            self.assertIsNone(soubor.content_file_response)

    def test_jina_chyba_neni_potlacena(self):
        """Potlačí se jen nedostupnost Fedory, ostatní chyby dál propadnou."""
        soubor, patch = self._soubor(side_effect=ValueError("bug"))
        with patch, self.assertRaises(ValueError):
            soubor.read_from_fedora(soubor.get_repository_content, thumb_small=True)


class HistorieFedoraVypadekTest(SimpleTestCase):
    """Testy, že výpadek Fedory neshodí stránku historie ani stažení historické verze."""

    def test_tabulka_historie_bez_fedory(self):
        """Stránka historie se při výpadku Fedory vykreslí bez tabulky verzí z Fedory."""
        from historie.views import HistorieListView

        record = mock.Mock(**{"get_historicke_verze.side_effect": FedoraNoResponseError(URL, "timed out", None)})
        view = HistorieListView()
        view.fedora_model = mock.Mock(**{"objects.get.return_value": record})
        context = {"ident_cely": "X-M-000023036"}
        with self.assertLogs("historie.views", level="WARNING"):
            view.add_fedora_history(context)
        self.assertNotIn("fedora_table", context)

    def test_stazeni_historickych_metadat_bez_fedory_je_404(self):
        """Stažení historických metadat skončí při výpadku Fedory 404 místo chyby 500."""
        from core.views import StahnoutDataHistorickaView
        from django.http import Http404

        record = mock.Mock(**{"get_metadata_historicka.side_effect": FedoraNoResponseError(URL, "timed out", None)})
        model = mock.Mock(**{"objects.get.return_value": record})
        with mock.patch.dict(StahnoutDataHistorickaView.MODEL_MAP, {"Projekt": model}):
            with self.assertLogs("core.views", level="WARNING"), self.assertRaises(Http404):
                StahnoutDataHistorickaView().get(None, "Projekt", "X-M-000023036", "20260101000000")

    def test_stazeni_historickeho_souboru_bez_obsahu_je_404(self):
        """Když ``get_soubor_historicky`` vrátí ``None`` (chybějící verze, výpadek Fedory), view vrátí 404."""
        from core.views import StahnoutDataHistorickaView
        from django.http import Http404

        record = mock.Mock(**{"get_soubor_historicky.return_value": None})
        model = mock.Mock(**{"objects.get.return_value": record})
        with mock.patch.dict(StahnoutDataHistorickaView.MODEL_MAP, {"Soubor": model}):
            with self.assertRaises(Http404):
                StahnoutDataHistorickaView().get(None, "Soubor", "1", "20260101000000")
