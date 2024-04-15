import time
import datetime
import logging
import unittest

import base64

from django.conf import settings
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.constants import SN_ZAPSANY,SN_ODESLANY,SN_POTVRZENY,SN_ARCHIVOVANY
#from core.tests.runner import EXISTING_PROJECT_IDENT_ZACHRANNY, EXISTING_PROJECT_IDENT_STATUS
from core.tests.test_selenium import BaseSeleniumTestClass, Wait_for_page_load

from pas.models import SamostatnyNalez
from django.utils.translation import gettext as _
from selenium.common.exceptions import *
logger = logging.getLogger("tests")


def addFileToDropzone(driver, css_selector, name, content):
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
"""% (content,css_selector,name)
  driver.execute_script(script)
  

@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceSamostatneNalezy(BaseSeleniumTestClass):   
    def go_to_form(self):
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-samostatny_nalez > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneNalezy.zapsat")).click()


    def test_zapsani_samostatneho_nalezu_p_001(self):
        #Scenar_25 Zapsání samostatného nálezu (pozitivní scénář 1)
        logger.info("AkceSamostatneNalezy.test_zapsani_samostatneho_nalezu_p_001.start")

        self.login("badatel1")
        self.go_to_form()
        SN_count_old = SamostatnyNalez.objects.count()

        self.driver.find_element(By.CSS_SELECTOR, "#div_id_projekt .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("M-202105907")
        self.wait(self.wait_interval)

        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.driver.find_element(By.ID, "select2-id_nalezce-container").click()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Omelka, Zdeněk")
        self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_datum_nalezu").send_keys("18.10.2023")

        self.driver.find_element(By.ID, "id_hloubka").send_keys("20")
        self.driver.find_element(By.ID, "visible_ss_combo").click()
        self.driver.find_element(By.CSS_SELECTOR, "#visible_ss_combo > option:nth-child(2)").click()
        self.driver.find_element(By.ID, "projectMap").click()
        self.driver.find_element(By.ID, "projectMap").click()
        self.driver.find_element(By.CSS_SELECTOR, ".leaflet-control-measure > img").click()
        self.driver.find_element(By.ID, "visible_x1").click()
        self.driver.find_element(By.ID, "visible_x1").send_keys("16,7494989")
        self.driver.find_element(By.ID, "visible_x2").click()
        self.driver.find_element(By.ID, "visible_x2").send_keys("49,2941092")
        self.driver.find_element(By.ID, "div_id_lokalizace").click()
        self.driver.find_element(By.ID, "id_lokalizace").click()
        self.driver.find_element(By.ID, "id_lokalizace").send_keys("test")
        self.driver.find_element(By.ID, "id_obdobi").send_keys("kultura púchovská")
        self.driver.find_element(By.ID, "id_obdobi").send_keys(Keys.ENTER)

        self.driver.find_element(By.ID, "id_druh_nalezu").send_keys('lahev')
        self.driver.find_element(By.ID, "id_druh_nalezu").send_keys(Keys.ENTER)

        self.driver.find_element(By.CSS_SELECTOR, "#div_id_specifikace .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("jantar")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "newEntitySubmitBtn").click()
        SN_count_new = SamostatnyNalez.objects.count()
        self.assertEqual(SN_count_old + 1, SN_count_new) 
        logger.info("AkceSamostatneNalezy.test_zapsani_samostatneho_nalezu_p_001.end")
        
        
    def test_zapsani_samostatneho_nalezu_n_001(self):
        #Scenar_26 Zapsání samostatného nálezu (negativní scénář 1)
        logger.info("AkceSamostatneNalezy.test_zapsani_samostatneho_nalezu_n_001.start")

        self.login("badatel1")
        self.go_to_form()
        SN_count_old = SamostatnyNalez.objects.count()
               
        #self.driver.find_element(By.CSS_SELECTOR, "#div_id_projekt .filter-option-inner-inner").click()
        #self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("M-202004181")
        #self.wait(self.wait_interval)

        #self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.driver.find_element(By.ID, "select2-id_nalezce-container").click()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Omelka, Zdeněk")
        self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_datum_nalezu").send_keys("18.10.2023")

        self.driver.find_element(By.ID, "id_hloubka").send_keys("20")
        self.driver.find_element(By.ID, "visible_ss_combo").click()
        self.driver.find_element(By.CSS_SELECTOR, "#visible_ss_combo > option:nth-child(2)").click()
        self.driver.find_element(By.ID, "projectMap").click()
        self.driver.find_element(By.ID, "projectMap").click()
        self.driver.find_element(By.CSS_SELECTOR, ".leaflet-control-measure > img").click()
        self.driver.find_element(By.ID, "visible_x1").click()
        self.driver.find_element(By.ID, "visible_x1").send_keys("16,7494989")
        self.driver.find_element(By.ID, "visible_x2").click()
        self.driver.find_element(By.ID, "visible_x2").send_keys("49,2941092")
        self.driver.find_element(By.ID, "div_id_lokalizace").click()
        self.driver.find_element(By.ID, "id_lokalizace").click()
        self.driver.find_element(By.ID, "id_lokalizace").send_keys("test")

        self.driver.find_element(By.ID, "id_obdobi").send_keys("kultura púchovská")
        self.driver.find_element(By.ID, "id_obdobi").send_keys(Keys.ENTER)

        self.driver.find_element(By.ID, "id_druh_nalezu").send_keys('lahev')
        self.driver.find_element(By.ID, "id_druh_nalezu").send_keys(Keys.ENTER)

        self.driver.find_element(By.CSS_SELECTOR, "#div_id_specifikace .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("jantar")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "newEntitySubmitBtn").click()
        SN_count_new = SamostatnyNalez.objects.count()
        self.assertEqual(SN_count_old , SN_count_new)   
        logger.info("AkceSamostatneNalezy.test_zapsani_samostatneho_nalezu_n_001.end")
        
        
    def test_odeslani_samostatneho_nalezu_p_001(self):
        #Scenar_28 Odeslání samostatného nálezu (pozitivní scénář 1)        
        logger.info("AkceSamostatneNalezy.test_odeslani_samostatneho_nalezu_p_001.start")

        self.login("badatel1")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='M-202105907-N00091').first().stav , SN_ZAPSANY)         
        
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-samostatny_nalez > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneNalezy.mojeNalezy")).click()
        self.driver.find_element(By.LINK_TEXT, "M-202105907-N00091").click()
        
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-dokument > .material-icons").click()    

        with open("pas/tests/resources/test_foto_1.jpg", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        addFileToDropzone(self.driver,"#my-awesome-dropzone",'test_foto_1.jpg',encoded_string)
        wait = WebDriverWait(self.driver, 10, poll_frequency=1, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
        element = wait.until(EC.element_to_be_clickable((By.LINK_TEXT,  _("core.templates.core.upload_file.dz.removeFile"))))

        self.driver.find_element(By.LINK_TEXT, _("core.templates.upload_file.submitButton.text")).click()

        self.driver.find_element(By.CSS_SELECTOR, "#pas-odeslat > .app-controls-button-text").click()
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "submit-btn").click()

        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='M-202105907-N00091').first().stav , SN_ODESLANY)        
        logger.info("AkceSamostatneNalezy.test_odeslani_samostatneho_nalezu_p_001.end")
        
    def test_odeslani_samostatneho_nalezu_n_001(self):
        #Scenar_29 Odeslání samostatného nálezu (negativní scénář 1)     
        logger.info("AkceSamostatneNalezy.test_odeslani_samostatneho_nalezu_n_001.start")

        self.login("badatel1")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='M-202105907-N00091').first().stav , SN_ZAPSANY)          
        
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-samostatny_nalez > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneNalezy.mojeNalezy")).click()
        self.driver.find_element(By.LINK_TEXT, "M-202105907-N00091").click()
        
        #self.driver.find_element(By.CSS_SELECTOR, ".app-entity-dokument > .material-icons").click()   

        #with open("pas/tests/resources/test_foto_1.jpg", "rb") as image_file:
        #    encoded_string = base64.b64encode(image_file.read()).decode()

        #addFileToDropzone(self.driver,"#my-awesome-dropzone",'test_foto_1.jpg',encoded_string)
        #wait = WebDriverWait(self.driver, 10, poll_frequency=1, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
        #element = wait.until(EC.element_to_be_clickable((By.LINK_TEXT,  _("core.templates.core.upload_file.dz.removeFile"))))

        #self.driver.find_element(By.LINK_TEXT, _("core.templates.upload_file.submitButton.text")).click()
        try:
            self.driver.find_element(By.CSS_SELECTOR, "#pas-odeslat > .app-controls-button-text").click()
            with Wait_for_page_load(self.driver):
                self.driver.find_element(By.ID, "submit-btn").click()
                
        except Exception as e:
            pass

        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='M-202105907-N00091').first().stav , SN_ZAPSANY)  
        logger.info("AkceSamostatneNalezy.test_odeslani_samostatneho_nalezu_n_001.end")
        
        
    def test_potvrzeni_samostatneho_nalezu_p_001(self):
        #Scenar_30 Potvrzení samostatného nálezu (pozitivní scénář 1)     
        logger.info("AkceSamostatneNalezy.test_potvrzeni_samostatneho_nalezu_p_001.start")

        self.login("archeolog")        
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='C-202211308-N00213').first().stav , SN_ODESLANY)   
       
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-samostatny_nalez > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneNalezy.vybrat")).click()
        
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand").click()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_stav .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-11-1 > .text").click()
       
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "C-202211308-N00213").click()
        self.driver.find_element(By.CSS_SELECTOR, "#pas-potvrdit > .app-controls-button-text").click()
        self.driver.find_element(By.CSS_SELECTOR, ".col-sm-3:nth-child(1) > #div_id_evidencni_cislo #id_evidencni_cislo").click()
        self.driver.find_element(By.CSS_SELECTOR, ".col-sm-3:nth-child(1) > #div_id_evidencni_cislo #id_evidencni_cislo").send_keys("123")
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_predano .filter-option-inner-inner").click()
        self.driver.find_element(By.ID, "bs-select-1-0").click()

        self.driver.find_element(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-2-3 > .text").click()
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "submit-btn").click()

        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='C-202211308-N00213').first().stav , SN_POTVRZENY)  
        logger.info("AkceSamostatneNalezy.test_potvrzeni_samostatneho_nalezu_p_001.end")
        
        
    def test_potvrzeni_samostatneho_nalezu_n_001(self):
        #Scenar_31 Potvrzení samostatného nálezu (negativní scénář 1)   
        logger.info("AkceSamostatneNalezy.test_potvrzeni_samostatneho_nalezu_n_001.start")

        self.login("archeolog")
        
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='C-202211308-N00213').first().stav , SN_ODESLANY)   
       
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-samostatny_nalez > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneNalezy.vybrat")).click()
        
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand").click()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_stav .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-11-1 > .text").click()
       
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "C-202211308-N00213").click()
        self.driver.find_element(By.CSS_SELECTOR, "#pas-potvrdit > .app-controls-button-text").click()
        self.driver.find_element(By.CSS_SELECTOR, ".col-sm-3:nth-child(1) > #div_id_evidencni_cislo #id_evidencni_cislo").click()
        self.driver.find_element(By.CSS_SELECTOR, ".col-sm-3:nth-child(1) > #div_id_evidencni_cislo #id_evidencni_cislo").send_keys("123")
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_predano .filter-option-inner-inner").click()
        #self.driver.find_element(By.ID, "bs-select-1-0").click()

        self.driver.find_element(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-2-3 > .text").click()
        try:
            with Wait_for_page_load(self.driver):
                self.driver.find_element(By.ID, "submit-btn").click()
        except Exception as e:
            pass

        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='C-202211308-N00213').first().stav , SN_ODESLANY)  
        logger.info("AkceSamostatneNalezy.test_potvrzeni_samostatneho_nalezu_n_001.end")
        
        
    def test_potvrzeni_samostatneho_nalezu_n_002(self):
        #Scenar_32 Potvrzení samostatného nálezu (negativní scénář 2)
        logger.info("AkceSamostatneNalezy.test_potvrzeni_samostatneho_nalezu_n_002.start")

        self.login("archeolog")
        
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='C-202211308-N00213').first().stav , SN_ODESLANY)   
       
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-samostatny_nalez > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneNalezy.vybrat")).click()
        
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand").click()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_stav .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-11-1 > .text").click()
       
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "C-202211308-N00213").click()
        self.driver.find_element(By.CSS_SELECTOR, "#pas-potvrdit > .app-controls-button-text").click()
        #self.driver.find_element(By.CSS_SELECTOR, ".col-sm-3:nth-child(1) > #div_id_evidencni_cislo #id_evidencni_cislo").click()
        #self.driver.find_element(By.CSS_SELECTOR, ".col-sm-3:nth-child(1) > #div_id_evidencni_cislo #id_evidencni_cislo").send_keys("123")
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_predano .filter-option-inner-inner").click()
        self.driver.find_element(By.ID, "bs-select-1-0").click()

        self.driver.find_element(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-2-3 > .text").click()
        try:
            with Wait_for_page_load(self.driver):
                self.driver.find_element(By.ID, "submit-btn").click()
        except Exception as e:
            pass

        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='C-202211308-N00213').first().stav , SN_ODESLANY)  
        logger.info("AkceSamostatneNalezy.test_potvrzeni_samostatneho_nalezu_n_002.end")
        
        
    def test_archivace_samostatneho_nalezu_p_001(self):
        #Scenar_38 Archivace samostatného nálezu (pozitivní scénář 1)
        logger.info("AkceSamostatneNalezy.test_archivace_samostatneho_nalezu_p_001.start")

        self.login("archivar")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='C-202010474-N00002').first().stav , SN_POTVRZENY) 
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-samostatny_nalez > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneNalezy.vybrat")).click()
        
        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_stav .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-11-2 > .text").click()
        
        self.driver.find_element(By.CSS_SELECTOR, ".card > .card-body").click()
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "C-202010474-N00002").click()
        self.driver.find_element(By.CSS_SELECTOR, "#pas-archivovat > .app-controls-button-text").click()
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "submit-btn").click()
        
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='C-202010474-N00002').first().stav , SN_ARCHIVOVANY)            

        logger.info("AkceSamostatneNalezy.test_archivace_samostatneho_nalezu_p_001.end")
    
    def test_archivace_samostatneho_nalezu_n_001(self):
        #Scenar_39 Archivace samostatného nálezu (negativní scénář 1)
        logger.info("AkceSamostatneNalezy.test_archivace_samostatneho_nalezu_n_001.start")

        self.login("archivar")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='C-202010474-N00002').first().stav , SN_POTVRZENY) 
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-samostatny_nalez > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneNalezy.vybrat")).click()
        
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202010474-N00002")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "C-202010474-N00002").click()
        self.driver.find_element(By.CSS_SELECTOR, "#file-smazat-518731 > .material-icons").click()
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "submit-btn").click()        

        try:
            self.driver.find_element(By.CSS_SELECTOR, "#pas-archivovat > .app-controls-button-text").click()
            with Wait_for_page_load(self.driver):
                self.driver.find_element(By.ID, "submit-btn").click()
        except Exception as e:
            pass
        
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='C-202010474-N00002').first().stav , SN_POTVRZENY)  
        logger.info("AkceSamostatneNalezy.test_archivace_samostatneho_nalezu_n_001.end")
    

    def test_vraceni_samostatneho_nalezu_p_001(self):
        #Scenar_45 Vrácení samostatného nálezu (pozitivní scénář 1)
        logger.info("AkceSamostatneNalezy.test_vraceni_samostatneho_nalezu_p_001.start")

        self.login("archivar")
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='M-202301371-N00015').first().stav , SN_POTVRZENY) 
        
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-samostatny_nalez > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneNalezy.vybrat")).click()
        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("M-202301371-N00015")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "M-202301371-N00015").click()
        self.driver.find_element(By.CSS_SELECTOR, "#pas-vratit > .app-controls-button-text").click()
        self.wait(1)
        self.driver.find_element(By.ID, "id_reason").click()
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "submit-btn").click()        
        
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely='M-202301371-N00015').first().stav , SN_ODESLANY)  
        logger.info("AkceSamostatneNalezy.test_vraceni_samostatneho_nalezu_p_001.end")