"""
Jednotkové testy pravidel pro názvy distribucí (``core.distribution_names``, issue #3527).

Pravidla sdílí validace importního CSV i connector, takže se testují na jednom místě
a bez databáze — jde o čisté funkce nad řetězci.
"""

from core.distribution_names import (
    find_distribution_prefix_collisions,
    has_unsafe_distribution_segments,
    is_reserved_distribution_name,
    normalize_distribution_name,
)
from django.test import SimpleTestCase


class NormalizeDistributionNameTest(SimpleTestCase):
    """Testy pro ``normalize_distribution_name``."""

    def test_strips_whitespace_and_surrounding_slashes(self):
        """Bílé znaky a okrajová lomítka se odstraní, vnitřní struktura zůstane."""
        self.assertEqual(normalize_distribution_name(" /ocr/alto-xml/ "), "ocr/alto-xml")

    def test_empty_input_yields_empty_string(self):
        """``None`` i prázdný vstup dají prázdný řetězec, ne výjimku."""
        self.assertEqual(normalize_distribution_name(None), "")
        self.assertEqual(normalize_distribution_name("   "), "")


class IsReservedDistributionNameTest(SimpleTestCase):
    """Testy pro ``is_reserved_distribution_name`` včetně vyhrazeného podstromu."""

    def test_exact_reserved_names(self):
        """Vyhrazené názvy samotné se odmítnou."""
        for name in ("orig", "paradata", "thumb/page"):
            with self.subTest(name=name):
                self.assertTrue(is_reserved_distribution_name(name))

    def test_whole_subtree_under_a_reserved_name(self):
        """Vyhrazený je i celý podstrom — jinak by šlo zapsat do chráněného kontejneru."""
        for name in ("paradata/alto-xml", "paradata/ocr/alto-xml", "orig/x", "thumb/page/1"):
            with self.subTest(name=name):
                self.assertTrue(is_reserved_distribution_name(name))

    def test_thumb_containers_are_not_reserved(self):
        """``thumb`` a ``thumb-large`` zůstávají zapisovatelné (zadání #3527)."""
        for name in ("thumb", "thumb-large", "thumb/other"):
            with self.subTest(name=name):
                self.assertFalse(is_reserved_distribution_name(name))

    def test_names_only_sharing_a_prefix_are_allowed(self):
        """Shoda na začátku řetězce nestačí — hranicí je celý segment cesty."""
        for name in ("paradata-extra", "origx", "ocr/alto-xml"):
            with self.subTest(name=name):
                self.assertFalse(is_reserved_distribution_name(name))

    def test_normalizes_before_deciding(self):
        """Rozhoduje se až nad normalizovanou hodnotou, takže obalení lomítky nepomůže."""
        self.assertTrue(is_reserved_distribution_name(" /paradata/alto-xml/ "))


class HasUnsafeDistributionSegmentsTest(SimpleTestCase):
    """Testy pro ``has_unsafe_distribution_segments``."""

    def test_detects_empty_and_traversal_segments(self):
        """Prázdný segment i průchod adresáři se odhalí."""
        for name in ("ocr//alto", "ocr/../orig", "ocr/./alto", ".."):
            with self.subTest(name=name):
                self.assertTrue(has_unsafe_distribution_segments(name))

    def test_allows_ordinary_nested_names(self):
        """Běžný vnořený název projde."""
        self.assertFalse(has_unsafe_distribution_segments("ocr/alto-xml"))


class FindDistributionPrefixCollisionsTest(SimpleTestCase):
    """Testy pro ``find_distribution_prefix_collisions``."""

    def test_reports_ancestor_descendant_pair(self):
        """Název, který je předkem jiného, se ohlásí jako kolize."""
        self.assertEqual(find_distribution_prefix_collisions(["ocr", "ocr/alto-xml"]), [("ocr", "ocr/alto-xml")])

    def test_no_collision_for_sibling_names(self):
        """Sourozenecké názvy spolu nekolidují."""
        self.assertEqual(find_distribution_prefix_collisions(["ocr/alto-xml", "ocr/hocr"]), [])

    def test_shared_string_prefix_is_not_a_collision(self):
        """Kolizí je jen celý segment cesty, ne shoda na začátku řetězce."""
        self.assertEqual(find_distribution_prefix_collisions(["ocr", "ocrx"]), [])

    def test_duplicates_and_whitespace_do_not_create_a_false_collision(self):
        """Tentýž název dvakrát (i s mezerami) není kolize sám se sebou."""
        self.assertEqual(find_distribution_prefix_collisions([" ocr ", "ocr", "/ocr/"]), [])

    def test_empty_names_are_ignored(self):
        """Prázdné hodnoty se přeskočí, nezpůsobí pád ani falešnou kolizi."""
        self.assertEqual(find_distribution_prefix_collisions(["", None, "ocr"]), [])

    def test_reports_every_descendant_of_the_same_ancestor(self):
        """Předek se ohlásí ke každému svému potomkovi."""
        self.assertEqual(
            find_distribution_prefix_collisions(["ocr", "ocr/a", "ocr/b"]),
            [("ocr", "ocr/a"), ("ocr", "ocr/b")],
        )
