"""
Testy jednotného odvozování URL kontejneru binárního souboru ve ``FedoraRepositoryConnector`` (issue #4302).

URL kontejneru ``{base}/record/{ident_cely}/file/{uuid}`` se předává do ``RepositoryBinaryFile`` a z ní se
odvozuje ``Soubor.path`` (``url_without_domain``) i ``uuid``. Všechny cesty (``save_binary_file``,
``migrate_binary_file``, ``get_binary_file``, ``update_binary_file``) ji musí sestavovat stejně - přes
``_get_binary_file_container_url`` z nastavení, ne z odpovědi Fedory.
"""

import hashlib
import io
import os
import tempfile
from unittest import mock

from core.repository_connector import FedoraError, FedoraRepositoryConnector, FedoraRequestType, FedoraTransaction
from django.test import SimpleTestCase, override_settings
from uzivatel.models import User

IDENT_CELY = "C-202500001"
IDENT_CELY_OLD = "X-C-000000001"
UUID = "0f2c9d1e-6a4b-4c7e-9f3a-2b8d5e1c7a90"
EXPECTED_PATH = f"rest/AMCR/record/{IDENT_CELY}/file/{UUID}"


class _FakeSoubor:
    """Duck-typed náhrada za ``Soubor`` pro ``migrate_binary_file`` bez reálné Fedory a DB."""

    def __init__(self, path="/tmp/neexistuje"):
        self.nazev = "foto.jpg"
        self.pk = 1
        self.suppress_signal = False
        self.path = path

    @property
    def repository_uuid(self):
        return None

    def save(self):
        pass


@override_settings(
    FEDORA_PROTOCOL="http", FEDORA_SERVER_HOSTNAME="fcrepo", FEDORA_PORT_NUMBER=8080, FEDORA_SERVER_NAME="AMCR"
)
class BinaryFileContainerUrlTests(SimpleTestCase):
    """Ověřuje, že všechny cesty vytvářející ``RepositoryBinaryFile`` dávají shodné ``url_without_domain`` i ``uuid``."""

    def _make_connector(self, ident_cely=IDENT_CELY):
        record = mock.Mock(ident_cely=ident_cely)
        transaction_user = User(ident_cely="U-000001")
        transaction = FedoraTransaction(main_record=record, transaction_user=transaction_user, uid="fake-txn-uid")
        return FedoraRepositoryConnector(record, transaction=transaction)

    def _fedora_create_response(self, connector, authority="http://fcrepo:8080"):
        return mock.Mock(text=f"{authority}/rest/AMCR/record/{connector.record.ident_cely}/file/{UUID}")

    def _save(self, connector, fedora_response):
        with (
            mock.patch.object(connector, "_check_binary_file_container"),
            mock.patch.object(connector, "_update_creator"),
            mock.patch.object(connector, "_send_request", return_value=fedora_response),
        ):
            return connector.save_binary_file("foto.jpg", "image/jpeg", io.BytesIO(b"data"), save_thumbs=False)

    def _migrate(self, connector, soubor, fedora_response):
        with (
            mock.patch.object(connector, "_check_binary_file_container"),
            mock.patch.object(connector, "_send_request", return_value=fedora_response),
        ):
            connector.migrate_binary_file(soubor, include_content=False, check_if_exists=False)
        return soubor

    def test_all_paths_agree(self):
        """``save``, ``migrate``, ``get`` i ``update`` dají pro totéž uuid shodnou cestu i uuid."""
        connector = self._make_connector()
        fedora_response = self._fedora_create_response(connector)

        saved = self._save(connector, fedora_response)
        migrated = self._migrate(connector, _FakeSoubor(), fedora_response)
        with mock.patch.object(connector, "_send_request", return_value=mock.Mock(content=b"data")):
            fetched = connector.get_binary_file(UUID)
        with mock.patch.object(connector, "_send_request"):
            updated = connector.update_binary_file("foto.jpg", "image/jpeg", io.BytesIO(b"data"), UUID, False)

        for rep_bin_file in (saved, fetched, updated):
            self.assertEqual(rep_bin_file.url_without_domain, EXPECTED_PATH)
            self.assertEqual(rep_bin_file.uuid, UUID)
        self.assertEqual(migrated.path, EXPECTED_PATH)

    def test_fedora_reporting_other_authority_does_not_change_path(self):
        """Když Fedora (např. za proxy) vrátí jinou autoritu, ``Soubor.path`` se nemění a nic se nezaloguje."""
        connector = self._make_connector()
        fedora_response = self._fedora_create_response(connector, authority="https://proxy.example.org")

        with self.assertNoLogs("core.repository_connector", level="WARNING"):
            saved = self._save(connector, fedora_response)
            migrated = self._migrate(connector, _FakeSoubor(), fedora_response)

        self.assertEqual(saved.url, f"http://fcrepo:8080/{EXPECTED_PATH}")
        self.assertEqual(migrated.path, EXPECTED_PATH)

    def test_fedora_reporting_other_path_raises(self):
        """Když Fedora vytvoří zdroj na jiné cestě, vyvolá se ``FedoraError`` a ``Soubor.path`` se nepřepíše."""
        connector = self._make_connector()
        fedora_response = mock.Mock(text=f"http://fcrepo:8080/rest/JINY/record/{IDENT_CELY}/file/{UUID}")
        soubor = _FakeSoubor(path="puvodni")

        with self.assertLogs("core.repository_connector", level="ERROR"):
            with self.assertRaises(FedoraError):
                self._save(connector, fedora_response)
            with self.assertRaises(FedoraError):
                self._migrate(connector, soubor, fedora_response)

        self.assertEqual(soubor.path, "puvodni")

    def test_migrate_new_file_with_content_hashes_raw_bytes(self):
        """Soubor, který ještě není ve Fedoře, se migruje i s obsahem a hash se spočítá z jeho bajtů."""
        connector = self._make_connector()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"data")
        self.addCleanup(os.remove, tmp.name)
        soubor = _FakeSoubor(path=tmp.name)

        with (
            mock.patch.object(connector, "_check_binary_file_container"),
            mock.patch.object(connector, "_update_creator"),
            mock.patch.object(connector, "save_thumbs"),
            mock.patch.object(connector, "_send_request", return_value=self._fedora_create_response(connector)) as send,
        ):
            migrated = connector.migrate_binary_file(soubor, include_content=True, check_if_exists=False)

        content_headers = send.call_args_list[-1].kwargs["headers"]
        self.assertEqual(content_headers["Digest"], f"sha-512={hashlib.sha512(b'data').hexdigest()}")
        self.assertEqual(migrated.url_without_domain, EXPECTED_PATH)
        self.assertEqual(soubor.path, EXPECTED_PATH)

    def test_get_binary_file_version_with_old_ident_reads_old_record(self):
        """Historická verze se stahuje ze stejného záznamu, jaký nese vrácený ``RepositoryBinaryFile``."""
        connector = self._make_connector()

        with mock.patch.object(connector, "_send_request", return_value=mock.Mock(content=b"data")) as send:
            fetched = connector.get_binary_file(UUID, ident_cely_old=IDENT_CELY_OLD, timestamp="20250101000000")

        self.assertEqual(
            send.call_args.args[0],
            f"http://fcrepo:8080/rest/AMCR/record/{IDENT_CELY_OLD}/file/{UUID}/orig/fcr:versions/20250101000000",
        )
        self.assertEqual(fetched.url_without_domain, f"rest/AMCR/record/{IDENT_CELY_OLD}/file/{UUID}")

    def test_save_thumbs_with_old_ident_targets_old_record_only(self):
        """Kontrola existence, zápis náhledu i úprava jeho metadat míří při ``ident_cely_old`` na starý záznam."""
        connector = self._make_connector()
        old_record_prefix = f"http://fcrepo:8080/rest/AMCR/record/{IDENT_CELY_OLD}/file/{UUID}/"
        source_thumbs = {True: b"large", False: b"small"}

        with (
            mock.patch.object(connector, "_send_request", return_value=mock.Mock(content=b"thumb")) as send,
            mock.patch.object(connector, "_get_creator", return_value=None),
        ):
            connector.save_thumbs(
                "foto.jpg",
                io.BytesIO(b"data"),
                UUID,
                update=True,
                ident_cely_old=IDENT_CELY_OLD,
                source_thumbs=source_thumbs,
            )

        urls = [call.args[0] for call in send.call_args_list]
        self.assertTrue(urls)
        for url in urls:
            self.assertTrue(url.startswith(old_record_prefix), url)
        request_types = {call.args[1] for call in send.call_args_list}
        self.assertIn(FedoraRequestType.UPDATE_BINARY_FILE_CONTENT_THUMB, request_types)
        self.assertIn(FedoraRequestType.UPDATE_BINARY_FILE_CONTENT_THUMB_LARGE, request_types)
        self.assertNotIn(FedoraRequestType.CREATE_BINARY_FILE_THUMB, request_types)
        self.assertNotIn(FedoraRequestType.CREATE_BINARY_FILE_THUMB_LARGE, request_types)

    def test_get_binary_file_with_old_ident_replaces_only_record_segment(self):
        """Starý identifikátor se dosadí jen do segmentu záznamu, ne do všech výskytů v URL."""
        uuid = f"{IDENT_CELY}-suffix"
        connector = self._make_connector()

        with mock.patch.object(connector, "_send_request", return_value=mock.Mock(content=b"data")) as send:
            fetched = connector.get_binary_file(uuid, ident_cely_old=IDENT_CELY_OLD)

        self.assertEqual(
            send.call_args.args[0], f"http://fcrepo:8080/rest/AMCR/record/{IDENT_CELY_OLD}/file/{uuid}/orig"
        )
        self.assertEqual(fetched.url_without_domain, f"rest/AMCR/record/{IDENT_CELY_OLD}/file/{uuid}")
        self.assertEqual(fetched.uuid, uuid)
