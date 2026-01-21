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
    def go_to_form(self):
        self.goToAddress("/pas/zapsat")

    def create_PAS(self):
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
        # Scenar_25 Zapsání samostatného nálezu (pozitivní scénář 1)
        logger.info("AkceSamostatneNalezy.test_025_zapsani_samostatneho_nalezu_p_001.start")
        self.login("badatel1")
        SN_count_old = SamostatnyNalez.objects.count()
        self.create_PAS()
        SN_count_new = SamostatnyNalez.objects.count()
        self.assertEqual(SN_count_old + 1, SN_count_new)
        logger.info("AkceSamostatneNalezy.test_025_zapsani_samostatneho_nalezu_p_001.end")

    def test_026_zapsani_samostatneho_nalezu_n_001(self):
        # Scenar_26 Zapsání samostatného nálezu (negativní scénář 1)
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
        # Scenar_28 Odeslání samostatného nálezu (pozitivní scénář 1)
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
        # Scenar_29 Odeslání samostatného nálezu (negativní scénář 1)
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
        # Scenar_30 Potvrzení samostatného nálezu (pozitivní scénář 1)
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
        # Scenar_31 Potvrzení samostatného nálezu (negativní scénář 1)
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
        # Scenar_32 Potvrzení samostatného nálezu (negativní scénář 2)
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
        # Scenar_38 Archivace samostatného nálezu (pozitivní scénář 1)
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
        # Scenar_39 Archivace samostatného nálezu (negativní scénář 1)
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
        # Scenar_45 Vrácení samostatného nálezu (pozitivní scénář 1)
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
        # Scenar_147 Test Fedory pro PAS
        logger.info("AkceSamostatneNalezy.test_147_test_Fedora_PAS_001.start")
        # C PAS
        self.login("badatel1")
        self.createFedoraRecord("M-202105907", "badatel1")
        time = self.getTime()
        ident = self.create_PAS()
        self.check_fedora_change(time, "pas/tests/resources/test_147/create_PAS")

        # U detail
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.ID, "id_lokalizace")
        self.ElementSendKeys(By.ID, "id_lokalizace", "test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-id-save")
        self.check_fedora_change(time, "pas/tests/resources/test_147/update_PAS")

        # C soubor
        time = self.getTime()
        self.ElementClick(By.ID, "NahratSoubory")
        self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "pas/tests/resources/test_147/create_soubor")

        # U soubor
        time = self.getTime()
        file = Soubor.objects.filter(vazba__samostatny_nalez_souboru__ident_cely=ident).first().pk
        self.ElementClick(By.ID, f"file-upgrade-{file}")
        self.upload_file("dokument/tests/resources/test1.jpg", "test1.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "pas/tests/resources/test_147/update_soubor")

        # D soubor
        time = self.getTime()
        file = Soubor.objects.filter(vazba__samostatny_nalez_souboru__ident_cely=ident).first().pk
        self.ElementClick(By.ID, f"file-smazat-{file}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "pas/tests/resources/test_147/delete_soubor")

        self.logout()
        self.login("archivar")
        self.goToAddress(f"/id/{ident}")

        # U ulozeni
        time = self.getTime()
        self.ElementClick(By.ID, "pas-edit-ulozeni")
        self.ElementSendKeys(By.CSS_SELECTOR, ".modal-body #id_evidencni_cislo", "1")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "pas/tests/resources/test_147/update_ulozeni")

        # D PAS
        time = self.getTime()
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "pas-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "pas/tests/resources/test_147/delete_PAS")

        logger.info("AkceSamostatneNalezy.test_147_test_Fedora_PAS_001.end")

    def test_154_zobrazeni_spoluprace_p_001(self):
        # Scenar_25 Zobrazební spolupráce badatel archeolog (pozitivní scénář 1)
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
