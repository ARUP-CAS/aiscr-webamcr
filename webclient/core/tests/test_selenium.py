import socket

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings, tag
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys

from webclient.settings.base import TEST_USER_EMAIL, TEST_USER_PASSWORD


class CoreSeleniumTest(StaticLiveServerTestCase):
    # fixtures = ['selenium_data.json']
    host = '0.0.0.0'

    def __init__(self):
        super().__init__()
        self.driver = self.selenium

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set host to externally accessible web server address
        cls.host = socket.gethostbyname(socket.gethostname())

        # Instantiate the remote WebDriver
        cls.selenium = webdriver.Remote(
            #  Set to: htttp://{selenium-container-name}:port/wd/hub
            #  In our example, the container is named `selenium`
            #  and runs on port 4444
            command_executor='http://selenium:4444/wd/hub',
            # Set to CHROME since we are using the Chrome container
            desired_capabilities=DesiredCapabilities.CHROME,

        )
        cls.selenium.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_login(self):
        self.driver.get("web:8000")
        self.driver.find_element(By.ID, "id_username").click()
        self.driver.find_element(By.ID, "id_username").send_keys(TEST_USER_EMAIL)
        self.driver.find_element(By.ID, "id_password").send_keys(TEST_USER_PASSWORD)
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        assert self.driver.title == "AMČR Homepage"

    def test_tableSorting(self):
        self.driver.get("http://localhost:8000/accounts/login/?next=/")
        self.driver.find_element(By.ID, "id_username").send_keys(TEST_USER_EMAIL)
        self.driver.find_element(By.ID, "id_password").send_keys(TEST_USER_PASSWORD)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.driver.find_element(By.CSS_SELECTOR, ".card:nth-child(1) .btn").click()
        self.driver.find_element(By.LINK_TEXT, "Vybrat projekty").click()
        assert "sort=ident_cely" in self.driver.current_url
        self.driver.find_element(By.LINK_TEXT, "Identifikátor").click()
        assert "sort=stav" in self.driver.current_url
