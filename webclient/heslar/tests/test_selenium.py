import logging
import unittest

from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from django.conf import settings
from selenium.webdriver.common.by import By

logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceHeslar(BaseSeleniumTestClass):
    """Implementuje komponentu ``AkceHeslar`` v rámci aplikace."""

    def test_151_test_Fedora_heslar_001(self):
        """Test 151 Test Fedory pro hesláře (pozitivní scénář 1)

        Role:
            Administrator

        TestData:
            HES-000886
            HES-001066
            HES-001065

        Steps:
            - Vytvoření záznamu Heslář
            - Editace záznamu Heslář
            - Vytvoření záznamu Heslář datace
            - Editace záznamu Heslář datace
            - Smazání záznamu Heslář datace
            - Vytvoření záznamu Heslář hierarchie
            - Editace záznamu Heslář hierarchie
            - Smazání záznamu Heslář hierarchie
            - Vytvoření záznamu Heslář odkaz
            - Editace záznamu Heslář odkaz
            - Smazání záznamu Heslář odkaz
            - Smazání záznamu Heslář

        Expected:
            - zápis dat do Fedory
        """
        logger.info("AkceHeslar.test_151_test_Fedora_heslar_001.start")
        self.login("administrator")
        # Vytvoření hesla
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslar/add/")
        self.ElementClick(By.ID, "id_nazev_heslare")
        self.ElementClick(By.CSS_SELECTOR, "option:nth-child(20)")
        self.ElementSendKeys(By.ID, "id_heslo", "test")
        self.ElementSendKeys(By.ID, "id_heslo_en", "testen")
        self.ElementSendKeys(By.ID, "id_zkratka", "t")
        self.ElementSendKeys(By.ID, "id_popis", "test popis")
        self.ElementSendKeys(By.ID, "id_popis_en", "test popis en")
        self.ElementSendKeys(By.ID, "id_razeni", "10")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/create_heslo")

        # Úprava detailu
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslar/1444/change/")
        self.ElementSendKeys(By.ID, "id_zkratka", "update")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/update_heslo")

        # Vytvoření vazby heslář_datace
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslardatace/add/")
        self.ElementClick(By.ID, "id_obdobi")
        self.ElementClick(By.CSS_SELECTOR, "option:nth-child(2)")
        self.ElementSendKeys(By.ID, "id_rok_od_min", "1940")
        self.ElementSendKeys(By.ID, "id_rok_od_max", "1945")
        self.ElementSendKeys(By.ID, "id_rok_do_min", "2000")
        self.ElementSendKeys(By.ID, "id_rok_do_max", "2005")
        self.ElementSendKeys(By.ID, "id_poznamka", "test popis en")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/create_heslar_datace")

        # Úprava vazby heslář_datace
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslardatace/1444/change/")
        self.driver.find_element(By.ID, "id_rok_do_min").clear()
        self.ElementSendKeys(By.ID, "id_rok_do_min", "1990")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/update_heslar_datace")

        # Smazání vazby heslář_datace
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslardatace/1444/change/")
        self.ElementClick(By.CSS_SELECTOR, ".deletelink")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "input[type=submit]:nth-child(2)")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/delete_heslar_datace")

        # Vytvoření vazby heslář_hierarchie
        self.createFedoraRecord("HES-000886", "administrator")
        self.createFedoraRecord("HES-001066", "administrator")
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslarhierarchie/add/")
        self.ElementClick(By.ID, "select2-id_heslar_nazev_podrazene-container")
        self.wait_for_select2_results()
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_heslar_nazev_podrazene-results > li:nth-child(4)")
        self.ElementClick(By.ID, "select2-id_heslo_podrazene-container")
        self.wait_for_select2_results()
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_heslo_podrazene-results > li:nth-child(4)")
        self.ElementClick(By.ID, "select2-id_heslar_nazev_nadrazene-container")
        self.wait_for_select2_results()
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_heslar_nazev_nadrazene-results > li:nth-child(8)")
        self.ElementClick(By.ID, "select2-id_heslo_nadrazene-container")
        self.wait_for_select2_results()
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_heslo_nadrazene-results > li:nth-child(2)")
        self.ElementClick(By.CSS_SELECTOR, "option:nth-child(4)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/create_heslar_hierarchie")

        # Úprava vazby heslář_hierarchie
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslarhierarchie/1215/change/")
        self.ElementClick(By.CSS_SELECTOR, "option:nth-child(3)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/update_heslar_hierarchie")

        # Smazání vazby heslář_hierarchie
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslarhierarchie/1215/change/")
        self.ElementClick(By.CSS_SELECTOR, ".deletelink")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "#content input[type=submit]:nth-child(2)")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/delete_heslar_hierarchie")

        # Vytvoření vazby heslář_odkaz
        self.createFedoraRecord("HES-001065", "administrator")
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslarodkaz/add/")
        self.ElementClick(By.ID, "select2-id_heslar_nazev-container")
        self.wait_for_select2_results()
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_heslar_nazev-results > li:nth-child(4)")
        self.ElementClick(By.ID, "select2-id_heslo-container")
        self.wait_for_select2_results()
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_heslo-results > li:nth-child(3)")
        self.ElementSendKeys(By.ID, "id_zdroj", "zdroj")
        self.ElementSendKeys(By.ID, "id_nazev_kodu", "nazev")
        self.ElementSendKeys(By.ID, "id_kod", "150")
        self.ElementClick(By.CSS_SELECTOR, "option:nth-child(3)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/create_heslar_odkaz")

        # Úprava vazby heslář_odkaz
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslarodkaz/1163/change/")
        self.ElementClick(By.CSS_SELECTOR, "#id_skos_mapping_relation > option:nth-child(2)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/update_heslar_odkaz")

        # Smazání vazby heslář_odkaz
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslarodkaz/1163/change/")
        self.ElementClick(By.CSS_SELECTOR, ".deletelink")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "#content input[type=submit]:nth-child(2)")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/delete_heslar_odkaz")

        # Smazání hesla
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslar/1444/change/")
        self.ElementClick(By.CSS_SELECTOR, ".deletelink")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "div:nth-child(2) > input:nth-child(2)")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/delete_heslo")

        logger.info("AkceHeslar.test_151_test_Fedora_heslar_001.end")
