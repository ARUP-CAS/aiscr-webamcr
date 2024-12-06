import base64
import logging
import unittest

from core.constants import D_STAV_ARCHIVOVANY, D_STAV_ODESLANY, D_STAV_ZAPSANY
from core.models import Soubor
from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from django.conf import settings
from django.utils.translation import gettext as _
from dokument.models import Dokument
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
        self.wait(1)
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
        self.ElementClick(By.CSS_SELECTOR, ".app-entity-dokument > .material-icons")
        with open("dokument/tests/resources/test.jpg", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        self.addFileToDropzone("#my-awesome-dropzone", "test.jpg", encoded_string)
        self.driver.set_script_timeout(15)
        self.driver.execute_async_script(
            """
            var done = arguments[0];
            newDropzone.on("success", function(){ done('foo');});
            """
        )
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("core.templates.upload_file.submitButton.text"))
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

    @unittest.skip
    def test_068_archivace_dokumentu_p_001(self):
        # Scenar_68 Archivace dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_068_archivace_dokumentu_p_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()

        self.assertEqual(Dokument.objects.filter(ident_cely="X-C-TX-202413020").first().stav, D_STAV_ODESLANY)
        id = Dokument.objects.filter(ident_cely="X-C-TX-202413020").first().id
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-202413020")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-TX-202413020")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-archivovat > .app-controls-button-text")
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
        self.ElementClick(By.CSS_SELECTOR, ".app-entity-dokument > .material-icons")
        with open("dokument/tests/resources/test.jpg", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        self.addFileToDropzone("#my-awesome-dropzone", "test.jpg", encoded_string)
        self.driver.set_script_timeout(15)
        self.driver.execute_async_script(
            """
            var done = arguments[0];
            newDropzone.on("success", function(){ done('foo');});
            """
        )
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("core.templates.upload_file.submitButton.text"))
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
        self.wait(0.5)
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
