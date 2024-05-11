import unittest
import time
import socket
import requests
import json
import psycopg2
import pandas
import os.path
from datetime import datetime
from webclient.settings.base import get_secret
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.common.exceptions import *
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings, tag
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from django.test import LiveServerTestCase
from core.tests.runner import USERS
import logging
import logstash
from django.db import connection

from unittest.util import safe_repr 

logger = logging.getLogger(__name__)


class Wait_for_page_load(object):

    def __init__(self, browser):
        self.browser = browser
        

    def __enter__(self):
        self.old_page = self.browser.find_element(By.TAG_NAME,'html')
        

    def page_has_loaded(self):
        new_page = self.browser.find_element(By.TAG_NAME,'html')
        return new_page.id != self.old_page.id
    
    def page_is_ready(self):
        page_state = self.browser.execute_script('return document.readyState;')
        return page_state == 'complete'
    

    def __exit__(self, *_):
        self.wait_for(self.page_has_loaded)
        self.wait_for(self.page_is_ready)
        
    
    def wait_for(self,condition_function):
        start_time = time.time()
        while time.time() < start_time + 12:
            if condition_function():
                return True
            else:
                time.sleep(0.5)


#@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class BaseSeleniumTestClass(StaticLiveServerTestCase):   
    #port = 5678   
    host = '0.0.0.0'
    test_number = 1


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
        #options = webdriver.ChromeOptions()
        if settings.USE_REMOTE_WEB_BROWSER:
            self.driver = webdriver.Remote(command_executor=f'http://{settings.SELENIMUM_ADDRESS}:{settings.SELENIUM_PORT}/wd/hub', options=options)
        else:
            self.driver = webdriver.Firefox()

        #self.driver=webdriver.Chrome()
        self.driver.implicitly_wait(2) 
        self.wait_interval  = 2
        logger.debug("core.tests.test_selenium.BaseSeleniumTestClass.setup.end") 
        
        
    def get_container_content(self,container_path):
        headers =  {"Accept": "application/ld+json"}
        response = requests.get(container_path,auth=self.auth,headers=headers) 
        members=[]
        if(response.status_code==200):
            res = json.loads(response.text)
            if 'http://www.w3.org/ns/ldp#contains' in res[0]:
                for n in res[0]['http://www.w3.org/ns/ldp#contains']:
                    members.append(n['@id'])
        return members   
    
        
    api_url = f"{settings.FEDORA_PROTOCOL}://{settings.FEDORA_SERVER_HOSTNAME}:{settings.FEDORA_PORT_NUMBER}/rest/"
    auth = requests.auth.HTTPBasicAuth(settings.FEDORA_ADMIN_USER, settings.FEDORA_ADMIN_USER_PASSWORD)
    
    
    def purge_container(self,container_path):
        response = requests.delete(container_path+"/fcr:tombstone",auth=self.auth) 
        

    def delete_container(self,container_path):
        response = requests.delete(container_path,auth=self.auth) 
        
    
    def wipe_Fedora(self):
        mem=self.get_container_content(f'{self.api_url}{settings.FEDORA_SERVER_NAME}/model')
        for item in mem:
            items=self.get_container_content(item+'/member')
            for i in items:
                self.delete_container(i)
                self.purge_container(i)
        
        mem=self.get_container_content(f'{self.api_url}{settings.FEDORA_SERVER_NAME}/record')
        for item in mem:
            self.delete_container(item) 
            self.purge_container(item)   
            

    @staticmethod
    def clone_Database():
        logger.debug("core.tests.test_selenium.BaseSeleniumTestClass.clone_Database")
        prod_conn = None
        prod_cursor = None
        try:                       
            prod_conn = psycopg2.connect(
                host=get_secret("DB_HOST"),
                database=get_secret("DB_NAME"),
                user=get_secret('DB_USER'),
                password=get_secret('DB_PASS'),
                port=get_secret('DB_PORT'),           
            )                  
            prod_conn.autocommit = True     
            prod_cursor = prod_conn.cursor()
            prod_cursor.execute(f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{connection.settings_dict['NAME']}' AND pid <> pg_backend_pid();")
            prod_cursor.execute(f"DROP DATABASE IF EXISTS {connection.settings_dict['NAME']};")
            prod_cursor.execute(f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{settings.TEST_DATABASE_NAME}' AND pid <> pg_backend_pid();")
            prod_cursor.execute(f"CREATE DATABASE {connection.settings_dict['NAME']} WITH TEMPLATE {settings.TEST_DATABASE_NAME};")
            prod_conn.commit()
            
        except Exception as err:
            logger.error("core.tests.test_selenium.BaseSeleniumTestClass.clone_Database.general_exception",
                           extra={"err": err})
        finally:
            if prod_cursor is not None:
                prod_cursor.close()
            if prod_conn is not None:
                prod_conn.close()            
        connection.connect()
            
    
    def assertIn2(self, member1 ,member2, container, msg=None):
        container_result=container.current_url
        repeat=0
        while (member1 not in container_result and member2 not in container_result) and repeat< 10:
            time.sleep(self.wait_interval)
            repeat+=1
            container_result=container.current_url
        
        if member1 not in container_result and member2 not in container_result:
            standardMsg = '%s or %s not found in %s' % (safe_repr(member1),safe_repr(member2),
                                                  safe_repr(container_result))
            self.fail(self._formatMessage(msg, standardMsg))
  
        
    def tearDown(self):
        self.driver.save_screenshot(f'{settings.TEST_SCREENSHOT_PATH}{self._testMethodName}.png')
        self.driver.quit()
        if hasattr(self._outcome, 'errors'):
            # Python 3.4 - 3.10  (These two methods have no side effects)
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
        else:
            # Python 3.11+
            result = self._outcome.result
        ok = all(test != self for test, text in result.errors + result.failures)

        if os.path.isfile(f'{settings.TEST_SCREENSHOT_PATH}results.xlsx'):
            data= pandas.read_excel(f'{settings.TEST_SCREENSHOT_PATH}results.xlsx')
            d= data.values.tolist()
        else:
            d=[]

        index=self.test_number
        if len(d)<index:
            for i in range(len(d)+1, index+1):
                d.append([i,"","",""])
        d[index-1][1] = datetime.now()
        d[index-1][2]= self.id()
        if ok:
            d[index-1][3]= "OK"
        else:
            if len(result.errors)>0:
                d[index-1][3]= "ERROR" 
            elif len(result.failures)>0:
                d[index-1][3]= "FAIL" 

        data = pandas.DataFrame(d)
        data.columns =['index','date', 'test name', 'result']

        try:
            data.to_excel(f'{settings.TEST_SCREENSHOT_PATH}results.xlsx',index=False) 
        except Exception as e:
            pass
        super().tearDown()
        
    
    def _fixture_teardown(self):
        pass
    
    
    def wait(self,interval):
        time.sleep(interval) 
        
    
    def wait_for(self,condition_function,by,value):
        start_time = time.time()
        while time.time() < start_time + 12:
            if condition_function(by,value):
                return True
            else:
                time.sleep(0.5)
        return False
    
    
    def findElement(self,by,value):
        elements=self.driver.find_elements(by,value)
        if  len(elements)>0: return True
        return False
    
    
    def ElementIsClickable(self,by,value):
        element=self.driver.find_element(by,value)
        if  element.is_displayed() and element.is_enabled()  : return True
        return False
    
    
    def ElementClick(self,by=By.ID, value: Optional[str] = None):       
        res=self.wait_for(self.findElement,by,value)
        if res==False:
            logger.error("BaseSeleniumTestClass.ElementClick.elementNotFound", extra={"filed": by, "content": value,})
            raise Exception("ElementClickError")  
        res=self.wait_for(self.ElementIsClickable,by,value) 
        if res==False:
            logger.error("BaseSeleniumTestClass.ElementClick.elementNotFound", extra={"filed": by, "content": value,})
            raise Exception("ElementIsNotClickableError")  
        attempts = 0
        while attempts < 10:
            try:
                self.driver.find_element(by,value).click()
                break
            except Exception as e:
                attempts += 1
                time.sleep(1)
        if attempts >= 10:
            logger.error("BaseSeleniumTestClass.ElementClick.elementNotFound", extra={"filed": by, "content": value,})
            raise Exception("ElementClickError")                    
             
        
    def clickAt(self,el,position_x,position_y):
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(el, position_x,position_y)
        action.click()
        action.perform()
    
    
    def _username(self,type="archeolog"):
        return  USERS[type]["USERNAME"] 
    

    def _password(sel,type="archeolog"):
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
        self.driver.find_element(By.CSS_SELECTOR, f".custom-radio:nth-child({item_order}) > .custom-control-label").click()
        

    def _fill_form_fields(self, test_data):
        for item, value in test_data.items():
            field_type = value["field_type"]
            logger.info("BaseSeleniumTestClass._fill_form_fields.start", extra={"filed": item, "content": value,
                                                                                 "field_type": field_type})
            if field_type == "text_field":
                self._fill_text_field(value.get("field_id"), value.get("value"))
            elif field_type == "select_picker":
                self._select_value_select_picker(value["field_id"], value["value"])
            elif field_type == "map":
                self._select_map_point(value["field_id"], value["click_count"])
            elif field_type == "radio_button":
                self._select_radion_group_item(value["item_order"])
            else:
                logger.error("BaseSeleniumTestClass._fill_form_fields.unknown_field_type",
                             extra={"field_type": field_type, "value": value})


    def login(self,type="archeolog"):
        port = self.server_thread.port
        self.driver.get(f"http://{settings.WEB_SERVER_ADDRESS}:{port}/")
        #if len(self.driver.find_elements(By.CSS_SELECTOR, ".cm__btn-group:nth-child(1) > .cm__btn:nth-child(1)"))>0:        
        #self.ElementClick(By.CSS_SELECTOR, ".cm__btn-group:nth-child(1) > .cm__btn:nth-child(1)")
         
        with Wait_for_page_load(self.driver): 
            self.ElementClick(By.ID, "czech")
    
        self.driver.find_element(By.ID, "id_username").send_keys(self._username(type))
        self.driver.find_element(By.ID, "id_password").send_keys(self._password(type))
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.CSS_SELECTOR, ".btn")

        self.driver.set_window_rect(0,0,1360, 1020)   


class CoreSeleniumTest(BaseSeleniumTestClass):
    def test_core_001(self):
        #Scenar_1 Přihlášení do AMČR (pozitivní scénář 1)
        logger.info("CoreSeleniumTest.test_core_001.start")
        self.test_number=1
        self.login()
        self.assertEqual(self.driver.title, "AMČR Homepage")
        logger.info("CoreSeleniumTest.test_core_001.end")
        
        
