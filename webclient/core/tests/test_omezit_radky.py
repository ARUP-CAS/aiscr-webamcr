"""Testy omezení řádků tabulek souvisejících záznamů na detailu (tag ``omezit_radky``)."""

from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

from core.constants import (
    SOUVISEJICI_RADKY_BEZ_LIMITU,
    SOUVISEJICI_RADKY_LIMIT,
    SOUVISEJICI_RADKY_PARAM,
    SOUVISEJICI_RADKY_VYSLEDEK_RADKY,
    SOUVISEJICI_RADKY_VYSLEDEK_ZBYVAJICI_URL,
)
from core.templatetags.template_tags import omezit_radky
from django.contrib.auth.models import AnonymousUser
from django.template import Context
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class OmezitRadkyTagTests(SimpleTestCase):
    """Ověřuje řez řádků, URL zbytku a výjimky bez limitu."""

    def setUp(self):
        """Připraví továrnu požadavků a 25 řádků (víc než limit)."""
        self.factory = RequestFactory()
        self.radky = list(range(SOUVISEJICI_RADKY_LIMIT + 5))

    def _context(self, path="/projekt/detail/X", **extra):
        """
        Sestaví kontext šablony s GET požadavkem na ``path``.

        :param path: Cesta včetně případného query stringu.
        :param extra: Další proměnné kontextu (např. ``SOUVISEJICI_RADKY_BEZ_LIMITU``).
        :return: Kontext šablony s ``request``.
        """
        return Context({"request": self.factory.get(path), **extra})

    def test_over_limit_shows_first_rows_and_url_for_rest(self):
        """Nad limitem vrátí prvních 20 řádků a URL se zachovanými parametry a klíčem tabulky."""
        result = omezit_radky(self._context("/ez/odkazy/X?card_type=akce"), self.radky, "ez_odkazy_akce")

        self.assertEqual(result[SOUVISEJICI_RADKY_VYSLEDEK_RADKY], self.radky[:SOUVISEJICI_RADKY_LIMIT])
        url = urlsplit(result[SOUVISEJICI_RADKY_VYSLEDEK_ZBYVAJICI_URL])
        self.assertEqual(url.path, "/ez/odkazy/X")
        self.assertEqual(parse_qs(url.query), {"card_type": ["akce"], SOUVISEJICI_RADKY_PARAM: ["ez_odkazy_akce"]})

    def test_at_limit_shows_all_rows_without_button(self):
        """Přesně 20 řádků se zobrazí celé a bez URL zbytku (bez tlačítka)."""
        radky = self.radky[:SOUVISEJICI_RADKY_LIMIT]
        result = omezit_radky(self._context(), radky, "soubory")

        self.assertEqual(result[SOUVISEJICI_RADKY_VYSLEDEK_RADKY], radky)
        self.assertIsNone(result[SOUVISEJICI_RADKY_VYSLEDEK_ZBYVAJICI_URL])

    def test_request_for_rest_returns_only_rows_past_limit(self):
        """Požadavek tlačítka (``vse_radky=<klic>``) vrátí jen řádky za limitem."""
        context = self._context("/x?%s=soubory" % SOUVISEJICI_RADKY_PARAM)
        result = omezit_radky(context, self.radky, "soubory")

        self.assertEqual(result[SOUVISEJICI_RADKY_VYSLEDEK_RADKY], self.radky[SOUVISEJICI_RADKY_LIMIT:])
        self.assertIsNone(result[SOUVISEJICI_RADKY_VYSLEDEK_ZBYVAJICI_URL])

    def test_request_for_other_table_keeps_this_table_limited(self):
        """Požadavek na zbytek jiné tabulky na stránce tuto tabulku neodemkne."""
        context = self._context("/x?%s=dokumenty" % SOUVISEJICI_RADKY_PARAM)
        result = omezit_radky(context, self.radky, "soubory")

        self.assertEqual(result[SOUVISEJICI_RADKY_VYSLEDEK_RADKY], self.radky[:SOUVISEJICI_RADKY_LIMIT])

    def test_bez_limitu_returns_all_rows(self):
        """Modaly připojení/odpojení (``SOUVISEJICI_RADKY_BEZ_LIMITU``) dostanou všechny řádky."""
        result = omezit_radky(self._context(**{SOUVISEJICI_RADKY_BEZ_LIMITU: True}), self.radky, "dokumenty")

        self.assertEqual(result[SOUVISEJICI_RADKY_VYSLEDEK_RADKY], self.radky)
        self.assertIsNone(result[SOUVISEJICI_RADKY_VYSLEDEK_ZBYVAJICI_URL])

    def test_without_request_returns_all_rows(self):
        """Bez ``request`` v kontextu (render bez požadavku) se neomezuje."""
        result = omezit_radky(Context({}), self.radky, "dokumenty")

        self.assertEqual(result[SOUVISEJICI_RADKY_VYSLEDEK_RADKY], self.radky)


class FiletableOmezeniTests(SimpleTestCase):
    """Ověřuje, že ``core/filetable.html`` vykreslí 20 souborů, tlačítko a na vyžádání zbytek."""

    def setUp(self):
        """Připraví 25 fiktivních souborů a továrnu požadavků."""
        self.factory = RequestFactory()
        self.soubory = [
            SimpleNamespace(id=i, nazev="soubor-%d.pdf" % i, mimetype="application/pdf", size_mb=1, rozsah=1)
            for i in range(1, SOUVISEJICI_RADKY_LIMIT + 6)
        ]

    def _render(self, path):
        """
        Vykreslí filetable pro požadavek na ``path``.

        :param path: Cesta požadavku včetně query stringu.
        :return: Vykreslené HTML.
        """
        context = {"soubory": self.soubory, "show": {}, "ident": "X", "vazba_trida": "projekt", "next_url": "/"}
        request = self.factory.get(path)
        # Project context processors read request.user.
        request.user = AnonymousUser()
        return render_to_string("core/filetable.html", context, request=request)

    def test_first_render_has_20_rows_and_button(self):
        """První vykreslení obsahuje 20 souborů a tlačítko s URL zbytku."""
        html = self._render("/projekt/detail/X")

        self.assertIn("soubor-%d.pdf" % SOUVISEJICI_RADKY_LIMIT, html)
        self.assertNotIn("soubor-%d.pdf" % (SOUVISEJICI_RADKY_LIMIT + 1), html)
        self.assertIn('data-url="/projekt/detail/X?%s=soubory"' % SOUVISEJICI_RADKY_PARAM, html)
        self.assertIn('<tbody data-radky="soubory">', html)

    def test_rest_request_renders_only_remaining_rows(self):
        """Požadavek tlačítka vykreslí jen soubory 21–25 a žádné další tlačítko."""
        html = self._render("/projekt/detail/X?%s=soubory" % SOUVISEJICI_RADKY_PARAM)

        self.assertNotIn("soubor-1.pdf", html)
        self.assertNotIn("soubor-%d.pdf" % SOUVISEJICI_RADKY_LIMIT, html)
        self.assertIn("soubor-%d.pdf" % (SOUVISEJICI_RADKY_LIMIT + 1), html)
        self.assertIn("soubor-%d.pdf" % (SOUVISEJICI_RADKY_LIMIT + 5), html)
        self.assertNotIn("app-nacist-zbyvajici-btn", html)
