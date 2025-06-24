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
    def test_148_test_Fedora_uzivatel_001(self):
        # Scenar_148 Test Fedory pro uživatele
        logger.info("AkceUzivatel.test_148_test_Fedora_uzivatel_001.start")
        # C uzivatel
        self.goToAddress("/accounts/register/")
        time = self.getTime()
        self.driver.find_element(By.ID, "id_first_name").send_keys("Jan")
        self.driver.find_element(By.ID, "id_last_name").send_keys("Havrlant")
        self.driver.find_element(By.ID, "id_email").send_keys("jan.havrlant@centrum.cz")
        self.ElementClick(By.ID, "id_organizace")
        self.ElementClick(By.CSS_SELECTOR, "option:nth-child(30)")
        self.driver.find_element(By.ID, "id_password1").send_keys("te0s0t001")
        self.driver.find_element(By.ID, "id_password2").send_keys("te0s0t001")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "registerSumbitButton")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/create_uzivatel")

        # validate email
        self.assertEqual(len(mail.outbox), 1)
        match = re.search(r"aktivační klíč:\s*(\S+)", str(mail.outbox[0].body), re.IGNORECASE)
        activation_key = match.group(1)
        self.goToAddress("/accounts/activate/")
        self.driver.find_element(By.ID, "id_activation_key").send_keys(activation_key)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        # activate uzivatel
        time = self.getTime()
        match = re.search(r"/user/(\d+)/change/", str(mail.outbox[3].body))
        user_id = match.group(1)
        self.login("administrator")
        self.goToAddress(f"/admin/uzivatel/user/{user_id}/change/")
        self.ElementClick(By.ID, "id_is_active")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/activate_uzivatel")

        # C uzivatel admin
        time = self.getTime()
        self.goToAddress("/admin/uzivatel/user/add/")
        self.driver.find_element(By.ID, "id_email").send_keys("jan.havrlant2@centrum.cz")
        self.ElementClick(By.ID, "id_organizace")
        self.ElementClick(By.CSS_SELECTOR, "#id_organizace > option:nth-child(30)")
        self.driver.find_element(By.ID, "id_password1").send_keys("te0s0t001")
        self.driver.find_element(By.ID, "id_password2").send_keys("te0s0t001")
        self.ElementClick(By.ID, "id_is_active")
        self.driver.find_element(By.ID, "id_first_name").send_keys("Jan")
        self.driver.find_element(By.ID, "id_last_name").send_keys("Havrlant")
        self.ElementClick(By.CSS_SELECTOR, "#id_groups_from > option:nth-child(2)")
        element = self.driver.find_element(By.CSS_SELECTOR, "#id_groups_from > option:nth-child(2)")
        actions = ActionChains(self.driver)
        actions.double_click(element).perform()
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/create_uzivatel_admin")

        # U uzivatel admin
        time = self.getTime()
        pk = User.objects.filter(email="jan.havrlant2@centrum.cz").first().pk
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.driver.find_element(By.ID, "id_first_name").send_keys("Jan")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/update_uzivatel_admin")

        # U heslo admin
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/password/")
        self.driver.find_element(By.ID, "id_password1").send_keys("te0s0t002")
        self.driver.find_element(By.ID, "id_password2").send_keys("te0s0t002")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/update_heslo_admin")

        # D notifikace admin
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.ElementClick(By.ID, "id_User_notification_types-0-DELETE")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/delete_notifikace_admin")

        # U notifikace admin
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.ElementClick(By.CSS_SELECTOR, "#id_User_notification_types-0-usernotificationtype > option:nth-child(2)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/update_notifikace_admin")

        # C notifikace admin
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.ElementClick(By.CSS_SELECTOR, "#id_User_notification_types-5-usernotificationtype > option:nth-child(3)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/create_notifikace_admin")

        # C pes admin
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.ElementClick(By.ID, "id_User_notification_types-2-0-usernotificationtype")
        self.ElementClick(By.CSS_SELECTOR, "#id_User_notification_types-2-0-usernotificationtype > option:nth-child(2)")
        self.ElementClick(By.ID, "id_pes_set-0-object_id")
        self.ElementClick(By.CSS_SELECTOR, "#id_pes_set-0-object_id > option:nth-child(13)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/create_pes_admin")

        # U pes admin
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.ElementClick(By.ID, "id_pes_set-0-object_id")
        self.ElementClick(By.CSS_SELECTOR, "#id_pes_set-0-object_id > option:nth-child(11)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/update_pes_admin")

        # D pes admin
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/user/{pk}/change/")
        self.ElementClick(By.ID, "id_pes_set-0-DELETE")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".submit-row > .default")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_148/delete_pes_admin")

        # D uzivatel
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
        # Scenar_149 Test Fedory pro uživatele
        logger.info("AkceUzivatel.test_149_test_Fedora_uzivatel_002.start")

        # U uzivatel
        self.createFedoraRecord("U-005362")
        self.createFedoraRecord("U-005357")

        self.login("badatel")
        self.goToAddress("/uzivatel/edit/")
        time = self.getTime()
        self.driver.find_element(By.ID, "id_telefon").send_keys("608456654")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "actionSubmitBtn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/update_uzivatel")

        # U heslo
        time = self.getTime()
        self.driver.find_element(By.ID, "id_pass-old_password").send_keys(self._password("badatel"))
        self.driver.find_element(By.ID, "id_pass-password1").send_keys("popfgdh562645fghsdffdcb")
        self.driver.find_element(By.ID, "id_pass-password2").send_keys("popfgdh562645fghsdffdcb")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "actionSubmitBtn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/update_heslo")

        # D notifikace
        self.login("archeolog")
        self.createFedoraRecord("U-005357")
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

        # U notifikace
        time = self.getTime()
        self.ElementClick(By.ID, "id_notification_types_2")
        self.ElementClick(By.ID, "id_notification_types_3")
        self.ElementClick(By.ID, "id_notification_types_4")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "notifikaceSubmitBtn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/update_notifikace")

        # C notifikace
        time = self.getTime()
        self.ElementClick(By.ID, "id_notification_types_0")
        self.ElementClick(By.ID, "id_notification_types_1")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "notifikaceSubmitBtn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/create_notifikace")

        # C pes
        time = self.getTime()
        self.goToAddress("/notifikace-projekty/")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_notifications-notification_types > div > div:nth-child(1) > label")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_notifications-notification_types > div > div:nth-child(2) > label")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_ruiankraj-0-object_id .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-12 > .text")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_ruianokres-0-object_id .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-4-8 > .text")
        self.ElementClick(By.ID, "select2-id_ruiankatastr-0-object_id-container")
        self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_ruiankatastr-0-object_id-results > li:nth-child(4)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editPesSubmitButton")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/create_pes")

        # U pes
        time = self.getTime()
        self.ElementClick(By.CSS_SELECTOR, "#div_id_notifications-notification_types > div > div:nth-child(1) > label")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_ruiankraj-1-object_id .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-3 > .text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "editPesSubmitButton")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/update_pes")

        # D pes
        time = self.getTime()
        pks = Pes.objects.filter(user__ident_cely="U-005357").values_list("pk", flat=True)
        for pk in pks:
            self.ElementClick(By.ID, f"pes-smazat-{pk}")
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_149/delete_pes")

        logger.info("AkceUzivatel.test_149_test_Fedora_uzivatel_002.end")

    def test_150_test_Fedora_spoluprace_001(self):
        # Scenar_150 Test Fedory pro spolupráci PAS
        logger.info("AkceUzivatel.test_150_test_Fedora_spoluprace_001.start")
        self.createFedoraRecord("U-000393")
        self.createFedoraRecord("U-003726")
        self.createFedoraRecord("U-005357")
        self.createFedoraRecord("U-000408")
        self.createFedoraRecord("U-000127")

        # C spolupráce
        self.login("badatel1")
        time = self.getTime()
        self.goToAddress("/pas/spoluprace/zadost")
        self.driver.find_element(By.ID, "id_email_uzivatele").send_keys("archeolog1@arup.cas.cz")
        self.driver.find_element(By.ID, "id_text").send_keys("Zadost")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_150/create_spoluprace")
        self.assertEqual(len(mail.outbox), 1)
        mail_body = mail.outbox[0].body
        match = re.search(r"https?://[^/]+(?P<path>/pas/spoluprace/aktivace-email/\d+)", mail_body)
        path = match.group("path")

        # U mail spolupráce
        self.logout()
        self.login("archeolog")
        time = self.getTime()
        self.goToAddress(path)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-id-save")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_150/update_spoluprace_mail")

        # U spolupráce
        self.logout()
        self.login("archeolog")
        time = self.getTime()
        self.goToAddress("/pas/spoluprace/vyber?spolupracovnik=3402&stav=1")
        self.ElementClick(By.ID, "spoluprace-aktivovat-609")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_150/update_spoluprace")

        # D spolupráce
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
    def test_152_test_Fedora_organizace_001(self):
        # Scenar_152 Test Fedory pro organizaci
        logger.info("AkceOrganizace.test_152_test_Fedora_organizace_001.start")
        self.login("administrator")
        # C organizace
        time = self.getTime()
        self.goToAddress("/admin/uzivatel/organizace/add/")
        self.driver.find_element(By.ID, "id_nazev").send_keys("Argeolog sro")
        self.driver.find_element(By.ID, "id_nazev_zkraceny").send_keys("Argeolog")
        self.driver.find_element(By.ID, "id_nazev_zkraceny_en").send_keys("Argeologen")
        self.ElementClick(By.ID, "id_typ_organizace")
        self.ElementClick(By.CSS_SELECTOR, "#id_typ_organizace > option:nth-child(2)")
        self.ElementClick(By.ID, "id_zverejneni_pristupnost")
        self.ElementClick(By.CSS_SELECTOR, "#id_zverejneni_pristupnost > option:nth-child(3)")
        self.driver.find_element(By.ID, "id_email").send_keys("adsds@aaa.cz")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_152/create_organizce")
        pk = Organizace.objects.filter(nazev="Argeolog sro").first().pk

        # U organizace
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/organizace/{pk}/change/")
        self.ElementClick(By.ID, "id_typ_organizace")
        self.ElementClick(By.CSS_SELECTOR, "#id_typ_organizace > option:nth-child(3)")
        self.driver.find_element(By.ID, "id_nazev_zkraceny_en").clear()
        self.driver.find_element(By.ID, "id_nazev_zkraceny_en").send_keys("Argeologaj")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_152/update_organizce")

        # D organizace
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
    def test_153_test_Fedora_osoba_001(self):
        # Scenar_152 Test Fedory pro sosbu
        logger.info("AkceOsoba.test_153_test_Fedora_osoba_001.start")
        self.login("administrator")
        # C osoba
        time = self.getTime()
        self.goToAddress("/admin/uzivatel/osoba/add/")
        self.driver.find_element(By.ID, "id_jmeno").send_keys("Jan")
        self.driver.find_element(By.ID, "id_prijmeni").send_keys("Argeolog")
        self.driver.find_element(By.ID, "id_vypis_cely").send_keys("Archeolog, Jan")
        self.driver.find_element(By.ID, "id_vypis").send_keys("Archeolog, J")
        self.ElementClick(By.ID, "select2-id_orcid-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Havrlant")
        self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, "#select2-id_orcid-results > li:nth-child(1)")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_153/create_osoba")
        pk = Osoba.objects.filter(vypis_cely="Archeolog, Jan").first().pk

        # U osoba
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/osoba/{pk}/change/")
        self.driver.find_element(By.ID, "id_jmeno").clear()
        self.driver.find_element(By.ID, "id_jmeno").send_keys("Martin")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.NAME, "_save")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_153/update_osoba")

        # D osoba
        time = self.getTime()
        self.goToAddress(f"/admin/uzivatel/osoba/{pk}/change/")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".deletelink")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "input[type=submit]:nth-child(2)")
        self.check_fedora_change(time, "uzivatel/tests/resources/test_153/delete_osoba")

        logger.info("AkceOsoba.test_153_test_Fedora_osoba_001.end")
