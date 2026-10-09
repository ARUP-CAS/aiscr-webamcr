"""Testy modulu výjimek ``core.exceptions``."""

from django.test import SimpleTestCase


class NepouzivaneVyjimkyTest(SimpleTestCase):
    """Hlídá, že se do modulu nevrátí odstraněné nepoužívané výjimky (issue #4291)."""

    def test_neocekavana_rada_error_je_odstranena(self):
        """Výjimka ``NeocekavanaRadaError`` neměla v kódu žádné použití a byla odstraněna."""
        from core import exceptions

        self.assertFalse(hasattr(exceptions, "NeocekavanaRadaError"))
