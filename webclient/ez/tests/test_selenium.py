import logging
import unittest

from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
from core.constants import EZ_STAV_ODESLANY, EZ_STAV_POTVRZENY, EZ_STAV_ZAPSANY
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

    def zapsat_zaznam(self):
        self.go_to_form_zapsat()
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-4 > .text")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".required-next .select2-search__field").send_keys("Pavloň")
        self.wait_for_select2_results()
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
        """Test 117 Zápsání nového externího zdroje typu kniha (pozitivní scénář 1)

        Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.

        Steps:
            - Uživatel se přihlásí
            - Uživatel klikne na menu Externí zdroje -> Zapsat
            - Uživatel vyplní data do formuláře
            - Uživatel klikne na tlačítko Zapsat

        Expected:
            - Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1
        """
        logger.info("AkceExterniZdroj.test_117_zapsani_externího_zdroje_p_001.start")
        self.login("archeolog")
        count_old = ExterniZdroj.objects.count()
        self.zapsat_zaznam()
        count_new = ExterniZdroj.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceExterniZdroj.test_117_zapsani_externího_zdroje_p_001.end")

    def test_118_odeslani_externího_zdroje_p_001(self):
        """Test 118 Odeslání záznamu Externí zdroj (pozitivní scénář 1)

        Test odeslání záznamu Externí zdroj. Scénář končí posunem záznamu ze stavu EZ1 do stavu EZ2.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - záznam Externí zdroj ve stavu EZ1

        TestData:
            X-BIB-000000001

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře modul “Externí zdroje”  → Vybrat → Filtr → ID obsahuje „X-BIB-000000001“ → Vybrat → otevřít záznam „X-BIB-000000001“
            - V panelu pro akce klikne uživatel na tlačítko “Odeslat” → v dialogovém okně “Odeslat dokument” klikne uživatel na tlačítko “Odeslat”

        Expected:
            - Záznam Externí zdroj se posune ze stavu EZ1 do stavu EZ2.
        """
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

    def test_119_pripojeni_akce_externího_zdroje_p_001(self):
        """Test 119 Připojení akce k externímu zdroji (pozitivní scénář 1)

        Test připojení záznamu Akce k záznamu Externí zdroj. Scénář končí vytvořením vazby mezi záznamy.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - záznam Externí zdroj ve stavu EZ1

        TestData:
            X-BIB-000000001

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře modul “Externí zdroje”  → Vybrat → Filtr → ID obsahuje „X-BIB-000000001“ → Vybrat → otevřít záznam „X-BIB-000000001“
            - V tabulce Připojené akce kliknout na “Připojit akci” → v dialogovém okně v poli “Připojovaný záznam” vyhledat záznam akce X-M-9000000007A, po vyhledání potvrdit kliknutím na “Připojit”

        Expected:
            - V tabulce připojených akcí je o jednu připojenou akci více
        """
        logger.info("AkceExterniZdroj.test_119_pripojeni_akce_externího_zdroje_p_001.start")
        self.login("archeolog")
        self.createFedoraRecord("X-BIB-000000001")
        id = ExterniZdroj.objects.filter(ident_cely="X-BIB-000000001").first().id
        ez_odkazy = ExterniOdkaz.objects.filter(externi_zdroj=id)
        count_old = ez_odkazy.filter(archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_AKCE).count()
        self.goToAddress("/id/X-BIB-000000001")
        self.ElementClick(By.ID, "eo-pripojit-akce")
        self.ElementClick(By.ID, "select2-id_arch_z-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("X-C-9000000001A")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        ez_odkazy = ExterniOdkaz.objects.filter(externi_zdroj=id)
        count_new = ez_odkazy.filter(archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_AKCE).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceExterniZdroj.test_119_pripojeni_akce_externího_zdroje_p_001.end")

    def test_120_pripojeni_lokality_externího_zdroje_p_001(self):
        """Test 120 Připojení lokality k externímu zdroji (pozitivní scénář 1)

        Test připojení záznamu Akce k záznamu Externí zdroj. Scénář končí vytvořením vazby mezi záznamy.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.
            - záznam Externí zdroj ve stavu EZ1

        TestData:
            C-K9000001
            X-BIB-000000001

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře modul “Externí zdroje”  → Vybrat → Filtr → ID obsahuje „X-BIB-000000001“ → Vybrat → otevřít záznam „X-BIB-000000001“
            - V tabulce Připojené lokality kliknout na “Připojit lokalitu” → v dialogovém okně v poli “Připojovaný záznam” vyhledat záznam lokality C-K9000001, po vyhledání potvrdit kliknutím na “Připojit”

        Expected:
            - V tabulce připojených lokalit je o jednu připojenou lokalitu více
        """
        logger.info("AkceExterniZdroj.test_120_pripojeni_lokality_externího_zdroje_p_001.start")
        self.login("archeolog")
        self.createFedoraRecord("X-BIB-000000001")
        id = ExterniZdroj.objects.filter(ident_cely="X-BIB-000000001").first().id
        ez_odkazy = ExterniOdkaz.objects.filter(externi_zdroj=id)
        count_old = ez_odkazy.filter(archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA).count()
        self.goToAddress("/id/X-BIB-000000001")
        self.ElementClick(By.ID, "eo-pripojit-lokalita")
        self.ElementClick(By.ID, "select2-id_arch_z-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("C-K9000001")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        ez_odkazy = ExterniOdkaz.objects.filter(externi_zdroj=id)
        count_new = ez_odkazy.filter(archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA).count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceExterniZdroj.test_120_pripojeni_lokality_externího_zdroje_p_001.end")

    def test_121_potvrzení_externího_zdroje_p_001(self):
        """Test 121 Potvrzení externího zdroje (pozitivní scénář 1)

        Test potvrzení záznamu v modulu Externí zdroje. Test končí posunem záznamu ze stavu EZ2 do EZ3.

        Role:
            Archivář

        Preconditions:
            - Uživatel je přihlášen
            - Záznam v modulu Externí zdroje ve stavu EZ2, který má vyplněny všechny náležitosti.

        TestData:
            X-BIB-1408662

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře modul “Externí zdroje”  → Vybrat → Filtr → ID obsahuje „X-BIB-1408662“ → Vybrat → otevřít záznam „X-BIB-1408662“
            - V panelu pro akce klikne uživatel na tlačítko “Potvrdit” → v dialogovém okně “Potvrdit externí zdroj” klikne uživatel na tlačítko “Potvrdit”

        Expected:
            - Záznam Externí zdroj se posune ze stavu EZ2 do stavu EZ3.
        """
        logger.info("AkceExterniZdroj.test_121_potvrzení_externího_zdroje_p_001.start")
        self.login("archivar")
        self.createFedoraRecord("X-BIB-1408662")
        dbID = ExterniZdroj.objects.filter(ident_cely="X-BIB-1408662").first().id
        self.assertEqual(ExterniZdroj.objects.filter(id=dbID).first().stav, EZ_STAV_ODESLANY)
        self.goToAddress("/id/X-BIB-1408662")
        self.ElementClick(By.ID, "ez-potvrdit")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(ExterniZdroj.objects.filter(id=dbID).first().stav, EZ_STAV_POTVRZENY)
        logger.info("AkceExterniZdroj.test_121_potvrzení_externího_zdroje_p_001.end")

    def test_122_zapsani_externího_zdroje_p_002(self):
        """Test 122 Zapsání nového externího zdroje (pozitivní scénář 2)

        Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.

        Steps:
            - Uživatel se přihlásí
            - Uživatel klikne na menu Externí zdroje -> Zapsat
            - Uživatel vyplní data do formuláře
            - Uživatel klikne na tlačítko Zapsat

        Expected:
            - Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1
        """
        logger.info("AkceExterniZdroj.test_122_zapsani_externího_zdroje_p_002.start")
        self.login("badatel")
        count_old = ExterniZdroj.objects.count()
        self.zapsat_zaznam()
        count_new = ExterniZdroj.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceExterniZdroj.test_122_zapsani_externího_zdroje_p_002.end")

    def test_123_odeslani_externího_zdroje_p_001(self):
        """Test 123 Odeslání záznamu Externí zdroj (pozitivní scénář 1)

        Test odeslání záznamu Externí zdroj. Scénář končí posunem záznamu ze stavu EZ1 do stavu EZ2.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.
            - záznam Externí zdroj ve stavu EZ1

        TestData:
            X-BIB-000000002

        Steps:
            - Uživatel se přihlásí
            - Uživatel otevře modul “Externí zdroje”  → Vybrat → Filtr → ID obsahuje „X-BIB-000000002“ → Vybrat → otevřít záznam „X-BIB-000000002“
            - V panelu pro akce klikne uživatel na tlačítko “Odeslat” → v dialogovém okně “Odeslat dokument” klikne uživatel na tlačítko “Odeslat”

        Expected:
            - Záznam Externí zdroj se posune ze stavu EZ1 do stavu EZ2.
        """
        logger.info("AkceExterniZdroj.test_123_odeslani_externího_zdroje_p_001.start")
        self.login("badatel")
        self.createFedoraRecord("X-BIB-000000002")
        self.assertEqual(ExterniZdroj.objects.filter(ident_cely="X-BIB-000000002").first().stav, EZ_STAV_ZAPSANY)
        id = ExterniZdroj.objects.filter(ident_cely="X-BIB-000000002").first().id
        self.goToAddress("/id/X-BIB-000000002")
        self.ElementClick(By.ID, "ez-odeslat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(ExterniZdroj.objects.filter(id=id).first().stav, EZ_STAV_ODESLANY)
        logger.info("AkceExterniZdroj.test_123_odeslani_externího_zdroje_p_001.end")

    def test_124_zapsani_externího_zdroje_p_003(self):
        """Test 124 Zápsání nového externího zdroje typu část knihy (pozitivní scénář 3)

        Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.

        Steps:
            - Uživatel se přihlásí
            - Uživatel klikne na menu Externí zdroje -> Zapsat
            - Uživatel vyplní data do formuláře
            - Uživatel klikne na tlačítko Zapsat

        Expected:
            - Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1
        """
        logger.info("AkceExterniZdroj.test_124_zapsani_externího_zdroje_p_003.start")
        self.login("archeolog")
        count_old = ExterniZdroj.objects.count()
        self.go_to_form_zapsat()
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_autori .select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys("havrlant")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_editori .select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_editori .select2-search__field").send_keys("abr")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_editori .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vydani_vzniku")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys("2023")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_nazev").send_keys("test")
        self.ElementClick(By.ID, "id_paginace_titulu")
        self.driver.find_element(By.ID, "id_paginace_titulu").send_keys("test1")
        self.ElementClick(By.ID, "id_sbornik_nazev")
        self.driver.find_element(By.ID, "id_sbornik_nazev").send_keys("Sborník")
        self.ElementClick(By.ID, "id_misto")
        self.driver.find_element(By.ID, "id_misto").send_keys("Praha")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        count_new = ExterniZdroj.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceExterniZdroj.test_124_zapsani_externího_zdroje_p_003.end")

    def test_125_zapsani_externího_zdroje_p_004(self):
        """Test 125 Zapsání nového externího zdroje typu článek v časopise (pozitivní scénář 4)

        Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.

        Steps:
            - Uživatel se přihlásí
            - Uživatel klikne na menu Externí zdroje -> Zapsat
            - Uživatel vyplní data do formuláře
            - Uživatel klikne na tlačítko Zapsat

        Expected:
            - Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1
        """
        logger.info("AkceExterniZdroj.test_125_zapsani_externího_zdroje_p_004.start")
        self.login("archeolog")
        count_old = ExterniZdroj.objects.count()
        self.go_to_form_zapsat()
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-2 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_autori .select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys("havrlant")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vydani_vzniku")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys("2024")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_nazev")
        self.driver.find_element(By.ID, "id_nazev").send_keys("test")
        self.ElementClick(By.ID, "id_casopis_denik_nazev")
        self.driver.find_element(By.ID, "id_casopis_denik_nazev").send_keys("nevim")
        self.ElementClick(By.ID, "id_casopis_rocnik")
        self.driver.find_element(By.ID, "id_casopis_rocnik").send_keys("2024")
        self.ElementClick(By.ID, "id_paginace_titulu")
        self.driver.find_element(By.ID, "id_paginace_titulu").send_keys("test1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        count_new = ExterniZdroj.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceExterniZdroj.test_125_zapsani_externího_zdroje_p_004.end")

    def test_126_zapsani_externího_zdroje_p_005(self):
        """Test 126 Zapsání nového externího zdroje typu článek v novinách (pozitivní scénář 5)

        Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.

        Steps:
            - Uživatel se přihlásí
            - Uživatel klikne na menu Externí zdroje -> Zapsat
            - Uživatel vyplní data do formuláře
            - Uživatel klikne na tlačítko Zapsat

        Expected:
            - Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1
        """
        logger.info("AkceExterniZdroj.test_126_zapsani_externího_zdroje_p_005.start")
        self.login("archeolog")
        count_old = ExterniZdroj.objects.count()
        self.go_to_form_zapsat()
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-3 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_autori .select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys("havrlant")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vydani_vzniku")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys("2024")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_nazev")
        self.driver.find_element(By.ID, "id_nazev").send_keys("clanek")
        self.ElementClick(By.ID, "id_casopis_denik_nazev")
        self.driver.find_element(By.ID, "id_casopis_denik_nazev").send_keys("nevim")
        self.driver.find_element(By.ID, "id_casopis_denik_nazev").send_keys("dikobraz")
        self.ElementClick(By.ID, "id_datum_rd")
        self.driver.find_element(By.ID, "id_datum_rd").send_keys("22.4.2023")
        self.ElementClick(By.ID, "id_paginace_titulu")
        self.driver.find_element(By.ID, "id_paginace_titulu").send_keys("test1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        count_new = ExterniZdroj.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceExterniZdroj.test_126_zapsani_externího_zdroje_p_005.end")

    def test_127_zapsani_externího_zdroje_p_006(self):
        """Test 127 Zapsání nového externího zdroje typu jiný zdroj (pozitivní scénář 6)

        Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

        Role:
            Archeolog

        Preconditions:
            - Uživatel je přihlášen.

        Steps:
            - Uživatel se přihlásí
            - Uživatel klikne na menu Externí zdroje -> Zapsat
            - Uživatel vyplní data do formuláře
            - Uživatel klikne na tlačítko Zapsat

        Expected:
            - Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1
        """
        logger.info("AkceExterniZdroj.test_127_zapsani_externího_zdroje_p_006.start")
        self.login("archeolog")
        count_old = ExterniZdroj.objects.count()
        self.go_to_form_zapsat()
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-5 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_autori .select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys("havrlant")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vydani_vzniku")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys("2024")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_nazev")
        self.driver.find_element(By.ID, "id_nazev").send_keys("clanek")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        count_new = ExterniZdroj.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceExterniZdroj.test_127_zapsani_externího_zdroje_p_006.end")

    def test_128_zapsani_externího_zdroje_p_007(self):
        """Test 128 Zápsání nového externího zdroje typu část knihy (pozitivní scénář 7)

        Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

        Role:
            Badatel

        Preconditions:
            Uživatel je přihlášen.

        Steps:
            - Uživatel se přihlásí
            - Uživatel klikne na menu Externí zdroje -> Zapsat
            - Uživatel vyplní data do formuláře
            - Uživatel klikne na tlačítko Zapsat

        Expected:
            - Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1
        """
        logger.info("AkceExterniZdroj.test_128_zapsani_externího_zdroje_p_007.start")
        self.login("badatel")
        count_old = ExterniZdroj.objects.count()
        self.go_to_form_zapsat()
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_autori .select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys("havrlant")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_editori .select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_editori .select2-search__field").send_keys("abr")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_editori .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vydani_vzniku")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys("2023")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_nazev").send_keys("test")
        self.ElementClick(By.ID, "id_paginace_titulu")
        self.driver.find_element(By.ID, "id_paginace_titulu").send_keys("test1")
        self.ElementClick(By.ID, "id_sbornik_nazev")
        self.driver.find_element(By.ID, "id_sbornik_nazev").send_keys("Sborník")
        self.ElementClick(By.ID, "id_misto")
        self.driver.find_element(By.ID, "id_misto").send_keys("Praha")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        count_new = ExterniZdroj.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceExterniZdroj.test_128_zapsani_externího_zdroje_p_007.end")

    def test_129_zapsani_externího_zdroje_p_008(self):
        """Test 129 Zapsání nového externího zdroje typu článek v časopise (pozitivní scénář 8)

        Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.

        Steps:
            - Uživatel se přihlásí
            - Uživatel klikne na menu Externí zdroje -> Zapsat
            - Uživatel vyplní data do formuláře
            - Uživatel klikne na tlačítko Zapsat

        Expected:
            - Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1
        """
        logger.info("AkceExterniZdroj.test_129_zapsani_externího_zdroje_p_008.start")
        self.login("badatel")
        count_old = ExterniZdroj.objects.count()
        self.go_to_form_zapsat()
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-2 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_autori .select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys("havrlant")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vydani_vzniku")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys("2024")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_nazev")
        self.driver.find_element(By.ID, "id_nazev").send_keys("test")
        self.ElementClick(By.ID, "id_casopis_denik_nazev")
        self.driver.find_element(By.ID, "id_casopis_denik_nazev").send_keys("nevim")
        self.ElementClick(By.ID, "id_casopis_rocnik")
        self.driver.find_element(By.ID, "id_casopis_rocnik").send_keys("2024")
        self.ElementClick(By.ID, "id_paginace_titulu")
        self.driver.find_element(By.ID, "id_paginace_titulu").send_keys("test1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        count_new = ExterniZdroj.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceExterniZdroj.test_129_zapsani_externího_zdroje_p_008.end")

    def test_130_zapsani_externího_zdroje_p_009(self):
        """Test 130 Zapsání nového externího zdroje typu článek v novinách (pozitivní scénář 9)

        Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.

        Steps:
            - Uživatel se přihlásí
            - Uživatel klikne na menu Externí zdroje -> Zapsat
            - Uživatel vyplní data do formuláře
            - Uživatel klikne na tlačítko Zapsat

        Expected:
            - Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1
        """
        logger.info("AkceExterniZdroj.test_130_zapsani_externího_zdroje_p_009.start")
        self.login("badatel")
        count_old = ExterniZdroj.objects.count()
        self.go_to_form_zapsat()
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-3 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_autori .select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys("havrlant")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vydani_vzniku")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys("2024")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_nazev")
        self.driver.find_element(By.ID, "id_nazev").send_keys("clanek")
        self.ElementClick(By.ID, "id_casopis_denik_nazev")
        self.driver.find_element(By.ID, "id_casopis_denik_nazev").send_keys("nevim")
        self.driver.find_element(By.ID, "id_casopis_denik_nazev").send_keys("dikobraz")
        self.ElementClick(By.ID, "id_datum_rd")
        self.driver.find_element(By.ID, "id_datum_rd").send_keys("22.4.2023")
        self.ElementClick(By.ID, "id_paginace_titulu")
        self.driver.find_element(By.ID, "id_paginace_titulu").send_keys("test1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        count_new = ExterniZdroj.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceExterniZdroj.test_130_zapsani_externího_zdroje_p_009.end")

    def test_131_zapsani_externího_zdroje_p_010(self):
        """Test 131 Zapsání nového externího zdroje typu jiný zdroj (pozitivní scénář 10)

        Test zapsání externího zdroje na stránce /ext-zdroj/zapsat. Končí zapsáním externího zdroje do databáze.

        Role:
            Badatel

        Preconditions:
            - Uživatel je přihlášen.

        Steps:
            - Uživatel se přihlásí
            - Uživatel klikne na menu Externí zdroje -> Zapsat
            - Uživatel vyplní data do formuláře
            - Uživatel klikne na tlačítko Zapsat

        Expected:
            - Po kliknutí na tlačítko Zapsat je v databázi o jeden externí zdroj více; externí zdroj změní svůj stav na EZ1
        """
        logger.info("AkceExterniZdroj.test_131_zapsani_externího_zdroje_p_010.start")
        self.login("badatel")
        count_old = ExterniZdroj.objects.count()
        self.go_to_form_zapsat()
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .btn")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-5 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_autori .select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys("havrlant")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_autori .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vydani_vzniku")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys("2024")
        self.driver.find_element(By.ID, "id_rok_vydani_vzniku").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_nazev")
        self.driver.find_element(By.ID, "id_nazev").send_keys("clanek")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        count_new = ExterniZdroj.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceExterniZdroj.test_131_zapsani_externího_zdroje_p_010.end")

    def test_136_test_Fedory_externi_zdroj_p_001(self):
        """Test 136 Test Fedory pro EZ (pozitivní scénář 1)

        Test zapsání dat do Fedory v EZ

        Role:
            Archeolog, Archivář

        TestData:
            X-BIB-1408662
            X-BIB-0926116
            X-BIB-0700016

        Steps:
            - Vytvoření EZ
            - Potvrzení EZ
            - Editace EZ
            - Smazání EZ

        Expected:
            - zápis dat do Fedory
        """
        logger.info("AkceExterniZdroj.test_136_test_Fedory_externi_zdroj_p_001.start")

        self.login("archeolog")
        # C EZ
        time = self.getTime()
        count_old = ExterniZdroj.objects.count()
        self.zapsat_zaznam()
        count_new = ExterniZdroj.objects.count()
        self.assertEqual(count_old + 1, count_new)
        self.check_fedora_change(time, "ez/tests/resources/test_136/create_EZ")
        self.logout()

        # změna ident_cely EZ
        self.login("archivar")
        self.createFedoraRecord("X-BIB-1408662", "archivar")
        self.createFedoraRecord("C-9120419A", "archivar")
        self.createFedoraRecord("C-9120749A", "archivar")
        self.createFedoraRecord("C-9133040A", "archivar")
        self.createFedoraRecord("C-K9000004", "archivar")
        time = self.getTime()
        dbID = ExterniZdroj.objects.filter(ident_cely="X-BIB-1408662").first().id
        self.assertEqual(ExterniZdroj.objects.filter(id=dbID).first().stav, EZ_STAV_ODESLANY)
        self.goToAddress("/id/X-BIB-1408662")
        self.ElementClick(By.ID, "ez-potvrdit")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(ExterniZdroj.objects.filter(id=dbID).first().stav, EZ_STAV_POTVRZENY)
        self.check_fedora_change(time, "ez/tests/resources/test_136/ident_cely")
        self.check_fedora_delete(["record/X-BIB-1408662"])

        # U EZ
        self.createFedoraRecord("X-BIB-0926116", "archivar")
        self.goToAddress("/id/X-BIB-0926116")
        time = self.getTime()
        self.ElementClick(By.ID, "edit-btn")
        self.ElementClick(By.ID, "id_misto")
        self.ElementSendKeys(By.ID, "id_misto", "Louny")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        self.check_fedora_change(time, "ez/tests/resources/test_136/update_EZ")

        # D EZ
        self.createFedoraRecord("X-BIB-0700016", "archivar")
        self.goToAddress("/id/X-BIB-0700016")
        count_old = ExterniZdroj.objects.count()
        time = self.getTime()

        self.ElementClick(By.ID, "otherOptions")
        self.ElementClick(By.ID, "ez-smazat")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        count_new = ExterniZdroj.objects.count()
        self.assertEqual(count_old - 1, count_new)
        self.check_fedora_change(time, "ez/tests/resources/test_136/delete_EZ")
        logger.info("AkceExterniZdroj.test_136_test_Fedory_externi_zdroj_p_001.end")

    def test_137_test_Fedory_externi_zdroj_p_002(self):
        """Test 137 Test Fedory pro EZ (pozitivní scénář 2)

        Test zapsání dat do Fedory v EZ

        Role:
            Archeolog

        TestData:
            X-BIB-000000001
            X-C-9000000001A
            C-K9000001

        Steps:
            Připojení AZ
            Připojení Lokalita
            Editace paginace AZ
            Editace paginace Lokalita
            Odpojení AZ
            Odpojení Lokalita

        Expected:
            - zápis dat do Fedory
        """
        logger.info("AkceExterniZdroj.test_137_test_Fedory_externi_zdroj_p_002.start")
        # připojení AZ
        self.login("archeolog")
        self.createFedoraRecord("X-BIB-000000001")
        self.createFedoraRecord("X-C-9000000001A")
        id = ExterniZdroj.objects.filter(ident_cely="X-BIB-000000001").first().id
        ez_odkazy = ExterniOdkaz.objects.filter(externi_zdroj=id)
        count_old = ez_odkazy.filter(archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_AKCE).count()
        self.goToAddress("/id/X-BIB-000000001")
        time = self.getTime()
        self.ElementClick(By.ID, "eo-pripojit-akce")
        self.ElementClick(By.ID, "select2-id_arch_z-container")
        self.ElementSendKeys(By.CSS_SELECTOR, ".select2-search__field", "X-C-9000000001A")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        ez_odkazy = ExterniOdkaz.objects.filter(externi_zdroj=id)
        count_new = ez_odkazy.filter(archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_AKCE).count()
        self.assertEqual(count_old + 1, count_new)
        self.check_fedora_change(time, "ez/tests/resources/test_137/pripojeni_AZ")

        # připojení lokalita
        self.createFedoraRecord("C-K9000001")
        time = self.getTime()
        self.ElementClick(By.ID, "eo-pripojit-lokalita")
        self.ElementClick(By.ID, "select2-id_arch_z-container")
        self.ElementSendKeys(By.CSS_SELECTOR, ".select2-search__field", "C-K9000001")
        self.wait_for_select2_results()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "ez/tests/resources/test_137/pripojeni_lokalita")

        # editace paginace AZ
        time = self.getTime()
        pk = (
            ExterniOdkaz.objects.filter(
                externi_zdroj__ident_cely="X-BIB-000000001", archeologicky_zaznam__ident_cely="X-C-9000000001A"
            )
            .first()
            .id
        )
        self.ElementClick(By.ID, f"ez-change-{pk}")
        self.ElementClick(By.ID, "id_paginace")
        self.ElementSendKeys(By.ID, "id_paginace", "22")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "ez/tests/resources/test_137/edit_paginace_EZ")

        # editace paginace lokalita
        time = self.getTime()
        pk = (
            ExterniOdkaz.objects.filter(
                externi_zdroj__ident_cely="X-BIB-000000001", archeologicky_zaznam__ident_cely="C-K9000001"
            )
            .first()
            .id
        )
        self.ElementClick(By.ID, f"ez-change-{pk}")
        self.ElementClick(By.ID, "id_paginace")
        self.ElementSendKeys(By.ID, "id_paginace", "22")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "ez/tests/resources/test_137/edit_paginace_lokalita")

        # odpojení AZ
        time = self.getTime()
        pk = (
            ExterniOdkaz.objects.filter(
                externi_zdroj__ident_cely="X-BIB-000000001", archeologicky_zaznam__ident_cely="X-C-9000000001A"
            )
            .first()
            .id
        )
        self.ElementClick(By.ID, f"ez-odpojit-{pk}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "ez/tests/resources/test_137/odpojeni_AZ")

        # odpojení lokalita
        time = self.getTime()
        pk = (
            ExterniOdkaz.objects.filter(
                externi_zdroj__ident_cely="X-BIB-000000001", archeologicky_zaznam__ident_cely="C-K9000001"
            )
            .first()
            .id
        )
        self.ElementClick(By.ID, f"ez-odpojit-{pk}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "ez/tests/resources/test_137/odpojeni_lokalita")

        logger.info("AkceExterniZdroj.test_137_test_Fedory_externi_zdroj_p_002.end")
