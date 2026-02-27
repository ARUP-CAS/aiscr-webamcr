import logging
import re
import unittest

from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from django.conf import settings
from django.core import mail
from notifikace_projekty.models import Pes
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from uzivatel.models import Organizace, Osoba, User

logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceUzivatel(BaseSeleniumTestClass):
    """Implementuje komponentu ``AkceUzivatel`` v rámci aplikace."""

    def test_148_test_Fedora_uzivatel_001(self):
        """Test 148 Test Fedory pro uživatele (pozitivní scénář 1)

        Role:
            Administrator

        Steps:
            - Registrace uživatele
            - Validace mailu
            - Aktivace uživatele
            - Vytvoření uživatele administrátorem
            - Editace uživatele administrátorem
            - Změna hesla administrátorem
            - Smazání notifikace admin
            - Editace notifikace admin
            - Vytvoření notifikace admin
            - Vytvoření hlídacího psa admin
            - Editace hlídacího psa admin
            - Smazání hlídacího psa admin
            - Smazání uživatele admin

        Expected:
            - zápis dat do Fedory
        """
        logger.info("AkceUzivatel.test_148_test_Fedora_uzivatel_001.start")
        # Vytvoření uživatele
        self.goToAddress("/accounts/register/")
        time = self.getTime()
        self.ElementSendKeys(By.ID, "id_first_name", "Jan")
        self.ElementSendKeys(By.ID, "id_last_name", "Havrlant")
        self.ElementSendKeys(By.ID, "id_email", "jan.havrlant@centrum.cz")
        self.ElementClick(By.ID, "id_organizace")
        self.ElementClick(By.CSS_SELECTOR, "option:nth-child(30)")
        self.ElementSendKeys(By.ID, "id_password1", "te0s0t001")
        self.ElementSendKeys(By.ID, "id_password2", "te0s0t001")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "registerSumbitButton")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/create_uzivatel")

        # Ověření e-mailu
        self.assertEqual(len(mail.outbox), 1)
        match = re.search(r"aktivační klíč:\s*(\S+)", str(mail.outbox[0].body), re.IGNORECASE)
        activation_key = match.group(1)
        self.goToAddress("/accounts/activate/")
        self.driver.find_element(By.ID, "id_activation_key").send_keys(activation_key)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        # Aktivace uživatele
        time = self.getTime()
        match = re.search(r"/user/(\d+)/change/", str(mail.outbox[3].body))
        user_id = match.group(1)
        self.login("administrator")
        self.goToAddress(f"/admin/uzivatel/user/{user_id}/change/")
        self.ElementClick(By.ID, "id_is_active")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/activate_uzivatel")

        # Vytvoření uživatele administrátora
        time = self.getTime()
        self.goToAddress("/admin/uzivatel/user/add/")
        self.ElementSendKeys(By.ID, "id_email", "jan.havrlant2@centrum.cz")
        self.ElementClick(By.ID, "id_organizace")
        self.ElementClick(By.CSS_SELECTOR, "#id_organizace > option:nth-child(30)")
        self.ElementSendKeys(By.ID, "id_password1", "te0s0t001")
        self.ElementSendKeys(By.ID, "id_password2", "te0s0t001")
        self.ElementClick(By.ID, "id_is_active")
        self.ElementSendKeys(By.ID, "id_first_name", "Jan")
        self.ElementSendKeys(By.ID, "id_last_name", "Havrlant")
        self.ElementClick(By.CSS_SELECTOR, "#id_groups_from > option:nth-child(2)")
        element = self.driver.find_element(By.CSS_SELECTOR, "#id_groups_from > option:nth-child(2)")
        actions = ActionChains(self.driver)
        actions.double_click(element).perform()
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/create_uzivatel_admin")

        # Úprava uživatele administrátora
        time = self.getTime()
        pk = User.objects.filter(email="jan.havrlant2@centrum.cz").first().pk
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.ElementSendKeys(By.ID, "id_first_name", "Jan")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/update_uzivatel_admin")

        # Úprava hesla administrátora
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/password/")
        self.ElementSendKeys(By.ID, "id_password1", "te0s0t002")
        self.ElementSendKeys(By.ID, "id_password2", "te0s0t002")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/update_heslo_admin")

        # Smazání notifikace administrátora
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.ElementClick(By.ID, "id_User_notification_types-0-DELETE")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/delete_notifikace_admin")

        # Úprava notifikace administrátora
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.ElementClick(By.CSS_SELECTOR, "#id_User_notification_types-0-usernotificationtype > option:nth-child(2)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/update_notifikace_admin")

        # Vytvoření notifikace administrátora
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.ElementClick(By.CSS_SELECTOR, "#id_User_notification_types-5-usernotificationtype > option:nth-child(3)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/create_notifikace_admin")

        # Vytvoření PES administrátora
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.ElementClick(By.ID, "id_User_notification_types-2-0-usernotificationtype")
        self.ElementClick(By.CSS_SELECTOR, "#id_User_notification_types-2-0-usernotificationtype > option:nth-child(2)")
        self.ElementClick(By.ID, "id_pes_set-0-object_id")
        self.ElementClick(By.CSS_SELECTOR, "#id_pes_set-0-object_id > option:nth-child(13)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/create_pes_admin")

        # Úprava PES administrátora
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.ElementClick(By.ID, "id_pes_set-0-object_id")
        self.ElementClick(By.CSS_SELECTOR, "#id_pes_set-0-object_id > option:nth-child(11)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/update_pes_admin")

        # Smazání PES administrátora
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.ElementClick(By.ID, "id_pes_set-0-DELETE")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/delete_pes_admin")

        # Smazání uživatele
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.ElementClick(By.CSS_SELECTOR, "#user_form div.submit-row > a")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > input:nth-child(1)")
        self.ElementClick(By.CSS_SELECTOR, "#user_form div.submit-row > a")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "input[type=submit]:nth-child(2)")
        User.objects.filter(email="jan.havrlant2@centrum.cz").count()
        self.assertEqual(User.objects.filter(email="jan.havrlant2@centrum.cz").count(), 0)
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/delete_uzivatel")

        logger.info("AkceUzivatel.test_148_test_Fedora_uzivatel_001.end")

    def test_149_test_Fedora_uzivatel_002(self):
        """Test 149 Test Fedory pro uživatele (pozitivní scénář 2)

        Role:
            Badatel, Archeolog

        TestData:
            U-005362
            U-005357

        Steps:
            - Editace uživatele Badatel
            - Změna hesla Badatel
            - Smazání notifikace Archeolog
            - Editace notifikace Archeolog
            - Vytvoření notifikace Archeolog
            - Vytvoření hlídacího psa Archeolog
            - Editace hlídacího psa Archeolog
            - Smazaní hlídacího psa Archeolog

        Expected:
            - zápis dat do Fedory
        """
        logger.info("AkceUzivatel.test_149_test_Fedora_uzivatel_002.start")

        # Úprava uživatele
        self.createFedoraRecord("U-005362", "administrator")
        self.createFedoraRecord("U-005357", "administrator")

        self.login("badatel")
        self.goToAddress("/uzivatel/edit/")
        time = self.getTime()
        self.ElementSendKeys(By.ID, "id_telefon", "608456654")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "actionSubmitBtn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/update_uzivatel")

        # Úprava hesla
        time = self.getTime()
        self.driver.find_element(By.ID, "id_pass-old_password").send_keys(self._password("badatel"))
        self.ElementSendKeys(By.ID, "id_pass-password1", "popfgdh562645fghsdffdcb")
        self.ElementSendKeys(By.ID, "id_pass-password2", "popfgdh562645fghsdffdcb")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "actionSubmitBtn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/update_heslo")

        # Smazání notifikace
        self.login("archeolog")
        self.createFedoraRecord("U-005357", "administrator")
        self.goToAddress("/uzivatel/edit/")
        time = self.getTime()
        self.ElementClick(By.ID, "id_notification_types_0")
        self.ElementClick(By.ID, "id_notification_types_1")
        self.ElementClick(By.ID, "id_notification_types_2")
        self.ElementClick(By.ID, "id_notification_types_3")
        self.ElementClick(By.ID, "id_notification_types_4")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "notifikaceSubmitBtn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/delete_notifikace")

        # Úprava notifikace
        time = self.getTime()
        self.ElementClick(By.ID, "id_notification_types_2")
        self.ElementClick(By.ID, "id_notification_types_3")
        self.ElementClick(By.ID, "id_notification_types_4")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "notifikaceSubmitBtn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/update_notifikace")

        # Vytvoření notifikace
        time = self.getTime()
        self.ElementClick(By.ID, "id_notification_types_0")
        self.ElementClick(By.ID, "id_notification_types_1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "notifikaceSubmitBtn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/create_notifikace")

        # Vytvoření PES
        time = self.getTime()
        self.goToAddress("/notifikace-projekty/")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_notifications-notification_types > div > div:nth-child(1) > label")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_notifications-notification_types > div > div:nth-child(2) > label")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_ruiankraj-0-object_id .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-12 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_ruianokres-0-object_id .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-4-8 > .text")
        self.ElementClick(By.ID, "select2-id_ruiankatastr-0-object_id-container")
        self.wait_for_select2_results()
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_ruiankatastr-0-object_id-results > li:nth-child(4)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editPesSubmitButton")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/create_pes")

        # Úprava PES
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, "#div_id_notifications-notification_types > div > div:nth-child(1) > label")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_ruiankraj-1-object_id .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-3 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editPesSubmitButton")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/update_pes")

        # Smazání PES
        time = self.getTime()
        pks = Pes.objects.filter(user__ident_cely="U-005357").values_list("pk", flat=True)
        for pk in pks:
            self.ElementClick(By.ID, f"pes-smazat-{pk}")
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/delete_pes")

        logger.info("AkceUzivatel.test_149_test_Fedora_uzivatel_002.end")

    def test_150_test_Fedora_spoluprace_001(self):
        """Test 150 Test Fedory pro spolupráci PAS (pozitivní scénář 1)

        Role:
            Badatel, Archeolog

        TestData:
            U-000393
            U-003726
            U-005357
            U-000408
            U-000127

        Steps:
            - Vytvoření žádosti o spolupráci v PAS - Badatel
            - Potvrzení spolupráce z mailu - Archeolog
            - Editace spolupráce - Archeolog
            - Smazání spolupráce  - Administrator

        Expected:
            - zápis dat do Fedory
        """
        logger.info("AkceUzivatel.test_150_test_Fedora_spoluprace_001.start")
        self.createFedoraRecord("U-000393", "administrator")
        self.createFedoraRecord("U-003726", "administrator")
        self.createFedoraRecord("U-005357", "administrator")
        self.createFedoraRecord("U-000408", "administrator")
        self.createFedoraRecord("U-000127", "administrator")

        # Vytvoření spolupráce
        self.login("badatel1")
        time = self.getTime()
        self.goToAddress("/pas/spoluprace/zadost")
        self.ElementSendKeys(By.ID, "id_email_uzivatele", "archeolog1@arup.cas.cz")
        self.ElementSendKeys(By.ID, "id_text", "Zadost")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_150/create_spoluprace")
        self.assertEqual(len(mail.outbox), 1)
        mail_body = mail.outbox[0].body
        match = re.search(r"https?://[^/]+(?P<path>/pas/spoluprace/aktivace-email/\d+)", mail_body)
        path = match.group("path")

        # Úprava e-mailu spolupráce
        self.logout()
        self.login("archeolog")
        time = self.getTime()
        self.goToAddress(path)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-id-save")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_150/update_spoluprace_mail")

        # Úprava spolupráce
        self.logout()
        self.login("archeolog")
        time = self.getTime()
        self.goToAddress("/pas/spoluprace/vyber?spolupracovnik=3402&stav=1")
        self.ElementClick(By.ID, "spoluprace-aktivovat-609")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_150/update_spoluprace")

        # Smazání spolupráce
        self.logout()
        self.login("administrator")
        time = self.getTime()
        self.goToAddress("/pas/spoluprace/vyber?spolupracovnik=3402&stav=1")
        self.ElementClick(By.ID, "spoluprace-smazat-604")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_150/delete_spoluprace")

        logger.info("AkceUzivatel.test_150_test_Fedora_spoluprace_001.end")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceOrganizace(BaseSeleniumTestClass):
    """Implementuje komponentu ``AkceOrganizace`` v rámci aplikace."""

    def test_152_test_Fedora_organizace_001(self):
        """Test 152 Test Fedory pro organizaci (pozitivní scénář 1)

        Role:
            Administrator

        Steps:
            - Vytvoření organizace
            - Editace organizace
            - Smazání organizace

        Expected:
            - zápis dat do Fedory
        """
        logger.info("AkceOrganizace.test_152_test_Fedora_organizace_001.start")
        self.login("administrator")
        # Vytvoření organizace
        time = self.getTime()
        self.goToAddress("/admin/uzivatel/organizace/add/")
        self.ElementSendKeys(By.ID, "id_nazev", "Argeolog sro")
        self.ElementSendKeys(By.ID, "id_nazev_zkraceny", "Argeolog")
        self.ElementSendKeys(By.ID, "id_nazev_zkraceny_en", "Argeologen")
        self.ElementClick(By.ID, "id_typ_organizace")
        self.ElementClick(By.CSS_SELECTOR, "#id_typ_organizace > option:nth-child(2)")
        self.ElementClick(By.ID, "id_zverejneni_pristupnost")
        self.ElementClick(By.CSS_SELECTOR, "#id_zverejneni_pristupnost > option:nth-child(3)")
        self.ElementSendKeys(By.ID, "id_email", "adsds@aaa.cz")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_152/create_organizce")
        pk = Organizace.objects.filter(nazev="Argeolog sro").first().pk

        # Úprava organizace
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/organizace/{pk}/change/")
        self.ElementClick(By.ID, "id_typ_organizace")
        self.ElementClick(By.CSS_SELECTOR, "#id_typ_organizace > option:nth-child(3)")
        self.driver.find_element(By.ID, "id_nazev_zkraceny_en").clear()
        self.ElementSendKeys(By.ID, "id_nazev_zkraceny_en", "Argeologaj")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_152/update_organizce")

        # Smazání organizace
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/organizace/{pk}/change/")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".deletelink")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "input[type=submit]:nth-child(2)")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_152/delete_organizce")

        logger.info("AkceOrganizace.test_152_test_Fedora_organizace_001.end")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceOsoba(BaseSeleniumTestClass):
    """Implementuje komponentu ``AkceOsoba`` v rámci aplikace."""

    def test_153_test_Fedora_osoba_001(self):
        """Test 153 Test Fedory pro osobu (pozitivní scénář 1)

        Role:
            Administrator

        Steps:
            - Vztvoření osoby
            - Editace osoby
            - Smazání osoby

        Expected:
            - zápis dat do Fedory
        """
        logger.info("AkceOsoba.test_153_test_Fedora_osoba_001.start")
        self.login("administrator")
        # Vytvoření osoby
        time = self.getTime()
        self.goToAddress("/admin/uzivatel/osoba/add/")
        self.ElementSendKeys(By.ID, "id_jmeno", "Jan")
        self.ElementSendKeys(By.ID, "id_prijmeni", "Argeolog")
        self.ElementSendKeys(By.ID, "id_vypis_cely", "Archeolog, Jan")
        self.ElementSendKeys(By.ID, "id_vypis", "Archeolog, J")
        self.ElementClick(By.ID, "select2-id_orcid-container")
        self.ElementSendKeys(By.CSS_SELECTOR, ".select2-search__field", "Havrlant")
        self.wait_for_select2_results()
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_orcid-results > li:nth-child(1)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_153/create_osoba")
        pk = Osoba.objects.filter(vypis_cely="Archeolog, Jan").first().pk

        # Úprava osoby
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/osoba/{pk}/change/")
        self.driver.find_element(By.ID, "id_jmeno").clear()
        self.ElementSendKeys(By.ID, "id_jmeno", "Martin")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_153/update_osoba")

        # Smazání osoby
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/osoba/{pk}/change/")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".deletelink")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "input[type=submit]:nth-child(2)")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_153/delete_osoba")

        logger.info("AkceOsoba.test_153_test_Fedora_osoba_001.end")
