"""
Testy pořadí kroků při obnově po chybě Fedory ve views ``smazat`` a ``odpojit`` (issue #4453, review PR #4520, O1).

Kompenzace DOI/IGSN čte z DB (``refresh_from_db``), proto se ``transaction.set_rollback(True)`` smí zavolat
až po ní, jinak Django další dotaz v téže transakci odmítne (``TransactionManagementError``).
DB i Fedora jsou mockované, testy nepotřebují běžící databázi ani Fedoru.
"""

from unittest import mock

from arch_z.models import ArcheologickyZaznam
from core.repository_connector import FedoraTransactionCommitFailedError
from django.test import RequestFactory, SimpleTestCase
from dokument import views


def _fedora_error():
    return FedoraTransactionCommitFailedError("chyba", url="url", code=500, headers={})


def _post_request():
    request = RequestFactory().post("/")
    request.user = mock.Mock(is_authenticated=True)
    return request


def _transaction_mock():
    """Mock ``django.db.transaction`` s ``atomic()``, který nepotlačuje výjimky."""
    transaction = mock.MagicMock()
    transaction.atomic.return_value.__exit__.return_value = False
    return transaction


class SmazatRecoveryOrderTests(SimpleTestCase):
    """View ``smazat``: kompenzace DOI proběhne před ``set_rollback(True)``."""

    def test_doi_compensation_before_set_rollback(self):
        """Po chybě Fedory proběhne rollback Fedory, kompenzace DOI a teprve potom ``set_rollback(True)``."""
        dokument = mock.MagicMock()
        dokument.doi_delete.side_effect = _fedora_error()
        fedora_transaction = mock.Mock()
        dokument.create_transaction.return_value = fedora_transaction
        transaction = _transaction_mock()
        order = mock.Mock()
        order.attach_mock(fedora_transaction.rollback_transaction, "fedora_rollback")
        order.attach_mock(dokument.doi_update, "doi_update")
        order.attach_mock(transaction.set_rollback, "set_rollback")
        with (
            mock.patch.object(views, "get_object_or_404", return_value=dokument),
            mock.patch.object(views, "check_stav_changed", return_value=False),
            mock.patch.object(views, "transaction", transaction),
            mock.patch.object(views, "get_detail_json_view", return_value="/detail"),
        ):
            response = views.smazat(_post_request(), "D-TEST")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            order.mock_calls,
            [mock.call.fedora_rollback(), mock.call.doi_update(False, True), mock.call.set_rollback(True)],
        )


class OdpojitRecoveryOrderTests(SimpleTestCase):
    """View ``odpojit``: kompenzace IGSN a DOI proběhne před ``set_rollback(True)``."""

    def test_igsn_and_doi_compensation_before_set_rollback(self):
        """Po chybě Fedory proběhne rollback Fedory, kompenzace IGSN a DOI a teprve potom ``set_rollback(True)``."""
        zaznam = mock.Mock(spec=ArcheologickyZaznam)
        zaznam.typ_zaznamu = ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
        zaznam.stav = views.AZ_STAV_ARCHIVOVANY
        zaznam.lokalita = mock.MagicMock()
        zaznam.get_absolute_url.return_value = "/zaznam"
        dokument_cast = mock.MagicMock()
        dokument_cast.dokument.stav = views.D_STAV_ARCHIVOVANY
        dokument_cast.delete.side_effect = _fedora_error()
        casti = mock.MagicMock()
        casti.__len__.return_value = 2
        casti.filter.return_value.__len__.return_value = 1
        casti.filter.return_value.first.return_value = dokument_cast
        fedora_transaction = mock.Mock()
        transaction = _transaction_mock()
        order = mock.Mock()
        order.attach_mock(fedora_transaction.rollback_transaction, "fedora_rollback")
        order.attach_mock(zaznam.lokalita.igsn_update, "igsn_update")
        order.attach_mock(dokument_cast.dokument.doi_update, "doi_update")
        order.attach_mock(transaction.set_rollback, "set_rollback")
        with (
            mock.patch.object(views.DokumentCast, "objects", mock.Mock(filter=mock.Mock(return_value=casti))),
            mock.patch.object(views, "FedoraTransaction", return_value=fedora_transaction),
            mock.patch.object(views, "transaction", transaction),
        ):
            response = views.odpojit(_post_request(), "D-TEST", "C-TEST", zaznam)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            order.mock_calls,
            [
                mock.call.fedora_rollback(),
                mock.call.igsn_update(False, True),
                mock.call.doi_update(False, True),
                mock.call.set_rollback(True),
            ],
        )
