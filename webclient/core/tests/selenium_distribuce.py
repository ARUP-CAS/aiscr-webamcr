"""
Sdílení pomocníci Selenium testů pro alternativní distribuce a paradata souborů (issue #4404).

Distribuce leží ve Fedoře v ``record/<ident>/file/<uuid>/<distribuce>`` a v databázi je
evidují jen záznamy historie souboru (``DIST01``/``DIST10``). Paradata leží v
``record/<ident>/file/<uuid>/paradata/<distribuce>`` a v databázi nemají nic. Pomocníci
zakládají a ověřují oba druhy kontejnerů stejně, aby se scénáře nerozcházely.

Mixin předpokládá atributy ``api_url``, ``auth``, ``driver`` a ``server_thread``
z ``BaseSeleniumTestClass``.
"""

import base64
import csv
import io
import json
import logging
import re
import shutil
import tempfile
import time
import zipfile
from contextlib import ExitStack, contextmanager
from datetime import datetime, timedelta
from unittest.mock import patch

import requests
from core.constants import NAHRANI_DISTRIBUCE
from core.repository_connector import FedoraRepositoryConnector, FedoraTransaction
from django.conf import settings
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

logger = logging.getLogger(__name__)

# Fáze importu, ve kterých úloha skončila (shodné s ``TERMINAL_PHASES`` stránky importu).
IMPORT_TERMINAL_PHASES = ("finished", "stopped", "canceled", "failed")
DELETED_TRIPLE = re.compile(r'<http://purl\.org/dc/terms/type>\s+"deleted"')


class DistribuceSeleniumMixin:
    """Pomocníci pro založení, stažení a ověření distribucí a paradat ve Fedoře."""

    def fedora_soubor_url(self, soubor):
        """
        Vrátí URL kontejneru souboru ve Fedoře podle aktuálního identu záznamu a UUID souboru.

        Soubor i navázaný záznam se znovu načtou z databáze, protože změna identu záznamu
        přesune soubor pod nový ident a s novým UUID.

        :param soubor: Instance ``Soubor`` uložená ve Fedoře.
        :return: URL ``…/record/<ident>/file/<uuid>``.
        """
        soubor.refresh_from_db()
        ident_cely = soubor.vazba.navazany_objekt.ident_cely
        return f"{self.api_url}{settings.FEDORA_SERVER_NAME}/record/{ident_cely}/file/{soubor.repository_uuid}"

    def pridej_distribuci(self, soubor, distribuce, nazev, mimetype, obsah, paradata=None):
        """
        Založí distribuci (a volitelně její paradata) přímo přes connector, stejně jako import.

        Zapíše kontejner distribuce, případně paradat, záznam ``DIST01`` do historie souboru pod
        ``ADMIN_USER`` a přegeneruje metadata záznamu — totéž co ``import_distributions_and_paradata``
        v ``cron.tasks.run_data_import``. Bez záznamu v historii by tabulka souborů distribuci
        nenabídla. Nakonec smaže cache paradat souboru.

        :param soubor: Instance ``Soubor`` uložená ve Fedoře.
        :param distribuce: Název distribuce, např. ``ocr/alto-xml``.
        :param nazev: Název souboru distribuce uložený do Fedory.
        :param mimetype: MIME typ distribuce.
        :param obsah: Binární obsah distribuce.
        :param paradata: Volitelná trojice ``(nazev, mimetype, obsah)`` paradat distribuce.
        """
        from heslar import hesla_dynamicka
        from historie.models import Historie
        from uzivatel.models import User

        admin_user = User.objects.get(pk=hesla_dynamicka.ADMIN_USER)
        record = soubor.vazba.navazany_objekt
        fedora_transaction = FedoraTransaction(transaction_user=admin_user)
        conn = FedoraRepositoryConnector(record, fedora_transaction)
        conn.save_distribution(soubor.repository_uuid, distribuce, nazev, mimetype, io.BytesIO(obsah))
        if paradata is not None:
            paradata_nazev, paradata_mimetype, paradata_obsah = paradata
            conn.save_paradata(
                soubor.repository_uuid, distribuce, paradata_nazev, paradata_mimetype, io.BytesIO(paradata_obsah)
            )
        if soubor.historie is None:
            soubor.suppress_signal = True
            soubor.create_soubor_vazby()
        Historie.objects.create(
            typ_zmeny=NAHRANI_DISTRIBUCE, uzivatel=admin_user, vazba=soubor.historie, poznamka=distribuce
        )
        record.active_transaction = fedora_transaction
        record.save_metadata(fedora_transaction)
        fedora_transaction.mark_transaction_as_closed()
        soubor.invalidate_paradata_cache()

    def _over_obsah_fedory(self, url, obsah, mimetype=None):
        """
        Ověří, že binární kontejner ve Fedoře existuje a má očekávaný obsah a MIME typ.

        :param url: URL binárního kontejneru.
        :param obsah: Očekávaný binární obsah.
        :param mimetype: Očekávaný MIME typ; ``None`` znamená bez kontroly.
        """
        response = requests.get(url, auth=self.auth)
        self.assertEqual(response.status_code, 200, f"Kontejner {url} neexistuje")
        self.assertEqual(response.content, obsah, f"Kontejner {url} má jiný obsah")
        if mimetype is not None:
            self.assertEqual(response.headers.get("Content-Type", "").split(";")[0].strip(), mimetype)

    def over_distribuci(self, soubor, distribuce, obsah, mimetype=None, paradata=None):
        """
        Ověří kontejner distribuce a volitelně jejích paradat ve Fedoře.

        :param soubor: Instance ``Soubor``, ke které distribuce patří.
        :param distribuce: Název distribuce.
        :param obsah: Očekávaný obsah distribuce.
        :param mimetype: Očekávaný MIME typ distribuce.
        :param paradata: Volitelná dvojice ``(mimetype, obsah)`` očekávaných paradat.
        """
        soubor_url = self.fedora_soubor_url(soubor)
        self._over_obsah_fedory(f"{soubor_url}/{distribuce}", obsah, mimetype)
        if paradata is not None:
            paradata_mimetype, paradata_obsah = paradata
            self._over_obsah_fedory(f"{soubor_url}/paradata/{distribuce}", paradata_obsah, paradata_mimetype)

    def over_smazani_distribuce(self, soubor_url, distribuce):
        """
        Ověří, že ve Fedoře nezůstala distribuce ani její paradata (404, nebo 410 s tombstonem).

        :param soubor_url: URL kontejneru souboru (viz :func:`fedora_soubor_url`).
        :param distribuce: Název distribuce.
        """
        for url in (f"{soubor_url}/{distribuce}", f"{soubor_url}/paradata/{distribuce}"):
            response = requests.get(url, auth=self.auth)
            self.assertIn(response.status_code, (404, 410), f"Kontejner {url} nebyl smazán")

    def over_soubor_oznacen_smazany(self, soubor_url):
        """
        Ověří, že kontejner souboru nese značku smazání ``dcterms:type "deleted"``.

        Smazání souboru v aplikaci kontejner ve Fedoře fyzicky neodstraní, jen ho takto označí
        (``FedoraRepositoryConnector.delete_binary_file``).

        :param soubor_url: URL kontejneru souboru.
        """
        response = requests.get(soubor_url, auth=self.auth, headers={"Accept": "application/n-triples"})
        self.assertEqual(response.status_code, 200, f"Kontejner {soubor_url} neexistuje")
        self.assertRegex(response.text, DELETED_TRIPLE, f"Kontejner {soubor_url} není označen jako smazaný")

    def stahni_jako_prihlaseny(self, href):
        """
        Stáhne odkaz se session přihlášeného uživatele z prohlížeče.

        Soubor stažený ve vzdáleném prohlížeči není z testu dostupný, proto se cookies prohlížeče
        přenesou do ``requests`` a odkaz se stáhne přímo z testovacího serveru.

        :param href: Absolutní URL odkazu ke stažení.
        :return: Odpověď ``requests.Response``.
        """
        session = requests.Session()
        for cookie in self.driver.get_cookies():
            session.cookies.set(cookie["name"], cookie["value"])
        return session.get(href, verify=False, allow_redirects=False)

    def vyber_distribuci_v_tabulce(self, soubor_pk, distribuce):
        """
        Vybere distribuci v rozbalovacím seznamu tabulky souborů.

        :param soubor_pk: PK souboru (řádek tabulky).
        :param distribuce: Název distribuce, který se vybere podle textu volby.
        :return: Pořadí vybrané volby, které je součástí ID odkazů ke stažení.
        """
        select = Select(self.driver.find_element(By.ID, f"file-distribution-{soubor_pk}"))
        select.select_by_visible_text(distribuce)
        return int(select.first_selected_option.get_attribute("value"))

    @staticmethod
    def nacti_importni_csv(path, nahrady=None):
        """
        Načte importní CSV z testovacích zdrojů a nahradí v něm zástupné hodnoty.

        Hodnoty známé až za běhu testu (např. ``Soubor.path`` s UUID přiděleným při nahrání)
        se v CSV zapisují jako ``{nazev}`` a nahradí se zde.

        :param path: Cesta k CSV souboru.
        :param nahrady: Slovník ``{"{zastupce}": "hodnota"}``.
        :return: Dvojice ``(obsah_csv_v_bytes, seznam_radku_jako_slovniky)``.
        """
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for zastupce, hodnota in (nahrady or {}).items():
            text = text.replace(zastupce, str(hodnota))
        return text.encode("utf-8"), list(csv.DictReader(io.StringIO(text)))

    def priprav_importni_adresar(self, zdrojovy_adresar):
        """
        Zkopíruje binární soubory importu do dočasného adresáře a nastaví ho jako importní.

        Import čte binární obsah z ``DIRECTORY_PATH`` a zapisuje do něj reporty, proto se nepoužívá
        adresář v repozitáři. Nastavení se ukládá do klonu testovací DB, který ``setUp`` obnovuje.

        :param zdrojovy_adresar: Adresář se soubory, na které CSV odkazují sloupcem ``nazev``.
        :return: Cesta k dočasnému importnímu adresáři.
        """
        from core.setting_models import CustomAdminSettings

        adresar = tempfile.mkdtemp(prefix="selenium_import_")
        self.addCleanup(shutil.rmtree, adresar, ignore_errors=True)
        shutil.copytree(zdrojovy_adresar, adresar, dirs_exist_ok=True)
        CustomAdminSettings.objects.update_or_create(
            item_id="import_directory_settings",
            defaults={"item_group": "import", "value": json.dumps({"DIRECTORY_PATH": adresar})},
        )
        return adresar

    def _uvolni_importni_ulohu(self, redis_connector, user_id):
        """
        Uvolní importní zámek úlohy, která po pádu testu zůstala v neukončené fázi.

        Redis se mezi testy neobnovuje, takže by držený zámek zablokoval import v dalších bězích.

        :param redis_connector: Spojení na Redis s dekódováním řetězců.
        :param user_id: ID uživatele, který import spustil.
        """
        from core.connectors import RedisConnector

        job_id = redis_connector.get(f"import_data_current_job_{user_id}")
        if not job_id or redis_connector.get(f"import_data_phase_{job_id}") in IMPORT_TERMINAL_PHASES:
            return
        lock_token = redis_connector.get(f"import_data_lock_token_{job_id}")
        if lock_token:
            RedisConnector.release_import_lock(redis_connector, lock_token)
        RedisConnector.delete_if_value_matches(redis_connector, f"import_data_current_job_{user_id}", job_id)
        RedisConnector.delete_if_value_matches(redis_connector, RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY, job_id)
        logger.warning("DistribuceSeleniumMixin.import_lock_released", extra={"job_id": job_id})

    @contextmanager
    def odstavka_systemu(self):
        """
        Po dobu bloku uvede systém do stavu probíhající odstávky.

        Založí v testovací DB odstávku, která začala před pěti minutami, a uloží ji i do cache
        ``maintenance``. Cache se jinak plní z DB jen při prázdném klíči a mohla by v ní zůstat
        hodnota „bez odstávky“ z dřívějška. Po skončení bloku se odstávka smaže a cache vyprázdní.

        Odstávka platí jen pro dobu importu: přihlašování a registrace jsou během ní blokované
        a přihlášený uživatel by byl po ``MAINTENANCE_LOGOUT_TIME`` odhlášen.
        """
        from core.models import OdstavkaSystemu
        from core.utils import get_timezone
        from django.core.cache import cache

        zacatek = datetime.now(get_timezone()) - timedelta(minutes=5)
        odstavka = OdstavkaSystemu.objects.create(
            info_od=zacatek.date(),
            datum_odstavky=zacatek.date(),
            cas_odstavky=zacatek.time().replace(microsecond=0),
            status=True,
        )
        cache.set("maintenance", odstavka, settings.AUTO_LOGOUT.get("MAINTENANCE_CACHE_TIMEOUT", 600))
        try:
            yield odstavka
        finally:
            odstavka.delete()
            cache.delete("maintenance")

    def spust_import(self, soubory_csv, akce, user_type="administrator", timeout=120):
        """
        Provede hromadný import přes stránku administrace a počká na jeho dokončení.

        Celery worker na testovacím serveru běží nad jinou databází, proto se validační i importní
        úloha místo ``.delay()`` spustí synchronně v požadavku testovacího serveru (běží ve stejném
        procesu jako test). Import lze spustit jen během odstávky, proto se po dobu importu zapne
        (viz :func:`odstavka_systemu`).

        :param soubory_csv: Slovník ``{"distribution.csv": bytes, ...}`` vložený do importního ZIP.
        :param akce: ``insert``, ``update`` nebo ``delete``.
        :param user_type: Testovací uživatel (superuživatel), pod kterým se import spustí.
        :param timeout: Maximální doba čekání na dokončení importu v sekundách.
        :raises AssertionError: Pokud import neskončí ve fázi ``finished``.
        """
        from core.connectors import RedisConnector
        from cron import tasks
        from uzivatel.models import User

        user = User.objects.get(email=self._username(user_type))
        if not user.is_superuser:
            # Import smí spustit jen superuživatel; vzorová DB to u testovacího administrátora nezaručuje.
            User.objects.filter(pk=user.pk).update(is_superuser=True)
        redis_connector = RedisConnector.get_connection_decode()
        self._uvolni_importni_ulohu(redis_connector, user.pk)
        self.addCleanup(self._uvolni_importni_ulohu, redis_connector, user.pk)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for nazev, obsah in soubory_csv.items():
                zf.writestr(nazev, obsah)

        validace = tasks.run_data_import_validation
        import_dat = tasks.run_data_import
        with ExitStack() as stack:
            validace_mock = stack.enter_context(patch("cron.tasks.run_data_import_validation"))
            validace_mock.delay.side_effect = validace
            import_mock = stack.enter_context(patch("cron.tasks.run_data_import"))
            import_mock.delay.side_effect = import_dat
            stack.enter_context(self.odstavka_systemu())

            self.goToAddress(reverse("admin:import_data"))
            Select(self.driver.find_element(By.ID, "id_performed_action")).select_by_value(akce)
            self.driver.execute_script(
                """
                const bytes = Uint8Array.from(atob(arguments[1]), (c) => c.charCodeAt(0));
                const file = new File([bytes], "import.zip", {type: "application/zip"});
                const transfer = new DataTransfer();
                transfer.items.add(file);
                document.getElementById(arguments[0]).files = transfer.files;
                """,
                "id_data_file",
                base64.b64encode(zip_buffer.getvalue()).decode("ascii"),
            )
            from core.tests.test_selenium import WaitForPageLoad

            with WaitForPageLoad(self.driver, wait_time=timeout):
                self.ElementClick(By.CSS_SELECTOR, "input[name='_save']")
            job_id = redis_connector.get(f"import_data_current_job_{user.pk}")
            self.assertIsNotNone(job_id, "Import se nezaložil")
            self.assertEqual(
                redis_connector.get(f"import_data_phase_{job_id}"),
                tasks.IMPORT_PHASE_AWAITING_APPROVAL,
                f"Validace importu neprošla: {redis_connector.get(f'import_data_status_message_tr_{job_id}')}",
            )
            self.assertEqual(redis_connector.get(f"import_data_valid_{job_id}"), "1", "Validace importu neprošla")
            # Tlačítko se povolí až po prvním dotazu stránky na stav úlohy.
            self.assertTrue(self.wait_for(self.ElementIsClickable, By.ID, "startImport"), "Import nelze spustit")
            self.ElementClick(By.ID, "startImport")
            konec = time.monotonic() + timeout
            phase = redis_connector.get(f"import_data_phase_{job_id}")
            while phase not in IMPORT_TERMINAL_PHASES and time.monotonic() < konec:
                time.sleep(1)
                phase = redis_connector.get(f"import_data_phase_{job_id}")
        self.assertEqual(
            phase,
            tasks.IMPORT_PHASE_FINISHED,
            f"Import skončil ve fázi {phase}: {redis_connector.get(f'import_data_status_message_tr_{job_id}')}",
        )
