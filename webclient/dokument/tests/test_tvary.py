"""
Testy zobrazení sekce tvarů u dokumentu (issue #3421).

Tvary nesou letecké fotografie. Dříve se sekce odvozovala z řady dokumentu, kterou určovala
kombinace typu a materiálu; od #3421 se řada přiděluje fixně, takže nově zapsané letecké
fotografie mají řadu "DD" a rozhoduje typ dokumentu. Databáze se nepoužívá – hodnoty konstant
hesláře jsou nahrazeny mockem.
"""

from unittest import mock

from django.test import SimpleTestCase

#: Náhradní identifikátory typů leteckých fotografií použité místo hodnot z hesláře.
LETECKE_TYPY = [1098, 1102]
#: Identifikátor typu, který mezi letecké fotografie nepatří (např. plán lokality).
JINY_TYP = 1106
#: Náhradní identifikátory historických leteckých řad dokumentu.
LETECKE_RADY = [880, 882]
#: Identifikátor řady, která mezi letecké řady nepatří (např. výchozí řada).
JINA_RADA = 871


def _dokument(typ_dokumentu_id, rada_id):
    """
    Sestaví náhradu za dokument s poli, na která se funkce dotazuje.

    :param typ_dokumentu_id: Identifikátor typu dokumentu.
    :param rada_id: Identifikátor řady dokumentu, nebo ``None`` pro dokument bez řady.
    :return: Mock dokumentu.
    """
    return mock.Mock(typ_dokumentu_id=typ_dokumentu_id, rada_id=rada_id)


def _ma_tvary(dokument):
    """
    Spustí zjištění evidence tvarů s náhradními konstantami hesláře.

    :param dokument: Náhrada za dokument.
    :return: ``True`` pokud se u dokumentu mají zobrazit tvary.
    """
    from dokument import views

    with mock.patch.object(views, "LETECKE_DOKUMENT_TYPES", LETECKE_TYPY):
        with mock.patch.object(views, "LETECKE_RADY_DOKUMENTU", LETECKE_RADY):
            return views.dokument_ma_tvary(dokument)


class DokumentMaTvaryTest(SimpleTestCase):
    """Testy funkce :func:`dokument.views.dokument_ma_tvary`."""

    def test_letecka_fotografie_ve_vychozi_rade(self):
        """Nově zapsaná letecká fotografie má řadu "DD" a tvary se u ní evidují."""
        self.assertTrue(_ma_tvary(_dokument(LETECKE_TYPY[0], JINA_RADA)))

    def test_letecka_fotografie_v_letecke_rade(self):
        """Dříve zapsaná letecká fotografie zůstává v letecké řadě a tvary má dál."""
        self.assertTrue(_ma_tvary(_dokument(LETECKE_TYPY[1], LETECKE_RADY[1])))

    def test_letecka_rada_bez_leteckeho_typu(self):
        """O tvarech rozhoduje i samotná historická letecká řada, kvůli importovaným datům."""
        self.assertTrue(_ma_tvary(_dokument(JINY_TYP, LETECKE_RADY[0])))

    def test_jiny_typ_ve_vychozi_rade_tvary_nema(self):
        """Dokument, který není letecká fotografie, sekci tvarů nezobrazuje."""
        self.assertFalse(_ma_tvary(_dokument(JINY_TYP, JINA_RADA)))

    def test_dokument_bez_rady(self):
        """Chybějící řada nesmí vyhodnocení shodit; rozhodne samotný typ dokumentu."""
        self.assertFalse(_ma_tvary(_dokument(JINY_TYP, None)))
        self.assertTrue(_ma_tvary(_dokument(LETECKE_TYPY[0], None)))
