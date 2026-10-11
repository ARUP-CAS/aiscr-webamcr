"""
Testy kontrol před změnou stavu archeologického záznamu a projektu vůči připojeným dokumentům (#4279).

Archivované připojené dokumenty (často neúplná data ze staršího importu) nesmějí blokovat
odeslání ani archivaci AZ, ani uzavření a archivaci projektu. Nearchivované připojené dokumenty
se při odeslání AZ kontrolují dál, při archivaci AZ zůstává jen měkká brána k potvrzení.

Relace modelů jsou nahrazeny jednoduchými náhradami, testy proto nepotřebují databázi.
"""

from unittest.mock import Mock, PropertyMock, patch

from arch_z.models import ArcheologickyZaznam
from core.constants import AZ_STAV_ARCHIVOVANY, AZ_STAV_ODESLANY, D_STAV_ARCHIVOVANY, D_STAV_ODESLANY, PIAN_POTVRZEN
from django.test import SimpleTestCase
from heslar.hesla_dynamicka import TYP_PROJEKTU_ZACHRANNY_ID
from projekt.models import Projekt

#: Varování, které vrací kontrola neúplného dokumentu.
CHYBI_POPIS = "Chybí popis."


class FakeCastiDokumentu:
    """
    Náhrada related manageru ``casti_dokumentu`` nad seznamem částí dokumentu.

    Podporuje jen volání, která používají kontroly před změnou stavu AZ.
    """

    def __init__(self, casti):
        self.casti = list(casti)

    def all(self):
        """
        Vrátí všechny části dokumentu.

        :return: Seznam částí dokumentu.
        """
        return list(self.casti)

    def filter(self, **kwargs):
        """
        Náhrada filtru na nálezovou zprávu; ta je v testech řešena přes ``akce.je_nz``.

        :param kwargs: Podmínky filtru (ignorují se).
        :return: Prázdný seznam.
        """
        return []

    def exclude(self, **kwargs):
        """
        Vynechá části s archivovaným dokumentem.

        :param kwargs: Podmínky; podporováno jen ``dokument__stav=D_STAV_ARCHIVOVANY``.
        :return: Nová náhrada s nearchivovanými částmi.
        :raises AssertionError: Při jiné podmínce, než kterou používá kontrola AZ.
        """
        if kwargs != {"dokument__stav": D_STAV_ARCHIVOVANY}:
            raise AssertionError(f"Neočekávaný exclude: {kwargs}")
        return FakeCastiDokumentu(c for c in self.casti if c.dokument.stav != D_STAV_ARCHIVOVANY)

    def select_related(self, *args):
        """
        Bez efektu, jen zachová řetězení volání.

        :param args: Názvy relací (ignorují se).
        :return: Tutéž náhradu.
        """
        return self

    def __iter__(self):
        """
        Iteruje přes části dokumentu.

        :return: Iterátor částí.
        """
        return iter(self.casti)


def dokument_cast(ident_cely, stav, warnings):
    """
    Vytvoří náhradu části dokumentu s dokumentem v daném stavu.

    :param ident_cely: Identifikátor dokumentu.
    :param stav: Stav dokumentu.
    :param warnings: Výsledek ``Dokument.check_pred_odeslanim``.
    :return: Náhrada ``DokumentCast``.
    """
    dokument = Mock(ident_cely=ident_cely, stav=stav)
    dokument.check_pred_odeslanim.return_value = list(warnings)
    return Mock(dokument=dokument)


class CheckStavuAZTestBase(SimpleTestCase):
    """Společná příprava validní akce, které chybí jen kontrolované připojené dokumenty."""

    def setUp(self):
        """Připraví odeslanou akci a nahradí její relace na akci, DJ a části dokumentu."""
        self.az = ArcheologickyZaznam(
            ident_cely="C-202400001A", typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_AKCE, stav=AZ_STAV_ODESLANY
        )
        # Validní akce s nálezovou zprávou (je_nz) a jednou zápornou DJ s potvrzeným PIANem.
        self.akce = Mock(je_nz=True, odlozena_nz=False)
        dj = Mock(ident_cely="C-202400001A-D01", negativni_jednotka=True, pian=Mock(stav=PIAN_POTVRZEN))
        self.dokumentacni_jednotky = Mock()
        self.dokumentacni_jednotky.all.return_value = [dj]
        self.casti = FakeCastiDokumentu([])
        for attr, value in (
            ("akce", self.akce),
            ("dokumentacni_jednotky_akce", self.dokumentacni_jednotky),
            ("casti_dokumentu", None),
        ):
            patcher = patch.object(ArcheologickyZaznam, attr, new_callable=PropertyMock)
            mock = patcher.start()
            self.addCleanup(patcher.stop)
            if attr == "casti_dokumentu":
                mock.side_effect = lambda: self.casti
            else:
                mock.return_value = value

    def pripoj(self, *casti):
        """
        Nastaví části dokumentu připojené k testované AZ.

        :param casti: Náhrady částí dokumentu.
        :return: Předané části (pro rozbalení v testu).
        """
        self.casti = FakeCastiDokumentu(casti)
        return casti


class CheckPredOdeslanimTests(CheckStavuAZTestBase):
    """Odeslání AZ: kontrolují se jen připojené dokumenty, které dosud nejsou archivované."""

    def test_bez_dokumentu_projde(self):
        """Validní akce bez připojených dokumentů projde kontrolou před odesláním."""
        self.assertEqual(self.az.check_pred_odeslanim(), [])

    def test_archivovany_neuplny_dokument_neblokuje(self):
        """Archivovaný neúplný dokument neblokuje odeslání AZ a jeho kontrola se nevolá."""
        (cast,) = self.pripoj(dokument_cast("C-TX-202400001", D_STAV_ARCHIVOVANY, [CHYBI_POPIS]))

        self.assertEqual(self.az.check_pred_odeslanim(), [])
        cast.dokument.check_pred_odeslanim.assert_not_called()

    def test_nearchivovany_neuplny_dokument_blokuje(self):
        """Nearchivovaný neúplný dokument blokuje odeslání AZ se stejným výčtem chyb jako dřív."""
        (cast,) = self.pripoj(dokument_cast("C-TX-202400002", D_STAV_ODESLANY, [CHYBI_POPIS, "Chybí jazyk."]))

        self.assertEqual(self.az.check_pred_odeslanim(), ["Dokument C-TX-202400002: Chybí popis., Chybí jazyk."])
        cast.dokument.check_pred_odeslanim.assert_called_once_with()

    def test_kombinace_hlasi_jen_nearchivovany_dokument(self):
        """Z archivovaného a nearchivovaného neúplného dokumentu se nahlásí jen nearchivovaný."""
        self.pripoj(
            dokument_cast("C-TX-202400001", D_STAV_ARCHIVOVANY, [CHYBI_POPIS]),
            dokument_cast("C-TX-202400002", D_STAV_ODESLANY, [CHYBI_POPIS]),
        )

        self.assertEqual(self.az.check_pred_odeslanim(), ["Dokument C-TX-202400002: Chybí popis."])

    def test_vypnuta_kontrola_dokumentu(self):
        """S ``kontrolovat_dokumenty=False`` se nekontroluje ani nearchivovaný dokument."""
        (cast,) = self.pripoj(dokument_cast("C-TX-202400002", D_STAV_ODESLANY, [CHYBI_POPIS]))

        self.assertEqual(self.az.check_pred_odeslanim(kontrolovat_dokumenty=False), [])
        cast.dokument.check_pred_odeslanim.assert_not_called()


class CheckPredArchivaciTests(CheckStavuAZTestBase):
    """Archivace AZ: obsah připojených dokumentů se nekontroluje, nearchivované jdou do měkké brány."""

    def test_archivovany_neuplny_dokument_neblokuje(self):
        """Archivovaný neúplný dokument neblokuje archivaci AZ ani nejde do varování k potvrzení."""
        (cast,) = self.pripoj(dokument_cast("C-TX-202400001", D_STAV_ARCHIVOVANY, [CHYBI_POPIS]))

        self.assertEqual(self.az.check_pred_archivaci(), ([], []))
        cast.dokument.check_pred_odeslanim.assert_not_called()

    def test_nearchivovany_neuplny_dokument_jen_k_potvrzeni(self):
        """Nearchivovaný neúplný dokument archivaci AZ neblokuje, jen jde do varování k potvrzení."""
        (cast,) = self.pripoj(dokument_cast("C-TX-202400002", D_STAV_ODESLANY, [CHYBI_POPIS]))

        result, doc_result = self.az.check_pred_archivaci()

        self.assertEqual(result, [])
        self.assertEqual(len(doc_result), 1)
        self.assertIn("C-TX-202400002", doc_result[0])
        cast.dokument.check_pred_odeslanim.assert_not_called()


class ProjektCheckTests(CheckStavuAZTestBase):
    """Uzavření a archivace projektu přebírají úlevu z kontroly AZ před odesláním."""

    def setUp(self):
        """Připraví záchranný projekt s jedinou akcí, kterou je testovaná AZ."""
        super().setUp()
        self.projekt = Projekt(ident_cely="C-202400001")
        for attr, value in (
            ("typ_projektu", Mock(id=TYP_PROJEKTU_ZACHRANNY_ID, pk=TYP_PROJEKTU_ZACHRANNY_ID)),
            ("akce_set", Mock(all=Mock(return_value=[Mock(archeologicky_zaznam=self.az)]))),
        ):
            patcher = patch.object(Projekt, attr, new_callable=PropertyMock, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_uzavreni_s_archivovanym_neuplnym_dokumentem(self):
        """Archivovaný neúplný dokument u akce neblokuje uzavření projektu."""
        self.pripoj(dokument_cast("C-TX-202400001", D_STAV_ARCHIVOVANY, [CHYBI_POPIS]))

        self.assertEqual(self.projekt.check_pred_uzavrenim(), {})

    def test_uzavreni_s_nearchivovanym_neuplnym_dokumentem_blokuje(self):
        """Nearchivovaný neúplný dokument u akce dál blokuje uzavření projektu."""
        self.pripoj(dokument_cast("C-TX-202400002", D_STAV_ODESLANY, [CHYBI_POPIS]))

        result = self.projekt.check_pred_uzavrenim()

        self.assertEqual(len(result), 1)
        self.assertIn("C-TX-202400002", next(iter(result.values())))

    def test_archivace_s_archivovanym_neuplnym_dokumentem(self):
        """Archivovaný neúplný dokument u archivované akce neblokuje archivaci projektu."""
        self.az.stav = AZ_STAV_ARCHIVOVANY
        self.pripoj(dokument_cast("C-TX-202400001", D_STAV_ARCHIVOVANY, [CHYBI_POPIS]))

        self.assertEqual(self.projekt.check_pred_archivaci(), {})
