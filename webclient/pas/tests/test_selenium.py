import logging
import unittest

from core.constants import SN_ARCHIVOVANY, SN_ODESLANY, SN_POTVRZENY, SN_ZAPSANY
from core.models import Soubor

# from core.tests.runner import EXISTING_PROJECT_IDENT_ZACHRANNY, EXISTING_PROJECT_IDENT_STATUS
from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from django.conf import settings
from pas.models import SamostatnyNalez
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceSamostatneNalezy(BaseSeleniumTestClass):
    """Implementuje komponentu ``AkceSamostatneNalezy`` v rámci aplikace."""

    def go_to_form(self):
        """Provádí operaci go to form."""
        self.goToAddress("/pas/zapsat")

    def create_PAS(self):
        """Vytvoří PAS. v aplikaci.

        :return: Vrací vybranou hodnotu z kolekce.
        """
        self.go_to_form()
        self.ElementClick(By.CSS_SELECTOR, "#div_id_projekt .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("M-202105907")
        self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "select2-id_nalezce-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Omelka, Zdeněk")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_datum_nalezu").send_keys("18.10.2023")

        self.driver.find_element(By.ID, "id_hloubka").send_keys("20")
        self.ElementClick(By.ID, "visible_ss_combo")
        self.ElementClick(By.CSS_SELECTOR, "#visible_ss_combo > option:nth-child(2)")
        self.ElementClick(By.ID, "projectMap")
        self.wait(0.5)
        self.clickAtMapCoord(16.7494989, 49.2941092)
        self.wait(0.5)
        self.ElementClick(By.ID, "div_id_lokalizace")
        self.ElementClick(By.ID, "id_lokalizace")
        self.ElementSendKeys(By.ID, "id_lokalizace", "test")
        self.ElementSendKeys(By.CSS_SELECTOR, "#div_id_obdobi  button", "kultura púchovská")
        self.ElementSendKeys(By.CSS_SELECTOR, "#div_id_obdobi  div.bs-searchbox > input", Keys.ENTER)

        self.ElementSendKeys(By.CSS_SELECTOR, "#div_id_druh_nalezu  button", "lahev")
        self.ElementSendKeys(By.CSS_SELECTOR, "#div_id_druh_nalezu  div.bs-searchbox > input", Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_specifikace button")
        self.ElementSendKeys(By.CSS_SELECTOR, "#div_id_specifikace input", "jantar")
        self.ElementSendKeys(By.CSS_SELECTOR, "#div_id_specifikace  div.bs-searchbox > input", Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        return self.driver.current_url.split("/")[-1]

    def test_025_zapsani_samostatneho_nalezu_p_001(self):
        """
        Test 025 Zapsání samostatného nálezu (pozitivní scénář 1)

        Test zapsání samostatného nálezu na stránce /pas/zapsat. Končí zapsáním samostatného nálezu do databáze.

        Role:
        Badatel

        Preconditions:
        - Uživatel je přihlášen.
        - Projekt typu “průzkum” je ve stavu P3

        Steps:
        - Uživatel se přihlásí
        - Uživatel klikne na menu Samostatné nálezy -> Zapsat nález
        - Uživatel vyplní data do formuláře a kliknutím na mapu vybere lokalizaci nálezu
        - Uživatel klikne na tlačítko Uložit

        Expected:
        -  Po kliknutí na tlačítko Uložit je v databázi o jeden samostatný nález více.
        """
        logger.info("AkceSamostatneNalezy.test_025_zapsani_samostatneho_nalezu_p_001.start")
        self.login("badatel1")
        SN_count_old = SamostatnyNalez.objects.count()
        self.create_PAS()
        SN_count_new = SamostatnyNalez.objects.count()
        self.assertEqual(SN_count_old + 1, SN_count_new)
        logger.info("AkceSamostatneNalezy.test_025_zapsani_samostatneho_nalezu_p_001.end")

    def test_026_zapsani_samostatneho_nalezu_n_001(self):
        """
        Test 026 Zapsání samostatného nálezu (negativní scénář 1)

        Test zapsání samostatného nálezu na stránce /pas/zapsat. Test simuluje zadání nevalidních dat a měl by končit nezapsáním projektu do databáze.

        Role:
        Badatel

        Preconditions:
        - Uživatel je přihlášen.
        - Projekt typu “průzkum” je ve stavu P3

        Steps:
        - Uživatel se přihlásí
        - Uživatel klikne na menu Samostatné nálezy -> Zapsat nález
        - Uživatel vyplní data do formuláře a kliknutím na mapu vybere lokalizaci nálezu
        - Uživatel klikne na tlačítko Uložit

        Expected:
        - Neúspěšné zapsání projektu, pocet projektů v databázi se nezměnil.
        - Zobrazena chyba “Chybí Projekt”
        """
        logger.info("AkceSamostatneNalezy.test_026_zapsani_samostatneho_nalezu_n_001.start")
        self.login("badatel1")
        self.go_to_form()
        SN_count_old = SamostatnyNalez.objects.count()

        # self.ElementClick(By.CSS_SELECTOR, "#div_id_projekt .filter-option-inner-inner")
        # self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("M-202004181")
        # self.wait(self.wait_interval)

        # self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.ID, "select2-id_nalezce-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Omelka, Zdeněk")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_datum_nalezu").send_keys("18.10.2023")

        self.driver.find_element(By.ID, "id_hloubka").send_keys("20")
        self.ElementClick(By.ID, "visible_ss_combo")
        self.ElementClick(By.CSS_SELECTOR, "#visible_ss_combo > option:nth-child(2)")
        self.ElementClick(By.ID, "projectMap")
        self.ElementClick(By.ID, "projectMap")
        self.ElementClick(By.CSS_SELECTOR, ".leaflet-control-measure > img")
        self.ElementClick(By.ID, "visible_x1")
        self.driver.find_element(By.ID, "visible_x1").send_keys("16,7494989")
        self.ElementClick(By.ID, "visible_x2")
        self.driver.find_element(By.ID, "visible_x2").send_keys("49,2941092")
        self.ElementSendKeys(By.ID, "id_lokalizace", "test")
        self.ElementSendKeys(By.CSS_SELECTOR, "#div_id_obdobi  button", "kultura púchovská")
        self.ElementSendKeys(By.CSS_SELECTOR, "#div_id_obdobi  div.bs-searchbox > input", Keys.ENTER)

        self.ElementSendKeys(By.CSS_SELECTOR, "#div_id_druh_nalezu  button", "lahev")
        self.ElementSendKeys(By.CSS_SELECTOR, "#div_id_druh_nalezu  div.bs-searchbox > input", Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_specifikace button")
        self.ElementSendKeys(By.CSS_SELECTOR, "#div_id_specifikace input", "jantar")
        self.ElementSendKeys(By.CSS_SELECTOR, "#div_id_specifikace  div.bs-searchbox > input", Keys.ENTER)
        with WaitForPageLoad(self.driver, 5):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        SN_count_new = SamostatnyNalez.objects.count()
        self.assertEqual(SN_count_old, SN_count_new)
        logger.info("AkceSamostatneNalezy.test_026_zapsani_samostatneho_nalezu_n_001.end")

    def test_028_odeslani_samostatneho_nalezu_p_001(self):
        """
        Test 028 Odeslání samostatného nálezu (pozitivní scénář 1)

        Test odeslání samostatného nálezu ve stavu SN1 na stránce /pas/detail. Měl by končit odesláním samostatného nálezu a změnou jeho stavu na SN2.

        Role:
        Badatel

        Preconditions:
        - Uživatel je přihlášen.
        - Samostatný nález je ve stavu SN1

        TestData:
        test_foto_1.jpg

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře samostatný nález ve stavu SN1
        - Uživatel nahraje k nálezu fotografii
        - Uživatel klikne na tlačítko Odeslat a volbu potvrdí

        Expected:
        -  Odeslání samostatného nálezu a změna jeho stavu na SN2.
        """
        logger.info("AkceSamostatneNalezy.test_028_odeslani_samostatneho_nalezu_p_001.start")
        self.login("badatel1")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="M-202105907-N00091").first().stav, SN_ZAPSANY)

        self.goToAddress("/pas/detail/M-202105907-N00091")
        self.ElementClick(By.CSS_SELECTOR, ".app-entity-dokument > .material-icons")
        self.upload_file("pas/tests/resources/test_foto_1.jpg", "test_foto_1.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")

        self.ElementClick(By.CSS_SELECTOR, "#pas-odeslat > .app-controls-button-text")
        self.wait(1)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="M-202105907-N00091").first().stav, SN_ODESLANY)
        logger.info("AkceSamostatneNalezy.test_028_odeslani_samostatneho_nalezu_p_001.end")

    def test_029_odeslani_samostatneho_nalezu_n_001(self):
        """
        Test 029 Odeslání samostatného nálezu (negativní scénář 1)

        Test odeslání samostatného nálezu ve stavu SN1 na stránce /pas/detail. Test simuluje zadání nevalidních dat a měl by končit neodesláním samostatného nálezu a jeho ponecháním ve stavu SN1.

        Role:
        Badatel

        Preconditions:
        - Uživatel je přihlášen.
        - Samostatný nález je ve stavu SN1

        TestData:
        M-202105907-N00091

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře samostatný nález ve stavu SN1 (číslo SN)
        - Vybrat → Filtr → ID obsahuje „číslo SN“ → Vybrat → otevřít SN
        - Uživatel klikne na tlačítko Odeslat

        Expected:
        -  Neodeslání samostatného nálezu a jeho ponechání ve stavu SN1.
        """
        logger.info("AkceSamostatneNalezy.test_029_odeslani_samostatneho_nalezu_n_001.start")
        self.login("badatel1")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="M-202105907-N00091").first().stav, SN_ZAPSANY)

        self.goToAddress("/pas/detail/M-202105907-N00091")
        # self.ElementClick(By.CSS_SELECTOR, ".app-entity-dokument > .material-icons")

        # with open("pas/tests/resources/test_foto_1.jpg", "rb") as image_file:
        #    encoded_string = base64.b64encode(image_file.read()).decode()

        # addFileToDropzone("#my-awesome-dropzone",'test_foto_1.jpg',encoded_string)
        # wait = WebDriverWait(self.driver, 10, poll_frequency=1, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
        # element = wait.until(EC.element_to_be_clickable((By.LINK_TEXT,  _("core.templates.core.upload_file.dz.removeFile"))))

        # self.ElementClick(By.LINK_TEXT, _("core.templates.upload_file.submitButton.text"))
        try:
            self.ElementClick(By.CSS_SELECTOR, "#pas-odeslat > .app-controls-button-text")
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "submit-btn")

        except Exception:
            pass

        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="M-202105907-N00091").first().stav, SN_ZAPSANY)
        logger.info("AkceSamostatneNalezy.test_029_odeslani_samostatneho_nalezu_n_001.end")

    def test_030_potvrzeni_samostatneho_nalezu_p_001(self):
        """
        Test 030 Potvrzení samostatného nálezu (pozitivní scénář 1)

        Test odeslání samostatného nálezu ve stavu SN2 na stránce /pas/detail. Měl by končit potvrzením samostatného nálezu a změnou jeho stavu na SN3.

        Role:
        Archeolog

        Preconditions:
        - Uživatel je přihlášen.
        - Samostatný nález je ve stavu SN2

        TestData:
        C-202211308-N00213

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře samostatný nález ve stavu SN2 (číslo SN) → Vybrat → Filtr → ID obsahuje „číslo SN“ → Vybrat → otevřít SN
        - Uživatel vyplní testovací data do formuláře
        - Uživatel klikne na tlačítko Odeslat a volbu potvrdí

        Expected:
        -  Odeslání samostatného nálezu a změna jeho stavu na SN3.
        """
        logger.info("AkceSamostatneNalezy.test_030_potvrzeni_samostatneho_nalezu_p_001.start")
        self.login("archeolog")
        self.createFedoraRecord("C-202211308-N00213")
        self.uploadFileToFedora(606453, "dokument/tests/resources/test.jpg")
        self.uploadFileToFedora(606455, "dokument/tests/resources/test.jpg")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="C-202211308-N00213").first().stav, SN_ODESLANY)

        self.goToAddress("/pas/detail/C-202211308-N00213")
        self.ElementClick(By.CSS_SELECTOR, "#pas-potvrdit > .app-controls-button-text")
        self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, ".col-sm-3:nth-child(1) > #div_id_evidencni_cislo #id_evidencni_cislo")
        self.driver.find_element(
            By.CSS_SELECTOR, ".col-sm-3:nth-child(1) > #div_id_evidencni_cislo #id_evidencni_cislo"
        ).send_keys("123")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_predano .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-1-0")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-3 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="C-202211308-N00213").first().stav, SN_POTVRZENY)
        logger.info("AkceSamostatneNalezy.test_030_potvrzeni_samostatneho_nalezu_p_001.end")

    def test_031_potvrzeni_samostatneho_nalezu_n_001(self):
        """
        Test 031 Potvrzení samostatného nálezu (negativní scénář 1)

        Test potvrzení samostatného nálezu ve stavu SN2 na stránce /pas/detail. Test simuluje zadání nevalidních dat a měl by končit nepotvrzením samostatného nálezu a jeho ponecháním ve stavu SN2.

        Role:
        Archeolog

        Preconditions:
        - Uživatel je přihlášen.
        - Samostatný nález je ve stavu SN2

        TestData:
        PAS C-202211308-N00213

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře samostatný nález ve stavu SN2 (číslo SN)
        - Samostatné nálezy → Vybrat → Filtr → ID obsahuje „číslo SN“ → Vybrat → otevřít SN
        - Uživatel vyplní testovací data do formuláře
        - Uživatel klikne na tlačítko Odeslat a volbu potvrdí

        Expected:
        - Nepotvrzení samostatného nálezu a jeho ponechání ve stavu SN2.
        - Zobrazena chyba “Před potvrzením musí být nález předán”
        """
        logger.info("AkceSamostatneNalezy.test_031_potvrzeni_samostatneho_nalezu_n_001.start")
        self.login("archeolog")
        self.createFedoraRecord("C-202211308-N00213")
        self.uploadFileToFedora(606453, "dokument/tests/resources/test.jpg")
        self.uploadFileToFedora(606455, "dokument/tests/resources/test.jpg")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="C-202211308-N00213").first().stav, SN_ODESLANY)

        self.goToAddress("/pas/detail/C-202211308-N00213")
        self.ElementClick(By.CSS_SELECTOR, "#pas-potvrdit > .app-controls-button-text")
        self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, ".col-sm-3:nth-child(1) > #div_id_evidencni_cislo #id_evidencni_cislo")
        self.driver.find_element(
            By.CSS_SELECTOR, ".col-sm-3:nth-child(1) > #div_id_evidencni_cislo #id_evidencni_cislo"
        ).send_keys("123")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_predano .filter-option-inner-inner")
        # self.ElementClick(By.ID, "bs-select-1-0")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-3 > .text")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass

        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="C-202211308-N00213").first().stav, SN_ODESLANY)
        logger.info("AkceSamostatneNalezy.test_031_potvrzeni_samostatneho_nalezu_n_001.end")

    def test_032_potvrzeni_samostatneho_nalezu_n_002(self):
        """
        Test 032 Potvrzení samostatného nálezu (negativní scénář 2)

        Test potvrzení samostatného nálezu ve stavu SN2 na stránce /pas/detail. Test simuluje zadání nevalidních dat a měl by končit nepotvrzením samostatného nálezu a jeho ponecháním ve stavu SN2.

        Role:
        Archeolog

        Preconditions:
        - Uživatel je přihlášen.
        - Samostatný nález je ve stavu SN2

        TestData:
        PAS C-202211308-N00213

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře samostatný nález ve stavu SN2 (číslo SN)
        - Samostatný nález → Vybrat → Filtr → ID obsahuje „číslo SN“ → Vybrat → otevřít SN
        - Uživatel vyplní tetovací data do formuláře
        - Uživatel klikne na tlačítko Odeslat a volbu potvrdí

        Expected:
        - Nepotvrzení samostatného nálezu a jeho ponechání ve stavu SN2.
        - Zobrazena chyba “Vyplňte prosím toto pole”
        """
        logger.info("AkceSamostatneNalezy.test_032_potvrzeni_samostatneho_nalezu_n_002.start")
        self.login("archeolog")
        self.createFedoraRecord("C-202211308-N00213")
        self.uploadFileToFedora(606453, "dokument/tests/resources/test.jpg")
        self.uploadFileToFedora(606455, "dokument/tests/resources/test.jpg")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="C-202211308-N00213").first().stav, SN_ODESLANY)

        self.goToAddress("/pas/detail/C-202211308-N00213")
        self.ElementClick(By.CSS_SELECTOR, "#pas-potvrdit > .app-controls-button-text")
        # self.ElementClick(By.CSS_SELECTOR, ".col-sm-3:nth-child(1) > #div_id_evidencni_cislo #id_evidencni_cislo")
        # self.driver.find_element(By.CSS_SELECTOR, ".col-sm-3:nth-child(1) > #div_id_evidencni_cislo #id_evidencni_cislo").send_keys("123")
        self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_predano .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-1-0")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-3 > .text")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass

        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="C-202211308-N00213").first().stav, SN_ODESLANY)
        logger.info("AkceSamostatneNalezy.test_032_potvrzeni_samostatneho_nalezu_n_002.end")

    def test_038_archivace_samostatneho_nalezu_p_001(self):
        """
        Test 038 Archivace samostatného nálezu (pozitivní scénář 1)

        Test archivace samostatného nálezu ve stavu SN3 na stránce /pas/detail. Měl by končit potvrzením samostatného nálezu a změnou jeho stavu na SN4.

        Role:
        Archivář

        Preconditions:
        - Uživatel je přihlášen.
        - Samostatný nález je ve stavu SN3

        TestData:
        C-202010474-N00002

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře samostatný nález ve stavu SN3
        - Samostatné nálezy → Vybrat → Filtr → ID obsahuje „C-202010474-N00002“ → Vybrat → otevřít samostatný nález
        - Uživatel klikne na tlačítko Archivovat a volbu potvrdí

        Expected:
        -  Archivace samostatného nálezu a jeho posunutí do stavu SN4.
        """
        logger.info("AkceSamostatneNalezy.test_038_archivace_samostatneho_nalezu_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-202010474-N00002")
        self.uploadFileToFedora(518731, "dokument/tests/resources/test.jpg")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="C-202010474-N00002").first().stav, SN_POTVRZENY)

        self.goToAddress("/pas/detail/C-202010474-N00002")
        self.ElementClick(By.CSS_SELECTOR, "#pas-archivovat > .app-controls-button-text")
        self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, ".custom-control-label")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="C-202010474-N00002").first().stav, SN_ARCHIVOVANY)
        logger.info("AkceSamostatneNalezy.test_038_archivace_samostatneho_nalezu_p_001.end")

    def test_039_archivace_samostatneho_nalezu_n_001(self):
        """
        Test 039 Archivace samostatného nálezu (negativní scénář 1)

        Test archivace samostatného nálezu ve stavu SN3 na stránce /pas/detail. Test simuluje zadání nevalidních dat a měl by končit nepotvrzením samostatného nálezu a jeho ponecháním ve stavu SN3.

        Role:
        Archivář

        Preconditions:
        - Uživatel je přihlášen.
        - Samostatný nález je ve stavu SN3
        - Uživatel smaže přiloženou fotografii

        TestData:
        C-202010474-N00002

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře samostatný nález ve stavu SN3
        - Samostatné nálezy → Vybrat → Filtr → ID obsahuje „samostatný nález v SN3“ → Vybrat → otevřít samostatný nález
        - Uživatel klikne na tlačítko Archivovat

        Expected:
        - Nepotvrzení samostatného nálezu a jeho ponechání ve stavu SN2.
        - Zobrazena chyba “Chybí fotografie”
        """
        logger.info("AkceSamostatneNalezy.test_039_archivace_samostatneho_nalezu_n_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-202010474-N00002")
        self.uploadFileToFedora(518731, "dokument/tests/resources/test.jpg")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="C-202010474-N00002").first().stav, SN_POTVRZENY)

        self.goToAddress("/pas/detail/C-202010474-N00002")
        self.ElementClick(By.CSS_SELECTOR, "#file-smazat-518731 > .material-icons")
        self.wait(1)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        try:
            self.ElementClick(By.CSS_SELECTOR, "#pas-archivovat > .app-controls-button-text")
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass
        self.wait(1)
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="C-202010474-N00002").first().stav, SN_POTVRZENY)
        logger.info("AkceSamostatneNalezy.test_039_archivace_samostatneho_nalezu_n_001.end")

    def test_045_vraceni_samostatneho_nalezu_p_001(self):
        """
        Test 045 Vrácení samostatného nálezu (pozitivní scénář 1)

        Test vrácení samostatného nálezu ve stavu SN3 na stránce /pas/detail. Měl by končit vrácením samostatného nálezu a změnou jeho stavu na SN2.

        Role:
        Archivář

        Preconditions:
        - Uživatel je přihlášen.
        - Samostatný nález je ve stavu SN3

        TestData:
        M-202301371-N00015

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře samostatný nález ve stavu SN3
        - Samostatné nálezy → Vybrat → Filtr → ID obsahuje „M-202301371-N00015“ → Vybrat → otevřít samostatný nález
        - Uživatel klikne na tlačítko Vrátit, vyplní důvod a volbu potvrdí

        Expected:
        - Vrácení samostatného nálezu do stavu SN2.
        """
        logger.info("AkceSamostatneNalezy.test_045_vraceni_samostatneho_nalezu_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("M-202301371-N00015")
        self.uploadFileToFedora(645376, "dokument/tests/resources/test.jpg")
        self.uploadFileToFedora(645377, "dokument/tests/resources/test.jpg")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="M-202301371-N00015").first().stav, SN_POTVRZENY)

        self.goToAddress("/pas/detail/M-202301371-N00015")
        self.ElementClick(By.CSS_SELECTOR, "#pas-vratit > .app-controls-button-text")
        self.wait(1)
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="M-202301371-N00015").first().stav, SN_ODESLANY)
        logger.info("AkceSamostatneNalezy.test_045_vraceni_samostatneho_nalezu_p_001.end")

    def test_147_test_Fedora_PAS_001(self):
        """
        Test 147 Test Fedory PAS (pozitivní scénář 1)

        Role:
        Badatel, Archivář

        TestData:
        M-202105907
        test.jpg
        test1.jpg

        Steps:
        - Vytvoření záznamu PAS
        - Editace záznamu PAS
        - Vytvoření souboru
        - Reload souboru
        - Smazání souboru
        - Editace záznamu Uložení
        - Smazání záznamu PAS

        Expected:
        - zápis dat do Fedory
        """
        logger.info("AkceSamostatneNalezy.test_147_test_Fedora_PAS_001.start")
        # Vytvoření záznamu PAS
        self.login("badatel1")
        self.createFedoraRecord("M-202105907", "badatel1")
        time = self.getTime()
        ident = self.create_PAS()
        self.check_fedora_change(time, "pas/tests/resources/test_147/create_PAS")

        # Úprava detailu
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.ID, "id_lokalizace")
        self.ElementSendKeys(By.ID, "id_lokalizace", "test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-id-save")
        self.check_fedora_change(time, "pas/tests/resources/test_147/update_PAS")

        # Vytvoření souboru
        time = self.getTime()
        self.ElementClick(By.ID, "NahratSoubory")
        self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "pas/tests/resources/test_147/create_soubor")

        # Úprava souboru
        time = self.getTime()
        file = Soubor.objects.filter(vazba__samostatny_nalez_souboru__ident_cely=ident).first().pk
        self.ElementClick(By.ID, f"file-upgrade-{file}")
        self.upload_file("dokument/tests/resources/test1.jpg", "test1.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "pas/tests/resources/test_147/update_soubor")

        # Smazání souboru
        time = self.getTime()
        file = Soubor.objects.filter(vazba__samostatny_nalez_souboru__ident_cely=ident).first().pk
        self.ElementClick(By.ID, f"file-smazat-{file}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "pas/tests/resources/test_147/delete_soubor")

        self.logout()
        self.login("archivar")
        self.goToAddress(f"/id/{ident}")

        # Úprava uložení
        time = self.getTime()
        self.ElementClick(By.ID, "pas-edit-ulozeni")
        self.ElementSendKeys(By.CSS_SELECTOR, ".modal-body #id_evidencni_cislo", "1")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "pas/tests/resources/test_147/update_ulozeni")

        # Smazání záznamu PAS
        time = self.getTime()
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "pas-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "pas/tests/resources/test_147/delete_PAS")

        logger.info("AkceSamostatneNalezy.test_147_test_Fedora_PAS_001.end")

    def test_154_zobrazeni_spoluprace_p_001(self):
        """
        Test 154 Zobrazení spolupráce Badatel - Archeolog (pozitivní scénář 1)

        Test  "Badatel" vidí jen své spolupráce a "Archeolog" vidí jen spolupráce své organizace

        Role:
        Badatel, Archeolog

        Preconditions:
        - Uživatel je přihlášen.

        TestData:
        žádné.

        Steps:
        Uživatel se přihlásí jako Badatel
        Uživatel klikne na menu PAS -> Spolupráce
        Uživatel Badatel vidí jen své spolupráce
        Uživatel se přihlásí jako Archeolog
        Uživatel Archeolog vidí jen spolupráce své organizace

        Expected:
        - Badatel a Archeolog vidí správný počet záznamů
        """
        logger.info("AkceSamostatneNalezy.test_154_zobrazeni_spoluprace_p_001.start")
        self.login("badatel1")
        self.goToAddress("/pas/spoluprace/vyber")
        pocet_zaznamu = self.driver.find_element(By.ID, "pocet_zaznamu").text
        self.assertEqual(pocet_zaznamu, "3")
        self.logout()
        self.login("archeolog")
        self.goToAddress("/pas/spoluprace/vyber")
        pocet_zaznamu = self.driver.find_element(By.ID, "pocet_zaznamu").text
        self.assertEqual(pocet_zaznamu, "70")
        logger.info("AkceSamostatneNalezy.test_154_zobrazeni_spoluprace_p_001.end")

    def test_159_smazani_samostatneho_nalezu_p_001(self):
        """
        Test 159 Smazání samostatného nálezu (pozitivní scénář 1)

        Smazání záznamu - test zahrne i to, že se smaže i vše, co je na záznam navázané resp. co se má smazat

        Role:
        Archivář

        Preconditions:
        - Uživatel je přihlášen.
        - Samostatný nález je ve stavu SN3

        TestData:
        C-202010474-N00002

        Steps:
        - Uživatel se přihlásí jako Archivář
        - Uživatel otevře samostatný nález ve stavu SN3
        - V panelu pro akce kliknout na  “Další akce” → “Smazat nález”
        - V dalším dialogovém okně “Smazat samostatný nález” kliknout na “Smazat”

        Expected:
        - Samostatný nález “C-202010474-N00002” bude smazán z databáze.
        - Projekt bude mít o 1 samostatný nález méně
        """
        logger.info("AkceSamostatneNalezy.test_159_smazani_samostatneho_nalezu_p_001.start")
        self.login("archivar")

        self.createFedoraRecord("C-202010474-N00002")
        self.uploadFileToFedora(518731, "dokument/tests/resources/test.jpg")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="C-202010474-N00002").first().stav, SN_POTVRZENY)
        pocet_pas_old = SamostatnyNalez.objects.filter(projekt__ident_cely="C-202010474").count()
        self.goToAddress("/pas/detail/C-202010474-N00002")

        self.ElementClick(By.ID, "file-smazat-518731")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "pas-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="C-202010474-N00002").count(), 0)
        pocet_pas_new = SamostatnyNalez.objects.filter(projekt__ident_cely="C-202010474").count()
        self.assertEqual(pocet_pas_new, pocet_pas_old - 1)
        logger.info("AkceSamostatneNalezy.test_159_smazani_samostatneho_nalezu_p_001.end")
