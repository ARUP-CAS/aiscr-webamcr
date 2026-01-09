import base64
import logging
import unittest

from core.constants import D_STAV_ARCHIVOVANY, D_STAV_ODESLANY, D_STAV_ZAPSANY
from core.models import Soubor
from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from django.conf import settings
from django.utils.translation import gettext as _
from dokument.models import Dokument, Let, Tvar
from nalez.models import NalezObjekt, NalezPredmet
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceDokumenty(BaseSeleniumTestClass):
    def go_to_form_zapsat(self):
        self.ElementClick(By.ID, "menuDokumenty")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.dokumenty.zapsat"))

    def go_to_form_vybrat(self):
        self.ElementClick(By.ID, "menuDokumenty")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.dokumenty.vybrat"))

    def test_064_zapsani_dokumentu_p_001(self):
        # Scenar_64 Zapsání dokumentu (pozitivní scénář 1)
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

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")

        count_new = Dokument.objects.count()

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceDokumenty.test_064_zapsani_dokumentu_p_001.end")

    def test_065_zapsani_dokumentu_n_001(self):
        # Scenar_65 Zapsání dokumentu (negativní scénář 1)
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
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "newDocumentSubmitBtn")
        except Exception:
            pass
        count_new = Dokument.objects.count()
        self.assertEqual(count_old, count_new)
        logger.info("AkceDokumenty.test_065_zapsani_dokumentu_n_001.end")

    def test_066_odeslani_dokumentu_p_001(self):
        # Scenar_66 Odeslání dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_066_odeslani_dokumentu_p_001.start")
        self.login("badatel")
        self.go_to_form_vybrat()
        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-000000003").first().stav, D_STAV_ZAPSANY)
        id = Dokument.objects.filter(ident_cely="X-C-TX-000000003").first().id
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-000000003")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-TX-000000003")
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
        # Scenar_67 Odeslání dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_067_odeslani_dokumentu_n_001.start")
        self.login("badatel")
        self.go_to_form_vybrat()

        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-000000003").first().stav, D_STAV_ZAPSANY)
        # self.wait(1)
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-000000003")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-TX-000000003")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.CSS_SELECTOR, "#dokument-odeslat > .app-controls-button-text")
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass

        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-000000003").first().stav, D_STAV_ZAPSANY)
        logger.info("AkceDokumenty.test_067_odeslani_dokumentu_n_001.end")

    def test_068_archivace_dokumentu_p_001(self):
        # Scenar_68 Archivace dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_068_archivace_dokumentu_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("X-C-TX-202413020")
        self.go_to_form_vybrat()

        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-202413020").first().stav, D_STAV_ODESLANY)
        id = Dokument.objects.filter(ident_cely="X-C-TX-202413020").first().id
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-202413020")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-TX-202413020")

        self.ElementClick(By.ID, "NahratSoubory")
        self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")

        self.ElementClick(By.CSS_SELECTOR, "#dokument-archivovat > .app-controls-button-text")
        self.ElementClick(By.CSS_SELECTOR, ".custom-control-label")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        # self.wait(self.wait_interval+10)
        self.assertEqual(Dokument.objects.filter(id=id).first().stav, D_STAV_ARCHIVOVANY)
        logger.info("AkceDokumenty.test_068_archivace_dokumentu_p_001.end")

    def test_069_archivace_dokumentu_n_001(self):
        # Scenar_69 Archivace dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_069_archivace_dokumentu_n_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()

        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-202413013").first().stav, D_STAV_ODESLANY)
        id = Dokument.objects.filter(ident_cely="X-C-TX-202413013").first().id
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-202413013")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-TX-202413013")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.CSS_SELECTOR, "#dokument-archivovat > .app-controls-button-text")
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass

        self.assertEqual(Dokument.objects.filter(id=id).first().stav, D_STAV_ODESLANY)
        logger.info("AkceDokumenty.test_069_archivace_dokumentu_n_001.end")

    def test_070_vraceni_odeslaneho_dokumentu_p_001(self):
        # Scenar_70 Vrácení odeslaného dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_070_vraceni_odeslaneho_dokumentu_p_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()

        self.assertEqual(Dokument.objects.filter(ident_cely="M-TX-201604272").first().stav, D_STAV_ODESLANY)
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("M-TX-201604272")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "M-TX-201604272")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text")
        # self.wait(1)
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(Dokument.objects.filter(ident_cely="M-TX-201604272").first().stav, D_STAV_ZAPSANY)
        logger.info("AkceDokumenty.test_070_vraceni_odeslaneho_dokumentu_p_001.end")

    def test_071_vraceni_odeslaneho_dokumentu_n_001(self):
        # Scenar_71 Vrácení odeslaného dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_071_vraceni_odeslaneho_dokumentu_n_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()

        self.assertEqual(Dokument.objects.filter(ident_cely="M-TX-201604272").first().stav, D_STAV_ODESLANY)
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("M-TX-201604272")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "M-TX-201604272")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text")
        # self.ElementClick(By.ID, "id_reason")
        # self.driver.find_element(By.ID, "id_reason").send_keys("test")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass
        self.assertEqual(Dokument.objects.filter(ident_cely="M-TX-201604272").first().stav, D_STAV_ODESLANY)
        logger.info("AkceDokumenty.test_071_vraceni_odeslaneho_dokumentu_n_001.end")

    def test_072_vraceni_archivovaneho_dokumentu_p_001(self):
        # Scenar_72 Vrácení archivovaného dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_072_vraceni_archivovaneho_dokumentu_p_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()

        self.assertEqual(Dokument.objects.filter(ident_cely="C-TX-202400071").first().stav, D_STAV_ARCHIVOVANY)
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-TX-202400071")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-TX-202400071")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text")
        # self.wait(1)
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(Dokument.objects.filter(ident_cely="C-TX-202400071").first().stav, D_STAV_ODESLANY)
        logger.info("AkceDokumenty.test_072_vraceni_archivovaneho_dokumentu_p_001.end")

    def test_073_vraceni_archivovaneho_dokumentu_n_001(self):
        # Scenar_73 Vrácení archivovaného dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_073_vraceni_archivovaneho_dokumentu_n_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()

        self.assertEqual(Dokument.objects.filter(ident_cely="C-TX-202400071").first().stav, D_STAV_ARCHIVOVANY)
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-TX-202400071")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-TX-202400071")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text")
        # self.ElementClick(By.ID, "id_reason")
        # self.driver.find_element(By.ID, "id_reason").send_keys("test")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass
        self.assertEqual(Dokument.objects.filter(ident_cely="C-TX-202400071").first().stav, D_STAV_ARCHIVOVANY)
        logger.info("AkceDokumenty.test_073_vraceni_archivovaneho_dokumentu_n_001.end")

    def test_132_zapsani_dokumentu_p_002(self):
        # Scenar_132 Zapsání dokumentu (pozitivní scénář 1)
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
        # Scenar_133 Zapsání dokumentu (negativní scénář 1)
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
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "newDocumentSubmitBtn")
        except Exception:
            pass
        count_new = Dokument.objects.count()

        self.assertEqual(count_old, count_new)
        logger.info("AkceDokumenty.test_133_zapsani_dokumentu_n_002.end")

    def test_134_odeslani_dokumentu_p_002(self):
        # Scenar_134 Odeslání dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_134_odeslani_dokumentu_p_002.start")
        self.login("archeolog")
        self.go_to_form_vybrat()
        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-000000002").first().stav, D_STAV_ZAPSANY)
        DBid = Dokument.objects.filter(ident_cely="X-C-TX-000000002").first().id
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-000000002")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-TX-000000002")
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
        # Scenar_135 Odeslání dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_135_odeslani_dokumentu_n_002.start")
        self.login("archeolog")
        self.go_to_form_vybrat()
        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-000000002").first().stav, D_STAV_ZAPSANY)
        DBid = Dokument.objects.filter(ident_cely="X-C-TX-000000002").first().id
        # self.wait(1)
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-000000002")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-TX-000000002")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.CSS_SELECTOR, "#dokument-odeslat > .app-controls-button-text")
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass
        self.assertEqual(Dokument.objects.filter(id=DBid).first().stav, D_STAV_ZAPSANY)
        logger.info("AkceDokumenty.test_135_odeslani_dokumentu_n_002.end")

    def test_141_test_Fedory_dokument_p_001(self):
        logger.info("AkceDokumenty.test_141_test_Fedory_dokument_p_001.start")

        # C dokument
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

        # U detail
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.ID, "id_popis")
        self.ElementSendKeys(By.ID, "id_popis", "test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_dokument")

        # U detail let
        self.createFedoraRecord("C-LET-00001", "archivar")
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_let .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-10-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_let")

        # C dokument_cast akce
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

        # C dokument_cast lokalita
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

        # C dokument_cast projekt
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

        # C komponenta
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

        # C nalez_objekt + předmět
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

        # C tvar
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}_d-0-tvar .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-26-8 > span:nth-child(2)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editTvarSubmitButton")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/create_tvar")

        # C soubor
        time = self.getTime()
        self.ElementClick(By.ID, "NahratSoubory")
        self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/create_soubor")

        # zmena idnet_cely
        time = self.getTime()
        self.ElementClick(By.ID, "dokument-odeslat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        new_ident = self.driver.current_url.split("/")[-1]
        self.check_fedora_change(time, "dokument/tests/resources/test_141/ident_cely")
        self.check_fedora_delete(["record/X-C-DL-000000009"])

        # U dokument_cast
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, ".list-group-item:nth-child(1) strong")
        self.ElementClick(By.ID, "button-edit-cast")
        self.ElementClick(By.CSS_SELECTOR, ".modal-body > #div_id_poznamka #id_poznamka")
        self.ElementSendKeys(By.CSS_SELECTOR, ".modal-body > #div_id_poznamka #id_poznamka", "test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_dokument_cast")

        # U komponenta C-DL-202500001-D004
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, f"#el_li_komponenta_{new_ident.replace('-','_')}_K001 a")
        self.ElementClick(By.ID, f"id_{new_ident}-K001-presna_datace")
        self.driver.find_element(By.ID, f"id_{new_ident}-K001-presna_datace").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_komponenta")

        # U nalez_
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, f"#el_li_komponenta_{new_ident.replace('-','_')}_K001 a")
        self.ElementClick(By.ID, f"id_{new_ident}-K001_o-0-pocet")
        self.driver.find_element(By.ID, f"id_{new_ident}-K001_o-0-pocet").send_keys("10")
        self.ElementClick(By.ID, f"id_{new_ident}-K001_p-0-pocet")
        self.driver.find_element(By.ID, f"id_{new_ident}-K001_p-0-pocet").send_keys("10")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_nalez")

        # D nalez_
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

        # D komponenta
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, f"#el_li_komponenta_{new_ident.replace('-','_')}_K001 a")
        self.ElementClick(By.ID, "others_komponenta")
        self.ElementClick(By.ID, f"komponenta-smazat-{new_ident}-K001")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_komponenta")

        # D dokument_cast
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, ".list-group-item:nth-child(1) strong")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "smazat-cast-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_dokument_cast")

        # D dokument_cast projekt
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, ".list-group-item:nth-child(2) strong")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "smazat-cast-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_dokument_cast_projekt")

        # D dokument_cast lokalita
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, ".list-group-item:nth-child(1) strong")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "smazat-cast-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_dokument_cast_lokalita")

        # U tvar
        time = self.getTime()
        self.ElementClick(By.ID, f"id_{new_ident}_d-0-poznamka")
        self.driver.find_element(By.ID, f"id_{new_ident}_d-0-poznamka").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editTvarSubmitButton")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_tvar")

        # D tvar
        time = self.getTime()
        tvar = Tvar.objects.filter(dokument__ident_cely=new_ident).first().pk
        self.ElementClick(By.ID, f"tvar-smazat-{tvar}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_tvar")

        # U soubor
        time = self.getTime()
        file = Soubor.objects.filter(vazba__dokument_souboru__ident_cely=new_ident).first().pk
        self.ElementClick(By.ID, f"file-upgrade-{file}")
        self.upload_file("dokument/tests/resources/test1.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_soubor")

        # D soubor
        time = self.getTime()
        file = Soubor.objects.filter(vazba__dokument_souboru__ident_cely=new_ident).first().pk
        self.ElementClick(By.ID, f"file-smazat-{file}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_soubor")

        # D dokument
        time = self.getTime()
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "dokument-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_dokument")

        # U neident_akce
        self.createFedoraRecord("C-TX-197602290", "archivar")
        time = self.getTime()
        self.goToAddress("/id/C-TX-197602290")
        self.ElementClick(By.CSS_SELECTOR, ".list-group-item:nth-child(1) strong")
        self.ElementClick(By.ID, "button-edit-neident")
        self.ElementClick(By.CSS_SELECTOR, ".row:nth-child(10) #id_popis")
        self.ElementSendKeys(By.CSS_SELECTOR, ".row:nth-child(10) #id_popis", "test")
        self.ElementClick(By.CSS_SELECTOR, ".row:nth-child(10) #id_poznamka")
        self.ElementSendKeys(By.CSS_SELECTOR, ".row:nth-child(10) #id_poznamka", "test1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/update_neident_akce")

        # D neident_akce
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, ".list-group-item:nth-child(1) strong")
        self.ElementClick(By.ID, "others_neident")
        self.ElementClick(By.ID, "smazat-neident-akce-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_141/delete_neident_akce")

        # D dokument X-C-TX-201801164
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
        # Scenar_142 Test Fedory pro LET
        logger.info("AkceDokumenty.test_142_test_Fedory_LET_p_001.start")
        # C Let
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

        # U Let
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

        # D Let
        time = self.getTime()
        let = Let.objects.filter(ident_cely="C-LET-00413").first().pk
        self.goToAddress(f"/admin/dokument/let/{let}/change/")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, "Odstranit")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "input:nth-child(2)")
        self.check_fedora_change(time, "dokument/tests/resources/test_142/delete_let")

        logger.info("AkceDokumenty.test_142_test_Fedory_LET_p_001.end")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceKnihovna3D(BaseSeleniumTestClass):
    def go_to_form_zapsat(self):
        self.ElementClick(By.ID, "menuKnihovna3D")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.knihovna3D.zapsat"))

    def go_to_form_vybrat(self):
        self.ElementClick(By.ID, "menuKnihovna3D")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.knihovna3D.vybrat"))

    def zapsat_zaznam(self):
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
        self.go_to_form_vybrat()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys(ident_cely)
        self.ElementClick(By.ID, "buttonVybrat")

        self.ElementClick(By.LINK_TEXT, ident_cely)
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
        with open("dokument/tests/resources/del.zip", "rb") as zip_file:
            encoded_string = base64.b64encode(zip_file.read()).decode()
        self.addFileToDropzone("#my-awesome-dropzone", "del.zip", encoded_string)
        self.wait(1)
        self.ElementClick(By.ID, "buttonUploadSubmit")
        self.ElementClick(By.ID, "dokument-odeslat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        ident = self.driver.current_url.split("/")[-1]
        return ident

    def pridani_objektu(self, ident):
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
        # Scenar_104 Zápis záznamu do knihovny 3D (pozitivní scénář 1)
        logger.info("AkceKnihovna3D.test_104_zapis_do_knihovny_D3_p_001.start")
        self.login("archeolog")
        count_old = Dokument.objects.count()
        self.zapsat_zaznam()
        count_new = Dokument.objects.count()

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_104_zapis_do_knihovny_D3_p_001.end")

    def test_105_odeslani_zaznamu_knihovny_D3_p_001(self):
        # Scenar_105 Odeslání záznamu do knihovny 3D (pozitivní scénář 1)
        logger.info("AkceKnihovna3D.test_105_odeslani_zaznamu_knihovny_D3_p_001.start")
        self.login("archeolog")
        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-3D-000000005").first().stav, D_STAV_ZAPSANY)
        id = Dokument.objects.filter(ident_cely="X-C-3D-000000005").first().id
        self.odeslat_zaznam("X-C-3D-000000005")

        self.assertEqual(Dokument.objects.filter(id=id).first().stav, D_STAV_ODESLANY)
        logger.info("AkceKnihovna3D.test_105_odeslani_zaznamu_knihovny_D3_p_001.end")

    def test_106_pridani_objektu_knihovny_D3_p_001(self):
        # Scenar_106 Přidání objektu k záznamu v Knihovně 3D (pozitivní scénář 1)
        logger.info("AkceKnihovna3D.test_106_pridani_objektu_knihovny_D3_p_001.start")
        self.login("archeolog")
        self.go_to_form_vybrat()

        count_old = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000005"
        ).count()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-3D-000000005")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-3D-000000005")
        self.pridani_objektu("X-C-3D-000000005")

        count_new = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000005"
        ).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_106_pridani_objektu_knihovny_D3_p_001.end")

    def test_107_pridani_predmetu_knihovny_D3_p_001(self):
        # Scenar_107 Přidání předmětu k záznamu v Knihovně 3D (pozitivní scénář 1)
        logger.info("AkceKnihovna3D.test_107_pridani_predmetu_knihovny_D3_p_001.start")
        self.login("archeolog")
        self.go_to_form_vybrat()

        count_old = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000005"
        ).count()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-3D-000000005")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-3D-000000005")
        self.pridani_predmetu("X-C-3D-000000005")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editNalezSubmitButton")
        count_new = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000005"
        ).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_107_pridani_predmetu_knihovny_D3_p_001.end")

    def test_108_pridani_souradnic_knihovny_D3_p_001(self):
        # Scenar_108 Přidání prostorového vymezení k záznamu v Knihovně 3D (pozitivní scénář 1)
        logger.info("AkceKnihovna3D.test_108_pridani_souradnic_knihovny_D3_p_001.start")
        self.login("archeolog")
        self.go_to_form_vybrat()

        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-3D-000000005").first().extra_data.geom, None)
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-3D-000000005")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-3D-000000005")

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
        # Scenar_109 Přidání souboru k záznamu v Knihovně 3D (pozitivní scénář 1)
        logger.info("AkceKnihovna3D.test_109_pridani_souboru_zaznamu_knihovny_D3_p_001.start")
        self.login("archeolog")
        self.go_to_form_vybrat()
        count_old = Soubor.objects.filter(vazba__dokument_souboru__ident_cely="X-C-3D-000000005").count()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-3D-000000005")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-3D-000000005")
        self.ElementClick(By.ID, "buttonUpload")
        with open("dokument/tests/resources/del.zip", "rb") as zip_file:
            encoded_string = base64.b64encode(zip_file.read()).decode()
        self.addFileToDropzone("#my-awesome-dropzone", "del.zip", encoded_string)
        self.wait(1)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        count_new = Soubor.objects.filter(vazba__dokument_souboru__ident_cely="X-C-3D-000000005").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_109_pridani_souboru_zaznamu_knihovny_D3_p_001.end")

    def test_110_archivace_zaznamu_knihovny_D3_p_001(self):
        # Scenar_110 Archivace záznamu v Knihovně 3D (pozitivní scénář 1)
        logger.info("AkceKnihovna3D.test_110_archivace_zaznamu_knihovny_D3_p_001.start")
        self.login("archeolog")

        ident = self.zapsat_zaznam()
        self.ElementClick(By.ID, "buttonLogout")
        self.login("archeolog")
        ident = self.odeslat_zaznam(ident)
        self.ElementClick(By.ID, "buttonLogout")
        self.login("archivar")
        self.go_to_form_vybrat()
        self.assertEqual(Dokument.objects.filter(ident_cely=ident).first().stav, D_STAV_ODESLANY)
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys(ident)
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, ident)

        self.ElementClick(By.ID, "dokument-archivovat")
        self.ElementClick(By.CSS_SELECTOR, ".custom-control-label")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(Dokument.objects.filter(ident_cely=ident).first().stav, D_STAV_ARCHIVOVANY)
        logger.info("AkceKnihovna3D.test_110_archivace_zaznamu_knihovny_D3_p_001.end")

    def test_111_zapis_do_knihovny_D3_p_002(self):
        # Scenar_111 Zápis záznamu do knihovny 3D (pozitivní scénář 1)
        logger.info("AkceKnihovna3D.test_111_zapis_do_knihovny_D3_p_002.start")
        self.login("badatel")
        count_old = Dokument.objects.count()
        self.zapsat_zaznam()
        count_new = Dokument.objects.count()

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_111_zapis_do_knihovny_D3_p_002.end")

    def test_112_odeslani_zaznamu_knihovny_D3_p_002(self):
        # Scenar_112 Odeslání záznamu do knihovny 3D (pozitivní scénář 2)
        logger.info("AkceKnihovna3D.test_112_odeslani_zaznamu_knihovny_D3_p_002.start")
        self.login("badatel")
        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-3D-000000006").first().stav, D_STAV_ZAPSANY)
        id = Dokument.objects.filter(ident_cely="X-C-3D-000000006").first().id
        self.odeslat_zaznam("X-C-3D-000000006")

        self.assertEqual(Dokument.objects.filter(id=id).first().stav, D_STAV_ODESLANY)
        logger.info("AkceKnihovna3D.test_112_odeslani_zaznamu_knihovny_D3_p_002.end")

    def test_113_pridani_objektu_knihovny_D3_p_002(self):
        # Scenar_113 Přidání objektu k záznamu v Knihovně 3D (pozitivní scénář 2)
        logger.info("AkceKnihovna3D.test_113_pridani_objektu_knihovny_D3_p_002.start")
        self.login("badatel")
        self.go_to_form_vybrat()

        count_old = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000006"
        ).count()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-3D-000000006")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-3D-000000006")
        self.pridani_objektu("X-C-3D-000000006")

        count_new = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000006"
        ).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_113_pridani_objektu_knihovny_D3_p_002.end")

    def test_114_pridani_predmetu_knihovny_D3_p_002(self):
        # Scenar_114 Přidání předmětu k záznamu v Knihovně 3D (pozitivní scénář 2)
        logger.info("AkceKnihovna3D.test_114_pridani_predmetu_knihovny_D3_p_002.start")
        self.login("badatel")
        self.go_to_form_vybrat()

        count_old = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000006"
        ).count()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-3D-000000006")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-3D-000000006")
        self.pridani_predmetu("X-C-3D-000000006")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editNalezSubmitButton")
        count_new = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__casti_dokumentu__dokument__ident_cely="X-C-3D-000000006"
        ).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_114_pridani_predmetu_knihovny_D3_p_002.end")

    def test_115_pridani_souradnic_knihovny_D3_p_002(self):
        # Scenar_115 Přidání prostorového vymezení k záznamu v Knihovně 3D (pozitivní scénář 2)
        logger.info("AkceKnihovna3D.test_115_pridani_souradnic_knihovny_D3_p_002.start")
        self.login("badatel")
        self.go_to_form_vybrat()

        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-3D-000000006").first().extra_data.geom, None)
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-3D-000000006")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-3D-000000006")

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
        # Scenar_116 Přidání souboru k záznamu v Knihovně 3D (pozitivní scénář 2)
        logger.info("AkceKnihovna3D.test_116_pridani_souboru_zaznamu_knihovny_D3_p_002.start")
        self.login("badatel")
        self.go_to_form_vybrat()
        count_old = Soubor.objects.filter(vazba__dokument_souboru__ident_cely="X-C-3D-000000006").count()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-3D-000000006")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-3D-000000006")
        self.ElementClick(By.ID, "buttonUpload")
        with open("dokument/tests/resources/del.zip", "rb") as zip_file:
            encoded_string = base64.b64encode(zip_file.read()).decode()
        self.addFileToDropzone("#my-awesome-dropzone", "del.zip", encoded_string)
        self.wait(1)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        count_new = Soubor.objects.filter(vazba__dokument_souboru__ident_cely="X-C-3D-000000006").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceKnihovna3D.test_116_pridani_souboru_zaznamu_knihovny_D3_p_002.end")

    def test_144_test_Fedory_3D_p_001(self):
        # Scenar_144 Test Fedory pro 3D dokumenty
        logger.info("AkceKnihovna3D.test_144_test_Fedory_3D_p_001.start")

        self.login("archivar")
        # C 3D dokument
        time = self.getTime()
        ident = self.zapsat_zaznam()
        self.check_fedora_change(time, "dokument/tests/resources/test_144/create_3D_dokument")

        # U detail
        time = self.getTime()
        self.ElementClick(By.ID, "buttonEdit")
        self.ElementClick(By.ID, "id_popis")
        self.ElementSendKeys(By.ID, "id_popis", "test1")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_format .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/update_3D_dokument")

        # U komponenta
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

        # C nalez_
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

        # U nalez_
        time = self.getTime()
        self.goToAddress(f"/id/{ident}")
        self.ElementClick(By.ID, f"id_{ident}-K001_o-0-pocet")
        self.driver.find_element(By.ID, f"id_{ident}-K001_o-0-pocet").send_keys("1")
        self.ElementClick(By.ID, f"id_{ident}-K001_p-0-pocet")
        self.driver.find_element(By.ID, f"id_{ident}-K001_p-0-pocet").send_keys("2")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editNalezSubmitButton")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/update_nalez")

        # C soubor
        time = self.getTime()
        self.goToAddress(f"/id/{ident}")
        self.ElementClick(By.ID, "buttonUpload")
        with open("dokument/tests/resources/del.zip", "rb") as zip_file:
            encoded_string = base64.b64encode(zip_file.read()).decode()
        self.addFileToDropzone("#my-awesome-dropzone", "del.zip", encoded_string)
        self.wait(1)
        self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/create_soubor")

        # U soubor
        time = self.getTime()
        file = Soubor.objects.filter(vazba__dokument_souboru__ident_cely=ident).first().pk
        self.ElementClick(By.ID, f"file-upgrade-{file}")
        with open("dokument/tests/resources/test.jpg", "rb") as zip_file:
            encoded_string = base64.b64encode(zip_file.read()).decode()
        self.addFileToDropzone("#my-awesome-dropzone", "test.jpg", encoded_string)
        self.wait(1)
        self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/update_soubor")

        # ident_cely
        time = self.getTime()
        self.ElementClick(By.ID, "dokument-odeslat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        new_ident = self.driver.current_url.split("/")[-1]
        self.check_fedora_change(time, "dokument/tests/resources/test_144/ident_cely")
        self.check_fedora_delete(["record/X-C-3D-000000009"])

        # D nalez_
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

        # D soubor
        time = self.getTime()
        file = Soubor.objects.filter(vazba__dokument_souboru__ident_cely=new_ident).first().pk
        self.ElementClick(By.ID, f"file-smazat-{file}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/delete_soubor")

        # D 3D dokument
        time = self.getTime()
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "dokument-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "dokument/tests/resources/test_144/delete_3D_dokument")

        logger.info("AkceKnihovna3D.test_144_test_Fedory_3D_p_001.end")
