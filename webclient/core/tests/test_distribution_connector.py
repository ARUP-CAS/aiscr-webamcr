"""
Testy zápisu alternativních distribucí a paradat do Fedory (issue #3527).

Pokrývají sestavení URL kontejnerů, zakládání mezilehlých kontejnerů u vnořených názvů,
hlavičky ``Slug`` a ``Overwrite-Tombstone`` u INSERTu a odmítnutí vyhrazených názvů distribucí.
Testy nepotřebují databázi ani běžící Fedoru – využívají odlehčené náhradní objekty
a mock ``_send_request``.
"""

import io
from unittest import mock

from core.repository_connector import (
    FedoraRepositoryConnector,
    FedoraRequestType,
    FedoraValidationError,
)
from django.test import SimpleTestCase


class _Response:
    """Náhrada za ``requests.Response`` s textem, obsahem a stavovým kódem."""

    def __init__(self, text="", status_code=200, content=b""):
        self.text = text
        self.status_code = status_code
        self.content = content


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


class SaveDistributionTest(DistributionConnectorTestBase):
    """Testy vytvoření nové alternativní distribuce."""

    def test_save_posts_to_file_container_with_slug(self):
        """Distribuce bez lomítka se zakládá POSTem na kontejner souboru se Slugem názvu."""
        with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=201)
        ) as send:
            self.connector.save_distribution(self.UUID, "alto-xml", "soubor.xml", "text/xml", self._file())

        self.assertEqual(send.call_count, 1)
        call = send.call_args_list[0]
        self.assertEqual(call.args[0], self.file_url)
        self.assertEqual(call.args[1], FedoraRequestType.CREATE_DISTRIBUTION_CONTENT)
        self.assertEqual(call.kwargs["headers"]["Slug"], "alto-xml")

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
        self.assertEqual(container_call.args[0], self.file_url)
        self.assertEqual(container_call.args[1], FedoraRequestType.CREATE_DISTRIBUTION_CONTAINER)
        self.assertEqual(container_call.kwargs["headers"]["Slug"], "ocr")
        self.assertEqual(container_call.kwargs["headers"]["Overwrite-Tombstone"], "true")
        content_call = send.call_args_list[2]
        self.assertEqual(content_call.args[0], f"{self.file_url}/ocr")
        self.assertEqual(content_call.args[1], FedoraRequestType.CREATE_DISTRIBUTION_CONTENT)
        self.assertEqual(content_call.kwargs["headers"]["Slug"], "alto-xml")

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
        self.assertEqual(container_call.args[1], FedoraRequestType.CREATE_DISTRIBUTION_CONTAINER)
        self.assertEqual(container_call.kwargs["headers"]["Slug"], "ocr")
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

        self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/ocr")
        self.assertEqual(send.call_args_list[1].args[0], self.file_url)
        self.assertEqual(send.call_args_list[1].kwargs["headers"]["Slug"], "ocr")
        self.assertEqual(send.call_args_list[2].args[0], f"{self.file_url}/ocr/alto")
        self.assertEqual(send.call_args_list[3].args[0], f"{self.file_url}/ocr")
        self.assertEqual(send.call_args_list[3].kwargs["headers"]["Slug"], "alto")
        self.assertEqual(send.call_args_list[4].args[0], f"{self.file_url}/ocr/alto")
        self.assertEqual(send.call_args_list[4].kwargs["headers"]["Slug"], "xml")

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

        expected = f"{FedoraRepositoryConnector.get_base_url()}/record/{other_ident}/file/{self.UUID}"
        self.assertEqual(send.call_args_list[0].args[0], expected)

    def test_save_allows_thumb_containers(self):
        """Samotné ``thumb`` a ``thumb-large`` lze zapsat jako distribuci."""
        for distribution in ("thumb", "thumb-large"):
            with self.subTest(distribution=distribution):
                with mock.patch.object(self.connector, "_update_creator"), mock.patch.object(
                    self.connector, "_send_request", return_value=_Response(status_code=201)
                ) as send:
                    self.connector.save_distribution(self.UUID, distribution, "soubor.png", "image/png", self._file())
                self.assertEqual(send.call_args_list[0].kwargs["headers"]["Slug"], distribution)

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
        """DELETE míří na URL distribuce; tombstone se záměrně nemaže."""
        with mock.patch.object(self.connector, "_send_request", return_value=_Response(status_code=204)) as send:
            self.connector.delete_distribution(self.UUID, "ocr/alto-xml")

        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0].args[0], f"{self.file_url}/ocr/alto-xml")
        self.assertEqual(send.call_args_list[0].args[1], FedoraRequestType.DELETE_DISTRIBUTION)

    def test_get_returns_content(self):
        """Načtená distribuce se vrátí jako wrapper s obsahem a URL."""
        with mock.patch.object(
            self.connector, "_send_request", return_value=_Response(status_code=200, content=b"data")
        ) as send:
            result = self.connector.get_distribution(self.UUID, "ocr/alto-xml")

        self.assertEqual(send.call_args_list[0].args[1], FedoraRequestType.GET_DISTRIBUTION_CONTENT)
        self.assertEqual(result.url, f"{self.file_url}/ocr/alto-xml")
        self.assertEqual(result.content.read(), b"data")

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
        self.assertEqual(send.call_args_list[1].kwargs["headers"]["Slug"], "paradata")
        content_call = send.call_args_list[2]
        self.assertEqual(content_call.args[0], f"{self.file_url}/paradata")
        self.assertEqual(content_call.kwargs["headers"]["Slug"], "alto-xml")
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
        self.assertEqual(send.call_args_list[2].kwargs["headers"]["Slug"], "ocr")
        self.assertEqual(send.call_args_list[3].args[0], f"{self.file_url}/paradata/ocr")

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

        self.assertEqual(send.call_args_list[1].kwargs["headers"]["Slug"], "orig")

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
