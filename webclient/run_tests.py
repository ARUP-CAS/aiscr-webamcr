import logging
import os
import subprocess

import logstash

SETTINGS = "webclient.settings.dev_test"

test_preparation_path = os.path.join("scripts", "test_preparation.sh")
if os.path.exists(test_preparation_path):
    subprocess.run(f"./{test_preparation_path}")

logger = logging.getLogger('webamcr.test_runner')
logger.setLevel(logging.INFO)
logger.addHandler(logstash.TCPLogstashHandler(host='logstash', version=1, tags="dev_test"))
logger.info('amcr_test_runner.start')

test_list = [
    "core.tests.test_selenium",
    "projekt.tests.test_selenium",
    "dokument.tests.test_selenium",
    "lokalita.tests.test_selenium",  
    "arch_z.tests.test_selenium",  
    "pas.tests.test_selenium",      
]

test_count = 0
for test_file  in test_list:
    
    logger.info("amcr_test_runner.start_test", extra={"test": f"{test_file}"})
    process = subprocess.Popen(f"python3 manage.py test {test_file} --settings={SETTINGS} --noinput", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in process.stdout:
        print(line, end="")
    for line in process.stderr:
        print(line, end="")
    process.wait()    
    logger.info("amcr_test_runner.end_test", extra={"test_file": test_file} )
    test_count += 1
logger.info("amcr_test_runner.end", extra={"test_count": test_count})
