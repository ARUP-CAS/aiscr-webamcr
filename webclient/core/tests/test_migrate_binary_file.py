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

from core.repository_connector import FedoraError, FedoraRepositoryConnector, FedoraTransaction
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
        self.recorded_thumb_writes = None

    @property
    def repository_uuid(self):
        return self._repository_uuid

    def get_repository_content(self, ident_cely_old=None, thumb_small=False, thumb_large=False, timestamp=None):
        data = self._contents.get((thumb_small, thumb_large))
        return _FakeRepositoryContent(data) if data is not None else None

    def save(self):
        self.saved = True

    def zaznamenej_distribuce(self, thumb_writes):
        self.recorded_thumb_writes = thumb_writes


class _MigrateBinaryFileTestBase(SimpleTestCase):
    """Společné pomocné metody pro testy migrace souboru; sama žádné testy neobsahuje."""

    def _make_connector(self):
        record = mock.Mock(ident_cely="C-202500001")
        transaction_user = User(ident_cely="U-000001")
        transaction = FedoraTransaction(main_record=record, transaction_user=transaction_user, uid="fake-txn-uid")
        return FedoraRepositoryConnector(record, transaction=transaction)

    def _migrate(self, connector, soubor, thumb_writes=(), children=()):
        with (
            mock.patch.object(
                FedoraRepositoryConnector, "_collect_file_children", return_value=list(children)
            ) as mock_collect_children,
            mock.patch.object(connector, "_save_file_child") as mock_save_file_child,
            mock.patch.object(connector, "_check_binary_file_container"),
            mock.patch.object(connector, "_update_creator"),
            mock.patch.object(connector, "save_thumbs") as mock_save_thumbs,
            mock.patch.object(connector, "get_binary_file") as mock_get_binary_file,
            mock.patch.object(connector, "_send_request") as mock_send_request,
        ):
            mock_save_thumbs.return_value = list(thumb_writes)
            mock_send_request.return_value = mock.Mock(
                text=f"{connector.get_base_url()}/record/C-202500001/file/new-uuid"
            )
            connector.migrate_binary_file(
                soubor, include_content=True, check_if_exists=False, ident_cely_old="X-C-000000001"
            )
        self.mock_collect_children = mock_collect_children
        self.mock_save_file_child = mock_save_file_child
        return mock_save_thumbs, mock_get_binary_file


class MigrateBinaryFileThumbSourceTests(_MigrateBinaryFileTestBase):
    """Ověřuje, odkud se berou náhledy při migraci souboru na nový identifikátor."""

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


class MigrateBinaryFileThumbHistoryTests(_MigrateBinaryFileTestBase):
    """Ověřuje, které náhledy migrovaného souboru se zapíší do historie (issue #3527)."""

    def test_copied_thumbs_are_not_recorded(self):
        """Náhledy zkopírované ze starého umístění jsou přesunem, nový záznam DIST01 nevzniká."""
        connector = self._make_connector()
        soubor = _FakeSoubor(
            "foto.jpg",
            pk=3,
            repository_uuid="old-uuid-3",
            contents={
                (False, False): b"orig-bytes",
                (False, True): b"large-thumb-bytes",
                (True, False): b"small-thumb-bytes",
            },
        )

        self._migrate(connector, soubor, thumb_writes=[("thumb-large", False), ("thumb", False)])

        self.assertEqual(soubor.recorded_thumb_writes, [])

    def test_regenerated_thumb_is_recorded(self):
        """Náhled, který na starém umístění chyběl a vygeneroval se znovu, se zapíše do historie."""
        connector = self._make_connector()
        soubor = _FakeSoubor(
            "foto.jpg",
            pk=4,
            repository_uuid="old-uuid-4",
            contents={(False, False): b"orig-bytes", (False, True): b"large-thumb-bytes"},
        )

        self._migrate(connector, soubor, thumb_writes=[("thumb-large", False), ("thumb", False)])

        self.assertEqual(soubor.recorded_thumb_writes, [("thumb", False)])


class _ChildResponse:
    """Náhrada za ``requests.Response`` pro průchod potomky kontejneru souboru."""

    def __init__(self, status_code=200, text="", content=b"", headers=None):
        self.status_code = status_code
        self.text = text
        self.content = content
        self.headers = headers or {}


class MigrateBinaryFileChildrenTests(_MigrateBinaryFileTestBase):
    """Ověřuje kopírování alternativních distribucí a paradat při změně identifikátoru (issue #3527)."""

    OLD_IDENT = "X-C-000000001"
    OLD_UUID = "old-uuid"

    def _listing(self, parent, *children):
        """Sestaví n-triples výpis ``ldp:contains`` kontejneru.

        :param parent: URL kontejneru.
        :param children: URL potomků.
        :return: Odpověď s výpisem potomků.
        """
        lines = [f"<{parent}> <{FedoraRepositoryConnector.LDP_CONTAINS_PREDICATE}> <{child}> ." for child in children]
        return _ChildResponse(text="\n".join(lines))

    def _metadata(self, filename):
        """Sestaví ``fcr:metadata`` binárního potomka s ``ebucore:filename``.

        :param filename: Název souboru uložený ve Fedoře.
        :return: Odpověď s metadaty.
        """
        return _ChildResponse(text=f'<x> <{FedoraRepositoryConnector.EBUCORE_FILENAME_PREDICATE}> "{filename}" .')

    def _old_file_tree(self, connector):
        """Připraví odpovědi Fedory pro starý kontejner souboru s distribucí i paradaty.

        :param connector: Connector, pro který se staví URL.
        :return: Slovník URL → odpověď; neznámá URL odpoví 404.
        """
        file_url = f"{connector.get_base_url()}/record/{self.OLD_IDENT}/file/{self.OLD_UUID}"
        f = file_url
        return {
            f: self._listing(f, f + "/orig", f + "/thumb", f + "/thumb-large", f + "/ocr", f + "/paradata"),
            f + "/ocr": self._listing(f + "/ocr", f + "/ocr/alto-xml"),
            f + "/ocr/alto-xml/fcr:metadata": self._metadata("scan_XC000000001.xml"),
            f + "/ocr/alto-xml": _ChildResponse(content=b"alto", headers={"Content-Type": "application/xml"}),
            f + "/paradata": self._listing(f + "/paradata", f + "/paradata/ocr"),
            f + "/paradata/ocr": self._listing(f + "/paradata/ocr", f + "/paradata/ocr/alto-xml"),
            f + "/paradata/ocr/alto-xml/fcr:metadata": self._metadata("paradata.json"),
            f
            + "/paradata/ocr/alto-xml": _ChildResponse(content=b"{}", headers={"Content-Type": "application/ld+json"}),
        }

    def test_children_are_collected_from_old_location_without_implicit_containers(self):
        """Projdou se vnořené distribuce i paradata; ``orig`` a náhledy se vynechají."""
        connector = self._make_connector()
        responses = self._old_file_tree(connector)

        def send(url, request_type, **kwargs):
            return responses.get(url, _ChildResponse(status_code=404))

        with mock.patch.object(connector, "_send_request", side_effect=send) as send_mock:
            children = connector._collect_file_children(self.OLD_UUID, self.OLD_IDENT)

        self.assertEqual(
            [(path, filename, content_type, content.read()) for path, filename, content_type, content in children],
            [
                ("ocr/alto-xml", "scan_XC000000001.xml", "application/xml", b"alto"),
                ("paradata/ocr/alto-xml", "paradata.json", "application/ld+json", b"{}"),
            ],
        )
        requested = [call.args[0] for call in send_mock.call_args_list]
        self.assertFalse([url for url in requested if url.rsplit("/", 1)[-1] in ("orig", "thumb", "thumb-large")])

    def test_unavailable_container_raises(self):
        """Nedostupný kontejner zastaví změnu identifikátoru, místo aby se data tiše ztratila."""
        connector = self._make_connector()

        with mock.patch.object(connector, "_send_request", return_value=_ChildResponse(status_code=500)):
            with self.assertRaises(FedoraError):
                connector._collect_file_children(self.OLD_UUID, self.OLD_IDENT)

    def test_children_are_written_to_new_container(self):
        """Potomci se zapíší pod nové UUID se stejnou cestou, MIME typem a názvem s novým identem."""
        connector = self._make_connector()
        soubor = _FakeSoubor("foto.jpg", pk=5, repository_uuid=self.OLD_UUID, contents={(False, False): b"orig-bytes"})
        content = io.BytesIO(b"alto")

        self._migrate(
            connector, soubor, children=[("ocr/alto-xml", "scan_XC000000001.xml", "application/xml", content)]
        )

        self.mock_collect_children.assert_called_once_with(self.OLD_UUID, self.OLD_IDENT)
        self.mock_save_file_child.assert_called_once_with(
            "new-uuid", "ocr/alto-xml", "scan_C202500001.xml", "application/xml", content
        )

    def test_file_without_children_writes_nothing_extra(self):
        """Soubor bez distribucí a paradat se migruje jako dosud."""
        connector = self._make_connector()
        soubor = _FakeSoubor("foto.jpg", pk=6, repository_uuid=self.OLD_UUID, contents={(False, False): b"orig-bytes"})

        self._migrate(connector, soubor)

        self.mock_save_file_child.assert_not_called()
