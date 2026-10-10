"""
Testy zápisu alternativních distribucí a paradat do Fedory (issue #3527).

Pokrývají sestavení URL kontejnerů, zakládání mezilehlých kontejnerů u vnořených názvů,
zakládání PUTem na přesnou URL s hlavičkou ``Overwrite-Tombstone`` u INSERTu a odmítnutí vyhrazených názvů distribucí.
Testy nepotřebují databázi ani běžící Fedoru – využívají odlehčené náhradní objekty
a mock ``_send_request``.
"""

import io
from unittest import mock

from core.repository_connector import (
    NON_RDF_SOURCE_LINK,
    FedoraNoResponseError,
    FedoraRepositoryConnector,
    FedoraRequestType,
    FedoraValidationError,
)
from django.conf import settings
from django.test import SimpleTestCase


class _Response:
    """Náhrada za ``requests.Response`` s textem, obsahem, hlavičkami a stavovým kódem."""

    def __init__(self, text="", status_code=200, content=b"", headers=None):
        self.text = text
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}


class _Record:
    """Náhrada za navázaný záznam – stačí identifikátor pro sestavení URL."""

    def __init__(self, ident_cely):
        self.ident_cely = ident_cely


class DistributionConnectorTestBase(SimpleTestCase):
    """Společná příprava connectoru bez ``__init__`` a pomocné konstanty."""

    IDENT_CELY = "C-DL-202500001"
    UUID = "11111111-2222-3333-4444-555555555555"

    def setUp(self):
        """Připraví connector bez volání ``__init__`` a předpočítá URL kontejneru souboru."""
        # Bypass __init__, which requires a request context and a user.
        self.connector = FedoraRepositoryConnector.__new__(FedoraRepositoryConnector)
        self.connector.record = _Record(self.IDENT_CELY)
        self.connector.transaction = None
        self.connector.transaction_uid = None
        self.connector.user = "U-000001"
        self.file_url = f"{FedoraRepositoryConnector.get_base_url()}/record/{self.IDENT_CELY}/file/{self.UUID}"

    def _file(self, data=b"obsah"):
        """Vrátí binární obsah pro zápis do Fedory."""
        return io.BytesIO(data)


class CreateDistributionMethodTest(DistributionConnectorTestBase):
    """Testy HTTP metody, kterou se zakládají distribuce, paradata a jejich mezilehlé kontejnery."""

    def test_create_requests_are_sent_as_put(self):
        """Zakládání jde PUTem: ``Overwrite-Tombstone`` Fedora respektuje jen u PUT.

        POST se Slugem kolidujícím s tombstonem po DIST10 by obsah uložil pod vygenerovaný
        název a následný zápis creatora na ``…/{distribuce}/fcr:metadata`` by narazil na tombstone.
        """
        for request_type in (
            FedoraRequestType.CREATE_DISTRIBUTION_CONTAINER,
            FedoraRequestType.CREATE_DISTRIBUTION_CONTENT,
        ):
            with self.subTest(request_type=request_type):
                session = mock.MagicMock()
                session.put.return_value = mock.MagicMock(status_code=201, text="", headers={})
                with mock.patch.object(self.connector, "_get_session", return_value=session):
                    self.connector._send_request(
                        f"{self.file_url}/ocr", request_type, headers={"Overwrite-Tombstone": "true"}, data=b"x"
                    )

                session.put.assert_called_once()
                self.assertEqual(session.put.call_args.args[0], f"{self.file_url}/ocr")
                session.post.assert_not_called()

    def test_create_requests_use_admin_identity(self):
        """Přepsání tombstonu Fedora povolí jen ``fedoraAdmin``; běžný uživatel dostane 403."""
        for request_type in (
            FedoraRequestType.CREATE_DISTRIBUTION_CONTAINER,
            FedoraRequestType.CREATE_DISTRIBUTION_CONTENT,
        ):
            with self.subTest(request_type=request_type):
                auth = FedoraRepositoryConnector._get_auth(request_type)
                self.assertEqual(auth.username, settings.FEDORA_ADMIN_USER)


class SaveDistributionTest(DistributionConnectorTestBase):
    """Testy vytvoření nové alternativní distribuce."""

    def test_save_puts_to_exact_distribution_url(self):
        """Distribuce se zakládá PUTem přímo na svou URL, bez Slugu.

        POST se Slugem kolidujícím s tombstonem by Fedora uložila pod vygenerovaný název.
        """
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=201)
        ) as send:
            self.connector.save_distribution(self.UUID, "alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(send.call_count, 1)
        call = send.call_args_list[0]
        self.assertEqual(call.args[0], f"{self.file_url}/alto-xml")
        self.assertEqual(call.args[1], FedoraRequestType.CREATE_DISTRIBUTION_CONTENT)
        self.assertNotIn("Slug", call.kwargs["headers"])

    def test_save_sends_overwrite_tombstone(self):
        """INSERT posílá ``Overwrite-Tombstone``, protože po dřívějším DIST10 zůstal na URL tombstone."""
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=201)
        ) as send:
            self.connector.save_distribution(self.UUID, "alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(send.call_args_list[0].kwargs["headers"]["Overwrite-Tombstone"], "true")

    def test_save_sets_content_headers(self):
        """Zapisují se hlavičky s MIME typem, názvem souboru a kontrolním součtem obsahu."""
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=201)
        ) as send:
            self.connector.save_distribution(self.UUID, "alto-xml", "soubor.xml", "text/xml", self._file(b"data"))

        headers = send.call_args_list[0].kwargs["headers"]
        self.assertEqual(headers["Content-Type"], "text/xml")
        self.assertEqual(headers["Content-Disposition"], b'attachment; filename="soubor.xml"')
        self.assertTrue(headers["Digest"].startswith("sha-512="))
        self.assertEqual(send.call_args_list[0].kwargs["data"], b"data")

    def test_rdf_mimetype_is_stored_as_binary(self):
        """Obsah v RDF serializaci se ukládá jako ``ldp:NonRDFSource``, ne jako RDF zdroj.

        Paradata jsou JSON-LD; bez hlavičky ``Link`` by je Fedora rozparsovala jako RDF a zdroj
        by neměl ``fcr:metadata``, na které míří zápis creatora.
        """
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=201)
        ) as send:
            self.connector.save_distribution(
                self.UUID, "atrium/document-json", "z.jsonld", "application/ld+json", self._file()
            )
            self.connector.update_distribution(
                self.UUID, "atrium/document-json", "z.jsonld", "application/ld+json", self._file()
            )

        for call in (send.call_args_list[-2], send.call_args_list[-1]):
            self.assertEqual(call.kwargs["headers"]["Link"], NON_RDF_SOURCE_LINK)

    def test_save_nested_creates_missing_parent_container(self):
        """U vnořeného názvu se chybějící mezilehlý kontejner nejprve založí."""
        responses = [_Response(status_code=404), _Response(status_code=201), _Response(status_code=201)]
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", side_effect=responses
        ) as send:
            self.connector.save_distribution(self.UUID, "ocr/alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(send.call_count, 3)
        self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/ocr")
        self.assertEqual(send.call_args_list[0].args[1], FedoraRequestType.GET_DISTRIBUTION_CONTAINER)
        container_call = send.call_args_list[1]
        self.assertEqual(container_call.args[0], f"{self.file_url}/ocr")
        self.assertEqual(container_call.args[1], FedoraRequestType.CREATE_DISTRIBUTION_CONTAINER)
        self.assertNotIn("Slug", container_call.kwargs["headers"])
        self.assertEqual(container_call.kwargs["headers"]["Overwrite-Tombstone"], "true")
        content_call = send.call_args_list[2]
        self.assertEqual(content_call.args[0], f"{self.file_url}/ocr/alto-xml")
        self.assertEqual(content_call.args[1], FedoraRequestType.CREATE_DISTRIBUTION_CONTENT)
        self.assertNotIn("Slug", content_call.kwargs["headers"])

    def test_save_nested_skips_existing_parent_container(self):
        """Existující mezilehlý kontejner se znovu nezakládá."""
        responses = [_Response(status_code=200), _Response(status_code=201)]
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", side_effect=responses
        ) as send:
            self.connector.save_distribution(self.UUID, "ocr/alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(send.call_count, 2)
        self.assertEqual(send.call_args_list[1].args[1], FedoraRequestType.CREATE_DISTRIBUTION_CONTENT)

    def test_save_recreates_tombstoned_parent_container(self):
        """Mezilehlý kontejner se stavem 410 (tombstone) se považuje za chybějící a založí se znovu."""
        responses = [_Response(status_code=410), _Response(status_code=201), _Response(status_code=201)]
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", side_effect=responses
        ) as send:
            self.connector.save_distribution(self.UUID, "ocr/alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(send.call_count, 3)
        container_call = send.call_args_list[1]
        self.assertEqual(container_call.args[0], f"{self.file_url}/ocr")
        self.assertEqual(container_call.args[1], FedoraRequestType.CREATE_DISTRIBUTION_CONTAINER)
        self.assertEqual(container_call.kwargs["headers"]["Overwrite-Tombstone"], "true")

    def test_save_creates_parent_container_when_no_response(self):
        """Bez odpovědi na dotaz na kontejner se kontejner raději založí, než aby zápis obsahu selhal."""
        responses = [None, _Response(status_code=201), _Response(status_code=201)]
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", side_effect=responses
        ) as send:
            self.connector.save_distribution(self.UUID, "ocr/alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(send.call_args_list[1].args[1], FedoraRequestType.CREATE_DISTRIBUTION_CONTAINER)

    def test_save_creates_each_missing_level_of_deep_path(self):
        """U víceúrovňové cesty se zakládá každý chybějící segment zvlášť a ve správném pořadí."""
        responses = [
            _Response(status_code=404),
            _Response(status_code=201),
            _Response(status_code=404),
            _Response(status_code=201),
            _Response(status_code=201),
        ]
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", side_effect=responses
        ) as send:
            self.connector.save_distribution(self.UUID, "ocr/alto/xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(
            [call.args[0] for call in send.call_args_list],
            [
                f"{self.file_url}/ocr",
                f"{self.file_url}/ocr",
                f"{self.file_url}/ocr/alto",
                f"{self.file_url}/ocr/alto",
                f"{self.file_url}/ocr/alto/xml",
            ],
        )

    def test_created_parent_container_carries_creator(self):
        """Zakládaný mezilehlý kontejner nese jako RDF obsah ``dcterms:creator`` s aktuálním uživatelem."""
        responses = [_Response(status_code=404), _Response(status_code=201), _Response(status_code=201)]
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", side_effect=responses
        ) as send:
            self.connector.save_distribution(self.UUID, "ocr/alto-xml", "soubor.xml", "text/xml", self._file())

        container_call = send.call_args_list[1]
        self.assertEqual(container_call.kwargs["headers"]["Content-Type"], "text/turtle")
        self.assertIn("dcterms:creator", container_call.kwargs["data"])
        self.assertIn(f"record/{self.connector.user}", container_call.kwargs["data"])

    def test_save_uses_explicit_ident_cely(self):
        """Zadaný ``ident_cely`` má přednost před identem navázaného záznamu."""
        other_ident = "C-DL-202500002"
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=201)
        ) as send:
            self.connector.save_distribution(
                self.UUID, "alto-xml", "soubor.xml", "text/xml", self._file(), ident_cely=other_ident
            )

        expected = f"{FedoraRepositoryConnector.get_base_url()}/record/{other_ident}/file/{self.UUID}/alto-xml"
        self.assertEqual(send.call_args_list[0].args[0], expected)

    def test_save_allows_thumb_containers(self):
        """Samotné ``thumb`` a ``thumb-large`` lze zapsat jako distribuci."""
        for distribution in ("thumb", "thumb-large"):
            with self.subTest(distribution=distribution):
                with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
                    self.connector, "_send_request", return_value=_Response(status_code=201)
                ) as send:
                    self.connector.save_distribution(self.UUID, distribution, "soubor.png", "image/png", self._file())
                self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/{distribution}")

    def test_save_updates_creator_of_new_container(self):
        """Po zápisu obsahu se nastaví ``dcterms:creator`` na URL vzniklé distribuce."""
        with mock.patch.object(self.connector, "_send_request", return_value=_Response(status_code=201)):
            with mock.patch.object(self.connector, "_update_creator") as update_creator:
                self.connector.save_distribution(self.UUID, "alto-xml", "soubor.xml", "text/xml", self._file())

        update_creator.assert_called_once_with(
            FedoraRequestType.DISTRIBUTION_CONTENT_UPDATE_RDF_DATA, self.UUID, None, path="alto-xml"
        )

    def test_save_returns_binary_file_with_content_url(self):
        """Vrácený wrapper ukazuje na URL obsahu distribuce a nese název souboru."""
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=201)
        ):
            result = self.connector.save_distribution(self.UUID, "ocr/alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(result.url, f"{self.file_url}/ocr/alto-xml")
        self.assertEqual(result.filename, "soubor.xml")


class UpdateDeleteDistributionTest(DistributionConnectorTestBase):
    """Testy aktualizace, smazání a načtení alternativní distribuce."""

    def test_update_puts_to_distribution_url(self):
        """UPDATE zapisuje PUTem přímo na URL distribuce, bez Slugu."""
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=204)
        ) as send:
            self.connector.update_distribution(self.UUID, "ocr/alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(send.call_count, 1)
        call = send.call_args_list[0]
        self.assertEqual(call.args[0], f"{self.file_url}/ocr/alto-xml")
        self.assertEqual(call.args[1], FedoraRequestType.UPDATE_DISTRIBUTION_CONTENT)
        self.assertNotIn("Slug", call.kwargs["headers"])

    def test_update_does_not_send_overwrite_tombstone(self):
        """UPDATE míří na živý zdroj, hlavička pro přepis tombstonu se neposílá."""
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=204)
        ) as send:
            self.connector.update_distribution(self.UUID, "ocr/alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertNotIn("Overwrite-Tombstone", send.call_args_list[0].kwargs["headers"])

    def test_delete_targets_distribution_url(self):
        """DELETE míří na URL distribuce; tombstone se záměrně nemaže a chybějící paradata se nemažou."""
        with mock.patch.object(
            self.connector, "_send_request", side_effect=[_Response(status_code=204), _Response(status_code=404)]
        ) as send:
            self.connector.delete_distribution(self.UUID, "ocr/alto-xml")

        self.assertEqual(send.call_count, 2)
        self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/ocr/alto-xml")
        self.assertEqual(send.call_args_list[0].args[1], FedoraRequestType.DELETE_DISTRIBUTION)
        self.assertEqual(send.call_args_list[1].args[0], f"{self.file_url}/paradata/ocr/alto-xml/fcr:metadata")
        self.assertEqual(send.call_args_list[1].args[1], FedoraRequestType.GET_DISTRIBUTION_METADATA)

    def test_delete_removes_existing_paradata_of_the_distribution(self):
        """Smazání distribuce smaže i její paradata, aby po ní nezůstala jako sirotek."""
        responses = [_Response(status_code=204), _Response(status_code=200), _Response(status_code=204)]
        with mock.patch.object(self.connector, "_send_request", side_effect=responses) as send:
            self.connector.delete_distribution(self.UUID, "ocr/alto-xml")

        self.assertEqual(send.call_count, 3)
        self.assertEqual(send.call_args_list[2].args[0], f"{self.file_url}/paradata/ocr/alto-xml")
        self.assertEqual(send.call_args_list[2].args[1], FedoraRequestType.DELETE_DISTRIBUTION)

    def test_get_returns_content(self):
        """Načtená distribuce se vrátí jako wrapper s obsahem a URL."""
        with mock.patch.object(
            self.connector,
            "_send_request",
            return_value=_Response(status_code=200, content=b"data", headers={"Content-Type": "application/xml"}),
        ) as send:
            result = self.connector.get_distribution(self.UUID, "ocr/alto-xml")

        self.assertEqual(send.call_args_list[0].args[1], FedoraRequestType.GET_DISTRIBUTION_CONTENT)
        self.assertEqual(result.url, f"{self.file_url}/ocr/alto-xml")
        self.assertEqual(result.content.read(), b"data")
        self.assertEqual(result.content_type, "application/xml")

    def test_get_reads_stored_filename(self):
        """Název ze ``Content-Disposition`` (uložený ``ebucore:filename``) se vrátí i s diakritikou."""
        # requests decodes headers as latin-1, so the UTF-8 name arrives as mojibake.
        disposition = 'attachment; filename="zpráva.xml"; size=4'.encode("utf-8").decode("latin-1")
        response = _Response(status_code=200, content=b"data", headers={"Content-Disposition": disposition})
        with mock.patch.object(self.connector, "_send_request", return_value=response):
            result = self.connector.get_distribution(self.UUID, "ocr/alto-xml")

        self.assertEqual(result.filename, "zpráva.xml")

    def test_get_without_content_disposition_has_no_filename(self):
        """Bez hlavičky ``Content-Disposition`` zůstane název prázdný."""
        with mock.patch.object(self.connector, "_send_request", return_value=_Response(status_code=200, content=b"x")):
            result = self.connector.get_distribution(self.UUID, "ocr/alto-xml")

        self.assertIsNone(result.filename)

    def test_get_returns_none_when_missing(self):
        """Neexistující distribuce vrátí ``None`` místo výjimky."""
        with mock.patch.object(self.connector, "_send_request", return_value=None):
            self.assertIsNone(self.connector.get_distribution(self.UUID, "ocr/alto-xml"))

    def test_update_sets_content_headers(self):
        """I při aktualizaci se posílá MIME typ, název souboru a kontrolní součet nového obsahu."""
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=204)
        ) as send:
            self.connector.update_distribution(
                self.UUID, "ocr/alto-xml", "soubor.xml", "text/xml", self._file(b"nova data")
            )

        headers = send.call_args_list[0].kwargs["headers"]
        self.assertEqual(headers["Content-Type"], "text/xml")
        self.assertEqual(headers["Content-Disposition"], b'attachment; filename="soubor.xml"')
        self.assertTrue(headers["Digest"].startswith("sha-512="))
        self.assertEqual(send.call_args_list[0].kwargs["data"], b"nova data")

    def test_update_updates_creator(self):
        """Po aktualizaci obsahu se ``dcterms:creator`` nastaví na URL distribuce."""
        with mock.patch.object(self.connector, "_send_request", return_value=_Response(status_code=204)):
            with mock.patch.object(self.connector, "_update_creator") as update_creator:
                self.connector.update_distribution(self.UUID, "ocr/alto-xml", "soubor.xml", "text/xml", self._file())

        update_creator.assert_called_once_with(
            FedoraRequestType.DISTRIBUTION_CONTENT_UPDATE_RDF_DATA, self.UUID, None, path="ocr/alto-xml"
        )

    def test_update_does_not_create_parent_containers(self):
        """UPDATE cílí na existující zdroj, mezilehlé kontejnery se neověřují ani nezakládají."""
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=204)
        ) as send:
            self.connector.update_distribution(self.UUID, "ocr/alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(send.call_count, 1)

    def test_creator_metadata_url_targets_fcr_metadata(self):
        """URL pro zápis ``dcterms:creator`` míří na ``fcr:metadata`` dané distribuce."""
        url = self.connector._get_request_url(
            FedoraRequestType.DISTRIBUTION_CONTENT_UPDATE_RDF_DATA, uuid=self.UUID, path="ocr/alto-xml"
        )
        self.assertEqual(url, f"{self.file_url}/ocr/alto-xml/fcr:metadata")


class ParadataConnectorTest(DistributionConnectorTestBase):
    """Testy zápisu paradat pod kontejner ``paradata`` konkrétní distribuce."""

    def test_save_paradata_creates_paradata_container(self):
        """Chybějící kontejner ``paradata`` se založí a obsah se uloží pod názvem distribuce."""
        responses = [_Response(status_code=404), _Response(status_code=201), _Response(status_code=201)]
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", side_effect=responses
        ) as send:
            self.connector.save_paradata(self.UUID, "alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/paradata")
        self.assertEqual(send.call_args_list[1].args[0], f"{self.file_url}/paradata")
        self.assertEqual(send.call_args_list[1].args[1], FedoraRequestType.CREATE_DISTRIBUTION_CONTAINER)
        content_call = send.call_args_list[2]
        self.assertEqual(content_call.args[0], f"{self.file_url}/paradata/alto-xml")
        self.assertEqual(content_call.kwargs["headers"]["Overwrite-Tombstone"], "true")

    def test_save_paradata_nested_distribution(self):
        """U vnořené distribuce se založí i kontejner ``paradata/ocr``."""
        responses = [
            _Response(status_code=200),
            _Response(status_code=404),
            _Response(status_code=201),
            _Response(status_code=201),
        ]
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", side_effect=responses
        ) as send:
            self.connector.save_paradata(self.UUID, "ocr/alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(send.call_args_list[1].args[0], f"{self.file_url}/paradata/ocr")
        self.assertEqual(send.call_args_list[2].args[0], f"{self.file_url}/paradata/ocr")
        self.assertEqual(send.call_args_list[2].args[1], FedoraRequestType.CREATE_DISTRIBUTION_CONTAINER)
        self.assertEqual(send.call_args_list[3].args[0], f"{self.file_url}/paradata/ocr/alto-xml")

    def test_update_paradata_puts_to_paradata_url(self):
        """UPDATE paradat zapisuje PUTem na ``paradata/{distribuce}``."""
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=204)
        ) as send:
            self.connector.update_paradata(self.UUID, "alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/paradata/alto-xml")
        self.assertEqual(send.call_args_list[0].args[1], FedoraRequestType.UPDATE_DISTRIBUTION_CONTENT)

    def test_delete_paradata_targets_paradata_url(self):
        """DELETE paradat míří na ``paradata/{distribuce}``."""
        with mock.patch.object(self.connector, "_send_request", return_value=_Response(status_code=204)) as send:
            self.connector.delete_paradata(self.UUID, "alto-xml")

        self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/paradata/alto-xml")

    def test_get_paradata_targets_paradata_url(self):
        """GET paradat míří na ``paradata/{distribuce}``."""
        with mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=200, content=b"x")
        ) as send:
            self.connector.get_paradata(self.UUID, "alto-xml")

        self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/paradata/alto-xml")

    def test_paradata_allowed_for_orig(self):
        """Paradata lze připojit i k původní distribuci ``orig``, na rozdíl od alternativních distribucí."""
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", side_effect=[_Response(status_code=200), _Response(status_code=201)]
        ) as send:
            self.connector.save_paradata(self.UUID, "orig", "soubor.xml", "text/xml", self._file())

        self.assertEqual(send.call_args_list[1].args[0], f"{self.file_url}/paradata/orig")

    def test_update_paradata_sends_overwrite_tombstone(self):
        """Paradata nemají historii, takže i UPDATE musí umět přepsat tombstone po dřívějším smazání."""
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=204)
        ) as send:
            self.connector.update_paradata(self.UUID, "alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(send.call_args_list[0].kwargs["headers"]["Overwrite-Tombstone"], "true")

    def test_delete_paradata_of_nested_distribution(self):
        """DELETE paradat vnořené distribuce míří pod ``paradata`` na celou cestu distribuce."""
        with mock.patch.object(self.connector, "_send_request", return_value=_Response(status_code=204)) as send:
            self.connector.delete_paradata(self.UUID, "ocr/alto-xml")

        self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/paradata/ocr/alto-xml")

    def test_get_paradata_returns_none_when_missing(self):
        """Neexistující paradata vrátí ``None`` místo výjimky."""
        with mock.patch.object(self.connector, "_send_request", return_value=None):
            self.assertIsNone(self.connector.get_paradata(self.UUID, "alto-xml"))

    def test_paradata_rejects_reserved_names(self):
        """Ani u paradat nelze cílit na ``paradata`` nebo na kontejnery pod ``thumb/page``."""
        for distribution in ("paradata", "thumb/page", "thumb/page/1"):
            with self.subTest(distribution=distribution):
                with self.assertRaises(FedoraValidationError):
                    self.connector.get_paradata(self.UUID, distribution)

    def test_all_paradata_operations_reject_reserved_names(self):
        """Guard platí pro zápis, aktualizaci i smazání paradat, ještě před dotazem do Fedory."""
        with mock.patch.object(self.connector, "_send_request") as send:
            with self.assertRaises(FedoraValidationError):
                self.connector.save_paradata(self.UUID, "paradata", "soubor.xml", "text/xml", self._file())
            with self.assertRaises(FedoraValidationError):
                self.connector.update_paradata(self.UUID, "paradata", "soubor.xml", "text/xml", self._file())
            with self.assertRaises(FedoraValidationError):
                self.connector.delete_paradata(self.UUID, "paradata")
        send.assert_not_called()


class ReservedDistributionNameTest(DistributionConnectorTestBase):
    """Testy odmítnutí vyhrazených a neplatných názvů distribucí ve všech operacích."""

    RESERVED = ("orig", "paradata", "thumb/page", "thumb/page/nested")
    INVALID = ("", "   ", "/", "ocr//alto-xml", "../orig", "ocr/../../orig")

    def test_save_rejects_reserved_names(self):
        """Vyhrazený název distribuce se odmítne dřív, než dojde na požadavek do Fedory."""
        for distribution in self.RESERVED:
            with self.subTest(distribution=distribution):
                with mock.patch.object(self.connector, "_send_request") as send:
                    with self.assertRaises(FedoraValidationError):
                        self.connector.save_distribution(
                            self.UUID, distribution, "soubor.xml", "text/xml", self._file()
                        )
                send.assert_not_called()

    def test_all_operations_reject_reserved_names(self):
        """Guard platí pro zápis, aktualizaci, smazání i čtení distribuce."""
        with mock.patch.object(self.connector, "_send_request") as send:
            with self.assertRaises(FedoraValidationError):
                self.connector.update_distribution(self.UUID, "orig", "soubor.xml", "text/xml", self._file())
            with self.assertRaises(FedoraValidationError):
                self.connector.delete_distribution(self.UUID, "orig")
            with self.assertRaises(FedoraValidationError):
                self.connector.get_distribution(self.UUID, "orig")
        send.assert_not_called()

    def test_rejects_invalid_paths(self):
        """Prázdné názvy a segmenty umožňující opustit kontejner souboru se odmítnou."""
        for distribution in self.INVALID:
            with self.subTest(distribution=distribution):
                with self.assertRaises(FedoraValidationError):
                    self.connector.delete_distribution(self.UUID, distribution)

    def test_allows_thumb_containers(self):
        """Samotné ``thumb`` a ``thumb-large`` vyhrazené nejsou a zůstávají zapisovatelné."""
        for distribution in ("thumb", "thumb-large"):
            with self.subTest(distribution=distribution):
                with mock.patch.object(
                    self.connector, "_send_request", return_value=_Response(status_code=204)
                ) as send:
                    self.connector.delete_distribution(self.UUID, distribution)
                self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/{distribution}")

    def test_strips_surrounding_slashes_and_whitespace(self):
        """Okrajová lomítka a bílé znaky se normalizují, URL zůstane bez dvojitých lomítek."""
        with mock.patch.object(self.connector, "_send_request", return_value=_Response(status_code=204)) as send:
            self.connector.delete_distribution(self.UUID, " /ocr/alto-xml/ ")

        self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/ocr/alto-xml")


class ReservedSubtreeTest(DistributionConnectorTestBase):
    """Testy vyhrazeného podstromu — vyhrazený název chrání i vše pod sebou."""

    def test_rejects_names_under_a_reserved_prefix(self):
        """Zápis pod vyhrazený název se odmítne dřív, než se odešle požadavek do Fedory."""
        for distribution in ("paradata/alto-xml", "paradata/ocr/alto-xml", "orig/x", "thumb/page/1"):
            with self.subTest(distribution=distribution):
                with mock.patch.object(self.connector, "_send_request") as send:
                    with self.assertRaises(FedoraValidationError):
                        self.connector.save_distribution(
                            self.UUID, distribution, "soubor.xml", "text/xml", self._file()
                        )
                send.assert_not_called()

    def test_paradata_exists_still_queries_the_paradata_container(self):
        """Vnitřně sestavená cesta ``paradata/{distribuce}`` se znovu nevaliduje.

        ``paradata`` je vyhrazený prefix, takže opětovná validace vlastní cesty by dotaz
        na existenci paradat shodila — proto jde přes ``_container_exists``.
        """
        with mock.patch.object(self.connector, "_send_request", return_value=_Response(status_code=200)) as send:
            exists = self.connector.paradata_exists(self.UUID, "alto-xml")

        self.assertTrue(exists)
        self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/paradata/alto-xml/fcr:metadata")

    def test_paradata_exists_allows_the_original_distribution(self):
        """Paradata lze mít i k ``orig``; cesta míří pod kontejner paradat."""
        with mock.patch.object(self.connector, "_send_request", return_value=_Response(status_code=404)) as send:
            exists = self.connector.paradata_exists(self.UUID, "orig")

        self.assertFalse(exists)
        self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/paradata/orig/fcr:metadata")

    def test_paradata_still_rejects_a_reserved_distribution(self):
        """Paradata k ``paradata`` nedávají smysl a odmítnou se i po rozšíření kontroly."""
        with mock.patch.object(self.connector, "_send_request") as send:
            with self.assertRaises(FedoraValidationError):
                self.connector.paradata_exists(self.UUID, "paradata")
        send.assert_not_called()


class PathConflictTest(DistributionConnectorTestBase):
    """Testy hledání kolize cesty nové distribuce nebo paradat se stavem Fedory."""

    def _fedora(self, responses):
        """Nahradí ``_send_request`` odpověďmi podle URL; neznámá URL vrátí 404.

        :param responses: Slovník relativní cesta pod souborem → stavový kód.
        :return: Patch ``_send_request``.
        """

        def send(url, request_type, **kwargs):
            relative = url[len(self.file_url) + 1 :]
            return _Response(status_code=responses.get(relative, 404))

        return mock.patch.object(self.connector, "_send_request", side_effect=send)

    def test_binary_ancestor_is_a_conflict(self):
        """Pod binárním náhledem ``thumb`` nelze založit ``thumb/x``."""
        with self._fedora({"thumb/fcr:metadata": 200}):
            conflict = self.connector.find_distribution_path_conflict(self.UUID, "thumb/x")

        self.assertEqual(conflict, "thumb")

    def test_existing_container_on_the_path_is_a_conflict(self):
        """Na místě kontejneru ``ocr`` s potomkem ``ocr/alto-xml`` nelze založit binární ``ocr``."""
        with self._fedora({"ocr": 200}):
            conflict = self.connector.find_distribution_path_conflict(self.UUID, "ocr")

        self.assertEqual(conflict, "ocr")

    def test_container_ancestor_is_not_a_conflict(self):
        """Existující kontejner ``ocr`` je pro ``ocr/alto-xml`` v pořádku — jen se do něj zapíše."""
        with self._fedora({"ocr": 200}) as send:
            conflict = self.connector.find_distribution_path_conflict(self.UUID, "ocr/alto-xml")

        self.assertIsNone(conflict)
        self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/ocr/fcr:metadata")

    def test_tombstone_on_the_path_is_not_a_conflict(self):
        """Tombstone po smazané distribuci zápis přepíše hlavičkou ``Overwrite-Tombstone``."""
        with self._fedora({"ocr/alto-xml": 410}):
            conflict = self.connector.find_distribution_path_conflict(self.UUID, "ocr/alto-xml")

        self.assertIsNone(conflict)

    def test_paradata_container_itself_is_not_checked(self):
        """Kontejner ``paradata`` je kontejnerem záměrně; hlídají se až segmenty pod ním."""
        with self._fedora({"paradata/ocr/fcr:metadata": 200}) as send:
            conflict = self.connector.find_paradata_path_conflict(self.UUID, "ocr/alto-xml")

        self.assertEqual(conflict, "paradata/ocr")
        urls = [call.args[0] for call in send.call_args_list]
        self.assertNotIn(f"{self.file_url}/paradata/fcr:metadata", urls)

    def test_reserved_name_is_rejected_before_querying_fedora(self):
        """Vyhrazený název se odmítne dřív, než se odešle požadavek do Fedory."""
        with mock.patch.object(self.connector, "_send_request") as send:
            with self.assertRaises(FedoraValidationError):
                self.connector.find_distribution_path_conflict(self.UUID, "orig/x")
        send.assert_not_called()

    def test_no_response_raises(self):
        """Bez odpovědi Fedory nelze kolizi vyloučit, validace se musí zastavit."""
        with mock.patch.object(self.connector, "_send_request", return_value=None):
            with self.assertRaises(FedoraNoResponseError):
                self.connector.find_distribution_path_conflict(self.UUID, "ocr")
