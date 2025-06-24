import logging
import unittest

from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from django.conf import settings
from selenium.webdriver.common.by import By

logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceHeslar(BaseSeleniumTestClass):
    def test_151_test_Fedora_heslar_001(self):
        # Scenar_151 Test Fedory pro heslare
        logger.info("AkceHeslar.test_151_test_Fedora_heslar_001.start")
        self.login("administrator")
        # C heslo
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslar/add/")
        self.ElementClick(By.ID, "id_nazev_heslare")
        self.ElementClick(By.CSS_SELECTOR, "option:nth-child(20)")
        self.driver.find_element(By.ID, "id_heslo").send_keys("test")
        self.driver.find_element(By.ID, "id_heslo_en").send_keys("testen")
        self.driver.find_element(By.ID, "id_zkratka").send_keys("t")
        self.driver.find_element(By.ID, "id_popis").send_keys("test popis")
        self.driver.find_element(By.ID, "id_popis_en").send_keys("test popis en")
        self.driver.find_element(By.ID, "id_razeni").send_keys("10")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/create_heslo")

        # U detail
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslar/1444/change/")
        self.driver.find_element(By.ID, "id_zkratka").send_keys("update")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/update_heslo")

        # C heslar_datace
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslardatace/add/")
        self.ElementClick(By.ID, "id_obdobi")
        self.ElementClick(By.CSS_SELECTOR, "option:nth-child(2)")
        self.driver.find_element(By.ID, "id_rok_od_min").send_keys("1940")
        self.driver.find_element(By.ID, "id_rok_od_max").send_keys("1945")
        self.driver.find_element(By.ID, "id_rok_do_min").send_keys("2000")
        self.driver.find_element(By.ID, "id_rok_do_max").send_keys("2005")
        self.driver.find_element(By.ID, "id_poznamka").send_keys("test popis en")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/create_heslar_datace")

        # U heslar_datace
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslardatace/1444/change/")
        self.driver.find_element(By.ID, "id_rok_do_min").clear()
        self.driver.find_element(By.ID, "id_rok_do_min").send_keys("1990")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/update_heslar_datace")

        # D heslar_datace
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslardatace/1444/change/")
        self.ElementClick(By.CSS_SELECTOR, ".deletelink")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "input[type=submit]:nth-child(2)")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/delete_heslar_datace")

        # C heslar_hierarchie
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslarhierarchie/add/")
        self.ElementClick(By.ID, "select2-id_heslar_nazev_podrazene-container")
        self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_heslar_nazev_podrazene-results > li:nth-child(4)")
        self.ElementClick(By.ID, "select2-id_heslo_podrazene-container")
        self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_heslo_podrazene-results > li:nth-child(4)")
        self.ElementClick(By.ID, "select2-id_heslar_nazev_nadrazene-container")
        self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_heslar_nazev_nadrazene-results > li:nth-child(8)")
        self.ElementClick(By.ID, "select2-id_heslo_nadrazene-container")
        self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_heslo_nadrazene-results > li:nth-child(2)")
        self.ElementClick(By.CSS_SELECTOR, "option:nth-child(4)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/create_heslar_hierarchie")

        # U heslar_hierarchie
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslarhierarchie/1215/change/")
        self.ElementClick(By.CSS_SELECTOR, "option:nth-child(3)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/update_heslar_hierarchie")

        # D heslar_hierarchie
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslarhierarchie/1215/change/")
        self.ElementClick(By.CSS_SELECTOR, ".deletelink")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "#content input[type=submit]:nth-child(2)")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/delete_heslar_hierarchie")

        # C heslar_odkaz
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslarodkaz/add/")
        self.ElementClick(By.ID, "select2-id_heslar_nazev-container")
        self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_heslar_nazev-results > li:nth-child(4)")
        self.ElementClick(By.ID, "select2-id_heslo-container")
        self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_heslo-results > li:nth-child(3)")
        self.driver.find_element(By.ID, "id_zdroj").send_keys("zdroj")
        self.driver.find_element(By.ID, "id_nazev_kodu").send_keys("nazev")
        self.driver.find_element(By.ID, "id_kod").send_keys("150")
        self.ElementClick(By.CSS_SELECTOR, "option:nth-child(3)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/create_heslar_odkaz")

        # U heslar_odkaz
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslarodkaz/1163/change/")
        self.ElementClick(By.CSS_SELECTOR, "#id_skos_mapping_relation > option:nth-child(2)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/update_heslar_odkaz")

        # D heslar_odkaz
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslarodkaz/1163/change/")
        self.ElementClick(By.CSS_SELECTOR, ".deletelink")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "#content input[type=submit]:nth-child(2)")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/delete_heslar_odkaz")

        # D heslo
        time = self.getTime()
        self.goToAddress("/admin/heslar/heslar/1444/change/")
        self.ElementClick(By.CSS_SELECTOR, ".deletelink")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "div:nth-child(2) > input:nth-child(2)")
        self.check_fedora_change(time, "heslar/tests/resources/test_151/delete_heslo")

        logger.info("AkceHeslar.test_151_test_Fedora_heslar_001.end")
