import datetime
import logging
import unittest

from arch_z.models import Akce
from core.constants import (
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
    PROJEKT_STAV_PRIHLASENY,
    PROJEKT_STAV_UKONCENY_V_TERENU,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    PROJEKT_STAV_ZAPSANY,
    PROJEKT_STAV_ZRUSENY,
)
from core.models import Soubor
from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from django.conf import settings
from django.core import mail
from django.utils.translation import gettext as _
from freezegun import freeze_time
from oznameni.tests.test_selenium import OznameniSeleniumTest
from projekt.models import Projekt
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class ProjektSeleniumTest(BaseSeleniumTestClass):
    """Implementuje komponentu ``ProjektSeleniumTest`` v rámci aplikace."""

    def _get_table_columns(self, table):
        """
        Vrací table columns.

        :param table: Parametr ``table`` pracuje se s atributy ``find_elements``.
        :return: Načtená data odpovídající zadaným vstupům.
        """
        elements = table.find_elements(By.TAG_NAME, "th")
        return [e.text.strip() for e in elements]

    def _check_column_hiding(self, element_id_initial, column_header_text, initial=True):
        """
        Ověří column hiding.

        :param element_id_initial: Parametr ``element_id_initial`` předává se do volání ``info()``, ``find_element()``, ovlivňuje větvení podmínek.
        :param column_header_text: Číselná hodnota ``column_header_text`` použitá při výpočtu nebo transformaci.
        :param initial: Stavová nebo časová hodnota `initial` používaná při rozhodování logiky.
        :return: Vrací výsledek ověření nebo validačního pravidla.
        """
        logger.info(
            "CoreSeleniumTest._check_column_hiding",
            extra={
                "element": element_id_initial,
                "text": column_header_text,
                "initial": initial,
            },
        )
        self.ElementClick(By.CSS_SELECTOR, "#btnGroupDropTable > .material-icons")
        if "display: none" not in self.driver.find_element(By.ID, f"ico_check_{element_id_initial}").get_attribute(
            "style"
        ):
            self.ElementClick(By.XPATH, f"//*[@data-td-class='{element_id_initial}']")
        table = self.driver.find_element(By.TAG_NAME, "table")
        columns = self._get_table_columns(table)
        self.assertNotIn(column_header_text, columns)
        self.ElementClick(By.XPATH, f"//*[@data-td-class='{element_id_initial}']")
        columns = self._get_table_columns(table)
        self.assertIn(column_header_text, columns)

    def test_002_projekt_001(self):
        """
        Test 002 Otevření tabulky projekty

        Testuje tabulku s projekty. Ověřuje, zda funguje řazení podle
        jednotlivých sloupců a zobrazení/skrývání sloupců.

        Využívá metodu ``_check_column_hiding``.

        Role:
        Archeolog

        Preconditions:
        -  Uživatel je přihlášen.

        TestData:
        *Žádná*

        Steps:
        1. Uživatel klikne na menu Projekty -> Vybrat projekty
        2. Uživatel kliká na záhlaví jednotlivých sloupců
        3. Uživatel skryje a znovu zobrazí jednotlivé sloupce pomocí výsuvného
        menu

        Expected:
        1. Po kliknutí na název sloupce je do adresy stránky přidán řetězec
        ``sort=sloupec``
        2. Po skrytí sloupce zmizí název sloupce ze záhlaví
        3. Po zobrazení sloupce je sloupec v záhlaví tabulky
        """
        self.login()
        # Přechod do seznamu projektů
        self.goToAddress("/projekt/vyber?sort=hlavni_katastr&sort=ident_cely")
        # Ověření řazení podle všech sloupců tabulky
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("projekt.models.projekt.stav.label"))
        # WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "btnGroupDropTable")))
        self.assertIn2("sort=stav", "sort=-stav", self.driver)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("projekt.tables.ProjektTable.ident_cely.label"))
        self.assertIn2("sort=ident_cely", "sort=-ident_cely", self.driver)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("projekt.models.projekt.hlavniKatastr.label"))
        self.assertIn2("sort=hlavni_katastr", "sort=-hlavni_katastr", self.driver)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("projekt.models.projekt.podnet.label"))
        self.assertIn2("sort=podnet", "sort=-podnet", self.driver)
        self.ElementClick(By.ID, "btnGroupDropTable")
        if self.driver.find_element(By.XPATH, "//*[@data-td-class='lokalizace']").get_attribute("data-state") != "on":
            self.ElementClick(By.XPATH, "//*[@data-td-class='lokalizace']")
        self.ElementClick(By.ID, "btnGroupDropTable")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("projekt.tables.ProjektTable.lokalizace.label"))
        self.assertIn2("sort=lokalizace", "sort=-lokalizace", self.driver)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("projekt.tables.ProjektTable.datum_zahajeni.label"))
        self.assertIn2("sort=datum_zahajeni", "sort=-datum_zahajeni", self.driver)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("projekt.tables.ProjektTable.datum_ukonceni.label"))
        self.assertIn2("sort=datum_ukonceni", "sort=-datum_ukonceni", self.driver)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("projekt.tables.ProjektTable.organizace.label"))
        self.assertIn2("sort=organizace", "sort=-organizace", self.driver)

        self.ElementClick(By.ID, "btnGroupDropTable")
        if (
            self.driver.find_element(By.XPATH, "//*[@data-td-class='vedouci_projektu']").get_attribute("data-state")
            != "on"
        ):
            self.ElementClick(By.XPATH, "//*[@data-td-class='vedouci_projektu']")
        self.ElementClick(By.ID, "btnGroupDropTable")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("projekt.tables.ProjektTable.vedouci_projektu.label"))
        self.assertIn2("sort=vedouci_projektu", "sort=-vedouci_projektu", self.driver)
        self.ElementClick(By.ID, "btnGroupDropTable")
        if (
            self.driver.find_element(By.XPATH, "//*[@data-td-class='uzivatelske_oznaceni']").get_attribute("data-state")
            != "on"
        ):
            self.ElementClick(By.XPATH, "//*[@data-td-class='uzivatelske_oznaceni']")
        self.ElementClick(By.ID, "btnGroupDropTable")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("projekt.tables.ProjektTable.uzivatelske_oznaceni.label"))
        self.assertIn2("sort=uzivatelske_oznaceni", "sort=-uzivatelske_oznaceni", self.driver)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("projekt.tables.ProjektTable.planovane_zahajeni.label"))
        self.assertIn2("sort=planovane_zahajeni", "sort=-planovane_zahajeni", self.driver)
        check_column_hiding_ids = (
            ("stav", "Stav"),
            ("hlavni_katastr", "Hlavní katastr"),
            ("podnet", "Podnět"),
            ("lokalizace", "Lokalizace"),
            ("datum_zahajeni", "Datum zahájení"),
            ("datum_ukonceni", "Datum ukončení"),
            ("organizace", "Organizace"),
            ("vedouci_projektu", "Vedoucí"),
        )
        for item in check_column_hiding_ids:
            self._check_column_hiding(item[0], item[1])
            self.driver.refresh()

    def test_145_test_Fedora_projekt_001(self):
        """
        Test 145 Test Fedory pro projekty (pozitivní scénář 1)

        Test zapsání dat do Fedory v projektech

        Role:
        Archivář

        TestData:
        Projekt C-201121404, X-M-202393246, C-202111043

        Steps:
        - Vytvoření - projekt zachrany
        - Update - projekt
        - Update oznamovatel
        - Smazat soubor v projektu
        - Vytvoření souboru
        - Vytvoření projektové akce
        - Změna přístupnosti Akce
        - Smazání projektové Akce
        - Smazání projektu
        - Znovu vytvoření projektové Akce

        Expected:
        - zápis dat do Fedory
        """
        logger.info("ProjektSeleniumTest.test_145_test_Fedora_projekt_001.start")
        self.login("archivar")
        # Vytvoření záchranného projektu
        self.createFedoraRecord("U-005361", "archivar")
        self.goToAddress("/projekt/zapsat")
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, ".filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        self.driver.execute_script("""map.setZoom(17); return map.getZoom();""")
        self.wait(0.5)
        self.clickAtMapCoord(15.1700002, 49.84)
        self.wait(0.5)
        self.ElementSendKeys(By.ID, "id_podnet", "test")
        self.ElementSendKeys(By.ID, "id_lokalizace", "test")
        self.ElementSendKeys(By.ID, "id_parcelni_cislo", "test")
        self.ElementSendKeys(By.ID, "id_planovane_zahajeni", "11.6.2025 - 12.6.2025")
        self.driver.find_element(By.ID, "id_planovane_zahajeni").send_keys(Keys.ESCAPE)
        self.ElementClick(By.ID, "id_oznamovatel")
        self.ElementSendKeys(By.ID, "id_oznamovatel", "test")
        self.ElementSendKeys(By.ID, "id_odpovedna_osoba", "test")
        self.ElementSendKeys(By.ID, "id_adresa", "test")
        self.ElementSendKeys(By.ID, "id_telefon", "xxx")
        self.ElementSendKeys(By.ID, "id_email", "test@example.com")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_send_mail label")
        with freeze_time("2025-07-26 12:00:01", ignore=["core.tests.test_selenium"]):
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "actionSubmitBtn")
        self.check_fedora_change(time, "projekt/tests/resources/test_145/create_projekt_zachranny")
        ident = self.driver.current_url.split("/")[-1]

        # Úprava detailu projektu
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementSendKeys(By.ID, "id_podnet", "test1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-id-save")
        self.check_fedora_change(time, "projekt/tests/resources/test_145/update_projekt")

        # Úprava oznamovatele
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn2")
        self.ElementSendKeys(By.ID, "id_adresa", "test1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-id-save")
        self.check_fedora_change(time, "projekt/tests/resources/test_145/update_oznamovatel")

        # Vytvoření souboru
        time = self.getTime()
        self.ElementClick(By.ID, "add_dokumentace")
        with WaitForPageLoad(self.driver):
            self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        self.check_fedora_change(time, "projekt/tests/resources/test_145/create_soubor")

        # Smazání souboru
        time = self.getTime()
        file = Soubor.objects.filter(vazba__projekt_souboru__ident_cely=ident).first().pk
        self.ElementClick(By.ID, f"file-smazat-{file}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "projekt/tests/resources/test_145/delete_soubor")

        # Vytvoření projektové akce
        self.createFedoraRecord("C-201121404", "archivar")
        self.goToAddress("/projekt/detail/C-201121404")
        time = self.getTime()
        self.ElementClick(By.ID, "add_akce")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "actionSubmitBtn")
        self.check_fedora_change(time, "projekt/tests/resources/test_145/create_projektova_akce")

        # zmena pristupnosti akce
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-5-2 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "actionSubmitBtn")
        self.check_fedora_change(time, "projekt/tests/resources/test_145/zmena_pristupnosti_akce")

        # Smazání projektové akce
        time = self.getTime()
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "akce-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "projekt/tests/resources/test_145/delete_projektova_akce")

        # Smazání projektu
        self.createFedoraRecord("X-M-202393246", "archivar")
        self.goToAddress("/projekt/detail/X-M-202393246")
        time = self.getTime()
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "projekt-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "projekt/tests/resources/test_145/delete_projekt")

        # reC projektová akce
        self.createFedoraRecord("C-202111043", "archivar")
        self.createFedoraRecord("C-202111043A", "archivar")
        self.uploadFileToFedora(364200, "projekt/tests/resources/test.pdf", "archivar")
        self.goToAddress("/id/C-202111043A")
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "akce-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.goToAddress("/projekt/detail/C-202111043")
        time = self.getTime()
        self.ElementClick(By.ID, "add_akce")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "actionSubmitBtn")
        self.check_fedora_change(time, "projekt/tests/resources/test_145/recreate_projektova_akce")
        self.check_fedora_delete(["model/deleted/member/C-202111043A"])

        logger.info("ProjektSeleniumTest.test_145_test_Fedora_projekt_001.end")

    def test_146_test_Fedora_projekt_002(self):
        """
        Test 146 Test Fedory pro projekty (pozitivní scénář 2)

        test zapsání dat do Fedory v projektech

        Role:
        Archivář, Administrator

        TestData:
        Projekt  C-202209999, C-202210662, M-202302810, C-202114070
        Dokument M-TX-194300151

        Steps:
        - Vytvoření oznámení
        - Smazání dokumentu u projektu
        - Schválení projektu - změna ident-cely projektu
        - Vytvoření průzkumného projektu
        - Vytvoření části dokumentu projektu
        - Vytvoření záznamu PAS
        - Změna přístupnosti PAS
        - Smazání části dokumentu
        - Smazání záznamu PAS
        - Smazání projektu
        - Znovu vytvoření PAS
        - Vytvoření části dokumentu - existující dokument

        Expected:
        - zápis dat do Fedory
        """
        logger.info("ProjektSeleniumTest.test_146_test_Fedora_projekt_002.start")

        # Vytvoření oznámení
        time = self.getTime()
        with freeze_time("2025-07-27 12:00:01", ignore=["core.tests.test_selenium"]):
            ident = OznameniSeleniumTest.oznameni_projektu(self)
        self.check_fedora_change(time, "projekt/tests/resources/test_146/create_projekt")

        # Úprava projektu – smazání dokumentace
        self.login("archivar")
        self.goToAddress(f"/id/{ident}")
        time = self.getTime()
        file = Soubor.objects.filter(vazba__projekt_souboru__ident_cely=ident).first().pk
        self.ElementClick(By.ID, f"file-smazat-{file}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "projekt/tests/resources/test_146/delete_soubor")

        # ident cely projektu
        self.goToAddress(f"/id/{ident}")
        time = self.getTime()
        self.ElementClick(By.ID, "projekt-schvalit")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_send_mail label")
        with freeze_time("2025-07-27 12:00:01", ignore=["core.tests.test_selenium"]):
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        # ident_new = self.driver.find_element(By.ID, "id-app-entity-item").text
        self.check_fedora_change(time, "projekt/tests/resources/test_146/ident_cely")
        self.check_fedora_delete(["record/X-C-000000001"])

        # Vytvoření projektu průzkumu
        self.goToAddress("/projekt/zapsat")
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, ".filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-3 > .text")
        self.driver.execute_script("""map.setZoom(17); return map.getZoom();""")
        self.wait(0.5)
        self.clickAtMapCoord(15.1700002, 49.84)
        self.wait(0.5)
        self.ElementSendKeys(By.ID, "id_podnet", "test")
        self.ElementSendKeys(By.ID, "id_lokalizace", "test")
        self.ElementSendKeys(By.ID, "id_parcelni_cislo", "test")
        self.ElementSendKeys(By.ID, "id_planovane_zahajeni", "11.6.2025 - 12.6.2025")
        self.driver.find_element(By.ID, "id_planovane_zahajeni").send_keys(Keys.ESCAPE)
        with freeze_time("2025-07-27 12:00:01", ignore=["core.tests.test_selenium"]):
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "actionSubmitBtn")
        self.check_fedora_change(time, "projekt/tests/resources/test_146/create_projekt_pruzkum")
        ident = self.driver.current_url.split("/")[-1]

        # Vytvoření části dokumentu
        self.createFedoraRecord("C-202209999", "archivar")
        self.goToAddress("/id/C-202209999")
        time = self.getTime()
        self.ElementClick(By.ID, "others_doc")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "dokument-add")
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
        self.select_nth_selectpicker_option("id_material_originalu")
        self.ElementClick(By.ID, "id_popis")
        self.ElementSendKeys(By.ID, "id_popis", "test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-7-1")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_licence .btn")
        self.ElementClick(By.ID, "bs-select-8-1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
        self.check_fedora_change(time, "projekt/tests/resources/test_146/create_dokument_cast")
        doc_ident = self.driver.current_url.split("/")[-1]

        # Vytvoření záznamu PAS
        time = self.getTime()
        self.goToAddress("/id/C-202209999")
        self.ElementClick(By.ID, "add_PAS")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        self.check_fedora_change(time, "projekt/tests/resources/test_146/create_PAS")

        # zmena pristupnosti PAS
        time = self.getTime()
        self.ElementClick(By.ID, "pas-edit-ulozeni")
        self.ElementSendKeys(By.CSS_SELECTOR, ".modal-body #id_evidencni_cislo", "1")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "projekt/tests/resources/test_146/zmena_pristupnosti")
        PAS_ident = self.driver.current_url.split("/")[-1]

        # Smazání části dokumentu
        time = self.getTime()
        self.goToAddress("/id/C-202209999")
        self.ElementClick(By.ID, f"dokument-odpojit-{doc_ident}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "projekt/tests/resources/test_146/delete_dokument_cast")

        # Smazání záznamu PAS
        time = self.getTime()
        self.goToAddress(f"/id/{PAS_ident}")
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "pas-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "projekt/tests/resources/test_146/delete_PAS")

        # Smazání projektu C-202210662
        self.logout()
        self.login("administrator")
        self.createFedoraRecord("C-202210662")
        self.createFedoraRecord("C-200810918A-DT-15")
        self.uploadFileToFedora(411126, "dokument/tests/resources/test.tif")
        self.goToAddress("/id/C-202210662")
        time = self.getTime()
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "projekt-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "projekt/tests/resources/test_146/delete_projekt")

        # reC PAS
        self.logout()
        self.login("archivar")
        self.createFedoraRecord("M-202302810", "archivar")
        self.createFedoraRecord("M-202302810-N00001", "archivar")
        self.uploadFileToFedora(584786, "projekt/tests/resources/test.pdf", "archivar")
        self.goToAddress("/id/M-202302810-N00001")
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "pas-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.goToAddress("/projekt/detail/M-202302810")
        time = self.getTime()
        self.ElementClick(By.ID, "add_PAS")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        self.check_fedora_change(time, "projekt/tests/resources/test_146/recreate_PAS")
        self.check_fedora_delete(["model/deleted/member/M-202302810-N00001"])

        # Vytvoření existující části dokumentu
        self.createFedoraRecord("C-202114070", "archivar")
        self.createFedoraRecord("M-TX-194300151", "archivar")
        self.uploadFileToFedora(534769, "projekt/tests/resources/test.pdf", "archivar")
        time = self.getTime()
        self.goToAddress("/id/C-202114070")
        self.ElementClick(By.ID, "others_doc")
        self.ElementClick(By.ID, "dokument-pripojit")
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("M-TX-194300151")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "projekt/tests/resources/test_146/create_dokument_cast_1")

        logger.info("ProjektSeleniumTest.test_146_test_Fedora_projekt_002.end")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class ProjektZapsatSeleniumTest(BaseSeleniumTestClass):
    """Implementuje komponentu ``ProjektZapsatSeleniumTest`` v rámci aplikace."""

    def ProjektZapsat(
        self, *, date_from=2, date_to=5, telefon="+420556123654", css_selector=".step:nth-child(3) .bs-stepper-circle"
    ):
        """
        Provádí operaci ProjektZapsat.

        :param date_from: Časový údaj ``date_from`` použitý při filtrování nebo výpočtu.
        :param date_to: Časový údaj ``date_to`` použitý při filtrování nebo výpočtu.
        :param telefon: Textová hodnota `telefon` používaná pro vyhledání, pojmenování nebo hlášení stavu.
        :param css_selector: Parametr ``css_selector`` slouží jako vstup pro logiku funkce ``ProjektZapsat``.

            :return: Vrací seznam.
        """
        self.login()
        self.go_to_form()
        project_count_old = Projekt.objects.count()
        self.ElementClick(By.CSS_SELECTOR, ".filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        self.driver.execute_script("""map.setZoom(17); return map.getZoom();""")
        self.wait(0.5)
        self.clickAtMapCoord(15.1700002, 49.84)
        self.wait(0.5)
        self.driver.find_element(By.ID, "id_podnet").send_keys("test")
        self.driver.find_element(By.ID, "id_lokalizace").send_keys("test")
        self.driver.find_element(By.ID, "id_parcelni_cislo").send_keys("test")
        datum = (
            (datetime.datetime.today() + datetime.timedelta(days=date_from)).strftime("%d.%m.%Y")
            + " - "
            + (datetime.datetime.today() + datetime.timedelta(days=date_to)).strftime("%d.%m.%Y")
        )
        self.driver.find_element(By.ID, "id_planovane_zahajeni").send_keys(datum)
        self.driver.find_element(By.ID, "id_planovane_zahajeni").send_keys(Keys.ESCAPE)
        self.ElementClick(By.ID, "id_oznamovatel")
        self.driver.find_element(By.ID, "id_oznamovatel").send_keys("test")
        self.driver.find_element(By.ID, "id_odpovedna_osoba").send_keys("test")
        self.driver.find_element(By.ID, "id_adresa").send_keys("test")
        self.driver.find_element(By.ID, "id_telefon").send_keys(telefon)
        self.driver.find_element(By.ID, "id_email").send_keys("test@example.com")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "actionSubmitBtn")
        except Exception:
            pass
        self.wait(4)
        project_count_new = Projekt.objects.count()
        return [project_count_old, project_count_new]

    def go_to_form(self):
        """Provádí operaci go to form."""
        self.goToAddress("/projekt/zapsat")

    def test_003_projekt_zapsat_p_001(self):
        """
        Test 003 Zapsání projektu (pozitivní scénář 1)

        Test zapsání projektu na stránce ``/projekt/zapsat``. Test simuluje
        zadání validních data měl by končit zapsáním projektu do databáze.

        Role:
        Archeolog

        Preconditions:
        -  Uživatel je přihlášen.
        -  Jsou vložena kompletní data o katastrech, okresech a krajích.

        TestData:
        +-----------------------+---------------------------------------------+
        | Field                 | Value                                       |
        +=======================+=============================================+
        | typ_projektu          | záchranný                                   |
        | id_podnet             | test                                        |
        | id_lokalizace         | test                                        |
        | id_parcelni_cislo     | test                                        |
        | id_planovane_zahajeni | dynamicky vložené datum (dnes + dva dny až  |
        |                       | dnes + pět dní)                             |
        | id_oznamovatel        | test                                        |
        | id_odpovedna_osoba    | test                                        |
        | id_adresa             | test                                        |
        | id_telefon            | +420123456789                               |
        | id_email              | test@example.com                            |

        Steps:
        1. Uživatel klikne na menu Projekty -> Zapsat
        2. Uživatel vyplní data do formuláře a kliknutím na mapu vybere hlavní
        katastr
        3. Uživatel klikne na tlačítko Uložit

        Expected:
        -  Pole ``id_oznamovatel`` je povoleno.
        -  Pole ``id_odpovedna_osoba`` je povoleno.
        -  Pole ``id_adresa`` je povoleno.
        -  Pole ``id_telefon`` je povoleno.
        -  Pole ``id_email`` je povoleno.
        -  Po kliknutí na tlačítko Uložit je v databázi o 1 projekt více
        """
        logger.info("CoreSeleniumTest.test_003_projekt_zapsat_p_001.start")
        [project_count_old, project_count_new] = self.ProjektZapsat()
        self.assertEqual(project_count_old + 1, project_count_new)
        logger.info("CoreSeleniumTest.test_003_projekt_zapsat_p_001.end")

    def test_006_schvaleni_projektu_p_001(self):
        """
        Test 006 Schválení projektu (pozitivní scénář 1)

        Test schválení projektu

        Role:
        Archeolog

        Preconditions:
        -  Archivář je přihlášen.
        - Projekt ve stavu Px0

        TestData:
        Očekávané výsledky
        ^^^^^^^^^^^^^^^^^^

        -  Změní se označení projektu.

        Steps:
        Archivář schválí projekt.

        Expected:
        - Projekt přejde do schváleného stavu a aktualizuje se jeho identifikátor.
        - Odešle se notifikační e-mail po schválení projektu.
        """
        logger.info("CoreSeleniumTest.test_006_schvaleni_projektu_p_001.start")

        ident_cely = OznameniSeleniumTest.oznameni_projektu(self)
        # Ověření e-mailu
        self.assertEqual(len(mail.outbox), 1)
        self.login("archivar")
        self.goToAddress(f"/id/{ident_cely}")
        self.ElementClick(By.ID, "projekt-schvalit")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        # Ověření e-mailu
        self.assertEqual(len(mail.outbox), 2)
        ident_cely_new = self.driver.current_url.split("/")[-1]
        self.assertNotEqual(ident_cely, ident_cely_new)
        oznameni = Soubor.objects.filter(
            vazba__projekt_souboru__ident_cely=ident_cely_new, nazev__startswith="oznameni", nazev__endswith=".pdf"
        )
        self.assertEqual(oznameni.count(), 1)
        self.assertGreater(oznameni.first().size_mb, 0.1)
        logger.info("CoreSeleniumTest.test_006_schvaleni_projektu_p_001.end")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class ProjektZahajitVyzkumSeleniumTest(BaseSeleniumTestClass):
    """Implementuje komponentu ``ProjektZahajitVyzkumSeleniumTest`` v rámci aplikace."""

    def go_to_form(self):
        """Provádí operaci go to form."""
        self.goToAddress("/projekt/vyber?stav=2&organizace=315755&sort=hlavni_katastr&sort=ident_cely")

    def test_007_projekt_zahajit_vyzkum_p_001(self):
        """
        Test 007 Zahájení výzkumu (pozitivní scénář 1)

        Test zahájení výzkumu u projektu ve stavu P2 s pozitivním výsledkem. Měl by končit posunem projektu do stavu P3

        Role:
        Archeolog

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt ve stavu A2.

        TestData:
        ================= =====================================
        Field ID          Value
        id_datum_zahajeni (date calculated: -5 days from today)

        Steps:
        Uživatel otevře projekt ve stavu A2.

        Expected:
        -  Projekt přesunut do stavu A3
        -  Datum zahájení projektu odpovídá testovacím datům.
        """
        logger.info("ProjektZahajitVyzkumSeleniumTest.test_007_projekt_zahajit_vyzkum_p_001.start")
        self.login()
        self.createFedoraRecord("C-202211750")
        self.uploadFileToFedora(459668, "projekt/tests/resources/test.pdf")
        self.uploadFileToFedora(459775, "projekt/tests/resources/test.pdf")
        self.go_to_form()

        self.ElementClick(By.CSS_SELECTOR, ".odd:nth-child(2) a")
        self.ElementClick(By.CSS_SELECTOR, "#projekt-zahajit-v-terenu > .app-controls-button-text")
        self.ElementClick(By.ID, "id_datum_zahajeni")
        datum = (datetime.datetime.today() + datetime.timedelta(days=-5)).strftime("%d.%m.%Y")
        self.driver.find_element(By.ID, "id_datum_zahajeni").send_keys(datum)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        datum_input = self.driver.find_element(By.CSS_SELECTOR, ".col-md-3:nth-child(9) .form-control").get_attribute(
            "value"
        )
        ident_cely = self.driver.current_url.split("/")[-1]

        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_ZAHAJENY_V_TERENU)
        self.assertEqual(
            datetime.datetime.strptime(datum_input, "%d.%m.%Y"), datetime.datetime.strptime(datum, "%d.%m.%Y")
        )
        logger.info("ProjektZahajitVyzkumSeleniumTest.test_007_projekt_zahajit_vyzkum_p_001.end")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class ProjektUkoncitVyzkumSeleniumTest(BaseSeleniumTestClass):
    """Implementuje komponentu ``ProjektUkoncitVyzkumSeleniumTest`` v rámci aplikace."""

    def go_to_form(self):
        """Provádí operaci go to form."""
        self.goToAddress("/projekt/vyber?stav=3&organizace=315755&sort=hlavni_katastr&sort=ident_cely")

    def test_008_projekt_ukoncit_vyzkum_p_001(self):
        """
        Test 008 Ukončení výzkumu (pozitivní scénář 1)

        Test ukončení výzkumu u projektu ve stavu P3 s pozitivním výsledkem. Měl by končit posunem projektu do stavu P4.

        Role:
        Archeolog

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt ve stavu A3.

        TestData:
        ================= =====================================
        Field ID          Value
        id_datum_ukonceni (date calculated: -1 days from today)

        Steps:
        Uživatel otevře projekt ve stavu A3.

        Expected:
        -  Projekt přesunut do stavu A4.
        -  Datum zahájení projektu odpovídá testovacím datům.
        """
        logger.info("ProjektUkoncitVyzkumSeleniumTest.test_008_projekt_ukoncit_vyzkum_p_001.start")
        self.login()
        self.createFedoraRecord("C-202006194")
        self.uploadFileToFedora(260183, "projekt/tests/resources/test.pdf")
        self.uploadFileToFedora(260151, "projekt/tests/resources/test.pdf")
        self.go_to_form()

        self.ElementClick(By.CSS_SELECTOR, ".even:nth-child(7) a")
        self.ElementClick(By.CSS_SELECTOR, "#projekt-ukoncit-v-terenu > .app-controls-button-text")
        self.ElementClick(By.ID, "id_datum_ukonceni")
        datum = (datetime.datetime.today() + datetime.timedelta(days=-1)).strftime("%d.%m.%Y")
        self.driver.find_element(By.ID, "id_datum_ukonceni").send_keys(datum)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        ident_cely = self.driver.current_url.split("/")[-1]

        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_UKONCENY_V_TERENU)
        logger.info("ProjektUkoncitVyzkumSeleniumTest.test_008_projekt_ukoncit_vyzkum_p_001.end")

    def test_009_projekt_ukoncit_vyzkum_n_001(self):
        """
        Test 009 Ukončení výzkumu (negativní scénář 1)

        Test ukončení výzkumu u projektu ve stavu P3 s negativním výsledkem. Měl by končit neposunutím projektu do stavu P4.

        Role:
        Archeolog

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt ve stavu A3.

        TestData:
        ================= =====================================
        Field ID          Value
        id_datum_ukonceni (date calculated: 90 days from today)

        Steps:
        Uživatel otevře projekt ve stavu A3.

        Expected:
        -  Projekt zůstal ve stavu A3.
        -  Zobrazena chyba ``Datum nesmí být dále než měsíc v budoucnosti``.
        """
        logger.info("ProjektUkoncitVyzkumSeleniumTest.test_009_projekt_ukoncit_vyzkum_n_001.start")
        self.login()
        self.createFedoraRecord("C-202006194")
        self.uploadFileToFedora(260183, "projekt/tests/resources/test.pdf")
        self.uploadFileToFedora(260151, "projekt/tests/resources/test.pdf")
        self.go_to_form()

        self.ElementClick(By.CSS_SELECTOR, ".even:nth-child(7) a")
        self.ElementClick(By.CSS_SELECTOR, "#projekt-ukoncit-v-terenu > .app-controls-button-text")
        self.ElementClick(By.ID, "id_datum_ukonceni")
        datum = (datetime.datetime.today() + datetime.timedelta(days=90)).strftime("%d.%m.%Y")
        self.driver.find_element(By.ID, "id_datum_ukonceni").send_keys(datum)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        ident_cely = self.driver.current_url.split("/")[-1]

        self.assertIn(
            _("arch_z.validators.maxDatum.error"), self.driver.find_element(By.ID, "div_id_datum_ukonceni").text
        )
        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_ZAHAJENY_V_TERENU)
        logger.info("ProjektUkoncitVyzkumSeleniumTest.test_009_projekt_ukoncit_vyzkum_n_001.end")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class ProjektUzavritSeleniumTest(BaseSeleniumTestClass):
    """Implementuje komponentu ``ProjektUzavritSeleniumTest`` v rámci aplikace."""

    def go_to_form(self):
        """Provádí operaci go to form."""
        self.goToAddress("/projekt/vyber?stav=4&organizace=315755&sort=hlavni_katastr&sort=ident_cely")

    def test_010_projekt_uzavrit_p_001(self):
        """
        Test 010 Uzavření projektu (pozitivní scénář 1)

        Test uzavření projektu ve stavu P4 s pozitivním výsledkem. Měl by končin posunem projektu do stavu P5.

        Role:
        Archeolog

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt ve stavu A4, který má projektovou akci.

        TestData:
        Žádná.

        Steps:
        Uživatel otevře projekt ve stavu A4.

        Expected:
        -  Projekt přesunut do stavu A5.
        """
        logger.info("ProjektUzavritSeleniumTest.test_010_projekt_uzavrit_p_001.start")
        self.login()
        self.go_to_form()

        self.ElementClick(By.LINK_TEXT, "C-201232899")
        self.ElementClick(By.CSS_SELECTOR, "#projekt-uzavrit > .app-controls-button-text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        ident_cely = self.driver.current_url.split("/")[-1]
        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_UZAVRENY)
        logger.info("ProjektUzavritSeleniumTest.test_010_projekt_uzavrit_p_001.end")

    def test_011_projekt_uzavrit_n_001(self):
        """
        Test 011 Uzavření projektu (negativní scénář 1)

        Test uzavření projektu ve stavu P4 s negativním výsledkem. Měl by končin neposunutím projektu do stavu P5.

        Role:
        Archeolog

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt ve stavu A4, který nemá projektovou akci.

        TestData:
        Žádná.

        Steps:
        Uživatel otevře projekt ve stavu A4.

        Expected:
        -  Projekt zůstal ve stavu A4.
        -  Zobrazena chyba ``Projekt musí mít alespoň jednu projektovou akci``.
        """
        logger.info("ProjektUzavritSeleniumTest.test_011_projekt_uzavrit_n_001.start")
        self.login()
        self.go_to_form()
        self.ElementClick(By.LINK_TEXT, "C-201230310")

        self.ElementClick(By.CSS_SELECTOR, "#projekt-uzavrit > .app-controls-button-text")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass
        ident_cely = self.driver.current_url.split("/")[-1]
        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_UKONCENY_V_TERENU)
        logger.info("ProjektUzavritSeleniumTest.test_011_projekt_uzavrit_n_001.end")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class ProjektArchivovatSeleniumTest(BaseSeleniumTestClass):
    """Implementuje komponentu ``ProjektArchivovatSeleniumTest`` v rámci aplikace."""

    stav_projektu = PROJEKT_STAV_UZAVRENY
    next_stav_projektu = PROJEKT_STAV_ARCHIVOVANY

    def go_to_form(self):
        """Provádí operaci go to form."""
        self.goToAddress("/projekt/vyber?stav=5&sort=datum_ukonceni&sort=ident_cely")

    def test_012_projekt_archivovat_p_001(self):
        """
        Test 012 Archivace projektu (pozitivní scénář 1)

        Test archivace projektu ve stavu P5 s pozitivním výsledkem. Scénář končí posunem projektu do stavu P6,

        Role:
        Archivář

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt ve stavu A5, který má archivovanou projektovou akci.

        TestData:
        Žádná.

        Steps:
        Uživatel otevře projekt ve stavu A5.

        Expected:
        -  Projekt je přesunut do stavu A6.
        """
        logger.info("ProjektArchivovatSeleniumTest.test_012_projekt_archivovat_p_001.start")
        self.login("archivar")
        self.go_to_form()

        self.ElementClick(By.LINK_TEXT, "C-201231446")
        self.ElementClick(By.CSS_SELECTOR, "#projekt-archivovat > .app-controls-button-text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        ident_cely = self.driver.current_url.split("/")[-1]
        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_ARCHIVOVANY)
        logger.info("ProjektArchivovatSeleniumTest.test_012_projekt_archivovat_p_001.end")

    def test_013_projekt_uzavrit_n_001(self):
        """
        Test 013 Archivace projektu (negativní scénář 1)

        Test archivace projektu ve stavu P5 s negativním výsledkem. Scénář končí neposunutím projektu do stavu P6,

        Role:
        Archivář

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt ve stavu A5, který má nearchivovanou projektovou
        akci.

        TestData:
        Stejná jako u ``test_projekt_zapsat_p_001``.

        Steps:
        Uživatel otevře projekt ve stavu A5.

        Expected:
        -  Projekt zůstal ve stavu A5.
        -  Zobrazena chyba ``Akce musí být archivovaná``.
        """
        logger.info("ProjektArchivovatSeleniumTest.test_013_projekt_uzavrit_n_001.start")
        self.login("archivar")
        self.go_to_form()

        self.ElementClick(By.LINK_TEXT, "M-201400072")

        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.CSS_SELECTOR, "#projekt-archivovat > .app-controls-button-text")
                self.ElementClick(By.ID, "submit-btn")
        except Exception:
            pass
        ident_cely = self.driver.current_url.split("/")[-1]
        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_UZAVRENY)

        alert_info = self.driver.find_element(By.CLASS_NAME, "alert-info")
        self.assertIn(_("projekt.models.projekt.checkPredArchivaci.akce.text"), alert_info.text)
        logger.info("ProjektArchivovatSeleniumTest.test_013_projekt_uzavrit_n_001.end")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class ProjektVratitSeleniumTest(BaseSeleniumTestClass):
    """Implementuje komponentu ``ProjektVratitSeleniumTest`` v rámci aplikace."""

    def go_to_form(self):
        """Provádí operaci go to form."""
        self.goToAddress("/projekt/vyber?sort=hlavni_katastr&sort=ident_cely")

    def test_014_projekt_vratit_p_001(self):
        """
        Test 014 Vrácení stavu u archivovaného projektu (pozitivní scénář 1)

        Test vrácení projektu do stavu P5 s pozitivním výsledkem. Scénář končí posunem do stavu P5.

        Role:
        Archivář

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt ve stavu A6.

        TestData:
        ========= =====
        Field ID  Value
        id_reason test

        Steps:
        Uživatel otevře projekt ve stavu A6.

        Expected:
        -  Projekt přesunut do stavu A5.
        """
        logger.info("ProjektVratitSeleniumTest.test_014_projekt_vratit_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-202205168")
        self.uploadFileToFedora(520356, "projekt/tests/resources/test.pdf")
        self.go_to_form()

        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_stav .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-6 > .text")

        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202205168")
        self.ElementClick(By.CSS_SELECTOR, "#projekt-vratit > .app-controls-button-text")
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        ident_cely = self.driver.current_url.split("/")[-1]
        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_UZAVRENY)
        logger.info("ProjektVratitSeleniumTest.test_014_projekt_vratit_p_001.end")

    def test_015_projekt_vratit_p_002(self):
        """
        Test 015 Vrácení stavu u uzavřeného projektu (pozitivní scénář 2)

        Test vrácení projektu do stavu P4 s pozitivním výsledkem. Scénář končí posunem do stavu P4.

        Role:
        Archivář

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt ve stavu A5.

        TestData:
        ========= =====
        Field ID  Value
        id_reason test

        Steps:
        Uživatel otevře projekt ve stavu A5.

        Expected:
        -  Projekt přesunut do stavu A4.
        """
        logger.info("ProjektVratitSeleniumTest.test_015_projekt_vratit_p_002.start")
        self.login("archivar")
        self.goToAddress("/projekt/detail/C-201231446")
        self.ElementClick(By.ID, "projekt-vratit")
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        ident_cely = self.driver.current_url.split("/")[-1]
        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_UKONCENY_V_TERENU)
        logger.info("ProjektVratitSeleniumTest.test_015_projekt_vratit_p_002.end")

    def test_016_projekt_vratit_p_003(self):
        """
        Test 016  Vrácení stavu u ukončeného projektu (pozitivní scénář 3)

        Test vrácení projektu do stavu P3 s pozitivním výsledkem. Scénář končí posunem do stavu P3.

        Role:
        Archivář

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt ve stavu A4.

        TestData:
        ========= =====
        Field ID  Value
        id_reason test

        Steps:
        Uživatel otevře projekt ve stavu A4.

        Expected:
        -  Projekt přesunut do stavu A3.
        """
        logger.info("ProjektVratitSeleniumTest.test_projekt_vratit_p_003.start")
        self.login("archivar")
        self.goToAddress("/projekt/detail/C-201557636")
        self.ElementClick(By.ID, "projekt-vratit")
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        ident_cely = self.driver.current_url.split("/")[-1]
        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_ZAHAJENY_V_TERENU)
        logger.info("ProjektVratitSeleniumTest.test_016_projekt_vratit_p_003.end")

    def test_017_projekt_vratit_p_004(self):
        """
        Test 017 Vrácení stavu u zahájeného projektu (pozitivní scénář 4)

        Test vrácení projektu do stavu P2 s pozitivním výsledkem. Scénář končí posunem do stavu P2.

        Role:
        Archivář

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt ve stavu A3.

        TestData:
        ========= =====
        Field ID  Value
        id_reason test

        Steps:
        Uživatel otevře projekt ve stavu A3.

        Expected:
        -  Projekt přesunut do stavu A2.
        """
        logger.info("ProjektVratitSeleniumTest.test_017_projekt_vratit_p_004.start")
        self.login("archivar")
        self.goToAddress("/projekt/detail/C-201121404")
        self.ElementClick(By.ID, "projekt-vratit")
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        ident_cely = self.driver.current_url.split("/")[-1]
        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_PRIHLASENY)
        logger.info("ProjektVratitSeleniumTest.test_017_projekt_vratit_p_004.end")

    def test_018_projekt_vratit_p_005(self):
        """
        Test 018 Vrácení stavu u přihlášeného projektu (pozitivní scénář 5)

        Test vrácení projektu do stavu P2 s pozitivním výsledkem. Scénář končí posunem do stavu A1.

        Role:
        Archivář

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt ve stavu A2.

        TestData:
        ========= =====
        Field ID  Value
        id_reason test

        Steps:
        Uživatel otevře projekt ve stavu A2.

        Expected:
        -  Projekt přesunut do stavu A1.
        """
        logger.info("ProjektVratitSeleniumTest.test_018_projekt_vratit_p_005.start")
        self.login("archivar")
        self.createFedoraRecord("C-201665792")
        self.uploadFileToFedora(17511, "projekt/tests/resources/test.doc")
        self.goToAddress("/projekt/detail/C-201665792")
        self.ElementClick(By.ID, "projekt-vratit")
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        ident_cely = self.driver.current_url.split("/")[-1]
        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_ZAPSANY)
        logger.info("ProjektVratitSeleniumTest.test_018_projekt_vratit_p_005.end")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class ProjektNavrhnoutZrusitSeleniumTest(BaseSeleniumTestClass):
    """Implementuje komponentu ``ProjektNavrhnoutZrusitSeleniumTest`` v rámci aplikace."""

    def test_019_projekt_zrusit_p_001(self):
        """
        Test 019 Navržení zrušení projektu (pozitivní scénář 1)

        Test navržení zrušení projektu s pozitivním výsledkem. Scénář končí posunem projektu do stavu A7.

        Role:
        Archivář

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt.

        TestData:
        ======== ==========
        Field ID Value
        reason   item no. 2

        Steps:
        Uživatel otevře projekt.

        Expected:
        -  Projekt přesunut do stavu A7.
        """
        logger.info("ProjektNavrhnoutZrusitSeleniumTest.test_019_projekt_zrusit_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-201665792")
        self.uploadFileToFedora(17511, "projekt/tests/resources/test.doc")

        self.goToAddress("/projekt/detail/C-201665792")
        self.ElementClick(By.CSS_SELECTOR, "#projekt-navrh-zruseni > .app-controls-button-text")
        self.ElementClick(By.ID, "id_reason_1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        ident_cely = self.driver.current_url.split("/")[-1]
        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_NAVRZEN_KE_ZRUSENI)
        logger.info("ProjektNavrhnoutZrusitSeleniumTest.test_019_projekt_zrusit_p_001.end")

    def test_020_projekt_zrusit_p_002(self):
        """
        Test 020 Navržení zrušení projektu (pozitivní scénář 2)

        Test navržení zrušení projektu s pozitivním výsledkem. Scénář končí posunem projektu do stavu A7.

        Role:
        Archivář

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt.

        TestData:
        ============= ==========
        Field ID      Value
        reason        item no. 1
        id_projekt_id test

        Steps:
        Uživatel otevře projekt.

        Expected:
        -  Projekt přesunut do stavu A7.
        """
        logger.info("ProjektNavrhnoutZrusitSeleniumTest.test_020_projekt_zrusit_p_002.start")
        self.login("archivar")
        self.createFedoraRecord("C-201665792")
        self.uploadFileToFedora(17511, "projekt/tests/resources/test.doc")

        self.goToAddress("/projekt/detail/C-201665792")
        self.ElementClick(By.CSS_SELECTOR, "#projekt-navrh-zruseni > .app-controls-button-text")
        self.ElementClick(By.ID, "id_reason_0")
        self.ElementClick(By.ID, "id_projekt_id")
        self.driver.find_element(By.ID, "id_projekt_id").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        ident_cely = self.driver.current_url.split("/")[-1]
        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_NAVRZEN_KE_ZRUSENI)
        logger.info("ProjektNavrhnoutZrusitSeleniumTest.test_020_projekt_zrusit_p_002.end")

    def test_021_projekt_zrusit_n_001(self):
        """
        Test 021 Navržení zrušení projektu (negativní scénář 1)

        Test navržení zrušení projektu s negativním výsledkem. Scénář končí neposunutím projektu do stavu A7.

        Role:
        Archivář

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt s projektovými akcemi.

        TestData:
        ======== ==========
        Field ID Value
        reason   item no. 2

        Steps:
        Uživatel otevře projekt s projektovými akcemi.

        Expected:
        -  Projekt zůstal ve výchozím stavu.
        -  Zobrazena chyba ``Projekt před zrušením nesmí mít projektové akce``.
        """
        logger.info("ProjektNavrhnoutZrusitSeleniumTest.test_021_projekt_zrusit_n_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-202401104")
        self.uploadFileToFedora(639669, "projekt/tests/resources/test.pdf")
        self.uploadFileToFedora(639688, "projekt/tests/resources/test.pdf")

        self.goToAddress("/projekt/detail/C-202401104")
        self.ElementClick(By.CSS_SELECTOR, "#projekt-navrh-zruseni > .app-controls-button-text")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.CSS_SELECTOR, ".custom-control:nth-child(2) > .custom-control-label")
                self.ElementClick(By.CSS_SELECTOR, ".btn-primary:nth-child(2)")
        except Exception:
            pass

        ident_cely = self.driver.current_url.split("/")[-1]
        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_UZAVRENY)
        logger.info("ProjektNavrhnoutZrusitSeleniumTest.test_021_projekt_zrusit_n_001.end")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class ProjektZrusitSeleniumTest(BaseSeleniumTestClass):
    """Implementuje komponentu ``ProjektZrusitSeleniumTest`` v rámci aplikace."""

    def test_022_projekt_zrusit_p_001(self):
        """
        Test 022 Zrušení projektu (pozitivní scénář 1)

        Test zrušení projektu s pozitivním výsledkem. Scénář končí posunem projektu do stavu A8

        Role:
        Archivář

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt ve stavu A7.

        TestData:
        ============== =====
        Field ID       Value
        id_reason_text test

        Steps:
        Uživatel otevře projekt s projektovými akcemi.

        Expected:
        -  Projekt je přesunut do stavu A8.
        """
        logger.info("ProjektZrusitSeleniumTest.test_022_projekt_zrusit_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("M-202202919")
        self.uploadFileToFedora(424158, "projekt/tests/resources/test.pdf")
        self.uploadFileToFedora(424159, "projekt/tests/resources/test.pdf")
        self.goToAddress("/projekt/detail/M-202202919")
        self.ElementClick(By.CSS_SELECTOR, "#projekt-zrusit > .app-controls-button-text")
        self.ElementClick(By.ID, "id_reason_text")
        self.driver.find_element(By.ID, "id_reason_text").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        ident_cely = self.driver.current_url.split("/")[-1]
        self.assertEqual(Projekt.objects.get(ident_cely=ident_cely).stav, PROJEKT_STAV_ZRUSENY)
        logger.info("ProjektZrusitSeleniumTest.test_022_projekt_zrusit_p_001.end")

    def test_155_smazani_projektu_p_001(self):
        """
        Test 155 Smazání záznamu projektu (pozitivní scénář 1)

        Smazání záznamu - test zahrne i to, že se smaže i vše, co je na záznam navázané resp. co se má smazat

        Role:
        Archivář

        TestData:
        Projekt X-C-202419296

        Preconditions:
        -  Uživatel je přihlášen.
        -  Existuje projekt ve stavu A0.

        Steps:
        - Uživatel otevře projekt ke smazání.
        - Smaže připojenou dokumentaci.
        - V panelu pro akce kliknout na  “Další akce” → “Smazat záznam”
        - V dalším dialogovém okně “Smazat projekt” kliknout na “Smazat”

        Expected:
        -  Projekt je vymazán z databáze.
        """
        logger.info("ProjektZrusitSeleniumTest.test_155_smazani_projektu_p_001.start")
        self.login("archivar")
        ident_cely = "X-C-202419296"
        self.createFedoraRecord(ident_cely)
        self.uploadFileToFedora(646217, "projekt/tests/resources/test.pdf")
        self.assertEqual(Projekt.objects.filter(ident_cely=ident_cely).count(), 1)
        self.goToAddress(f"/projekt/detail/{ident_cely}")
        self.ElementClick(By.ID, "file-smazat-646217")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "projekt-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(Projekt.objects.filter(ident_cely=ident_cely).count(), 0)
        logger.info("ProjektZrusitSeleniumTest.test_155_smazani_projektu_p_001.end")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class ProjektVytvoreniProjektoveAkce(BaseSeleniumTestClass):
    """Implementuje komponentu ``ProjektVytvoreniProjektoveAkce`` v rámci aplikace."""

    def test_023_projekt_vytvori_akci_p_001(self):
        """
        Test 023 Vytvoření projektové akce (pozitivní scénář 1)

        Test vytvoření projektové akce. Scénář končí vytvořením projektové akce ve stavu A1.

        Role:
        Archeolog

        Preconditions:
        - Uživatel je přihlášen.
        - Projekt je ve stavu P3

        TestData:
        Projekt C-202401502

        Steps:
        - Uživatel se přihlásí
        - Uživatel otevře projekt ve stavu P3 (viz předpoklady)
        - Projekty → Vybrat → Filtr → ID obsahuje „C-202111043“ → Vybrat → otevřít projekt
        - Kliknout na Vložit další akci (v sekci Archeologické akce)
        - Vytvoření akci

        Expected:
        -  Vytvoření akce u projektu - v databázi bude o jednu akci více.
        """
        logger.info("ProjektVytvoreniProjektoveAkce.test_023_projekt_vytvori_akci_p_001.start")
        self.login()
        self.createFedoraRecord("C-202401502")
        self.uploadFileToFedora(643547, "projekt/tests/resources/test.pdf")

        arch_z_count_old = Akce.objects.count()
        self.goToAddress("/projekt/detail/C-202401502")

        self.ElementClick(By.CSS_SELECTOR, ".card:nth-child(6) .app-fx .material-icons")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "actionSubmitBtn")
        arch_z_count_new = Akce.objects.count()
        self.assertEqual(arch_z_count_old + 1, arch_z_count_new)
        logger.info("ProjektVytvoreniProjektoveAkce.test_023_projekt_vytvori_akci_p_001.end")
