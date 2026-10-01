"""
Testy pro ``FedoraRepositoryConnector.migrate_binary_file`` (issue #4218).

Při schválení projektu se dočasný identifikátor mění na trvalý a každý připojený soubor se
migruje do nového Fedora kontejneru (``core.repository_connector.record_ident_change``).
Náhledy (``thumb``, ``thumb-large``) pro migrovaný soubor už na starém umístění existují, proto
se musí číst stejnou (netransakční) cestou jako originál - přes ``Soubor.get_repository_content``.
Čtení přes ``FedoraRepositoryConnector.get_binary_file`` na transakčním připojení by po smazání
starého kontejneru uvnitř probíhající transakce vracelo 404, a náhledy by se tak zbytečně
přegenerovávaly z obrazových dat.
"""

import io
from unittest import mock

from core.repository_connector import FedoraRepositoryConnector, FedoraTransaction
from django.test import SimpleTestCase
from uzivatel.models import User


class _FakeRepositoryContent:
    """Odlehčená náhrada za ``RepositoryBinaryFile`` vrácenou z Fedory."""

    def __init__(self, data: bytes):
        self.content = io.BytesIO(data)
        self.sha_512 = "fake-sha-512"


class _FakeSoubor:
    """Duck-typed náhrada za ``Soubor`` - ``get_repository_content`` vrací předpřipravený obsah bez reálné Fedory/DB."""

    def __init__(self, nazev, pk, repository_uuid, contents):
        self.nazev = nazev
        self.pk = pk
        self.suppress_signal = False
        self.path = f"record/OLD-IDENT/file/{repository_uuid}/orig"
        self._repository_uuid = repository_uuid
        self._contents = contents  # {(thumb_small, thumb_large): bytes}
        self.saved = False

    @property
    def repository_uuid(self):
        return self._repository_uuid

    def get_repository_content(self, ident_cely_old=None, thumb_small=False, thumb_large=False, timestamp=None):
        data = self._contents.get((thumb_small, thumb_large))
        return _FakeRepositoryContent(data) if data is not None else None

    def save(self):
        self.saved = True


class MigrateBinaryFileThumbSourceTests(SimpleTestCase):
    """Ověřuje, odkud se berou náhledy při migraci souboru na nový identifikátor."""

    def _make_connector(self):
        record = mock.Mock(ident_cely="C-202500001")
        transaction_user = User(ident_cely="U-000001")
        transaction = FedoraTransaction(main_record=record, transaction_user=transaction_user, uid="fake-txn-uid")
        return FedoraRepositoryConnector(record, transaction=transaction)

    def _migrate(self, connector, soubor):
        with (
            mock.patch.object(connector, "_check_binary_file_container"),
            mock.patch.object(connector, "_update_creator"),
            mock.patch.object(connector, "save_thumbs") as mock_save_thumbs,
            mock.patch.object(connector, "get_binary_file") as mock_get_binary_file,
            mock.patch.object(connector, "_send_request") as mock_send_request,
        ):
            mock_send_request.return_value = mock.Mock(
                text=f"{connector.get_base_url()}/record/C-202500001/file/new-uuid"
            )
            connector.migrate_binary_file(
                soubor, include_content=True, check_if_exists=False, ident_cely_old="X-C-000000001"
            )
        return mock_save_thumbs, mock_get_binary_file

    def test_thumbs_are_copied_from_old_location_not_regenerated(self):
        """Náhledy se čtou přes soubor.get_repository_content, transakční get_binary_file se pro ně nesmí volat."""
        connector = self._make_connector()
        soubor = _FakeSoubor(
            "foto.jpg",
            pk=1,
            repository_uuid="old-uuid",
            contents={
                (False, False): b"orig-bytes",
                (False, True): b"large-thumb-bytes",
                (True, False): b"small-thumb-bytes",
            },
        )

        mock_save_thumbs, mock_get_binary_file = self._migrate(connector, soubor)

        mock_get_binary_file.assert_not_called()
        mock_save_thumbs.assert_called_once()
        self.assertEqual(
            mock_save_thumbs.call_args.kwargs["source_thumbs"],
            {True: b"large-thumb-bytes", False: b"small-thumb-bytes"},
        )

    def test_missing_old_thumb_falls_back_to_regeneration(self):
        """Chybějící náhled na starém umístění se předá jako None - save_thumbs jej pak sám přegeneruje."""
        connector = self._make_connector()
        soubor = _FakeSoubor(
            "foto.jpg",
            pk=2,
            repository_uuid="old-uuid-2",
            contents={(False, False): b"orig-bytes", (False, True): b"large-thumb-bytes"},
        )

        mock_save_thumbs, mock_get_binary_file = self._migrate(connector, soubor)

        mock_get_binary_file.assert_not_called()
        self.assertEqual(
            mock_save_thumbs.call_args.kwargs["source_thumbs"],
            {True: b"large-thumb-bytes", False: None},
        )
