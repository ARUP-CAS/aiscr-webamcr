import logging
import unittest

from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
from core.constants import AZ_STAV_ARCHIVOVANY, AZ_STAV_ODESLANY, AZ_STAV_ZAPSANY
from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from dj.models import DokumentacniJednotka
from django.conf import settings
from django.utils.translation import gettext as _
from dokument.models import Dokument
from komponenta.models import Komponenta
from lokalita.models import Lokalita
from nalez.models import NalezObjekt, NalezPredmet
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceLokality(BaseSeleniumTestClass):
    def go_to_form_zapsat(self):
        self.ElementClick(By.ID, "menuLokality")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.lokality.zapsat"))

    def go_to_form_vybrat(self):
        self.ElementClick(By.ID, "menuLokality")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.lokality.vybrat"))

    def test_051_zapsani_lokality_p_001(self):
        # Scenar_51 Zapsání lokality (pozitivní scénář 1)
        logger.info("AkceLokality.test_051_zapsani_lokality_p_001.start")
        self.login("archeolog")
        self.go_to_form_zapsat()
        count_old = Lokalita.objects.count()

        self.ElementClick(By.ID, "select2-id_hlavni_katastr-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            "Křtiny"
        )
        self.wait(1)
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            Keys.ENTER
        )
        self.ElementClick(By.CSS_SELECTOR, "#div_id_druh .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("pol")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-5-0 > .text")
        # self.ElementClick(By.ID, "div_id_nazev")
        self.wait(1)
        self.ElementClick(By.ID, "id_nazev")
        self.driver.find_element(By.ID, "id_nazev").send_keys("test")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")

        count_new = Lokalita.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceLokality.test_051_zapsani_lokality_p_001.end")

    def test_052_zapsani_lokality_n_001(self):
        # Scenar_52 Zapsání lokality (negativní scénář 1)
        logger.info("AkceLokality.test_052_zapsani_lokality_n_001.start")
        self.login("archeolog")
        self.go_to_form_zapsat()
        count_old = Lokalita.objects.count()

        self.ElementClick(By.ID, "select2-id_hlavni_katastr-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Křtiny")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_druh .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("pol")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-5-0 > .text")
        # self.ElementClick(By.ID, "div_id_nazev")
        # self.ElementClick(By.ID, "id_nazev")
        # self.driver.find_element(By.ID, "id_nazev").send_keys("test")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "newEntitySubmitBtn")
        except Exception:
            pass

        count_new = Lokalita.objects.count()
        self.assertEqual(count_old, count_new)
        logger.info("AkceLokality.test_052_zapsani_lokality_n_001.end")

    def test_053_pridani_DJ_lokality_p_001(self):
        # Scenar_53 Přidání dokumentační jednotky lokalita (pozitivní scénář 1)
        logger.info("AkceLokality.test_053_pridani_DJ_lokality_p_001.start")
        self.login("archeolog")
        self.go_to_form_vybrat()
        count_old = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-L000000001").count()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-L000000001")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")

        self.ElementClick(By.LINK_TEXT, "X-C-L000000001")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-2 > .text")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-2-0")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDjSubmitButton")

        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-L000000001").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceLokality.test_053_pridani_DJ_lokality_p_001.end")

    def test_054_pridani_DJ_lokality_n_001(self):
        # Scenar_54 Přidání dokumentační jednotky lokalita (negativní scénář 1)
        logger.info("AkceLokality.test_054_pridani_DJ_lokality_n_001.start")
        self.login("archeolog")
        self.go_to_form_vybrat()
        count_old = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-L000000001").count()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-L000000001")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")

        self.ElementClick(By.LINK_TEXT, "X-C-L000000001")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        # self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        # self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-2 > .text")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-2-0")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "newDjSubmitButton")
        except Exception:
            pass

        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-L000000001").count()
        self.assertEqual(count_old, count_new)
        logger.info("AkceLokality.test_054_pridani_DJ_lokality_n_001.end")

    def test_055_pridani_komponenty_DJ_lokality_p_001(self):
        # Scenar_55 Přidání komponenty k dokumentační jednotce lokalita (pozitivní scénář 1)
        logger.info("AkceLokality.test_055_pridani_komponenty_DJ_lokality_p_001.start")
        self.login("archeolog")
        self.go_to_form_vybrat()
        count_old = Komponenta.objects.filter(
            komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-L000000002-D01"
        ).count()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")

        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-L000000002")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "X-C-L000000002")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_L000000002_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_X-C-L000000002-D01 > .card-header .material-icons")
        self.ElementClick(By.LINK_TEXT, _("lokalita.templates.dj.djUpdate.moreActions.pridatKomponentu.label"))
        self.ElementClick(By.CSS_SELECTOR, "#div_id_obdobi .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("úně")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.DOWN)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("s")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createCompotSubmitButton")

        count_new = Komponenta.objects.filter(
            komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-L000000002-D01"
        ).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceLokality.test_055_pridani_komponenty_DJ_lokality_p_001.end")

    def test_056_odeslani_lokality_p_001(self):
        # Scenar_56 Odeslání lokality (pozitivní scénář 1)
        logger.info("AkceLokality.test_056_odeslani_lokality_p_001.start")
        self.login("archeolog")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000579").first().stav, AZ_STAV_ZAPSANY)

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")

        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N9000579")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N9000579")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-odeslat > .app-controls-button-text")
        self.wait(1)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000579").first().stav, AZ_STAV_ODESLANY)
        logger.info("AkceLokality.test_056_odeslani_lokality_p_001.end")

    def test_057_odeslani_lokality_n_001(self):
        # Scenar_57 Odeslání lokality (negativní scénář 1)
        logger.info("AkceLokality.test_057_odeslani_lokality_n_001.start")

        self.login("archeolog")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000145").first().stav, AZ_STAV_ZAPSANY)

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")

        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N9000145")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N9000145")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-odeslat > .app-controls-button-text")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000145").first().stav, AZ_STAV_ZAPSANY)
        logger.info("AkceLokality.test_057_odeslani_lokality_n_001.end")

    def test_058_archivace_lokality_p_001(self):
        # Scenar_58 Archivace lokality (pozitivní scénář 1)
        logger.info("AkceLokality.test_058_archivace_lokality_p_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000003").first().stav, AZ_STAV_ODESLANY)
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-archivovat > .material-icons")
        self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, ".custom-control-label")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000003").first().stav, AZ_STAV_ARCHIVOVANY)
        logger.info("AkceLokality.test_058_archivace_lokality_p_001.end")

    def test_059_archivace_lokality_n_001(self):
        # Scenar_59 Archivace lokality (negativní scénář 1)
        logger.info("AkceLokality.test_059_archivace_lokality_n_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000109").first().stav, AZ_STAV_ODESLANY)
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N1000109")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N1000109")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-archivovat > .material-icons")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000109").first().stav, AZ_STAV_ODESLANY)
        logger.info("AkceLokality.test_059_archivace_lokality_n_001.end")

    def test_060_vraceni_odeslane_lokality_p_001(self):
        # Scenar_60 Vrácení odeslané lokality (pozitivní scénář 1)
        logger.info("AkceLokality.test_060_vraceni_odeslane_lokality_p_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000003").first().stav, AZ_STAV_ODESLANY)

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-vratit > .app-controls-button-text")
        self.wait(1)
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000003").first().stav, AZ_STAV_ZAPSANY)
        logger.info("AkceLokality.test_060_vraceni_odeslane_lokality_p_001.end")

    def test_061_vraceni_odeslane_lokality_n_001(self):
        # Scenar_61 Vrácení odeslané lokality (negativní scénář 1)
        logger.info("AkceLokality.test_061_vraceni_odeslane_lokality_n_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000003").first().stav, AZ_STAV_ODESLANY)

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-vratit > .app-controls-button-text")
        # self.ElementClick(By.ID, "id_reason")
        # self.driver.find_element(By.ID, "id_reason").send_keys("test")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000003").first().stav, AZ_STAV_ODESLANY)
        logger.info("AkceLokality.test_061_vraceni_odeslane_lokality_n_001.end")

    def test_062_vraceni_archivovane_lokality_p_001(self):
        # Scenar_62 Vrácení archivované lokality (pozitivní scénář 1)
        logger.info("AkceLokality.test_062_vraceni_archivovane_lokality_p_001.start")

        self.login("archivar")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000593").first().stav, AZ_STAV_ARCHIVOVANY)

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N9000593")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N9000593")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-vratit > .app-controls-button-text")
        self.wait(1)
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000593").first().stav, AZ_STAV_ODESLANY)
        logger.info("AkceLokality.test_062_vraceni_archivovane_lokality_p_001.end")

    def test_063_vraceni_archivovane_lokality_n_001(self):
        # Scenar_63 Vrácení archivované lokality (negativní scénář 1)
        logger.info("AkceLokality.test_063_vraceni_archivovane_lokality_n_001.start")

        self.login("archivar")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000593").first().stav, AZ_STAV_ARCHIVOVANY)

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N9000593")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N9000593")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-vratit > .app-controls-button-text")
        # self.ElementClick(By.ID, "id_reason")
        # self.driver.find_element(By.ID, "id_reason").send_keys("test")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000593").first().stav, AZ_STAV_ARCHIVOVANY)
        logger.info("AkceLokality.test_063_vraceni_archivovane_lokality_n_001.end")

    def test_143_test_Fedory_lokalita_p_001(self):
        # Scenar_143 Test Fedory pro lokalitu
        logger.info("AkceLokality.test_143_test_Fedory_lokalita_p_001.start")
        self.login("archivar")
        # C lokalita
        self.go_to_form_zapsat()
        time = self.getTime()
        self.ElementClick(By.ID, "select2-id_hlavni_katastr-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            "Lanšperk"
        )
        self.wait(1)
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            Keys.ENTER
        )
        self.ElementClick(By.CSS_SELECTOR, "#div_id_druh .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("pol")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-5-0 > .text")
        self.wait(1)
        self.ElementClick(By.ID, "id_nazev")
        self.driver.find_element(By.ID, "id_nazev").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        ident = self.driver.current_url.split("/")[-1]
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_lokalita")

        # U lokalita detail
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.ID, "id_nazev")
        self.driver.find_element(By.ID, "id_nazev").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/update_lokalita")

        # C dokumentacni_jednotka
        time = self.getTime()
        self.ElementClick(By.ID, "button-add-dj")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDjSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_DJ")

        # U dokumentacni_jednotka
        time = self.getTime()
        self.ElementClick(By.ID, f"id_{ident}-D01-nazev")
        self.driver.find_element(By.ID, f"id_{ident}-D01-nazev").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editDjSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/update_DJ")

        # C komponenta
        time = self.getTime()
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, f"#el_dokumentacni_jednotka_{ident.replace('-','_')}_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, f"#detail_dj_form_{ident}-D01 .btn-group:nth-child(1) .material-icons")
        self.ElementClick(
            By.LINK_TEXT, _("arch_z.templates.arch_z.dj.partials.dj_update.editButtons.pridatKomponentu.label")
        )
        self.ElementClick(By.CSS_SELECTOR, "#div_id_obdobi .btn")
        self.ElementClick(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("únětická kultura")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("poh")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createCompotSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_komponenta")

        # U komponenta
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001-obdobi .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-6 > .text")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001-jistota .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-2-1")
        self.ElementClick(By.ID, f"id_{ident}-K001-presna_datace")
        self.driver.find_element(By.ID, f"id_{ident}-K001-presna_datace").send_keys("ne")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001-areal .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-5 > .text")
        self.ElementClick(By.CSS_SELECTOR, ".show-tick .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-4-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/update_komponenta")

        # C nalez_
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_o-0-druh .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-7-8 > .text")
        self.ElementClick(By.ID, f"id_{ident}-K001_o-0-pocet")
        self.driver.find_element(By.ID, f"id_{ident}-K001_o-0-pocet").send_keys("1")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_p-0-druh .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-15-19 > .text")
        self.ElementClick(By.CSS_SELECTOR, ".dropup > .bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-16-4 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_nalez")

        # U nalez_
        time = self.getTime()
        self.driver.find_element(By.ID, f"id_{ident}-K001_o-0-pocet").send_keys("2")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_p-0-specifikace .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-18-14 > .text")
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_o-0-specifikace .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-8-7 > .text")
        self.ElementClick(By.ID, f"id_{ident}-K001_p-0-pocet")
        self.driver.find_element(By.ID, f"id_{ident}-K001_p-0-pocet").send_keys("2")
        self.ElementClick(By.ID, f"id_{ident}-K001_p-0-poznamka")
        self.driver.find_element(By.ID, f"id_{ident}-K001_p-0-poznamka").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/update_nalez")

        # C dokument_cast
        time = self.getTime()
        self.ElementClick(By.ID, "others_doc")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("dokument.templates.dokument_table.pridatNovyDokument.label"))
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
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-0 > .text")
        self.ElementClick(By.ID, "id_popis")
        self.driver.find_element(By.ID, "id_popis").send_keys("test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-7-1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        # nahrat soubor
        self.ElementClick(By.ID, "NahratSoubory")
        self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_dokument_cast")

        # C externi_odkaz
        time = self.getTime()
        self.goToAddress(f"/id/{ident}")
        self.ElementClick(By.ID, "eo-pripojit-do-az")
        self.ElementClick(By.ID, "select2-id_ez-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_EZ")

        # U externi_odkaz
        time = self.getTime()
        id = ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely=ident).first().pk
        self.ElementClick(By.ID, f"ez-change-{id}")
        self.driver.find_element(By.ID, "id_paginace").send_keys("10")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/upadate_EZ")

        # ident_cely
        time = self.getTime()
        self.ElementClick(By.ID, "lokalita-odeslat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        new_ident = self.driver.current_url.split("/")[-1]
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/ident_cely")

        # D externi_odkaz
        time = self.getTime()
        self.ElementClick(By.ID, f"ez-odpojit-{id}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/delete_EZ")

        # D dokument_cast
        time = self.getTime()
        dockument_ident = Dokument.objects.filter(casti__archeologicky_zaznam__ident_cely=new_ident).first().ident_cely
        self.ElementClick(By.ID, f"dokument-odpojit-{dockument_ident}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/delete_dokument_cast")

        # D nalez_
        time = self.getTime()
        self.ElementClick(By.ID, f"el_komponenta_{new_ident.replace('-','_')}_K001")
        pk = (
            NalezObjekt.objects.filter(
                komponenta__komponenta_vazby__dokumentacni_jednotka__archeologicky_zaznam__ident_cely=new_ident
            )
            .first()
            .pk
        )
        self.ElementClick(By.ID, f"objekt-smazat-{pk}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        pk = (
            NalezPredmet.objects.filter(
                komponenta__komponenta_vazby__dokumentacni_jednotka__archeologicky_zaznam__ident_cely=new_ident
            )
            .first()
            .pk
        )
        self.ElementClick(By.ID, f"objekt-smazat-{pk}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/delete_nalez")

        # D komponenta
        time = self.getTime()
        self.ElementClick(By.ID, f"el_komponenta_{new_ident.replace('-','_')}_K001")
        self.ElementClick(By.ID, "others_komponenta")
        self.ElementClick(By.ID, f"komponenta-smazat-{new_ident}-K001")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/delete_komponenta")

        # D dokumentacni_jednotka
        time = self.getTime()
        self.ElementClick(By.ID, f"el_dokumentacni_jednotka_{new_ident.replace('-','_')}_D01")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, f"dj-smazat-{new_ident}-D01")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/delete_DJ")

        # D lokalita
        time = self.getTime()
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "lokalita-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/delete_lokalita")
        logger.info("AkceLokality.test_143_test_Fedory_lokalita_p_001.end")
