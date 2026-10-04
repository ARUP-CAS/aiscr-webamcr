"""Testy hlavičky ``Content-Disposition`` u odpovědí se souborem (``Soubor._create_file_response``).

Hlavičku sestavuje ``FileResponse`` podle RFC 6266; testy hlídají, že se název neořízne
u mezer a nerozsype u diakritiky a že se nezmění typ dispozice (``attachment``/``inline``).
Nepotřebují databázi ani Fedoru — pracují nad neuloženou instancí ``Soubor`` a fake obsahem.
"""

import io
from unittest import mock

from core.models import Soubor
from django.test import SimpleTestCase

ASCII_NAME = "plain.pdf"
NASTY_NAME = "zpráva o průzkumu.pdf"


class _FakeBinaryFile:
    """Minimální náhrada ``RepositoryBinaryFile`` — nese jen ``content`` a ``content_type``."""

    def __init__(self, data=b"obsah", content_type=None):
        """
        :param data: Binární obsah vrácený v odpovědi.
        :param content_type: MIME typ uložený u obsahu ve Fedoře.
        """
        self.content = io.BytesIO(data)
        self.content_type = content_type


class SouborFileResponseTest(SimpleTestCase):
    """Testy pro ``Soubor._create_file_response`` a odvozené odpovědi."""

    def _soubor(self, nazev):
        """Vytvoří neuloženou instanci ``Soubor`` se zadaným názvem.

        :param nazev: Název souboru.
        :return: Instance ``Soubor``.
        """
        return Soubor(nazev=nazev, mimetype="application/pdf", size_mb=1)

    def test_ascii_name_is_quoted(self):
        """Prostý asciiový název se uvozovkuje a zůstane čitelný."""
        response = self._soubor(ASCII_NAME)._create_file_response(_FakeBinaryFile())

        self.assertEqual(response["Content-Disposition"], 'attachment; filename="plain.pdf"')

    def test_name_with_space_and_diacritics_is_rfc6266_encoded(self):
        """Název s mezerou i diakritikou se zakóduje tvarem ``filename*``, nic se neořízne."""
        response = self._soubor(NASTY_NAME)._create_file_response(_FakeBinaryFile())

        disposition = response["Content-Disposition"]
        self.assertTrue(disposition.startswith("attachment; filename*=utf-8''"), disposition)
        # Mezera ani diakritika nesmí zůstat v hlavičce doslova — musí být procentově zakódované.
        self.assertNotIn(" o ", disposition)
        self.assertNotIn("á", disposition)

    def test_download_stays_an_attachment(self):
        """Stažení souboru musí zůstat ``attachment`` — ne ``inline`` (výchozí u FileResponse)."""
        response = self._soubor(NASTY_NAME)._create_file_response(_FakeBinaryFile())

        self.assertTrue(response["Content-Disposition"].startswith("attachment;"))

    def test_small_thumbnail_stays_inline(self):
        """Malý náhled se vykresluje ve stránce, takže si drží ``inline`` a příponu ``.png``."""
        soubor = self._soubor(ASCII_NAME)
        with mock.patch.object(Soubor, "repository_uuid", "uuid-1"), mock.patch.object(
            Soubor, "get_repository_content", return_value=_FakeBinaryFile()
        ):
            response = soubor.small_thumbnail

        self.assertEqual(response["Content-Disposition"], 'inline; filename="plain.pdf.png"')
        self.assertEqual(response["Content-Type"], "image/png")

    def test_large_thumbnail_is_an_attachment_with_png_suffix(self):
        """Velký náhled se stahuje jako ``attachment`` s příponou ``.png``."""
        soubor = self._soubor(ASCII_NAME)
        with mock.patch.object(Soubor, "repository_uuid", "uuid-1"), mock.patch.object(
            Soubor, "get_repository_content", return_value=_FakeBinaryFile()
        ):
            response = soubor.large_thumbnail

        self.assertEqual(response["Content-Disposition"], 'attachment; filename="plain.pdf.png"')

    def test_distribution_name_is_derived_from_the_distribution(self):
        """Distribuce se stáhne pod názvem odvozeným z distribuce, ne pod názvem souboru.

        Lomítka v názvu distribuce se nahrazují podtržítkem, aby název zůstal jedním segmentem.
        """
        soubor = self._soubor("scan.pdf")
        # ``vazba`` je FK deskriptor, který Mock odmítne — nahrazuje se proto na úrovni třídy.
        with mock.patch.object(Soubor, "repository_uuid", "uuid-1"), mock.patch.object(
            Soubor, "vazba", mock.Mock(navazany_objekt=mock.Mock())
        ), mock.patch("core.repository_connector.FedoraRepositoryConnector") as connector:
            connector.return_value.get_distribution.return_value = _FakeBinaryFile(b"<xml/>")
            response = soubor.get_distribution_response("ocr/alto-xml")

        self.assertEqual(response["Content-Disposition"], 'attachment; filename="scan.pdf.ocr_alto-xml"')

    def _distribution_response(self, nazev, distribution, content_type):
        """Vrátí odpověď ke stažení distribuce s mocknutým repozitářem.

        :param nazev: Název souboru.
        :param distribution: Název distribuce.
        :param content_type: MIME typ uložený u distribuce ve Fedoře.
        :return: ``FileResponse`` s obsahem distribuce.
        """
        soubor = self._soubor(nazev)
        with mock.patch.object(Soubor, "repository_uuid", "uuid-1"), mock.patch.object(
            Soubor, "vazba", mock.Mock(navazany_objekt=mock.Mock())
        ), mock.patch("core.repository_connector.FedoraRepositoryConnector") as connector:
            connector.return_value.get_distribution.return_value = _FakeBinaryFile(b"{}", content_type)
            return soubor.get_distribution_response(distribution)

    def test_distribution_name_gets_extension_from_stored_mimetype(self):
        """Přípona staženého souboru se odvodí z MIME typu distribuce a odpověď ho nese."""
        response = self._distribution_response("scan.pdf", "atr/json", "application/json")

        self.assertEqual(response["Content-Disposition"], 'attachment; filename="scan.pdf.atr_json.json"')
        self.assertEqual(response["Content-Type"], "application/json")

    def test_structured_suffix_mimetype_gets_syntax_extension(self):
        """Typ se suffixem ``+xml``/``+json``, který ``mimetypes`` nezná, dostane příponu podle syntaxe."""
        response = self._distribution_response("scan.pdf", "ocr/alto-xml", "application/alto+xml; charset=utf-8")

        self.assertEqual(response["Content-Disposition"], 'attachment; filename="scan.pdf.ocr_alto-xml.xml"')

    def test_unknown_mimetype_keeps_name_without_extension(self):
        """Neznámý MIME typ název nemění — přípona se nehádá."""
        response = self._distribution_response("scan.pdf", "cva/raw", "application/x-amcr-unknown")

        self.assertEqual(response["Content-Disposition"], 'attachment; filename="scan.pdf.cva_raw"')
