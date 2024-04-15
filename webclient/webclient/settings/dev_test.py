from .dev import *

LOGGING["handlers"]["logstash"]["tags"] = "dev_test"
SELENIMUM_ADDRESS = 'selenium'
SELENIUM_PORT='4444'
WEB_SERVER_ADDRESS='web' #adresa na které běží test a kterou použije selenium
TEST_DATABASE_NAME="test_vzor" #jmeno vzorové databáze, která se klonuje
USE_REMOTE_WEB_BROWSER=True

FEDORA_SERVER_NAME = "AMCR-selenium-test"
TEST_SCREENSHOT_PATH = "/vol/web/selenium_test"
