import logging
import unittest

from core.constants import D_STAV_ARCHIVOVANY, D_STAV_ODESLANY, D_STAV_ZAPSANY
from core.models import Soubor
from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from django.conf import settings
from django.utils.translation import gettext as _
from dokument.models import Dokument, DokumentCast, Let, Tvar
from freezegun import freeze_time
from nalez.models import NalezObjekt, NalezPredmet
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceDokumenty(BaseSeleniumTestClass):
    """Implementuje komponentu ``AkceDokumenty`` v rámci aplikace."""

    def go_to_form_zapsat(self):
        """
        Naviguje na stránku pro zapsání dokumentu.
        """
        self.goToAddress("/dokument/zapsat")

    def test_064_zapsani_dokumentu_p_001(self):
        """
        Test 064 Zapsání dokumentu (pozitivní scénář 1)

        Test zapsání dokumentu na stránce /dokument/zapsat. Končí zapsáním dokumentu do databáze.

        Role:
        Badatel

        Preconditions:
        - Uživatel je přihlášen.

        Steps:
        - Uživatel se přihlásí
        - Uživatel klikne na menu Dokumenty -> Zapsat
        - Uživatel vyplní územní příslušnost
        - Uživatel vyplní data do formuláře
        - Uživatel klikne na tlačítko Zapsat

        Expected:
        - Po kliknutí na tlačítko Zapsat je v databázi o jeden dokument více. Dokument změní svůj stav na D1
        """
        logger.info("AkceDokumenty.test_064_zapsani_dokumentu_p_001.start")
        self.login("badatel")
        self.goToAddress("/dokument/zapsat/do-arch-z/X-C-9000000001A")

        count_old = Dokument.objects.count()

        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Pavloň")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vzniku")
        self.driver.find_element(By.ID, "id_rok_vzniku").send_keys("2023")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(
            "Archeologický ústav Brno"
        )
        # self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-0 > .text")
        # self.wait(1)
        self.ElementClick(By.ID, "id_popis")
        self.driver.find_element(By.ID, "id_popis").send_keys("test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-7-1")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_licence .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-8-1")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")

        count_new = Dokument.objects.count()

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceDokumenty.test_064_zapsani_dokumentu_p_001.end")

    def test_065_zapsani_dokumentu_n_001(self):
        """
        Test 065 Zapsání dokumentu (negativní scénář 1)

        Test zapsání dokumentu na stránce /dokument/zapsat. Končí neúspěšným zapsáním dokumentu do databáze.

        Role:
        Badatel

        Preconditions:
        - Uživatel je přihlášen.

        Steps:
        - Uživatel se přihlásí
        - Uživatel klikne na menu Dokumenty -> Zapsat
        - Uživatel vyplní územní příslušnost
        - Uživatel vyplní data do formuláře, nevyplní pole Autoři
        - Uživatel klikne na tlačítko Zapsat

        Expected:
        - Po kliknutí na tlačítko Zapsat se objeví nápověda u pole autoři “Vyberte prosím v seznamu některou položku”
        """
        logger.info("AkceDokumenty.test_065_zapsani_dokumentu_n_001.start")
        self.login("badatel")
        self.goToAddress("/dokument/zapsat/do-arch-z/X-C-9000000001A")

        count_old = Dokument.objects.count()
        # self.wait(self.wait_interval)
        # self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        # self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Pavloň")
        # self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        # self.wait(1)
        self.ElementClick(By.ID, "id_rok_vzniku")
        self.driver.find_element(By.ID, "id_rok_vzniku").send_keys("2023")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(
            "Archeologický ústav Brno"
        )
        # self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-0 > .text")
        # self.wait(1)
        self.ElementClick(By.ID, "id_popis")
        self.driver.find_element(By.ID, "id_popis").send_keys("test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-7-1")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "newDocumentSubmitBtn")
        except Exception:
            pass
        count_new = Dokument.objects.count()
        self.assertEqual(count_old, count_new)
        logger.info("AkceDokumenty.test_065_zapsani_dokumentu_n_001.end")

    def test_066_odeslani_dokumentu_p_001(self):
        """
        Test 066 Odeslání dokumentu (pozitivní scénář 1)

        Test odeslání dokumentu ve stavu D1 na stránce /dokument/detail/. Měl by končit úspěšným odesláním dokumentu a jeho posunutím do stavu D2.

        Role:
        Badatel

        Preconditions:
        - Uživatel je přihlášen.
        - Dokument je ve stavu D1.

        TestData:
        X-C-TX-000000003

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře dokument ve stavu D1
        - Dokument → Vybrat → Filtr → ID obsahuje „X-C-TX-000000003“ → Vybrat → otevřít dokument
        - Uživatel klikne na tlačítko Odeslat

        Expected:
        - Odeslání dokumentu a změna jeho procesního stavu na D2.
        """
        logger.info("AkceDokumenty.test_066_odeslani_dokumentu_p_001.start")
        self.login("badatel")
        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-000000003").first().stav, D_STAV_ZAPSANY)
        id = Dokument.objects.filter(ident_cely="X-C-TX-000000003").first().id
        self.goToAddress("/dokument/detail/X-C-TX-000000003")
        self.ElementClick(By.ID, "NahratSoubory")
        self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-odeslat > .app-controls-button-text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(Dokument.objects.filter(id=id).first().stav, D_STAV_ODESLANY)

        logger.info("AkceDokumenty.test_066_odeslani_dokumentu_p_001.end")

    def test_067_odeslani_dokumentu_n_001(self):
        """
        Test 067 Odeslání dokumentu (negativní scénář 1)

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
        - Uživatel otevře dokument ve stavu D1
        - Dokument → Vybrat → Filtr → ID obsahuje „X-C-TX-000000003“ → Vybrat → otevřít dokument
        - Uživatel klikne na tlačítko Odeslat

        Expected:
        -  Neúspěšné odeslání dokumentu a jeho ponechání ve stavu D1. Chybová hláška “Dokument nelze odeslat, zkontrolujte zda má všechny náležitosti.” a nápověda “Dokument musí mít alespoň jeden soubor.”,
        """
        logger.info("AkceDokumenty.test_067_odeslani_dokumentu_n_001.start")
        self.login("badatel")
        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-000000003").first().stav, D_STAV_ZAPSANY)
        self.goToAddress("/dokument/detail/X-C-TX-000000003")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.CSS_SELECTOR, "#dokument-odeslat > .app-controls-button-text")
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass

        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-000000003").first().stav, D_STAV_ZAPSANY)
        logger.info("AkceDokumenty.test_067_odeslani_dokumentu_n_001.end")

    def test_068_archivace_dokumentu_p_001(self):
        """
        Test 068 Archivace dokumentu (pozitivní scénář 1)

        Test archivace dokumentu ve stavu D2 na stránce /dokument/detail/. Měl by končit archivací dokumentu a změnou jeho stavu na D3.

        Role:
        Archivář

        Preconditions:
        - Uživatel je přihlášen.
        - Dokument je ve stavu D2.

        TestData:
        X-C-TX-202413020

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře dokument ve stavu D2
        - Dokumenty → Vybrat → Filtr → ID obsahuje „X-C-TX-202413020“ → Vybrat → otevřít dokument
        - Uživatel klikne na tlačítko Archivovat a volbu potvrdí

        Expected:
        - Archivace dokumentu a jeho posunutí do stavu D3.
        """
        logger.info("AkceDokumenty.test_068_archivace_dokumentu_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("X-C-TX-202413020")

        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-202413020").first().stav, D_STAV_ODESLANY)
        id = Dokument.objects.filter(ident_cely="X-C-TX-202413020").first().id
        self.goToAddress("/dokument/detail/X-C-TX-202413020")
        self.ElementClick(By.ID, "NahratSoubory")
        self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")

        self.ElementClick(By.CSS_SELECTOR, "#dokument-archivovat > .app-controls-button-text")
        self.ElementClick(By.ID, "id_confirm")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        # self.wait(self.wait_interval+10)
        self.assertEqual(Dokument.objects.filter(id=id).first().stav, D_STAV_ARCHIVOVANY)
        logger.info("AkceDokumenty.test_068_archivace_dokumentu_p_001.end")

    def test_069_archivace_dokumentu_n_001(self):
        """
        Test 069 Archivace dokumentu (negativní scénář 1)

        Test archivace dokumentu ve stavu D2 na stránce /dokument/detail/. Měl by končit neúspěšnou archivací dokumentu a jeho ponecháním ve stavu D2.

        Role:
        Archivář

        Preconditions:
        - Uživatel je přihlášen.
        - Dokument je ve stavu D1.

        TestData:
        X-C-TX-202413013

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře dokument ve stavu D2
        - Dokument → Vybrat → Filtr → ID obsahuje „X-C-TX-202413013“ → Vybrat → otevřít dokument
        - Uživatel klikne na tlačítko Archivovat

        Expected:
        - Neúspěšná archivace dokumentu a jeho ponechání ve stavu D2. Chybová hláška “Dokument nelze archivovat, zkontrolujte zda má všechny náležitosti.” a nápověda “Dokument musí mít alespoň jeden soubor.”
        """
        logger.info("AkceDokumenty.test_069_archivace_dokumentu_n_001.start")
        self.login("archivar")
        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-202413013").first().stav, D_STAV_ODESLANY)
        id = Dokument.objects.filter(ident_cely="X-C-TX-202413013").first().id

        self.goToAddress("/dokument/detail/X-C-TX-202413013")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.CSS_SELECTOR, "#dokument-archivovat > .app-controls-button-text")
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass

        self.assertEqual(Dokument.objects.filter(id=id).first().stav, D_STAV_ODESLANY)
        logger.info("AkceDokumenty.test_069_archivace_dokumentu_n_001.end")

    def test_070_vraceni_odeslaneho_dokumentu_p_001(self):
        """
        Test 070 Vrácení odeslaného dokumentu (pozitivní scénář 1)

        Test vrácení dokumentu ve stavu D2 na stránce /dokument/detail. Měl by končit vrácením dokumentu a změnou jeho stavu na D1.

        Role:
        Archivář

        Preconditions:
        - Uživatel je přihlášen.
        - Dokument je ve stavu D2

        TestData:
        M-TX-201604272

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře dokument ve stavu D2
        - Dokumenty → Vybrat → Filtr → ID obsahuje „M-TX-201604272“ → Vybrat → otevřít dokument
        - Uživatel klikne na tlačítko Vrátit, vyplní důvod a volbu potvrdí

        Expected:
        - Vrácení dokumentu do stavu D1.
        """
        logger.info("AkceDokumenty.test_070_vraceni_odeslaneho_dokumentu_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("M-TX-201604272")
        self.uploadFileToFedora(53532, "projekt/tests/resources/test.pdf")

        self.assertEqual(Dokument.objects.filter(ident_cely="M-TX-201604272").first().stav, D_STAV_ODESLANY)
        self.goToAddress("/dokument/detail/M-TX-201604272")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text")
        # self.wait(1)
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(Dokument.objects.filter(ident_cely="M-TX-201604272").first().stav, D_STAV_ZAPSANY)
        logger.info("AkceDokumenty.test_070_vraceni_odeslaneho_dokumentu_p_001.end")

    def test_071_vraceni_odeslaneho_dokumentu_n_001(self):
        """
        Test 071 Vrácení odeslaného dokumentu (negativní scénář 1)

        Test vrácení dokumentu ve stavu D2 na stránce /dokument/detail. Měl by končit neúspěšným vrácením a ponecháním dokumentu ve stavu D2.

        Role:
        Archivář

        Preconditions:
        - Uživatel je přihlášen.
        - Dokument je ve stavu D2

        TestData:
        M-TX-201604272

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře dokument ve stavu D2
        - Dokumenty → Vybrat → Filtr → ID obsahuje „M-TX-201604272“ → Vybrat → otevřít dokument
        - Uživatel klikne na tlačítko Vrátit a volbu potvrdí

        Expected:
        - K vrácení dokumentu nedojde, ten zůstane ve stavu D2.
        - Zobrazena nápověda “Vyplňte prosím toto pole”
        """
        logger.info("AkceDokumenty.test_071_vraceni_odeslaneho_dokumentu_n_001.start")
        self.login("archivar")
        self.createFedoraRecord("M-TX-201604272")
        self.uploadFileToFedora(53532, "projekt/tests/resources/test.pdf")

        self.assertEqual(Dokument.objects.filter(ident_cely="M-TX-201604272").first().stav, D_STAV_ODESLANY)
        self.goToAddress("/dokument/detail/M-TX-201604272")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text")
        # self.ElementClick(By.ID, "id_reason")
        # self.driver.find_element(By.ID, "id_reason").send_keys("test")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass
        self.assertEqual(Dokument.objects.filter(ident_cely="M-TX-201604272").first().stav, D_STAV_ODESLANY)
        logger.info("AkceDokumenty.test_071_vraceni_odeslaneho_dokumentu_n_001.end")

    def test_072_vraceni_archivovaneho_dokumentu_p_001(self):
        """
        Test 072 Vrácení archivovaného dokumentu (pozitivní scénář 1)

        Test vrácení dokumentu ve stavu D3 na stránce /dokument/detail. Měl by končit vrácením dokumentu a změnou jeho stavu na D2.

        Role:
        Archivář

        Preconditions:
        - Uživatel je přihlášen.
        - Dokument je ve stavu D3

        TestData:
        C-TX-202400071

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře dokument ve stavu D3
        - Dokumenty → Vybrat → Filtr → ID obsahuje „C-TX-202400071“ → Vybrat → otevřít dokument
        - Uživatel klikne na tlačítko Vrátit, vyplní důvod a volbu potvrdí

        Expected:
        - Vrácení dokumentu do stavu D2.
        """
        logger.info("AkceDokumenty.test_072_vraceni_archivovaneho_dokumentu_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-TX-202400071")
        self.uploadFileToFedora(638784, "projekt/tests/resources/test.pdf")

        self.assertEqual(Dokument.objects.filter(ident_cely="C-TX-202400071").first().stav, D_STAV_ARCHIVOVANY)
        self.goToAddress("/dokument/detail/C-TX-202400071")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text")
        # self.wait(1)
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(Dokument.objects.filter(ident_cely="C-TX-202400071").first().stav, D_STAV_ODESLANY)
        logger.info("AkceDokumenty.test_072_vraceni_archivovaneho_dokumentu_p_001.end")

    def test_073_vraceni_archivovaneho_dokumentu_n_001(self):
        """
        Test 073 Vrácení archivovaného dokumentu (negativní scénář 1)

        Test vrácení dokumentu ve stavu D3 na stránce /dokument/detail. Měl by končit neúspěšným vrácením a ponecháním dokumentu ve stavu D3.

        Role:
        Archivář

        Preconditions:
        - Uživatel je přihlášen.
        - Dokument je ve stavu D3

        TestData:
        C-TX-202400071

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře dokument ve stavu D3
        - Lokality → Vybrat → Filtr → ID obsahuje „C-TX-202400071“ → Vybrat → otevřít dokument
        - Uživatel klikne na tlačítko Vrátit a volbu potvrdí

        Expected:
        - K vrácení dokumentu nedojde, ten zůstane ve stavu D3.
        - Zobrazena nápověda “Vyplňte prosím toto pole”
        """
        logger.info("AkceDokumenty.test_073_vraceni_archivovaneho_dokumentu_n_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-TX-202400071")
        self.uploadFileToFedora(638784, "projekt/tests/resources/test.pdf")

        self.assertEqual(Dokument.objects.filter(ident_cely="C-TX-202400071").first().stav, D_STAV_ARCHIVOVANY)
        self.goToAddress("/dokument/detail/C-TX-202400071")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text")
        # self.ElementClick(By.ID, "id_reason")
        # self.driver.find_element(By.ID, "id_reason").send_keys("test")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass
        self.assertEqual(Dokument.objects.filter(ident_cely="C-TX-202400071").first().stav, D_STAV_ARCHIVOVANY)
        logger.info("AkceDokumenty.test_073_vraceni_archivovaneho_dokumentu_n_001.end")

    def test_132_zapsani_dokumentu_p_002(self):
        """
        Test 132 Zapsání dokumentu (pozitivní scénář 2)

        Test zapsání dokumentu na stránce /dokument/zapsat. Končí zapsáním dokumentu do databáze.

        Role:
        Archeolog

        Preconditions:
        - Uživatel je přihlášen.

        Steps:
        - Uživatel se přihlásí
        - Uživatel klikne na menu Dokumenty -> Zapsat
        - Uživatel vyplní územní příslušnost
        - Uživatel vyplní data do formuláře
        - Uživatel klikne na tlačítko Zapsat

        Expected:
        - Po kliknutí na tlačítko Zapsat je v databázi o jeden dokument více. Dokument změní svůj stav na D1
        """
        logger.info("AkceDokumenty.test_132_zapsani_dokumentu_p_002.start")
        self.login("archeolog")
        self.goToAddress("/dokument/zapsat/do-arch-z/X-C-9000000013A")
        count_old = Dokument.objects.count()
        # self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Pavloň")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vzniku")
        self.driver.find_element(By.ID, "id_rok_vzniku").send_keys("2023")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(
            "Archeologický ústav Brno"
        )
        # self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-0 > .text")
        # self.wait(1)
        self.ElementClick(By.ID, "id_popis")
        self.driver.find_element(By.ID, "id_popis").send_keys("test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-7-1")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        count_new = Dokument.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceDokumenty.test_132_zapsani_dokumentu_p_002.end")

    def test_133_zapsani_dokumentu_n_002(self):
        """
        Test 133 Zapsání dokumentu (negativní scénář 2)

        Test zapsání dokumentu na stránce /dokument/zapsat. Končí neúspěšným zapsáním dokumentu do databáze.

        Role:
        Archeolog

        Preconditions:
        - Uživatel je přihlášen.

        TestData:
        Očekávané výsledky
        ^^^^^^^^^^^^^^^^^^

        - Po kliknutí na tlačítko Zapsat se objeví nápověda u pole autoři “Vyberte prosím v seznamu některou položku”

        Steps:
        - Uživatel se přihlásí
        - Uživatel klikne na menu Dokumenty -> Zapsat
        - Uživatel vyplní územní příslušnost
        - Uživatel vyplní data do formuláře, nevyplní pole Autoři
        - Uživatel klikne na tlačítko Zapsat

        Expected:
        - Formulář se neuloží a zobrazí validaci u pole Autoři.
        - U pole Autoři se zobrazí nápověda „Vyberte prosím v seznamu některou položku“.
        """
        logger.info("AkceDokumenty.test_133_zapsani_dokumentu_n_002.start")
        self.login("archeolog")
        self.goToAddress("/dokument/zapsat/do-arch-z/X-C-9000000013A")

        count_old = Dokument.objects.count()
        # self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        # self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Pavloň")
        # self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        # self.wait(1)
        self.ElementClick(By.ID, "id_rok_vzniku")
        self.driver.find_element(By.ID, "id_rok_vzniku").send_keys("2023")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(
            "Archeologický ústav Brno"
        )
        # self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-0 > .text")
        # self.wait(1)
        self.ElementClick(By.ID, "id_popis")
        self.driver.find_element(By.ID, "id_popis").send_keys("test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-7-1")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "newDocumentSubmitBtn")
        except Exception:
            pass
        count_new = Dokument.objects.count()

        self.assertEqual(count_old, count_new)
        logger.info("AkceDokumenty.test_133_zapsani_dokumentu_n_002.end")

    def test_134_odeslani_dokumentu_p_002(self):
        """
        Test 134 Odeslání dokumentu (pozitivní scénář 2)

        Test odeslání dokumentu ve stavu D1 na stránce /dokument/detail/. Měl by končit úspěšným odesláním dokumentu a jeho posunutím do stavu D2.

        Role:
        Archeolog

        Preconditions:
        - Uživatel je přihlášen.
        - Dokument je ve stavu D1.

        TestData:
        X-C-TX-000000002

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře dokument ve stavu L1
        - Dokument → Vybrat → Filtr → ID obsahuje „X-C-TX-000000002“ → Vybrat → otevřít dokument
        - Uživatel klikne na tlačítko Odeslat

        Expected:
        - Odeslání dokumentu a změna jeho procesního stavu na D2.
        """
        logger.info("AkceDokumenty.test_134_odeslani_dokumentu_p_002.start")
        self.login("archeolog")
        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-000000002").first().stav, D_STAV_ZAPSANY)
        DBid = Dokument.objects.filter(ident_cely="X-C-TX-000000002").first().id
        self.goToAddress("/dokument/detail/X-C-TX-000000002")
        self.ElementClick(By.ID, "NahratSoubory")
        self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-odeslat > .app-controls-button-text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(Dokument.objects.filter(id=DBid).first().stav, D_STAV_ODESLANY)
        logger.info("AkceDokumenty.test_134_odeslani_dokumentu_p_002.end")

    def test_135_odeslani_dokumentu_n_002(self):
        """
        Test 135 Odeslání dokumentu (negativní scénář 2)

        Test odeslání dokumentu ve stavu D1 na stránce /dokument/detail/. Měl by končit neúspěšným odesláním dokumentu a jeho ponecháním ve stavu D1.

        Role:
        Archeolog

        Preconditions:
        - Uživatel je přihlášen.
        - Dokument je ve stavu D1.

        TestData:
        X-C-TX-000000002

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře dokument ve stavu L1
        - Dokument → Vybrat → Filtr → ID obsahuje „X-C-TX-000000002“ → Vybrat → otevřít dokument
        - Uživatel klikne na tlačítko Odeslat

        Expected:
        - Neúspěšné odeslání dokumentu a jeho ponechání ve stavu D1. Chybová hláška “Dokument nelze odeslat, zkontrolujte zda má všechny náležitosti.” a nápověda “Dokument musí mít alespoň jeden soubor.”,
        """
        logger.info("AkceDokumenty.test_135_odeslani_dokumentu_n_002.start")
        self.login("archeolog")
        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-000000002").first().stav, D_STAV_ZAPSANY)
        DBid = Dokument.objects.filter(ident_cely="X-C-TX-000000002").first().id
        self.goToAddress("/dokument/detail/X-C-TX-000000002")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.CSS_SELECTOR, "#dokument-odeslat > .app-controls-button-text")
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass
        self.assertEqual(Dokument.objects.filter(id=DBid).first().stav, D_STAV_ZAPSANY)
        logger.info("AkceDokumenty.test_135_odeslani_dokumentu_n_002.end")

    def test_141_test_Fedory_dokument_p_001(self):
        """
        Test 141 Test Fedory pro Dokument (pozitivní scénář 1)

        Role:
        Archivář

        TestData:
        C-LET-00001
        C-200810821A
        C-K9000001
        C-201911202
        C-TX-197602290
        X-C-TX-201801164
        C-201125635A
        C-202010506
        C-K9000010
        C-LET-00010
        X-C-TX-201801166
        C-201226860A
        C-K9000024
        C-202104117

        Steps:
        - Vytvoření Dokumentu
        - Editace Dokumentu
        - Editace Letu v Dokumentu
        - Vytvoření Části Dokumentu typ Akce
        - Vytvoření Části Dokumentu typ Lokalita
        - Vytvoření Části Dokumentu typ Projekt
        - Vytvoření komponenty
        - Vytvoření nálezu objektu a předmětu
        - Vytvoření Tvaru
        - Přidání souboru
        - Odeslání Dokumentu
        - Editace Části Dokumentu
        - Editace komponenty
        - Editace nálezu
        - Smazání nálezu
        - Smazání komponenty
        - Smazání Části Dokumentu
        - Smazání Části Dokumentu typ projekt
        - Smazání Části Dokumentu typ lokalita
        - Editace Tvaru
        - Smazání Tvaru
        - Upgrade souboru
        - Smazání souboru
        - Editace Neidentifikované Akce
        - Smazání Neidentifikované Akce
        - Smazání Dokumentu
        - Odpojení Akce
        - Odpojení Lokality
        - Odpojení Projektu

        Expected:
        - zápis dat do Fedory
        """
        logger.info("AkceDokumenty.test_141_test_Fedory_dokument_p_001.start")

        # Vytvoření dokumentu
        self.login("archivar")
        self.go_to_form_zapsat()
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, "#id-modal-region-div > #div_id_region .btn")
        self.ElementClick(By.ID, "bs-select-10-1")
        self.ElementClick(By.ID, "submit-btn")
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
        # self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-24 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-0 > .text")
        # self.wait(1)
        self.ElementClick(By.ID, "id_popis")
        self.ElementSendKeys(By.ID, "id_popis", "test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-7-1")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_licence .btn")
        self.ElementClick(By.ID, "bs-select-8-1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/create_dokument")
        ident = self.driver.current_url.split("/")[-1]

        # Úprava detailu
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.ID, "id_popis")
        self.ElementSendKeys(By.ID, "id_popis", "test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_dokument")

        # Úprava detailu letu
        self.createFedoraRecord("C-LET-00001", "archivar")
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_let .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-10-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_let")

        # Vytvoření části dokumentu - akce
        self.createFedoraRecord("C-200810821A", "archivar")
        time = self.getTime()
        self.ElementClick(By.ID, "button-add-cast")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "button-pripojit-akci")
        self.wait(2)
        self.ElementClick(By.ID, "select2-id_arch_z-container")
        self.ElementSendKeys(By.CSS_SELECTOR, ".select2-search__field", "C-200810821A")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/create_dokument_cast_akce")

        # Vytvoření části dokumentu - lokality
        self.createFedoraRecord("C-K9000001", "archivar")
        time = self.getTime()
        self.ElementClick(By.ID, "button-add-cast")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "button-pripojit-lokalitu")
        self.wait(2)
        self.ElementClick(By.ID, "select2-id_arch_z-container")
        self.ElementSendKeys(By.CSS_SELECTOR, ".select2-search__field", "C-K9000001")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/create_dokument_cast_lokalita")

        # Vytvoření části dokumentu - projekty
        self.createFedoraRecord("C-201911202", "archivar")
        time = self.getTime()
        self.ElementClick(By.ID, "button-add-cast")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "pripojit-projekt-btn")
        self.wait(2)
        self.ElementClick(By.ID, "select2-id_projekt-container")
        self.ElementSendKeys(By.CSS_SELECTOR, ".select2-search__field", "C-201911202")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/create_dokument_cast_projekt")

        # Vytvoření komponenty
        time = self.getTime()
        self.ElementClick(By.ID, "button-add-cast")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.LINK_TEXT, _("dokument.templates.dok.detail_cast_dokumentu.pridatKomponentu.label"))
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
        self.check_fedora_change(time, "dokument/tests/resources/test_141/create_komponenta")

        # Vytvoření nálezového objektu + předmětu
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
        self.check_fedora_change(time, "dokument/tests/resources/test_141/create_objekt")

        # Vytvoření tvaru
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}_d-0-tvar .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-26-8 > span:nth-child(2)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editTvarSubmitButton")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/create_tvar")

        # Vytvoření souboru
        time = self.getTime()
        self.ElementClick(By.ID, "NahratSoubory")
        self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/create_soubor")

        # zmena idnet_cely
        time = self.getTime()
        self.ElementClick(By.ID, "dokument-odeslat")
        with freeze_time("2025-07-27 12:00:01", ignore=["core.tests.test_selenium"]):
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        new_ident = self.driver.current_url.split("/")[-1]
        self.check_fedora_change(time, "dokument/tests/resources/test_141/ident_cely")
        self.check_fedora_delete(["record/X-C-DL-000000009"])

        # Úprava části dokumentu
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, ".list-group-item:nth-child(1) strong")
        self.ElementClick(By.ID, "button-edit-cast")
        self.ElementClick(By.CSS_SELECTOR, ".modal-body > #div_id_poznamka #id_poznamka")
        self.ElementSendKeys(By.CSS_SELECTOR, ".modal-body > #div_id_poznamka #id_poznamka", "test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_dokument_cast")

        # Úprava komponenty C-DL-202500001-D004
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, f"#el_li_komponenta_{new_ident.replace('-','_')}_K001 a")
        self.ElementClick(By.ID, f"id_{new_ident}-K001-presna_datace")
        self.driver.find_element(By.ID, f"id_{new_ident}-K001-presna_datace").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_komponenta")

        # Úprava nálezu
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, f"#el_li_komponenta_{new_ident.replace('-','_')}_K001 a")
        self.ElementClick(By.ID, f"id_{new_ident}-K001_o-0-pocet")
        self.driver.find_element(By.ID, f"id_{new_ident}-K001_o-0-pocet").send_keys("10")
        self.ElementClick(By.ID, f"id_{new_ident}-K001_p-0-pocet")
        self.driver.find_element(By.ID, f"id_{new_ident}-K001_p-0-pocet").send_keys("10")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_nalez")

        # Smazání nálezu
        time = self.getTime()
        pk = (
            NalezObjekt.objects.filter(komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely=new_ident)
            .first()
            .pk
        )
        self.ElementClick(By.CSS_SELECTOR, f"#el_li_komponenta_{new_ident.replace('-','_')}_K001 a")
        self.ElementClick(By.ID, f"objekt-smazat-{pk}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_nalez")

        # Smazání komponenty
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, f"#el_li_komponenta_{new_ident.replace('-','_')}_K001 a")
        self.ElementClick(By.ID, "others_komponenta")
        self.ElementClick(By.ID, f"komponenta-smazat-{new_ident}-K001")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_komponenta")

        # Smazání části dokumentu
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, ".list-group-item:nth-child(1) strong")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "smazat-cast-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_dokument_cast")

        # Smazání části dokumentu - projekt
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, ".list-group-item:nth-child(2) strong")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "smazat-cast-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_dokument_cast_projekt")

        # Smazání části dokumentu - lokalita
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, ".list-group-item:nth-child(1) strong")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "smazat-cast-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_dokument_cast_lokalita")

        # Úprava tvaru
        time = self.getTime()
        self.ElementClick(By.ID, f"id_{new_ident}_d-0-poznamka")
        self.driver.find_element(By.ID, f"id_{new_ident}_d-0-poznamka").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editTvarSubmitButton")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_tvar")

        # Smazání tvaru
        time = self.getTime()
        tvar = Tvar.objects.filter(dokument__ident_cely=new_ident).first().pk
        self.ElementClick(By.ID, f"tvar-smazat-{tvar}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_tvar")

        # Úprava souboru
        time = self.getTime()
        file = Soubor.objects.filter(vazba__dokument_souboru__ident_cely=new_ident).first().pk
        self.ElementClick(By.ID, f"file-upgrade-{file}")
        self.upload_file("dokument/tests/resources/test1.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_soubor")

        # Smazání souboru
        time = self.getTime()
        file = Soubor.objects.filter(vazba__dokument_souboru__ident_cely=new_ident).first().pk
        self.ElementClick(By.ID, f"file-smazat-{file}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_soubor")

        # Smazání dokumentu
        time = self.getTime()
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "dokument-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_dokument")

        # Úprava neidentifikované akce
        self.createFedoraRecord("C-TX-197602290", "archivar")
        self.uploadFileToFedora(113981, "projekt/tests/resources/test.pdf", "archivar")
        time = self.getTime()
        self.goToAddress("/id/C-TX-197602290")
        self.ElementClick(By.CSS_SELECTOR, ".list-group-item:nth-child(1) strong")
        self.ElementClick(By.ID, "button-edit-neident")
        self.ElementClick(By.ID, "id_neident_modal-popis")
        self.ElementSendKeys(By.ID, "id_neident_modal-popis", "test")
        self.ElementClick(By.ID, "id_neident_modal-poznamka")
        self.ElementSendKeys(By.ID, "id_neident_modal-poznamka", "test1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_neident_akce")

        # Smazání neidentifikované akce
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, ".list-group-item:nth-child(1) strong")
        self.ElementClick(By.ID, "others_neident")
        self.ElementClick(By.ID, "smazat-neident-akce-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_neident_akce")

        # Smazání dokumentu X-C-TX-201801164
        self.createFedoraRecord("X-C-TX-201801164", "archivar")
        self.createFedoraRecord("C-201125635A", "archivar")
        self.createFedoraRecord("C-202010506", "archivar")
        self.createFedoraRecord("C-K9000010", "archivar")
        self.createFedoraRecord("C-LET-00010", "archivar")
        self.goToAddress("/id/X-C-TX-201801164")
        self.ElementClick(By.ID, "NahratSoubory")
        self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        time = self.getTime()
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "dokument-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_dokument_1")

        # odpojeni akce
        self.createFedoraRecord("X-C-TX-201801166", "archivar")
        self.createFedoraRecord("C-201226860A", "archivar")
        self.createFedoraRecord("C-K9000024", "archivar")
        self.createFedoraRecord("C-202104117", "archivar")
        self.uploadFileToFedora(41065, "projekt/tests/resources/test.pdf", "archivar")
        self.goToAddress("/dokument/detail/X-C-TX-201801166/cast/X-C-TX-201801166-D001")
        time = self.getTime()
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "odpojit-cast-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/odpojeni_akce")

        # odpojeni lokality
        self.goToAddress("/dokument/detail/X-C-TX-201801166/cast/X-C-TX-201801166-D002")
        time = self.getTime()
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "odpojit-cast-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/odpojeni_lokality")

        # odpojeni projektu
        self.goToAddress("/dokument/detail/X-C-TX-201801166/cast/X-C-TX-201801166-D003")
        time = self.getTime()
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "odpojit-cast-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/odpojeni_projektu")

        logger.info("AkceDokumenty.test_141_test_Fedory_dokument_p_001.end")

    def test_142_test_Fedory_LET_p_001(self):
        """
        Test 142 Test Fedory pro LET (pozitivní scénář 1)

        Role:
        Administrator

        TestData:
        M-TX-202000166

        Steps:
        - Vytvoření Letu
        - Editace Letu
        - Připojení Letu v Dokumentu
        - Odpojení Letu v Dokumentu
        - Smazání Letu

        Expected:
        - zápis dat do Fedory
        """
        logger.info("AkceDokumenty.test_142_test_Fedory_LET_p_001.start")
        # Vytvoření letu
        self.login("administrator")
        self.goToAddress("/admin/dokument/let/add/")
        time = self.getTime()
        self.ElementClick(By.ID, "id_ident_cely")
        self.ElementSendKeys(By.ID, "id_ident_cely", "C-LET-00413")
        self.ElementClick(By.ID, "id_uzivatelske_oznaceni")
        self.ElementSendKeys(By.ID, "id_uzivatelske_oznaceni", "test")
        self.ElementClick(By.ID, "id_datum")
        self.ElementSendKeys(By.ID, "id_datum", "08.06.2025 ")
        self.ElementClick(By.ID, "id_pilot")
        self.ElementSendKeys(By.ID, "id_pilot", "Havrlant")
        self.ElementClick(By.CSS_SELECTOR, "#id_pozorovatel > option:nth-child(33)")
        self.ElementClick(By.ID, "id_ucel_letu")
        self.ElementSendKeys(By.ID, "id_ucel_letu", "Vyhlídkový")
        self.ElementClick(By.ID, "id_typ_letounu")
        self.ElementSendKeys(By.ID, "id_typ_letounu", "Blaník")
        self.ElementClick(By.ID, "id_letiste_start")
        self.ElementClick(By.CSS_SELECTOR, "#id_letiste_start > option:nth-child(17)")
        self.ElementClick(By.ID, "id_letiste_cil")
        self.ElementClick(By.CSS_SELECTOR, "#id_letiste_cil > option:nth-child(17)")
        self.ElementClick(By.ID, "id_hodina_zacatek")
        self.ElementSendKeys(By.ID, "id_hodina_zacatek", "10")
        self.ElementClick(By.ID, "id_hodina_konec")
        self.ElementSendKeys(By.ID, "id_hodina_konec", "11")
        self.ElementClick(By.ID, "id_pocasi")
        self.ElementClick(By.CSS_SELECTOR, "#id_pocasi > option:nth-child(6)")
        self.ElementClick(By.ID, "id_dohlednost")
        self.ElementClick(By.CSS_SELECTOR, "#id_dohlednost > option:nth-child(9)")
        self.ElementClick(By.ID, "id_fotoaparat")
        self.ElementSendKeys(By.ID, "id_fotoaparat", "nic")
        self.ElementClick(By.ID, "id_organizace")
        self.ElementClick(By.CSS_SELECTOR, "#id_organizace > option:nth-child(30)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "dokument/tests/resources/test_142/create_let")

        # Úprava letu
        time = self.getTime()
        self.ElementClick(By.LINK_TEXT, "C-LET-00413")
        self.ElementClick(By.ID, "id_fotoaparat")
        self.ElementSendKeys(By.ID, "id_fotoaparat", "nic")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "dokument/tests/resources/test_142/update_let")

        # pripojeni dokument
        self.createFedoraRecord("M-TX-202000166")
        time = self.getTime()
        self.goToAddress("/id/M-TX-202000166")
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_let .btn")
        element_text = self.driver.find_element(By.CSS_SELECTOR, "#bs-select-10-411 > .text").text
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-10-411 > .text")
        self.assertEqual(element_text, "C-LET-00413")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        self.check_fedora_change(time, "dokument/tests/resources/test_142/pripojeni_dokument")

        # odpojeni dokument
        time = self.getTime()
        self.goToAddress("/id/M-TX-202000166")
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_let .btn")
        self.ElementClick(By.ID, "bs-select-10-0")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        self.check_fedora_change(time, "dokument/tests/resources/test_142/odpojeni_dokument")

        # Smazání letu
        time = self.getTime()
        let = Let.objects.filter(ident_cely="C-LET-00413").first().pk
        self.goToAddress(f"/admin/dokument/let/{let}/change/")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, "Odstranit")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "input:nth-child(2)")
        self.check_fedora_change(time, "dokument/tests/resources/test_142/delete_let")

        logger.info("AkceDokumenty.test_142_test_Fedory_LET_p_001.end")

    def test_162_smazání_dokumentu_p_001(self):
        """
        Test 162 Smazání dokumentu (pozitivní scénář 1)

        Smazání záznamu - test zahrne i to, že se smaže i vše, co je na záznam navázané resp. co se má smazat

        Role:
        Archivář

        Preconditions:
        - Uživatel je přihlášen.
        - Dokument je ve stavu D2.

        TestData:
        C-TX-197602290

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře dokument ve stavu D2
        - V panelu pro akce kliknout na  “Další akce” → “Smazat dokument”
        - V dalším dialogovém okně “Smazat dokument” kliknout na “Smazat”

        Expected:
        - Dokument bude smazán z databáze
        """
        logger.info("AkceDokumenty.test_162_smazání_dokumentu_p_001.start")
        self.login("archivar")

        self.assertEqual(Dokument.objects.filter(ident_cely="C-TX-197602290").first().stav, D_STAV_ODESLANY)
        self.createFedoraRecord("C-TX-197602290")
        self.uploadFileToFedora(113981, "projekt/tests/resources/test.pdf")
        self.assertEqual(DokumentCast.objects.filter(dokument__ident_cely="C-TX-197602290").count(), 3)
        self.goToAddress("/dokument/detail/C-TX-197602290/cast/C-TX-197602290-D001")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "smazat-cast-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.goToAddress("/dokument/detail/C-TX-197602290/cast/C-TX-197602290-D002")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "smazat-cast-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.goToAddress("/dokument/detail/C-TX-197602290/cast/C-TX-197602290-D003")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "smazat-cast-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(DokumentCast.objects.filter(dokument__ident_cely="C-TX-197602290").count(), 0)
        self.goToAddress("/dokument/detail/C-TX-197602290")
        self.ElementClick(By.ID, "file-smazat-113981")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "dokument-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(Dokument.objects.filter(ident_cely="C-TX-197602290").count(), 0)
        logger.info("AkceDokumenty.test_162_smazání_dokumentu_p_001.end")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceKnihovna3D(BaseSeleniumTestClass):
    """Implementuje komponentu ``AkceKnihovna3D`` v rámci aplikace."""

    def go_to_form_zapsat(self):
        """
        Naviguje na stránku pro zapsání dokumentu.
        """
        self.goToAddress("/dokument/model/zapsat")

    def zapsat_zaznam(self):
        """Provádí operaci zapsat zaznam.

        :return: Vrací proměnná ``ident``.
        """
        self.go_to_form_zapsat()
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("švejcar")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vzniku")
        self.driver.find_element(By.ID, "id_rok_vzniku").send_keys("2024")
        self.driver.find_element(By.ID, "id_rok_vzniku").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(
            "Archeologický ústav Praha"
        )
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("3")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_licence .btn")
        self.ElementClick(By.ID, "bs-select-4-1")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        ident = self.driver.current_url.split("/")[-1]
        return ident

    def odeslat_zaznam(self, ident_cely):
        """
        Provádí operaci odeslat zaznam.

        :param ident_cely: Parametr ``ident_cely`` se předává do volání ``goToAddress()``.

            :return: Vrací proměnná ``ident``.
        """
        self.goToAddress(f"/dokument/model/detail/{ident_cely}")
        self.ElementClick(By.ID, "buttonEdit")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_format .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-1 > .text")
        self.ElementClick(By.ID, "id_popis")
        self.driver.find_element(By.ID, "id_popis").send_keys("test")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_komponenta-obdobi .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-6-3 > .text")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-7-3 > .text")
        self.ElementClick(By.ID, "id_duveryhodnost")
        self.driver.find_element(By.ID, "id_duveryhodnost").send_keys("100")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        self.ElementClick(By.ID, "buttonUpload")
        self.upload_file("dokument/tests/resources/del.zip", "del.zip", "application/zip")
        self.ElementClick(By.ID, "buttonUploadSubmit")
        self.ElementClick(By.ID, "dokument-odeslat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        ident = self.driver.current_url.split("/")[-1]
        return ident

    def pridani_objektu(self, ident):
        """
        Provádí operaci pridani objektu.

        :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.
        """
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_o-0-druh .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-3 > .text")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_o-0-specifikace .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-4-3 > .text")

        self.ElementClick(By.ID, f"id_{ident}-K001_o-0-pocet")
        self.driver.find_element(By.ID, f"id_{ident}-K001_o-0-pocet").send_keys("1")
        self.ElementClick(By.ID, f"id_{ident}-K001_o-0-poznamka")
        self.driver.find_element(By.ID, f"id_{ident}-K001_o-0-poznamka").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editNalezSubmitButton")

    def pridani_predmetu(self, ident):
        """
        Provádí operaci pridani predmetu.

        :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.
        """
        self.driver.execute_script("$(window).scrollTop(1500 );")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_p-0-druh .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-11-6 > .text")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_p-0-specifikace .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-12-28")

        self.ElementClick(By.ID, f"id_{ident}-K001_p-0-pocet")
        self.driver.find_element(By.ID, f"id_{ident}-K001_p-0-pocet").send_keys("2")
        self.ElementClick(By.ID, f"id_{ident}-K001_p-0-poznamka")
        self.driver.find_element(By.ID, f"id_{ident}-K001_p-0-poznamka").send_keys("test")

    def test_104_zapis_do_knihovny_D3_p_001(self):
        """
        Test 104 Zápis záznamu do knihovny 3D (pozitivní scénář 1)

        Test zápisu nového záznamu do Knihovny 3D. Scénář končí vytvořením nového záznamu v Knihovně 3D.

        Role:
        Archeolog

        Preconditions:
        - Uživatel je přihlášen.
        - Hodnoty pro povinná pole

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře modul “Knihovna 3D”  → Zapsat  → uživatel vyplní povinná pole  → uživatel klikne na tlačítko “Zapsat”

        Expected:
        - Vznikne nový záznam v Knihovně 3D - v databázi bude o jeden záznam více.
        """
        logger.info("AkceKnihovna3D.test_104_zapis_do_knihovny_D3_p_001.start")
        self.login("archeolog")
        count_old = Dokument.objects.count()
        self.zapsat_zaznam()
        count_new = Dokument.objects.count()

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_104_zapis_do_knihovny_D3_p_001.end")

    def test_105_odeslani_zaznamu_knihovny_D3_p_001(self):
        """
        Test 105 Odeslání záznamu do knihovny 3D (pozitivní scénář 1)

        Test odeslání záznamu do Knihovny 3D. Scénář končí posunem záznamu ze stavu D1 do stavu D2.

        Role:
        Archeolog

        Preconditions:
        - Uživatel je přihlášen.
        - Hodnoty pro povinná pole
        - Soubor s náhledem 3D modelu

        TestData:
        X-C-3D-000000005
        del.zip

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000005“ → Vybrat → otevřít záznam „X-C-3D-000000005“
        - Uživatel vyplní povinná pole
        - V sekci “Náhledy 3D modelu/soubory s texturou” klikne uživatel na možnost “Nahrát soubory” → vloží soubor “del.zip” a klikne na “Dokončit”
        - V panelu pro akce klikne uživatel na tlačítko “Odeslat” → v dialogovém okně “Odeslat dokument” klikne uživatel na tlačítko “Odeslat”

        Expected:
        - Záznam v Knihovně 3D se posune ze stavu D1 do stavu D2.
        """
        logger.info("AkceKnihovna3D.test_105_odeslani_zaznamu_knihovny_D3_p_001.start")
        self.login("archeolog")
        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-3D-000000005").first().stav, D_STAV_ZAPSANY)
        id = Dokument.objects.filter(ident_cely="X-C-3D-000000005").first().id
        self.odeslat_zaznam("X-C-3D-000000005")

        self.assertEqual(Dokument.objects.filter(id=id).first().stav, D_STAV_ODESLANY)
        logger.info("AkceKnihovna3D.test_105_odeslani_zaznamu_knihovny_D3_p_001.end")

    def test_106_pridani_objektu_knihovny_D3_p_001(self):
        """
        Test 106 Přidání objektu k záznamu v Knihovně 3D (pozitivní scénář 1)

        Test přidání objektu k záznamu v Knihovně 3D. Scénář končí přidání objektu k záznamu v Knihovně 3D - v databázi je o jeden záznam více.

        Role:
        Archeolog

        Preconditions:
        - Uživatel je přihlášen
        - Záznam v Knihovně 3D ve stavu D1.

        TestData:
        X-C-3D-000000005

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000005“ → Vybrat → otevřít záznam „X-C-3D-000000005“
        - V části “Specifikace obsahu” v části “Objekty” vybere uživatel v poli “Druh” hodnotu “hradba” a klikne na “Uložit změny”

        Expected:
        - U záznamu v Knihovně 3D bude vytvořen nový objekt. V databázi bude o jeden objekt více.
        """
        logger.info("AkceKnihovna3D.test_106_pridani_objektu_knihovny_D3_p_001.start")
        self.login("archeolog")
        count_old = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000005"
        ).count()
        self.goToAddress("/dokument/model/detail/X-C-3D-000000005")
        self.pridani_objektu("X-C-3D-000000005")

        count_new = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000005"
        ).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_106_pridani_objektu_knihovny_D3_p_001.end")

    def test_107_pridani_predmetu_knihovny_D3_p_001(self):
        """
        Test 107 Přidání předmětu k záznamu v Knihovně 3D (pozitivní scénář 1)

        Test přidání objektu k záznamu v Knihovně 3D. Scénář končí přidáním předmětu k záznamu v Knihovně 3D - v databázi je o jeden záznam více.

        Role:
        Archeolog

        Preconditions:
        - Uživatel je přihlášen
        - Záznam v Knihovně 3D ve stavu D1.

        TestData:
        X-C-3D-000000005

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000005“ → Vybrat → otevřít záznam „X-C-3D-000000005“
        - V části “Specifikace obsahu” v části “Předměty” vybere uživatel v poli “Druh” hodnotu “dýka”, v poli “Specifikace” hodnotu “kámen štípaný” a klikne na “Uložit změny”

        Expected:
        - U záznamu v Knihovně 3D bude vytvořen nový předmět. V databázi bude o jeden předmět více.
        """
        logger.info("AkceKnihovna3D.test_107_pridani_predmetu_knihovny_D3_p_001.start")
        self.login("archeolog")

        count_old = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000005"
        ).count()
        self.goToAddress("/dokument/model/detail/X-C-3D-000000005")
        self.pridani_predmetu("X-C-3D-000000005")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editNalezSubmitButton")
        count_new = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000005"
        ).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_107_pridani_predmetu_knihovny_D3_p_001.end")

    def test_108_pridani_souradnic_knihovny_D3_p_001(self):
        """
        Test 108 Přidání prostorového vymezení k záznamu v Knihovně 3D (pozitivní scénář 1)

        Test přidání prostorového vymezení k záznamu v Knihovně 3D.

        Role:
        Archeolog

        Preconditions:
        - Uživatel je přihlášen
        - Záznam v Knihovně 3D ve stavu D1.

        TestData:
        X-C-3D-000000005

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000005“ → Vybrat → otevřít záznam „X-C-3D-000000005“
        - V části “Detail” klikne uživatel na “upravit”  → v mapě se přiblíží na místo XXX a klikne do mapy (jak vyřešit v testu?) → kliknout na “Uložit změny”

        Expected:
        - U záznamu v Knihovně 3D bude vytvořeno nové prostorové vymezení - bude vytvořena vazba mezi záznamem a prostorovým vymezením.
        """
        logger.info("AkceKnihovna3D.test_108_pridani_souradnic_knihovny_D3_p_001.start")
        self.login("archeolog")

        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-3D-000000005").first().extra_data.geom, None)
        self.goToAddress("/dokument/model/detail/X-C-3D-000000005")

        self.ElementClick(By.ID, "buttonEdit")
        self.clickAt(self.driver.find_element(By.ID, "projectMap"), 20, 20)
        self.wait(0.2)
        self.clickAt(self.driver.find_element(By.ID, "projectMap"), 20, 20)
        self.wait(0.2)
        self.clickAt(self.driver.find_element(By.ID, "projectMap"), 20, 20)
        self.wait(0.2)
        self.clickAt(self.driver.find_element(By.ID, "projectMap"), 20, 20)
        self.wait(0.2)
        self.clickAt(self.driver.find_element(By.ID, "projectMap"), 20, 20)
        self.wait(0.2)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")

        self.assertNotEqual(Dokument.objects.filter(ident_cely="X-C-3D-000000005").first().extra_data.geom, None)
        logger.info("AkceKnihovna3D.test_108_pridani_souradnic_knihovny_D3_p_001.end")

    def test_109_pridani_souboru_zaznamu_knihovny_D3_p_001(self):
        """
        Test 109 Přidání souboru k záznamu v Knihovně 3D (pozitivní scénář 1)

        Test přidání souboru k záznamu v Knihovně 3D.

        Role:
        Archeolog

        Preconditions:
        - Uživatel je přihlášen
        - Záznam v Knihovně 3D ve stavu D1, který nemá připojený soubor.

        TestData:
        del.zip
        X-C-3D-000000005

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000005“ → Vybrat → otevřít záznam „X-C-3D-000000005“
        - V části “Náhledy 3D modelu/soubory s texturou” klikne uživatel na “nahrát soubory” → v dialogové obrazovce vybere uživatel soubor del.zip → kliknout na “Dokončit”

        Expected:
        - U záznamu v Knihovně 3D bude připojen nový soubor.
        """
        logger.info("AkceKnihovna3D.test_109_pridani_souboru_zaznamu_knihovny_D3_p_001.start")
        self.login("archeolog")
        count_old = Soubor.objects.filter(vazba__dokument_souboru__ident_cely="X-C-3D-000000005").count()
        self.goToAddress("/dokument/model/detail/X-C-3D-000000005")
        self.ElementClick(By.ID, "buttonUpload")
        self.upload_file("dokument/tests/resources/del.zip", "del.zip", "application/zip")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        count_new = Soubor.objects.filter(vazba__dokument_souboru__ident_cely="X-C-3D-000000005").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_109_pridani_souboru_zaznamu_knihovny_D3_p_001.end")

    def test_110_archivace_zaznamu_knihovny_D3_p_001(self):
        """
        Test 110 Archivace záznamu v Knihovně 3D (pozitivní scénář 1)

        Test archivace záznamu v Knihovně 3D. Test končí posunem záznamu ze stavu D2 do D3.

        Role:
        Archivář

        Preconditions:
        - Uživatel je přihlášen
        - Záznam v Knihovně 3D ve stavu D2, který má vyplněny všechny náležitosti.

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „XXX“ → Vybrat → otevřít záznam „XXX“
        - V panelu pro akce klikne uživatel na tlačítko “Archivovat” → v dialogovém okně “Archivovat dokument” klikne uživatel na tlačítko “Archivovat”

        Expected:
        - Záznam v Knihovně 3D se posune ze stavu D2 do stavu D3.
        """
        logger.info("AkceKnihovna3D.test_110_archivace_zaznamu_knihovny_D3_p_001.start")

        self.login("archivar")
        self.createFedoraRecord("C-3D-202600001")
        self.uploadFileToFedora(646257, "dokument/tests/resources/del.zip")
        self.assertEqual(Dokument.objects.filter(ident_cely="C-3D-202600001").first().stav, D_STAV_ODESLANY)

        self.goToAddress("/dokument/model/detail/C-3D-202600001")
        self.ElementClick(By.ID, "dokument-archivovat")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_confirm > label")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(Dokument.objects.filter(ident_cely="C-3D-202600001").first().stav, D_STAV_ARCHIVOVANY)
        logger.info("AkceKnihovna3D.test_110_archivace_zaznamu_knihovny_D3_p_001.end")

    def test_111_zapis_do_knihovny_D3_p_002(self):
        """
        Test 111 Zápis záznamu do knihovny 3D (pozitivní scénář 2)

        Test zápisu nového záznamu do Knihovny 3D. Scénář končí vytvořením nového záznamu v Knihovně 3D.

        Role:
        Badatel

        Preconditions:
        - Uživatel je přihlášen.
        - Hodnoty pro povinná pole

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře modul “Knihovna 3D”  → Zapsat  → uživatel vyplní povinná pole  → uživatel klikne na tlačítko “Zapsat”

        Expected:
        - Vznikne nový záznam v Knihovně 3D - v databázi bude o jeden záznam více.
        """
        logger.info("AkceKnihovna3D.test_111_zapis_do_knihovny_D3_p_002.start")
        self.login("badatel")
        count_old = Dokument.objects.count()
        self.zapsat_zaznam()
        count_new = Dokument.objects.count()

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_111_zapis_do_knihovny_D3_p_002.end")

    def test_112_odeslani_zaznamu_knihovny_D3_p_002(self):
        """
        Test 112 Odeslání záznamu do knihovny 3D (pozitivní scénář 2)

        Test odeslání záznamu do Knihovny 3D. Scénář končí posunem záznamu ze stavu D1 do stavu D2.

        Role:
        Badatel

        Preconditions:
        - Uživatel je přihlášen.
        - Hodnoty pro povinná pole
        - Soubor s náhledem 3D modelu

        TestData:
        del.zip
        X-C-3D-000000006

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000006“ → Vybrat → otevřít záznam „X-C-3D-000000006“
        - Uživatel vyplní povinná pole
        - V sekci “Náhledy 3D modelu/soubory s texturou” klikne uživatel na možnost “Nahrát soubory” → vloží soubor “del.zip” a klikne na “Dokončit”
        - V panelu pro akce klikne uživatel na tlačítko “Odeslat” → v dialogovém okně “Odeslat dokument” klikne uživatel na tlačítko “Odeslat”

        Expected:
        - Záznam v Knihovně 3D se posune ze stavu D1 do stavu D2.
        """
        logger.info("AkceKnihovna3D.test_112_odeslani_zaznamu_knihovny_D3_p_002.start")
        self.login("badatel")
        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-3D-000000006").first().stav, D_STAV_ZAPSANY)
        id = Dokument.objects.filter(ident_cely="X-C-3D-000000006").first().id
        self.odeslat_zaznam("X-C-3D-000000006")

        self.assertEqual(Dokument.objects.filter(id=id).first().stav, D_STAV_ODESLANY)
        logger.info("AkceKnihovna3D.test_112_odeslani_zaznamu_knihovny_D3_p_002.end")

    def test_113_pridani_objektu_knihovny_D3_p_002(self):
        """
        Test 113 Přidání objektu k záznamu v Knihovně 3D (pozitivní scénář 2)

        Test přidání objektu k záznamu v Knihovně 3D. Scénář končí přidání objektu k záznamu v Knihovně 3D - v databázi je o jeden záznam více.

        Role:
        Badatel

        Preconditions:
        - Uživatel je přihlášen
        - Záznam v Knihovně 3D ve stavu D1.

        TestData:
        X-C-3D-000000006

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000006“ → Vybrat → otevřít záznam „X-C-3D-000000006“
        - V části “Specifikace obsahu” v části “Objekty” vybere uživatel v poli “Druh” hodnotu “kašna” a klikne na “Uložit změny”

        Expected:
        - U záznamu v Knihovně 3D bude vytvořen nový objekt. V databázi bude o jeden objekt více.
        """
        logger.info("AkceKnihovna3D.test_113_pridani_objektu_knihovny_D3_p_002.start")
        self.login("badatel")

        count_old = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000006"
        ).count()
        self.goToAddress("/dokument/model/detail/X-C-3D-000000006")
        self.pridani_objektu("X-C-3D-000000006")

        count_new = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000006"
        ).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_113_pridani_objektu_knihovny_D3_p_002.end")

    def test_114_pridani_predmetu_knihovny_D3_p_002(self):
        """
        Test 114 Přidání předmětu k záznamu v Knihovně 3D (pozitivní scénář 2)

        Test přidání objektu k záznamu v Knihovně 3D. Scénář končí přidáním předmětu k záznamu v Knihovně 3D - v databázi je o jeden záznam více.

        Role:
        Badatel

        Preconditions:
        - Uživatel je přihlášen
        - Záznam v Knihovně 3D ve stavu D1.

        TestData:
        X-C-3D-000000006

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000006“ → Vybrat → otevřít záznam „X-C-3D-000000006“
        - V části “Specifikace obsahu” v části “Předměty” vybere uživatel v poli “Druh” hodnotu “zub”, v poli “Specifikace” hodnotu “zub lidský” a klikne na “Uložit změny”

        Expected:
        - U záznamu v Knihovně 3D bude vytvořen nový předmět. V databázi bude o jeden předmět více.
        """
        logger.info("AkceKnihovna3D.test_114_pridani_predmetu_knihovny_D3_p_002.start")
        self.login("badatel")

        count_old = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000006"
        ).count()
        self.goToAddress("/dokument/model/detail/X-C-3D-000000006")
        self.pridani_predmetu("X-C-3D-000000006")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editNalezSubmitButton")
        count_new = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000006"
        ).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_114_pridani_predmetu_knihovny_D3_p_002.end")

    def test_115_pridani_souradnic_knihovny_D3_p_002(self):
        """
        Test 115 Přidání prostorového vymezení k záznamu v Knihovně 3D (pozitivní scénář 2)

        Test přidání prostorového vymezení k záznamu v Knihovně 3D.

        Role:
        Badatel

        Preconditions:
        - Uživatel je přihlášen
        - Záznam v Knihovně 3D ve stavu D1.

        TestData:
        X-C-3D-000000006

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000006“ → Vybrat → otevřít záznam „X-C-3D-000000006“
        - V části “Detail” klikne uživatel na “upravit”  → v mapě se přiblíží na místo XXX a klikne do mapy → kliknout na “Uložit změny”

        Expected:
        - U záznamu v Knihovně 3D bude vytvořeno nové prostorové vymezení - bude vytvořena vazba mezi záznamem a prostorovým vymezením.
        """
        logger.info("AkceKnihovna3D.test_115_pridani_souradnic_knihovny_D3_p_002.start")
        self.login("badatel")

        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-3D-000000006").first().extra_data.geom, None)
        self.goToAddress("/dokument/model/detail/X-C-3D-000000006")

        self.ElementClick(By.ID, "buttonEdit")
        self.clickAt(self.driver.find_element(By.ID, "projectMap"), 20, 20)
        self.wait(0.2)
        self.clickAt(self.driver.find_element(By.ID, "projectMap"), 20, 20)
        self.wait(0.2)
        self.clickAt(self.driver.find_element(By.ID, "projectMap"), 20, 20)
        self.wait(0.2)
        self.clickAt(self.driver.find_element(By.ID, "projectMap"), 20, 20)
        self.wait(0.2)
        self.clickAt(self.driver.find_element(By.ID, "projectMap"), 20, 20)
        self.wait(0.2)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        self.assertNotEqual(Dokument.objects.filter(ident_cely="X-C-3D-000000006").first().extra_data.geom, None)
        logger.info("AkceKnihovna3D.test_115_pridani_souradnic_knihovny_D3_p_002.end")

    def test_116_pridani_souboru_zaznamu_knihovny_D3_p_002(self):
        """
        Test 116 Přidání souboru k záznamu v Knihovně 3D (pozitivní scénář 2)

        Test přidání souboru k záznamu v Knihovně 3D.

        Role:
        Badatel

        Preconditions:
        - Uživatel je přihlášen
        - Záznam v Knihovně 3D ve stavu D1, který nemá připojený soubor.

        TestData:
        del.zip
        X-C-3D-000000006

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře modul “Knihovna 3D”  → Vybrat → Filtr → ID obsahuje „X-C-3D-000000006“ → Vybrat → otevřít záznam „X-C-3D-000000006“
        - V části “Náhledy 3D modelu/soubory s texturou” klikne uživatel na “nahrát soubory” → v dialogové obrazovce vybere uživatel soubor del.zip  → kliknout na “Dokončit”

        Expected:
        - U záznamu v Knihovně 3D bude připojen nový soubor.
        """
        logger.info("AkceKnihovna3D.test_116_pridani_souboru_zaznamu_knihovny_D3_p_002.start")
        self.login("badatel")
        count_old = Soubor.objects.filter(vazba__dokument_souboru__ident_cely="X-C-3D-000000006").count()
        self.goToAddress("/dokument/model/detail/X-C-3D-000000006")

        self.ElementClick(By.ID, "buttonUpload")
        self.upload_file("dokument/tests/resources/del.zip", "del.zip", "application/zip")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        count_new = Soubor.objects.filter(vazba__dokument_souboru__ident_cely="X-C-3D-000000006").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_116_pridani_souboru_zaznamu_knihovny_D3_p_002.end")

    def test_144_test_Fedory_3D_p_001(self):
        """
        Test 144 Test Fedory pro 3D dokumenty (pozitivní scénář 1)

        Role:
        Archivář

        Steps:
        - Vytvoření 3D dokumentu
        - Editace 3D dokumentu
        - Editace komponenty
        - Vytvoření nálezu
        - Editace nálezu
        - Nahrání souboru
        - Upgrade souboru
        - Odeslání 3D dokumentu
        - Smazání nálezu
        - Smazání souboru
        - Smazání 3D dokumentu

        Expected:
        -  zápis dat do Fedory
        """
        logger.info("AkceKnihovna3D.test_144_test_Fedory_3D_p_001.start")

        self.login("archivar")
        # Vytvoření 3D dokumentu
        time = self.getTime()
        ident = self.zapsat_zaznam()
        self.check_fedora_change(time, "dokument/tests/resources/test_144/create_3D_dokument")

        # Úprava detailu
        time = self.getTime()
        self.ElementClick(By.ID, "buttonEdit")
        self.ElementClick(By.ID, "id_popis")
        self.ElementSendKeys(By.ID, "id_popis", "test1")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_format .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/update_3D_dokument")

        # Úprava komponenty
        time = self.getTime()
        self.ElementClick(By.ID, "buttonEdit")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_komponenta-obdobi .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-6-3 > .text")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-7-3 > .text")
        self.ElementClick(By.ID, "id_duveryhodnost")
        self.ElementSendKeys(By.ID, "id_duveryhodnost", "100")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/update_komponenta")

        # Vytvoření nálezu
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_o-0-druh .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-3 > .text")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_o-0-specifikace .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-4-3 > .text")
        self.ElementClick(By.ID, f"id_{ident}-K001_o-0-pocet")
        self.driver.find_element(By.ID, f"id_{ident}-K001_o-0-pocet").send_keys("1")
        self.ElementClick(By.ID, f"id_{ident}-K001_o-0-poznamka")
        self.driver.find_element(By.ID, f"id_{ident}-K001_o-0-poznamka").send_keys("test")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_p-0-druh .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-11-6 > .text")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_p-0-specifikace .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-12-28")
        self.ElementClick(By.ID, f"id_{ident}-K001_p-0-pocet")
        self.driver.find_element(By.ID, f"id_{ident}-K001_p-0-pocet").send_keys("2")
        self.ElementClick(By.ID, f"id_{ident}-K001_p-0-poznamka")
        self.driver.find_element(By.ID, f"id_{ident}-K001_p-0-poznamka").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editNalezSubmitButton")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/create_nalez")

        # Úprava nálezu
        time = self.getTime()
        self.goToAddress(f"/id/{ident}")
        self.ElementClick(By.ID, f"id_{ident}-K001_o-0-pocet")
        self.driver.find_element(By.ID, f"id_{ident}-K001_o-0-pocet").send_keys("1")
        self.ElementClick(By.ID, f"id_{ident}-K001_p-0-pocet")
        self.driver.find_element(By.ID, f"id_{ident}-K001_p-0-pocet").send_keys("2")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editNalezSubmitButton")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/update_nalez")

        # Vytvoření souboru
        time = self.getTime()
        self.goToAddress(f"/id/{ident}")
        self.ElementClick(By.ID, "buttonUpload")
        self.upload_file("dokument/tests/resources/del.zip", "del.zip", "application/zip")
        self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/create_soubor")

        # Úprava souboru
        time = self.getTime()
        file = Soubor.objects.filter(vazba__dokument_souboru__ident_cely=ident).first().pk
        self.ElementClick(By.ID, f"file-upgrade-{file}")
        self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/update_soubor")

        # ident_cely
        time = self.getTime()
        self.ElementClick(By.ID, "dokument-odeslat")
        with freeze_time("2025-07-27 12:00:01", ignore=["core.tests.test_selenium"]):
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        new_ident = self.driver.current_url.split("/")[-1]
        self.check_fedora_change(time, "dokument/tests/resources/test_144/ident_cely")
        self.check_fedora_delete(["record/X-C-3D-000000009"])

        # Smazání nálezu
        time = self.getTime()
        pk = (
            NalezObjekt.objects.filter(komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely=new_ident)
            .first()
            .pk
        )
        self.ElementClick(By.ID, f"objekt-smazat-{pk}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/delete_nalez")

        # Smazání souboru
        time = self.getTime()
        file = Soubor.objects.filter(vazba__dokument_souboru__ident_cely=new_ident).first().pk
        self.ElementClick(By.ID, f"file-smazat-{file}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/delete_soubor")

        # Smazání 3D dokumentu
        time = self.getTime()
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "dokument-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/delete_3D_dokument")

        logger.info("AkceKnihovna3D.test_144_test_Fedory_3D_p_001.end")

    def test_160_smazani_zaznamu_knihovny_D3_p_001(self):
        """
        Test 160 Smazání záznamu v Knihovně 3D (pozitivní scénář 1)

        Smazání záznamu - test zahrne i to, že se smaže i vše, co je na záznam navázané resp. co se má smazat

        Role:
        Archivář

        Preconditions:
        - Uživatel je přihlášen.
        - Záznam v Knihovně 3D ve stavu D2,

        TestData:

        C-3D-202600001

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře modul “Knihovna 3D”  → vybere záznam „C-3D-202600001“
        - Smaže připojený soubor
        - V panelu pro akce kliknout na  “Další akce” → “Smazat dokument”
        - V dalším dialogovém okně “Smazat dokument” kliknout na “Smazat”

        Expected:
        - Záznam v Knihovně 3D v databázi bude smazán.
        """
        logger.info("AkceKnihovna3D.test_160_smazani_zaznamu_knihovny_D3_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-3D-202600001")
        self.uploadFileToFedora(646257, "dokument/tests/resources/del.zip")
        self.assertEqual(Dokument.objects.filter(ident_cely="C-3D-202600001").first().stav, D_STAV_ODESLANY)
        self.goToAddress("/dokument/model/detail/C-3D-202600001")
        self.ElementClick(By.ID, "file-smazat-646257")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "dokument-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(Dokument.objects.filter(ident_cely="C-3D-202600001").count(), 0)
        logger.info("AkceKnihovna3D.test_160_smazani_zaznamu_knihovny_D3_p_001.end")
