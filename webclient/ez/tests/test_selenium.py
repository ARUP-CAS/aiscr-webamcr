import logging
import unittest

from core.constants import EZ_STAV_ODESLANY, EZ_STAV_ZAPSANY
from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from django.conf import settings
from django.utils.translation import gettext as _
from ez.models import ExterniZdroj
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceExterniZdroj(BaseSeleniumTestClass):
    def go_to_form_zapsat(self):
        self.ElementClick(By.ID, "menuExterniZdroje")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.externiZdroje.zapsat"))

    def go_to_form_vybrat(self):
        self.ElementClick(By.ID, "menuExterniZdroje")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.externiZdroje.vybrat"))

    def zaspat_zaznam(self):
        self.go_to_form_zapsat()
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-4 > .text")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".required-next .select2-search__field").send_keys("Pavloň")
        self.driver.find_element(By.CSS_SELECTOR, ".required-next .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vydani_vzniku")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys("2023")
        self.ElementClick(By.ID, "id_nazev")
        self.driver.find_element(By.ID, "id_nazev").send_keys("test")
        self.ElementClick(By.ID, "id_misto")
        self.driver.find_element(By.ID, "id_misto").send_keys("Praha")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        ident = self.driver.current_url.split("/")[-1]
        return ident

    def test_117_zapsani_externího_zdroje_p_001(self):
        # Scenar_117 Zápsání nového externího zdroje typu kniha (pozitivní scénář 1)
        logger.info("AkceExterniZdroj.test_117_zapsani_externího_zdroje_p_001.start")
        self.login("archeolog")
        count_old = ExterniZdroj.objects.count()
        self.zaspat_zaznam()
        count_new = ExterniZdroj.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceExterniZdroj.test_117_zapsani_externího_zdroje_p_001.end")

    def test_118_odeslani_externího_zdroje_p_001(self):
        # Scenar_118 Odeslání záznamu Externí zdroj (pozitivní scénář 1)
        logger.info("AkceExterniZdroj.test_118_odeslani_externího_zdroje_p_001.start")
        self.login("archeolog")
        self.createFedoraRecord("X-BIB-000000001")
        self.assertEqual(ExterniZdroj.objects.filter(ident_cely="X-BIB-000000001").first().stav, EZ_STAV_ZAPSANY)
        id = ExterniZdroj.objects.filter(ident_cely="X-BIB-000000001").first().id
        self.goToAddress("/id/X-BIB-000000001")
        self.ElementClick(By.ID, "ez-odeslat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(ExterniZdroj.objects.filter(id=id).first().stav, EZ_STAV_ODESLANY)
        logger.info("AkceExterniZdroj.test_118_odeslani_externího_zdroje_p_001.end")
