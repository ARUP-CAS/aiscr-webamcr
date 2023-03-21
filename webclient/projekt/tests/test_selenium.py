import time
import datetime
import unittest
from types import MappingProxyType

import structlog
from django.conf import settings
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from core.constants import PROJEKT_STAV_PRIHLASENY, PROJEKT_STAV_ZAHAJENY_V_TERENU, PROJEKT_STAV_UKONCENY_V_TERENU, \
    PROJEKT_STAV_UZAVRENY
from core.tests.runner import EXISTING_PROJECT_IDENT_ZACHRANNY, EXISTING_PROJECT_IDENT_STATUS
from core.tests.test_selenium import BaseSeleniumTestClass
from projekt.models import Projekt

logger_s = structlog.get_logger(__name__)


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class ProjektSeleniumTest(BaseSeleniumTestClass):
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

@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class ProjektZapsatSeleniumTest(BaseSeleniumTestClass):
    @classmethod
    def get_base_test_data(cls):
        return {
            "typ_projektu": {
                "field_type": "select_picker",
                "field_id": "id_typ_projektu",
                "value": "záchranný",
            },
            "hlavni_katastr": {
                "field_type": "map",
                "field_id": "projectMap",
                "click_count": 5
            },
            "podnet": {
                "field_type": "text_field",
                "field_id": "id_podnet",
                "value": "test"
            },
            "iokalizace": {
                "field_type": "text_field",
                "field_id": "id_lokalizace",
                "value": "test"
            },
            "parcelni_cislo": {
                "field_type": "text_field",
                "field_id": "id_parcelni_cislo",
                "value": "test"
            },
            "planovane_zahajeni": {
                "field_type": "text_field",
                "field_id": "id_planovane_zahajeni",
                "value":
                    (datetime.datetime.today() + datetime.timedelta(days=2)).strftime('%d.%m.%Y') + " - " + (
                            datetime.datetime.today() + datetime.timedelta(days=5)).strftime('%d.%m.%Y')
            },
            "oznamovatel": {
                "field_type": "text_field",
                "field_id": "id_oznamovatel",
                "value": "test"
            },
            "odpovedna_osoba": {
                "field_type": "text_field",
                "field_id": "id_odpovedna_osoba",
                "value": "test"
            },
            "adresa": {
                "field_type": "text_field",
                "field_id": "id_adresa",
                "value": "test"
            },
            "telefon": {
                "field_type": "text_field",
                "field_id": "id_telefon",
                "value": "+420734456789"
            },
            "email": {
                "field_type": "text_field",
                "field_id": "id_email",
                "value": "test@example.com"
            },
        }

    def go_to_form(self):
        self.driver.find_element(By.CSS_SELECTOR, ".card:nth-child(1) .btn").click()
        self.driver.find_element(By.LINK_TEXT, "Zapsat").click()
        self.driver.find_element(By.CSS_SELECTOR, ".filter-option-inner-inner").click()
        self.driver.find_element(By.ID, "bs-select-1-1").click()

    def test_projekt_zapsat_p_001(self):
        logger_s.debug("CoreSeleniumTest.test_projekt_zapsat_p_001.start")
        project_count_old = Projekt.objects.count()

        self.login()
        self.go_to_form()

        test_data = ProjektZapsatSeleniumTest.get_base_test_data()
        self._fill_form_fields(test_data)

        element = self.driver.find_element(By.ID, "id_oznamovatel")
        assert element.is_enabled() is True
        element = self.driver.find_element(By.ID, "id_odpovedna_osoba")
        assert element.is_enabled() is True
        element = self.driver.find_element(By.ID, "id_adresa")
        assert element.is_enabled() is True
        element = self.driver.find_element(By.ID, "id_telefon")
        assert element.is_enabled() is True
        element = self.driver.find_element(By.ID, "id_email")
        assert element.is_enabled() is True
        self.driver.find_element(By.ID, "actionSubmitBtn").click()

        project_count_new = Projekt.objects.count()
        self.assertEqual(project_count_old + 1, project_count_new)

        logger_s.debug("CoreSeleniumTest.test_projekt_zapsat_p_001.end")

    def test_projekt_zapsat_n_001(self):
        logger_s.debug("CoreSeleniumTest.test_projekt_zapsat_n_001.start")
        project_count_old = Projekt.objects.count()

        self.login()
        self.go_to_form()

        test_data = ProjektZapsatSeleniumTest.get_base_test_data()
        test_data["planovane_zahajeni"] = {
            "field_type": "text_field",
            "field_id": "id_planovane_zahajeni",
            "value":
                (datetime.datetime.today() + datetime.timedelta(days=-9)).strftime('%d.%m.%Y') + " - "
                + (datetime.datetime.today() + datetime.timedelta(days=-5)).strftime('%d.%m.%Y')
        }
        self._fill_form_fields(test_data)

        self.driver.find_element(By.ID, "actionSubmitBtn").click()
        project_count_new = Projekt.objects.count()
        self.assertEqual(project_count_old, project_count_new)
        logger_s.debug("CoreSeleniumTest.test_projekt_zapsat_n_001.end")

    def test_projekt_zapsat_n_002(self):
        logger_s.debug("CoreSeleniumTest.test_projekt_zapsat_n_002.start")
        project_count_old = Projekt.objects.count()

        self.login()
        self.go_to_form()

        test_data = ProjektZapsatSeleniumTest.get_base_test_data()
        test_data["telefon"] = {
            "field_type": "text_field",
            "field_id": "id_telefon",
            "value": "XXX"
        }
        self._fill_form_fields(test_data)

        self.driver.find_element(By.ID, "actionSubmitBtn").click()
        project_count_new = Projekt.objects.count()
        self.assertEqual(project_count_old, project_count_new)
        logger_s.debug("CoreSeleniumTest.test_projekt_zapsat_n_002.end")

    def test_projekt_zapsat_n_003(self):
        logger_s.debug("CoreSeleniumTest.test_projekt_zapsat_n_003.start")
        project_count_old = Projekt.objects.count()

        self.login()
        self.go_to_form()

        test_data = ProjektZapsatSeleniumTest.get_base_test_data()
        test_data["planovane_zahajeni"] = {
            "field_type": "text_field",
            "field_id": "id_planovane_zahajeni",
            "value":
                (datetime.datetime.today() + datetime.timedelta(days=600)).strftime('%d.%m.%Y') + " - "
                + (datetime.datetime.today() + datetime.timedelta(days=620)).strftime('%d.%m.%Y')
        }
        self._fill_form_fields(test_data)

        self.driver.find_element(By.ID, "actionSubmitBtn").click()
        project_count_new = Projekt.objects.count()
        self.assertEqual(project_count_old, project_count_new)
        logger_s.debug("CoreSeleniumTest.test_projekt_zapsat_n_003.end")


class ProjektZmenaStavuSeleniumTest(BaseSeleniumTestClass):
    stav_projektu = None
    next_stav_projektu = None

    def go_to_form(self, y_fill="01"):
        self.driver.find_element(By.CSS_SELECTOR, ".card:nth-child(1) .btn").click()
        self.driver.find_element(By.LINK_TEXT, "Vybrat projekty").click()
        self.driver.find_element(By.LINK_TEXT, self.get_project(y_fill).ident_cely).click()

    @classmethod
    def get_project(cls, y_fill="01") -> Projekt:
        ident_cely = EXISTING_PROJECT_IDENT_STATUS.replace("X", str(cls.stav_projektu)).replace("YY", y_fill)
        return Projekt.objects.get(ident_cely=ident_cely)


class ProjektZahajitVyzkumSeleniumTest(ProjektZmenaStavuSeleniumTest):
    stav_projektu = PROJEKT_STAV_PRIHLASENY
    next_stav_projektu = PROJEKT_STAV_ZAHAJENY_V_TERENU

    def go_to_form(self):
        super(ProjektZahajitVyzkumSeleniumTest, self).go_to_form()
        self.driver.find_element(By.ID, "projekt-zahajit-v-terenu").click()
        time.sleep(2)

    @classmethod
    def get_base_test_data(cls):
        return {
            "datum_zahajeni": {
                "field_type": "text_field",
                "field_id": "id_datum_zahajeni",
                "value": (datetime.datetime.today() + datetime.timedelta(days=-5)).strftime('%d.%m.%Y'),
            },
        }

    def test_projekt_zahajit_vyzkum_p_001(self):
        logger_s.debug("ProjektZahajitVyzkumSeleniumTest.test_projekt_zahajit_vyzkum_p_001.start")

        self.login()
        self.go_to_form()

        test_data = self.get_base_test_data()
        self._fill_form_fields(test_data)
        self.driver.find_element(By.ID, "submit-btn").click()

        self.assertEqual(self.get_project().stav, self.next_stav_projektu)
        self.assertEqual(self.get_project().datum_zahajeni, datetime.datetime.today() + datetime.timedelta(days=-5))

        logger_s.debug("ProjektZahajitVyzkumSeleniumTest.test_projekt_zahajit_vyzkum_p_001.end")


class ProjektUkoncitVyzkumSeleniumTest(ProjektZmenaStavuSeleniumTest):
    stav_projektu = PROJEKT_STAV_ZAHAJENY_V_TERENU
    next_stav_projektu = PROJEKT_STAV_UKONCENY_V_TERENU

    def go_to_form(self):
        super(ProjektUkoncitVyzkumSeleniumTest, self).go_to_form()
        self.driver.find_element(By.ID, "projekt-ukoncit-v-terenu").click()
        time.sleep(2)

    @classmethod
    def get_base_test_data(cls):
        return {
            "datum_ukonceni": {
                "field_type": "text_field",
                "field_id": "id_datum_ukonceni",
                "value": (datetime.datetime.today() + datetime.timedelta(days=-1)).strftime('%d.%m.%Y'),
            },
        }

    def test_projekt_ukoncit_vyzkum_p_001(self):
        logger_s.debug("ProjektUkoncitVyzkumSeleniumTest.test_projekt_ukoncit_vyzkum_p_001.start")

        self.login()
        self.go_to_form()

        test_data = self.get_base_test_data()
        self._fill_form_fields(test_data)
        self.driver.find_element(By.ID, "submit-btn").click()

        self.assertEqual(self.get_project().stav, self.next_stav_projektu)

        logger_s.debug("ProjektUkoncitVyzkumSeleniumTest.test_projekt_ukoncit_vyzkum_p_001.end")

    def test_projekt_ukoncit_vyzkum_n_001(self):
        logger_s.debug("ProjektUkoncitVyzkumSeleniumTest.test_projekt_ukoncit_vyzkum_n_001.start")

        self.login()
        self.go_to_form()

        test_data = self.get_base_test_data()
        test_data["datum_ukonceni"]["value"] = (datetime.datetime.today() +
                                                datetime.timedelta(days=90)).strftime('%d.%m.%Y')
        self._fill_form_fields(test_data)
        self.driver.find_element(By.ID, "submit-btn").click()
        self.assertIn("Datum nesmí být dále než měsíc v budoucnosti",
                      self.driver.find_element(By.ID, "div_id_datum_ukonceni").text)

        self.assertEqual(self.get_project().stav, self.stav_projektu)

        logger_s.debug("ProjektUkoncitVyzkumSeleniumTest.test_projekt_ukoncit_vyzkum_n_001.end")


class ProjektUzavritSeleniumTest(ProjektZmenaStavuSeleniumTest):
    stav_projektu = PROJEKT_STAV_UKONCENY_V_TERENU
    next_stav_projektu = PROJEKT_STAV_UZAVRENY

    def go_to_form(self, y_fill="01"):
        super(ProjektUzavritSeleniumTest, self).go_to_form(y_fill)
        self.driver.find_element(By.ID, "projekt-uzavrit").click()
        time.sleep(2)

    @classmethod
    def get_base_test_data(cls):
        return {}

    def test_projekt_uzavrit_p_001(self):
        logger_s.debug("ProjektUzavritSeleniumTest.test_projekt_uzavrit_p_001.start")

        self.login()
        self.go_to_form()

        test_data = self.get_base_test_data()
        self._fill_form_fields(test_data)
        self.driver.find_element(By.ID, "submit-btn").click()

        self.assertEqual(self.get_project().stav, self.next_stav_projektu)

        logger_s.debug("ProjektUzavritSeleniumTest.test_projekt_uzavrit_p_001.end")

    def test_projekt_uzavrit_n_001(self):
        logger_s.debug("ProjektUzavritSeleniumTest.test_projekt_uzavrit_n_001.start")

        self.login()
        self.go_to_form("02")
        alert_info = self.driver.find_element(By.CLASS_NAME, "alert alert-info")
        self.assertIn("Projekt musí mít alespoň jednu projektovou akci.", alert_info.text)
        self.assertEqual(self.get_project().stav, self.stav_projektu)

        logger_s.debug("ProjektUzavritSeleniumTest.test_projekt_uzavrit_n_001.end")
