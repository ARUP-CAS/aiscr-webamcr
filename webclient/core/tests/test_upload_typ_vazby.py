"""
Testy shody ``typ_vazby`` s typem dokumentu při uploadu souborů (review PR #4538, issue #4527).

Pokrývají pomocnou funkci ``typ_vazby_odpovida_dokumentu``, odmítnutí nesouhlasného typu v
``UploadFileView.get_zaznam`` a ``NewFileUploadView._resolve_object_and_name`` a volbu MIME whitelistu
podle trasy namísto klientem zaslaného ``source-url``. Testy nepotřebují databázi.
"""

from types import SimpleNamespace
from unittest import mock

from core.views import NewFileUploadView, UploadFileView, typ_vazby_odpovida_dokumentu
from django.http import Http404, JsonResponse
from django.test import RequestFactory, SimpleTestCase


def _dokument(je_model_3d):
    """Vytvoří náhradní dokument daného typu (3D model / běžný dokument)."""
    return SimpleNamespace(je_model_3d=je_model_3d, ident_cely="X-1")


class TypVazbyOdpovidaDokumentuTest(SimpleTestCase):
    """Ověřuje pomocnou funkci porovnávající ``typ_vazby`` s typem dokumentu."""

    def test_shoda(self):
        """Běžný dokument odpovídá ``dokument``, 3D model odpovídá ``model3d``."""
        self.assertTrue(typ_vazby_odpovida_dokumentu(_dokument(False), "dokument"))
        self.assertTrue(typ_vazby_odpovida_dokumentu(_dokument(True), "model3d"))

    def test_neshoda(self):
        """Opačné kombinace se odmítají."""
        self.assertFalse(typ_vazby_odpovida_dokumentu(_dokument(False), "model3d"))
        self.assertFalse(typ_vazby_odpovida_dokumentu(_dokument(True), "dokument"))


class UploadFileViewGetZaznamTest(SimpleTestCase):
    """Ověřuje, že stránka uploadu odmítne nesouhlasný ``typ_vazby``."""

    def _get_zaznam(self, typ_vazby, dokument):
        view = UploadFileView()
        view.kwargs = {"typ_vazby": typ_vazby, "ident_cely": "X-1"}
        with mock.patch("core.views.get_object_or_404", return_value=dokument):
            return view.get_zaznam()

    def test_shoda_vraci_dokument(self):
        """Odpovídající kombinace vrátí dokument."""
        dok = _dokument(False)
        self.assertIs(self._get_zaznam("dokument", dok), dok)

    def test_bezny_dokument_pres_model3d(self):
        """Běžný dokument přes ``model3d`` končí 404."""
        with self.assertRaises(Http404):
            self._get_zaznam("model3d", _dokument(False))

    def test_model3d_pres_dokument(self):
        """3D model přes ``dokument`` končí 404."""
        with self.assertRaises(Http404):
            self._get_zaznam("dokument", _dokument(True))


class ResolveObjectAndNameTest(SimpleTestCase):
    """Ověřuje ``NewFileUploadView._resolve_object_and_name`` pro nesouhlasný ``typ_vazby``."""

    def _resolve(self, typ_vazby, dokument):
        view = NewFileUploadView()
        view.fedora_transaction = mock.Mock()
        request = RequestFactory().post("/")
        request.user = mock.Mock(is_authenticated=False)
        with mock.patch("core.views.Dokument.objects.filter") as flt, mock.patch(
            "core.views.get_next_soubor_name", return_value="X-1-F001.pdf"
        ):
            flt.return_value.first.return_value = dokument
            return view._resolve_object_and_name(request, "X-1", "a.pdf", typ_vazby), view

    def test_shoda_projde(self):
        """Odpovídající kombinace vrátí dvojici objekt a název."""
        dok = _dokument(False)
        (objekt, nazev), _view = self._resolve("dokument", dok)
        self.assertIs(objekt, dok)
        self.assertEqual(nazev, "X-1-F001.pdf")

    def test_bezny_dokument_pres_model3d_je_odmitnut(self):
        """Běžný dokument přes ``model3d`` vrací 400 a ruší transakci."""
        resp, view = self._resolve("model3d", _dokument(False))
        self.assertIsInstance(resp, JsonResponse)
        self.assertEqual(resp.status_code, 400)
        view.fedora_transaction.rollback_transaction.assert_called_once()

    def test_model3d_pres_dokument_je_odmitnut(self):
        """3D model přes ``dokument`` vrací 400."""
        resp, _view = self._resolve("dokument", _dokument(True))
        self.assertEqual(resp.status_code, 400)


class PostMimeWhitelistTest(SimpleTestCase):
    """Ověřuje, že whitelist MIME typů určuje trasa a ne ``source-url`` z POST."""

    def test_source_url_se_bere_z_trasy(self):
        """Klientem zaslané ``source-url`` na modelu 3D se pro trasu ``dokument`` ignoruje."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        request = RequestFactory().post(
            "/", {"file": SimpleUploadedFile("a.pdf", b"x"), "source-url": "/soubor/nahrat/model3d/X-1"}
        )
        request.user = mock.Mock(pk=1, is_authenticated=True)
        with mock.patch("core.views.FedoraTransaction"), mock.patch(
            "core.views.Soubor.check_mime_for_url", return_value=False
        ) as check:
            resp = NewFileUploadView().post(request, typ_vazby="dokument", ident_cely="X-1")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(check.call_args.args[1], "soubor/nahrat/dokument/")
