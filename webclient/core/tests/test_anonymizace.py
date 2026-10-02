"""
Testy příkazu ``anonymizace_dat`` (issue #4264).

Většina testů běží bez databáze (``SimpleTestCase``) nad čistými funkcemi
modulů ``core.management.commands.utils.anonymizace`` a
``...utils.anonymizace_geometrie``. Třídy ``TestSekceNadDatabazi``
a ``TestNahodneKatastry`` spouštějí sekce příkazu nad testovací databází:
minimální data si založí samy a sekce omezí jen na ně, takže test funguje nad
prázdnou databází i nad kopií produkčních dat. Očekávané hodnoty se berou
z čistých funkcí, takže testy hlídají i shodu SQL výrazů příkazu s těmito
funkcemi.

Nejdůležitější je ``TestXsdParitaChranenychUdaju``: porovnává tabulku
chráněných polí přímo proti ``amcr.xsd``, takže povýšení schématu rozbije test
dřív, než anonymizace tiše přestane některé pole zakrývat.
"""

import io
import logging
import os
import random
import xml.etree.ElementTree as ET

from core.management.commands.utils import anonymizace
from core.management.commands.utils.anonymizace_geometrie import (
    charakteristicky_rozmer,
    deformuj_geometrii,
    posun_bodu_3d,
    posun_geometrii,
    reprezentativni_bod,
    splnuje_minimalni_posun,
    spocitej_posun,
    tise_geos,
    velikost_deformace,
    vzdalenost,
)
from django.contrib.gis.geos import GEOSGeometry, Point
from django.test import SimpleTestCase, TestCase

XSD_NAMESPACE = "http://www.w3.org/2001/XMLSchema"

#: Geometrie v EPSG:5514 používané napříč testy. Souřadnice jsou záporné,
#: protože projekt drží S-JTSK v konvenci ``[-Y, -X]``.
BOD = "SRID=5514;POINT(-700000 -1000000)"
LINIE = "SRID=5514;LINESTRING(-700000 -1000000, -700100 -1000100, -700200 -1000050)"
PLOCHA = (
    "SRID=5514;POLYGON((-700000 -1000000, -700100 -1000000, " "-700100 -1000100, -700000 -1000100, -700000 -1000000))"
)
MALA_PLOCHA = (
    "SRID=5514;POLYGON((-700000 -1000000, -700005 -1000000, " "-700005 -1000005, -700000 -1000005, -700000 -1000000))"
)
KLIKATA_PLOCHA = (
    "SRID=5514;POLYGON((-700000 -1000000, -700040 -1000002, -700080 -1000000, "
    "-700080 -1000004, -700040 -1000006, -700000 -1000004, -700000 -1000000))"
)
MULTIPLOCHA = (
    "SRID=5514;MULTIPOLYGON(((-700000 -1000000, -700100 -1000000, "
    "-700100 -1000100, -700000 -1000100, -700000 -1000000)))"
)


class TestZastupneHodnoty(SimpleTestCase):
    """Zástupné hodnoty musí být deterministické a vejít se do sloupců."""

    def test_hodnoty_jsou_deterministicke(self):
        """Dvojí zavolání nad týmž klíčem vrátí totéž, což dává idempotenci."""
        self.assertEqual(anonymizace.zastupne_jmeno(7), anonymizace.zastupne_jmeno(7))
        self.assertEqual(anonymizace.zastupny_text("popis", 7), anonymizace.zastupny_text("popis", 7))
        self.assertEqual(anonymizace.zastupny_email_uzivatele(7), anonymizace.zastupny_email_uzivatele(7))

    def test_konvence_prevzata_z_drivejsi_anonymizace(self):
        """Tvary hodnot odpovídají tomu, co na testovacím serveru už je."""
        self.assertEqual(anonymizace.zastupne_jmeno(1), "Jméno_1")
        self.assertEqual(anonymizace.zastupne_prijmeni(1), "Příjmení_1")
        self.assertEqual(anonymizace.zastupny_email_oznamovatele(1093528), "1093528@example.cz")
        self.assertEqual(anonymizace.zastupny_text("oznamovatel", 1093528), "oznamovatel_1093528")

    def test_emaily_jsou_unikatni_pro_ruzne_klice(self):
        """``User.email`` má ``unique=True``, odvození z pk to musí zaručit."""
        adresy = {anonymizace.zastupny_email_uzivatele(pk) for pk in range(1, 500)}
        self.assertEqual(len(adresy), 499)

    def test_hodnoty_se_vejdou_do_sloupcu(self):
        """Nejdelší reálné pk nesmí přetéct délku sloupce."""
        velke_pk = 9_999_999_999
        self.assertLessEqual(len(anonymizace.zastupny_email_uzivatele(velke_pk)), 254)
        self.assertLessEqual(len(anonymizace.zastupny_email_notifikace(velke_pk)), 254)
        self.assertLessEqual(len(anonymizace.zastupny_text("nazev", velke_pk)), 500)
        self.assertLessEqual(len(anonymizace.zastupny_text("poznamka", velke_pk)), 1000)

    def test_nepouzitelne_heslo_je_stabilni_a_neprihlasitelne(self):
        """
        Heslo musí být nepoužitelné a pro všechny běhy stejné.

        ``make_password(None)`` by generoval pokaždé jiný náhodný přívěsek
        a druhý běh příkazu by tím přepsal všechny účty znovu.
        """
        from django.contrib.auth.hashers import is_password_usable

        self.assertFalse(is_password_usable(anonymizace.NEPOUZITELNE_HESLO))
        self.assertEqual(anonymizace.NEPOUZITELNE_HESLO, "!")

    def test_telefon_uzivatele_projde_validatorem(self):
        """
        ``User.telefon`` má validátor, takže vzor ``telefon_{pk}`` by neprošel.

        Kontroluje se skutečným validátorem, ne opsaným regulárem.
        """
        from core.validators import validate_phone_number

        validate_phone_number(anonymizace.ANONYM_TELEFON)


class TestPrefixPid(SimpleTestCase):
    """Přepis DOI a IGSN na prefix cílové instance."""

    def test_hodnota_nese_prefix_instance(self):
        """Formát odpovídá setterům ``set_doi`` a ``set_igsn``."""
        self.assertEqual(anonymizace.zastupny_pid("10.82734", "C-TX-202500005"), "10.82734/C-TX-202500005")

    def test_prazdny_prefix_vede_na_none(self):
        """
        Bez prefixu se hodnota vynuluje, aby v DB nezůstal produkční identifikátor.

        Setter by jinak uložil nesmyslné ``/C-TX-…``, které by se PID vrstva
        mohla pokusit zaregistrovat.
        """
        self.assertIsNone(anonymizace.zastupny_pid("", "C-TX-202500005"))
        self.assertIsNone(anonymizace.zastupny_pid(None, "C-TX-202500005"))

    def test_opakovane_pouziti_da_totez(self):
        """Hodnota je funkcí prefixu a identifikátoru, tedy idempotentní."""
        prvni = anonymizace.zastupny_pid("10.82734", "C-TX-202500005")
        druhy = anonymizace.zastupny_pid("10.82734", "C-TX-202500005")
        self.assertEqual(prvni, druhy)


class TestXsdParitaChranenychUdaju(SimpleTestCase):
    """Tabulka chráněných polí musí odpovídat schématu ``amcr.xsd``."""

    @classmethod
    def setUpClass(cls):
        """
        Načte schéma ``amcr.xsd`` ze zdrojů generátoru XML.

        :return: Nevrací hodnotu.
        """
        super().setUpClass()
        cesta = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "xml_generator",
            "definitions",
            "amcr.xsd",
        )
        cls.strom = ET.parse(cesta)

    def _textova_pole_typu(self, nazev_typu):
        """
        Vrátí názvy elementů typu ``xs:string`` v zadaném complexType.

        :param nazev_typu: Název typu v ``amcr.xsd``.
        :return: Množina názvů elementů.
        """
        for complex_type in self.strom.iter(f"{{{XSD_NAMESPACE}}}complexType"):
            if complex_type.get("name") != nazev_typu:
                continue
            return {
                element.get("name")
                for element in complex_type.iter(f"{{{XSD_NAMESPACE}}}element")
                if element.get("type") == "xs:string"
            }
        self.fail(f"Typ {nazev_typu} v amcr.xsd neexistuje.")

    def test_vsechny_typy_schematu_jsou_pokryte(self):
        """
        Každý ``*-chranene_udajeType`` musí být v mapování, i kdyby byl prázdný.

        Nový typ ve schématu tak nemůže projít bez povšimnutí.
        """
        ve_schematu = {
            complex_type.get("name")
            for complex_type in self.strom.iter(f"{{{XSD_NAMESPACE}}}complexType")
            if (complex_type.get("name") or "").endswith("-chranene_udajeType")
        }
        self.assertEqual(ve_schematu, set(anonymizace.XSD_TYP_MODELU))

    def test_textova_pole_odpovidaji_schematu(self):
        """
        Pro každý typ sedí seznam polí v kódu s elementy ``xs:string``.

        Elementy uvedené v ``POLE_RESENA_GEOMETRII`` se odečítají, protože je
        nastavuje sekce ``geometrie`` – dnes jde o ``zm10``, které je sice
        ``xs:string``, ale v databázi je to cizí klíč do kladu mapových listů.
        """
        for nazev_typu, klic_modelu in anonymizace.XSD_TYP_MODELU.items():
            with self.subTest(typ=nazev_typu):
                resena_geometrii = anonymizace.POLE_RESENA_GEOMETRII.get(nazev_typu, frozenset())
                ve_schematu = self._textova_pole_typu(nazev_typu) - resena_geometrii
                if klic_modelu is None:
                    self.assertEqual(
                        ve_schematu,
                        set(),
                        f"Typ {nazev_typu} nove obsahuje textova pole, doplnit do CHRANENA_TEXTOVA_POLE.",
                    )
                    continue
                v_kodu = {element for element, _pole in anonymizace.CHRANENA_TEXTOVA_POLE[klic_modelu]}
                self.assertEqual(ve_schematu, v_kodu)

    def test_vyjimky_resene_geometrii_ve_schematu_existuji(self):
        """
        Výjimka nesmí přežít odstranění elementu ze schématu.

        Kdyby ``zm10`` z ``amcr.xsd`` zmizelo, zůstala by v kódu mrtvá výjimka,
        která by později zakryla nově přidané pole téhož jména.
        """
        for nazev_typu, elementy in anonymizace.POLE_RESENA_GEOMETRII.items():
            with self.subTest(typ=nazev_typu):
                self.assertTrue(elementy <= self._textova_pole_typu(nazev_typu))

    def test_pole_oznamovatele_odpovidaji_schematu(self):
        """Osobní údaje oznamovatele se také berou ze schématu."""
        ve_schematu = self._textova_pole_typu("oznamovatelType")
        v_kodu = {element for element, _pole in anonymizace.OZNAMOVATEL_POLE}
        self.assertEqual(ve_schematu, v_kodu)


class TestInvalidaceCache(SimpleTestCase):
    """Po dávkovém zápisu musí příkaz sám zneplatnit cacheops cache."""

    @staticmethod
    def _volby(**zmeny):
        """
        Sestaví slovník voleb příkazu s výchozími hodnotami.

        :param zmeny: Volby, které se mají oproti výchozím přepsat.
        :return: Slovník voleb pro ``handle``.
        """
        from core.management.commands.anonymizace_dat import Command

        parser = Command().create_parser("manage.py", "anonymizace_dat")
        volby = vars(parser.parse_args(["--potvrzuji-testovaci-server"]))
        volby.update(zmeny)
        return volby

    def test_zahodi_celou_cacheops_cache(self):
        """
        Po dávkovém zápisu se zahodí celá cacheops cache.

        Anonymizace přepisuje podstatnou část databáze, takže udržovat seznam
        dotčených modelů by bylo křehčí než zahodit cache celou.
        """
        from unittest import mock

        from core.management.commands.anonymizace_dat import Command

        prikaz = Command(stdout=io.StringIO(), stderr=io.StringIO())
        with mock.patch("cacheops.invalidate_all") as zneplatni:
            prikaz._invaliduj_cache(self._volby())

        zneplatni.assert_called_once_with()

    def test_dry_run_cache_nesaha(self):
        """Dry-run nic nemění, takže není co zneplatňovat."""
        from unittest import mock

        from core.management.commands.anonymizace_dat import Command

        prikaz = Command(stdout=io.StringIO(), stderr=io.StringIO())
        with mock.patch("cacheops.invalidate_all") as zneplatni:
            prikaz._invaliduj_cache(self._volby(dry_run=True))

        zneplatni.assert_not_called()

    def test_upozorni_na_redis_snapshoty(self):
        """
        Výstup musí připomenout Redis snapshoty, které příkaz nepřegenerovává.

        Snapshoty nemají expiraci, takže bez ručního zásahu drží data z doby
        před anonymizací.
        """
        from unittest import mock

        from core.management.commands.anonymizace_dat import Command

        vystup = io.StringIO()
        prikaz = Command(stdout=vystup, stderr=io.StringIO())
        with mock.patch("cacheops.invalidate_all"):
            prikaz._invaliduj_cache(self._volby())

        self.assertIn("update_all_redis_snapshots", vystup.getvalue())


class TestTichyVystup(SimpleTestCase):
    """Úspěšný běh nesmí zahltit výstup hláškami o zahozených kandidátech."""

    def test_geos_hlasky_se_pri_zkouseni_ztlumi(self):
        """
        Deformace zkouší kandidáty, GEOS na každý neplatný hlásí self-intersection.

        Bez ztlumení vypíše úspěšný běh stovky varování o tvarech, které jsme
        právě zahodili, a skutečné varování v nich zanikne.
        """
        zachycene = []

        class Zachytavac(logging.Handler):
            """Sbírá záznamy loggeru pro kontrolu v testu."""

            def emit(self, record):
                """
                Uloží záznam loggeru.

                :param record: Záznam loggeru.
                """
                zachycene.append(record)

        gis_logger = logging.getLogger("django.contrib.gis")
        zachytavac = Zachytavac()
        gis_logger.addHandler(zachytavac)
        try:
            generator = random.Random(1)
            for _pokus in range(50):
                deformuj_geometrii(GEOSGeometry(KLIKATA_PLOCHA), 10.0, generator)
        finally:
            gis_logger.removeHandler(zachytavac)

        self.assertEqual(zachycene, [])

    def test_uroven_loggeru_se_vrati(self):
        """Ztlumení je dočasné, po bloku musí logger fungovat jako dřív."""
        gis_logger = logging.getLogger("django.contrib.gis")
        puvodni = gis_logger.level
        with tise_geos():
            self.assertEqual(gis_logger.level, logging.ERROR)
        self.assertEqual(gis_logger.level, puvodni)

    def test_duvody_se_scitaji_a_vypisuji_souhrnne(self):
        """Místo řádku na každý záznam se vypíše jeden řádek na důvod."""
        from core.management.commands.anonymizace_dat import Command

        vystup = io.StringIO()
        prikaz = Command(stdout=vystup, stderr=io.StringIO())
        for _pokus in range(3):
            prikaz._zapocti_duvod("neplatna_geometrie")
        prikaz._zapocti_duvod("bez_nove_polohy")
        prikaz._vypis_duvody()

        text = vystup.getvalue()
        self.assertIn("3×", text)
        self.assertIn("1×", text)
        self.assertEqual(text.count("×"), 2)

    def test_vypise_identy_preskocenych_pianu(self):
        """
        U každého důvodu se vypíšou identifikátory dotčených PIANů.

        Bez nich by se nedalo dohledat, které záznamy zůstaly beze změny,
        a tedy na skutečné poloze.
        """
        from core.management.commands.anonymizace_dat import Command

        vystup = io.StringIO()
        prikaz = Command(stdout=vystup, stderr=io.StringIO())
        prikaz._zapocti_duvod("neplatna_geometrie", "P-1234-000001")
        prikaz._zapocti_duvod("neplatna_geometrie", "P-1234-000002")
        prikaz._vypis_duvody()

        text = vystup.getvalue()
        self.assertIn("P-1234-000001", text)
        self.assertIn("P-1234-000002", text)

    def test_dlouhy_seznam_identu_se_zkrati(self):
        """
        Výpis na konzoli se zkrátí, aby u tisíců záznamů nepřerostl vše ostatní.

        Úplný seznam zůstává v logu.
        """
        from core.management.commands.anonymizace_dat import MAX_VYPSANYCH_IDENTU, Command

        vystup = io.StringIO()
        prikaz = Command(stdout=vystup, stderr=io.StringIO())
        pocet = MAX_VYPSANYCH_IDENTU + 5
        for poradi in range(pocet):
            prikaz._zapocti_duvod("neplatna_geometrie", f"P-1234-{poradi:06d}")
        prikaz._vypis_duvody()

        text = vystup.getvalue()
        self.assertIn("a dalších 5", text)
        self.assertNotIn(f"P-1234-{pocet - 1:06d}", text)
        self.assertEqual(len(prikaz.identy_preskocenych["neplatna_geometrie"]), pocet)

    def test_vystup_projde_konzoli_windows(self):
        """
        Souhrn musí jít zakódovat do cp1250, jinak konzole na Windows spadne.

        Proto se ve výpisu nepoužívají znaky jako trojtečka nebo šipka.
        """
        from core.management.commands.anonymizace_dat import Command

        vystup = io.StringIO()
        prikaz = Command(stdout=vystup, stderr=io.StringIO())
        for duvod in ("neplatna_geometrie", "bez_nove_polohy", "bez_nahradniho_katastru", "bez_deformace"):
            for poradi in range(60):
                prikaz._zapocti_duvod(duvod, f"P-1234-{poradi:06d}")
        prikaz._vypis_duvody()

        vystup.getvalue().encode("cp1250")

    def test_bez_duvodu_se_nic_nevypisuje(self):
        """Když se nic nepřeskočilo, nemá se objevit prázdná sekce."""
        from core.management.commands.anonymizace_dat import Command

        vystup = io.StringIO()
        prikaz = Command(stdout=vystup, stderr=io.StringIO())
        prikaz._vypis_duvody()

        self.assertEqual(vystup.getvalue(), "")


class TestPravidlaDatabaze(SimpleTestCase):
    """Replika pravidel triggeru musí dávat tentýž verdikt jako databáze."""

    #: Polygon se segmentem 5 cm, tedy pod databázovou mezí 0,11 m.
    KRATKY_SEGMENT = (
        "-700000 -1000000, -700000.05 -1000000, -700100 -1000000, "
        "-700100 -1000100, -700000 -1000100, -700000 -1000000"
    )

    def test_polygon_s_kratkym_segmentem_neprojde(self):
        """U polygonu databáze délku segmentu kontroluje."""
        from core.management.commands.utils.anonymizace_geometrie import splnuje_pravidla_databaze

        self.assertFalse(splnuje_pravidla_databaze(GEOSGeometry(f"SRID=5514;POLYGON(({self.KRATKY_SEGMENT}))")))

    def test_multipolygon_s_kratkym_segmentem_projde(self):
        """
        U multipolygonu databáze délku segmentu nekontroluje.

        ``validategeom`` volá ``validateLine`` jen pro linii a polygon. Hranice
        katastrů jsou multipolygony a běžně mají segmenty pod mezí – přísnější
        replika by je odmítala, přestože je databáze přijme.
        """
        from core.management.commands.utils.anonymizace_geometrie import splnuje_pravidla_databaze

        self.assertTrue(splnuje_pravidla_databaze(GEOSGeometry(f"SRID=5514;MULTIPOLYGON((({self.KRATKY_SEGMENT})))")))


class TestZapisSVypnutymTriggerem(SimpleTestCase):
    """Vadu zdroje zapsat smíme, novou vadu vyrobenou anonymizací nikdy."""

    #: Polygon se segmentem 5 cm – trigger ho odmítne už v produkčních datech.
    VADNY = (
        "SRID=5514;POLYGON((-700000 -1000000, -700000.05 -1000000, -700100 -1000000, "
        "-700100 -1000100, -700000 -1000100, -700000 -1000000))"
    )

    def _prikaz(self, lze_vypnout):
        """
        Připraví příkaz bez databáze se zadanou možností vypnout trigger.

        :param lze_vypnout: Zda má příkaz oprávnění trigger vypnout.
        :return: Instance příkazu.
        """
        from core.management.commands.anonymizace_dat import Command

        prikaz = Command(stdout=io.StringIO(), stderr=io.StringIO())
        prikaz.statistika["geometrie"] = {"zpracovano": 0, "zmeneno": 0, "preskoceno": 0, "chyb": 0}
        prikaz.lze_vypnout_trigger = lze_vypnout
        return prikaz

    @staticmethod
    def _pian(wkt):
        """
        Vytvoří náhražku PIANu s danou zdrojovou geometrií.

        Kopie ve WGS-84 se dopočítá stejnou transformací jako v aplikaci, aby
        nesla tutéž vadu jako skutečný PIAN – vada zdroje se posuzuje zvlášť
        v každém souřadnicovém systému.

        :param wkt: Geometrie ve tvaru EWKT v EPSG:5514.
        :return: Objekt s atributy, které čte ``_uloz_geometrii_pianu``.
        """
        from types import SimpleNamespace

        from core.coordTransform import transform_geom_to_wgs84

        geom_sjtsk = GEOSGeometry(wkt)
        wgs_wkt, _vysledek = transform_geom_to_wgs84(geom_sjtsk.wkt)
        return SimpleNamespace(
            pk=1, ident_cely="P-0000-000001", geom_sjtsk=geom_sjtsk, geom=GEOSGeometry(wgs_wkt, srid=4326)
        )

    def test_vada_zdroje_se_zapise_s_vypnutym_triggerem(self):
        """Posunutou geometrii s vadou z produkce smíme zapsat a PIAN si poznamenáme."""
        prikaz = self._prikaz(lze_vypnout=True)
        pian = self._pian(self.VADNY)
        posunuta = posun_geometrii(pian.geom_sjtsk, 500.0, 500.0)

        self.assertTrue(prikaz._uloz_geometrii_pianu(pian, posunuta, zm10=None))
        self.assertIn(pian.pk, prikaz.piany_s_vadou_zdroje)
        self.assertEqual(prikaz.duvody_preskoceni.get("zapsano_s_vadou_zdroje"), 1)

    def test_bez_opravneni_se_vada_zdroje_nezapise(self):
        """Když trigger vypnout nejde, PIAN zůstane jako dřív beze změny."""
        prikaz = self._prikaz(lze_vypnout=False)
        pian = self._pian(self.VADNY)
        posunuta = posun_geometrii(pian.geom_sjtsk, 500.0, 500.0)

        self.assertFalse(prikaz._uloz_geometrii_pianu(pian, posunuta, zm10=None))
        self.assertEqual(prikaz.piany_s_vadou_zdroje, set())

    def test_vada_vyrobena_anonymizaci_se_nezapise(self):
        """Platný zdroj s vadným výsledkem se nezapíše, i kdyby trigger vypnout šlo."""
        prikaz = self._prikaz(lze_vypnout=True)
        pian = self._pian(PLOCHA)

        self.assertFalse(prikaz._uloz_geometrii_pianu(pian, GEOSGeometry(self.VADNY), zm10=None))
        self.assertEqual(prikaz.piany_s_vadou_zdroje, set())

    def test_vada_zdroje_jen_ve_wgs_se_rozpozna(self):
        """
        Zdroj s vadou jen v kopii WGS-84 se hlásí jako vada zdroje.

        Mez segmentu ve stupních umí porušit i tvar, který v S-JTSK projde;
        dřív se takový PIAN chybně hlásil jako vada vyrobená anonymizací.
        """
        from types import SimpleNamespace

        from core.management.commands.anonymizace_dat import Command

        pian = SimpleNamespace(
            geom_sjtsk=GEOSGeometry(PLOCHA),
            geom=GEOSGeometry("SRID=4326;LINESTRING(15 50, 15.0000001 50, 15.001 50.001)"),
        )
        self.assertTrue(Command._zdroj_wgs_je_vadny(pian))
        self.assertEqual(self._prikaz(lze_vypnout=True)._duvod_neplatne_geometrie(pian), "zdrojova_geometrie_neplatna")

    def test_chybejici_wgs_neni_vada_zdroje(self):
        """Bez kopie ve WGS-84 není co převzít, takže to není vada zdroje."""
        from types import SimpleNamespace

        from core.management.commands.anonymizace_dat import Command

        self.assertFalse(Command._zdroj_wgs_je_vadny(SimpleNamespace(geom=None)))


class TestTrojrozmernaGeometrie(SimpleTestCase):
    """Linie a plocha se souřadnicí ``z`` nesmí shodit posun ani deformaci."""

    LINIE_3D = "SRID=5514;LINESTRING Z(-700000 -1000000 10, -700100 -1000100 11, -700200 -1000050 12)"
    PLOCHA_3D = (
        "SRID=5514;POLYGON Z((-700000 -1000000 5, -700100 -1000000 6, "
        "-700100 -1000100 7, -700000 -1000100 8, -700000 -1000000 5))"
    )

    @staticmethod
    def _vysky(geom):
        """
        Vrátí souřadnice ``z`` vrcholů linie nebo vnějšího prstence.

        :param geom: Geometrie se souřadnicí ``z``.
        :return: Seznam výšek.
        """
        souradnice = geom.coords if geom.geom_type == "LineString" else geom.coords[0]
        return [vrchol[2] for vrchol in souradnice]

    def test_posun_zachova_vysky(self):
        """Posun mění jen polohu, výšky vrcholů zůstanou."""
        for wkt in (self.LINIE_3D, self.PLOCHA_3D):
            with self.subTest(wkt=wkt[:30]):
                geom = GEOSGeometry(wkt)
                posunuta = posun_geometrii(geom, 100.0, 200.0)
                self.assertTrue(posunuta.hasz)
                self.assertEqual(self._vysky(posunuta), self._vysky(geom))

    def test_deformace_zachova_vysky(self):
        """Deformace posouvá vrcholy jen v rovině."""
        for wkt in (self.LINIE_3D, self.PLOCHA_3D):
            with self.subTest(wkt=wkt[:30]):
                geom = GEOSGeometry(wkt)
                deformovana, zmeneno = deformuj_geometrii(geom, 10.0, random.Random(1))
                self.assertTrue(zmeneno)
                self.assertEqual(self._vysky(deformovana), self._vysky(geom))


class TestDuvodyBodovychModelu(SimpleTestCase):
    """Přeskočený projekt, nález nebo dokument musí mít v souhrnu důvod i identifikátor."""

    def _prikaz(self):
        """
        Připraví příkaz bez databáze.

        :return: Instance příkazu.
        """
        from core.management.commands.anonymizace_dat import Command

        prikaz = Command(stdout=io.StringIO(), stderr=io.StringIO())
        prikaz.statistika["geometrie"] = {"zpracovano": 0, "zmeneno": 0, "preskoceno": 0, "chyb": 0}
        return prikaz

    def test_zaznam_bez_okresu_se_zapise_s_identem(self):
        """Když nejde určit okres, zapíše se důvod i ``ident_cely``."""
        from types import SimpleNamespace

        prikaz = self._prikaz()
        zaznam = SimpleNamespace(pk=7, ident_cely="C-202699007", geom_sjtsk=GEOSGeometry(BOD))

        self.assertIsNone(prikaz._nova_poloha_zaznamu(zaznam, None, {"min_posun_m": 100.0}))
        self.assertEqual(prikaz.identy_preskocenych["bod_bez_okresu"], ["C-202699007"])

    def test_dokument_bez_vlastniho_identu_bere_ident_dokumentu(self):
        """``DokumentExtraData`` nemá ``ident_cely``, použije se identifikátor dokumentu."""
        from types import SimpleNamespace

        from core.management.commands.anonymizace_dat import Command

        extra = SimpleNamespace(pk=3, dokument=SimpleNamespace(ident_cely="C-TX-202699001"))
        self.assertEqual(Command._ident_zaznamu(extra), "C-TX-202699001")


class TestMinimalniPosun(SimpleTestCase):
    """Nová poloha nesmí padnout těsně vedle té původní."""

    def test_hranicni_vzdalenost_projde(self):
        """Bod přesně na mezi se bere jako vyhovující."""
        stary = Point(-700000, -1000000, srid=5514)
        novy = Point(-700100, -1000000, srid=5514)
        self.assertEqual(vzdalenost(stary, novy), 100)
        self.assertTrue(splnuje_minimalni_posun(stary, novy, 100))

    def test_blizsi_bod_neprojde(self):
        """O metr blíž už podmínku nesplňuje."""
        stary = Point(-700000, -1000000, srid=5514)
        novy = Point(-700099, -1000000, srid=5514)
        self.assertFalse(splnuje_minimalni_posun(stary, novy, 100))

    def test_nulova_vzdalenost_neprojde(self):
        """Nezměněná poloha není anonymizace."""
        stary = Point(-700000, -1000000, srid=5514)
        self.assertFalse(splnuje_minimalni_posun(stary, stary, 100))

    def test_nulova_mez_kontrolu_vypne(self):
        """Volba ``--min-posun-m 0`` propustí i nulový posun."""
        stary = Point(-700000, -1000000, srid=5514)
        self.assertTrue(splnuje_minimalni_posun(stary, stary, 0))


class TestPosunuGeometrie(SimpleTestCase):
    """Posun geometrie a výškových bodů."""

    def test_posun_zachova_typ_i_pocet_vrcholu(self):
        """Posouvá se jen poloha, struktura geometrie zůstává."""
        for wkt in (BOD, LINIE, PLOCHA, MULTIPLOCHA):
            with self.subTest(wkt=wkt[:40]):
                geom = GEOSGeometry(wkt)
                posunuta = posun_geometrii(geom, 150.0, 200.0)
                self.assertEqual(posunuta.geom_type, geom.geom_type)
                self.assertEqual(posunuta.num_coords, geom.num_coords)
                self.assertEqual(posunuta.srid, 5514)

    def test_posun_odpovida_vektoru(self):
        """Reprezentativní bod se posune přesně o zadaný vektor."""
        geom = GEOSGeometry(PLOCHA)
        posunuta = posun_geometrii(geom, 150.0, 200.0)
        dx, dy = spocitej_posun(reprezentativni_bod(geom), reprezentativni_bod(posunuta))
        self.assertAlmostEqual(dx, 150.0, places=6)
        self.assertAlmostEqual(dy, 200.0, places=6)

    def test_vyskovy_bod_si_zachova_nivelaci(self):
        """Souřadnice ``z`` je výška, ne poloha, a posouvat se nesmí."""
        bod = GEOSGeometry("SRID=5514;POINT Z(-700000 -1000000 250.5)")
        posunuty = posun_bodu_3d(bod, 10, 20)
        self.assertEqual(posunuty.z, 250.5)
        self.assertEqual(posunuty.x, -699990)
        self.assertEqual(posunuty.y, -999980)

    def test_znamenkova_konvence_zustava(self):
        """Posun je řádově menší než souřadnice, znaménka se nepřeklopí."""
        bod = GEOSGeometry("SRID=5514;POINT Z(-700000 -1000000 250.5)")
        posunuty = posun_bodu_3d(bod, 150, -200)
        self.assertLess(posunuty.x, 0)
        self.assertLess(posunuty.y, 0)


class TestDeformaceTvaru(SimpleTestCase):
    """Deformace musí tvar změnit, ale nerozbít."""

    def setUp(self):
        """
        Připraví generátor s pevným zrnem, aby byly testy reprodukovatelné.

        :return: Nevrací hodnotu.
        """
        self.generator = random.Random(4264)

    def test_zachova_typ_pocet_vrcholu_a_platnost(self):
        """Struktura geometrie zůstává, jinak by přestal sedět ``Pian.typ``."""
        for wkt in (LINIE, PLOCHA, MULTIPLOCHA):
            with self.subTest(wkt=wkt[:40]):
                geom = GEOSGeometry(wkt)
                deformovana, zmeneno = deformuj_geometrii(geom, 10.0, self.generator)
                self.assertTrue(zmeneno)
                self.assertEqual(deformovana.geom_type, geom.geom_type)
                self.assertEqual(deformovana.num_coords, geom.num_coords)
                self.assertTrue(deformovana.valid)
                self.assertEqual(deformovana.srid, 5514)

    def test_tvar_se_opravdu_zmeni(self):
        """Bez změny tvaru by obrys dál kopíroval skutečnou stavbu."""
        geom = GEOSGeometry(PLOCHA)
        deformovana, _zmeneno = deformuj_geometrii(geom, 10.0, self.generator)
        self.assertNotEqual(deformovana.wkt, geom.wkt)

    def test_prstenec_zustane_uzavreny(self):
        """První a poslední vrchol prstence musí zůstat totožné."""
        geom = GEOSGeometry(PLOCHA)
        deformovana, _zmeneno = deformuj_geometrii(geom, 10.0, self.generator)
        prstenec = deformovana.coords[0]
        self.assertEqual(prstenec[0], prstenec[-1])

    def test_zadny_vrchol_se_neposune_nad_mez(self):
        """Posun vrcholu drží pod zadanou horní mezí."""
        geom = GEOSGeometry(PLOCHA)
        mez = 10.0
        deformovana, _zmeneno = deformuj_geometrii(geom, mez, self.generator)
        puvodni = geom.coords[0]
        nove = deformovana.coords[0]
        for (stary_x, stary_y), (novy_x, novy_y) in zip(puvodni, nove):
            self.assertLessEqual(vzdalenost(Point(stary_x, stary_y), Point(novy_x, novy_y)), mez)

    def test_mala_plocha_se_nerozpadne(self):
        """
        Relativní mez chrání drobné sondy.

        U plochy o hraně 5 m by posun vrcholu o 10 m tvar zničil, proto se
        velikost deformace odvozuje i z rozměru geometrie.
        """
        geom = GEOSGeometry(MALA_PLOCHA)
        self.assertLess(velikost_deformace(geom, 10.0), 1.0)
        deformovana, _zmeneno = deformuj_geometrii(geom, 10.0, self.generator)
        self.assertTrue(deformovana.valid)

    def test_nulova_mez_deformaci_vypne(self):
        """Volba ``--deformace-m 0`` vrátí geometrii beze změny."""
        geom = GEOSGeometry(PLOCHA)
        deformovana, zmeneno = deformuj_geometrii(geom, 0, self.generator)
        self.assertFalse(zmeneno)
        self.assertEqual(deformovana.wkt, geom.wkt)

    def test_bod_nema_co_deformovat(self):
        """Bod žádné vrcholy k rozvlnění nemá, anonymizuje ho jen posun."""
        geom = GEOSGeometry(BOD)
        self.assertEqual(charakteristicky_rozmer(geom), 0.0)
        deformovana, zmeneno = deformuj_geometrii(geom, 10.0, self.generator)
        self.assertFalse(zmeneno)
        self.assertEqual(deformovana.wkt, geom.wkt)


class _OmezenyPrikaz:
    """
    Továrna na příkaz ``anonymizace_dat`` omezený na vybrané záznamy.

    Testy běží nad kopií produkční databáze, takže bez omezení by každá sekce
    přepisovala statisíce řádků. Omezení jde přes metodu ``_zaklad``, kterou
    sekce používají jako výchozí množinu záznamů.
    """

    @staticmethod
    def vytvor(omezeni):
        """
        Vytvoří instanci příkazu, jejíž sekce vidí jen zadané záznamy.

        :param omezeni: Slovník ``{model: [pk, ...]}``; model bez položky je prázdný.
        :return: Instance příkazu s tichým výstupem.
        """
        from core.management.commands.anonymizace_dat import Command

        class Omezeny(Command):
            """Příkaz, jehož sekce pracují jen s vybranými záznamy."""

            def _zaklad(self, model):
                """
                Vrátí jen záznamy vybrané testem.

                :param model: Třída modelu.
                :return: ``QuerySet`` omezený na vybrané primární klíče.
                """
                return model.objects.filter(pk__in=omezeni.get(model, []))

        return Omezeny(stdout=io.StringIO(), stderr=io.StringIO())


def _volby_prikazu(**zmeny):
    """
    Sestaví slovník voleb příkazu ``anonymizace_dat`` s výchozími hodnotami.

    :param zmeny: Volby, které se mají oproti výchozím přepsat.
    :return: Slovník voleb pro metody sekcí.
    """
    from core.management.commands.anonymizace_dat import Command

    parser = Command().create_parser("manage.py", "anonymizace_dat")
    volby = vars(parser.parse_args(["--potvrzuji-testovaci-server"]))
    volby.update(zmeny)
    return volby


def _spust_sekci(nazev, omezeni, **zmeny):
    """
    Spustí jednu sekci příkazu nad vybranými záznamy.

    :param nazev: Název sekce, např. ``"uzivatele"``.
    :param omezeni: Slovník ``{model: [pk, ...]}`` pro :class:`_OmezenyPrikaz`.
    :param zmeny: Volby příkazu, které se mají přepsat.
    :return: Instance příkazu po doběhnutí sekce.
    """
    prikaz = _OmezenyPrikaz.vytvor(omezeni)
    prikaz.statistika[nazev] = {"zpracovano": 0, "zmeneno": 0, "preskoceno": 0, "chyb": 0}
    getattr(prikaz, f"_sekce_{nazev}")(_volby_prikazu(**zmeny))
    return prikaz


class TestPojistky(SimpleTestCase):
    """Příkaz se nesmí rozběhnout mimo testovací server ani bez potvrzení."""

    def test_bez_test_env_odmitne(self):
        """``TEST_ENV`` vypnuté znamená produkci, příkaz musí skončit chybou."""
        from django.core.management import CommandError, call_command
        from django.test import override_settings

        with override_settings(TEST_ENV=False), self.assertRaises(CommandError):
            call_command("anonymizace_dat", "--potvrzuji-testovaci-server", "--dry-run", stdout=io.StringIO())

    def test_bez_potvrzeni_odmitne(self):
        """``TEST_ENV`` má výchozí hodnotu ``True``, proto je nutné i potvrzení."""
        from django.core.management import CommandError, call_command
        from django.test import override_settings

        with override_settings(TEST_ENV=True), self.assertRaises(CommandError):
            call_command("anonymizace_dat", "--dry-run", stdout=io.StringIO())

    def test_jina_databaze_odmitne(self):
        """``--ocekavana-databaze`` chrání před během proti špatnému serveru."""
        from django.core.management import CommandError, call_command
        from django.test import override_settings

        with override_settings(TEST_ENV=True), self.assertRaises(CommandError):
            call_command(
                "anonymizace_dat",
                "--potvrzuji-testovaci-server",
                "--ocekavana-databaze=neexistujici_databaze",
                "--dry-run",
                stdout=io.StringIO(),
            )

    def test_neznama_sekce_odmitne(self):
        """Překlep v názvu sekce nesmí vést k tichému přeskočení."""
        from django.core.management import CommandError, call_command
        from django.test import override_settings

        with override_settings(TEST_ENV=True), self.assertRaises(CommandError):
            call_command(
                "anonymizace_dat", "--potvrzuji-testovaci-server", "--jen=uzivatele,neznama", stdout=io.StringIO()
            )


def _ctverec(x, y, strana, vyska=None):
    """
    Vrátí obdélníkový polygon v EPSG:5514.

    :param x: Souřadnice X levého dolního rohu.
    :param y: Souřadnice Y levého dolního rohu.
    :param strana: Šířka v metrech.
    :param vyska: Výška v metrech; bez zadání vznikne čtverec.
    :return: ``Polygon`` se SRID 5514.
    """
    from django.contrib.gis.geos import Polygon

    vyska = strana if vyska is None else vyska
    return Polygon(
        ((x, y), (x + strana, y), (x + strana, y + vyska), (x, y + vyska), (x, y)),
        srid=5514,
    )


def _vytvor_data():
    """
    Založí minimální data pro testy sekcí nad databází.

    Testovací databáze je prázdná, takže se zakládá všechno potřebné: okres
    s šesti katastry, chráněný projekt s oznamovatelem a dalšími katastry,
    chráněnou lokalitu s PIANem, uživatele a řádky logů. Záznamy se vkládají
    přes ``bulk_create``, aby se nespouštěly signály zapisující do Fedory.

    :return: ``SimpleNamespace`` s vytvořenými záznamy.
    """
    from types import SimpleNamespace

    from arch_z.models import ArcheologickyZaznam, ArcheologickyZaznamKatastr
    from core.constants import KLADYZM10, KLADYZM50, ROLE_ADMIN_ID
    from core.tests.test_mappers.fixtures import create_dokument_fixture
    from dj.models import DokumentacniJednotka
    from django.contrib.auth.models import Group
    from django.contrib.gis.geos import MultiPolygon, Point
    from heslar.hesla import HESLAR_PRISTUPNOST
    from heslar.models import Heslar, HeslarNazev, RuianKatastr, RuianKraj, RuianOkres
    from lokalita.models import Lokalita
    from oznameni.models import Oznamovatel
    from pas.models import SamostatnyNalez
    from pian.models import Kladyzm, Pian
    from projekt.models import Projekt, ProjektKatastr
    from uzivatel.models import NotificationsLog, User, UserNotificationType, UzivatelPrihlaseniLog

    d = SimpleNamespace()
    d.dokument = create_dokument_fixture()
    Dokument = type(d.dokument)
    Dokument.objects.filter(pk=d.dokument.pk).update(doi=f"10.12345/{d.dokument.ident_cely}")
    organizace = d.dokument.organizace

    hn_pristupnost = HeslarNazev.objects.get_or_create(pk=HESLAR_PRISTUPNOST, defaults={"nazev": "Přístupnost"})[0]
    hn_ostatni = HeslarNazev.objects.create(pk=990001, nazev="Test anonymizace")
    d.chranena = Heslar.objects.create(
        ident_cely="HES-PRIST-C", heslo="C", heslo_en="C", nazev_heslare=hn_pristupnost, razeni=3
    )
    ostatni = Heslar.objects.create(ident_cely="HES-ANON-001", heslo="x", heslo_en="x", nazev_heslare=hn_ostatni)

    # Okres 3 × 2 km rozdělený na šest katastrů 1 × 1 km.
    kraj = RuianKraj.objects.bulk_create([RuianKraj(nazev="Kraj", nazev_en="Region", kod=1, rada_id="C")])[0]
    d.okres = RuianOkres.objects.bulk_create(
        [
            RuianOkres(
                nazev="Okres",
                nazev_en="District",
                kraj=kraj,
                spz="XX",
                kod=1,
                # Okres pokrývají katastry beze zbytku, stejně jako ve skutečných datech.
                hranice=MultiPolygon(_ctverec(-700000, -1000000, 3000, 2000)),
            )
        ]
    )[0]
    d.katastry = RuianKatastr.objects.bulk_create(
        RuianKatastr(
            okres=d.okres,
            nazev=f"Katastr {poradi}",
            kod=poradi,
            hranice=MultiPolygon(_ctverec(-700000 + (poradi % 3) * 1000, -1000000 + (poradi // 3) * 1000, 1000)),
            definicni_bod=Point(-699500 + (poradi % 3) * 1000, -999500 + (poradi // 3) * 1000, srid=5514),
        )
        for poradi in range(6)
    )
    k0, k1, k2 = d.katastry[:3]

    d.projekt = Projekt.objects.bulk_create(
        [
            Projekt(
                typ_projektu=ostatni,
                ident_cely="C-202699001",
                hlavni_katastr=k0,
                pristupnost_snapshot=d.chranena,
                lokalizace="Za kostelem",
                parcelni_cislo="123/4",
                kulturni_pamatka_cislo=None,
            )
        ]
    )[0]
    ProjektKatastr.objects.bulk_create([ProjektKatastr(projekt=d.projekt, katastr=k) for k in (k1, k2)])
    d.oznamovatel = Oznamovatel.objects.bulk_create(
        [
            Oznamovatel(
                projekt=d.projekt,
                email="jan.novak@firma.cz",
                adresa="Hlavní 1, Praha",
                odpovedna_osoba="Jan Novák",
                oznamovatel="Firma s.r.o.",
                telefon="+420 777 111 222",
                poznamka=None,
            )
        ]
    )[0]
    d.nalez = SamostatnyNalez.objects.bulk_create(
        [
            SamostatnyNalez(
                projekt=d.projekt, pristupnost=d.chranena, stav=1, ident_cely="C-202699001-N00001", igsn="10.1/x"
            )
        ]
    )[0]

    d.zaznam = ArcheologickyZaznam.objects.bulk_create(
        [
            ArcheologickyZaznam(
                typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA,
                pristupnost=d.chranena,
                ident_cely="C-L9900001",
                stav=1,
                hlavni_katastr=k0,
            )
        ]
    )[0]
    ArcheologickyZaznamKatastr.objects.bulk_create(
        [ArcheologickyZaznamKatastr(archeologicky_zaznam=d.zaznam, katastr=k) for k in (k1, k2)]
    )
    d.lokalita = Lokalita.objects.bulk_create(
        [
            Lokalita(
                archeologicky_zaznam=d.zaznam,
                druh=ostatni,
                typ_lokality=ostatni,
                nazev="Hradiště",
                igsn="10.1/C-L9900001",
                dalsi_katastry_snapshot="skutečný",
            )
        ]
    )[0]

    zm10 = Kladyzm.objects.create(kategorie=KLADYZM10, cislo="T10", the_geom=_ctverec(-700000, -1000000, 3000))
    zm50 = Kladyzm.objects.create(kategorie=KLADYZM50, cislo="T50", the_geom=_ctverec(-700000, -1000000, 3000))
    d.pian = Pian.objects.bulk_create(
        [
            Pian(
                presnost=ostatni,
                typ=ostatni,
                geom=Point(15.0, 50.0, srid=4326),
                geom_sjtsk=Point(-698500, -999500, srid=5514),
                zm10=zm10,
                zm50=zm50,
                ident_cely="P-9999-000001",
            )
        ]
    )[0]
    DokumentacniJednotka.objects.bulk_create(
        [
            DokumentacniJednotka(
                typ=ostatni, ident_cely=f"{d.zaznam.ident_cely}-D01", archeologicky_zaznam=d.zaznam, pian=d.pian
            )
        ]
    )

    admin_skupina = Group.objects.get_or_create(pk=ROLE_ADMIN_ID, defaults={"name": "Admin anonymizace test"})[0]
    d.admin, d.umely, d.bezny, d.bez_telefonu = User.objects.bulk_create(
        User(
            ident_cely=f"U-99{poradi:04d}",
            first_name=jmeno,
            last_name=prijmeni,
            email=f"{prijmeni.lower().replace(' ', '')}@firma.cz",
            password="pbkdf2_sha256$skutecny",
            organizace=organizace,
            telefon=telefon,
            sha_1="abc",
        )
        for poradi, (jmeno, prijmeni, telefon) in enumerate(
            (
                ("Adam", "Admin", "+420 777 000 001"),
                ("Ústav", "Anonym", None),
                ("Jana", "Skutečná", "+420 777 000 002"),
                ("Petr", "Bez Telefonu", None),
            )
        )
    )
    User.groups.through.objects.create(user_id=d.admin.pk, group_id=admin_skupina.pk)

    d.prihlaseni = UzivatelPrihlaseniLog.objects.create(user=d.bezny, ip_adresa="192.0.2.10")
    typ = UserNotificationType.objects.create(ident_cely="E-ANON-TEST")
    d.notifikace = NotificationsLog.objects.create(
        notification_type=typ, user=d.bezny, receiver_address="jana@firma.cz"
    )
    return d


class TestSekceNadDatabazi(TestCase):
    """
    Sekce příkazu nad záznamy v databázi.

    Očekávané hodnoty se berou z funkcí modulu ``utils.anonymizace``, takže
    test hlídá, že SQL výrazy příkazu a tyto funkce dávají totéž.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Založí data sdílená testy třídy.

        :return: Nevrací hodnotu.
        """
        cls.d = _vytvor_data()

    def test_uzivatele_mimo_vyjimky_se_anonymizuji(self):
        """Běžní uživatelé dostanou zástupné údaje, admin a umělý účet ne."""
        from uzivatel.models import User

        d = self.d
        vsichni = [d.admin, d.umely, d.bezny, d.bez_telefonu]

        def stav(uzivatel):
            """
            Vrátí sledované údaje uživatele.

            :param uzivatel: Instance uživatele.
            :return: N-tice jména, příjmení, e-mailu, telefonu a hesla.
            """
            return (
                User.objects.filter(pk=uzivatel.pk)
                .values_list("first_name", "last_name", "email", "telefon", "password")
                .get()
            )

        admin_pred, umely_pred = stav(d.admin), stav(d.umely)
        omezeni = {User: [uzivatel.pk for uzivatel in vsichni]}
        _spust_sekci("uzivatele", omezeni)

        for uzivatel in (d.bezny, d.bez_telefonu):
            uzivatel.refresh_from_db()
            self.assertEqual(uzivatel.first_name, anonymizace.zastupne_jmeno(uzivatel.pk))
            self.assertEqual(uzivatel.last_name, anonymizace.zastupne_prijmeni(uzivatel.pk))
            self.assertEqual(uzivatel.email, anonymizace.zastupny_email_uzivatele(uzivatel.pk))
            self.assertEqual(uzivatel.password, anonymizace.NEPOUZITELNE_HESLO)
            self.assertIsNone(uzivatel.sha_1)
        self.assertEqual(d.bezny.telefon, anonymizace.ANONYM_TELEFON)
        self.assertIsNone(d.bez_telefonu.telefon)
        self.assertEqual(stav(d.admin), admin_pred)
        self.assertEqual(stav(d.umely), umely_pred)

        # Druhý běh musí dát totéž a nesmí narazit na unikátní e-mail.
        po_prvnim = [stav(uzivatel) for uzivatel in vsichni]
        _spust_sekci("uzivatele", omezeni)
        self.assertEqual([stav(uzivatel) for uzivatel in vsichni], po_prvnim)

    def test_projekt_bez_snapshotu_pristupnosti_se_bere_jako_chraneny(self):
        """
        Projekt s ``pristupnost_snapshot = NULL`` se anonymizuje jako chráněný.

        Neznámá přístupnost může znamenat chráněný projekt; nechat ho na skutečné
        poloze je horší než ho přesunout zbytečně.
        """
        from core.management.commands.anonymizace_dat import Command
        from projekt.models import Projekt

        projekt = Projekt.objects.bulk_create(
            [
                Projekt(
                    typ_projektu=self.d.projekt.typ_projektu,
                    ident_cely="C-202699003",
                    hlavni_katastr=self.d.projekt.hlavni_katastr,
                    pristupnost_snapshot=None,
                )
            ]
        )[0]
        self.assertTrue(Projekt.objects.filter(Command._chraneny_projekt(), pk=projekt.pk).exists())

    def test_ucet_s_anonymizovanym_jmenem_se_dokonci(self):
        """
        Účet, který má zástupné jméno, ale skutečný e-mail, se anonymizuje celý.

        To je stav testovacího serveru po dřívější ruční anonymizaci. Zástupné
        příjmení ``Příjmení_{pk}`` proto nesmí spadnout do výjimky pro umělé
        účty (filtr ``last_name__icontains``), jinak by e-mail zůstal skutečný.
        """
        from uzivatel.models import User

        bezny = self.d.bezny
        User.objects.filter(pk=bezny.pk).update(
            first_name=anonymizace.zastupne_jmeno(bezny.pk), last_name=anonymizace.zastupne_prijmeni(bezny.pk)
        )
        _spust_sekci("uzivatele", {User: [bezny.pk]})
        bezny.refresh_from_db()
        self.assertEqual(bezny.email, anonymizace.zastupny_email_uzivatele(bezny.pk))

    def test_neprazdna_poznamka_oznamovatele_se_nahradi(self):
        """
        Neprázdná poznámka dostane zástupnou hodnotu podle sdílené předpony.

        Větev s prázdnou poznámkou pokrývá :meth:`test_oznamovatele_se_anonymizuji`;
        tady se hlídá, že SQL výraz příkazu a funkce ``zastupny_udaj_oznamovatele``
        dávají totéž.
        """
        from oznameni.models import Oznamovatel
        from projekt.models import Projekt

        projekt = Projekt.objects.bulk_create(
            [
                Projekt(
                    typ_projektu=self.d.projekt.typ_projektu,
                    ident_cely="C-202699002",
                    hlavni_katastr=self.d.projekt.hlavni_katastr,
                    pristupnost_snapshot=self.d.chranena,
                )
            ]
        )[0]
        ozn = Oznamovatel.objects.bulk_create(
            [
                Oznamovatel(
                    projekt=projekt,
                    email="petr@firma.cz",
                    adresa="Vedlejší 2",
                    odpovedna_osoba="Petr Svoboda",
                    oznamovatel="Stavby a.s.",
                    telefon="+420 777 333 444",
                    poznamka="Volat po 16. hodině",
                )
            ]
        )[0]
        _spust_sekci("oznamovatele", {Oznamovatel: [ozn.pk]})
        ozn.refresh_from_db()
        self.assertEqual(ozn.poznamka, anonymizace.zastupny_udaj_oznamovatele("poznamka", ozn.pk))

    def test_oznamovatele_se_anonymizuji(self):
        """Kontaktní údaje oznamovatele se nahradí, telefon projde validátorem."""
        from core.validators import validate_phone_number
        from oznameni.models import Oznamovatel

        ozn = self.d.oznamovatel
        _spust_sekci("oznamovatele", {Oznamovatel: [ozn.pk]})

        ozn.refresh_from_db()
        self.assertEqual(ozn.oznamovatel, anonymizace.zastupny_udaj_oznamovatele("oznamovatel", ozn.pk))
        # ``osoba_`` místo ``odpovedna_osoba_`` je převzato z dřívější ruční anonymizace.
        self.assertEqual(ozn.odpovedna_osoba, f"osoba_{ozn.pk}")
        self.assertEqual(ozn.odpovedna_osoba, anonymizace.zastupny_udaj_oznamovatele("odpovedna_osoba", ozn.pk))
        self.assertEqual(ozn.adresa, anonymizace.zastupny_udaj_oznamovatele("adresa", ozn.pk))
        self.assertEqual(ozn.email, anonymizace.zastupny_email_oznamovatele(ozn.pk))
        self.assertEqual(ozn.telefon, anonymizace.ANONYM_TELEFON)
        validate_phone_number(ozn.telefon)
        self.assertIsNone(ozn.poznamka)

    def test_logy_se_anonymizuji(self):
        """IP adresy přihlášení i adresy příjemců notifikací dostanou zástupné hodnoty."""
        from uzivatel.models import NotificationsLog, UzivatelPrihlaseniLog

        d = self.d
        _spust_sekci("logy", {UzivatelPrihlaseniLog: [d.prihlaseni.pk], NotificationsLog: [d.notifikace.pk]})

        d.prihlaseni.refresh_from_db()
        d.notifikace.refresh_from_db()
        self.assertEqual(d.prihlaseni.ip_adresa, anonymizace.ANONYM_IP)
        self.assertEqual(d.notifikace.receiver_address, anonymizace.zastupny_email_notifikace(d.notifikace.pk))

    def test_chranene_texty_se_zakryji(self):
        """Neprázdná chráněná pole dostanou zástupný text, prázdná zůstanou."""
        from lokalita.models import Lokalita
        from projekt.models import Projekt

        d = self.d
        omezeni = {Projekt: [d.projekt.pk], Lokalita: [d.lokalita.pk]}
        _spust_sekci("texty", omezeni)

        d.projekt.refresh_from_db()
        d.lokalita.refresh_from_db()
        self.assertEqual(d.projekt.lokalizace, anonymizace.zastupny_text("lokalizace", d.projekt.pk))
        self.assertEqual(d.projekt.parcelni_cislo, anonymizace.zastupny_text("parcelni_cislo", d.projekt.pk))
        self.assertIsNone(d.projekt.kulturni_pamatka_cislo)
        self.assertEqual(d.lokalita.nazev, anonymizace.zastupny_text("nazev", d.lokalita.pk))

        # Opakovaný běh je idempotentní.
        _spust_sekci("texty", omezeni)
        d.projekt.refresh_from_db()
        self.assertEqual(d.projekt.lokalizace, anonymizace.zastupny_text("lokalizace", d.projekt.pk))

    def test_pid_nese_prefix_instance(self):
        """Uložené DOI a IGSN dostanou prefix cílové instance ze settings."""
        from django.test import override_settings
        from dokument.models import Dokument
        from lokalita.models import Lokalita
        from pas.models import SamostatnyNalez

        d = self.d
        omezeni = {Dokument: [d.dokument.pk], Lokalita: [d.lokalita.pk], SamostatnyNalez: [d.nalez.pk]}
        with override_settings(DOI_PREFIX="10.99999", IGSN_PREFIX="10.88888"):
            _spust_sekci("pid", omezeni)

        d.dokument.refresh_from_db()
        d.lokalita.refresh_from_db()
        d.nalez.refresh_from_db()
        self.assertEqual(d.dokument.doi, anonymizace.zastupny_pid("10.99999", d.dokument.ident_cely))
        self.assertEqual(d.lokalita.igsn, anonymizace.zastupny_pid("10.88888", d.zaznam.ident_cely))
        self.assertEqual(d.nalez.igsn, anonymizace.zastupny_pid("10.88888", d.nalez.ident_cely))

    def test_prazdny_prefix_hodnotu_vynuluje(self):
        """Instance bez prefixu nesmí držet produkční identifikátor."""
        from django.test import override_settings
        from dokument.models import Dokument

        with override_settings(DOI_PREFIX="", IGSN_PREFIX="10.88888"):
            _spust_sekci("pid", {Dokument: [self.d.dokument.pk]})

        self.d.dokument.refresh_from_db()
        self.assertIsNone(self.d.dokument.doi)

    def test_snapshot_katastru_odpovida_modelu(self):
        """Hromadná přegenerace dá týž text jako ``Lokalita.set_snapshots``."""
        from lokalita.models import Lokalita

        lokalita = self.d.lokalita
        prikaz = _OmezenyPrikaz.vytvor({Lokalita: [lokalita.pk]})
        prikaz.statistika["geometrie"] = {"zpracovano": 0, "zmeneno": 0, "preskoceno": 0, "chyb": 0}
        prikaz._obnov_snapshot_katastru(_volby_prikazu())

        lokalita.refresh_from_db()
        ocekavana = Lokalita.objects.get(pk=lokalita.pk)
        ocekavana.set_snapshots()
        self.assertEqual(lokalita.dalsi_katastry_snapshot, "Katastr 1; Katastr 2")
        self.assertEqual(lokalita.dalsi_katastry_snapshot, ocekavana.dalsi_katastry_snapshot)


class TestNahodneKatastry(TestCase):
    """Náhodné katastry musí zůstat v okrese a nahradit ty skutečné."""

    @classmethod
    def setUpTestData(cls):
        """
        Založí data sdílená testy třídy.

        :return: Nevrací hodnotu.
        """
        cls.d = _vytvor_data()

    def _prikaz(self):
        """
        Připraví příkaz s pevným zrnem náhody.

        :return: Instance příkazu s tichým výstupem.
        """
        from core.management.commands.anonymizace_dat import Command

        prikaz = Command(stdout=io.StringIO(), stderr=io.StringIO())
        prikaz.generator_nahody = random.Random(4264)
        prikaz.statistika["geometrie"] = {"zpracovano": 0, "zmeneno": 0, "preskoceno": 0, "chyb": 0}
        return prikaz

    def test_vyber_zustane_v_okrese_a_mimo_vyloucene(self):
        """Vybrané katastry leží v zadaném okrese a nejsou mezi vyloučenými."""
        katastry = {katastr.pk for katastr in self.d.katastry}
        vyloucit = {self.d.katastry[0].pk, self.d.katastry[1].pk}

        vybrane = self._prikaz()._vyber_nahodne_katastry(self.d.okres.pk, 2, vyloucit)

        self.assertEqual(len(set(vybrane)), 2)
        self.assertTrue(set(vybrane) <= katastry - vyloucit)
        # Stejné zrno dá stejný výběr, což je smysl volby ``--seed``.
        self.assertEqual(self._prikaz()._vyber_nahodne_katastry(self.d.okres.pk, 2, vyloucit), vybrane)
        # Požadavek nad počet dostupných katastrů vrátí všechny dostupné.
        self.assertEqual(len(self._prikaz()._vyber_nahodne_katastry(self.d.okres.pk, 100, vyloucit)), 4)

    def test_chraneny_zaznam_dostane_jine_katastry_z_okresu(self):
        """Hlavní i další katastry se vymění za jiné katastry téhož okresu."""
        from arch_z.models import ArcheologickyZaznam, ArcheologickyZaznamKatastr

        zaznam = self.d.zaznam
        puvodni = {katastr.pk for katastr in self.d.katastry[:3]}

        self._prikaz()._nahodne_katastry_zaznamu(
            ArcheologickyZaznam.objects.filter(pk=zaznam.pk),
            ArcheologickyZaznamKatastr,
            "archeologicky_zaznam_id",
            preskocit=frozenset(),
            ponechat_hlavni={},
            options=_volby_prikazu(),
        )

        zaznam.refresh_from_db()
        dalsi = set(zaznam.katastry.values_list("pk", flat=True))
        self.assertNotIn(zaznam.hlavni_katastr_id, puvodni)
        self.assertEqual(len(dalsi), 2)
        self.assertFalse(dalsi & puvodni)
        self.assertNotIn(zaznam.hlavni_katastr_id, dalsi)
        self.assertEqual(zaznam.hlavni_katastr.okres_id, self.d.okres.pk)

    def test_ponechany_hlavni_katastr_se_nemeni(self):
        """U přesunutého projektu zůstává hlavní katastr odvozený z nové polohy."""
        from projekt.models import Projekt, ProjektKatastr

        projekt = self.d.projekt
        puvodni_dalsi = {katastr.pk for katastr in self.d.katastry[1:3]}
        # Hlavní katastr před přesunem; nesmí se vrátit mezi další katastry.
        puvodni_hlavni = self.d.katastry[5].pk

        for _beh in range(10):
            self._prikaz()._nahodne_katastry_zaznamu(
                Projekt.objects.filter(pk=projekt.pk),
                ProjektKatastr,
                "projekt_id",
                preskocit=frozenset(),
                ponechat_hlavni={projekt.pk: puvodni_hlavni},
                options=_volby_prikazu(),
            )
            projekt.refresh_from_db()
            dalsi = set(projekt.katastry.values_list("pk", flat=True))
            self.assertEqual(projekt.hlavni_katastr_id, self.d.katastry[0].pk)
            self.assertEqual(len(dalsi), 2)
            self.assertNotIn(puvodni_hlavni, dalsi)
            self.assertFalse(dalsi & (puvodni_dalsi | {projekt.hlavni_katastr_id}))
            puvodni_dalsi = dalsi

    def test_preskoceny_zaznam_zustane(self):
        """Záznam s katastry přepočítanými z PIANů se náhodně nemění."""
        from arch_z.models import ArcheologickyZaznam, ArcheologickyZaznamKatastr

        zaznam = self.d.zaznam
        zmeneno = self._prikaz()._nahodne_katastry_zaznamu(
            ArcheologickyZaznam.objects.filter(pk=zaznam.pk),
            ArcheologickyZaznamKatastr,
            "archeologicky_zaznam_id",
            preskocit={zaznam.pk},
            ponechat_hlavni={},
            options=_volby_prikazu(),
        )

        zaznam.refresh_from_db()
        self.assertEqual(zmeneno, 0)
        self.assertEqual(zaznam.hlavni_katastr_id, self.d.katastry[0].pk)

    def test_katastry_z_vybranych_pianu(self):
        """Přepočet katastrů smí vzít v úvahu jen zadané PIANy."""
        from heslar.ruian_sync.reassign import compute_az_katastr_assignment

        ident = self.d.zaznam.ident_cely
        # PIAN leží uprostřed katastru 1 (druhý čtverec v řadě).
        self.assertEqual(compute_az_katastr_assignment(ident)[0], self.d.katastry[1].pk)
        self.assertEqual(compute_az_katastr_assignment(ident, pian_ids=[self.d.pian.pk])[0], self.d.katastry[1].pk)
        self.assertEqual(compute_az_katastr_assignment(ident, pian_ids=[]), (None, []))


class TestSekceGeometrie(TestCase):
    """Celá sekce ``geometrie`` nad malými daty – dry-run i ostrý běh."""

    @classmethod
    def setUpTestData(cls):
        """
        Založí data a dá chráněnému projektu bodovou polohu.

        :return: Nevrací hodnotu.
        """
        from django.contrib.gis.geos import Point
        from projekt.models import Projekt

        cls.d = _vytvor_data()
        Projekt.objects.filter(pk=cls.d.projekt.pk).update(
            geom_sjtsk=Point(-699500, -999500, srid=5514), geom=Point(15.0, 50.0, srid=4326)
        )

    def _spust(self, **volby):
        """
        Spustí sekci ``geometrie`` s omezením snapshotů na testovací lokalitu.

        :param volby: Volby příkazu, které se mají přepsat.
        :return: Instance příkazu po doběhnutí sekce.
        """
        from lokalita.models import Lokalita

        return _spust_sekci("geometrie", {Lokalita: [self.d.lokalita.pk]}, **volby)

    def test_dry_run_nic_nezmeni(self):
        """Dry-run projde všechny kroky, spočítá záznamy a nic nezapíše."""
        from pian.models import Pian

        prikaz = self._spust(dry_run=True)

        self.assertEqual(Pian.objects.get(pk=self.d.pian.pk).geom_sjtsk.wkt, self.d.pian.geom_sjtsk.wkt)
        # PIAN, projekt, nález, záznam s PIANem, chráněný záznam, projekt ke katastrům, lokalita.
        self.assertGreaterEqual(prikaz.statistika["geometrie"]["zpracovano"], 5)
        self.assertEqual(prikaz.statistika["geometrie"]["zmeneno"], 0)

    def test_ostry_beh_presune_a_prepocita_katastry(self):
        """PIAN i projekt se přesunou v okrese a katastry odpovídají nové poloze."""
        from arch_z.models import ArcheologickyZaznam
        from core.utils import get_cadastre_from_point
        from heslar.models import RuianKatastr
        from lokalita.models import Lokalita
        from pian.models import Pian
        from projekt.models import Projekt

        d = self.d
        puvodni_projekt = {k.pk for k in d.katastry[:3]}
        self._spust()

        pian = Pian.objects.get(pk=d.pian.pk)
        self.assertGreaterEqual(vzdalenost(pian.geom_sjtsk, d.pian.geom_sjtsk), 100)
        self.assertTrue(d.okres.hranice.contains(pian.geom_sjtsk))
        self.assertNotEqual(pian.geom.wkt, d.pian.geom.wkt)

        zaznam = ArcheologickyZaznam.objects.get(pk=d.zaznam.pk)
        nove_misto = get_cadastre_from_point((pian.geom_sjtsk.x, pian.geom_sjtsk.y))
        self.assertEqual(zaznam.hlavni_katastr_id, nove_misto.pk)

        projekt = Projekt.objects.get(pk=d.projekt.pk)
        katastr_projektu = get_cadastre_from_point((projekt.geom_sjtsk.x, projekt.geom_sjtsk.y))
        self.assertEqual(projekt.hlavni_katastr_id, katastr_projektu.pk)
        dalsi = set(projekt.katastry.values_list("pk", flat=True))
        self.assertEqual(len(dalsi), 2)
        self.assertNotIn(projekt.hlavni_katastr_id, dalsi)
        self.assertFalse(dalsi & (puvodni_projekt - {projekt.hlavni_katastr_id}))
        self.assertEqual(
            set(RuianKatastr.objects.filter(pk__in=dalsi).values_list("okres_id", flat=True)), {d.okres.pk}
        )

        lokalita = Lokalita.objects.get(pk=d.lokalita.pk)
        ocekavany = Lokalita.sestav_snapshot_katastru(
            list(zaznam.katastry.order_by("nazev").values_list("nazev", flat=True))
        )
        self.assertEqual(lokalita.dalsi_katastry_snapshot, ocekavany)

    def test_okres_pianu_se_bere_z_jeho_polohy(self):
        """
        PIAN ležící v jiném okrese než hlavní katastr záznamu zůstane ve svém okrese.

        Dřív se okres bral z hlavního katastru záznamu, takže by se PIAN buď
        přesunul do cizího okresu, nebo zůstal na skutečné poloze.
        """
        from core.management.commands.anonymizace_dat import Command
        from django.contrib.gis.geos import MultiPolygon, Point
        from heslar.models import RuianKatastr, RuianOkres
        from pian.models import Pian

        okres2 = RuianOkres.objects.bulk_create(
            [
                RuianOkres(
                    nazev="Okres 2",
                    nazev_en="District 2",
                    kraj=self.d.okres.kraj,
                    spz="YY",
                    kod=2,
                    hranice=MultiPolygon(_ctverec(-690000, -1000000, 1000)),
                )
            ]
        )[0]
        katastr2 = RuianKatastr.objects.bulk_create(
            [
                RuianKatastr(
                    okres=okres2,
                    nazev="Katastr jinde",
                    kod=99,
                    hranice=MultiPolygon(_ctverec(-690000, -1000000, 1000)),
                    definicni_bod=Point(-689500, -999500, srid=5514),
                )
            ]
        )[0]
        Pian.objects.filter(pk=self.d.pian.pk).update(geom_sjtsk=Point(-689500, -999500, srid=5514))

        radky = {radek[0]: radek for radek in Command()._chranene_piany()}

        _pian_id, _zm50, okres_id, katastr_id, _zkratka = radky[self.d.pian.pk]
        self.assertEqual(okres_id, okres2.pk)
        self.assertEqual(katastr_id, katastr2.pk)
