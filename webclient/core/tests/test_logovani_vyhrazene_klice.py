"""Hlídá, že žádné volání loggeru nepoužívá v ``extra`` vyhrazený klíč (issue #4397)."""

import ast
import logging
from pathlib import Path

from django.test import SimpleTestCase

WEBCLIENT = Path(__file__).resolve().parents[2]
VYNECHANE_ADRESARE = {"migrations", "node_modules", "static", "tests", "__pycache__"}

#: Atributy ``LogRecord`` – ``Logger.makeRecord`` při takovém klíči v ``extra`` vyhodí ``KeyError``.
ATRIBUTY_LOGRECORD = set(logging.LogRecord("x", logging.INFO, "x", 1, "x", None, None).__dict__) | {
    "message",
    "asctime",
}
#: Pole, která nastavuje ``python-logstash`` formatter – klíč z ``extra`` je přepíše.
POLE_FORMATTERU = {"path", "type", "host", "level", "logger_name", "tags"}
#: Pole, která nastavuje ``core.logging_filters.UserLogFilter`` – hodnota z ``extra`` se ztratí.
POLE_FILTRU = {"url", "user_id"}


def _extra_klice():
    """
    Projde zdrojové soubory a vrátí všechny literální klíče předávané v ``extra=``.

    :return: Seznam trojic ``(soubor, řádek, klíč)``.
    """
    nalezene = []
    for soubor in WEBCLIENT.rglob("*.py"):
        if VYNECHANE_ADRESARE & set(soubor.relative_to(WEBCLIENT).parts):
            continue
        strom = ast.parse(soubor.read_text(encoding="utf-8"))
        for uzel in ast.walk(strom):
            if not isinstance(uzel, ast.Call):
                continue
            for kw in uzel.keywords:
                if kw.arg == "extra" and isinstance(kw.value, ast.Dict):
                    for klic in kw.value.keys:
                        if isinstance(klic, ast.Constant) and isinstance(klic.value, str):
                            nalezene.append((soubor.relative_to(WEBCLIENT).as_posix(), klic.lineno, klic.value))
    return nalezene


class VyhrazeneKliceExtraTest(SimpleTestCase):
    """Vyhrazený klíč v ``extra`` buď shodí volání loggeru, nebo tiše přepíše či ztratí data."""

    @classmethod
    def setUpClass(cls):
        """Projde zdrojové soubory jen jednou pro všechny testy."""
        super().setUpClass()
        cls.klice = _extra_klice()

    def test_sken_nasel_volani(self):
        """Pojistka, že sken skutečně prochází kód (jinak by ostatní testy prošly naprázdno)."""
        self.assertGreater(len(self.klice), 1000)

    def test_zadny_atribut_logrecord(self):
        """Klíč jako ``name`` nebo ``message`` vyhodí ``KeyError`` a volání loggeru spadne."""
        kolize = [f"{s}:{r} {k}" for s, r, k in self.klice if k in ATRIBUTY_LOGRECORD]
        self.assertEqual(kolize, [])

    def test_zadne_pole_formatteru_ani_filtru(self):
        """Klíč jako ``level`` přepíše úroveň logu, ``url`` přepíše ``UserLogFilter``."""
        kolize = [f"{s}:{r} {k}" for s, r, k in self.klice if k in POLE_FORMATTERU | POLE_FILTRU]
        self.assertEqual(kolize, [])
