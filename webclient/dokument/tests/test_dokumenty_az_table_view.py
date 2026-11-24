"""
Test ``DokumentyAzTableView`` – oprávnění odpojení dokumentu ve větvi projektu (review PR #4538).

Test nepotřebuje databázi; dotazy a vykreslení šablony jsou nahrazeny mocky.
"""

from unittest import mock

from django.test import RequestFactory, SimpleTestCase
from dokument.views import DokumentyAzTableView


class DokumentyAzTableViewTest(SimpleTestCase):
    """Ověřuje, že ``dokument_odpojit`` je skutečná pravdivostní hodnota oprávnění."""

    def _context(self, povoleno):
        request = RequestFactory().get("/")
        request.user = mock.Mock()
        with mock.patch("dokument.views.Dokument"), mock.patch("dokument.views.Projekt"), mock.patch(
            "dokument.views.check_permissions", return_value=povoleno
        ), mock.patch("dokument.views.render_to_string", return_value="") as render:
            DokumentyAzTableView().get(request, "projekt", "P-1")
        return render.call_args.args[1]

    def test_bez_opravneni(self):
        """Bez oprávnění je ``dokument_odpojit`` ``False``, ne neprázdná n-tice."""
        self.assertIs(self._context(False)["show"]["dokument_odpojit"], False)

    def test_s_opravnenim(self):
        """S oprávněním je ``dokument_odpojit`` ``True``."""
        self.assertIs(self._context(True)["show"]["dokument_odpojit"], True)
