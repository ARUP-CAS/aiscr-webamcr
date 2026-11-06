import logging
import unittest

from core.forms import ImportDataAdminForm
from core.models import Soubor
from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from django.conf import settings
from dokument.models import Dokument
from heslar import hesla_dynamicka
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

logger = logging.getLogger("tests")

# CSV pro import a binární soubory, na které odkazují sloupcem ``nazev``. V CSV lze použít
# zástupné hodnoty ``{soubor_id}`` a ``{soubor_path}``, které se doplní za běhu testu.
RESOURCES = "core/tests/resources/distribuce"


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class DistribuceSeleniumTest(BaseSeleniumTestClass):
    """Selenium testy alternativních distribucí a paradat souborů (issue #4404)."""

    def _nacti_testovaci_data(self, soubor):
        """
        Načte importní CSV a očekávaný obsah distribuce a paradat pro zadaný soubor.

        :param soubor: Instance ``Soubor``, ke které se distribuce a paradata vážou.
        :return: Slovník s obsahem CSV (``distribution_csv``, ``paradata_csv``), řádky CSV
            (``distribuce``, ``paradata``) a binárním obsahem (``obsah_distribuce``, ``obsah_paradat``).
        """
        nahrady = {"{soubor_id}": soubor.pk, "{soubor_path}": soubor.path}
        distribution_csv, distribuce = self.nacti_importni_csv(f"{RESOURCES}/distribution.csv", nahrady)
        paradata_csv, paradata = self.nacti_importni_csv(f"{RESOURCES}/paradata.csv", nahrady)
        self.assertEqual(len(distribuce), 1, "distribution.csv má mít jeden řádek")
        self.assertEqual(len(paradata), 1, "paradata.csv má mít jeden řádek")
        self.assertEqual(paradata[0]["distribution"], distribuce[0]["distribution"])
        with open(f"{RESOURCES}/{distribuce[0]['nazev']}", "rb") as f:
            obsah_distribuce = f.read()
        with open(f"{RESOURCES}/{paradata[0]['nazev']}", "rb") as f:
            obsah_paradat = f.read()
        return {
            "distribution_csv": distribution_csv,
            "paradata_csv": paradata_csv,
            "distribuce": distribuce[0],
            "paradata": paradata[0],
            "obsah_distribuce": obsah_distribuce,
            "obsah_paradat": obsah_paradat,
        }

    def _over_stazeni_z_tabulky(self, soubor, data):
        """
        Ověří nabídku distribuce a paradat v tabulce souborů a stažení obou odkazů.

        Na stránce detailu záznamu musí být otevřená tabulka souborů. Před výběrem distribuce
        je odkaz na její paradata skrytý, po výběru se zobrazí odkaz ke stažení distribuce
        i ikona paradat a oba vrátí obsah uložený importem.

        :param soubor: Instance ``Soubor`` (řádek tabulky).
        :param data: Testovací data z :func:`_nacti_testovaci_data`.
        """
        distribuce = data["distribuce"]
        paradata = data["paradata"]
        select = Select(self.driver.find_element(By.ID, f"file-distribution-{soubor.pk}"))
        self.assertEqual([o.text for o in select.options], ["orig", distribuce["distribution"]])
        self.assertFalse(self.driver.find_element(By.ID, f"file-paradata-{soubor.pk}-1").is_displayed())

        poradi = self.vyber_distribuci_v_tabulce(soubor.pk, distribuce["distribution"])
        odkaz_distribuce = self.driver.find_element(By.ID, f"file-download-{soubor.pk}-{poradi}")
        odkaz_paradat = self.driver.find_element(By.ID, f"file-paradata-{soubor.pk}-{poradi}")
        self.assertTrue(odkaz_distribuce.is_displayed())
        self.assertTrue(odkaz_paradat.is_displayed())

        for odkaz, radek, obsah in (
            (odkaz_distribuce, distribuce, data["obsah_distribuce"]),
            (odkaz_paradat, paradata, data["obsah_paradat"]),
        ):
            response = self.stahni_jako_prihlaseny(odkaz.get_attribute("href"))
            self.assertEqual(response.status_code, 200, odkaz.get_attribute("href"))
            self.assertEqual(response.content, obsah)
            self.assertTrue(response.headers.get("Content-Type", "").startswith(radek["mimetype"]))
            self.assertIn(radek["nazev"], response.headers.get("Content-Disposition", ""))

        # Distribuci, kterou soubor nemá, view nevydá (název z URL se do Fedory nedostane).
        odkaz_orig = self.driver.find_element(By.ID, f"file-download-{soubor.pk}-0").get_attribute("href")
        response = self.stahni_jako_prihlaseny(f"{odkaz_orig}?distribution=neexistuje")
        self.assertEqual(response.status_code, 404)

    def test_164_distribuce_paradata_import_p_001(self):
        """
        Test 164 Import, stažení a smazání distribuce a paradat (pozitivní scénář 1)

        Test hromadného importu alternativní distribuce a jejích paradat k existujícímu souboru,
        jejich nabídky a stažení v tabulce souborů, smazání distribuce importem a smazání souboru.

        Role:
        Administrátor (superuživatel)

        Preconditions:
        - Dokument M-TX-201604272 se souborem 53532 je uložen ve Fedoře.
        - Importní adresář obsahuje soubory z core/tests/resources/distribuce.

        TestData:
        M-TX-201604272, soubor 53532, core/tests/resources/distribuce/distribution.csv a paradata.csv

        Steps:
        - Administrátor provede import distribution.csv a paradata.csv s akcí Vložit
        - Otevře detail dokumentu a v tabulce souborů vybere distribuci, stáhne ji i paradata
        - Provede import distribution_delete.csv (jako distribution.csv) s akcí Smazat
        - Znovu provede import s akcí Vložit (na místo s tombstonem)
        - Smaže soubor v tabulce souborů

        Expected:
        - Po importu existují ve Fedoře kontejnery file/<uuid>/<distribuce> a file/<uuid>/paradata/<distribuce>
          s obsahem ze vstupních souborů a distribuce je v historii souboru.
        - Tabulka souborů nabízí distribuci a ikonu paradat, stažení vrací obsah ze vstupních souborů.
        - Smazání distribuce odstraní i její paradata a tabulka distribuci přestane nabízet.
        - Opětovné vložení na smazané místo projde.
        - Smazaný soubor je ve Fedoře označen jako smazaný a distribuci už nelze stáhnout.
        """
        logger.info("DistribuceSeleniumTest.test_164_distribuce_paradata_import_p_001.start")
        dokument = "M-TX-201604272"
        self.login("administrator")
        # Dokument ve vzorové DB nemá licenci, kterou schéma metadat vyžaduje; bez ní by XML neprošlo validací.
        Dokument.objects.filter(ident_cely=dokument, licence__isnull=True).update(
            licence_id=hesla_dynamicka.DOKUMENT_LICENCE_NEZNAMA
        )
        self.createFedoraRecord(dokument, "administrator")
        self.uploadFileToFedora(53532, "projekt/tests/resources/test.pdf", "administrator")
        soubor = Soubor.objects.get(pk=53532)
        data = self._nacti_testovaci_data(soubor)
        nazev_distribuce = data["distribuce"]["distribution"]
        ocekavana_distribuce = {
            "obsah": data["obsah_distribuce"],
            "mimetype": data["distribuce"]["mimetype"],
            "paradata": (data["paradata"]["mimetype"], data["obsah_paradat"]),
        }
        vlozeni = {"distribution.csv": data["distribution_csv"], "paradata.csv": data["paradata_csv"]}
        self.priprav_importni_adresar(RESOURCES)

        # Import distribuce a paradat
        time = self.getTime()
        self.spust_import(vlozeni, ImportDataAdminForm.PERFORMED_ACTION_INSERT)
        self.over_distribuci(soubor, nazev_distribuce, **ocekavana_distribuce)
        self.assertIn(nazev_distribuce, soubor.available_distributions())
        self.check_fedora_change(time, "core/tests/resources/test_164/import_dat")

        # Nabídka v tabulce souborů a stažení
        self.goToAddress(f"/dokument/detail/{dokument}")
        self._over_stazeni_z_tabulky(soubor, data)

        # Smazání distribuce importem maže i její paradata
        time = self.getTime()
        soubor_url = self.fedora_soubor_url(soubor)
        # Mazání očekává jen sloupce id a distribution, proto má vlastní CSV.
        smazani_csv, _ = self.nacti_importni_csv(f"{RESOURCES}/distribution_delete.csv", {"{soubor_id}": soubor.pk})
        self.spust_import({"distribution.csv": smazani_csv}, ImportDataAdminForm.PERFORMED_ACTION_DELETE)
        self.over_smazani_distribuce(soubor_url, nazev_distribuce)
        soubor.refresh_from_db()
        self.assertNotIn(nazev_distribuce, soubor.available_distributions())
        self.goToAddress(f"/dokument/detail/{dokument}")
        self.assertFalse(self.findElement(By.ID, f"file-distribution-{soubor.pk}"))
        self.check_fedora_change(time, "core/tests/resources/test_164/delete_dat")
        soubor_cesta = f"record/{dokument}/file/{soubor.repository_uuid}"
        self.check_fedora_delete([f"{soubor_cesta}/{nazev_distribuce}", f"{soubor_cesta}/paradata/{nazev_distribuce}"])
        # Opětovné vložení na místo, kde zůstal tombstone
        time = self.getTime()
        self.spust_import(vlozeni, ImportDataAdminForm.PERFORMED_ACTION_INSERT)
        self.over_distribuci(soubor, nazev_distribuce, **ocekavana_distribuce)
        self.check_fedora_change(time, "core/tests/resources/test_164/import_dat_1")

        # Smazání souboru
        time = self.getTime()
        self.goToAddress(f"/dokument/detail/{dokument}")
        poradi = self.vyber_distribuci_v_tabulce(soubor.pk, nazev_distribuce)
        odkaz_distribuce = self.driver.find_element(By.ID, f"file-download-{soubor.pk}-{poradi}").get_attribute("href")
        self.ElementClick(By.ID, f"file-smazat-{soubor.pk}")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertFalse(Soubor.objects.filter(pk=soubor.pk).exists())
        self.over_soubor_oznacen_smazany(soubor_url)
        self.assertNotEqual(self.stahni_jako_prihlaseny(odkaz_distribuce).status_code, 200)
        self.check_fedora_change(time, "core/tests/resources/test_164/delete_soubor")
        logger.info("DistribuceSeleniumTest.test_164_distribuce_paradata_import_p_001.end")

    def test_165_distribuce_paradata_zmena_identu_p_001(self):
        """
        Test 165 Distribuce a paradata při změně identu záznamu (pozitivní scénář 1)

        Test odeslání dokumentu s dočasným identem, jehož soubor má alternativní distribuci
        a paradata. Odesláním dokument dostane trvalý ident a soubor se ve Fedoře přesune
        do kontejneru nového identu.

        Role:
        Badatel

        Preconditions:
        - Uživatel je přihlášen.
        - Dokument je ve stavu D1 s dočasným identem.

        TestData:
        X-C-TX-000000003, core/tests/resources/distribuce

        Steps:
        - Uživatel nahraje k dokumentu soubor
        - K souboru se založí distribuce a paradata (sdílený pomocník, stejně jako import)
        - Uživatel dokument odešle

        Expected:
        - Distribuce a paradata jsou zkopírovány do kontejneru souboru pod novým identem.
        - Kontejner záznamu s dočasným identem je smazán.
        - Tabulka souborů na detailu dokumentu s novým identem nabízí distribuci i paradata ke stažení.
        """
        logger.info("DistribuceSeleniumTest.test_165_distribuce_paradata_zmena_identu_p_001.start")
        dokument = "X-C-TX-000000003"
        self.login("badatel")
        self.goToAddress(f"/dokument/detail/{dokument}")
        self.ElementClick(By.ID, "NahratSoubory")
        with WaitForPageLoad(self.driver):
            self.upload_file("dokument/tests/resources/test.jpg", "test.jpg")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "buttonUploadSubmit")
        soubor = Soubor.objects.filter(vazba__dokument_souboru__ident_cely=dokument).order_by("-pk").first()
        self.assertIsNotNone(soubor)

        data = self._nacti_testovaci_data(soubor)
        nazev_distribuce = data["distribuce"]["distribution"]
        ocekavana_distribuce = {
            "obsah": data["obsah_distribuce"],
            "mimetype": data["distribuce"]["mimetype"],
            "paradata": (data["paradata"]["mimetype"], data["obsah_paradat"]),
        }
        self.pridej_distribuci(
            soubor,
            nazev_distribuce,
            data["distribuce"]["nazev"],
            data["distribuce"]["mimetype"],
            data["obsah_distribuce"],
            paradata=(data["paradata"]["nazev"], data["paradata"]["mimetype"], data["obsah_paradat"]),
        )
        self.over_distribuci(soubor, nazev_distribuce, **ocekavana_distribuce)
        stary_soubor_url = self.fedora_soubor_url(soubor)

        # Odeslání dokumentu - změna identu
        time = self.getTime()
        self.goToAddress(f"/dokument/detail/{dokument}")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-odeslat > .app-controls-button-text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        novy_ident = self.driver.current_url.rstrip("/").split("/")[-1]
        self.assertNotEqual(novy_ident, dokument)

        self.assertNotEqual(self.fedora_soubor_url(soubor), stary_soubor_url)
        self.over_distribuci(soubor, nazev_distribuce, **ocekavana_distribuce)
        self.check_fedora_change(time, "core/tests/resources/test_165/ident_cely")
        self.check_fedora_delete([f"record/{dokument}"])

        self.goToAddress(f"/dokument/detail/{novy_ident}")
        self._over_stazeni_z_tabulky(soubor, data)
        logger.info("DistribuceSeleniumTest.test_165_distribuce_paradata_zmena_identu_p_001.end")
