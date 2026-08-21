"""
Testy sdíleného řazení souborů podle názvu.

Pokrývají :func:`core.models.soubor_nazev_razeni_klic` a
:func:`core.models.prvni_soubor_dle_nazvu`, které jednotně určují pořadí souborů
a výběr náhledového souboru napříč dokumenty, 3D modely i samostatnými nálezy.
"""

from core.models import prvni_soubor_dle_nazvu, soubor_nazev_razeni_klic
from django.test import SimpleTestCase


class _SouborStub:
    """Odlehčená náhrada za :class:`core.models.Soubor` nesoucí pouze název."""

    def __init__(self, nazev):
        """
        Inicializuje stub souboru.

        :param nazev: Název souboru použitý pro řazení.
        """
        self.nazev = nazev

    def __repr__(self):
        """
        Vrátí čitelnou reprezentaci pro výstup testů.

        :return: Reprezentace obsahující název souboru.
        """
        return f"_SouborStub({self.nazev!r})"


class SouborNazevRazeniKlicTest(SimpleTestCase):
    """Testuje řadicí klíč :func:`soubor_nazev_razeni_klic`."""

    def test_klic_nahrazuje_tecku_nulou(self):
        """Ověří, že klíč porovnává tečku jako znak ``0`` a zachová původní název."""
        self.assertEqual(soubor_nazev_razeni_klic(_SouborStub("foto.jpg")), ("foto0jpg", "foto.jpg"))

    def test_zaklad_pred_ciselnym_suffixem_bez_pomlcky(self):
        """``foto.jpg`` se řadí před ``foto2.jpg`` (tečka jako ``0`` je menší než ``2``)."""
        soubory = [_SouborStub("foto2.jpg"), _SouborStub("foto.jpg")]
        self.assertEqual([s.nazev for s in sorted(soubory, key=soubor_nazev_razeni_klic)], ["foto.jpg", "foto2.jpg"])

    def test_pomlckovy_suffix_pred_zakladem(self):
        """``foto-2.jpg`` se řadí před ``foto.jpg`` (pomlčka je menší než ``0``)."""
        soubory = [_SouborStub("foto.jpg"), _SouborStub("foto-2.jpg")]
        self.assertEqual([s.nazev for s in sorted(soubory, key=soubor_nazev_razeni_klic)], ["foto-2.jpg", "foto.jpg"])


class PrvniSouborDleNazvuTest(SimpleTestCase):
    """Testuje výběr náhledového souboru :func:`prvni_soubor_dle_nazvu`."""

    def test_prazdny_vstup_vraci_none(self):
        """Prázdná kolekce vrátí ``None``."""
        self.assertIsNone(prvni_soubor_dle_nazvu([]))

    def test_vybere_prvni_dle_klice(self):
        """Vybere soubor s nejnižším řadicím klíčem názvu bez ohledu na vstupní pořadí."""
        soubory = [_SouborStub("C-3D-x.jpg"), _SouborStub("C-3D-x-b.jpg"), _SouborStub("C-3D-x-a.jpg")]
        self.assertEqual(prvni_soubor_dle_nazvu(soubory).nazev, "C-3D-x-a.jpg")

    def test_vyber_odpovida_serazeni(self):
        """Vybraný soubor je totožný s prvním prvkem ``sorted`` podle stejného klíče."""
        soubory = [_SouborStub("b.jpg"), _SouborStub("a-1.jpg"), _SouborStub("a.jpg")]
        serazene = sorted(soubory, key=soubor_nazev_razeni_klic)
        self.assertIs(prvni_soubor_dle_nazvu(soubory), serazene[0])

    def test_prijima_generator(self):
        """Funkce zvládne i neopakovatelný iterátor (generátor)."""
        soubory = (_SouborStub(n) for n in ["z.jpg", "a.jpg", "m.jpg"])
        self.assertEqual(prvni_soubor_dle_nazvu(soubory).nazev, "a.jpg")


class RealneNazvySouboruTest(SimpleTestCase):
    """Testuje řazení na reálných názvech souborů používaných v aplikaci."""

    def test_dokument_foto_serie_F(self):
        """Fotografie dokumentu ``...F01``–``...F03`` se řadí vzestupně a náhled je ``F01``."""
        soubory = [
            _SouborStub("C201911202N00047F03.jpg"),
            _SouborStub("C201911202N00047F01.jpg"),
            _SouborStub("C201911202N00047F02.jpg"),
        ]
        self.assertEqual(
            [s.nazev for s in sorted(soubory, key=soubor_nazev_razeni_klic)],
            [
                "C201911202N00047F01.jpg",
                "C201911202N00047F02.jpg",
                "C201911202N00047F03.jpg",
            ],
        )
        self.assertEqual(prvni_soubor_dle_nazvu(soubory).nazev, "C201911202N00047F01.jpg")

    def test_foto_serie_zachova_poradi_pri_dvouciferne_nule(self):
        """Nula doplněné pořadí (``F01``–``F10``) se řadí správně i pro dvojciferný index."""
        soubory = [
            _SouborStub("C201911202N00047F10.jpg"),
            _SouborStub("C201911202N00047F02.jpg"),
            _SouborStub("C201911202N00047F01.jpg"),
        ]
        self.assertEqual(prvni_soubor_dle_nazvu(soubory).nazev, "C201911202N00047F01.jpg")

    def test_dokument_pdf_pismenny_suffix(self):
        """PDF s písmenným suffixem ``A``–``C`` se řadí abecedně a náhled je ``A``."""
        soubory = [
            _SouborStub("XCDD000000009B.pdf"),
            _SouborStub("XCDD000000009A.pdf"),
            _SouborStub("XCDD000000009C.pdf"),
        ]
        self.assertEqual(
            [s.nazev for s in sorted(soubory, key=soubor_nazev_razeni_klic)],
            [
                "XCDD000000009A.pdf",
                "XCDD000000009B.pdf",
                "XCDD000000009C.pdf",
            ],
        )
        self.assertEqual(prvni_soubor_dle_nazvu(soubory).nazev, "XCDD000000009A.pdf")

    def test_ruzne_zaklady_nazvu(self):
        """Soubory s odlišným základem názvu se řadí podle celého názvu."""
        soubory = [
            _SouborStub("XCDD000000009A.pdf"),
            _SouborStub("C201911202N00047F03.jpg"),
        ]
        self.assertEqual(prvni_soubor_dle_nazvu(soubory).nazev, "C201911202N00047F03.jpg")
