"""
Testy větvení podle výsledku ``delete()`` ve views ``dj.smazat``, ``dokument.smazat`` a ``adb.smazat_vb`` (#4453, PR #4520).

Django vrací z ``Model.delete()`` dvojici ``(počet smazaných řádků, detail)``, která je vždy pravdivá.
Views proto musí větvit podle počtu smazaných řádků: při nule se odvolá Fedora transakce a smazání
se nepovažuje za úspěšné, jinak se commit Fedory odloží do ``transaction.on_commit``.
DB i Fedora jsou mockované, testy nepotřebují běžící databázi ani Fedoru.
"""

import json
from unittest import mock

from adb import views as adb_views
from dj import views as dj_views
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, SimpleTestCase
from dokument import views as dokument_views


def _post_request():
    request = RequestFactory().post("/")
    request.user = mock.Mock(is_authenticated=True)
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


def _transaction_mock():
    """Mock ``django.db.transaction`` s ``atomic()``, který nepotlačuje výjimky."""
    transaction = mock.MagicMock()
    transaction.atomic.return_value.__exit__.return_value = False
    return transaction


class DjSmazatDeletedCountTests(SimpleTestCase):
    """View ``dj.smazat``: větvení podle počtu smazaných řádků."""

    def _run(self, deleted_count):
        dj = mock.MagicMock()
        dj.delete.return_value = (deleted_count, {})
        dj.archeologicky_zaznam.get_absolute_url.return_value = "/zaznam"
        fedora_transaction = dj.archeologicky_zaznam.create_transaction.return_value
        transaction = _transaction_mock()
        with mock.patch.object(dj_views, "get_object_or_404", return_value=dj), mock.patch.object(
            dj_views, "update_all_katastr_within_akce_or_lokalita"
        ), mock.patch.object(dj_views, "transaction", transaction):
            response = dj_views.smazat(_post_request(), "DJ-TEST")
        return response, fedora_transaction, transaction

    def test_deleted_schedules_close_after_commit(self):
        """Smazaný řádek: commit Fedory se odloží do ``on_commit``, rollback se nevolá."""
        response, fedora_transaction, transaction = self._run(1)
        self.assertEqual(response.status_code, 200)
        transaction.on_commit.assert_called_once_with(fedora_transaction.mark_transaction_as_closed)
        fedora_transaction.rollback_transaction.assert_not_called()

    def test_nothing_deleted_rolls_back(self):
        """Nula smazaných řádků: odvolá se Fedora transakce, odpověď 403, commit se neplánuje."""
        response, fedora_transaction, transaction = self._run(0)
        self.assertEqual(response.status_code, 403)
        fedora_transaction.rollback_transaction.assert_called_once()
        transaction.on_commit.assert_not_called()


class DokumentSmazatDeletedCountTests(SimpleTestCase):
    """View ``dokument.smazat``: větvení podle počtu smazaných řádků."""

    def _run(self, deleted_count):
        dokument = mock.MagicMock()
        dokument.delete.return_value = (deleted_count, {})
        dokument.casti.all.return_value = []
        fedora_transaction = dokument.create_transaction.return_value
        transaction = _transaction_mock()
        with mock.patch.object(dokument_views, "get_object_or_404", return_value=dokument), mock.patch.object(
            dokument_views, "check_stav_changed", return_value=False
        ), mock.patch.object(dokument_views, "transaction", transaction), mock.patch.object(
            dokument_views, "get_detail_json_view", return_value="/detail"
        ):
            response = dokument_views.smazat(_post_request(), "D-TEST")
        return response, fedora_transaction, transaction

    def test_deleted_schedules_close_after_commit(self):
        """Smazaný řádek: commit Fedory se odloží do ``on_commit``, rollback DB se nenastavuje."""
        response, fedora_transaction, transaction = self._run(1)
        self.assertEqual(response.status_code, 200)
        transaction.on_commit.assert_called_once_with(fedora_transaction.mark_transaction_as_closed)
        transaction.set_rollback.assert_not_called()

    def test_nothing_deleted_rolls_back(self):
        """Nula smazaných řádků: odvolá se Fedora i DB transakce a commit se neplánuje."""
        response, fedora_transaction, transaction = self._run(0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"redirect": "/detail"})
        fedora_transaction.rollback_transaction.assert_called_once()
        transaction.set_rollback.assert_called_once_with(True)
        transaction.on_commit.assert_not_called()


class AdbSmazatVbDeletedCountTests(SimpleTestCase):
    """View ``adb.smazat_vb``: větvení podle počtu smazaných řádků."""

    def _run(self, deleted_count):
        vyskovy_bod = mock.MagicMock()
        vyskovy_bod.delete.return_value = (deleted_count, {})
        fedora_transaction = mock.Mock()
        transaction = _transaction_mock()
        with mock.patch.object(adb_views, "get_object_or_404", return_value=vyskovy_bod), mock.patch.object(
            adb_views, "FedoraTransaction", return_value=fedora_transaction
        ), mock.patch.object(adb_views, "transaction", transaction):
            response = adb_views.smazat_vb(_post_request(), "VB-TEST")
        return response, fedora_transaction, transaction

    def test_deleted_schedules_close_after_commit(self):
        """Smazaný řádek: commit Fedory se odloží do ``on_commit``, rollback se nevolá."""
        response, fedora_transaction, transaction = self._run(1)
        self.assertEqual(response.status_code, 200)
        transaction.on_commit.assert_called_once_with(fedora_transaction.mark_transaction_as_closed)
        fedora_transaction.rollback_transaction.assert_not_called()

    def test_nothing_deleted_rolls_back(self):
        """Nula smazaných řádků: odvolá se Fedora transakce, odpověď 403, commit se neplánuje."""
        response, fedora_transaction, transaction = self._run(0)
        self.assertEqual(response.status_code, 403)
        fedora_transaction.rollback_transaction.assert_called_once()
        transaction.on_commit.assert_not_called()
