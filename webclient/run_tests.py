import logging
import os
import subprocess
from threading import Thread
import logstash
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-f','--fail', help='provede neúspěšné testy', action='store_true')
parser.add_argument('-a','--all', help='provede všechny testy', action='store_true')

args = parser.parse_args()

SETTINGS = "webclient.settings.dev_test"

test_preparation_path = os.path.join("scripts", "test_preparation.sh")
if os.path.exists(test_preparation_path):
    subprocess.run(f"./{test_preparation_path}")

logger = logging.getLogger('webamcr.test_runner')
#logger.setLevel(logging.INFO)
logger.addHandler(logstash.TCPLogstashHandler(host='logstash', version=1, tags="dev_test"))
logger.info('amcr_test_runner.start')

if args.fail==True:
    from webclient.settings.dev_test import TEST_SCREENSHOT_PATH
    import pandas
    if os.path.isfile(f'{TEST_SCREENSHOT_PATH}results.xlsx'):
            data= pandas.read_excel(f'{TEST_SCREENSHOT_PATH}results.xlsx')
            d= data.values.tolist()
            test_list = []
            for line in d:
                if(line[3]!="OK" and isinstance(line[3], float)!=True ):
                    test_list.append(line[2])
            if len(test_list)==0:
                print("Všechny testy OK")
                exit()
                
    else:
        print("Nenalezn soubor s výsledky")
        exit()
    
else:    
    test_list = [
    "core.tests.test_selenium",
    "projekt.tests.test_selenium",
    "dokument.tests.test_selenium",
    "lokalita.tests.test_selenium",  
    "arch_z.tests.test_selenium",  
    "pas.tests.test_selenium",       
    ]


def reader(pipe):
    while True:
        line = pipe.read(1)
        print(line,end="")
        if not line:
            break
    
logger.info("amcr_test_runner.start_test", extra={"test": f"{' '.join(test_list)}"})
subprocess.run(f"python3 manage.py migrate --database test_db --settings={SETTINGS}", text=True, shell=True )

process = subprocess.Popen(f"python3 manage.py test {' '.join(test_list)} --settings={SETTINGS} --noinput --verbosity=2", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True )

t1=Thread(target=reader, args=[process.stdout]).start()
t2=Thread(target=reader, args=[process.stderr]).start()
process.wait()

logger.info("amcr_test_runner.end")
