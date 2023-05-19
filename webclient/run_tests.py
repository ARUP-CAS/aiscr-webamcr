import logging
import os
import subprocess

import logstash

SETTINGS = "webclient.settings.dev_test"

test_preparation_path = os.path.join("scripts", "test_preparation.sh")
if os.path.exists(test_preparation_path):
    subprocess.run(f"./{test_preparation_path}")

logger = logging.getLogger('python-logstash-logger')
logger.setLevel(logging.INFO)
logger.addHandler(logstash.TCPLogstashHandler(host='logstash', version=1, tags="dev_test"))
logger.info('amcr_test_runner.start')

test_list = {
    "core.tests.test_selenium": {
        "CoreSeleniumTest": ["test_core_001"]
    },
    "projekt.tests.test_selenium": {
        "ProjektSeleniumTest":
            [
                "test_projekt_001",
            ],
        "ProjektZapsatSeleniumTest":
            [
                "test_projekt_zapsat_p_001", "test_projekt_zapsat_n_001", "test_projekt_zapsat_n_002",
                "test_projekt_zapsat_n_003"
            ],
        "ProjektZahajitVyzkumSeleniumTest":
            [
                "test_projekt_zahajit_vyzkum_p_001"
            ],
        "ProjektUkoncitVyzkumSeleniumTest":
            [
                "test_projekt_ukoncit_vyzkum_p_001", "test_projekt_ukoncit_vyzkum_n_001"
            ],
        "ProjektUzavritSeleniumTest":
            [
                "test_projekt_uzavrit_p_001", "test_projekt_uzavrit_n_001"
            ],
        "ProjektArchivovatSeleniumTest":
            [
                "test_projekt_archivovat_p_001", "test_projekt_uzavrit_n_001"
            ],
        "ProjektVratitArchivovanySeleniumTest":
            [
                "test_projekt_vratit_p_001"
            ],
        "ProjektVratitUzavrenySeleniumTest":
            [
                "test_projekt_vratit_p_001"
            ],
        "ProjektVratitUkoncenySeleniumTest":
            [
                "test_projekt_vratit_p_001"
            ],
        "ProjektVratitZahajenySeleniumTest":
            [
                "test_projekt_vratit_p_001"
            ],
        "ProjektVratitPrihlasenySeleniumTest":
            [
                "test_projekt_vratit_p_001"
            ],
        "ProjektNavrhnoutZrusitSeleniumTest":
            [
                "test_projekt_zrusit_p_001", "test_projekt_zrusit_p_002", "test_projekt_zrusit_n_001"
            ],
        "ProjektZrusitSeleniumTest":
            [
                "test_projekt_zrusit_p_001"
            ]
    }
}

test_count = 0
for test_file, test_list in test_list.items():
    for test_class, test_method_list in test_list.items():
        for test_method in test_method_list:
            logger.info("amcr_test_runner.start_test", extra={"test": f"{test_file}.{test_class}.{test_method}"})
            subprocess.run(f"python3 manage.py test {test_file}.{test_class}.{test_method} --settings={SETTINGS}",
                           shell=True, capture_output=True)
            logger.info("amcr_test_runner.end_test", extra={"test_file": test_file, "test_class": test_class,
                                                            "test_method": test_method})
            test_count += 1
logger.info("amcr_test_runner.end", extra={"test_count": test_count})
