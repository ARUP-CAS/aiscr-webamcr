import base64
import json
import logging
import os
import os.path
import re
import time
from collections import Counter
from datetime import datetime, timezone
from io import BytesIO
from typing import Optional
from unittest.util import safe_repr
from urllib.parse import urlparse

import pandas
import psycopg2
import requests
from cacheops import invalidate_all
from core.ident_cely import get_record_from_ident
from core.repository_connector import FedoraError, FedoraTransaction
from core.tests.custom_server import WerkzeugServerThread
from core.tests.runner import USERS
from django.conf import settings
from django.db import connection
from django.http import Http404
from django.test import LiveServerTestCase
from lxml import etree
from PIL import Image, ImageChops
from rdflib import Graph, Literal, URIRef
from selenium import webdriver
from selenium.webdriver.common.by import By
from uzivatel.models import User
from xml_generator.models import ModelWithMetadata

from webclient.settings.base import get_secret

logger = logging.getLogger(__name__)


class WaitForPageLoad:
    def __init__(self, browser):
        self.browser = browser

    def __enter__(self):
        self.old_page = self.browser.find_element(By.TAG_NAME, "html")

    def page_has_loaded(self):
        new_page = self.browser.find_element(By.TAG_NAME, "html")
        return new_page.id != self.old_page.id

    def page_is_ready(self):
        page_state = self.browser.execute_script("return document.readyState;")
        return page_state == "complete"

    def __exit__(self, *_):
        self.wait_for(self.page_has_loaded)
        self.wait_for(self.page_is_ready)

    def wait_for(self, condition_function):
        start_time = time.time()
        while time.time() < start_time + 20:
            if condition_function():
                return True
            else:
                time.sleep(0.5)
        logger.error("SeleniumTest.WaitForPageLoad.timeout")


# @unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
# @override_settings(DEBUG=True)
class BaseSeleniumTestClass(LiveServerTestCase):
    # port = 8808
    host = "0.0.0.0"
    del settings.DATABASES["test_db"]
    databases = {"default", "urgent"}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.server_thread.is_ready.wait()
        if cls.server_thread.error:
            raise RuntimeError(f"Chyba při spuštění serveru: {cls.server_thread.error}")

    @classmethod
    def tearDownClass(cls):
        cls.server_thread.terminate()
        super().tearDownClass()

    @classmethod
    def _create_server_thread(cls, connections_override):
        """Vytvoření vlastního serverového vlákna"""
        return WerkzeugServerThread(host=cls.host, port=cls.port)

    @classmethod
    def _terminate_thread(cls):
        pass

    @classmethod
    def get_base_test_data(cls):
        pass

    def go_to_form(self):
        pass

    def setUp(self):
        logger.debug("core.tests.test_selenium.BaseSeleniumTestClass.setup.start")
        self.wipe_Fedora()
        self.clone_Database()

        options = webdriver.FirefoxOptions()
        # options = webdriver.ChromeOptions()
        if settings.USE_REMOTE_WEB_BROWSER:
            self.driver = webdriver.Remote(
                command_executor=f"http://{settings.SELENIMUM_ADDRESS}:{settings.SELENIUM_PORT}/wd/hub", options=options
            )
        else:
            self.driver = webdriver.Firefox()

        # self.driver=webdriver.Chrome()
        self.driver.implicitly_wait(2)
        self.wait_interval = 2
        logger.debug("core.tests.test_selenium.BaseSeleniumTestClass.setup.end")

    def get_container_content(self, container_path):
        headers = {}
        response = requests.get(container_path, auth=self.auth, headers=headers)
        members = []
        if response.status_code == 200:
            res = response.text.split("\n")
            for n in res:
                if "ldp:contains" in n:
                    start = n.find("<")
                    end = n.find(">", start)
                    if start != -1 and end != -1:
                        result = n[start + 1 : end]
                        members.append(result)
        return members

    def save_container_content(self, container_path, path):
        headers = {}
        response = requests.get(container_path, auth=self.auth, headers=headers)
        members = []
        extensions = {
            "text/turtle": "turtle",
            "application/xml": "xml",
            "image/jpeg": "jpg",
            "image/png": "png",
            "application/zip": "zip",
            "application/pdf": "pdf",
        }
        filename = (
            str(container_path.split(f"/{settings.FEDORA_SERVER_NAME}/", 1)[1]).replace("/", "__").replace(":", "--")
        )
        extension = extensions[response.headers.get("Content-Type", "").split(";")[0].strip()]
        if "__file__" in filename:
            filename = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "", filename)
        if response.status_code == 200:
            f = open(f"{path}/{filename}.{extension}", "wb")
            if extension == "xml":
                f.write(response.content.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
            else:
                f.write(response.content)
            f.close()
        return members

    def porovnej_png_obsah(self, bin1, bin2):
        """
        Porovná dva PNG obrázky zadané jako binární řetězce.
        Vrací True, pokud jsou zcela totožné.
        """
        try:
            img1 = Image.open(BytesIO(bin1)).convert("RGBA")
            img2 = Image.open(BytesIO(bin2)).convert("RGBA")
        except Exception:
            return False

        if img1.size != img2.size or img1.mode != img2.mode:
            return False

        rozdil = ImageChops.difference(img1, img2)
        return not rozdil.getbbox()

    def check_container_content(self, container_path, path):
        headers = {}
        response = requests.get(container_path, auth=self.auth, headers=headers)
        members = []
        extensions = {
            "text/turtle": "turtle",
            "application/xml": "xml",
            "image/jpeg": "jpg",
            "image/png": "png",
            "application/zip": "zip",
            "application/pdf": "pdf",
        }
        filename = (
            str(container_path.split(f"/{settings.FEDORA_SERVER_NAME}/", 1)[1]).replace("/", "__").replace(":", "--")
        )
        extension = extensions[response.headers.get("Content-Type", "").split(";")[0].strip()]
        if "__file__" in filename:
            filename = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "", filename)
        if response.status_code == 200:
            f = open(f"{path}/{filename}.{extension}", "rb")
            sample_file = f.read()
            f.close()
        if extension == "turtle":
            assert self.porovnej_rdf_obsah(
                response.content,
                sample_file,
                ignorovat_predikaty=["fedora:created", "fedora:lastModified", "premis:hasMessageDigest"],
            )
        elif extension == "xml":
            assert self.porovnej_xml_bez_ignorovanych(
                sample_file,
                response.content,
                ignorovane_tagy=["amcr:datum_zmeny", "amcr:datum_registrace", "amcr:datum_zverejneni"],
            )
        elif extension == "png":
            assert self.porovnej_png_obsah(sample_file, response.content)
        else:
            res = sample_file == response.content
            if res is False:
                logger.error(
                    "BaseSeleniumTestClass.fedora_error.check_container_content.file",
                    extra={"data": filename},
                )

            assert res

        return members

    api_url = f"{settings.FEDORA_PROTOCOL}://{settings.FEDORA_SERVER_HOSTNAME}:{settings.FEDORA_PORT_NUMBER}/rest/"
    auth = requests.auth.HTTPBasicAuth(settings.FEDORA_ADMIN_USER, settings.FEDORA_ADMIN_USER_PASSWORD)

    def purge_container(self, container_path):
        response = requests.delete(container_path + "/fcr:tombstone", auth=self.auth)
        if not str(response.status_code).startswith("2"):
            logger.error(
                "core.tests.test_selenium.BaseSeleniumTestClass.purge_container.failed",
                extra={"response": response.text},
            )

    def delete_container(self, container_path):
        response = requests.delete(container_path, auth=self.auth)
        if not str(response.status_code).startswith("2"):
            logger.error(
                "core.tests.test_selenium.BaseSeleniumTestClass.delete_container.failed",
                extra={"response": response.text},
            )

    def wipe_Fedora_dir(self, name, deep):
        mem = self.get_container_content(name)
        for item in mem:
            self.wipe_Fedora_dir(item, deep + 1)
            if deep > 1:
                self.delete_container(item)

    def find_files(self, directory, filename):
        matches = []
        for root, _, files in os.walk(directory):
            if filename in files:
                matches.append(os.path.join(root, filename))
        return matches

    def delete_tombstones(self, url, name, dir):
        results = self.find_files(dir, "fcr-root.json")
        for res in results:
            if os.path.isfile(res):
                with open(res, "r", encoding="utf-8") as file:
                    data = json.load(file)
                if data["deleted"] is True and name in data["id"]:
                    matches = data["id"][data["id"].find("/") + 1 :]
                    self.purge_container(f"{url}{matches}")

    def save_fedora_change(self, time, path):
        headers = {}
        response = requests.get(
            f"{self.api_url}fcr:search?condition=fedora_id={self.api_url}{settings.FEDORA_SERVER_NAME}/*&condition=modified>{time}&offset=0&max_results=100&format=json",
            auth=self.auth,
            headers=headers,
        )

        if response.status_code == 200:
            os.makedirs(path, exist_ok=True)
            f = open(f"{path}/index.json", "wb")
            f.write(response.content)
            f.close()
            res = json.loads(response.text)
            for n in res["items"]:
                self.save_container_content(n["fedora_id"], path)

    def check_fedora_change(self, time, path):
        # self.save_fedora_change(time, path)
        if os.name == "nt":
            self.wait(1.5)
            self.save_fedora_change(
                time,
                f"{settings.TEST_SCREENSHOT_PATH}result_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')}_{path.rsplit('/', 1)[-1]}",
            )

        headers = {}
        response = requests.get(
            f"{self.api_url}fcr:search?condition=fedora_id={self.api_url}{settings.FEDORA_SERVER_NAME}/*&condition=modified>{time}&offset=0&max_results=100&format=json",
            auth=self.auth,
            headers=headers,
        )
        if response.status_code == 200:
            os.makedirs(path, exist_ok=True)
            f = open(f"{path}/index.json", "rb")
            json_vzor = f.read()
            f.close()

            assert self.porovnej_json_rovnost(
                vzor_json_text=json_vzor,
                vystup_json_text=response.content,
                klice_k_ignoraci=["created", "modified", "content_size"],
            )

            res = json.loads(response.text)
            for n in res["items"]:
                self.check_container_content(n["fedora_id"], path)

    def check_fedora_delete(self, records):
        headers = {}
        for item in records:
            response = requests.get(
                f"{self.api_url}{settings.FEDORA_SERVER_NAME}/{item}", auth=self.auth, headers=headers
            )
            self.assertIn(response.status_code, [410, 404])

    def wipe_Fedora(self):
        self.wipe_Fedora_dir(f"{self.api_url}{settings.FEDORA_SERVER_NAME}/model", 0)
        self.wipe_Fedora_dir(f"{self.api_url}{settings.FEDORA_SERVER_NAME}/record", 2)
        self.delete_tombstones(self.api_url, settings.FEDORA_SERVER_NAME, settings.FEDORA_PATH)

    @staticmethod
    def clone_Database():
        logger.debug("core.tests.test_selenium.BaseSeleniumTestClass.clone_Database")
        prod_conn = None
        prod_cursor = None
        try:
            prod_conn = psycopg2.connect(
                host=get_secret("DB_HOST"),
                database=get_secret("DB_NAME"),
                user=get_secret("DB_USER"),
                password=get_secret("DB_PASS"),
                port=get_secret("DB_PORT"),
            )
            prod_conn.autocommit = True
            prod_cursor = prod_conn.cursor()
            prod_cursor.execute(
                f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{connection.settings_dict['NAME']}' AND pid <> pg_backend_pid();"
            )
            prod_cursor.execute(f"DROP DATABASE IF EXISTS {connection.settings_dict['NAME']};")
            prod_cursor.execute(
                f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{settings.TEST_DATABASE_NAME}' AND pid <> pg_backend_pid();"
            )
            prod_cursor.execute(
                f"CREATE DATABASE {connection.settings_dict['NAME']} WITH TEMPLATE {settings.TEST_DATABASE_NAME} strategy FILE_COPY;"
            )
            prod_conn.commit()
            invalidate_all()
        except Exception as err:
            logger.error(
                "core.tests.test_selenium.BaseSeleniumTestClass.clone_Database.general_exception", extra={"error": err}
            )
        finally:
            if prod_cursor is not None:
                prod_cursor.close()
            if prod_conn is not None:
                prod_conn.close()
        connection.connect()

    def assertIn2(self, member1, member2, container, msg=None):
        container_result = container.current_url
        repeat = 0
        while (member1 not in container_result and member2 not in container_result) and repeat < 10:
            time.sleep(self.wait_interval)
            repeat += 1
            container_result = container.current_url

        if member1 not in container_result and member2 not in container_result:
            standardMsg = "%s or %s not found in %s" % (
                safe_repr(member1),
                safe_repr(member2),
                safe_repr(container_result),
            )
            self.fail(self._formatMessage(msg, standardMsg))

    def tearDown(self):
        self.driver.save_screenshot(f"{settings.TEST_SCREENSHOT_PATH}{self._testMethodName}.png")
        self.driver.quit()
        if hasattr(self._outcome, "errors"):
            # Python 3.4 - 3.10  (These two methods have no side effects)
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
        else:
            # Python 3.11+
            result = self._outcome.result
        ok = all(test != self for test, text in result.errors + result.failures)

        if os.path.isfile(f"{settings.TEST_SCREENSHOT_PATH}results.xlsx"):
            data = pandas.read_excel(f"{settings.TEST_SCREENSHOT_PATH}results.xlsx")
            d = data.values.tolist()
        else:
            d = []
        index = int(self._testMethodName.split("_")[1])
        if len(d) < index:
            for i in range(len(d) + 1, index + 1):
                d.append([i, "", "", ""])
        d[index - 1][1] = datetime.now()
        d[index - 1][2] = self.id()
        if ok:
            d[index - 1][3] = "OK"
        else:
            if len(result.errors) > 0:
                d[index - 1][3] = "ERROR"
            elif len(result.failures) > 0:
                d[index - 1][3] = "FAIL"
        data = pandas.DataFrame(d)
        data.columns = ["index", "date", "test name", "result"]
        try:
            data.to_excel(f"{settings.TEST_SCREENSHOT_PATH}results.xlsx", index=False)
        except Exception:
            pass
        super().tearDown()

    def _fixture_teardown(self):
        pass

    def wait(self, interval):
        time.sleep(interval)

    def wait_for(self, condition_function, by, value):
        start_time = time.time()
        while time.time() < start_time + 12:
            if condition_function(by, value):
                return True
            else:
                time.sleep(0.5)
        return False

    def findElement(self, by, value):
        elements = self.driver.find_elements(by, value)
        if len(elements) > 0:
            return True
        return False

    def ElementIsClickable(self, by, value):
        element = self.driver.find_element(by, value)
        if element.is_displayed() and element.is_enabled():
            return True
        return False

    def ElementClick(self, by=By.ID, value: Optional[str] = None):
        res = self.wait_for(self.findElement, by, value)
        if res is False:
            logger.warning(
                "BaseSeleniumTestClass.ElementClick.elementNotFound",
                extra={
                    "filed": by,
                    "value": value,
                },
            )
            raise Exception("ElementClickError")
        res = self.wait_for(self.ElementIsClickable, by, value)
        if res is False:
            logger.warning(
                "BaseSeleniumTestClass.ElementClick.elementNotFound",
                extra={
                    "filed": by,
                    "value": value,
                },
            )
            raise Exception("ElementIsNotClickableError")
        attempts = 0
        while attempts < 10:
            try:
                self.driver.find_element(by, value).click()
                break
            except Exception:
                attempts += 1
                time.sleep(1)
        if attempts >= 10:
            logger.warning(
                "BaseSeleniumTestClass.ElementClick.elementNotFound",
                extra={
                    "filed": by,
                    "value": value,
                },
            )
            raise Exception("ElementClickError")

    def ElementSendKeys(self, by, value, keys):
        res = self.wait_for(self.findElement, by, value)
        if res is False:
            logger.warning(
                "BaseSeleniumTestClass.ElementClick.elementNotFound",
                extra={
                    "filed": by,
                    "value": value,
                },
            )
            raise Exception("ElementSendKeysError")
        attempts = 0
        while attempts < 10:
            try:
                self.driver.find_element(by, value).send_keys(keys)
                break
            except Exception:
                attempts += 1
                time.sleep(1)
        if attempts >= 10:
            logger.warning(
                "BaseSeleniumTestClass.ElementSendKeys.elementError",
                extra={
                    "filed": by,
                    "value": value,
                },
            )
            raise Exception("ElementSendKeysError")

    def clickAt(self, el, position_x, position_y):
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(el, position_x, position_y)
        action.click()
        action.perform()

    def clickAtMapCoord(self, lon, lat):

        self.driver.execute_script(
            f"""
 window.getToday = function() {{
return new Date('2025-06-28T12:00:00Z');}};
 const latlng = L.latLng({lat}, {lon});
 map.setView(latlng, 17);
 const containerPoint = map.latLngToContainerPoint(latlng);
 const layerPoint = map.latLngToLayerPoint(latlng);
 const syntheticEvent = new MouseEvent('click', {{
 bubbles: true,
 cancelable: true,
 clientX: 0,
 clientY: 0
}});
 map.fire('click', {{
 latlng: latlng,
 containerPoint: containerPoint,
 layerPoint: layerPoint,
 originalEvent: syntheticEvent
}});"""
        )

    def _username(self, type="archeolog"):
        return USERS[type]["USERNAME"]

    def _password(sel, type="archeolog"):
        return USERS[type]["PASSWORD"]

    def _select_value_select_picker(self, field_id, selected_value):
        dropdown = self.driver.find_element(By.ID, field_id)
        dropdown.find_element(By.XPATH, f"//option[. = '{selected_value}']").click()

    def _fill_text_field(self, field_id, field_value):
        self.driver.find_element(By.ID, field_id).click()
        self.driver.find_element(By.ID, field_id).send_keys(field_value)

    def _select_map_point(self, field_id, click_count):
        for _ in range(click_count):
            self.driver.find_element(By.ID, field_id).click()
            time.sleep(1)

    def _select_radion_group_item(self, item_order=1):
        self.driver.find_element(
            By.CSS_SELECTOR, f".custom-radio:nth-child({item_order}) > .custom-control-label"
        ).click()

    def _fill_form_fields(self, test_data):
        for item, value in test_data.items():
            field_type = value["field_type"]
            logger.info(
                "BaseSeleniumTestClass._fill_form_fields.start",
                extra={"filed": item, "value": value, "field_type": field_type},
            )
            if field_type == "text_field":
                self._fill_text_field(value.get("field_id"), value.get("value"))
            elif field_type == "select_picker":
                self._select_value_select_picker(value["field_id"], value["value"])
            elif field_type == "map":
                self._select_map_point(value["field_id"], value["click_count"])
            elif field_type == "radio_button":
                self._select_radion_group_item(value["item_order"])
            else:
                logger.error(
                    "BaseSeleniumTestClass._fill_form_fields.unknown_field_type",
                    extra={"field_type": field_type, "value": value},
                )

    def login(self, type="archeolog"):
        self.goToAddress()
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "czech")

        self.driver.find_element(By.ID, "id_username").send_keys(self._username(type))
        self.driver.find_element(By.ID, "id_password").send_keys(self._password(type))
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".btn")
        self.driver.set_window_rect(0, 0, 1360, 1020)

    def logout(self):
        self.ElementClick(By.ID, "buttonLogout")

    def goToAddress(self, rel_address="/"):
        port = self.server_thread.port
        self.driver.get(f"https://{settings.WEB_SERVER_ADDRESS}:{port}{rel_address}")

    def addFileToDropzone(self, css_selector, name, content):
        """
        Trigger a file add with `name` and `content` to Dropzone element at `css_selector`.
        """
        script = """
        const b64toBlob = (b64Data, contentType='', sliceSize=512) => {
        const byteCharacters = atob(b64Data);
        const byteArrays = [];

        for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
            const slice = byteCharacters.slice(offset, offset + sliceSize);
            const byteNumbers = new Array(slice.length);
            for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            byteArrays.push(byteArray);
        }
        const blob = new Blob(byteArrays, {type: contentType});
        return blob;
        }
        var blob = b64toBlob('%s', 'image/jpeg');
        var dropzone_instance = Dropzone.forElement('%s')
        var new_file = new File([blob], '%s', {type: 'image/jpeg'})
        dropzone_instance.addFile(new_file)
        """ % (
            content,
            css_selector,
            name,
        )
        self.driver.execute_script(script)

    def upload_file(self, file_path, file_name):
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        self.addFileToDropzone("#my-awesome-dropzone", file_name, encoded_string)
        self.driver.set_script_timeout(15)
        self.driver.execute_async_script(
            """
            var done = arguments[0];
            newDropzone.on("success", function(){ done('foo');});
            """
        )

    def createFedoraRecord(self, ident_cely, user_name="archeolog"):
        try:
            record = get_record_from_ident(ident_cely)
            self._username(user_name)
            user = User.objects.get(email=self._username(user_name))
        except Http404 as err:
            record = None
            logger.debug(
                "BaseSeleniumTestClass.createFedoraRecord.not_found",
                extra={"ident_cely": ident_cely, "error": err},
            )
        if record and isinstance(record, ModelWithMetadata) or isinstance(record, User):
            try:
                fedora_transaction = FedoraTransaction(transaction_user=user)
                record.save_metadata(fedora_transaction)
                fedora_transaction.mark_transaction_as_closed()
            except FedoraError as err:
                logger.debug(
                    "BaseSeleniumTestClass.fedora_error.not_found",
                    extra={"ident_cely": ident_cely, "error": err},
                )

    def odstran_elementy(self, root, ignorovane_tagy):
        """Rekurzivně odstraní ignorované tagy z XML stromu."""
        for elem in list(root):
            if elem.tag in ignorovane_tagy:
                elem.text = None
            else:
                self.odstran_elementy(elem, ignorovane_tagy)

    def odstran_uuid_z_xml(self, element):
        """
        Rekurzivně odstraní UUID z textů a atributů XML elementu.
        """
        # Nahraď v textu
        if element.text:
            element.text = self.UUID_REGEX.sub("UUID-REMOVED", element.text)
        if element.tail:
            element.tail = self.UUID_REGEX.sub("UUID-REMOVED", element.tail)

        # Nahraď v atributech
        for key, value in element.attrib.items():
            element.attrib[key] = self.UUID_REGEX.sub("UUID-REMOVED", value)

        # Rekurzivně pokračuj
        for child in element:
            self.odstran_uuid_z_xml(child)

    def serad_elementy_xml(self, element):
        """
        Rekurzivně seřadí podřízené XML elementy podle tagu, obsahu a atributů.
        """
        # Nejprve rekurzivně seřaď všechny děti
        for child in element:
            self.serad_elementy_xml(child)

        # Pokud má element více dětí stejného názvu, seřadíme je podle vnitřního obsahu
        if len(element) > 1:
            element[:] = sorted(element, key=lambda e: (e.tag, self._element_klic(e)))

    def _element_klic(self, elem):
        """
        Vytvoří porovnávací klíč pro element: spojení tagu, textu, vnořených textů a atributů.
        """
        hodnoty = [elem.tag]
        if elem.text:
            hodnoty.append(elem.text.strip())
        for pod in elem:
            if pod.text:
                hodnoty.append(pod.text.strip())
            for _, v in sorted(pod.attrib.items()):
                hodnoty.append(v.strip())
        return "|".join(hodnoty)

    def xml_to_string_bez_ignorovanych_z_textu(self, xml_text, ignorovane_tagy):
        """
        Načte XML z textového vstupu, odstraní ignorované tagy a vrátí serializovanou podobu.
        """
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(xml_text, parser)
        ignorovane_tagy_trans = []
        for item in ignorovane_tagy:
            ignorovane_tagy_trans.append(item.replace("amcr:", "{https://api.aiscr.cz/schema/amcr/2.2/}"))
        self.odstran_elementy(root, ignorovane_tagy_trans)
        self.odstran_uuid_z_xml(root)
        self.serad_elementy_xml(root)
        text = etree.tostring(root, pretty_print=True, encoding="utf-8")
        text = re.sub(rb">hist-\d+<", rb">hist-<", text)
        return text

    def porovnej_xml_bez_ignorovanych(self, vzorovy_soubor, vystupni_soubor, ignorovane_tagy):
        """Porovná dva XML soubory po odstranění ignorovaných tagů."""
        vzor = self.xml_to_string_bez_ignorovanych_z_textu(vzorovy_soubor, ignorovane_tagy)
        vystup = self.xml_to_string_bez_ignorovanych_z_textu(vystupni_soubor, ignorovane_tagy)
        res = vzor == vystup
        if res is False:
            logger.error(
                "BaseSeleniumTestClass.fedora_error.porovnej_xml_bez_ignorovanych",
                extra={"data": vystup},
            )
        return res

    def nahrad_base_uri_auto(self, graf, nova_base_uri="info:test-base/"):
        """
        Najde nejběžnější základní URI (hostname + prefix) v grafu a nahradí ho za `nova_base_uri`.
        """
        uri_counter = {}

        # Detekuj nejčastější base z URI
        for s, p, o in graf:
            for term in [s, o]:
                if isinstance(term, URIRef) and settings.FEDORA_SERVER_NAME in str(term):
                    parsed = urlparse(str(term))
                    if parsed.scheme and parsed.netloc:
                        base = f"{parsed.scheme}://{parsed.netloc}/"
                        uri_counter[base] = uri_counter.get(base, 0) + 1

        if not uri_counter:
            return  # žádné URI k nahrazení

        # Nejčastější base URI (např. http://192.168.1.27:8080/)
        puvodni_base = max(uri_counter, key=uri_counter.get)

        # Nahraď v grafech
        """nove_triples = []
        for s, p, o in list(graf):
            novy_s = URIRef(str(s).replace(puvodni_base, nova_base_uri)) if isinstance(s, URIRef) and str(s).startswith(puvodni_base) else s
            novy_o = URIRef(str(o).replace(puvodni_base, nova_base_uri)) if isinstance(o, URIRef) and str(o).startswith(puvodni_base) else o
            nove_triples.append((novy_s, p, novy_o))
            graf.remove((s, p, o))
        for t in nove_triples:
            graf.add(t)"""

        nove_triples = []
        for s, p, o in list(graf):
            novy_s = (
                URIRef(str(s).replace(puvodni_base, nova_base_uri))
                if isinstance(s, URIRef) and str(s).startswith(puvodni_base)
                else s
            )
            novy_o = o
            if isinstance(o, URIRef) and str(o).startswith(puvodni_base):
                novy_o = URIRef(str(o).replace(puvodni_base, nova_base_uri))
            elif isinstance(o, Literal) and str(o).startswith(puvodni_base):
                novy_o = Literal(str(o).replace(puvodni_base, nova_base_uri), datatype=o.datatype, lang=o.language)

            nove_triples.append((novy_s, p, novy_o))
            graf.remove((s, p, o))
        for t in nove_triples:
            graf.add(t)

    def rdf_graf_z_textu(self, data, format="turtle"):
        g = Graph()
        g.parse(data=data, format=format)
        return g

    def odstran_predikaty(self, graf, predikaty_k_ignoru):
        """Odstraní trojice podle predikátů (může být prefixed nebo plné URI)."""
        for pred in predikaty_k_ignoru:
            # Pokud je to string s dvojtečkou, pokusíme se ho expandovat jako CURIE (prefix:name)
            if ":" in pred and not pred.startswith("http"):
                try:
                    pred_uri = graf.namespace_manager.expand_curie(pred)
                except ValueError:
                    continue
            else:
                pred_uri = URIRef(pred)

            for s, p, o in list(graf.triples((None, pred_uri, None))):
                graf.remove((s, p, o))

    def odstran_uuid_z_rdf(self, graf):
        """
        Projde RDF graf a nahradí výskyty UUID v URIRef i Literal hodnotách.
        """
        nove_triples = []

        for s, p, o in list(graf):
            # Subjekt
            new_s = URIRef(self.UUID_REGEX.sub("UUID-REMOVED", str(s))) if isinstance(s, URIRef) else s
            # Objekt
            if isinstance(o, URIRef):
                new_o = URIRef(self.UUID_REGEX.sub("UUID-REMOVED", str(o)))
            elif isinstance(o, Literal) and isinstance(o.value, str):
                new_o = Literal(self.UUID_REGEX.sub("UUID-REMOVED", str(o)), datatype=o.datatype, lang=o.language)
            else:
                new_o = o

            # Zachováme predikát beze změny (většinou se UUID v predikátu nevyskytuje)
            nove_triples.append((new_s, p, new_o))
            graf.remove((s, p, o))

        for triple in nove_triples:
            graf.add(triple)

    def porovnej_rdf_obsah(self, aktualni_rdf, ocekavany_rdf, ignorovat_predikaty=None):
        g1 = Graph()
        g1.parse(data=aktualni_rdf, format="turtle")

        g2 = Graph()
        g2.parse(data=ocekavany_rdf, format="turtle")

        if ignorovat_predikaty:
            self.odstran_predikaty(g1, ignorovat_predikaty)
            self.odstran_predikaty(g2, ignorovat_predikaty)

        self.nahrad_base_uri_auto(g1)
        self.nahrad_base_uri_auto(g2)

        self.odstran_uuid_z_rdf(g1)
        self.odstran_uuid_z_rdf(g2)

        return g1.isomorphic(g2)

    def najdi_base_uri(self, vsechny_retezce):
        """
        Najde nejčastější base URI ve všech string hodnotách (např. http://.../rest/)
        """
        prefixy = []
        for s in vsechny_retezce:
            if s.startswith("http"):
                # vezmeme např. až po /rest/
                parts = s.split("/")
                if len(parts) >= 4:
                    prefix = "/".join(parts[:4]) + "/"  # např. http://192.168.1.27:8080/rest/
                    prefixy.append(prefix)
        if not prefixy:
            return None
        return Counter(prefixy).most_common(1)[0][0]

    def sesbiraj_retezce(self, data):
        """Rekurzivně sesbírá všechny stringy z JSON dat."""
        hodnoty = []
        if isinstance(data, dict):
            for v in data.values():
                hodnoty.extend(self.sesbiraj_retezce(v))
        elif isinstance(data, list):
            for item in data:
                hodnoty.extend(self.sesbiraj_retezce(item))
        elif isinstance(data, str) and settings.FEDORA_SERVER_NAME in data:
            hodnoty.append(data)
        return hodnoty

    def nahrad_base_uri_v_json(self, data, puvodni_base, nova_base):
        """Rekurzivně nahradí base URI ve všech stringových hodnotách JSON objektu."""
        if isinstance(data, dict):
            return {k: self.nahrad_base_uri_v_json(v, puvodni_base, nova_base) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.nahrad_base_uri_v_json(item, puvodni_base, nova_base) for item in data]
        elif isinstance(data, str):
            return data.replace(puvodni_base, nova_base)
        else:
            return data

    def nahrad_base_uri_auto_json(self, data, nova_base="info:test-base/"):
        """
        Najde a nahradí nejčastější base URI v JSON string hodnotách.
        """
        vsechny_str = self.sesbiraj_retezce(data)
        puvodni_base = self.najdi_base_uri(vsechny_str)
        if puvodni_base:
            return self.nahrad_base_uri_v_json(data, puvodni_base, nova_base)
        return data  # žádná změna

    def odstran_klice(self, data, klice_k_ignoraci):
        """
        Rekurzivně odstraní z JSON objektu všechny klíče uvedené v seznamu.
        """
        if isinstance(data, dict):
            return {k: self.odstran_klice(v, klice_k_ignoraci) for k, v in data.items() if k not in klice_k_ignoraci}
        elif isinstance(data, list):
            return [self.odstran_klice(item, klice_k_ignoraci) for item in data]
        else:
            return data

    def normalizuj_json(self, data):
        """
        Rekurzivně seřadí seznamy (pokud to jde) a klíče ve slovnících.
        """
        if isinstance(data, dict):
            return {k: self.normalizuj_json(v) for k, v in sorted(data.items())}
        elif isinstance(data, list):
            normalizovane = [self.normalizuj_json(i) for i in data]
            try:
                return sorted(normalizovane, key=lambda x: json.dumps(x, sort_keys=True))
            except TypeError:
                # nelze seřadit (např. kombinace typů), ponecháme původní pořadí
                return normalizovane
        else:
            return data

    UUID_REGEX = re.compile(r"[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}", re.IGNORECASE)

    def odstran_uuid(self, data):
        """
        Rekurzivně nahradí UUID ve stringových hodnotách JSON objektu za placeholder.
        """
        if isinstance(data, dict):
            return {k: self.odstran_uuid(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.odstran_uuid(item) for item in data]
        elif isinstance(data, str):
            return self.UUID_REGEX.sub("UUID-REMOVED", data)
        else:
            return data

    def porovnej_json_rovnost(self, vzor_json_text, vystup_json_text, klice_k_ignoraci=None):
        json_vzor = json.loads(vzor_json_text)
        json_vystup = json.loads(vystup_json_text)

        if klice_k_ignoraci:
            json_vzor = self.odstran_klice(json_vzor, klice_k_ignoraci)
            json_vystup = self.odstran_klice(json_vystup, klice_k_ignoraci)

        json_vzor = self.nahrad_base_uri_auto_json(json_vzor)
        json_vystup = self.nahrad_base_uri_auto_json(json_vystup)

        json_vzor = self.odstran_uuid(json_vzor)
        json_vystup = self.odstran_uuid(json_vystup)

        json_vzor = self.normalizuj_json(json_vzor)
        json_vystup = self.normalizuj_json(json_vystup)
        res = json_vzor == json_vystup
        if res is False:
            logger.error(
                "BaseSeleniumTestClass.fedora_error.porovnej_json_rovnost",
                extra={"data": vystup_json_text},
            )
        return res

    def getTime(self):
        if os.name == "nt":
            self.wait(1.5)
        t = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if os.name == "nt":
            self.wait(1.5)
        return t

    def wait_for_select2_results(self):
        self.driver.set_script_timeout(6)
        try:
            self.driver.find_element(By.CSS_SELECTOR, ".loading-results")
            self.driver.execute_async_script(
                """
var done = arguments[0];
var $ = window.jQuery || (typeof django !== 'undefined' && django.jQuery);
if (!$) {
    done("no jQuery");
    return;
}
$(document).one('ajaxSuccess', function(event, xhr, settings) {
done("ok");
});
"""
            )
        except Exception:
            pass


class CoreSeleniumTest(BaseSeleniumTestClass):
    def test_001_core_001(self):
        # Scenar_1 Přihlášení do AMČR (pozitivní scénář 1)
        logger.info("CoreSeleniumTest.test_core_001.start")
        self.login()
        self.assertEqual(self.driver.title, "AMČR Homepage")
        logger.info("CoreSeleniumTest.test_core_001.end")
