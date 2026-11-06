"""
Hlídá vyhrazené klíče v ``extra`` volání loggeru (issue #4397).

Sken zachytí klíče, které jsou ve zdrojovém kódu zapsané jako literál: slovník předaný přímo
v ``extra={...}``, slovník přiřazený do proměnné, která se pak předává jako ``extra=promenna``
nebo rozbaluje jako ``extra={**promenna}``, a přiřazení ``promenna["klic"] = ...`` v téže funkci.
Klíče skládané dynamicky (např. z proměnné jako klíče) sken nevidí.
"""

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
#: Pole, která nastavuje formatter ``python-logstash`` (``LogstashFormatterVersion1``) – klíč z ``extra`` je přepíše.
POLE_FORMATTERU = {"@timestamp", "@version", "path", "type", "host", "level", "logger_name", "tags"}
#: Pole, která formatter přidá z ``get_debug_fields()`` při ``exc_info`` až po ``extra`` (``lineno``,
#: ``process`` a ``funcName`` jsou zároveň atributy ``LogRecord``, ty hlídá ``ATRIBUTY_LOGRECORD``).
POLE_FORMATTERU_PRI_VYJIMCE = {"stack_trace", "thread_name"}
#: Pole, která nastavuje ``core.logging_filters.UserLogFilter`` – hodnota z ``extra`` se ztratí.
POLE_FILTRU = {"url", "user_id"}


def _literalni_klice(slovnik):
    """
    Vrátí literální řetězcové klíče slovníku spolu s čísly řádků.

    :param slovnik: Uzel ``ast.Dict``.
    :return: Seznam dvojic ``(řádek, klíč)``.
    """
    return [(k.lineno, k.value) for k in slovnik.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)]


def _klice_ve_funkci(funkce):
    """
    Najde klíče ``extra`` v jedné funkci (nebo v těle modulu).

    Nejdřív zjistí jména proměnných předávaných jako ``extra=promenna`` nebo rozbalovaných
    v ``extra={**promenna}``, potom posbírá klíče z literálních slovníků přiřazených do těchto
    proměnných a z přiřazení ``promenna["klic"] = ...``.

    :param funkce: Uzel funkce nebo modulu.
    :return: Seznam dvojic ``(řádek, klíč)``.
    """
    nalezene = []
    promenne = set()
    for uzel in ast.walk(funkce):
        if not isinstance(uzel, ast.Call):
            continue
        for kw in uzel.keywords:
            if kw.arg != "extra":
                continue
            if isinstance(kw.value, ast.Name):
                promenne.add(kw.value.id)
            elif isinstance(kw.value, ast.Dict):
                nalezene += _literalni_klice(kw.value)
                promenne |= {
                    v.id for k, v in zip(kw.value.keys, kw.value.values) if k is None and isinstance(v, ast.Name)
                }
    for uzel in ast.walk(funkce):
        if not isinstance(uzel, ast.Assign):
            continue
        for cil in uzel.targets:
            if isinstance(cil, ast.Name) and cil.id in promenne and isinstance(uzel.value, ast.Dict):
                nalezene += _literalni_klice(uzel.value)
            elif (
                isinstance(cil, ast.Subscript)
                and isinstance(cil.value, ast.Name)
                and cil.value.id in promenne
                and isinstance(cil.slice, ast.Constant)
                and isinstance(cil.slice.value, str)
            ):
                nalezene.append((cil.lineno, cil.slice.value))
    return nalezene


def _extra_klice():
    """
    Projde zdrojové soubory a vrátí klíče předávané v ``extra``.

    :return: Seznam trojic ``(soubor, řádek, klíč)``; duplicity (klíč nalezený z vnější
        i vnořené funkce) jsou odstraněné.
    """
    nalezene = set()
    for soubor in WEBCLIENT.rglob("*.py"):
        if VYNECHANE_ADRESARE & set(soubor.relative_to(WEBCLIENT).parts):
            continue
        strom = ast.parse(soubor.read_text(encoding="utf-8"))
        cesta = soubor.relative_to(WEBCLIENT).as_posix()
        rozsahy = [strom] + [u for u in ast.walk(strom) if isinstance(u, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for rozsah in rozsahy:
            for radek, klic in _klice_ve_funkci(rozsah):
                nalezene.add((cesta, radek, klic))
    return sorted(nalezene)


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

    def test_sken_vidi_extra_v_promenne(self):
        """Sken zachytí i ``extra`` sestavené v proměnné (``payload`` ve slow_request middlewaru)."""
        self.assertIn("view_name", {k for s, _, k in self.klice if s == "core/log_middleware.py"})

    def test_zadny_atribut_logrecord(self):
        """Klíč jako ``name`` nebo ``message`` vyhodí ``KeyError`` a volání loggeru spadne."""
        kolize = [f"{s}:{r} {k}" for s, r, k in self.klice if k in ATRIBUTY_LOGRECORD]
        self.assertEqual(kolize, [])

    def test_zadne_pole_formatteru_ani_filtru(self):
        """Klíč jako ``level`` přepíše úroveň logu, ``url`` přepíše ``UserLogFilter``."""
        kolize = [
            f"{s}:{r} {k}" for s, r, k in self.klice if k in POLE_FORMATTERU | POLE_FORMATTERU_PRI_VYJIMCE | POLE_FILTRU
        ]
        self.assertEqual(kolize, [])
