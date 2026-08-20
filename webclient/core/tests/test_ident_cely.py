"""
Testy přidělování a rozpoznávání identifikátorů po úpravách z issue #3421.

Pokrývají nový sufix projektových akcí (``A##``), rozpoznání identifikátoru v
:func:`core.ident_cely.get_record_from_ident` a odvození řady dokumentu z ručně zadaného
identifikátoru. Testy nepotřebují databázi – dotazy do DB jsou nahrazeny mockem.
"""

import re
from unittest import mock

from core.exceptions import MaximalEventCount
from core.ident_cely import get_dokument_rada_from_ident, get_project_event_ident
from django.test import SimpleTestCase


class _Projekt:
    """Odlehčená náhrada za projekt nesoucí pouze identifikátor."""

    def __init__(self, ident_cely):
        """
        Inicializuje stub projektu.

        :param ident_cely: Identifikátor projektu, ze kterého se odvozují identy akcí.
        """
        self.ident_cely = ident_cely


def _cursor_with(idents):
    """
    Nahradí databázové připojení mockem, jehož dotaz vrátí zadané identifikátory.

    Nahrazuje se celý objekt ``connection`` v modulu, ne jen jeho metoda ``cursor`` – ta je
    v ``SimpleTestCase`` obalená hlídačem přístupu do databáze, který se nesmí přepsat.

    :param idents: Kolekce identifikátorů archeologických záznamů, které má dotaz vrátit.
    :return: Kontextový manažer s mockem databázového připojení.
    """
    cursor = mock.MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.fetchall.return_value = [(index, ident) for index, ident in enumerate(idents)]
    connection = mock.MagicMock()
    connection.cursor.return_value = cursor
    return mock.patch("core.ident_cely.connection", connection)


class ProjectEventIdentTest(SimpleTestCase):
    """Testy sufixu projektových akcí ve tvaru ``A##`` (#3421)."""

    def test_first_event_gets_a01(self):
        """První akce projektu dostane sufix A01."""
        with _cursor_with([]):
            self.assertEqual(get_project_event_ident(_Projekt("C-202302249")), "C-202302249A01")

    def test_next_event_continues_numbering(self):
        """Další akce navazuje na nejvyšší obsazené pořadové číslo."""
        with _cursor_with(["C-202302249A01", "C-202302249A02"]):
            self.assertEqual(get_project_event_ident(_Projekt("C-202302249")), "C-202302249A03")

    def test_historical_letter_suffixes_are_ignored(self):
        """Historické akce označené písmenem číslování neovlivňují, začíná se od A01."""
        with _cursor_with(["C-202302249A", "C-202302249B"]):
            self.assertEqual(get_project_event_ident(_Projekt("C-202302249")), "C-202302249A01")

    def test_occupied_ident_is_skipped(self):
        """Obsazené pořadové číslo se přeskočí (kolize s importovaným identifikátorem)."""
        with _cursor_with(["C-202302249A05", "C-202302249A06"]):
            self.assertEqual(get_project_event_ident(_Projekt("C-202302249")), "C-202302249A07")

    def test_maximum_events_raises(self):
        """Po vyčerpání všech pořadových čísel se vyvolá chyba o překročení maxima."""
        with _cursor_with([f"C-202302249A{number:02d}" for number in range(1, 100)]):
            with self.assertRaises(MaximalEventCount):
                get_project_event_ident(_Projekt("C-202302249"))

    def test_missing_project_ident(self):
        """Projekt bez identifikátoru nedostane ident akce."""
        self.assertIsNone(get_project_event_ident(_Projekt("")))


class RecordFromIdentPatternTest(SimpleTestCase):
    """Testy vzorů pro rozpoznání typu záznamu podle identifikátoru."""

    AKCE = r"(C|M|X-C|X-M)-\d{9}\D{1}\d{0,2}"
    DJ = r"(C|M|X-C|X-M)-\w{7,10}\D{1}\d{0,2}-D\d{2}"
    KOMPONENTA = r"(C|M|X-C|X-M)-\w{7,10}\D{1}\d{0,2}-K\d{3}"
    KOMPONENTA_LOKALITY = r"(C|M|X-C|X-M)-(N|L|K)\d{7,9}-K\d{3}"
    DOKUMENT = r"(C|M|X-C|X-M)-\D{2}-\d{9}"

    def test_akce_pattern_matches_both_suffixes(self):
        """Vzor akce pokrývá historický jednopísmenný i nový dvojciferný sufix."""
        self.assertTrue(re.fullmatch(self.AKCE, "C-202302249A"))
        self.assertTrue(re.fullmatch(self.AKCE, "C-202302249A01"))

    def test_dj_and_komponenta_patterns_match_new_suffix(self):
        """Vzory DJ a komponenty akce fungují i s novým sufixem akce."""
        self.assertTrue(re.fullmatch(self.DJ, "C-202302249A01-D01"))
        self.assertTrue(re.fullmatch(self.DJ, "X-M-9000123456A-D01"))
        self.assertTrue(re.fullmatch(self.KOMPONENTA, "C-202302249A01-K001"))

    def test_komponenta_lokality_pattern(self):
        """Komponenta lokality má vlastní vzor, obecný vzor komponenty na ni nesedí."""
        self.assertIsNone(re.fullmatch(self.KOMPONENTA, "C-N202302249-K001"))
        self.assertTrue(re.fullmatch(self.KOMPONENTA_LOKALITY, "C-N202302249-K001"))
        self.assertTrue(re.fullmatch(self.KOMPONENTA_LOKALITY, "C-K0751394-K001"))

    def test_dokument_ident_is_not_matched_as_akce(self):
        """Identifikátor dokumentu se nesmí zaměnit za akci."""
        self.assertIsNone(re.fullmatch(self.AKCE, "M-DD-202100034"))
        self.assertTrue(re.fullmatch(self.DOKUMENT, "M-DD-202100034"))


class DokumentRadaFromIdentTest(SimpleTestCase):
    """Testy odvození řady dokumentu z ručně zadaného identifikátoru (#3421)."""

    def _with_heslar(self, vysledek):
        """
        Nahradí dotaz do hesláře řad pevnou návratovou hodnotou.

        :param vysledek: Hodnota, kterou má vrátit ``Heslar.objects.filter(...).first()``.
        :return: Kontextový manažer s mockem manageru hesláře.
        """
        manager = mock.MagicMock()
        manager.filter.return_value.first.return_value = vysledek
        return mock.patch("core.ident_cely.Heslar.objects", manager)

    def test_valid_ident_returns_rada(self):
        """Platný identifikátor vrátí heslo řady odpovídající jeho zkratce."""
        rada = object()
        with self._with_heslar(rada):
            self.assertIs(get_dokument_rada_from_ident("M-DD-202100034"), rada)

    def test_unknown_rada_returns_none(self):
        """Neexistující řada v hesláři vede na ``None``."""
        with self._with_heslar(None):
            self.assertIsNone(get_dokument_rada_from_ident("M-ZZ-202100034"))

    def test_invalid_shapes_return_none(self):
        """Neplatné tvary identifikátoru se odmítnou bez dotazu do hesláře."""
        for ident in ("", None, "M-DD-2021000", "X-M-DD-202100034", "C-3D-202100034", "M-DD-202100034-D001"):
            with self.subTest(ident=ident):
                self.assertIsNone(get_dokument_rada_from_ident(ident))
