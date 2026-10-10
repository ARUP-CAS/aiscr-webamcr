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
    """Minimální náhrada ``RepositoryBinaryFile`` — nese jen ``content``, ``content_type`` a ``filename``."""

    def __init__(self, data=b"obsah", content_type=None, filename=None):
        """
        :param data: Binární obsah vrácený v odpovědi.
        :param content_type: MIME typ uložený u obsahu ve Fedoře.
        :param filename: Název uložený u obsahu ve Fedoře (``ebucore:filename``).
        """
        self.content = io.BytesIO(data)
        self.content_type = content_type
        self.filename = filename


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

    def _distribution_response(self, nazev, distribution, content_type=None, filename=None):
        """Vrátí odpověď ke stažení distribuce s mocknutým repozitářem.

        :param nazev: Název souboru.
        :param distribution: Název distribuce.
        :param content_type: MIME typ uložený u distribuce ve Fedoře.
        :param filename: Název uložený u distribuce ve Fedoře.
        :return: ``FileResponse`` s obsahem distribuce.
        """
        soubor = self._soubor(nazev)
        # ``vazba`` je FK deskriptor, který Mock odmítne — nahrazuje se proto na úrovni třídy.
        with mock.patch.object(Soubor, "repository_uuid", "uuid-1"), mock.patch.object(
            Soubor, "vazba", mock.Mock(navazany_objekt=mock.Mock())
        ), mock.patch("core.repository_connector.FedoraRepositoryConnector") as connector:
            connector.return_value.get_distribution.return_value = _FakeBinaryFile(b"{}", content_type, filename)
            return soubor.get_distribution_response(distribution)

    def test_distribution_is_downloaded_under_stored_name(self):
        """Distribuce se stáhne pod názvem uloženým ve Fedoře a odpověď nese uložený MIME typ."""
        response = self._distribution_response("scan.pdf", "ocr/alto-xml", "application/xml", "scan_alto.xml")

        self.assertEqual(response["Content-Disposition"], 'attachment; filename="scan_alto.xml"')
        self.assertEqual(response["Content-Type"], "application/xml")

    def test_stored_name_without_extension_is_kept(self):
        """Uložený název bez přípony se nemění — chybějící přípona je záměr, nedoplňuje se z MIME typu."""
        response = self._distribution_response("scan.pdf", "atr/json", "application/json", "atributy")

        self.assertEqual(response["Content-Disposition"], 'attachment; filename="atributy"')

    def test_missing_stored_name_falls_back_to_distribution(self):
        """Bez uloženého názvu se název odvodí ze souboru a distribuce; lomítka se nahradí podtržítkem."""
        response = self._distribution_response("scan.pdf", "ocr/alto-xml", "application/xml")

        self.assertEqual(response["Content-Disposition"], 'attachment; filename="scan.pdf.ocr_alto-xml"')
