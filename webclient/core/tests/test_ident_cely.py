"""
Testy přidělování a rozpoznávání identifikátorů po úpravách z issue #3421.

Pokrývají nový sufix projektových akcí (``A##``), rozpoznání identifikátoru v
:func:`core.ident_cely.get_record_from_ident` a odvození řady dokumentu z ručně zadaného
identifikátoru. Testy nepotřebují databázi – dotazy do DB jsou nahrazeny mockem.
"""

from unittest import mock

from core.exceptions import MaximalEventCount
from core.ident_cely import (
    get_dokument_rada_from_ident,
    get_dokument_region_from_ident,
    get_project_event_ident,
    get_record_from_ident,
)
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


class RecordFromIdentTest(SimpleTestCase):
    """
    Testy rozpoznání typu záznamu podle identifikátoru v :func:`core.ident_cely.get_record_from_ident`.

    Volá se přímo produkční funkce; dohledání záznamu v databázi je nahrazeno mockem, který vrací
    název modelu a dohledávaný identifikátor. Změna vzorů v produkčním kódu se tak v testech projeví.
    """

    def _rozpoznej(self, ident_cely):
        """
        Vrátí dvojici (model, dohledávaný identifikátor), kterou by funkce předala do databáze.

        :param ident_cely: Rozpoznávaný identifikátor.
        :return: Dvojice názvu modelu a identifikátoru, nebo ``None`` pokud identifikátor nerozpozná.
        """

        def podvrh(model, **kwargs):
            return model.__name__, kwargs.get("ident_cely")

        with mock.patch("core.ident_cely.get_object_or_404", side_effect=podvrh):
            return get_record_from_ident(ident_cely)

    def test_akce_stary_i_novy_sufix(self):
        """Projektová akce se rozpozná s historickým jednopísmenným i novým dvojciferným sufixem."""
        self.assertEqual(self._rozpoznej("C-202302249A"), ("ArcheologickyZaznam", "C-202302249A"))
        self.assertEqual(self._rozpoznej("C-202302249A01"), ("ArcheologickyZaznam", "C-202302249A01"))
        self.assertEqual(self._rozpoznej("X-M-000001234A01"), ("ArcheologickyZaznam", "X-M-000001234A01"))

    def test_samostatna_akce(self):
        """Samostatná akce si ponechává písmenný sufix."""
        self.assertEqual(self._rozpoznej("X-M-9000123456A"), ("ArcheologickyZaznam", "X-M-9000123456A"))

    def test_dokumentacni_jednotka_akce(self):
        """Dokumentační jednotka akce se rozpozná se starým i novým sufixem akce."""
        self.assertEqual(self._rozpoznej("C-202302249A-D01"), ("DokumentacniJednotka", "C-202302249A-D01"))
        self.assertEqual(self._rozpoznej("C-202302249A01-D01"), ("DokumentacniJednotka", "C-202302249A01-D01"))

    def test_komponenta_akce(self):
        """Komponenta akce se rozpozná se starým i novým sufixem akce."""
        self.assertEqual(self._rozpoznej("C-202302249A-K001"), ("Komponenta", "C-202302249A-K001"))
        self.assertEqual(self._rozpoznej("C-202302249A01-K001"), ("Komponenta", "C-202302249A01-K001"))

    def test_lokalita_a_jeji_potomci(self):
        """Lokalita, její dokumentační jednotka i komponenta se rozpoznají jako správné typy."""
        self.assertEqual(self._rozpoznej("C-N1000001"), ("ArcheologickyZaznam", "C-N1000001"))
        self.assertEqual(self._rozpoznej("C-N1000001-D01"), ("DokumentacniJednotka", "C-N1000001-D01"))
        self.assertEqual(self._rozpoznej("C-N1000001-K001"), ("Komponenta", "C-N1000001-K001"))
        self.assertEqual(self._rozpoznej("C-K0751394-K001"), ("Komponenta", "C-K0751394-K001"))

    def test_dokument_neni_zamenen_za_akci(self):
        """Identifikátor dokumentu a jeho části vedou na dokument, ne na archeologický záznam."""
        self.assertEqual(self._rozpoznej("M-DD-202100034"), ("Dokument", "M-DD-202100034"))
        self.assertEqual(self._rozpoznej("M-DD-202100034-D001"), ("Dokument", "M-DD-202100034"))
        self.assertEqual(self._rozpoznej("M-DD-202100034-K001"), ("Dokument", "M-DD-202100034"))

    def test_projekt_a_samostatny_nalez(self):
        """Projekt a samostatný nález se nezamění s projektovou akcí."""
        self.assertEqual(self._rozpoznej("C-202302249"), ("Projekt", "C-202302249"))
        self.assertEqual(self._rozpoznej("C-202302249-N00001"), ("SamostatnyNalez", "C-202302249-N00001"))


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

    def test_nulove_poradi_se_odmitne(self):
        """Pořadí 00000 se odmítne, protože by rozbilo hledání mezer při přidělování trvalých identů."""
        with self._with_heslar(object()):
            self.assertIsNone(get_dokument_rada_from_ident("M-DD-202600000"))
            self.assertIsNotNone(get_dokument_rada_from_ident("M-DD-202600001"))

    def test_unicodove_cislice_se_odmitnou(self):
        """Číslice mimo ASCII (např. arabské) se nepřijmou jako pořadí identifikátoru."""
        with self._with_heslar(object()):
            self.assertIsNone(get_dokument_rada_from_ident("M-DD-٢٠٢٦٠٠٠٠١"))


class DokumentRegionFromIdentTest(SimpleTestCase):
    """Testy odvození regionu z ručně zadaného identifikátoru dokumentu (#3421)."""

    def test_region_prefix(self):
        """Vrací se prefix regionu včetně pomlčky, tedy ve tvaru hodnot pole ``region``."""
        self.assertEqual(get_dokument_region_from_ident("M-DD-202100034"), "M-")
        self.assertEqual(get_dokument_region_from_ident("C-TX-198500123"), "C-")

    def test_invalid_shapes_return_none(self):
        """Neplatné tvary identifikátoru vrací ``None``, aby se kontrola regionu neprováděla."""
        for ident in ("", None, "M-DD-2021000", "X-M-DD-202100034", "C-3D-202100034", "M-DD-202600000"):
            with self.subTest(ident=ident):
                self.assertIsNone(get_dokument_region_from_ident(ident))
