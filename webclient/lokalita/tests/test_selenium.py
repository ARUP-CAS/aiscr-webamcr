import logging
import unittest

from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
from core.constants import AZ_STAV_ARCHIVOVANY, AZ_STAV_ODESLANY, AZ_STAV_ZAPSANY
from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from dj.models import DokumentacniJednotka
from django.conf import settings
from django.utils.translation import gettext as _
from dokument.models import Dokument
from freezegun import freeze_time
from komponenta.models import Komponenta
from lokalita.models import Lokalita
from nalez.models import NalezObjekt, NalezPredmet
from pian.models import Pian
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceLokality(BaseSeleniumTestClass):
    def go_to_form_zapsat(self):
        self.goToAddress("/arch-z/lokalita/zapsat")

    def go_to_form_vybrat(self):
        self.goToAddress("/arch-z/lokalita/vyber?sort=nazev")

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
        self.wait_for_select2_results()
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
        self.wait_for_select2_results()
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
            with WaitForPageLoad(self.driver, 5):
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
            with WaitForPageLoad(self.driver, 5):
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
        self.createFedoraRecord("C-DT-100000146")
        self.createFedoraRecord("C-DT-100000147")
        self.uploadFileToFedora(81227, "dokument/tests/resources/test.tif")
        self.uploadFileToFedora(81228, "dokument/tests/resources/test.tif")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000145").first().stav, AZ_STAV_ZAPSANY)

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")

        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N9000145")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N9000145")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-odeslat > .app-controls-button-text")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N9000145").first().stav, AZ_STAV_ZAPSANY)
        logger.info("AkceLokality.test_057_odeslani_lokality_n_001.end")

    def test_058_archivace_lokality_p_001(self):
        # Scenar_58 Archivace lokality (pozitivní scénář 1)
        logger.info("AkceLokality.test_058_archivace_lokality_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-DT-100005206")
        self.createFedoraRecord("C-DY-100000065")
        self.uploadFileToFedora(187330, "dokument/tests/resources/test.tif")
        self.uploadFileToFedora(63104, "dokument/tests/resources/test.tif")
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
        self.createFedoraRecord("C-DT-100005454")
        self.createFedoraRecord("C-DY-100000058")
        self.uploadFileToFedora(187349, "dokument/tests/resources/test.tif")
        self.uploadFileToFedora(63179, "dokument/tests/resources/test.tif")
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000109").first().stav, AZ_STAV_ODESLANY)
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N1000109")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N1000109")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-archivovat > .material-icons")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-N1000109").first().stav, AZ_STAV_ODESLANY)
        logger.info("AkceLokality.test_059_archivace_lokality_n_001.end")

    def test_060_vraceni_odeslane_lokality_p_001(self):
        # Scenar_60 Vrácení odeslané lokality (pozitivní scénář 1)
        logger.info("AkceLokality.test_060_vraceni_odeslane_lokality_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-DT-100005206")
        self.createFedoraRecord("C-DY-100000065")
        self.uploadFileToFedora(187330, "dokument/tests/resources/test.tif")
        self.uploadFileToFedora(63104, "dokument/tests/resources/test.tif")
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
        self.createFedoraRecord("C-DT-100005206")
        self.createFedoraRecord("C-DY-100000065")
        self.uploadFileToFedora(187330, "dokument/tests/resources/test.tif")
        self.uploadFileToFedora(63104, "dokument/tests/resources/test.tif")
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
            with WaitForPageLoad(self.driver, 5):
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
            with WaitForPageLoad(self.driver, 5):
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
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            Keys.ENTER
        )
        self.ElementClick(By.CSS_SELECTOR, "#div_id_druh .filter-option-inner-inner")
        self.ElementSendKeys(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control", "pol")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-5-0 > .text")
        self.wait(1)
        self.ElementClick(By.ID, "id_nazev")
        self.ElementSendKeys(By.ID, "id_nazev", "test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        ident = self.driver.current_url.split("/")[-1]
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_lokalita")

        # U lokalita detail
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.ID, "id_nazev")
        self.ElementSendKeys(By.ID, "id_nazev", "test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/update_lokalita")

        # C dokumentacni_jednotka
        self.createFedoraRecord("ruian-679038", "archivar")
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
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-L000000003-D01-typ .btn.dropdown-toggle.btn-light")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-2 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editDjSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/update_DJ")

        # C PIAN
        time = self.getTime()
        self.ElementClick(By.ID, "add_others")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "show_menu_pian_new_id")
        self.driver.execute_script("""map.setZoom(17); return map.getZoom();""")
        self.wait(2)
        self.ElementClick(By.LINK_TEXT, _("mapa.EditAddMarker"))
        self.wait(0.5)
        self.clickAtMapCoord(12.8289904, 50.3706078)
        self.wait(0.5)
        self.ElementClick(By.CSS_SELECTOR, ".filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createPianSubmitButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_PIAN")

        # U PIAN
        pian = Pian.objects.filter(dokumentacni_jednotky_pianu__ident_cely="X-C-L000000003-D01").first().ident_cely
        time = self.getTime()
        self.ElementClick(By.ID, "el_dokumentacni_jednotka_X_C_L000000003_D01")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, f"pian-upravit-{pian}")
        self.wait(1)
        self.driver.execute_script("""map.setZoom(17); return map.getZoom();""")
        self.wait(2)
        self.ElementClick(By.LINK_TEXT, _("mapa.EditAddMarker"))
        self.wait(0.5)
        self.clickAtMapCoord(12.9, 49.88)
        self.wait(0.5)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editPianButton")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/update_PIAN")

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
        self.ElementSendKeys(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control", "únětická kultura")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner")
        self.ElementSendKeys(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control", "poh")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.wait(1)
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
        self.ElementClick(By.CSS_SELECTOR, f"#div_id_{ident}-K001_p-0-specifikace .filter-option-inner-inner")
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
        self.ElementSendKeys(By.CSS_SELECTOR, ".select2-search__field", "Pavloň")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vzniku")
        self.ElementSendKeys(By.ID, "id_rok_vzniku", "2023")
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
        self.ElementSendKeys(By.ID, "id_popis", "test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-7-1")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_licence .btn")
        self.ElementClick(By.ID, "bs-select-8-1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        # nahrat soubor
        self.ElementClick(By.ID, "NahratSoubory")
        self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_dokument_cast")

        # C externi_odkaz
        self.createFedoraRecord("BIB-0000001", "archivar")
        time = self.getTime()
        self.goToAddress(f"/id/{ident}")
        self.ElementClick(By.ID, "eo-pripojit-do-az")
        self.ElementClick(By.ID, "select2-id_ez-container")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_EZ")

        # U externi_odkaz
        time = self.getTime()
        pk = ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely=ident).first().pk
        self.ElementClick(By.ID, f"ez-change-{pk}")
        self.ElementSendKeys(By.ID, "id_paginace", "10")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/update_EZ")

        # ident_cely
        time = self.getTime()
        self.ElementClick(By.ID, "lokalita-odeslat")
        with freeze_time("2025-07-27 12:00:01", ignore=["core.tests.test_selenium"]):
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        new_ident = self.driver.current_url.split("/")[-1]
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/ident_cely")
        self.check_fedora_delete(["record/X-C-L000000003", "record/X-C-TX-000000009"])

        # D externi_odkaz
        time = self.getTime()
        self.ElementClick(By.ID, f"ez-odpojit-{pk}")
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

        # změna ident_cely PIAN
        self.createFedoraRecord("X-C-K0751147", "archivar")
        self.createFedoraRecord("N-1412-000000007", "archivar")
        self.createFedoraRecord("C-DT-100005023", "archivar")
        self.createFedoraRecord("C-DT-100005024", "archivar")
        self.uploadFileToFedora(187083, "dokument/tests/resources/test.tif", "archivar")
        self.uploadFileToFedora(187080, "dokument/tests/resources/test.tif", "archivar")
        time = self.getTime()
        self.goToAddress("/arch-z/lokalita/detail/X-C-K0751147/dj/C-K0751147-D01")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "pian-potvrdit-N-1412-000000007")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/ident_cely_PIAN")
        self.check_fedora_delete(["record/N-1412-000000007"])

        # C dokument_cast existujici
        self.createFedoraRecord("M-L9000181", "archivar")
        self.createFedoraRecord("M-TX-194300151", "archivar")
        self.createFedoraRecord("M-LN-000000803", "archivar")
        self.uploadFileToFedora(418643, "dokument/tests/resources/test.tif", "archivar")
        self.uploadFileToFedora(534769, "dokument/tests/resources/test.tif", "archivar")
        time = self.getTime()
        self.goToAddress("/id/M-L9000181")
        self.ElementClick(By.ID, "others_doc")
        self.ElementClick(By.ID, "dokument-pripojit")
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection--multiple > .select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("M-TX-194300151")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "lokalita/tests/resources/test_143/create_dokument_cast_1")

        logger.info("AkceLokality.test_143_test_Fedory_lokalita_p_001.end")
