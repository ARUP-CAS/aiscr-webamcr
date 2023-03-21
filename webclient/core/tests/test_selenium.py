import unittest

import time

import structlog
import socket

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings, tag
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from django.test import LiveServerTestCase

from core.tests.runner import TEST_USER_USERNAME, TEST_USER_PASSWORD, AMCRSeleniumTestRunner

logger_s = structlog.get_logger(__name__)


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class BaseSeleniumTestClass(StaticLiveServerTestCase):
    # fixtures = ['selenium_data.json']
    host = '0.0.0.0'

    @classmethod
    def get_base_test_data(cls):
        pass

    def go_to_form(self):
        pass

    def setUp(self):
        # Set host to externally accessible web server address
        self.host = socket.gethostbyname(socket.gethostname())

        # Instantiate the remote WebDriver
        self.driver = webdriver.Remote(
            #  Set to: htttp://{selenium-container-name}:port/wd/hub
            #  In our example, the container is named `selenium`
            #  and runs on port 4444
            command_executor='http://selenium:4444/wd/hub',
            # Set to CHROME since we are using the Chrome container
            desired_capabilities=DesiredCapabilities.CHROME,

        )
        self.driver.implicitly_wait(5)
        AMCRSeleniumTestRunner.save_geographical_data()
        AMCRSeleniumTestRunner.create_common_test_records()


    def tearDown(self):
        # self.driver.quit()
        super().tearDown()

    def _username(self):
        return TEST_USER_USERNAME

    def _password(self):
        return TEST_USER_PASSWORD

    def _select_value_select_picker(self, field_id, selected_value):
        dropdown = self.driver.find_element(By.ID, field_id)
        dropdown.find_element(By.XPATH, f"//option[. = '{selected_value}']").click()

    def _fill_text_field(self, field_id, field_value):
        self.driver.find_element(By.ID, field_id).click()
        self.driver.find_element(By.ID, field_id).send_keys(field_value)

    def _select_map_point(self, field_id, click_count):
        for _ in range(click_count):
            self.driver.find_element(By.ID, field_id).click()
            time.sleep(5)

    def _fill_form_fields(self, test_data):
        for item, value in test_data.items():
            field_type = value["field_type"]
            logger_s.debug("BaseSeleniumTestClass._fill_form_fields.start", filed=item, content=value,
                           field_type=field_type)
            if field_type == "text_field":
                self._fill_text_field(value.get("field_id"), value.get("value"))
            elif field_type == "select_picker":
                self._select_value_select_picker(value["field_id"], value["value"])
            elif field_type == "map":
                self._select_map_point(value["field_id"], value["click_count"])
            else:
                logger_s.error("BaseSeleniumTestClass._fill_form_fields.unknown_field_type",
                               field_type=field_type, value=value)

    def login(self):
        port = self.server_thread.port
        self.driver.get(f"http://web:{port}/")
        self.driver.find_element(By.ID, "id_username").send_keys(self._username())
        self.driver.find_element(By.ID, "id_password").send_keys(self._password())
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        self.driver.set_window_size(1936, 1056)


class CoreSeleniumTest(BaseSeleniumTestClass):
    def test_core_001(self):
        self.login()
        self.assertEqual(self.driver.title, "AMČR Homepage")
