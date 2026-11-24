"""
Testy ``check_soubor_vazba`` – shoda ``typ_vazby`` s typem dokumentu (issue #4527).

Testy nepotřebují databázi; vyhledání dokumentu a souborů je nahrazeno mockem.
"""

from unittest import mock

from core.exceptions import ZaznamSouborNotmatching
from core.views import check_soubor_vazba
from django.test import SimpleTestCase
from heslar.hesla_dynamicka import MODEL_3D_DOKUMENT_TYPES

TYP_3D = MODEL_3D_DOKUMENT_TYPES[0]
TYP_JINY = max(MODEL_3D_DOKUMENT_TYPES) + 1


def _dokument(typ_dokumentu_id, pocet_souboru=1):
    """Vytvoří náhradní dokument s daným typem a počtem souborů odpovídajících filtru."""
    from dokument.models import Dokument

    dok = mock.Mock()
    dok.je_model_3d = Dokument.je_model_3d.fget(mock.Mock(typ_dokumentu_id=typ_dokumentu_id))
    dok.soubory.soubory.filter.return_value.count.return_value = pocet_souboru
    return dok


class CheckSouborVazbaTest(SimpleTestCase):
    """Ověřuje, že ``model3d`` a ``dokument`` nelze zaměnit."""

    def _check(self, typ_vazby, dok):
        with mock.patch("core.views.get_object_or_404", return_value=dok):
            return check_soubor_vazba(typ_vazby, "X-C-1", 1)

    def test_bezny_dokument_pres_dokument(self):
        """Běžný dokument projde s ``typ_vazby=dokument``."""
        self.assertTrue(self._check("dokument", _dokument(TYP_JINY)))

    def test_model3d_pres_model3d(self):
        """3D model projde s ``typ_vazby=model3d``."""
        self.assertTrue(self._check("model3d", _dokument(TYP_3D)))

    def test_bezny_dokument_pres_model3d_je_odmitnut(self):
        """Běžný dokument je přes ``typ_vazby=model3d`` odmítnut."""
        with self.assertRaises(ZaznamSouborNotmatching):
            self._check("model3d", _dokument(TYP_JINY))

    def test_model3d_pres_dokument_je_odmitnut(self):
        """3D model je přes ``typ_vazby=dokument`` odmítnut."""
        with self.assertRaises(ZaznamSouborNotmatching):
            self._check("dokument", _dokument(TYP_3D))

    def test_soubor_nepatri_k_dokumentu(self):
        """Soubor, který k dokumentu nepatří, je odmítnut."""
        with self.assertRaises(ZaznamSouborNotmatching):
            self._check("dokument", _dokument(TYP_JINY, pocet_souboru=0))

    def test_neznama_hodnota_typ_vazby(self):
        """Neznámý ``typ_vazby`` vyvolá chybu vazby místo ``UnboundLocalError``."""
        with self.assertRaises(ZaznamSouborNotmatching):
            check_soubor_vazba("neexistuje", "X-C-1", 1)
