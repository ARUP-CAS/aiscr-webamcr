import logging
import unittest

from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
from core.constants import AZ_STAV_ARCHIVOVANY, AZ_STAV_ODESLANY, AZ_STAV_ZAPSANY
from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from dj.models import DokumentacniJednotka
from django.conf import settings
from django.utils.translation import gettext as _
from dokument.models import Dokument
from freezegun import freeze_time
from komponenta.models import Komponenta
from lokalita.models import Lokalita
from nalez.models import NalezObjekt, NalezPredmet
from pian.models import Pian
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceLokality(BaseSeleniumTestClass):
    """Zapouzdřuje chování třídy ``AkceLokality`` pro modul ``webclient.lokalita.tests.test_selenium``."""
    def go_to_form_zapsat(self):
        """Zajišťuje logiku funkce ``go_to_form_zapsat``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.goToAddress("/arch-z/lokalita/zapsat")

    def go_to_form_vybrat(self):
        """Zajišťuje logiku funkce ``go_to_form_vybrat``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.goToAddress("/arch-z/lokalita/vyber?sort=nazev")

    def test_051_zapsani_lokality_p_001(self):
        """Test 051 Zapsání lokality (pozitivní scénář 1)

        Test zapsání lokality na stránce /arch-z/lokalita/zapsat. Končí zapsáním lokality do databáze.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen

        Steps:
            - Uživatel se přihlásí
            - Uživatel klikne na menu Lokality -> Zapsat
            - Uživatel vyplní data do formuláře
            - Uživatel klikne na tlačítko Zapsat

        Expected:
            - Po kliknutí na tlačítko Zapsat je v databázi o jednu lokalitu více.
        """
        logger.info("AkceLokality.test_051_zapsani_lokality_p_001.start")
        self.login("archeolog")
        self.go_to_form_zapsat()
        count_old = Lokalita.objects.count()

        self.ElementClick(By.ID, "select2-id_hlavni_katastr-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            "Křtiny"
        )
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            Keys.ENTER
        )
        self.ElementClick(By.CSS_SELECTOR, "#div_id_druh .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("pol")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-5-0 > .text")
        # self.ElementClick(By.ID, "div_id_nazev")
        self.wait(1)
        self.ElementClick(By.ID, "id_nazev")
        self.driver.find_element(By.ID, "id_nazev").send_keys("test")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")

        count_new = Lokalita.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceLokality.test_051_zapsani_lokality_p_001.end")

    def test_052_zapsani_lokality_n_001(self):
        """Test 052 Zapsání lokality (negativní scénář 1)

        Test zapsání lokality na stránce /arch-z/lokalita/zapsat. Nekončí zapsáním lokality do databáze.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.

        Steps:
            - Uživatel se přihlásí
            - Uživatel klikne na menu Lokality -> Zapsat
            - Uživatel vyplní data do formuláře, nevyplní pole Název
            - Uživatel klikne na tlačítko Zapsat

        Expected:
            - Neúspěšné zapsání lokality, počet lokalit v databázi se nezměnil.
            - Zobrazena nápověda “Vyplňte prosím toto pole” u pole Název.
        """
        logger.info("AkceLokality.test_052_zapsani_lokality_n_001.start")
        self.login("archeolog")
        self.go_to_form_zapsat()
        count_old = Lokalita.objects.count()

        self.ElementClick(By.ID, "select2-id_hlavni_katastr-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Křtiny")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_druh .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("pol")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-5-0 > .text")
        # self.ElementClick(By.ID, "div_id_nazev")
        # self.ElementClick(By.ID, "id_nazev")
        # self.driver.find_element(By.ID, "id_nazev").send_keys("test")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "newEntitySubmitBtn")
        except Exception:
            pass

        count_new = Lokalita.objects.count()
        self.assertEqual(count_old, count_new)
        logger.info("AkceLokality.test_052_zapsani_lokality_n_001.end")

    def test_053_pridani_DJ_lokality_p_001(self):
        """Test 053 Přidání dokumentační jednotky lokalita (pozitivní scénář 1)

        Test vytvoření dokumentační jednotky typu lokalita u lokalita ve stavu L1. Scénář končí vytvořením dokumentační jednotky D01 typu lokalita.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Lokalita je ve stavu L1 a nemá žádnou dokumentační jednotku

        TestData:
            X-C-L000000001

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře lokalitu ve stavu L1 (viz předpoklady)
            - Lokalita → Vybrat → Filtr → ID obsahuje „X-C-L000000001“ → Vybrat → otevřít lokalitu
            - Kliknout na tlačítko “Přidat dokumentační jednotku”
            - Zvolit typ DJ “lokalita”
            - Zvolit typ Negativní jednotka “ne”
            - Kliknout na “uložit”

        Expected:
            - U akce bude vytvořena DJ typu “lokalita” (v databázi je o jednu DJ více).
        """
        logger.info("AkceLokality.test_053_pridani_DJ_lokality_p_001.start")
        self.login("archeolog")
        self.go_to_form_vybrat()
        count_old = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-L000000001").count()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-L000000001")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")

        self.ElementClick(By.LINK_TEXT, "X-C-L000000001")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-2 > .text")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-2-0")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDjSubmitButton")

        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-L000000001").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceLokality.test_053_pridani_DJ_lokality_p_001.end")

    def test_054_pridani_DJ_lokality_n_001(self):
        """Test 054 Přidání dokumentační jednotky lokalita (negativní scénář 1)

        Test vytvoření dokumentační jednotky typu lokalita u lokalita ve stavu L1. Scénář nekončí vytvořením dokumentační jednotky D01 typu lokalita.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Lokalita je ve stavu L1 a nemá žádnou dokumentační jednotku

        TestData:
            X-C-L000000001

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře lokalitu ve stavu L1 (viz předpoklady)
            - Lokalita → Vybrat → Filtr → ID obsahuje „X-C-L000000001“ → Vybrat → otevřít lokalitu
            - Kliknout na tlačítko “Přidat dokumentační jednotku”
            - Zvolit typ Negativní jednotka “ne”, nevybere pole Typ
            - Kliknout na “uložit”

        Expected:
            - Neúspěšné vytvoření DJ typu “lokalita”, počet DJ v databázi se nezměnil.
            - Zobrazena nápověda “Vyberte prosím v seznamu některou položku” u pole Typ.
        """
        logger.info("AkceLokality.test_054_pridani_DJ_lokality_n_001.start")
        self.login("archeolog")
        self.go_to_form_vybrat()
        count_old = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-L000000001").count()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-L000000001")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")

        self.ElementClick(By.LINK_TEXT, "X-C-L000000001")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        # self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        # self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-2 > .text")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-2-0")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "newDjSubmitButton")
        except Exception:
            pass

        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-L000000001").count()
        self.assertEqual(count_old, count_new)
        logger.info("AkceLokality.test_054_pridani_DJ_lokality_n_001.end")

    def test_055_pridani_komponenty_DJ_lokality_p_001(self):
        """Test 055 Přidání komponenty k dokumentační jednotce lokalita (pozitivní scénář 1)

        Test vytvoření komponenty u dokumentační jednotky typu lokalita u lokality ve stavu L1. Scénář končí vytvořením komponenty K001 u dokumentační jednotky D01.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Lokalita je ve stavu L1 a má dokumentační jednotku D01 typu lokalita, která je pozitivní.

        TestData:
            X-C-L000000002

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře lokalitu ve stavu L1 (X-C-L000000002)
            - Lokalita → Vybrat → Filtr → ID obsahuje „X-C-L000000002“ → Vybrat → otevřít lokalitu
            - Kliknout na dokumentační jednotku D01
            - Kliknout na “Další volby” a zvolit ”Komponenta - vytvořit”.
            - Zvolit Období “únětická k.”
            - Zvolit Areál “sídliště nesp.”.
            - Kliknout na “uložit změny”

        Expected:
            - U DJ D01 bude vytvořena nová komponenta K001, v databázi bude o jednu komponentu více.
        """
        logger.info("AkceLokality.test_055_pridani_komponenty_DJ_lokality_p_001.start")
        self.login("archeolog")
        self.go_to_form_vybrat()
        count_old = Komponenta.objects.filter(
            komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-L000000002-D01"
        ).count()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")

        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-L000000002")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "X-C-L000000002")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_L000000002_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_X-C-L000000002-D01 > .card-header .material-icons")
        self.ElementClick(By.LINK_TEXT, _("lokalita.templates.dj.djUpdate.moreActions.pridatKomponentu.label"))
        self.ElementClick(By.CSS_SELECTOR, "#div_id_obdobi .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("úně")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.DOWN)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("s")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createCompotSubmitButton")

        count_new = Komponenta.objects.filter(
            komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-L000000002-D01"
        ).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceLokality.test_055_pridani_komponenty_DJ_lokality_p_001.end")

    def test_056_odeslani_lokality_p_001(self):
        """Test 056 Odeslání lokality (pozitivní scénář 1)

        Test odeslání lokality ve stavu L1 na stránce /arch-z/lokalita/detail. Měl by končit odesláním lokality a změnou jeho stavu na L2.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Lokalita je ve stavu L1, má připojenu dokumentační jednotku D01, ta má připojenu komponentu K001. Dokumentační jednotka má připojený PIAN.

        TestData:
            C-N9000579

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře lokalitu ve stavu L1
            - Lokalita → Vybrat → Filtr → ID obsahuje „C-N9000579“ → Vybrat → otevřít lokalitu
            - Uživatel klikne na tlačítko Odeslat a volbu potvrdí

        Expected:
            -  Odeslání lokality a změna jejího stavu na L2.
        """
        logger.info("AkceLokality.test_056_odeslani_lokality_p_001.start")
        self.login("archeolog")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000579").first().stav, AZ_STAV_ZAPSANY)

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")

        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N9000579")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N9000579")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-odeslat > .app-controls-button-text")
        self.wait(1)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000579").first().stav, AZ_STAV_ODESLANY)
        logger.info("AkceLokality.test_056_odeslani_lokality_p_001.end")

    def test_057_odeslani_lokality_n_001(self):
        """Test 057 Odeslání dokumentu (negativní scénář 1)

        Test odeslání dokumentu ve stavu D1 na stránce /dokument/detail/. Měl by končit neúspěšným odesláním dokumentu a jeho ponecháním ve stavu D1.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Dokument je ve stavu D1.

        TestData:
            X-C-TX-000000003

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře dokument ve stavu L1
            - Dokument → Vybrat → Filtr → ID obsahuje „X-C-TX-000000003“ → Vybrat → otevřít dokument
            - Uživatel klikne na tlačítko Odeslat

        Expected:
            -  Neúspěšné odeslání dokumentu a jeho ponechání ve stavu D1. Chybová hláška “Dokument nelze odeslat, zkontrolujte zda má všechny náležitosti.” a nápověda “Dokument musí mít alespoň jeden soubor.”,
        """
        logger.info("AkceLokality.test_057_odeslani_lokality_n_001.start")

        self.login("archeolog")
        self.createFedoraRecord("C-DT-100000146")
        self.createFedoraRecord("C-DT-100000147")
        self.uploadFileToFedora(81227, "dokument/tests/resources/test.tif")
        self.uploadFileToFedora(81228, "dokument/tests/resources/test.tif")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000145").first().stav, AZ_STAV_ZAPSANY)

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")

        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N9000145")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N9000145")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-odeslat > .app-controls-button-text")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000145").first().stav, AZ_STAV_ZAPSANY)
        logger.info("AkceLokality.test_057_odeslani_lokality_n_001.end")

    def test_058_archivace_lokality_p_001(self):
        """Test 058 Archivace lokality (pozitivní scénář 1)

        Test archivace lokality ve stavu L2 na stránce /arch-z/lokalita/detail. Měl by končit archivací lokality a změnou jeho stavu na L3.

        Role:
            Archivář

        Preconditions:
            - Uživatel je přihlášen.
            - Lokalita je ve stavu L2.

        TestData:
            C-N1000003

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře lokalitu ve stavu L2
            - Lokality → Vybrat → Filtr → ID obsahuje „C-N1000003“ → Vybrat → otevřít lokalitu
            - Uživatel vybere dokumentační jednotku D01 a potvrdí nepotvrzený PIAN
            - Dokumentační jednotky → D01 → Další volby → PIAN - potvrdit
            - Uživatel klikne na tlačítko Archivovat a volbu potvrdí

        Expected:
            - Archivace lokality a její posunutí do stavu L3.
        """
        logger.info("AkceLokality.test_058_archivace_lokality_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-DT-100005206")
        self.createFedoraRecord("C-DY-100000065")
        self.uploadFileToFedora(187330, "dokument/tests/resources/test.tif")
        self.uploadFileToFedora(63104, "dokument/tests/resources/test.tif")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000003").first().stav, AZ_STAV_ODESLANY)
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-archivovat > .material-icons")
        self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, ".custom-control-label")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000003").first().stav, AZ_STAV_ARCHIVOVANY)
        logger.info("AkceLokality.test_058_archivace_lokality_p_001.end")

    def test_059_archivace_lokality_n_001(self):
        """Test 059 Archivace lokality (negativní scénář 1)

        Test archivace lokality ve stavu L2 na stránce /arch-z/lokalita/detail. Měl by končit ponecháním lokality ve stavu L2.

        Role:
            Archivář

        Preconditions:
            - Uživatel je přihlášen.
            - Lokalita je ve stavu L2.

        TestData:
            C-N1000109

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře lokalitu ve stavu L2
            - Lokality → Vybrat → Filtr → ID obsahuje „C-N1000109“ → Vybrat → otevřít lokalitu
            - Uživatel klikne na tlačítko Archivovat

        Expected:
            - K archivaci lokality nedojde, ta zůstane ve stavu L2.
            - Zobrazena chyba “Lokalitu nelze odeslat. Zkontrolujte, zda má všechny náležitosti.” a nápověda “Dokumentační jednotce X-M-K000000034-D01 chybí PIAN.”
        """
        logger.info("AkceLokality.test_059_archivace_lokality_n_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-DT-100005454")
        self.createFedoraRecord("C-DY-100000058")
        self.uploadFileToFedora(187349, "dokument/tests/resources/test.tif")
        self.uploadFileToFedora(63179, "dokument/tests/resources/test.tif")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000109").first().stav, AZ_STAV_ODESLANY)
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N1000109")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N1000109")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-archivovat > .material-icons")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000109").first().stav, AZ_STAV_ODESLANY)
        logger.info("AkceLokality.test_059_archivace_lokality_n_001.end")

    def test_060_vraceni_odeslane_lokality_p_001(self):
        """Test 060 Vrácení odeslané lokality (pozitivní scénář 1)

        Test vrácení lokality ve stavu L2 na stránce /arch-z/lokalita/detail. Měl by končit vrácením lokality a změnou jejího stavu na L1.

        Role:
            Archivář

        Preconditions:
            - Uživatel je přihlášen.
            - Lokalita je ve stavu L2

        TestData:
            C-N1000003

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře lokalitu ve stavu L2
            - Lokality → Vybrat → Filtr → ID obsahuje „C-N1000003“ → Vybrat → otevřít lokalitu
            - Uživatel klikne na tlačítko Vrátit, vyplní důvod a volbu potvrdí

        Expected:
            - Vrácení lokality do stavu L1.
        """
        logger.info("AkceLokality.test_060_vraceni_odeslane_lokality_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-DT-100005206")
        self.createFedoraRecord("C-DY-100000065")
        self.uploadFileToFedora(187330, "dokument/tests/resources/test.tif")
        self.uploadFileToFedora(63104, "dokument/tests/resources/test.tif")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000003").first().stav, AZ_STAV_ODESLANY)

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-vratit > .app-controls-button-text")
        self.wait(1)
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000003").first().stav, AZ_STAV_ZAPSANY)
        logger.info("AkceLokality.test_060_vraceni_odeslane_lokality_p_001.end")

    def test_061_vraceni_odeslane_lokality_n_001(self):
        """Test 061 Vrácení odeslané lokality (negativní scénář 1)

        Test vrácení lokality ve stavu L2 na stránce /arch-z/lokalita/detail. Měl by končit neúspěšným vrácením a ponecháním lokality ve stavu L2.

        Role:
            Archivář

        Preconditions:
            - Uživatel je přihlášen.
            - Lokalita je ve stavu L2

        TestData:
            C-N1000003

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře lokalitu ve stavu L2
            - Lokality → Vybrat → Filtr → ID obsahuje „C-N1000003“ → Vybrat → otevřít lokalitu
            - Uživatel klikne na tlačítko Vrátit a volbu potvrdí

        Expected:
            - K vrácení lokality nedojde, ta zůstane ve stavu L2.
            - Zobrazena nápověda “Vyplňte prosím toto pole”
        """
        logger.info("AkceLokality.test_061_vraceni_odeslane_lokality_n_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-DT-100005206")
        self.createFedoraRecord("C-DY-100000065")
        self.uploadFileToFedora(187330, "dokument/tests/resources/test.tif")
        self.uploadFileToFedora(63104, "dokument/tests/resources/test.tif")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000003").first().stav, AZ_STAV_ODESLANY)

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-vratit > .app-controls-button-text")
        # self.ElementClick(By.ID, "id_reason")
        # self.driver.find_element(By.ID, "id_reason").send_keys("test")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000003").first().stav, AZ_STAV_ODESLANY)
        logger.info("AkceLokality.test_061_vraceni_odeslane_lokality_n_001.end")

    def test_062_vraceni_archivovane_lokality_p_001(self):
        """Test 062 Vrácení archivované lokality (pozitivní scénář 1)

        Test vrácení lokality ve stavu L3 na stránce /arch-z/lokalita/detail. Měl by končit vrácením lokality a změnou jejího stavu na L2.

        Role:
            Archivář

        Preconditions:
            - Uživatel je přihlášen.
            - Lokalita je ve stavu L3

        TestData:
            C-N9000593

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře lokalitu ve stavu L3
            - Lokality → Vybrat → Filtr → ID obsahuje „C-N9000593“ → Vybrat → otevřít lokalitu
            - Uživatel klikne na tlačítko Vrátit, vyplní důvod a volbu potvrdí

        Expected:
            - Vrácení lokality do stavu L2.
        """
        logger.info("AkceLokality.test_062_vraceni_archivovane_lokality_p_001.start")

        self.login("archivar")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000593").first().stav, AZ_STAV_ARCHIVOVANY)

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N9000593")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N9000593")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-vratit > .app-controls-button-text")
        self.wait(1)
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000593").first().stav, AZ_STAV_ODESLANY)
        logger.info("AkceLokality.test_062_vraceni_archivovane_lokality_p_001.end")

    def test_063_vraceni_archivovane_lokality_n_001(self):
        """Test 063 Vrácení archivované lokality (negativní scénář 1)

        Test vrácení lokality ve stavu L3 na stránce /arch-z/lokalita/detail. Měl by končit neúspěšným vrácením a ponecháním lokality ve stavu L3.

        Role:
            Archivář

        Preconditions:
            - Uživatel je přihlášen.
            - Lokalita je ve stavu L3

        TestData:
            C-N9000593

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře lokalitu ve stavu L3
            - Lokality → Vybrat → Filtr → ID obsahuje „C-N9000593“ → Vybrat → otevřít lokalitu
            - Uživatel klikne na tlačítko Vrátit a volbu potvrdí

        Expected:
            - K vrácení lokality nedojde, ta zůstane ve stavu L3.
            - Zobrazena nápověda “Vyplňte prosím toto pole”
        """
        logger.info("AkceLokality.test_063_vraceni_archivovane_lokality_n_001.start")

        self.login("archivar")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000593").first().stav, AZ_STAV_ARCHIVOVANY)

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N9000593")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N9000593")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-vratit > .app-controls-button-text")
        # self.ElementClick(By.ID, "id_reason")
        # self.driver.find_element(By.ID, "id_reason").send_keys("test")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000593").first().stav, AZ_STAV_ARCHIVOVANY)
        logger.info("AkceLokality.test_063_vraceni_archivovane_lokality_n_001.end")

    def test_143_test_Fedory_lokalita_p_001(self):
        """Test 143 Test Fedory pro lokalitu (pozitivní scénář 1)

        Role:
            Archivář

        TestData:
            ruian-679038
            BIB-0000001
            X-C-K0751147
            N-1412-000000007
            M-L9000181
            M-TX-194300151

        Steps:
            - Vytvoření Lokality
            - Editace Lokality
            - Vytvoření DJ
            - Editace DJ
            - Vytvoření PIAN
            - Editace PIAN
            - Vytvoření komponenty
            - Editace komponenty
            - Vytvoření nálezu
            - Editace nálezu
            - Připojení a vytvoření nového Části dokumentu
            - Připojení EZ
            - Editace EZ
            - Odeslání Lokality
            - Smazaní EZ
            - Smazání Části dokumentu
            - Smazání nálezu
            - Smazání komponenty
            - Smazání DJ
            - Smazání Lokality
            - Potvrzení PIAN
            - Připojení existujícího dokumentu

        Expected:
            - zápis dat do Fedory
        """
        logger.info("AkceLokality.test_143_test_Fedory_lokalita_p_001.start")
        self.login("archivar")
        # Vytvoření lokality
        self.go_to_form_zapsat()
        time = self.getTime()
        self.ElementClick(By.ID, "select2-id_hlavni_katastr-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            "Lanšperk"
        )
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            Keys.ENTER
        )
        self.ElementClick(By.CSS_SELECTOR, "#div_id_druh .filter-option-inner-inner")
        self.ElementSendKeys(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control", "pol")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-5-0 > .text")
        self.wait(1)
        self.ElementClick(By.ID, "id_nazev")
        self.ElementSendKeys(By.ID, "id_nazev", "test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        ident = self.driver.current_url.split("/")[-1]
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_lokalita")

        # Úprava detailu lokality
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.ID, "id_nazev")
        self.ElementSendKeys(By.ID, "id_nazev", "test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/update_lokalita")

        # Vytvoření dokumentační jednotky
        self.createFedoraRecord("ruian-679038", "archivar")
        time = self.getTime()
        self.ElementClick(By.ID, "button-add-dj")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDjSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_DJ")

        # Úprava dokumentační jednotky
        time = self.getTime()
        self.ElementClick(By.ID, f"id_{ident}-D01-nazev")
        self.driver.find_element(By.ID, f"id_{ident}-D01-nazev").send_keys("test")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-L000000003-D01-typ .btn.dropdown-toggle.btn-light")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-2 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editDjSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/update_DJ")

        # Vytvoření záznamu PIAN
        time = self.getTime()
        self.ElementClick(By.ID, "add_others")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "show_menu_pian_new_id")
        self.driver.execute_script("""map.setZoom(17); return map.getZoom();""")
        self.wait(2)
        self.ElementClick(By.LINK_TEXT, _("mapa.EditAddMarker"))
        self.wait(0.5)
        self.clickAtMapCoord(12.8289904, 50.3706078)
        self.wait(0.5)
        self.ElementClick(By.CSS_SELECTOR, ".filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createPianSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_PIAN")

        # Úprava záznamu PIAN
        pian = Pian.objects.filter(dokumentacni_jednotky_pianu__ident_cely="X-C-L000000003-D01").first().ident_cely
        time = self.getTime()
        self.ElementClick(By.ID, "el_dokumentacni_jednotka_X_C_L000000003_D01")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, f"pian-upravit-{pian}")
        self.wait(1)
        self.driver.execute_script("""map.setZoom(17); return map.getZoom();""")
        self.wait(2)
        self.ElementClick(By.LINK_TEXT, _("mapa.EditAddMarker"))
        self.wait(0.5)
        self.clickAtMapCoord(12.9, 49.88)
        self.wait(0.5)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editPianButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/update_PIAN")

        # Vytvoření komponenty
        time = self.getTime()
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, f"#el_dokumentacni_jednotka_{ident.replace('-','_')}_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, f"#detail_dj_form_{ident}-D01 .btn-group:nth-child(1) .material-icons")
        self.ElementClick(
            By.LINK_TEXT, _("arch_z.templates.arch_z.dj.partials.dj_update.editButtons.pridatKomponentu.label")
        )
        self.ElementClick(By.CSS_SELECTOR, "#div_id_obdobi .btn")
        self.ElementClick(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control")
        self.ElementSendKeys(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control", "únětická kultura")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner")
        self.ElementSendKeys(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control", "poh")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.wait(1)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createCompotSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_komponenta")

        # Úprava komponenty
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001-obdobi .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-6 > .text")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001-jistota .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-2-1")
        self.ElementClick(By.ID, f"id_{ident}-K001-presna_datace")
        self.driver.find_element(By.ID, f"id_{ident}-K001-presna_datace").send_keys("ne")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001-areal .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-5 > .text")
        self.ElementClick(By.CSS_SELECTOR, ".show-tick .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-4-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/update_komponenta")

        # Vytvoření nálezu
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_o-0-druh .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-7-8 > .text")
        self.ElementClick(By.ID, f"id_{ident}-K001_o-0-pocet")
        self.driver.find_element(By.ID, f"id_{ident}-K001_o-0-pocet").send_keys("1")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_p-0-druh .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-15-19 > .text")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_p-0-specifikace .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-16-4 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_nalez")

        # Úprava nálezu
        time = self.getTime()
        self.driver.find_element(By.ID, f"id_{ident}-K001_o-0-pocet").send_keys("2")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_p-0-specifikace .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-18-14 > .text")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_o-0-specifikace .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-8-7 > .text")
        self.ElementClick(By.ID, f"id_{ident}-K001_p-0-pocet")
        self.driver.find_element(By.ID, f"id_{ident}-K001_p-0-pocet").send_keys("2")
        self.ElementClick(By.ID, f"id_{ident}-K001_p-0-poznamka")
        self.driver.find_element(By.ID, f"id_{ident}-K001_p-0-poznamka").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/update_nalez")

        # Vytvoření dokumentační části
        time = self.getTime()
        self.ElementClick(By.ID, "others_doc")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("dokument.templates.dokument_table.pridatNovyDokument.label"))
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.ElementSendKeys(By.CSS_SELECTOR, ".select2-search__field", "Pavloň")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vzniku")
        self.ElementSendKeys(By.ID, "id_rok_vzniku", "2023")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(
            "Archeologický ústav Brno"
        )
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-0 > .text")
        self.ElementClick(By.ID, "id_popis")
        self.ElementSendKeys(By.ID, "id_popis", "test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-7-1")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_licence .btn")
        self.ElementClick(By.ID, "bs-select-8-1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        # nahrat soubor
        self.ElementClick(By.ID, "NahratSoubory")
        self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_dokument_cast")

        # Vytvoření externího odkazu
        self.createFedoraRecord("BIB-0000001", "archivar")
        time = self.getTime()
        self.goToAddress(f"/id/{ident}")
        self.ElementClick(By.ID, "eo-pripojit-do-az")
        self.ElementClick(By.ID, "select2-id_ez-container")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_EZ")

        # Úprava externího odkazu
        time = self.getTime()
        pk = ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely=ident).first().pk
        self.ElementClick(By.ID, f"ez-change-{pk}")
        self.ElementSendKeys(By.ID, "id_paginace", "10")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/update_EZ")

        # ident_cely
        time = self.getTime()
        self.ElementClick(By.ID, "lokalita-odeslat")
        with freeze_time("2025-07-27 12:00:01", ignore=["core.tests.test_selenium"]):
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        new_ident = self.driver.current_url.split("/")[-1]
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/ident_cely")
        self.check_fedora_delete(["record/X-C-L000000003", "record/X-C-TX-000000009"])

        # Smazání externího odkazu
        time = self.getTime()
        self.ElementClick(By.ID, f"ez-odpojit-{pk}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/delete_EZ")

        # Smazání dokumentační části
        time = self.getTime()
        dokument_ident = Dokument.objects.filter(casti__archeologicky_zaznam__ident_cely=new_ident).first().ident_cely
        self.ElementClick(By.ID, f"dokument-odpojit-{dokument_ident}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/delete_dokument_cast")

        # Smazání nálezu
        time = self.getTime()
        self.ElementClick(By.ID, f"el_komponenta_{new_ident.replace('-','_')}_K001")
        pk = (
            NalezObjekt.objects.filter(
                komponenta__komponenta_vazby__dokumentacni_jednotka__archeologicky_zaznam__ident_cely=new_ident
            )
            .first()
            .pk
        )
        self.ElementClick(By.ID, f"objekt-smazat-{pk}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        pk = (
            NalezPredmet.objects.filter(
                komponenta__komponenta_vazby__dokumentacni_jednotka__archeologicky_zaznam__ident_cely=new_ident
            )
            .first()
            .pk
        )
        self.ElementClick(By.ID, f"objekt-smazat-{pk}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/delete_nalez")

        # Smazání komponenty
        time = self.getTime()
        self.ElementClick(By.ID, f"el_komponenta_{new_ident.replace('-','_')}_K001")
        self.ElementClick(By.ID, "others_komponenta")
        self.ElementClick(By.ID, f"komponenta-smazat-{new_ident}-K001")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/delete_komponenta")

        # Smazání dokumentační jednotky
        time = self.getTime()
        self.ElementClick(By.ID, f"el_dokumentacni_jednotka_{new_ident.replace('-','_')}_D01")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, f"dj-smazat-{new_ident}-D01")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/delete_DJ")

        # Smazání lokality
        time = self.getTime()
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "lokalita-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/delete_lokalita")

        # změna ident_cely PIAN
        self.createFedoraRecord("X-C-K0751147", "archivar")
        self.createFedoraRecord("N-1412-000000007", "archivar")
        self.createFedoraRecord("C-DT-100005023", "archivar")
        self.createFedoraRecord("C-DT-100005024", "archivar")
        self.uploadFileToFedora(187083, "dokument/tests/resources/test.tif", "archivar")
        self.uploadFileToFedora(187080, "dokument/tests/resources/test.tif", "archivar")
        time = self.getTime()
        self.goToAddress("/arch-z/lokalita/detail/X-C-K0751147/dj/C-K0751147-D01")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "pian-potvrdit-N-1412-000000007")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/ident_cely_PIAN")
        self.check_fedora_delete(["record/N-1412-000000007"])

        # Vytvoření existující dokumentační části
        self.createFedoraRecord("M-L9000181", "archivar")
        self.createFedoraRecord("M-TX-194300151", "archivar")
        self.createFedoraRecord("M-LN-000000803", "archivar")
        self.uploadFileToFedora(418643, "dokument/tests/resources/test.tif", "archivar")
        self.uploadFileToFedora(534769, "dokument/tests/resources/test.tif", "archivar")
        time = self.getTime()
        self.goToAddress("/id/M-L9000181")
        self.ElementClick(By.ID, "others_doc")
        self.ElementClick(By.ID, "dokument-pripojit")
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection--multiple > .select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("M-TX-194300151")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_dokument_cast_1")

        logger.info("AkceLokality.test_143_test_Fedory_lokalita_p_001.end")

    def test_158_smazani_lokality_p_001(self):
        """Test 158 Smazání lokality (pozitivní scénář 1)

        Test smazání záznamu lokality, test zahrne i to, že se smaže i vše, co je na záznam navázané resp. co se má smazat.

        Role:
            Archivář

        Preconditions:
            - Uživatel je přihlášen.
            - Lokalita je ve stavu L2

        TestData:
            C-N1000109

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře lokalitu ve stavu L2
            - Uživatel smaže dokumenty
            - V panelu pro akce kliknout na  “Další volby” → “Smazat záznam”
            - V dalším dialogovém okně “Smazat lokalitu” kliknout na “Smazat”

        Expected:
            - Lokalita je vymazána z databáze.
        """
        logger.info("AkceLokality.test_158_smazani_lokality_p_001.start")

        self.login("archivar")
        self.createFedoraRecord("C-N1000109")
        self.createFedoraRecord("C-DT-100005454")
        self.createFedoraRecord("C-DY-100000058")
        self.uploadFileToFedora(187349, "projekt/tests/resources/test.pdf")
        self.uploadFileToFedora(63179, "projekt/tests/resources/test.pdf")
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000109").count(), 1)
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000109").first().stav, AZ_STAV_ODESLANY)
        self.goToAddress("/arch-z/lokalita/detail/C-N1000109")
        self.ElementClick(By.ID, "dokument-odpojit-C-DT-100005454")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.ElementClick(By.ID, "dokument-odpojit-C-DY-100000058")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "lokalita-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000109").count(), 0)

        logger.info("AkceLokality.test_158_smazani_lokality_p_001.end")
