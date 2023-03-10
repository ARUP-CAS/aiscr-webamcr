import unittest

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

from core.tests.runner import TEST_USER_USERNAME, TEST_USER_PASSWORD

logger_s = structlog.get_logger(__name__)


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class BaseSeleniumTestClass(StaticLiveServerTestCase):
    # fixtures = ['selenium_data.json']
    host = '0.0.0.0'

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

    def tearDown(self):
        # self.driver.quit()
        super().tearDown()

    def _username(self):
        return TEST_USER_USERNAME

    def _password(self):
        return TEST_USER_PASSWORD

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
