"""Testy kontroly přihlášení a oprávnění u importu překladového katalogu v Rosettě (issue #4542)."""

import tempfile
from pathlib import Path
from unittest import mock

from core.views import TranslationImportView
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase
from django.views.generic import View

URL = "/rosetta/files/import/project/cs/0/"
KWARGS = {"po_filter": "project", "lang_id": "cs", "idx": 0}
ACCESS = "rosetta.access.get_access_control_function"


class TranslationImportViewAccessTest(SimpleTestCase):
    """Pohled importu musí procházet dekorátory Rosetty dřív, než se zpracuje nahraný soubor."""

    def setUp(self):
        """Připraví ``RequestFactory`` pro sestavení požadavků."""
        self.factory = RequestFactory()

    def _request(self, method, user):
        if method == "post":
            request = self.factory.post(URL, {"file": SimpleUploadedFile("cs.po", b'msgid ""\nmsgstr ""\n' * 100)})
        else:
            request = self.factory.get(URL)
        request.user = user
        return request

    def test_dispatch_neni_djangovo_view_dispatch(self):
        """Dispatch musí pocházet z mixinu Rosetty, ne přímo z ``View``."""
        self.assertIsNot(TranslationImportView.dispatch, View.dispatch)

    @mock.patch("core.views.pofile")
    def test_anonym_je_presmerovan_na_prihlaseni(self, pofile_mock):
        """Nepřihlášený uživatel (GET i POST) skončí na přihlášení a soubor se nenačte polibem.

        :param pofile_mock: Mock funkce ``pofile`` v ``core.views``.
        """
        for method in ("get", "post"):
            with self.subTest(method=method):
                response = TranslationImportView.as_view()(self._request(method, AnonymousUser()), **KWARGS)
                self.assertEqual(response.status_code, 302)
                self.assertIn("login", response["Location"])
        pofile_mock.assert_not_called()

    @mock.patch("core.views.pofile")
    def test_uzivatel_bez_prava_je_odmitnut_pred_parsovanim(self, pofile_mock):
        """Přihlášený uživatel bez práva překládat je odmítnut a soubor se nenačte polibem.

        :param pofile_mock: Mock funkce ``pofile`` v ``core.views``.
        """
        user = mock.Mock(is_authenticated=True)
        with mock.patch(ACCESS, return_value=lambda u: False):
            for method in ("get", "post"):
                with self.subTest(method=method):
                    response = TranslationImportView.as_view()(self._request(method, user), **KWARGS)
                    self.assertEqual(response.status_code, 302)
        pofile_mock.assert_not_called()

    @mock.patch("core.views.pofile")
    def test_jazyk_bez_prava_nacte_soubor_az_po_kontrole_jazyka(self, pofile_mock):
        """Překladatel bez práva na daný jazyk dostane 404 dřív, než se soubor naparsuje.

        :param pofile_mock: Mock funkce ``pofile`` v ``core.views``.
        """
        user = mock.Mock(is_authenticated=True)
        with mock.patch(ACCESS, return_value=lambda u: True), mock.patch.object(
            TranslationImportView, "po_file_path", new_callable=mock.PropertyMock, side_effect=Http404
        ):
            with self.assertRaises(Http404):
                TranslationImportView.as_view()(self._request("post", user), **KWARGS)
        pofile_mock.assert_not_called()

    def test_prekladatel_projde_a_odpoved_ma_no_cache_hlavicky(self):
        """Překladatel dostane formulář a odpověď zakazuje cache."""
        user = mock.Mock(is_authenticated=True)
        # Katalog se dodá z dočasného adresáře, aby test nezávisel na lokálním svazku s překlady.
        with tempfile.TemporaryDirectory() as tmpdir:
            po_path = Path(tmpdir, "locale", "cs", "LC_MESSAGES", "django.po")
            po_path.parent.mkdir(parents=True)
            po_path.write_text('msgid ""\nmsgstr ""\n', encoding="utf-8")
            with mock.patch(ACCESS, return_value=lambda u: True), mock.patch(
                "core.views.find_pos_with_backup", return_value=[str(po_path)]
            ):
                response = TranslationImportView.as_view()(self._request("get", user), **KWARGS)
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-cache", response["Cache-Control"])
