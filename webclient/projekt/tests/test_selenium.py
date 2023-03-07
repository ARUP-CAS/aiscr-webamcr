import time

import structlog
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from core.tests.test_selenium import BaseSeleniumTestClass
from projekt.models import Projekt

logger_s = structlog.get_logger(__name__)


class CoreSeleniumTest(BaseSeleniumTestClass):
    def _get_table_columns(self, table):
        elements = table.find_elements(By.TAG_NAME, "th")
        return [e.find_element(By.TAG_NAME, "a").text for e in elements]

    def _check_column_hiding(self, element_id_initial, column_header_text, initial=True):
        logger_s.debug("CoreSeleniumTest._check_column_hiding", element_id_initial=element_id_initial,
                       column_header_text=column_header_text, initial=initial)
        self.driver.find_element(By.CSS_SELECTOR, "#btnGroupDropTable > .material-icons").click()
        self.driver.find_element(By.ID, element_id_initial).click()
        table = self.driver.find_element(By.TAG_NAME, "table")
        columns = self._get_table_columns(table)
        self.assertNotIn(column_header_text, columns)

        element_id_changed = element_id_initial.replace("check", "un" * initial + "check")
        self.driver.find_element(By.ID, element_id_changed).click()
        columns = self._get_table_columns(table)
        self.assertIn(column_header_text, columns)

    def test_projekt_001(self):
        self.login()

        # Go to projects
        self.driver.find_element(By.CSS_SELECTOR, ".card:nth-child(1) .btn").click()
        self.driver.find_element(By.LINK_TEXT, "Vybrat projekty").click()

        # Test sorting by all table columns
        self.driver.find_element(By.LINK_TEXT, "Identifikátor").click()
        self.assertIn("sort=ident_cely", self.driver.current_url)
        self.driver.find_element(By.LINK_TEXT, "Stav").click()
        self.assertIn("sort=stav", self.driver.current_url)
        self.driver.find_element(By.LINK_TEXT, "Hlavní katastr").click()
        self.assertIn("sort=hlavni_katastr", self.driver.current_url)
        self.driver.find_element(By.LINK_TEXT, "Podnět").click()
        self.assertIn("sort=podnet", self.driver.current_url)
        self.driver.find_element(By.LINK_TEXT, "Lokalizace").click()
        self.assertIn("sort=lokalizace", self.driver.current_url)
        self.driver.find_element(By.LINK_TEXT, "Datum zahájení").click()
        self.assertIn("sort=datum_zahajeni", self.driver.current_url)
        self.driver.find_element(By.LINK_TEXT, "Datum ukončení").click()
        self.assertIn("sort=datum_ukonceni", self.driver.current_url)
        self.driver.find_element(By.LINK_TEXT, "Organizace").click()
        self.assertIn("sort=organizace", self.driver.current_url)
        self.driver.find_element(By.LINK_TEXT, "Vedoucí projektů").click()
        self.assertIn("sort=vedouci_projektu", self.driver.current_url)
        self.driver.find_element(By.LINK_TEXT, "Uživatelské označení").click()
        self.assertIn("sort=uzivatelske_oznaceni", self.driver.current_url)
        self.driver.find_element(By.LINK_TEXT, "Plánované zahájení").click()
        self.assertIn("sort=planovane_zahajeni", self.driver.current_url)

        check_column_hiding_ids = (
            ("ico_check_ident_cely", "Identifikátor"),
            ("ico_check_stav", "Stav"),
            ("ico_check_hlavni_katastr", "Hlavní katastr"),
            ("ico_check_podnet", "Podnět"),
            ("ico_check_lokalizace", "Lokalizace"),
            ("ico_check_datum_zahajeni", "Datum zahájení"),
            ("ico_check_datum_ukonceni", "Datum ukončení"),
            ("ico_check_organizace", "Organizace"),
            ("ico_check_vedouci_projektu", "Vedoucí projektů"),
        )

        for item in check_column_hiding_ids:
            self._check_column_hiding(item[0], item[1])
            self.driver.refresh()

    def test_projekt_002(self):
        logger_s.debug("CoreSeleniumTest.test_project_creation.start")
        project_count_old = Projekt.objects.count()

        self.login()

        self.driver.find_element(By.CSS_SELECTOR, ".card:nth-child(1) .btn").click()
        self.driver.find_element(By.LINK_TEXT, "Zapsat").click()

        self.driver.find_element(By.CSS_SELECTOR, ".filter-option-inner-inner").click()
        self.driver.find_element(By.ID, "bs-select-1-1").click()
        dropdown = self.driver.find_element(By.ID, "id_typ_projektu")
        dropdown.find_element(By.XPATH, "//option[. = 'záchranný']").click()
        self.driver.find_element(By.ID, "projectMap").click()
        self.driver.implicitly_wait(1)
        self.driver.find_element(By.ID, "projectMap").click()

        self.driver.find_element(By.ID, "projectMap").click()
        time.sleep(5)
        self.driver.find_element(By.ID, "projectMap").click()
        time.sleep(5)
        self.driver.find_element(By.ID, "projectMap").click()
        time.sleep(5)
        self.driver.find_element(By.ID, "projectMap").click()
        time.sleep(5)
        self.driver.find_element(By.ID, "projectMap").click()
        self.driver.find_element(By.ID, "id_podnet").click()
        self.driver.find_element(By.ID, "id_podnet").send_keys("test")
        self.driver.find_element(By.ID, "id_lokalizace").click()
        self.driver.find_element(By.ID, "id_lokalizace").send_keys("test")
        self.driver.find_element(By.ID, "id_parcelni_cislo").click()
        self.driver.find_element(By.ID, "id_parcelni_cislo").send_keys("test")
        self.driver.find_element(By.ID, "id_planovane_zahajeni").click()
        self.driver.find_element(By.ID, "id_planovane_zahajeni").send_keys("04.03.2023 - 11.03.2023")
        self.driver.find_element(By.ID, "id_oznamovatel").click()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_oznamovatel > div").click()
        element = self.driver.find_element(By.ID, "id_oznamovatel")
        assert element.is_enabled() is True
        self.driver.find_element(By.ID, "id_oznamovatel").click()
        self.driver.find_element(By.ID, "id_oznamovatel").send_keys("test")
        element = self.driver.find_element(By.ID, "id_odpovedna_osoba")
        assert element.is_enabled() is True
        self.driver.find_element(By.ID, "id_odpovedna_osoba").click()
        self.driver.find_element(By.ID, "id_odpovedna_osoba").send_keys("test")
        element = self.driver.find_element(By.ID, "id_adresa")
        assert element.is_enabled() is True
        self.driver.find_element(By.ID, "id_adresa").click()
        self.driver.find_element(By.ID, "id_adresa").send_keys("test")
        element = self.driver.find_element(By.ID, "id_telefon")
        assert element.is_enabled() is True
        self.driver.find_element(By.ID, "id_telefon").click()
        self.driver.find_element(By.ID, "id_telefon").send_keys("+420123456789")
        element = self.driver.find_element(By.ID, "id_email")
        assert element.is_enabled() is True
        self.driver.find_element(By.ID, "id_email").click()
        self.driver.find_element(By.ID, "id_email").send_keys("test@example.com")
        self.driver.find_element(By.ID, "actionSubmitBtn").click()

        project_count_new = Projekt.objects.count()
        self.assertEqual(project_count_old + 1, project_count_new)

        logger_s.debug("CoreSeleniumTest.test_project_creation.end")

