"""
Ruční integrační test zjišťování paradat souboru proti běžící Fedoře.

Tabulka souborů zobrazuje ikonu paradat podle ``has_paradata`` a ``paradata_exists``. Obě metody
stojí na chování Fedory, které jednotkové testy mockují: ``paradata`` je RDF kontejner bez
``fcr:metadata`` (dotaz na něj vrací 404), kdežto binární paradata ``fcr:metadata`` mají, a smazaný
zdroj vrací 410 (tombstone). Test toto chování ověří na skutečné instanci — právě dotaz na
``paradata/fcr:metadata`` dříve způsobil, že se ikona paradat nezobrazila nikdy.

Běží jen na vyžádání, protože zapisuje do Fedory nastavené v ``settings``. Pod vlastním dočasným
záznamem si postaví soubory s paradaty i bez nich a po testu je smaže i s tombstonem::

    docker compose -f docker-compose-dev-local-db-all-containers.yml exec -e FEDORA_INTEGRATION_TESTS=1 \\
        web python manage.py test core.tests.test_fedora_integration_paradata

Při úplném běhu Selenium testů (``run_tests.py``) se spouští automaticky proti jejich testové Fedoře.
Nespouštět proti produkční Fedoře.
"""

import os
import unittest
import uuid as uuid_lib
from types import SimpleNamespace

import requests
from core.repository_connector import NON_RDF_SOURCE_LINK, FedoraRepositoryConnector
from django.conf import settings
from django.test import SimpleTestCase


@unittest.skipUnless(os.environ.get("FEDORA_INTEGRATION_TESTS") == "1", "Set FEDORA_INTEGRATION_TESTS=1 to run.")
class FedoraParadataIntegrationTest(SimpleTestCase):
    """Ověřuje ``has_paradata`` a ``paradata_exists`` na běžící Fedoře."""

    def setUp(self):
        """Založí ve Fedoře dočasný záznam se souborem s paradaty a souborem bez nich."""
        self.auth = (settings.FEDORA_ADMIN_USER, settings.FEDORA_ADMIN_USER_PASSWORD)
        self.ident_cely = f"X-PROTOCOL-{uuid_lib.uuid4().hex[:12]}"
        self.record_url = f"{FedoraRepositoryConnector.get_base_url()}/record/{self.ident_cely}"
        self.addCleanup(self._delete_record)
        self.uuid_with_paradata = str(uuid_lib.uuid4())
        self.uuid_without_paradata = str(uuid_lib.uuid4())
        self._put_container(self.record_url)
        self._put_container(f"{self.record_url}/file")
        for uuid in (self.uuid_with_paradata, self.uuid_without_paradata):
            self._put_container(self._file_url(uuid))
            self._put_binary(f"{self._file_url(uuid)}/orig", "scan.pdf", "application/pdf", b"%PDF")
        # Paradata of a nested distribution, the layout produced by the paradata import.
        file_url = self._file_url(self.uuid_with_paradata)
        for container in ("ocr", "paradata", "paradata/ocr"):
            self._put_container(f"{file_url}/{container}")
        self._put_binary(f"{file_url}/ocr/alto-xml", "scan.alto.xml", "application/xml", b"<alto/>")
        self._put_binary(f"{file_url}/paradata/ocr/alto-xml", "paradata.json", "application/ld+json", b"{}")

    def _file_url(self, uuid):
        """
        Vrátí URL kontejneru souboru pod dočasným záznamem.

        :param uuid: UUID kontejneru souboru.
        :return: URL kontejneru souboru.
        """
        return f"{self.record_url}/file/{uuid}"

    def _put_container(self, url):
        """
        Založí prázdný kontejner na zadané URL.

        :param url: URL zakládaného kontejneru.
        """
        response = requests.put(url, auth=self.auth)
        self.assertEqual(response.status_code, 201, f"Kontejner {url} se nepodařilo založit: {response.text}")

    def _put_binary(self, url, filename, content_type, content):
        """
        Uloží binární obsah se zadaným názvem souboru stejně jako connector.

        :param url: URL ukládaného binárního souboru.
        :param filename: Název souboru předaný v ``Content-Disposition``.
        :param content_type: MIME typ obsahu.
        :param content: Binární obsah.
        """
        headers = {
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Link": NON_RDF_SOURCE_LINK,
        }
        response = requests.put(url, auth=self.auth, headers=headers, data=content)
        self.assertEqual(response.status_code, 201, f"Soubor {url} se nepodařilo uložit: {response.text}")

    def _delete_record(self):
        """Smaže dočasný záznam i jeho tombstone, aby ve Fedoře nic nezůstalo."""
        requests.delete(self.record_url, auth=self.auth)
        requests.delete(f"{self.record_url}/fcr:tombstone", auth=self.auth)

    def _connector(self):
        """
        Vrátí connector pro dočasný záznam.

        :return: Netransakční ``FedoraRepositoryConnector``.
        """
        return FedoraRepositoryConnector(SimpleNamespace(ident_cely=self.ident_cely))

    def test_has_paradata_finds_the_paradata_container(self):
        """Existující RDF kontejner ``paradata`` se rozpozná, přestože nemá ``fcr:metadata``."""
        self.assertTrue(self._connector().has_paradata(self.uuid_with_paradata))

    def test_has_paradata_is_false_for_a_file_without_paradata(self):
        """Soubor bez kontejneru ``paradata`` (Fedora vrací 404) paradata nemá."""
        self.assertFalse(self._connector().has_paradata(self.uuid_without_paradata))

    def test_has_paradata_is_false_after_the_paradata_were_deleted(self):
        """Po smazání kontejneru ``paradata`` zůstane tombstone (410), který se nepovažuje za paradata."""
        response = requests.delete(f"{self._file_url(self.uuid_with_paradata)}/paradata", auth=self.auth)
        self.assertEqual(response.status_code, 204)

        self.assertFalse(self._connector().has_paradata(self.uuid_with_paradata))

    def test_paradata_exists_only_for_distributions_with_paradata(self):
        """Paradata vnořené distribuce se najdou; distribuce bez paradat je nemá."""
        connector = self._connector()

        self.assertTrue(connector.paradata_exists(self.uuid_with_paradata, "ocr/alto-xml"))
        self.assertFalse(connector.paradata_exists(self.uuid_with_paradata, "orig"))
