import base64
import logging
import unittest

from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from django.conf import settings
from projekt.models import Projekt
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class OznameniSeleniumTest(BaseSeleniumTestClass):
    def test_027_oznameni_projektu_001(self):
        # Scenar_27 Oznámení projektu

        port = self.server_thread.port
        self.driver.get(f"https://{settings.WEB_SERVER_ADDRESS}:{port}/oznameni")
        project_count_old = Projekt.objects.count()
        self.ElementClick(By.ID, "id_oznamovatel")
        self.driver.find_element(By.ID, "id_oznamovatel").send_keys("Jan Havrlant")
        self.ElementClick(By.ID, "id_odpovedna_osoba")
        self.driver.find_element(By.ID, "id_odpovedna_osoba").send_keys("Jan Havrlant")
        self.ElementClick(By.ID, "id_adresa")
        self.driver.find_element(By.ID, "id_adresa").send_keys("Hilbertova 59")
        self.ElementClick(By.ID, "id_telefon")
        self.driver.find_element(By.ID, "id_telefon").send_keys("608643071")
        self.ElementClick(By.ID, "id_email")
        self.driver.find_element(By.ID, "id_email").send_keys("jhavrlant@arup.cas.cz")
        self.driver.execute_script("$(window).scrollTop(1500 );")
        self.driver.execute_script("""map.setZoom(16); return map.getZoom();""")
        self.clickAt(self.driver.find_element(By.ID, "projectMap"), 0, 0)
        self.wait(self.wait_interval)
        self.clickAt(self.driver.find_element(By.ID, "projectMap"), 0, 0)
        self.ElementClick(By.ID, "id_planovane_zahajeni")
        self.driver.find_element(By.ID, "id_planovane_zahajeni").send_keys("28.11.2024 - 30.11.2024")
        self.driver.find_element(By.ID, "id_planovane_zahajeni").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_podnet")
        self.driver.find_element(By.ID, "id_podnet").send_keys("dům")
        self.ElementClick(By.ID, "id_lokalizace")
        self.driver.find_element(By.ID, "id_lokalizace").send_keys("ulice")
        self.ElementClick(By.ID, "id_parcelni_cislo")
        self.driver.find_element(By.ID, "id_parcelni_cislo").send_keys("1")
        self.ElementClick(By.ID, "id_souhlas")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-id-save")

        with open("oznameni/tests/resources/test_foto_1.jpg", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        self.addFileToDropzone("#my-awesome-dropzone", "test_foto_1.jpg", encoded_string)
        self.wait(1)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit_btn")
            self.driver.switch_to.alert.accept()
        project_count_new = Projekt.objects.count()
        self.assertEqual(project_count_old + 1, project_count_new)
