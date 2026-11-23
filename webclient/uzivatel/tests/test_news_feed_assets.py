"""Kontroly zdrojových stylů a skriptů pro responzivní obrázky v novinkách."""

from pathlib import Path

from django.test import SimpleTestCase


class NewsFeedResponsiveAssetsTest(SimpleTestCase):
    """Ověří omezení rozměrů obrázků a přepočet výšky novinek po jejich načtení."""

    @classmethod
    def setUpClass(cls):
        """Načte šablonu a styly používané při testech obrázků."""
        super().setUpClass()
        app_root = Path(__file__).resolve().parents[2]
        cls.scss = (app_root / "static" / "scss" / "_app-login.scss").read_text(encoding="utf-8")
        cls.template = (app_root / "templates" / "registration" / "login.html").read_text(encoding="utf-8")

    def test_embedded_images_are_constrained_without_changing_thumbnail_rules(self):
        """Ověří omezení vložených obrázků a zachování stylu náhledů."""
        embedded_rule = self.scss.split(".news-item-html", 1)[1].split("// ── Obrázek položky", 1)[0]
        self.assertIn("max-width: 100%", embedded_rule)
        self.assertIn("height: auto", embedded_rule)
        self.assertIn("max-height: 80px", self.scss)

    def test_loaded_and_cached_images_recalculate_expanded_height(self):
        """Ověří přepočet výšky po načtení i při použití uložených obrázků."""
        self.assertIn('querySelectorAll(".news-item-html img")', self.template)
        self.assertIn('image.addEventListener("load", recalculateAfterImageLoad)', self.template)
        self.assertIn("image.complete && image.naturalWidth > 0", self.template)
        self.assertIn("updateCollapsedHeight();", self.template)
