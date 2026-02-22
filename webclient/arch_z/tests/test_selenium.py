import logging
import unittest

from adb.models import VyskovyBod
from arch_z.models import Akce, ArcheologickyZaznam, ExterniOdkaz
from core.constants import AZ_STAV_ARCHIVOVANY, AZ_STAV_ODESLANY, PROJEKT_STAV_ARCHIVOVANY, PROJEKT_STAV_UZAVRENY
from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from dj.models import DokumentacniJednotka
from django.conf import settings
from django.utils.translation import gettext as _
from dokument.models import DokumentCast
from freezegun import freeze_time
from komponenta.models import Komponenta
from nalez.models import NalezObjekt, NalezPredmet
from pian.models import Pian
from projekt.models import Projekt
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger("tests")


class AkceTestClass(BaseSeleniumTestClass):
    __test__ = False

    def go_to_Projekty_vyper(self):
        self.goToAddress("/projekt/vyber?sort=hlavni_katastr&sort=ident_cely")

    def go_to_Akce_zapsat(self):
        self.goToAddress("/arch-z/akce/zapsat")

    def go_to_Akce_vybrat(self):
        self.goToAddress("/arch-z/akce/vyber?zahrnout_projektove=False&sort=hlavni_katastr&sort=ident_cely")

    def draw_polygon(self):
        self.wait(1)
        self.driver.execute_script("""map.setZoom(16); return map.getZoom();""")
        self.wait(2)
        self.ElementClick(By.LINK_TEXT, _("mapa.EditAddPolygon"))
        self.clickAt(self.driver.find_element(By.ID, "djMap"), 0, 0)
        self.wait(0.2)
        self.clickAt(self.driver.find_element(By.ID, "djMap"), 0, 20)
        self.wait(0.2)
        self.clickAt(self.driver.find_element(By.ID, "djMap"), 20, 20)
        self.wait(0.2)
        self.clickAt(self.driver.find_element(By.ID, "djMap"), 20, 0)
        self.wait(0.2)
        self.ElementClick(By.LINK_TEXT, _("mapa.EditFinishText"))
        self.wait(0.2)


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceProjektoveAkce(AkceTestClass):
    def test_024_pridani_dokumentacni_jednotky_p_001(self):
        """Test 024 Přidání dokumentační jednotky celek akce (pozitivní scénář 1)

        Test vytvoření dokumentační jednotky typu celek akce u projektové akce ve stavu A1. Scénář končí vytvořením dokumentační jednotky D01 typu celek akce.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projekt je ve stavu P3
            - Projekt obsahuje projektovou akci ve stavu A1, která nemá žádnou dokumentační jednotku.

        TestData:
            - typ: celek akce
            - negativni_jednotka : Ano

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt ve stavu P3 (viz předpoklady)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202110946“ → Vybrat → otevřít projekt
            - Uživatel otevře akci ve stavu A1 (C-202110946A).
            - Kliknout na tlačítko “Přidat dokumentační jednotku”
            - Zvolit typ DJ “celek akce”
            - Zvolit typ Negativní jednotka “ano”
            - Kliknout na “uložit”

        Expected:
            - U akce bude vytvořena DJ typu “celek akce” (v databázi je o jednu DJ více).
        """
        logger.info("AkceProjektoveAkce.test_024_pridani_dokumentacni_jednotky_p_001.start")

        self.login()
        self.createFedoraRecord("C-202307816")
        self.uploadFileToFedora(592645, "projekt/tests/resources/test.pdf")
        self.go_to_Projekty_vyper()

        count_old = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202307816A").count()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202307816")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202307816")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDjSubmitButton")

        self.assertNotEqual(
            self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202307816A_D01 > strong"), None
        )
        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202307816A").count()

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceProjektoveAkce.test_024_pridani_dokumentacni_jednotky_p_001.end")

    def test_034_pridani_dokumentacni_jednotky_n_001(self):
        """Test 034 Přidání dokumentační jednotky celek akce (negativní scénář 1)

        Test vytvoření dokumentační jednotky typu celek akce u projektové akce ve stavu A1. Scénář končí nevytvořením dokumentační jednotky D01 typu celek akce.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projekt je ve stavu P3
            - Projekt obsahuje projektovou akci ve stavu A1, která nemá žádnou dokumentační jednotku.

        TestData:
            Akce C-202401502A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt ve stavu P3 (číslo projektu)
            - Projekty → Vybrat → Filtr → ID obsahuje „číslo projektu“ → Vybrat → otevřít projekt
            - Uživatel otevře akci ve stavu A1 (číslo akce).
            - Kliknout na tlačítko “Přidat dokumentační jednotku”
            - Zvolit typ DJ - ponechat nevyplněno
            - Zvolit typ Negativní jednotka “ano”
            - Kliknout na “uložit změny”

        Expected:
            -  U akce nebude vytvořena DJ typu “celek akce” (v databázi není o jednu DJ více).
        """
        logger.info("AkceProjektoveAkce.test_034_pridani_dokumentacni_jednotky_n_001.start")
        self.login()
        self.createFedoraRecord("C-202401502")
        self.uploadFileToFedora(643547, "projekt/tests/resources/test.pdf")
        self.go_to_Projekty_vyper()
        # ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        count_old = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202401502A").count()

        self.ElementClick(By.CSS_SELECTOR, ".btn > .me-1")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_stav .filter-option-inner-inner")
        self.ElementClick(
            By.XPATH, "//span[contains(.,'" + _("projekt.models.projekt.states.zahajenVTerenu.label") + "')]"
        )
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202401502")

        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        # self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        # self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")

        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "newDjSubmitButton")
        except Exception:
            pass

        # self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401502A_D01 > strong"), None)
        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202401502A").count()

        self.assertEqual(count_old, count_new)
        logger.info("AkceProjektoveAkce.test_034_pridani_dokumentacni_jednotky_n_001.end")

    def test_035_pridani_dokumentacni_jednotky_p_002(self):
        """Test 035 Přidání dokumentační jednotky část akce (pozitivní scénář 2)

        Test vytvoření dokumentační jednotky typu část akce u projektové akce ve stavu A1. Scénář končí vytvořením dokumentační jednotky D02 typu část akce.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projekt je ve stavu P3
            - Projekt obsahuje projektovou akci ve stavu A1, která  má dokumentační jednotku D01 typu celkem akce.

        TestData:
            C-202309552A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt ve stavu P3 (M-202400005)
            - Projekty → Vybrat → Filtr → ID obsahuje „M-202400005“ → Vybrat → otevřít projekt
            - Uživatel otevře akci ve stavu A1 (M-202400005A).
            - Kliknout na tlačítko “Přidat dokumentační jednotku”
            - Zvolit typ DJ “část akce”
            - Zvolit typ Negativní jednotka “ano”
            - Kliknout na “uložit změny”

        Expected:
            - U akce bude vytvořena DJ D02 typu “část akce” (v databázi je o jednu DJ více).
        """
        logger.info("AkceProjektoveAkce.test_035_pridani_dokumentacni_jednotky_p_002.start")
        self.login()
        self.createFedoraRecord("C-202309552")
        self.uploadFileToFedora(605456, "projekt/tests/resources/test.pdf")
        self.go_to_Projekty_vyper()
        # ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        count_old = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202309552")
        self.ElementClick(By.ID, "buttonVybrat")

        self.ElementClick(By.LINK_TEXT, "C-202309552")

        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        # self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        # self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDjSubmitButton")

        self.assertNotEqual(
            self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202309552A_D02 > strong"), None
        )
        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceProjektoveAkce.test_035_pridani_dokumentacni_jednotky_p_002.end")

    def test_036_pridani_dokumentacni_jednotky_n_002(self):
        """Test 036 Přidání dokumentační jednotky část akce (negativní scénář 2)

        Test vytvoření dokumentační jednotky typu část akce u projektové akce ve stavu A1. Scénář končí nevytvořením dokumentační jednotky D02 typu část akce.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projekt je ve stavu P3
            - Projekt obsahuje projektovou akci ve stavu A1, která  má dokumentační jednotku D01 typu celkem akce.

        TestData:
            C-202309552

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt ve stavu P3 (C-202309552)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202309552“ → Vybrat → otevřít projekt
            - Uživatel otevře akci ve stavu A1 (C-202309552A).
            - Kliknout na tlačítko “Přidat dokumentační jednotku”
            - Zvolit typ DJ “nevyplněno”
            - Zvolit typ Negativní jednotka “ano”
            - Kliknout na “uložit změny”

        Expected:
            -  U akce nebude vytvořena DJ D02 typu “část akce” (v databázi není o jednu DJ více).
        """
        logger.info("AkceProjektoveAkce.test_036_pridani_dokumentacni_jednotky_n_002.start")
        self.login()
        self.createFedoraRecord("C-202309552")
        self.uploadFileToFedora(605456, "projekt/tests/resources/test.pdf")
        self.go_to_Projekty_vyper()
        # ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        count_old = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202309552")
        self.ElementClick(By.ID, "buttonVybrat")

        self.ElementClick(By.LINK_TEXT, "C-202309552")

        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.ID, "button-add-dj")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-1-0")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")

        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "newDjSubmitButton")
        except Exception:
            pass

        # self.assertNotEqual(self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202309552A_D02 > strong"), None)
        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()

        self.assertEqual(count_old, count_new)
        logger.info("AkceProjektoveAkce.test_036_pridani_dokumentacni_jednotky_n_002.end")

    def test_037_pridani_komponenty_dokumentacni_jednotky_p_001(self):
        """Test 037 Přidání komponenty k dokumentační jednotce celek akce (pozitivní scénář 1)

        Test vytvoření komponenty u dokumentační jednotky typu celek akce u projektové akce ve stavu A1. Scénář končí vytvořením komponenty K001 u dokumentační jednotky D01.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projekt je ve stavu P3
            - Projekt obsahuje projektovou akci ve stavu A1, která  má dokumentační jednotku D01 typu celkem akce, která je pozitivní.

        TestData:
            C-202309027

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt ve stavu P3 (M-202400004)
            - Projekty → Vybrat → Filtr → ID obsahuje „M-202400004“ → Vybrat → otevřít projekt
            - Uživatel otevře akci ve stavu A1 (M-202400004A).
            - Kliknout na dokumentační jednotku D01
            - Kliknout na “Další volby” a zvolit ”Přidat komponentu”.
            - Zvolit Období “únětická k.”
            - Zvolit Areál “sídliště nesp.”.
            - Kliknout na “uložit změny”

        Expected:
            -  U DJ D01 bude vytvořena nová komponenta K001, v databázi bude o jednu komponentu více.
        """
        logger.info("AkceProjektoveAkce.test_037_pridani_komponenty_dokumentacni_jednotky_p_001.start")
        self.login()
        self.createFedoraRecord("C-202309027")
        self.uploadFileToFedora(601604, "projekt/tests/resources/test.pdf")
        self.uploadFileToFedora(601608, "projekt/tests/resources/test.pdf")
        self.go_to_Projekty_vyper()  # C-202309027
        # ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        # count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()
        count_old = Komponenta.objects.filter(
            komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202309027A-D01"
        ).count()

        self.ElementClick(By.ID, "buttonFiltr")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202309027")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202309027")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202309027A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_C-202309027A-D01 .btn-group:nth-child(1) .material-icons")
        self.ElementClick(
            By.LINK_TEXT, _("arch_z.templates.arch_z.dj.partials.dj_update.editButtons.pridatKomponentu.label")
        )
        self.ElementClick(By.CSS_SELECTOR, "#div_id_obdobi .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("ún")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_jistota .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-2-0")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-3 > .text")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createCompotSubmitButton")

        self.assertNotEqual(self.driver.find_element(By.ID, "el_komponenta_C_202309027A_K001"), None)
        count_new = Komponenta.objects.filter(
            komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202309027A-D01"
        ).count()

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceProjektoveAkce.test_037_pridani_komponenty_dokumentacni_jednotky_p_001.end")

    def test_040_pridani_komponenty_dokumentacni_jednotky_n_001(self):
        """Test 040 Přidání komponenty k dokumentační jednotce celek akce (negativní scénář 1)

        Test vytvoření komponenty u dokumentační jednotky typu celek akce u projektové akce ve stavu A1. Scénář končí nevytvořením komponenty K001 u dokumentační jednotky D01.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projekt je ve stavu P3
            - Projekt obsahuje projektovou akci ve stavu A1, která  má dokumentační jednotku D01 typu celkem akce, která je pozitivní.

        TestData:
            C-202309027

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt ve stavu P3 (C-202309027)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202309027“ → Vybrat → otevřít projekt
            - Uživatel otevře akci ve stavu A1 (C-202309027A).
            - Kliknout na dokumentační jednotku D01
            - Kliknout na “Další volby” a zvolit ”Přidat komponentu”.
            - Zvolit Období “únětická k.”
            - Zvolit Areál “zůstane nevyplněno”.
            - Kliknout na “uložit změny”

        Expected:
            -  U DJ D01 nebude vytvořena nová komponenta K001, v databázi bude o jednu komponentu více.
        """
        logger.info("AkceProjektoveAkce.test_040_pridani_komponenty_dokumentacni_jednotky_n_001.start")
        self.login()
        self.createFedoraRecord("C-202309027")
        self.uploadFileToFedora(601604, "projekt/tests/resources/test.pdf")
        self.uploadFileToFedora(601608, "projekt/tests/resources/test.pdf")
        self.go_to_Projekty_vyper()  # C-202309027
        # ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        # count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()
        count_old = Komponenta.objects.filter(
            komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202309027A-D01"
        ).count()

        self.ElementClick(By.ID, "buttonFiltr")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202309027")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202309027")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202309027A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_C-202309027A-D01 .btn-group:nth-child(1) .material-icons")
        self.ElementClick(
            By.LINK_TEXT, _("arch_z.templates.arch_z.dj.partials.dj_update.editButtons.pridatKomponentu.label")
        )
        self.ElementClick(By.CSS_SELECTOR, "#div_id_obdobi .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("ún")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_jistota .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-2-0")
        # self.ElementClick(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner")
        # self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-3 > .text")

        with WaitForPageLoad(self.driver, 5):
            self.ElementClick(By.ID, "createCompotSubmitButton")

        # self.assertNotEqual(self.driver.find_element(By.ID, "el_komponenta_C_202309027A_K001"), None)
        self.assertEqual(len(self.driver.find_elements(By.ID, "el_komponenta_C_202309027A_K001")), 0)
        count_new = Komponenta.objects.filter(
            komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202309027A-D01"
        ).count()

        self.assertEqual(count_old, count_new)
        logger.info("AkceProjektoveAkce.test_040_pridani_komponenty_dokumentacni_jednotky_n_001.end")

    def test_041_pridani_objektu_komponente_p_001(self):
        """Test 041  Přidání objektu k pozitivní komponentě (pozitivní scénář 1)

        Test vytvoření objektu u komponenty připojené k dokumentační jednotce projektové akce. Scénář končí vytvořením objektu u komponenty K001 u dokumentační jednotky D01.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projekt je ve stavu P3
            - Projekt obsahuje projektovou akci ve stavu A1, která  má dokumentační jednotku D01 typu celkem akce, která je pozitivní a obsahuje komponentu K001.

        TestData:
            C-202004814

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt ve stavu P3 (C-202004814)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202004814“ → Vybrat → otevřít projekt
            - Uživatel otevře akci ve stavu A1 (C-202004814A).
            - Kliknout na komponentu K001 u dokumentační jednotky D01
            - V sekci Nálezy a Objekty zvolit Druh “(polo)zemnice”.
            - V sekci Nálezy a Objekty vyplnit Počet “1”.
            - Kliknout na “Uložit změny”

        Expected:
            - U komponenty K001 bude vytvořen nový objekt. V databázi bude o jeden objekt více.
        """
        logger.info("AkceProjektoveAkce.test_041_pridani_objektu_komponente_p_001.start")
        self.login()
        self.createFedoraRecord("C-202004814")
        self.uploadFileToFedora(253674, "projekt/tests/resources/test.pdf")
        self.go_to_Projekty_vyper()
        count_old = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202004814A-D01"
        ).count()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202004814")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202004814")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.ID, "el_komponenta_C_202004814A_K001")
        # with WaitForPageLoad(self.driver):
        self.ElementClick(By.CSS_SELECTOR, "#div_id_C-202004814A-K001_o-0-druh .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-7-6 > .text")
        self.ElementClick(By.ID, "id_C-202004814A-K001_o-0-pocet")
        self.driver.find_element(By.ID, "id_C-202004814A-K001_o-0-pocet").send_keys("1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")

        count_new = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202004814A-D01"
        ).count()
        self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, ".badge.badge-primary.badge-pill").text, "1")
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceProjektoveAkce.test_041_pridani_objektu_komponente_p_001.end")

    def test_042_pridani_predmetu_komponente_p_001(self):
        """Test 042 Přidání předmětu k pozitivní komponentě (pozitivní scénář 1)

        Test vytvoření předmětu u komponenty připojené k dokumentační jednotce projektové akce. Scénář končí vytvořením předmětu u komponenty K001 u dokumentační jednotky D01.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projekt je ve stavu P3
            - Projekt obsahuje projektovou akci ve stavu A1, která  má dokumentační jednotku D01 typu celkem akce, která je pozitivní a obsahuje komponentu K001.

        TestData:
            C-202004814

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt ve stavu P3 (C-202004814)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202004814“ → Vybrat → otevřít projekt
            - Uživatel otevře akci ve stavu A1 (C-202004814A).
            - Kliknout na komponentu K001 u dokumentační jednotky D01
            - V sekci Nálezy a Předměty zvolit Druh “džbán”.
            - V sekci Nálezy a Předměty zvolit Specifikace “keramika nesp.”.
            - V sekci Nálezy a Předměty vyplnit Počet “1”.
            - Kliknout na “Uložit změny”

        Expected:
            - U komponenty K001 bude vytvořen nový objekt. V databázi bude o jeden objekt více.
        """
        logger.info("AkceProjektoveAkce.test_042_pridani_predmetu_komponente_p_001.start")
        self.login()
        self.createFedoraRecord("C-202004814")
        self.uploadFileToFedora(253674, "projekt/tests/resources/test.pdf")
        self.go_to_Projekty_vyper()
        count_old = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202004814A-D01"
        ).count()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202004814")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202004814")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "el_komponenta_C_202004814A_K001")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_C-202004814A-K001_p-0-druh .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-15-82 > .text")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_C-202004814A-K001_p-0-specifikace .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-16-15 > .text")

        self.ElementClick(By.ID, "id_C-202004814A-K001_p-0-pocet")
        self.driver.find_element(By.ID, "id_C-202004814A-K001_p-0-pocet").send_keys("1")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")

        count_new = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202004814A-D01"
        ).count()
        self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, ".badge.badge-primary.badge-pill").text, "1")
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceProjektoveAkce.test_042_pridani_predmetu_komponente_p_001.end")

    def test_043_smazani_objektu_komponente_p_001(self):
        """Test 043 Smazání objektu u projektové akce (pozitivní scénář 1)

        Test smazání objektu u komponenty připojené k dokumentační jednotce projektové akce. Scénář končí smazáním objektu.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A1
            - Dokumentační jednotka D01
            - Komponenta K001
            - Objekt “jáma kůlová/sloupová” připojený ke komponentě K001

        TestData:
            X-C-91277520A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projektovou akci ve stavu A1 (X-C-91277520A)
            - Projekty → Vybrat → Filtr → ID obsahuje „X-C-91277520“ → Vybrat → otevřít projektovou akci X-C-91277520A
            - Kliknout na komponentu K001 u dokumentační jednotky D01
            - V sekci Nálezy a Objekty u položky “jáma kůlová/sloupová” kliknout na možnost “odstranit”
            - Volbu potvrdit

        Expected:
            -  U komponenty K001 bude odebrána položka typu objekt. V databázi bude o jeden objekt méně. Oznámení “Záznam byl úspěšně smazán”
        """
        logger.info("AkceProjektoveAkce.test_043_smazani_objektu_komponente_p_001.start")
        self.login()
        self.createFedoraRecord("X-C-TX-202107588")
        self.uploadFileToFedora(339739, "projekt/tests/resources/test.pdf")
        count_old = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-91277520A-D01"
        ).count()
        self.go_to_Akce_vybrat()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-91277520A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-91277520A")
        self.ElementClick(By.ID, "el_komponenta_X_C_91277520A_K001")
        self.ElementClick(By.CSS_SELECTOR, "#objekt-smazat-101441 > .material-icons")
        self.wait(self.wait_interval)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        count_new = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-91277520A-D01"
        ).count()
        # self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, ".badge.badge-primary.badge-pill").text,'1')
        self.assertEqual(count_old, count_new + 1)
        logger.info("AkceProjektoveAkce.test_043_smazani_objektu_komponente_p_001.end")

    def test_044_smazani_predmetu_komponente_p_001(self):
        """Test 044 Smazání předmětu u projektové akce (pozitivní scénář 1)

        Test smazání předmětu u komponenty připojené k dokumentační jednotce projektové akce. Scénář končí smazáním předmětu.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A1
            - Dokumentační jednotka D01
            - Komponenta K001
            - Předmět “doklad umění/kultu” připojený ke komponentě K001

        TestData:
            X-C-91277520A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projektovou akci ve stavu A1 (M-202400926A)
            - Projekty → Vybrat → Filtr → ID obsahuje „M-202400926“ → Vybrat → otevřít projektovou akci M-202400926A
            - Kliknout na komponentu K001 u dokumentační jednotky D01
            - V sekci Nálezy a Předměty u položky “doklad umění/kultu” kliknout na možnost “odstranit”
            - Volbu potvrdit

        Expected:
            -  U komponenty K001 bude odebrána položka typu předmět. V databázi bude o jeden předmět méně. Oznámení “Záznam byl úspěšně smazán”
        """
        logger.info("AkceProjektoveAkce.test_044_smazani_predmetu_komponente_p_001.start")
        self.login()
        self.createFedoraRecord("X-C-TX-202107588")
        self.uploadFileToFedora(339739, "projekt/tests/resources/test.pdf")
        count_old = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-91277520A-D01"
        ).count()

        self.go_to_Akce_vybrat()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-91277520A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-91277520A")
        self.ElementClick(By.ID, "el_komponenta_X_C_91277520A_K001")

        self.ElementClick(By.CSS_SELECTOR, "#objekt-smazat-161256 > .material-icons")
        self.wait(1)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        count_new = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-91277520A-D01"
        ).count()
        # self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, ".badge.badge-primary.badge-pill").text,'1')
        self.assertEqual(count_old, count_new + 1)
        logger.info("AkceProjektoveAkce.test_044_smazani_predmetu_komponente_p_001.end")

    # C-202207641A
    def test_079_pridani_dokumentu_projektove_akci_p_001(self):
        """Test 079 Přidání dokumentu (pozitivní scénář 1)

        Test přidání dokumentu k projektové akci. Scénář končí vytvořením záznamu dokumentu a jeho připojením k projektové akci.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projekt je ve stavu P3
            - Projekt obsahuje projektovou akci ve stavu A1.

        TestData:
            C-202207641A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt ve stavu P3 (C-202207641A)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202207641A“ → Vybrat → otevřít projekt
            - Uživatel otevře akci (C-202207641A).
            - V tabulce Dokumenty kliknout na tlačítko “Přidat dokument”
            - Uživatel vyplní povinné údaje ve formuláři Dokument
            - Klikne na tlačítko Zapsat

        Expected:
            - Bude vytvořen nový záznam typu dokument (v databázi je o jeden dokument více). Tento dokument je připojený k projektové akci C-202207641A
        """
        logger.info("AkceProjektoveAkce.test_079_pridani_dokumentu_projektove_akci_p_001.start")
        self.login("archeolog")
        self.createFedoraRecord("C-202207641")
        self.uploadFileToFedora(435547, "projekt/tests/resources/test.pdf")
        count_old = DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="C-202207641A").count()
        self.goToAddress("/id/C-202207641")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.ID, "others_doc")
        self.ElementClick(By.LINK_TEXT, _("dokument.templates.dokument_table.pridatNovyDokument.label"))
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Absolon")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vzniku")
        self.driver.find_element(By.ID, "id_rok_vzniku").send_keys("2023")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(
            "Moravské zemské muzeum"
        )
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("Investorsk")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("di")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.ID, "id_popis")
        self.driver.find_element(By.ID, "id_popis").send_keys("test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("anonym")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")

        count_new = DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="C-202207641A").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceProjektoveAkce.test_079_pridani_dokumentu_projektove_akci_p_001.end")

    def test_080_pridani_existujiciho_dokumentu_projektove_akci_p_001(self):
        """Test 080 Připojení existujícího dokumentu (pozitivní scénář 1)

        Test připojení existujícího dokumentu k projektové akci. Scénář končí vytvořením vazby mezi dokumentem a projektovou akcí.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projekt je ve stavu P3
            - Projekt obsahuje projektovou akci ve stavu A1.

        TestData:
            C-202207641
            M-TX-194300151

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt ve stavu P3 (C-202207641)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202207641“ → Vybrat → otevřít projekt
            - Uživatel otevře akci (C-202207641A).
            - V tabulce Dokumenty kliknout na tlačítko “Připojit existující dokument”
            - Uživatel vyhledá dokument “M-TX-194300114”
            - Klikne na tlačítko Připojit

        Expected:
            - Je vytvořena vazba mezi dokumentem a projektovou akcí C-202207641A
        """
        logger.info("AkceProjektoveAkce.test_080_pridani_existujiciho_dokumentu_projektove_akci_p_001.start")
        self.login("archeolog")
        self.createFedoraRecord("C-202207641")
        self.uploadFileToFedora(435547, "projekt/tests/resources/test.pdf")
        self.createFedoraRecord("M-TX-194300151")
        self.uploadFileToFedora(534769, "projekt/tests/resources/test.pdf")
        count_old = DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="C-202207641A").count()
        self.go_to_Projekty_vyper()

        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202207641")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202207641")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.ID, "others_doc")
        self.ElementClick(By.ID, "dokument-pripojit")
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("M-TX-194300151")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        count_new = DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="C-202207641A").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceProjektoveAkce.test_080_pridani_existujiciho_dokumentu_projektove_akci_p_001.end")

    def test_081_pridani_existujiciho_dokumentu_z_projektu_projektove_akci_p_001(self):
        """Test 081 Připojení existujícího dokumentu z projektu (pozitivní scénář 1)

        Test připojení existujícího dokumentu z projektu k projektové akci. Scénář končí vytvořením vazby mezi dokumentem a projektovou akcí.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projekt je ve stavu P3
            - Projekt obsahuje projektovou akci s připojeným dokumentem
            - Projekt obsahuje další projektovou akci ve stavu A1

        TestData:
            C-202401979B

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt ve stavu P3 (M-202400928)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202401979“ → Vybrat → otevřít projekt
            - Uživatel otevře akci (C-202401979B).
            - V tabulce Dokumenty kliknout na tlačítko “Připojit existující dokument z projektu”
            - Uživatel vyhledá dokument “...”
            - Zaškrtne políčko Vybrat a klikne na tlačítko Připojit

        Expected:
            - Je vytvořena vazba mezi dokumentem a projektovou akcí C-202401979B
        """
        logger.info("AkceProjektoveAkce.test_081_pridani_existujiciho_dokumentu_z_projektu_projektove_akci_p_001.start")
        self.createFedoraRecord("C-202401979")
        self.uploadFileToFedora(646252, "projekt/tests/resources/test.pdf")
        self.login("archeolog")

        count_old = DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="C-202401979B").count()
        self.go_to_Projekty_vyper()

        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202401979")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202401979")
        self.ElementClick(By.CSS_SELECTOR, ".app-card-akce > .card-body")
        self.ElementClick(By.CSS_SELECTOR, "tr:nth-child(2) a")
        self.ElementClick(By.ID, "others_doc")
        self.ElementClick(By.ID, "dokument-pripojit-z-projektu")
        self.ElementClick(By.NAME, "dokument")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        count_new = DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="C-202401979B").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceProjektoveAkce.test_081_pridani_existujiciho_dokumentu_z_projektu_projektove_akci_p_001.end")

    def test_084_pripojeni_externiho_zdroje_projektove_akci_p_001(self):
        """Test 084 Připojení externího zdroje k projektové akci (pozitivní scénář 1)

        Test připojení externího zdroje k projektové akci. Scénář končí vytvořením vazby mezi samostatnou akcí a externím zdrojem.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A1.

        TestData:
            C-202301164
            X-BIB-1295324

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202301164)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202301164“ → Vybrat → otevřít projekt → otevřít akci „C-202301164A“
            - V části “Externí zdroje” kliknout na “připojit externí zdroj”
            - Uživatel vyhledá identifikátor “X-BIB-1295324”
            - Klikne na tlačítko Připojit

        Expected:
            -  Je vytvořena vazba mezi projektovou akcí externím zdrojem  „X-BIB-1295324“
        """
        logger.info("AkceProjektoveAkce.test_084_pripojeni_externiho_zdroje_projektove_akci_p_001.start")
        self.login("archeolog")
        self.createFedoraRecord("C-202301164")
        self.uploadFileToFedora(553894, "projekt/tests/resources/test.pdf")
        self.uploadFileToFedora(553892, "projekt/tests/resources/test.pdf")
        self.uploadFileToFedora(553893, "projekt/tests/resources/test.pdf")
        count_old = ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely="C-202301164A").count()
        self.go_to_Projekty_vyper()
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202301164")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202301164")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#eo-pripojit-do-az > .material-icons")
        self.ElementClick(By.ID, "select2-id_ez-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("X-BIB-1295324")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.ElementClick(By.CSS_SELECTOR, "#eo-pripojit-do-az > .material-icons")
        self.ElementClick(By.ID, "select2-id_ez-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("X-BIB-1295325")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        count_new = ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely="C-202301164A").count()
        self.assertEqual(count_old + 2, count_new)
        logger.info("AkceProjektoveAkce.test_084_pripojeni_externiho_zdroje_projektove_akci_p_001.end")

    def test_086_vytvoreni_PIAN_projektove_akce_p_001(self):
        """Test 086 Vytvoření PIAN u projektové akce (pozitivní scénář 1)

        Test vytvoření PIAN k projektové akci.Scénář končí vytvořením nového PIAN připojeného k DJ 01 u projektové akce.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A1 s dokumentační jednotkou D01, která nemá připojen PIAN.

        TestData:
            C-202401980

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202401980)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202401980“ → Vybrat → otevřít projekt → otevřít akci „C-202401980“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
            - V části “Dokumentační jednotka C-202401980-D01” kliknout na Další volby → PIAN - vytvořit → vytvořit geometrii PIAN (jak vyřešit v testu?)
            - V části nový PIAN nastavit přesnost na hodnotu “odchylka jednotky metrů”

        Expected:
            - U dokumentační jednotky “C-202401980-D01” je připojen nový PIAN.
        """
        logger.info("AkceProjektoveAkce.test_086_vytvoreni_PIAN_projektove_akce_p_001.start")
        self.login("archeolog")
        self.createFedoraRecord("C-202401980")
        self.uploadFileToFedora(646253, "projekt/tests/resources/test.pdf")
        pian_old = DokumentacniJednotka.objects.filter(ident_cely="C-202401980A-D01")[0].pian
        self.assertEqual(pian_old, None)

        self.go_to_Projekty_vyper()
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202401980")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202401980")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401980A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_C-202401980A-D01 .btn-group:nth-child(1) .material-icons")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "show_menu_pian_new_id")
        self.draw_polygon()
        self.ElementClick(By.CSS_SELECTOR, ".filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createPianSubmitButton")

        pian_new = DokumentacniJednotka.objects.filter(ident_cely="C-202401980A-D01")[0].pian

        self.assertNotEqual(pian_new, None)
        logger.info("AkceProjektoveAkce.test_086_vytvoreni_PIAN_projektove_akce_p_001.end")

    def test_087_editace_PIAN_projektove_akce_p_001(self):
        """Test 087 Editace PIAN u projektové akce (pozitivní scénář 1)

        Test editace PIAN u projektové akci. Scénář končí novu geometrií PIAN u dokumentační jednotky DJ 01 u projektové akce.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A1 s dokumentační jednotkou D01, která má připojen nepotvrzený PIAN.

        TestData:
            N-1212-000000002
            C-202401981A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202401981A)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202401981A“ → Vybrat → otevřít projekt → otevřít akci „C-202401981A“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
            - V části “Dokumentační jednotka C-202401981A-D01” kliknout na Další volby → PIAN - upravit → upravit geometrii PIAN

        Expected:
            - U dokumentační jednotky “C-202401981A-D01” je upravena geometrie připojeného PIAN.
        """
        logger.info("AkceProjektoveAkce.test_087_editace_PIAN_projektove_akce_p_001.start")
        self.login("archeolog")
        self.createFedoraRecord("C-202401981")
        self.uploadFileToFedora(646254, "projekt/tests/resources/test.pdf")
        pian_old = str(DokumentacniJednotka.objects.filter(ident_cely="C-202401981A-D01")[0].pian.geom)

        self.go_to_Projekty_vyper()
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202401981")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202401981")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401981A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "pian-upravit-N-1212-000000002")
        self.draw_polygon()
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editPianButton")

        pian_new = str(DokumentacniJednotka.objects.filter(ident_cely="C-202401981A-D01")[0].pian.geom)

        self.assertNotEqual(pian_new, pian_old)
        logger.info("AkceProjektoveAkce.test_087_editace_PIAN_projektove_akce_p_001.end")

    def test_088_smazani_PIAN_projektove_akce_p_001(self):
        """Test 088 Smazání PIAN u projektové akce (pozitivní scénář 1)

        Test smazání PIAN u projektové akci. Scénář končí smazáním nepotvrzeného PIAN u dokumentační jednotky D01 u projektové akce.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A1 s dokumentační jednotkou D01, která má připojen nepotvrzený PIAN.

        TestData:
            C-202401981A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202401981A)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202401981“ → Vybrat → otevřít projekt → otevřít akci „C-202401981A“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
            - V části “Dokumentační jednotka C-202401981A-D01” kliknout na Další volby → PIAN - odpojit → v dialogovém okně “Odpojení PIAN” kliknout na tlačítko “Odpojit”

        Expected:
            - U dokumentační jednotky “C-202401981A-D01” je smazán nepotvrzený PIAN, v databázi je o 1 PIAN méně.
        """
        logger.info("AkceProjektoveAkce.test_088_smazani_PIAN_projektove_akce_p_001.start")
        self.login("archeolog")
        self.createFedoraRecord("C-202401981")
        self.uploadFileToFedora(646254, "projekt/tests/resources/test.pdf")
        pian = DokumentacniJednotka.objects.filter(ident_cely="C-202401981A-D01")[0].pian
        self.assertNotEqual(pian, None)

        self.go_to_Projekty_vyper()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202401981")
        self.ElementClick(By.ID, "buttonVybrat")

        self.ElementClick(By.LINK_TEXT, "C-202401981")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401981A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")
        self.ElementClick(By.ID, "pian-odpojit-N-1212-000000002")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        pian = DokumentacniJednotka.objects.filter(ident_cely="C-202401981A-D01")[0].pian
        self.assertEqual(pian, None)
        logger.info("AkceProjektoveAkce.test_088_smazani_PIAN_projektove_akce_p_001.end")

    def test_089_pripojeni_PIAN_projektove_akce_p_001(self):
        """Test 089 Připojení PIAN z mapy u projektové akce (pozitivní scénář 1)

        Test připojení PIAN z mapy u projektové akci. Scénář končí připojením existujícího PIAN k dokumentační jednotce D01 u projektové akce.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A1 s dokumentační jednotkou D01, která nemá připojen PIAN.

        TestData:
            C-202401980

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202401980A)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202401980“ → Vybrat → otevřít projekt → otevřít akci „C-202401980A“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
            - V části “Dokumentační jednotka C-202401980A-D01” kliknout na Další volby → PIAN - připojit z mapy→ kliknout na PIAN XXX  → kliknout na “Uložit změny”

        Expected:
            - U dokumentační jednotky “C-202401980A-D01” bude vytvořena vazba s PIAN „XXX”.
        """
        logger.info("AkceProjektoveAkce.test_089_pripojeni_PIAN_projektove_akce_p_001.start")
        self.login("archeolog")
        self.createFedoraRecord("C-202401980")
        self.uploadFileToFedora(646253, "projekt/tests/resources/test.pdf")
        pian_old = DokumentacniJednotka.objects.filter(ident_cely="C-202401980A-D01")[0].pian
        self.assertEqual(pian_old, None)

        self.go_to_Projekty_vyper()
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202401980")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202401980")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401980A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_C-202401980A-D01 .btn-group:nth-child(1) .material-icons")
        self.ElementClick(By.ID, "show_menu_pian_from_map_id")
        self.wait(0.5)
        self.driver.execute_script("""map.setView([50.357377039,  13.795522698],19)""")
        js = """
const done = arguments[arguments.length - 1];
const deadline = Date.now() + 10000;

(function tick() {
  const layers = (window.poi_pian && poi_pian._layers) ? Object.values(poi_pian._layers) : [];
  const first = layers[0];
   console.log(layers[0]);
  if (window.L && window.map && first && typeof first.fire === "function") {
    const latlng = L.latLng(50.357377039, 13.795522698);
    console.log("log1");
    first.fire("click", {
      latlng,
      layerPoint: map.latLngToLayerPoint(latlng),
      containerPoint: map.latLngToContainerPoint(latlng),
      originalEvent: {
        clientX: map.latLngToContainerPoint(latlng).x,
        clientY: map.latLngToContainerPoint(latlng).y
      }
    });
    return done(true);
  }

  if (Date.now() > deadline) return done(false);
  setTimeout(tick, 50);
})();
"""
        self.driver.set_script_timeout(10)
        self.driver.execute_async_script(js)
        self.wait(0.5)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editDjSubmitButton")

        pian_new = DokumentacniJednotka.objects.filter(ident_cely="C-202401980A-D01")[0].pian

        self.assertNotEqual(pian_new, None)
        logger.info("AkceProjektoveAkce.test_089_pripojeni_PIAN_projektove_akce_p_001.end")

    # 90 C-202307816A 202007232A
    def test_090_odpojeni_PIAN_projektove_akce_p_001(self):
        """Test 090 Odpojení potvrzeného PIAN u projektové akce (pozitivní scénář 1)

        Test odpojení potvrzeného PIAN projektové akci. Scénář končí odpojením existujícího PIAN od dokumentační jednotky D01 u projektové akce.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A1 s dokumentační jednotkou D01, která má připojen potvrzený PIAN.

        TestData:
            C-202007232A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202007232A)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202007232“ → Vybrat → otevřít projekt → otevřít akci „C-202007232A“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
            - V části “Dokumentační jednotka C-202007232A-D01” kliknout na Další volby → PIAN - odpojit → V dialogovém okně “Odpojení PIAN” kliknout na “Odpojit”

        Expected:
            - U dokumentační jednotky “C-202007232A-D01” zanikne vazba s PIAN „XXX”.
        """
        logger.info("AkceProjektoveAkce.test_090_odpojeni_PIAN_projektove_akce_p_001.start")
        self.login("archeolog")
        self.createFedoraRecord("C-202007232")
        self.uploadFileToFedora(264976, "projekt/tests/resources/test.pdf")
        self.uploadFileToFedora(265018, "projekt/tests/resources/test.pdf")
        pian = DokumentacniJednotka.objects.filter(ident_cely="C-202007232A-D01")[0].pian
        self.assertNotEqual(pian, None)

        self.go_to_Projekty_vyper()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202007232")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202007232")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202007232A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")
        self.ElementClick(By.ID, "pian-odpojit-P-1221-100589")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        pian = DokumentacniJednotka.objects.filter(ident_cely="C-202007232A-D01")[0].pian
        self.assertEqual(pian, None)
        logger.info("AkceProjektoveAkce.test_090_odpojeni_PIAN_projektove_akce_p_001.end")

    # C-202309724
    def test_091_import_PIAN_projektove_akce_p_001(self):
        """Test 091 Import PIAN k projektové akci (pozitivní scénář 1)

        Test importu PIAN k projektové akci. Scénář končí vytvořením PIAN u dokumentační jednotky D01 u projektové akce.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A1 s dokumentační jednotkou D01, která nemá připojen PIAN.

        TestData:
            geom.csv
            C-202309724

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202309724A)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202309724“ → Vybrat → otevřít projekt → otevřít akci „C-202309724A“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
            - V části “Dokumentační jednotka C-202309724A-D01” kliknout na Další volby → PIAN - importovat → V dialogovém okně “Importovat PIAN” vložit soubor CSV geom.csv a kliknout na Dokončit
            - V části “Nový PIAN” vybrat přesnost “odchylka jednotky metrů” a kliknout “uložit změny”

        Expected:
            - U dokumentační jednotky “C-202309724A-D01” bude připojen nový PIAN „XXX”. V databázi bude o jeden PIAN více (vznikne vazba s D01).
        """
        logger.info("AkceProjektoveAkce.test_091_import_PIAN_projektove_akce_p_001.start")
        self.login("archeolog")
        pian = DokumentacniJednotka.objects.filter(ident_cely="C-202309724A-D01")[0].pian
        self.assertEqual(pian, None)
        self.goToAddress("/arch-z/akce/detail/C-202309724A/dj/C-202309724A-D01")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_C-202309724A-D01 .btn-group:nth-child(1) .material-icons")
        self.ElementClick(By.CSS_SELECTOR, ".show > .dropdown-item:nth-child(2)")
        self.upload_file("arch_z/tests/resources/geom.csv", "geom.csv", "application/csv")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createPianSubmitButton")

        pian = DokumentacniJednotka.objects.filter(ident_cely="C-202309724A-D01")[0].pian

        self.assertNotEqual(pian, None)
        logger.info("AkceProjektoveAkce.test_091_import_PIAN_projektove_akce_p_001.end")

        # 202005190A

    def test_092_editace_PIAN_projektove_akce_importem_p_001(self):
        """Test 092 Editace PIAN k projektové akci importem (pozitivní scénář 1)

        Test editace PIAN k projektové akci importem. Scénář končí upraveným PIAN u dokumentační jednotky D01 u projektové akce.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A1 s dokumentační jednotkou D01, která má připojen nepotvrzený PIAN.

        TestData:
            C-202005190A
            geom.csv

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202005190)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202005190“ → Vybrat → otevřít projekt → otevřít akci „C-202005190A“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
            - V části “Dokumentační jednotka C-202005190A-D01” kliknout na Další volby → PIAN - upravit importem → V dialogovém okně “Importovat PIAN” vložit soubor CSV geom.csv a kliknout na Dokončit
            - V části ““Dokumentační jednotka C-202005190A-D01” kliknout na “uložit změny”

        Expected:
            - U dokumentační jednotky “C-202005190A-D01” bude upravena geometrie PIAN „XXX”.
        """
        logger.info("AkceProjektoveAkce.test_092_editace_PIAN_projektove_akce_importem_p_001.start")
        self.login("archeolog")
        self.createFedoraRecord("C-202005190")
        self.uploadFileToFedora(255492, "projekt/tests/resources/test.pdf")
        pian_old = str(DokumentacniJednotka.objects.filter(ident_cely="C-202005190A-D01")[0].pian.geom)
        self.go_to_Projekty_vyper()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202005190")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202005190")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202005190A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")
        self.ElementClick(By.CSS_SELECTOR, ".show > .dropdown-item:nth-child(2)")
        self.upload_file("arch_z/tests/resources/geom.csv", "geom.csv", "application/csv")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editPianButton")

        pian_new = str(DokumentacniJednotka.objects.filter(ident_cely="C-202005190A-D01")[0].pian.geom)
        self.assertNotEqual(pian_new, pian_old)
        logger.info("AkceProjektoveAkce.test_092_editace_PIAN_projektove_akce_importem_p_001.end")

    def test_093_pripojeni_PIAN_projektove_akce_p_001(self):
        """Test 093 Připojení PIAN k projektové akci podle ID (pozitivní scénář 1)

        Test připojení PIAN k projektové akci podel ID. Scénář končí připojením PIAN podle ID u dokumentační jednotky D01 u projektové akce.

        Role:
            Archivář

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A1 s dokumentační jednotkou D01, která nemá připojen PIAN.

        TestData:
            C-202401980
            P-0134-00000

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202401980A)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202401980“ → Vybrat → otevřít projekt → otevřít akci „C-202401980A“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
            - V části “Dokumentační jednotka C-202401980A-D01” kliknout na Další volby → PIAN - připojit podle ID
            - V části ““Dokumentační jednotka C-202401980A-D01” v poli “PIAN” zadat ID PIAN “P-0134-00000” a kliknout na “uložit změny”

        Expected:
            - U dokumentační jednotky “C-202401980A-D01” bude připojen PIAN „P-0134-00000”. V databázi bude vytvořena vazba mezi PIAN a dokumentační jednotkou “C-202401980A-D01”.
        """
        logger.info("AkceProjektoveAkce.test_093_pripojeni_PIAN_projektove_akce_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-202401980")
        self.uploadFileToFedora(646253, "projekt/tests/resources/test.pdf")
        pian_old = DokumentacniJednotka.objects.filter(ident_cely="C-202401980A-D01")[0].pian
        self.assertEqual(pian_old, None)

        self.go_to_Projekty_vyper()
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202401980")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202401980")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401980A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_C-202401980A-D01 .btn-group:nth-child(1) .material-icons")
        self.ElementClick(By.ID, "pian-pripojit-")
        self.ElementClick(By.ID, "select2-id_C-202401980A-D01-pian-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("P-0134-00000")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editDjSubmitButton")

        pian_new = DokumentacniJednotka.objects.filter(ident_cely="C-202401980A-D01")[0].pian
        self.assertNotEqual(pian_new, None)
        logger.info("AkceProjektoveAkce.test_093_pripojeni_PIAN_projektove_akce_p_001.end")

    # C-201015104
    def test_094_smazani_komponenty_projektove_akce_p_001(self):
        """Test 094 Smazání komponenty u projektové akce (pozitivní scénář 1)

        Test smazání komponenty u projektové akce. Scénář končí smazáním komponenty K001 u dokumentační jednotky D01 u projektové akce.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A1 s dokumentační jednotkou D01, která má připojenou komponentu K001.

        TestData:
            C-201015104A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-201015104A)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-201015104“ → Vybrat → otevřít projekt → otevřít akci „C-201015104A“
            - V části “Dokumentační jednotky” kliknout na komponentu “K001” u dokumentační jednotky “D01”
            - V části “Komponenta C-201015104A-K001 ” kliknout na Další nabídka → Smazat komponentu  → v dialogovém okne “Smazat komponentu” kliknout na “Smazat”

        Expected:
            - U dokumentační jednotky “C-201015104A-D01” bude smazána komponenta K001 „XXX”. V databázi bude o jeden záznam méně.
        """
        logger.info("AkceProjektoveAkce.test_094_smazani_komponenty_projektove_akce_p_001.start")
        self.login("archeolog")
        count_old = Komponenta.objects.filter(
            komponenta_vazby__dokumentacni_jednotka__ident_cely="C-201015104A-D01"
        ).count()
        self.go_to_Projekty_vyper()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-201015104")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-201015104")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.ID, "el_komponenta_C_201015104A_K001")
        self.ElementClick(By.ID, "others_komponenta")
        self.ElementClick(By.ID, "komponenta-smazat-C-201015104A-K001")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        count_new = Komponenta.objects.filter(
            komponenta_vazby__dokumentacni_jednotka__ident_cely="C-201015104A-D01"
        ).count()
        self.assertEqual(count_old - 1, count_new)
        logger.info("AkceProjektoveAkce.test_094_smazani_komponenty_projektove_akce_p_001.end")

    # C-202401980
    def test_095_smazani_DJ_projektove_akce_p_001(self):
        """Test 095 Smazání dokumentační jednotky u projektové akce (pozitivní scénář 1)

        Test smazání dokumentační jednotky u projektové akce. Scénář končí smazáním dokumentační jednotky D01 u projektové akce.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A1 s dokumentační jednotkou D01.

        TestData:
            C-202401980A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-202401980A)
            - Projekty → Vybrat → Filtr → ID obsahuje „C-202401980“ → Vybrat → otevřít projekt → otevřít akci „C-202401980A“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku“D01”  →  v části “Dokumentační jednotka “Dokumentační jednotka C-202401980A-D01“ kliknout na “Další volby”  → DJ - smazat
            - V části “Dokumentační jednotka “Dokumentační jednotka C-202401980A-D01“ kliknout na “Další volby”  → DJ - smazat → v dialogovém okně “Smazat dokumentační jednotku” kliknout na “Smazat”

        Expected:
            - U projektové akce  “C-202401980A” bude smazána dokumentační jednotka D01. V databázi bude o jeden záznam méně.
        """
        logger.info("AkceProjektoveAkce.test_095_smazani_DJ_projektove_akce_p_001.start")
        self.login("archeolog")
        self.createFedoraRecord("C-202401980")
        self.uploadFileToFedora(646253, "projekt/tests/resources/test.pdf")
        count_old = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202401980A").count()
        self.go_to_Projekty_vyper()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202401980")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-202401980")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401980A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")
        self.ElementClick(By.ID, "dj-smazat-C-202401980A-D01")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202401980A").count()
        self.assertEqual(count_old - 1, count_new)
        logger.info("AkceProjektoveAkce.test_095_smazani_DJ_projektove_akce_p_001.end")

    # C-201443939A
    def test_102_archivace_projektove_akce_p_001(self):
        """Test 102 Archivace projektové akce (pozitivní scénář 1)

        Test archivace projektové akce. Scénář končí posunem projektové akce ze stavu A2 do stavu A3.

        Role:
            Archivář

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A2 s dokumentační jednotkou D01, která má připojen potvrzený PIAN.
            - Nahrazuje NZ - Ano

        TestData:
            C-201443939A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-201443939A)
            - Projekty → Vybrat → Filtr → ID obsahuje C-201443939A → Vybrat → otevřít projekt →  otevřít akci „C-201443939A“
            - V panelu pro akce kliknout na “Archivovat” → v dialogovém okně “Archivovat záznam” kliknout na “Archivovat”
            - V dalším dialogovém okně “Archivace projektu” kliknout na “Archivovat”

        Expected:
            - Projektová akce “C-201443939A” se posune ze stavu A2 do stavu A3. Projekt “C-201443939A” se posune ze stavu P5 do stavu P6.
        """
        logger.info("AkceProjektoveAkce.test_102_archivace_projektove_akce_p_001.start")
        self.login("archivar")

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-201443939A").first().stav, AZ_STAV_ODESLANY)
        self.assertEqual(Projekt.objects.get(ident_cely="C-201443939").stav, PROJEKT_STAV_UZAVRENY)
        self.go_to_Projekty_vyper()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-201443939")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-201443939")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.ID, "akce-archivovat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(
            ArcheologickyZaznam.objects.filter(ident_cely="C-201443939A").first().stav, AZ_STAV_ARCHIVOVANY
        )
        self.assertEqual(Projekt.objects.get(ident_cely="C-201443939").stav, PROJEKT_STAV_ARCHIVOVANY)

        logger.info("AkceProjektoveAkce.test_102_archivace_projektove_akce_p_001.end")

    def test_156_smazani_projektove_akce_p_001(self):
        """Test 156 Smazání projektové akce (pozitivní scénář 1)

        Test smazání projektové akce. Scénář končí odstranění projektové akce z databáze.

        Role:
            Archivář

        Preconditions:
            - Uživatel je přihlášen.
            - Projektová akce ve stavu A2.

        TestData:
            C-201443939A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A2 a otevře tuto akci (C-201443939A)
            - V panelu pro akce kliknout na  “Další akce” → “Smazat záznam”
            - V dalším dialogovém okně “Smazat archeologický záznam” kliknout na “Smazat”

        Expected:
            - Projektová akce “C-201443939A” bude smazána z databáze.
            - Projekt “C-201443939” bude mít o jednu akci méně
        """
        logger.info("AkceProjektoveAkce.test_156_smazani_projektove_akce_p_001.start")
        self.login("archivar")

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-201443939A").first().stav, AZ_STAV_ODESLANY)
        pocet_akci_old = Akce.objects.filter(projekt__ident_cely="C-201443939").count()
        self.assertEqual(Projekt.objects.get(ident_cely="C-201443939").stav, PROJEKT_STAV_UZAVRENY)
        self.createFedoraRecord("C-201443939A")
        self.goToAddress("/arch-z/akce/detail/C-201443939A")
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "akce-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-201443939A").count(), 0)
        pocet_akci_new = Akce.objects.filter(projekt__ident_cely="C-201443939").count()
        self.assertEqual(pocet_akci_new, pocet_akci_old - 1)
        logger.info("AkceProjektoveAkce.test_156_smazani_projektove_akce_p_001.end")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceSamostatneAkce(AkceTestClass):
    def create_Samostatna_Akce(self):
        self.go_to_Akce_zapsat()
        self.ElementClick(By.ID, "select2-id_hlavni_katastr-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            "Velká Do"
        )
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            Keys.ENTER
        )
        self.ElementClick(By.ID, "select2-id_hlavni_vedouci-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            "Švejcar"
        )
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            Keys.ENTER
        )
        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("archeologický")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-29 > .text")

        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("sonda")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-22 > .text")

        self.ElementClick(By.ID, "id_datum_zahajeni")
        self.driver.find_element(By.ID, "id_datum_zahajeni").send_keys("07.03.2024")
        self.ElementClick(By.ID, "id_datum_ukonceni")
        self.driver.find_element(By.ID, "id_datum_ukonceni").send_keys("07.03.2024")
        self.ElementClick(By.ID, "id_lokalizace_okolnosti")
        self.driver.find_element(By.ID, "id_lokalizace_okolnosti").send_keys("Hora")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "actionSubmitBtn")

    def test_046_vytvoreni_samostatne_akce_p_001(self):
        """Test 046 Vytvoření samostatné akce (pozitivní scénář 1)

        Test vytvoření samostatné akce. Scénář končí vytvořením samostatné akce akce ve stavu A1.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.

        Steps:
            - Uživatel se přihlásí
            - Uživatel vstoupí do modulu Samostatné akce pro zápis nové akce
            - Samostatné akce → Zapsat
            - Uživatel vyplní povinné položky
            - Uživatel klikne na tlačítko “Zapsat”

        Expected:
            -  Vytvoření samostatné akce - v databázi bude o jednu akci více
        """
        logger.info("AkceSamostatneAkce.test_046_vytvoreni_samostatne_akce_p_001.start")
        self.login("badatel")

        arch_z_count_old = Akce.objects.count()
        self.create_Samostatna_Akce()
        arch_z_count_new = Akce.objects.count()
        self.assertEqual(arch_z_count_old + 1, arch_z_count_new)
        logger.info("AkceSamostatneAkce.test_046_vytvoreni_samostatne_akce_p_001.end")

    def test_047_vytvoreni_samostatne_akce_n_001(self):
        """Test 047 Vytvoření samostatné akce (negativní scénář 1)

        Test vytvoření samostatné akce. Scénář nekončí vytvořením samostatné akce ve stavu A1.

        Role:
            Badatel

        Steps:
            - Uživatel se přihlásí
            - Uživatel vstoupí do modulu Samostatné akce pro zápis nové akce
            - Samostatné akce → Zapsat
            - Uživatel vyplní povinné položky, nevyplní Hlavní katastr
            - Uživatel klikne na tlačítko “Zapsat”

        Expected:
            - Nedojde k vytvoření samostatné akce - v databázi bude stejný počet akcí
        """
        logger.info("AkceSamostatneAkce.test_047_vytvoreni_samostatne_akce_n_001.start")
        self.login("badatel")

        arch_z_count_old = Akce.objects.count()

        self.go_to_Akce_zapsat()
        # self.ElementClick(By.ID, "select2-id_hlavni_katastr-container")
        # self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys("Velká Do")
        # self.wait(self.wait_interval)
        # self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "select2-id_hlavni_vedouci-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            "Švejcar"
        )
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(
            Keys.ENTER
        )
        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("archeologický")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-29 > .text")

        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("sonda")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-22 > .text")

        self.ElementClick(By.ID, "id_datum_zahajeni")
        self.driver.find_element(By.ID, "id_datum_zahajeni").send_keys("07.03.2024")
        self.ElementClick(By.ID, "id_datum_ukonceni")
        self.driver.find_element(By.ID, "id_datum_ukonceni").send_keys("07.03.2024")
        self.ElementClick(By.ID, "id_lokalizace_okolnosti")
        self.driver.find_element(By.ID, "id_lokalizace_okolnosti").send_keys("Hora")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "actionSubmitBtn")
        except Exception:
            pass
        arch_z_count_new = Akce.objects.count()
        self.assertEqual(arch_z_count_old, arch_z_count_new)
        logger.info("AkceSamostatneAkce.test_047_vytvoreni_samostatne_akce_n_001.end")

    def test_048_pridani_dokumentacni_jednotky_samostatne_akce_p_001(self):
        """Test 048 Přidání dokumentační jednotky celek akce (pozitivní scénář 1)

        Test vytvoření dokumentační jednotky typu celek akce u samostatné akce ve stavu A1. Scénář končí vytvořením dokumentační jednotky D01.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A1

        TestData:
            X-C-9000000001A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře samostatnou akci ve stavu A1
            - Samostatné akce  → Vybrat → Filtr → ID obsahuje „číslo SA“ → Vybrat → otevřít SA
            - Uživatel přidá dokumentační jednotku “Celek akce” (v sekci dokumentační jednotky)
            - Dokumentační jednotky  → Přidat dokumentační jednotku
            - Uživatel vyplní povinná pole
            - Uživatel klikne na tlačítko “Uložit změny”

        Expected:
            - U akce bude vytvořena DJ D01 typu “Celek akce” (v databázi je o jednu DJ více)
        """
        logger.info("AkceSamostatneAkce.test_048_pridani_dokumentacni_jednotky_samostatne_akce_p_001.start")
        self.login("badatel")

        count_old = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.go_to_Akce_vybrat()
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000001A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11) > .material-icons")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000001A")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDjSubmitButton")

        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceSamostatneAkce.test_048_pridani_dokumentacni_jednotky_samostatne_akce_p_001.end")

    def test_049_pridani_dokumentacni_jednotky_samostatne_akce_n_001(self):
        """Test 049  Přidání dokumentační jednotky “Celek akce” (negativní scénář 1)

        Test vytvoření dokumentační jednotky typu celek akce u samostatné akce ve stavu A1. Scénář nekončí vytvořením dokumentační jednotky D01.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A1

        TestData:
            X-C-9000000001A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře samostatnou akci ve stavu A1
            - Samostatné akce  → Vybrat → Filtr → ID obsahuje „číslo SA“ → Vybrat → otevřít SA
            - Uživatel přidá dokumentační jednotku “Celek akce” (v sekci dokumentační jednotky)
            - Dokumentační jednotky  → Přidat dokumentační jednotku
            - Uživatel vyplní povinná pole, nevyplní Typ
            - Uživatel klikne na tlačítko “Uložit změny”

        Expected:
            - U akce NEbude vytvořena DJ typu “Celek akce” (v databázi je stejný počet DJ)
        """
        logger.info("AkceSamostatneAkce.test_049_pridani_dokumentacni_jednotky_samostatne_akce_n_001.start")
        self.login("badatel")

        count_old = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.go_to_Akce_vybrat()
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000001A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11) > .material-icons")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000001A")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")

        # self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        # self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        try:
            with WaitForPageLoad(self.driver, 5):
                self.ElementClick(By.ID, "newDjSubmitButton")
        except Exception:
            pass
        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.assertEqual(count_old, count_new)
        logger.info("AkceSamostatneAkce.test_049_pridani_dokumentacni_jednotky_samostatne_akce_n_001.end")

    def test_050_pridani_komponenty_DJ_samostatne_akce_p_001(self):
        """Test 050 Přidání komponenty k DJ u samostatné akce (pozitivní scénář 1)

        Test vytvoření komponenty k DJ u samostatné akce ve stavu A1. Scénář 	končí vytvořením komponenty K01.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A1
            - Dokumentační jednotka D01

        TestData:
            X-C-9000000002A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře samostatnou akci ve stavu A1
            - Samostatné akce  → Vybrat → Filtr → ID obsahuje „číslo SA“ → Vybrat → otevřít SA
            - Uživatel vybere dokumentační jednotku D01 (v sekci “Dokumentační jednotky”)
            - Uživatel k DJ přidá komponentu K01 - X-C-9000000060A-D01  → Další volby (+) → Komponenta vytvořit
            - Uživatel vyplní povinná pole
            - Uživatel klikne na tlačítko “Uložit změny”

        Expected:
            -  U DJ bude vytvořena komponenta K01. V databázi bude o jednu komponentu více.
        """
        logger.info("AkceSamostatneAkce.test_050_pridani_komponenty_DJ_samostatne_akce_p_001.start")
        self.login("badatel")

        count_old = Komponenta.objects.filter(
            komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000002A-D01"
        ).count()
        # count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.go_to_Akce_vybrat()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000002A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000002A")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_9000000002A_D01 > strong")
        # self.driver.execute_script("window.scrollTo(0,0)")
        self.ElementClick(
            By.CSS_SELECTOR, "#detail_dj_form_X-C-9000000002A-D01 .btn-group:nth-child(1) .material-icons"
        )
        self.ElementClick(
            By.LINK_TEXT, _("arch_z.templates.arch_z.dj.partials.dj_update.editButtons.pridatKomponentu.label")
        )
        self.ElementClick(By.CSS_SELECTOR, "#div_id_obdobi .btn")
        self.ElementClick(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control")
        # self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.DOWN)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("únětická kultura")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("poh")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        # self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-39 > .text")

        # self.driver.execute_script("window.scrollTo(0,0)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createCompotSubmitButton")

        count_new = Komponenta.objects.filter(
            komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000002A-D01"
        ).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceSamostatneAkce.test_050_pridani_komponenty_DJ_samostatne_akce_p_001.end")

    def test_074_pridani_komponenty_DJ_samostatne_akce_n_001(self):
        """Test 074 Přidání komponenty k DJ u samostatné akce (negativní scénář 1)

        Test vytvoření komponenty k DJ u samostatné akce ve stavu A1. Scénář nekončí vytvořením komponenty.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A1
            - Dokumentační jednotka D01

        TestData:
            X-C-9000000002A

        Steps:
            -  Uživatel se přihlásí
            -  Uživatel otevře samostatnou akci ve stavu A1
            -  Samostatné akce  → Vybrat → Filtr → ID obsahuje „X-C-9000000002A“ → Vybrat → otevřít SA
            -  Uživatel vybere dokumentační jednotku D01 (v sekci “Dokumentační jednotky”)
            -  Uživatel k DJ přidá komponentu K01  X-C-9000000002AD01  → Další volby (+) → Komponenta vytvořit
            -  Uživatel vyplní povinná pole, nevyplní Areál
            -  Uživatel klikne na tlačítko “Uložit změny”

        Expected:
            - U dokumentační jednotky D01 NEbude vytvořena komponenta (v databázi je stejný počet DJ). U pole Areál se objeví nápověda “Vyberte prosím v seznamu některou položku”.
        """
        logger.info("AkceSamostatneAkce.test_074_pridani_komponenty_DJ_samostatne_akce_n_001.start")
        self.login("badatel")

        count_old = Komponenta.objects.filter(
            komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000002A-D01"
        ).count()
        # count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.go_to_Akce_vybrat()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000002A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000002A")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_9000000002A_D01 > strong")
        self.ElementClick(
            By.CSS_SELECTOR, "#detail_dj_form_X-C-9000000002A-D01 .btn-group:nth-child(1) .material-icons"
        )
        self.ElementClick(
            By.LINK_TEXT, _("arch_z.templates.arch_z.dj.partials.dj_update.editButtons.pridatKomponentu.label")
        )
        self.ElementClick(By.CSS_SELECTOR, "#div_id_obdobi .btn")
        self.ElementClick(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control")
        # self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.DOWN)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("únětická kultura")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        # self.ElementClick(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner")
        # self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("poh")
        # self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        # self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-39 > .text")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createCompotSubmitButton")

        count_new = Komponenta.objects.filter(
            komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000002A-D01"
        ).count()
        self.assertEqual(count_old, count_new)
        logger.info("AkceSamostatneAkce.test_074_pridani_komponenty_DJ_samostatne_akce_n_001.end")

    def test_075_pridani_objektu_komponente_DJ_samostatna_akce_p_001(self):
        """Test 075 Přidání objektu k pozitivní komponentě (pozitivní scénář 1)

        Test vytvoření objektu u komponenty připojené k dokumentační jednotce samostatné akce. Scénář končí vytvořením objektu u komponenty K001 u dokumentační jednotky D01.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A1
            - Dokumentační jednotka D01
            - Komponenta K001

        TestData:
            X-C-9000000003A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře samostatnou akci ve stavu A1 (X-C-9000000003A)
            - Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000003A“ → Vybrat → otevřít samostatnou akci
            - Kliknout na komponentu K001 u dokumentační jednotky D01
            - V sekci Nálezy a Objekty zvolit Druh “(polo)zemnice”.
            - V sekci Nálezy a Objekty vyplnit Počet “1”.
            - Kliknout na “Uložit změny”

        Expected:
            - U komponenty K001 bude vytvořen nový objekt. V databázi bude o jeden objekt více.
        """
        logger.info("AkceSamostatneAkce.test_075_pridani_objektu_komponente_DJ_samostatna_akce_p_001.start")
        self.login("badatel")

        count_old = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000003A-D01"
        ).count()

        self.go_to_Akce_vybrat()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000003A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000003A")
        self.ElementClick(By.ID, "el_komponenta_X_C_9000000003A_K001")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-9000000003A-K001_o-0-druh .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("polo")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_X-C-9000000003A-K001_o-0-pocet")
        self.driver.find_element(By.ID, "id_X-C-9000000003A-K001_o-0-pocet").send_keys("1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")

        count_new = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000003A-D01"
        ).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceSamostatneAkce.test_075_pridani_objektu_komponente_DJ_samostatna_akce_p_001.end")

    def test_076_pridani_predmetu_komponente_DJ_samostatna_akce_p_001(self):
        """Test 076 Přidání předmětu k pozitivní komponentě (pozitivní scénář 1)

        Test vytvoření předmětu u komponenty připojené k dokumentační jednotce samostatné akce. Scénář končí vytvořením předmětu u komponenty K001 u dokumentační jednotky D01.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A1
            - Dokumentační jednotka D01
            - Komponenta K001

        TestData:
            X-C-9000000003A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře samostatnou akci ve stavu A1 (X-C-9000000003A)
            - Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000003A“ → Vybrat → otevřít samostatnou akci
            - Kliknout na komponentu K001 u dokumentační jednotky D01
            - V sekci Nálezy a Předměty zvolit Druh “džbán”.
            - V sekci Nálezy a Předměty zvolit Specifikace “keramika”.
            - V sekci Nálezy a Předměty vyplnit Počet “1”.
            - Kliknout na “Uložit změny”

        Expected:
            - U komponenty K001 bude vytvořen nový předmět. V databázi bude o jeden předmět více.
        """
        logger.info("AkceSamostatneAkce.test_076_pridani_predmetu_komponente_DJ_samostatna_akce_p_001.start")
        self.login("badatel")

        count_old = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000003A-D01"
        ).count()

        self.go_to_Akce_vybrat()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000003A")

        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000003A")
        self.ElementClick(By.ID, "el_komponenta_X_C_9000000003A_K001")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-9000000003A-K001_p-0-druh .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("dž")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, ".dropup .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("keramika")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.ID, "id_X-C-9000000003A-K001_p-0-pocet")
        self.driver.find_element(By.ID, "id_X-C-9000000003A-K001_p-0-pocet").send_keys("1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")

        count_new = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000003A-D01"
        ).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceSamostatneAkce.test_076_pridani_predmetu_komponente_DJ_samostatna_akce_p_001.end")

    def test_077_smazani_objektu_komponenty_DJ_samostatna_akce_p_001(self):
        """Test 077 Smazání objektu u samostatné akce (pozitivní scénář 1)

        Test smazání objektu u komponenty připojené k dokumentační jednotce samostatné akce. Scénář končí smazáním objektu.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A1
            - Dokumentační jednotka D01
            - Komponenta K001
            - Objekt “jáma kůlová/sloupová” připojený ke komponentě K001

        TestData:
            X-C-9000000004A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře samostatnou akci ve stavu A1 (X-C-9000000004A)
            - Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000004A“ → Vybrat → otevřít samostatnou akci
            - Kliknout na komponentu K001 u dokumentační jednotky D01
            - V sekci Nálezy a Objekty u položky “jáma kůlová/sloupová” kliknout na možnost “odstranit”
            - Volbu potvrdit

        Expected:
            -  U komponenty K001 bude odebrána položka typu objekt. V databázi bude o jeden objekt méně. Oznámení “Záznam byl úspěšně smazán”
        """
        logger.info("AkceSamostatneAkce.test_077_smazani_objektu_komponenty_DJ_samostatna_akce_p_001.start")
        self.login("badatel")

        count_old = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000004A-D01"
        ).count()

        self.go_to_Akce_vybrat()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000004A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000004A")
        self.ElementClick(By.ID, "el_komponenta_X_C_9000000004A_K001")
        self.ElementClick(By.CSS_SELECTOR, "#objekt-smazat-180491 > .material-icons")
        self.ElementClick(By.ID, "submit-btn")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")

        count_new = NalezObjekt.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000004A-D01"
        ).count()
        self.assertEqual(count_old, count_new + 1)
        logger.info("AkceSamostatneAkce.test_077_smazani_objektu_komponenty_DJ_samostatna_akce_p_001.end")

    def test_078_smazani_predmetu_komponenty_DJ_samostatna_akce_p_001(self):
        """Test 078 Smazání předmětu u samostatné akce (pozitivní scénář 1)

        Test smazání předmětu u komponenty připojené k dokumentační jednotce samostatné akce. Scénář končí smazáním předmětu.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A1
            - Dokumentační jednotka D01
            - Komponenta K001
            - Předmět “doklad umění/kultu” připojený ke komponentě K001

        TestData:
            X-C-9000000004A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře samostatnou akci ve stavu A1 (X-C-9000000004A)
            - Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000004A“ → Vybrat → otevřít samostatnou akci
            - Kliknout na komponentu K001 u dokumentační jednotky D01
            - V sekci Nálezy a Předměty u položky “doklad umění/kultu” kliknout na možnost “odstranit”
            - Volbu potvrdit

        Expected:
            - U komponenty K001 bude odebrána položka typu předmět. V databázi bude o jeden předmět méně. Oznámení “Záznam byl úspěšně smazán”
        """
        logger.info("AkceSamostatneAkce.test_078_smazani_predmetu_komponenty_DJ_samostatna_akce_p_001.start")
        self.login("badatel")

        count_old = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000004A-D01"
        ).count()

        self.go_to_Akce_vybrat()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000004A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000004A")
        self.ElementClick(By.ID, "el_komponenta_X_C_9000000004A_K001")
        self.ElementClick(By.CSS_SELECTOR, "#objekt-smazat-175762 > .material-icons")
        self.ElementClick(By.ID, "submit-btn")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")

        count_new = NalezPredmet.objects.filter(
            komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000004A-D01"
        ).count()
        self.assertEqual(count_old, count_new + 1)
        logger.info("AkceSamostatneAkce.test_078_smazani_predmetu_komponenty_DJ_samostatna_akce_p_001.end")

    # 82 a 83 X-C-9000000003A
    def test_082_pridani_dokumentu_samostatne_akci_p_001(self):
        """Test 082 Přidání dokumentu k samostatné akci (pozitivní scénář 1)

        Test přidání dokumentu k samostatné akci. Scénář končí vytvořením záznamu dokumentu a jeho připojením k samostatné akci.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce je ve stavu A1.

        TestData:
            X-C-9000000003A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře samostatnou akci ve stavu A1 (X-C-9000000003A)
            - Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000003A“ → Vybrat → otevřít samostatnou akci
            - V tabulce Dokumenty kliknout na tlačítko “Přidat dokument”
            - Uživatel vyplní povinné údaje ve formuláři Dokument
            - Klikne na tlačítko Zapsat

        Expected:
            - Bude vytvořen nový záznam typu dokument (v databázi je o jeden dokument více). Tento dokument je připojený k samostatné akci X-C-9000000003A
        """
        logger.info("AkceSamostatneAkce.test_082_pridani_dokumentu_samostatne_akci_p_001.start")
        self.login("badatel")

        count_old = DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000003A").count()
        self.go_to_Akce_vybrat()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")

        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000003A")

        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000003A")

        # self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.ID, "others_doc")
        self.ElementClick(By.LINK_TEXT, _("dokument.templates.dokument_table.pridatNovyDokument.label"))
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Absolon")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vzniku")
        self.driver.find_element(By.ID, "id_rok_vzniku").send_keys("2023")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(
            "Moravské zemské muzeum"
        )
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("Investorsk")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("di")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.ID, "id_popis")
        self.driver.find_element(By.ID, "id_popis").send_keys("test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("anonym")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")

        count_new = DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000003A").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceSamostatneAkce.test_082_pridani_dokumentu_samostatne_akci_p_001.end")

    def test_083_pridani_existujiciho_dokumentu_samostatne_akci_p_001(self):
        """Test 083 Připojení existujícího dokumentu k samostatné akci (pozitivní scénář 1)

        Test připojení existujícího dokumentu k samostatné akci.Scénář končí vytvořením vazby mezi dokumentem a samostatnou akcí.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce je ve stavu A1.

        TestData:
            X-C-9000000004A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře samostatnou akci ve stavu A1 (X-C-9000000004A)
            - Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000004A“ → Vybrat → otevřít projekt
            - V tabulce Dokumenty kliknout na tlačítko “Připojit existující dokument”
            - Uživatel vyhledá dokument “M-TX-194300126”
            - Klikne na tlačítko Připojit

        Expected:
            - Je vytvořena vazba mezi dokumentem a projektovou akcí X-C-9000000004A
        """
        logger.info("AkceSamostatneAkce.test_083_pridani_existujiciho_dokumentu_samostatne_akci_p_001.start")
        self.login("badatel")

        count_old = DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000004A").count()
        self.go_to_Akce_vybrat()

        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")

        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000004A")

        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000004A")

        self.ElementClick(By.ID, "others_doc")
        self.driver.execute_script('$("#app-wrapper").scrollTop($("#app-wrapper")[0].scrollHeight);')
        self.ElementClick(By.ID, "dokument-pripojit")

        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("X-C-TX-000000003")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        count_new = DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000004A").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceSamostatneAkce.test_083_pridani_existujiciho_dokumentu_samostatne_akci_p_001.end")

        # X-C-9000000003A

    def test_085_pripojeni_externiho_zdroje_samostatne_akci_p_001(self):
        """Test 085 Připojení externího zdroje k samostatné akci (pozitivní scénář 1)

        Test připojení externího zdroje k samostatné akci..Scénář končí vytvořením vazby mezi samostatnou akcí a externím zdrojem.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A1.

        TestData:
            X-C-9000000003A
            X-BIB-1295324

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře samostatnou akci ve stavu A1 (X-C-9000000003A)
            - Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000003A“ → Vybrat → otevřít akci „X-C-9000000003A“
            - V části “Externí zdroje” kliknout na “připojit externí zdroj”
            - Uživatel vyhledá identifikátor “X-BIB-1295325”
            - Klikne na tlačítko Připojit

        Expected:
            - Je vytvořena vazba mezi samostatnou akcí externím zdrojem  „X-BIB-1295325“
        """
        logger.info("AkceSamostatneAkce.test_085_pripojeni_externiho_zdroje_samostatne_akci_p_001.start")
        self.login("badatel")

        count_old = ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000003A").count()
        self.go_to_Akce_vybrat()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000003A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000003A")
        self.ElementClick(By.CSS_SELECTOR, "#eo-pripojit-do-az > .material-icons")
        self.ElementClick(By.ID, "select2-id_ez-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("X-BIB-1295324")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.ElementClick(By.CSS_SELECTOR, "#eo-pripojit-do-az > .material-icons")
        self.ElementClick(By.ID, "select2-id_ez-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("X-BIB-1295325")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        count_new = ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000003A").count()
        self.assertEqual(count_old + 2, count_new)
        logger.info("AkceSamostatneAkce.test_085_pripojeni_externiho_zdroje_samostatne_akci_p_001.end")

    def test_096_vytvoreni_PIAN_samostatne_akce_p_001(self):
        """Test 096 Vytvoření PIAN u samostatné akce (pozitivní scénář 1)

        Test vytvoření PIAN k samostatné akci.Scénář končí vytvořením nového PIAN připojeného k DJ D01 u samostatné akce.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A1 s dokumentační jednotkou D01, která nemá připojen PIAN.

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (X-C-9000000002A)
            - Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000002A“ → Vybrat → otevřít akci „X-C-9000000002A“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
            - V části “Dokumentační jednotka X-C-9000000002A-D01” kliknout na Další volby → PIAN - vytvořit → vytvořit geometrii PIAN
            - V části nový PIAN nastavit přesnost na hodnotu “odchylka jednotky metrů”

        Expected:
            - U dokumentační jednotky “X-C-9000000002A-D01” samostatné akce je připojen nový PIAN. V databázi je o jeden záznam více.
        """
        logger.info("AkceSamostatneAkce.test_096_vytvoreni_PIAN_samostatne_akce_p_001.start")
        self.login("badatel")
        pian_old = DokumentacniJednotka.objects.filter(ident_cely="X-C-9000000002A-D01")[0].pian
        self.assertEqual(pian_old, None)

        self.go_to_Akce_vybrat()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000002A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000002A")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_9000000002A_D01 > strong")
        self.ElementClick(
            By.CSS_SELECTOR, "#detail_dj_form_X-C-9000000002A-D01 .btn-group:nth-child(1) .material-icons"
        )
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "show_menu_pian_new_id")
        self.draw_polygon()

        self.ElementClick(By.CSS_SELECTOR, ".filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createPianSubmitButton")

        pian_new = DokumentacniJednotka.objects.filter(ident_cely="X-C-9000000002A-D01")[0].pian

        self.assertNotEqual(pian_new, None)
        logger.info("AkceSamostatneAkce.test_096_vytvoreni_PIAN_samostatne_akce_p_001.end")

    def test_097_editace_PIAN_samostatne_akce_p_001(self):
        """Test 097 Editace PIAN u samostatné akce (pozitivní scénář 1)

        Test editace PIAN u samostatné akce. Scénář končí novou geometrií PIAN u dokumentační jednotky D01 u samostatné akce.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A1 s dokumentační jednotkou D01, která má připojen nepotvrzený PIAN.

        TestData:
            X-C-9000000006A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (X-C-9000000006A-)
            - Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000006A-“ → Vybrat → otevřít akci „X-C-9000000006A-“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
            - V části “Dokumentační jednotka X-C-9000000006A--D01” kliknout na Další volby → PIAN - upravit → upravit geometrii PIAN (jak vyřešit v testu?)

        Expected:
            - U dokumentační jednotky “X-C-9000000006A--D01” je upravena geometrie připojeného PIAN (jak poznáme v testu?).
        """
        logger.info("AkceSamostatneAkce.test_097_editace_PIAN_samostatne_akce_p_001.start")
        self.login("badatel")
        pian_old = str(DokumentacniJednotka.objects.filter(ident_cely="X-C-9000000006A-D01")[0].pian.geom)

        self.go_to_Akce_vybrat()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")

        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000006A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000006A")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_9000000006A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "pian-upravit-N-1212-000000001")
        self.draw_polygon()
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editPianButton")

        pian_new = str(DokumentacniJednotka.objects.filter(ident_cely="X-C-9000000006A-D01")[0].pian.geom)

        self.assertNotEqual(pian_new, pian_old)
        logger.info("AkceSamostatneAkce.test_097_editace_PIAN_samostatne_akce_p_001.end")

    def test_098_editace_PIAN_samostatne_akce_importem_p_001(self):
        """Test 098 Editace PIAN k samostatné akci importem (pozitivní scénář 1)

        Test editace PIAN k samostatné akci importem. Scénář končí upraveným PIAN u dokumentační jednotky D01 u samostatné akce.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A1 s dokumentační jednotkou D01, která má připojen nepotvrzený PIAN.

        TestData:
            X-C-9000000006A
            geom.csv

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (X-C-9000000006A)
            - Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000006A“ → Vybrat → otevřít akci „X-C-9000000006A“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
            - V části “Dokumentační jednotka X-C-9000000006A-D01” kliknout na Další volby → PIAN - upravit importem → V dialogovém okně “Importovat PIAN” vložit soubor CSV geom.csv a kliknout na Dokončit
            - V části ““Dokumentační jednotka X-C-9000000006A-D01” kliknout na “uložit změny”

        Expected:
            - U dokumentační jednotky “X-C-9000000006A-D01” bude upravena geometrie PIAN „XXX”.
        """
        logger.info("AkceSamostatneAkce.test_098_editace_PIAN_samostatne_akce_importem_p_001.start")
        self.login("badatel")
        pian_old = str(DokumentacniJednotka.objects.filter(ident_cely="X-C-9000000006A-D01")[0].pian.geom)

        self.go_to_Akce_vybrat()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")

        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000006A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000006A")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_9000000006A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")

        self.ElementClick(By.CSS_SELECTOR, ".show > .dropdown-item:nth-child(2)")
        self.upload_file("arch_z/tests/resources/geom.csv", "geom.csv", "application/csv")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editPianButton")

        pian_new = str(DokumentacniJednotka.objects.filter(ident_cely="X-C-9000000006A-D01")[0].pian.geom)

        self.assertNotEqual(pian_new, pian_old)
        logger.info("AkceSamostatneAkce.test_098_editace_PIAN_samostatne_akce_importem_p_001.end")

    def test_099_import_PIAN_samostatne_akce_p_001(self):
        """Test 099 Import PIAN k samostatné akci (pozitivní scénář 1)

        Test importu PIAN k samostatné akci. Scénář končí vytvořením PIAN u dokumentační jednotky D01 u samostatné akce.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A1 s dokumentační jednotkou D01, která nemá připojen PIAN.

        TestData:
            X-C-9000000002A
            geom.csv

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (X-C-9000000002A)
            - Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000002A“ → Vybrat → otevřít akci „X-C-9000000002A“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
            - V části “Dokumentační jednotka X-C-9000000002A-D01” kliknout na Další volby → PIAN - importovat → V dialogovém okně “Importovat PIAN” vložit soubor CSV geom.csv a kliknout na Dokončit
            - V části “Nový PIAN” vybrat přesnost “odchylka jednotky metrů” a kliknout “uložit změny”

        Expected:
            - U dokumentační jednotky “X-C-9000000002A-D01” bude připojen nový PIAN „XXX”. V databázi bude o jeden PIAN více (vznikne vazba s D01).
        """
        logger.info("AkceSamostatneAkce.test_099_import_PIAN_samostatne_akce_p_001.start")
        self.login("badatel")
        pian_old = DokumentacniJednotka.objects.filter(ident_cely="X-C-9000000002A-D01")[0].pian
        self.assertEqual(pian_old, None)

        self.go_to_Akce_vybrat()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000002A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000002A")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_9000000002A_D01 > strong")
        self.ElementClick(
            By.CSS_SELECTOR, "#detail_dj_form_X-C-9000000002A-D01 .btn-group:nth-child(1) .material-icons"
        )
        self.ElementClick(By.CSS_SELECTOR, ".show > .dropdown-item:nth-child(2)")
        self.upload_file("arch_z/tests/resources/geom.csv", "geom.csv", "application/csv")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")

        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createPianSubmitButton")

        pian_new = DokumentacniJednotka.objects.filter(ident_cely="X-C-9000000002A-D01")[0].pian

        self.assertNotEqual(pian_new, None)
        logger.info("AkceSamostatneAkce.test_099_import_PIAN_samostatne_akce_p_001.end")

    def test_100_odpojeni_potvrzeneho_PIAN_samostatne_akce_p_001(self):
        """Test 100 Odpojení potvrzeného PIAN u samostatné akce (pozitivní scénář 1)

        Test odpojení potvrzeného PIAN u samostatné akce. Scénář končí odpojením existujícího PIAN od dokumentační jednotky D01 u samostatné akce.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - samostatná akce ve stavu A1 s dokumentační jednotkou D01, která má připojen potvrzený PIAN.

        TestData:
            X-C-9000000012A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (X-C-9000000012A)
            - Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000012A“ → Vybrat → otevřít akci „X-C-9000000012A“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
            - V části “Dokumentační jednotka X-C-9000000012A-D01” kliknout na Další volby → PIAN - odpojit → V dialogovém okně “Odpojení PIAN” kliknout na “Odpojit”

        Expected:
            - U dokumentační jednotky “X-C-9000000012A-D01” zanikne vazba s PIAN „XXX”.
        """
        logger.info("AkceSamostatneAkce.test_100_odpojeni_potvrzeneho_PIAN_samostatne_akce_p_001.start")
        self.login("badatel")
        pian_old = DokumentacniJednotka.objects.filter(ident_cely="X-C-9000000012A-D01")[0].pian
        self.assertNotEqual(pian_old, None)
        self.go_to_Akce_vybrat()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000012A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000012A")
        self.ElementClick(By.ID, "el_dokumentacni_jednotka_X_C_9000000012A_D01")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")
        self.ElementClick(By.ID, "pian-odpojit-P-3312-100051")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        pian_new = DokumentacniJednotka.objects.filter(ident_cely="X-C-9000000012A-D01")[0].pian
        self.assertEqual(pian_new, None)
        logger.info("AkceSamostatneAkce.test_100_odpojeni_potvrzeneho_PIAN_samostatne_akce_p_001.end")

    def test_101_smazani_PIAN_samostatne_akce_p_001(self):
        """Test 101 Smazání PIAN u samostatné akce (pozitivní scénář 1)

        Test smazání PIAN u samostatné akce. Scénář končí smazáním nepotvrzeného PIAN u dokumentační jednotky D01 u samostatné akce.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A1 s dokumentační jednotkou D01, která má připojen nepotvrzený PIAN.

        TestData:
            X-C-9000000006A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (X-C-9000000006A)
            - Samostatné akce → Vybrat → Filtr → ID obsahuje „X-C-9000000006A“ → Vybrat → otevřít akci „X-C-9000000006A“
            - V části “Dokumentační jednotky” kliknout na dokumentační jednotku “D01”
            - V části “Dokumentační jednotka X-C-9000000006A-D01” kliknout na Další volby → PIAN - odpojit → v dialogovém okně “Odpojení PIAN” kliknout na tlačítko “Odpojit”

        Expected:
            - U dokumentační jednotky “X-C-9000000006A-D01” je smazán nepotvrzený PIAN, v databázi je o 1 PIAN méně.
        """
        logger.info("AkceSamostatneAkce.test_101_smazani_PIAN_samostatne_akce_p_001.start")
        self.login("badatel")
        pian_old = DokumentacniJednotka.objects.filter(ident_cely="X-C-9000000006A-D01")[0].pian
        pians_count_old = Pian.objects.count()
        self.assertNotEqual(pian_old, None)
        self.go_to_Akce_vybrat()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000006A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000006A")
        self.ElementClick(By.ID, "el_dokumentacni_jednotka_X_C_9000000006A_D01")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")
        self.ElementClick(By.ID, "pian-odpojit-N-1212-000000001")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        pians_count_new = Pian.objects.count()
        pian_new = DokumentacniJednotka.objects.filter(ident_cely="X-C-9000000006A-D01")[0].pian
        self.assertEqual(pian_new, None)
        self.assertEqual(pians_count_old, pians_count_new + 1)
        logger.info("AkceSamostatneAkce.test_101_smazani_PIAN_samostatne_akce_p_001.end")

    def test_103_archivace_samostatne_akce_p_001(self):
        """Test 103 Archivace samostatné akce (pozitivní scénář 1)

        Test archivace samostatné akce. Scénář končí posunem projektové akce ze stavu A2 do stavu A3.

        Role:
            Archivář

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A2 s dokumentační jednotkou D01, která má připojen potvrzený PIAN.
            - Nahrazuje NZ - Ano

        TestData:
            C-9157766A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře projekt s připojenou akcí ve stavu A1 a otevře tuto akci (C-9157766A)
            - Samostatné akce → Vybrat → Filtr → ID obsahuje „C-9157766A“ → Vybrat →  otevřít akci „C-9157766A“
            - V panelu pro akce kliknout na “Archivovat” → v dialogovém okně “Archivovat záznam” kliknout na “Archivovat”

        Expected:
            - Samostatná akce “C-9157766A” se posune ze stavu A2 do stavu A3.
        """
        logger.info("AkceProjektoveAkce.test_103_archivace_samostatne_akce_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("C-9157766A", "archivar")
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-9157766A").first().stav, AZ_STAV_ODESLANY)
        self.go_to_Akce_vybrat()
        self.ElementClick(By.ID, "buttonFiltr")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-9157766A")
        self.ElementClick(By.ID, "buttonVybrat")
        self.ElementClick(By.LINK_TEXT, "C-9157766A")
        time = self.getTime()
        self.ElementClick(By.ID, "akce-archivovat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="C-9157766A").first().stav, AZ_STAV_ARCHIVOVANY)
        self.check_fedora_change(time, "arch_z/tests/resources/test_103/archivace_AZ")
        logger.info("AkceProjektoveAkce.test_103_archivace_samostatne_akce_p_001.end")

    def test_138_test_Fedory_samostatne_akce_p_001(self):
        """Test 138 Test Fedory pro Samostatne akce (pozitivní scénář 1)

        Test Fedory pro Samostatne akce

        Role:
            Badatel, Archivář

        TestData:
            X-M-9922437A
            X-C-9000000002A
            BIB-0000001
            X-C-91468414A
            X-C-TX-000000008
            ADB-BLAT60-000001
            N-2214-000000004
            C-9003982A
            X-M-91558334A
            M-TX-194300151

        Steps:
            - Vytvoření Samostatné Akce
            - Editace Akce
            - Vytvoření vedoucího Akce
            - Editace vedoucího Akce
            - Smazání vedoucího Akce
            - Vytvoření DJ
            - Editace DJ
            - Smazání DJ
            - Vytvoření komponenty
            - Editace komponenty
            - Vytvoření nálezu
            - Editace nálezu
            - Smazání nálezu
            - Smazání komponenty
            - Připojení nového Dokumentu
            - Odpojení Dokumentu
            - Připojení EZ
            - Editace EZ
            - Odpojení EZ
            - Odeslání Akce
            - Smazání Akce
            - Připojení existujícího dokumentu

        Expected:
            - zápis dat do Fedory
        """
        logger.info("AkceProjektoveAkce.test_138_test_Fedory_samostatne_akce_p_001.start")

        # vytvoření akce
        self.login("badatel")
        time = self.getTime()
        self.create_Samostatna_Akce()
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/create_AZ")
        self.logout()

        # update akce X-M-9922437A
        self.login("archivar")
        self.createFedoraRecord("X-M-9922437A", "archivar")
        self.goToAddress("/id/X-M-9922437A")
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.ID, "id_lokalizace_okolnosti")
        self.ElementSendKeys(By.ID, "id_lokalizace_okolnosti", "Louny")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "actionSubmitBtn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/update_AZ")

        # C akce_vedouci
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__placeholder")
        self.wait_for_select2_results()
        self.ElementClick(By.CSS_SELECTOR, "#select2-id__osv-0-vedouci-results > li:nth-child(5)")
        self.ElementClick(By.CSS_SELECTOR, "#div_id__osv-0-organizace .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-9-9 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "actionSubmitBtn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/create_vedouci")

        # U akce_vedouci
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.CSS_SELECTOR, "#div_id__osv-0-organizace .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-9-16 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#select2-id__osv-0-vedouci-container")
        self.wait_for_select2_results()
        self.ElementClick(By.CSS_SELECTOR, "#select2-id__osv-0-vedouci-results > li:nth-child(4)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "actionSubmitBtn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/update_vedouci")

        # D akce_vedouci
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.CSS_SELECTOR, ".app-color-danger")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "actionSubmitBtn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/delete_vedouci")

        # C DJ
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDjSubmitButton")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/create_DJ")

        # U DJ
        time = self.getTime()
        self.ElementClick(By.ID, "id_X-M-9922437A-D01-nazev")
        self.ElementSendKeys(By.ID, "id_X-M-9922437A-D01-nazev", "test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editDjSubmitButton")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/update_DJ")

        # D DJ
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")
        self.ElementClick(By.ID, "dj-smazat-X-M-9922437A-D01")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/delete_DJ")

        # C komponenta
        self.createFedoraRecord("X-C-9000000002A", "archivar")
        self.goToAddress("/id/X-C-9000000002A")
        time = self.getTime()
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_9000000002A_D01 > strong")
        self.ElementClick(
            By.CSS_SELECTOR, "#detail_dj_form_X-C-9000000002A-D01 .btn-group:nth-child(1) .material-icons"
        )
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
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/create_komponenta")

        # U komponenta
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-9000000002A-K001-obdobi .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-6 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-9000000002A-K001-jistota .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-2-1")
        self.ElementClick(By.ID, "id_X-C-9000000002A-K001-presna_datace")
        self.ElementSendKeys(By.ID, "id_X-C-9000000002A-K001-presna_datace", "ne")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-9000000002A-K001-areal .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-5 > .text")
        self.ElementClick(By.CSS_SELECTOR, ".show-tick .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-4-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/update_komponenta")

        # C nalez
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-9000000002A-K001_o-0-druh .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-7-8 > .text")
        self.ElementClick(By.ID, "id_X-C-9000000002A-K001_o-0-pocet")
        self.ElementSendKeys(By.ID, "id_X-C-9000000002A-K001_o-0-pocet", "1")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-9000000002A-K001_p-0-druh .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-15-19 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-9000000002A-K001_p-0-specifikace .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-16-4 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/create_nalez")

        # U nalez
        time = self.getTime()
        self.ElementSendKeys(By.ID, "id_X-C-9000000002A-K001_o-0-pocet", "2")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-9000000002A-K001_p-0-specifikace .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-18-14 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-9000000002A-K001_o-0-specifikace .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-8-7 > .text")
        self.ElementClick(By.ID, "id_X-C-9000000002A-K001_p-0-pocet")
        self.ElementSendKeys(By.ID, "id_X-C-9000000002A-K001_p-0-pocet", "2")
        self.ElementClick(By.ID, "id_X-C-9000000002A-K001_p-0-poznamka")
        self.ElementSendKeys(By.ID, "id_X-C-9000000002A-K001_p-0-poznamka", "test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/update_nalez")

        # D nalez
        pk = (
            NalezObjekt.objects.filter(
                komponenta__komponenta_vazby__dokumentacni_jednotka__archeologicky_zaznam__ident_cely="X-C-9000000002A"
            )
            .first()
            .pk
        )
        time = self.getTime()
        self.ElementClick(By.ID, f"objekt-smazat-{pk}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        pk = (
            NalezPredmet.objects.filter(
                komponenta__komponenta_vazby__dokumentacni_jednotka__archeologicky_zaznam__ident_cely="X-C-9000000002A"
            )
            .first()
            .pk
        )
        self.ElementClick(By.ID, f"objekt-smazat-{pk}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/delete_nalez")

        # D komponenta
        time = self.getTime()
        self.ElementClick(By.ID, "others_komponenta")
        self.ElementClick(By.ID, "komponenta-smazat-X-C-9000000002A-K001")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/delete_komponenta")

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
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/create_dokument_cast")

        # D dokument_cast
        time = self.getTime()
        with WaitForPageLoad(self.driver):
            self.goToAddress("/id/X-C-9000000002A")
        self.wait(1)
        self.ElementClick(By.ID, "dokument-odpojit-X-C-TX-000000009")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/delete_dokument_cast")

        # C EZ
        self.createFedoraRecord("BIB-0000001", "archivar")
        time = self.getTime()
        self.ElementClick(By.ID, "eo-pripojit-do-az")
        self.ElementClick(By.ID, "select2-id_ez-container")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/create_EZ")

        # U EZ
        time = self.getTime()
        pk = ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000002A").first().id
        self.ElementClick(By.ID, f"ez-change-{pk}")
        self.ElementSendKeys(By.ID, "id_paginace", "10")
        self.ElementSendKeys(By.ID, f"ez-change-{pk}", "10")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/update_EZ")

        # D EZ
        time = self.getTime()
        pk = ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000002A").first().id
        self.ElementClick(By.ID, f"ez-odpojit-{pk}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/delete_EZ")

        # změna ident_cely AZ X-C-91468414A
        # změna ident_cely DJ
        # změna ident_cely komponenta
        # ADB-BLAT60-000001
        self.createFedoraRecord("X-C-91468414A", "archivar")
        self.createFedoraRecord("X-C-TX-000000008", "archivar")
        self.createFedoraRecord("BIB-0000001", "archivar")
        self.createFedoraRecord("ADB-BLAT60-000001", "archivar")
        self.createFedoraRecord("N-2214-000000004", "archivar")
        self.goToAddress("/id/X-C-TX-000000008")
        self.ElementClick(By.ID, "NahratSoubory")
        self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        time = self.getTime()
        self.goToAddress("/id/X-C-91468414A")
        self.ElementClick(By.ID, "akce-odeslat")
        with freeze_time("2025-07-27 12:00:01", ignore=["core.tests.test_selenium"]):
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/ident_cely")
        self.check_fedora_delete(["record/X-C-91468414A", "record/X-C-TX-000000008"])

        # AZ smazat
        self.goToAddress("/id/C-9003982A-D01")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "adb-smazat-ADB-BLAT60-000001")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        time = self.getTime()
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "akce-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/delete_AZ")

        # C dokument_cast existujici
        self.createFedoraRecord("X-M-91558334A", "archivar")
        self.createFedoraRecord("M-TX-194300151", "archivar")
        self.uploadFileToFedora(534769, "projekt/tests/resources/test.pdf", "archivar")
        time = self.getTime()
        self.goToAddress("/id/X-M-91558334A")
        self.ElementClick(By.ID, "others_doc")
        self.ElementClick(By.ID, "dokument-pripojit")
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("M-TX-194300151")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_138/create_dokument_cast_1")

    def test_139_test_Fedory_PIAN_p_001(self):
        """Test 139 Test Fedory pro PIAN, ADB, vyskovy bod (pozitivní scénář 1)

        Role:
            Archivář

        TestData:
            X-C-9000000011A
            P-1121-100070
            ruian-693154
            ruian-600016
            X-C-91601363A
            P-2212-010011

        Steps:
            - Vytvoření PIAN
            - Vytvoření ADB
            - Vytvoření Výškového bodu
            - Editace PIAN
            - Editace ADB
            - Změna přístupnosti Akce
            - Editace Výškového bodu
            - Smazání Výškového bodu
            - Smazání ADB
            - Odpojení a smazání PIAN
            - Připojení existujícího PIAN
            - Odpojení PIAN bez smazání
            - Potvrzení PIAN
            - Vytvoření DJ typu katastr
            - Editace DJ typu katastr
            - Smazání DJ typu katastr
            - Smazání DJ

        Expected:
            - zápis dat do Fedory
        """
        logger.info("AkceProjektoveAkce.test_139_test_Fedory_PIAN_p_001.start")

        # C PIAN X-C-9000000011A
        self.login("archivar")
        self.createFedoraRecord("X-C-9000000011A", "archivar")
        self.goToAddress("/id/X-C-9000000011A")
        self.ElementClick(By.ID, "button-add-dj")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-2 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDjSubmitButton")
        time = self.getTime()
        self.ElementClick(By.ID, "add_others")
        self.ElementClick(By.ID, "show_menu_pian_new_id")
        self.wait(1)
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
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/create_PIAN")

        # C ADB
        time = self.getTime()
        self.ElementClick(By.ID, "add_others")
        self.ElementClick(By.LINK_TEXT, "ADB - vytvořit")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_sondy .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-4 > .text")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-2 > .text")
        self.ElementClick(By.ID, "id_trat")
        self.ElementSendKeys(By.ID, "id_trat", "test")
        self.ElementClick(By.ID, "id_cislo_popisne")
        self.ElementSendKeys(By.ID, "id_cislo_popisne", "559")
        self.ElementClick(By.ID, "id_parcelni_cislo")
        self.ElementSendKeys(By.ID, "id_parcelni_cislo", "5")
        self.ElementClick(By.ID, "id_stratigraficke_jednotky")
        self.ElementSendKeys(By.ID, "id_stratigraficke_jednotky", "2")
        self.ElementClick(By.ID, "select2-id_autor_popisu-container")
        self.wait_for_select2_results()
        self.ElementClick(By.CSS_SELECTOR, "li.select2-results__option:nth-child(2)")
        self.ElementClick(By.ID, "id_rok_popisu")
        self.ElementClick(By.CSS_SELECTOR, ".year:nth-child(7)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createAdbSubmitButton")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/create_ADB")

        # C výškový bod
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, "#div_id_ADB-KRAS07-000001_vb-0-typ .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-6-3 > .text")
        self.ElementClick(By.ID, "id_ADB-KRAS07-000001_vb-0-niveleta")
        self.ElementSendKeys(By.ID, "id_ADB-KRAS07-000001_vb-0-niveleta", "500")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editDjSubmitButton")
        pk_vyskovy_bod = (
            VyskovyBod.objects.filter(adb__dokumentacni_jednotka__archeologicky_zaznam__ident_cely="X-C-9000000011A")
            .first()
            .pk
        )
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/create_vyskovy_bod")

        # U PIAN
        pian = Pian.objects.filter(dokumentacni_jednotky_pianu__ident_cely="X-C-9000000011A-D01").first().ident_cely
        time = self.getTime()
        self.ElementClick(By.ID, "el_dokumentacni_jednotka_X_C_9000000011A_D01")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, f"pian-upravit-{pian}")
        self.wait(1)
        self.driver.execute_script("""map.setZoom(17); return map.getZoom();""")
        self.wait(2)
        self.ElementClick(By.LINK_TEXT, _("mapa.EditAddMarker"))
        self.wait(0.5)
        self.clickAtMapCoord(13.2262752, 50.3166203)
        self.wait(0.5)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editPianButton")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/update_PIAN")

        # U ADB
        time = self.getTime()
        self.ElementClick(By.ID, "el_dokumentacni_jednotka_X_C_9000000011A_D01")
        self.ElementClick(By.ID, "id_cislo_popisne")
        self.ElementSendKeys(By.ID, "id_cislo_popisne", "59")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editDjSubmitButton")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/update_ADB")

        # změna přístupnosti
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-5-2 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "actionSubmitBtn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/zmena_pristupnosti")

        # U  výškový bod
        time = self.getTime()
        self.ElementClick(By.ID, "el_dokumentacni_jednotka_X_C_9000000011A_D01")
        self.ElementClick(By.ID, "id_ADB-KRAS07-000001_vb-0-niveleta")
        self.ElementSendKeys(By.ID, "id_ADB-KRAS07-000001_vb-0-niveleta", "50")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editDjSubmitButton")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/update_vyskovy_bod")

        # D výškový bod
        time = self.getTime()
        self.ElementClick(By.ID, "el_dokumentacni_jednotka_X_C_9000000011A_D01")
        self.ElementClick(By.ID, f"vb-smazat-{pk_vyskovy_bod}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/delete_vyskovy_bod")

        # D ADB
        time = self.getTime()
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "adb-smazat-ADB-KRAS07-000001")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/delete_adb")

        # odpojení smazání PIAN
        time = self.getTime()
        self.ElementClick(By.ID, "el_dokumentacni_jednotka_X_C_9000000011A_D01")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, f"pian-odpojit-{pian}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/odpojeni_smazani_PIAN")

        # připojení PIAN
        self.createFedoraRecord("P-1121-100070", "archivar")
        time = self.getTime()
        self.ElementClick(By.ID, "el_dokumentacni_jednotka_X_C_9000000011A_D01")
        self.ElementClick(By.ID, "add_others")
        self.ElementClick(By.ID, "pian-pripojit-")
        self.ElementClick(By.ID, "select2-id_X-C-9000000011A-D01-pian-container")
        self.ElementSendKeys(By.CSS_SELECTOR, ".select2-search__field", "P-1121-100070")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editDjSubmitButton")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/pripojeni_PIAN")

        # PIAN odpojení bez smazání
        time = self.getTime()
        self.ElementClick(By.ID, "el_dokumentacni_jednotka_X_C_9000000011A_D01")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "pian-odpojit-P-1121-100070")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/odpojeni_PIAN")

        # změna ident_cely PIAN
        time = self.getTime()
        self.ElementClick(By.ID, "el_dokumentacni_jednotka_X_C_9000000011A_D01")
        self.ElementClick(By.ID, "add_others")
        self.ElementClick(By.ID, "show_menu_pian_new_id")
        self.wait(1)
        self.driver.execute_script("""map.setZoom(17); return map.getZoom();""")
        self.wait(2)
        self.ElementClick(By.LINK_TEXT, _("mapa.EditAddMarker"))
        self.wait(0.5)
        self.clickAtMapCoord(12.8224622, 50.3416221)
        self.wait(0.5)
        self.ElementClick(By.CSS_SELECTOR, ".filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "createPianSubmitButton")
        pian = Pian.objects.filter(dokumentacni_jednotky_pianu__ident_cely="X-C-9000000011A-D01").first().ident_cely
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, f"pian-potvrdit-{pian}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/ident_cely_PIAN")
        self.check_fedora_delete([f"record/{pian}"])

        # C DJ katastr
        self.createFedoraRecord("ruian-693154", "archivar")
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-9000000011A-D01-typ .btn")
        self.ElementClick(By.ID, "bs-select-1-3")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editDjSubmitButton")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/create_DJ_katastr")

        # U DJ katastr
        self.createFedoraRecord("ruian-600016", "archivar")
        time = self.getTime()
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "zmenit-katastr-X-C-9000000011A-D01")
        self.ElementClick(By.ID, "select2-id_katastr-container")
        self.ElementSendKeys(By.CSS_SELECTOR, ".select2-search__field", "Louny")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/update_DJ_katastr")

        # D DJ katastr
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-9000000011A-D01-typ .btn")
        self.ElementClick(By.ID, "bs-select-1-1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editDjSubmitButton")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/delete_DJ_katastr")

        # D DJ
        self.createFedoraRecord("X-C-91601363A", "archivar")
        self.createFedoraRecord("P-2212-010011", "archivar")
        self.goToAddress("/id/X-C-91601363A-D01")
        time = self.getTime()
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "dj-smazat-X-C-91601363A-D01")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_139/delete_DJ")
        logger.info("AkceProjektoveAkce.test_139_test_Fedory_PIAN_p_001.end")

    def test_140_test_Fedory_ADB_p_001(self):
        """Test 140 Test Fedory pro ADB (pozitivní scénář 1)

        Role:
            Archivář

        TestData:
            M-9002352A
            N-1541-000000005
            ADB-OPAV13-000001

        Steps:
            - Archivovat Akci s ADB

        Expected:
            - zápis dat do Fedory
        """
        logger.info("AkceProjektoveAkce.test_140_test_Fedory_ADB_p_001.start")
        self.login("archivar")

        # změna zmena stavu ADB
        self.createFedoraRecord("M-9002352A", "archivar")
        self.createFedoraRecord("N-1541-000000005", "archivar")
        self.createFedoraRecord("ADB-OPAV13-000001", "archivar")
        self.goToAddress("/arch-z/akce/detail/M-9002352A/dj/M-9002352A-D01")
        self.ElementClick(By.ID, "others")
        self.ElementClick(By.ID, "pian-potvrdit-N-1541-000000005")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        time = self.getTime()
        self.ElementClick(By.ID, "akce-archivovat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "arch_z/tests/resources/test_140/zmena_stavu")

        logger.info("AkceProjektoveAkce.test_140_test_Fedory_PIAN_p_002.end")

    def test_157_smazani_samostatne_akce_p_001(self):
        """Test 157 Smazání samostatné akce (pozitivní scénář 1)

        Test smazání samostatné akce. Scénář končí odstranění samostatné akce z databáze.

        Role:
            Archivář

        Preconditions:
            - Uživatel je přihlášen.
            - Samostatná akce ve stavu A2.

        TestData:
            M-9116053A

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře samostatnou akci ve stavu A2 (M-9116053A)
            - V panelu pro akce kliknout na  “Další akce” → “Smazat záznam”
            - V dalším dialogovém okně “Smazat archeologický záznam” kliknout na “Smazat”

        Expected:
            - Samostatná akce “M-9116053A” bude smazána z databáze.
        """
        logger.info("AkceSamostatneAkce.test_157_smazani_samostatne_akce_p_001.start")
        self.login("archivar")

        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="M-9116053A").first().stav, AZ_STAV_ODESLANY)
        self.createFedoraRecord("M-9116053A")
        self.createFedoraRecord("M-TX-195602015")
        self.uploadFileToFedora(540628, "projekt/tests/resources/test.pdf")
        self.goToAddress("/arch-z/akce/detail/M-9116053A")
        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "akce-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely="M-9116053A").count(), 0)
        logger.info("AkceSamostatneAkce.test_157_smazani_samostatne_akce_p_001.end")
