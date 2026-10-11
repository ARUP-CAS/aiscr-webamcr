"""
Ruční integrační test průchodu potomky souboru proti běžící Fedoře.

Přejmenování souboru (``_rename_filenames_in_container``) i kopírování distribucí a paradat při
změně identifikátoru (``_collect_file_children``) procházejí potomky stejně a stojí na chování
Fedory, které jednotkové testy mockují:
výpis ``ldp:contains`` v n-triples, rozlišení kontejneru podle 404 na ``fcr:metadata`` a uložení
``ebucore:filename`` z ``Content-Disposition``. Test toto chování ověří na skutečné instanci, takže
odhalí změnu protokolu, kvůli které by kterýkoli z obou průchodů přestal fungovat.

Běží jen na vyžádání, protože zapisuje do Fedory nastavené v ``settings``. Pod vlastním dočasným
záznamem si postaví strom souboru a po testu ho smaže i s tombstonem::

    docker compose -f docker-compose-dev-local-db-all-containers.yml exec -e FEDORA_INTEGRATION_TESTS=1 \\
        web python manage.py test core.tests.test_fedora_integration_child_walk

Při úplném běhu Selenium testů (``run_tests.py``) se spouští automaticky proti jejich testové Fedoře.
Nespouštět proti produkční Fedoře.
"""

import os
import re
import unittest
import uuid as uuid_lib
from types import SimpleNamespace

import requests
from core.repository_connector import NON_RDF_SOURCE_LINK, FedoraRepositoryConnector
from django.conf import settings
from django.test import SimpleTestCase

OLD_BASE = "CTX900000001A"
NEW_BASE = "CTX900000001B"
FILENAME_PATTERN = re.compile(
    r"<" + re.escape(FedoraRepositoryConnector.EBUCORE_FILENAME_PREDICATE) + r">\s+\"((?:[^\"\\]|\\.)*)\""
)


@unittest.skipUnless(os.environ.get("FEDORA_INTEGRATION_TESTS") == "1", "Set FEDORA_INTEGRATION_TESTS=1 to run.")
class FedoraChildWalkIntegrationTest(SimpleTestCase):
    """Ověřuje oba průchody potomky souboru na běžící Fedoře."""

    def setUp(self):
        """Založí ve Fedoře dočasný záznam se souborem, vnořenou distribucí a paradaty."""
        self.auth = (settings.FEDORA_ADMIN_USER, settings.FEDORA_ADMIN_USER_PASSWORD)
        self.ident_cely = f"X-PROTOCOL-{uuid_lib.uuid4().hex[:12]}"
        self.record_url = f"{FedoraRepositoryConnector.get_base_url()}/record/{self.ident_cely}"
        self.uuid = str(uuid_lib.uuid4())
        self.file_url = f"{self.record_url}/file/{self.uuid}"
        self.addCleanup(self._delete_record)
        for container in (self.record_url, f"{self.record_url}/file", self.file_url):
            self._put_container(container)
        # Path under the file container -> (ebucore:filename, MIME type, content).
        self.binaries = {
            "orig": (f"{OLD_BASE}.jpg", "image/jpeg", b"jpeg"),
            "ocr/alto-xml": (f"{OLD_BASE}.alto.xml", "application/xml", b"<alto/>"),
            "paradata/ocr/alto-xml": (f"paradata-{OLD_BASE}.json", "application/ld+json", b"{}"),
        }
        for container in ("ocr", "paradata", "paradata/ocr"):
            self._put_container(f"{self.file_url}/{container}")
        for path, (filename, content_type, content) in self.binaries.items():
            self._put_binary(f"{self.file_url}/{path}", filename, content_type, content)

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

    def _filenames(self, path):
        """
        Načte ``ebucore:filename`` binárního souboru.

        :param path: Cesta binárního souboru pod kontejnerem souboru.
        :return: Nalezené hodnoty ``ebucore:filename``.
        """
        response = requests.get(
            f"{self.file_url}/{path}/fcr:metadata", auth=self.auth, headers={"Accept": "application/n-triples"}
        )
        self.assertEqual(response.status_code, 200)
        return FILENAME_PATTERN.findall(response.text)

    def _connector(self):
        """
        Vrátí connector pro dočasný záznam.

        :return: Netransakční ``FedoraRepositoryConnector``.
        """
        return FedoraRepositoryConnector(SimpleNamespace(ident_cely=self.ident_cely))

    def test_rename_reaches_every_binary_child(self):
        """Přejmenování projde vnořené kontejnery a upraví název u všech binárních potomků."""
        renamed = self._connector()._rename_filenames_in_container(self.file_url, OLD_BASE, NEW_BASE, depth=0)

        self.assertEqual(renamed, len(self.binaries), "Průchod nedošel ke všem binárním potomkům.")
        for path, (filename, _content_type, _content) in self.binaries.items():
            with self.subTest(path=path):
                self.assertEqual(self._filenames(path), [filename.replace(OLD_BASE, NEW_BASE)])

    def test_collect_returns_distributions_and_paradata_with_their_paths(self):
        """Kopírování při změně identifikátoru načte vnořenou distribuci i paradata, ``orig`` vynechá."""
        children = self._connector()._collect_file_children(self.uuid, self.ident_cely)

        collected = {
            path: (filename, content_type, content.read()) for path, filename, content_type, content in children
        }
        expected = {path: binary for path, binary in self.binaries.items() if path != "orig"}
        self.assertEqual(collected, expected)
