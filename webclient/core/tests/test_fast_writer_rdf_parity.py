"""
Testy shody RDF formátu mezi ``_FastFedoraWriter`` a :class:`FedoraRepositoryConnector`.

``generate_metadata_fast`` zapisuje do Fedory vlastní, zrychlenou cestou a přitom musí
produkovat bajtově stejné RDF jako běžný zápis z aplikace - jinak by se záznamy vzniklé
migrací lišily od záznamů vzniklých v provozu a nic by si toho nevšimlo (závěrečná
kontrola konzistence porovnává jen identifikátory, ne RDF). Dřív tuhle shodu držela
pouze věta v docstringu; tenhle test ji hlídá skutečným porovnáním odeslaných dat
(review PR #4262).

Data se odebírají tak, jak by odešla na drát - odesílací metoda se nahradí záchytem,
takže se testuje reálné chování obou implementací, ne podoba jejich zdrojáku.
"""

from types import SimpleNamespace
from unittest import mock

from core.management.commands.generate_metadata_fast import _FastFedoraWriter
from core.repository_connector import FedoraRepositoryConnector, FedoraRequestType
from django.test import SimpleTestCase, override_settings

SERVER_NAME = "AMCR-TEST"
USER_IDENT = "U-000322"
IDENT_CELY = "C-202300001"
MODEL_NAME = "akce"


@override_settings(
    FEDORA_SERVER_NAME=SERVER_NAME,
    FEDORA_USER="u",
    FEDORA_USER_PASSWORD="p",
    FEDORA_ADMIN_USER="au",
    FEDORA_ADMIN_USER_PASSWORD="ap",
)
class CreatorRdfParityTest(SimpleTestCase):
    """Porovnává creator RDF, SPARQL update a link turtle obou implementací."""

    def _writer(self):
        """
        Vytvoří ``_FastFedoraWriter`` bez síťového spojení.

        :return: Instance ``_FastFedoraWriter``.
        """
        return _FastFedoraWriter(f"https://fedora.example/rest/{SERVER_NAME}", USER_IDENT)

    def _connector(self):
        """
        Vytvoří ``FedoraRepositoryConnector`` s obejitým ``__init__`` (nepotřebuje DB ani transakci).

        :return: Instance ``FedoraRepositoryConnector`` s doplněnými atributy, které
            testované metody čtou.
        """
        connector = FedoraRepositoryConnector.__new__(FedoraRepositoryConnector)
        connector.user = USER_IDENT
        connector.record = SimpleNamespace(ident_cely=IDENT_CELY)
        connector.transaction_uid = None
        connector.transaction = None
        connector.skip_container_check = True
        connector.restored_container = False
        return connector

    @staticmethod
    def _odeslana_data(connector, volani):
        """
        Zachytí ``data`` předaná do ``_send_request`` při zavolání ``volani``.

        :param connector: Instance ``FedoraRepositoryConnector``.
        :param volani: Funkce bez argumentů, která spustí testovanou metodu.
        :return: Seznam dvojic ``(request_type, data)`` v pořadí odeslání.
        """
        zachyceno = []

        def zachyt(url, request_type, headers=None, data=None, **kwargs):
            zachyceno.append((request_type, data))

        with mock.patch.object(connector, "_send_request", side_effect=zachyt), mock.patch.object(
            connector, "_get_request_url", return_value="https://fedora.example/rest/dummy"
        ):
            volani()
        return zachyceno

    def test_creator_turtle_je_shodny(self):
        """Turtle fragment s ``dcterms:creator`` musí být shodný s tím z ``_create_container``."""
        connector = self._connector()
        odeslane = self._odeslana_data(connector, connector._create_container)
        podle_typu = dict(odeslane)
        self.assertIn(FedoraRequestType.CREATE_CONTAINER, podle_typu)
        self.assertEqual(self._writer()._creator_rdf(), podle_typu[FedoraRequestType.CREATE_CONTAINER])

    def test_creator_sparql_update_je_shodny(self):
        """SPARQL update nastavující ``dcterms:creator`` musí být shodný s ``_get_creator_rdf_data``."""
        self.assertEqual(self._writer()._creator_sparql_update(), self._connector()._get_creator_rdf_data())

    def test_link_turtle_je_shodny(self):
        """Turtle fragment link resource (``ore:proxyFor`` + ``dcterms:creator``) musí být shodný."""
        connector = self._connector()
        odeslane = self._odeslana_data(connector, connector.create_link)
        self.assertEqual(len(odeslane), 1)
        ocekavane = odeslane[0][1]

        writer = self._writer()
        zachyceno = []

        def zachyt(method, url, headers, data, tx_url=None):
            zachyceno.append((url, data))
            return mock.Mock()

        with mock.patch.object(writer, "_request", side_effect=zachyt), mock.patch.object(writer, "_zkontroluj_slug"):
            writer.create_record(IDENT_CELY, MODEL_NAME, b"<xml/>", "0" * 128)

        link_data = [data for url, data in zachyceno if "/member" in url]
        self.assertEqual(len(link_data), 1, f"očekáván jeden zápis link resource, zachyceno: {zachyceno}")
        self.assertEqual(link_data[0], ocekavane)
