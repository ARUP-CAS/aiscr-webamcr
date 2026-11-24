"""
Testy šablony řádku tabulky dokumentů ``dokument_table_row.html`` (review PR #4538, issue #4527).

Řádek se vykresluje i pro modely 3D, proto musí náhledy a odkaz na detail odpovídat typu dokumentu.
Testy nepotřebují databázi; dokument je nahrazen jednoduchým objektem.
"""

from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import SimpleTestCase


def _dokument(je_model_3d):
    """Vytvoří náhradní dokument s náhledem a daným typem (3D model / běžný dokument)."""
    return SimpleNamespace(
        id=1,
        ident_cely="C-3D-000000001" if je_model_3d else "C-TX-000000001",
        je_model_3d=je_model_3d,
        thumbnail_image=7,
        get_stav_display="Archivovaný",
    )


class DokumentTableRowTest(SimpleTestCase):
    """Ověřuje ``typ_vazby`` v odkazech náhledu a odkaz na detail podle typu dokumentu."""

    def _render(self, je_model_3d):
        return render_to_string("dokument/dokument_table_row.html", {"d": _dokument(je_model_3d), "prefix": "x"})

    def test_bezny_dokument(self):
        """Běžný dokument má náhledy s ``dokument`` a odkaz na běžný detail."""
        html = self._render(False)
        self.assertIn("/soubor/stahnout-nahled/dokument/C-TX-000000001/7", html)
        self.assertIn("/soubor/stahnout-nahled-velky/dokument/C-TX-000000001/7", html)
        self.assertIn("/dokument/detail/C-TX-000000001", html)

    def test_model_3d(self):
        """3D model má náhledy s ``model3d`` a odkaz na detail modelu 3D."""
        html = self._render(True)
        self.assertIn("/soubor/stahnout-nahled/model3d/C-3D-000000001/7", html)
        self.assertIn("/soubor/stahnout-nahled-velky/model3d/C-3D-000000001/7", html)
        self.assertIn("/dokument/model/detail/C-3D-000000001", html)
