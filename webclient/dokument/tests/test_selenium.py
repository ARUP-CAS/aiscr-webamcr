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
from core.constants import D_STAV_ZAPSANY,D_STAV_ODESLANY,D_STAV_ARCHIVOVANY
from core.tests.test_selenium import BaseSeleniumTestClass, WaitForPageLoad
from dokument.models import Dokument
from django.utils.translation import gettext as _
from selenium.common.exceptions import *
logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceDokumenty(BaseSeleniumTestClass):   
    def go_to_form_zapsat(self):
        self.ElementClick(By.CSS_SELECTOR, ".app-entity-dokument > .card-body")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.dokumenty.zapsat"))

    def go_to_form_vybrat(self):
        self.ElementClick(By.CSS_SELECTOR, ".app-entity-dokument > .card-body")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.dokumenty.vybrat"))
    
    def test_064_zapsani_dokumentu_p_001(self):
        #Scenar_64 Zapsání dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_064_zapsani_dokumentu_p_001.start")
        self.login("archivar")
        self.go_to_form_zapsat()
        
        count_old=Dokument.objects.count()          
        #self.wait(self.wait_interval)
        self.ElementClick(By.CSS_SELECTOR, "#id-modal-region-div > #div_id_region .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-10-2 > .text")
        
        self.ElementClick(By.CSS_SELECTOR, ".modal-footer > .btn-primary")
        #self.wait(1)
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Pavloň")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vzniku")
        self.driver.find_element(By.ID, "id_rok_vzniku").send_keys("2023")   
      
        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("Archeologický ústav Brno")
        #self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        
        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")
        
        self.ElementClick(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-0 > .text")
        #self.wait(1)
        self.ElementClick(By.ID, "id_popis")
        self.driver.find_element(By.ID, "id_popis").send_keys("test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-7-1")
       
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")

        count_new=Dokument.objects.count()     

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceDokumenty.test_064_zapsani_dokumentu_p_001.end")        
        
    def test_065_zapsani_dokumentu_n_001(self):
        #Scenar_65 Zapsání dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_065_zapsani_dokumentu_n_001.start")
        self.login("archivar")
        self.go_to_form_zapsat()
        
        count_old=Dokument.objects.count()          
        #self.wait(self.wait_interval)
        self.ElementClick(By.CSS_SELECTOR, "#id-modal-region-div > #div_id_region .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-10-2 > .text")
       
        self.ElementClick(By.CSS_SELECTOR, ".modal-footer > .btn-primary")
        #self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        #self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Pavloň")
        #self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        #self.wait(1)
        self.ElementClick(By.ID, "id_rok_vzniku")
        self.driver.find_element(By.ID, "id_rok_vzniku").send_keys("2023")   
      
        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("Archeologický ústav Brno")
        #self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        
        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")
        
        self.ElementClick(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-0 > .text")
        #self.wait(1)
        self.ElementClick(By.ID, "id_popis")
        self.driver.find_element(By.ID, "id_popis").send_keys("test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-7-1")
        try:       
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "newDocumentSubmitBtn")
        except Exception as e:
            pass    
        count_new=Dokument.objects.count()     

        self.assertEqual(count_old, count_new)
        logger.info("AkceDokumenty.test_065_zapsani_dokumentu_n_001.end")        

    def test_066_odeslani_dokumentu_p_001(self):
        #Scenar_66 Odeslání dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_066_odeslani_dokumentu_p_001.start")
        self.login("badatel")
        self.go_to_form_vybrat()
        self.assertEqual(Dokument.objects.filter(ident_cely='X-C-TX-000000003').first().stav , D_STAV_ZAPSANY)   
        id=Dokument.objects.filter(ident_cely='X-C-TX-000000003').first().id
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-000000003")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-TX-000000003")
        self.ElementClick(By.CSS_SELECTOR, ".app-entity-dokument > .material-icons")        
        with open("dokument/tests/resources/test.jpg", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        self.addFileToDropzone("#my-awesome-dropzone",'test.jpg',encoded_string)
        self.driver.set_script_timeout(15)
        response = self.driver.execute_async_script("""
            var done = arguments[0];           
           newDropzone.on("success", 
            function(){ done('foo');});
            """)
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.LINK_TEXT, _("core.templates.upload_file.submitButton.text"))        
        self.ElementClick(By.CSS_SELECTOR, "#dokument-odeslat > .app-controls-button-text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.assertEqual(Dokument.objects.filter(id=id).first().stav , D_STAV_ODESLANY) 

        logger.info("AkceDokumenty.test_066_odeslani_dokumentu_p_001.end")        
        
    def test_067_odeslani_dokumentu_n_001(self):
        #Scenar_67 Odeslání dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_067_odeslani_dokumentu_n_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='X-C-TX-202413001').first().stav , D_STAV_ZAPSANY)  
        #self.wait(1) 
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-202413001")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-TX-202413001")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.CSS_SELECTOR, "#dokument-odeslat > .app-controls-button-text")
                self.ElementClick(By.ID, "submit-btn")
        except Exception as e:
            pass    
   
        self.assertEqual(Dokument.objects.filter(ident_cely='X-C-TX-202413001').first().stav , D_STAV_ZAPSANY)   
        logger.info("AkceDokumenty.test_067_odeslani_dokumentu_n_001.end")        
        
    @unittest.skip    
    def test_068_archivace_dokumentu_p_001(self):
        #Scenar_68 Archivace dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_068_archivace_dokumentu_p_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='X-C-TX-202413020').first().stav , D_STAV_ODESLANY)   
        id=Dokument.objects.filter(ident_cely='X-C-TX-202413020').first().id
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-202413020")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-TX-202413020")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-archivovat > .app-controls-button-text")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        #self.wait(self.wait_interval+10)
        self.assertEqual(Dokument.objects.filter(id=id).first().stav , D_STAV_ARCHIVOVANY)   
        logger.info("AkceDokumenty.test_068_archivace_dokumentu_p_001.end")        
        
    def test_069_archivace_dokumentu_n_001(self):
        #Scenar_69 Archivace dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_069_archivace_dokumentu_n_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='X-C-TX-202413013').first().stav , D_STAV_ODESLANY)   
        id=Dokument.objects.filter(ident_cely='X-C-TX-202413013').first().id
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-202413013")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-TX-202413013")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.CSS_SELECTOR, "#dokument-archivovat > .app-controls-button-text")
                self.ElementClick(By.ID, "submit-btn")
        except Exception as e:
            pass
        
        self.assertEqual(Dokument.objects.filter(id=id).first().stav , D_STAV_ODESLANY)   
        logger.info("AkceDokumenty.test_069_archivace_dokumentu_n_001.end")        
    
    def test_070_vraceni_odeslaneho_dokumentu_p_001(self):
        #Scenar_70 Vrácení odeslaného dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_070_vraceni_odeslaneho_dokumentu_p_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='M-TX-201604272').first().stav , D_STAV_ODESLANY)   
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("M-TX-201604272")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "M-TX-201604272")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text")
        #self.wait(1)
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        self.assertEqual(Dokument.objects.filter(ident_cely='M-TX-201604272').first().stav , D_STAV_ZAPSANY)   
        logger.info("AkceDokumenty.test_070_vraceni_odeslaneho_dokumentu_p_001.end")          
        
    def test_071_vraceni_odeslaneho_dokumentu_n_001(self):
        #Scenar_71 Vrácení odeslaného dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_071_vraceni_odeslaneho_dokumentu_n_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='M-TX-201604272').first().stav , D_STAV_ODESLANY)   
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("M-TX-201604272")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "M-TX-201604272")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text")
        #self.ElementClick(By.ID, "id_reason")
        #self.driver.find_element(By.ID, "id_reason").send_keys("test")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        except Exception as e:
            pass
        self.assertEqual(Dokument.objects.filter(ident_cely='M-TX-201604272').first().stav , D_STAV_ODESLANY)   
        logger.info("AkceDokumenty.test_071_vraceni_odeslaneho_dokumentu_n_001.end")           
        
    def test_072_vraceni_archivovaneho_dokumentu_p_001(self):
        #Scenar_72 Vrácení archivovaného dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_072_vraceni_archivovaneho_dokumentu_p_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='C-TX-202400071').first().stav , D_STAV_ARCHIVOVANY)   
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-TX-202400071")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-TX-202400071")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text")
        #self.wait(1)
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with WaitForPageLoad(self.driver):
            self.ElementClick(By.ID, "submit-btn")        

        self.assertEqual(Dokument.objects.filter(ident_cely='C-TX-202400071').first().stav , D_STAV_ODESLANY)   
        logger.info("AkceDokumenty.test_072_vraceni_archivovaneho_dokumentu_p_001.end")         
        
    def test_073_vraceni_archivovaneho_dokumentu_n_001(self):
        #Scenar_73 Vrácení archivovaného dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_073_vraceni_archivovaneho_dokumentu_n_001.start")
        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='C-TX-202400071').first().stav , D_STAV_ARCHIVOVANY)   
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-TX-202400071")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-TX-202400071")
        self.ElementClick(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text")
        #self.ElementClick(By.ID, "id_reason")
        #self.driver.find_element(By.ID, "id_reason").send_keys("test")
        try:
            with WaitForPageLoad(self.driver):
                self.ElementClick(By.ID, "submit-btn")        
        except Exception as e:
            pass
        self.assertEqual(Dokument.objects.filter(ident_cely='C-TX-202400071').first().stav , D_STAV_ARCHIVOVANY)   
        logger.info("AkceDokumenty.test_073_vraceni_archivovaneho_dokumentu_n_001.end") 
        

        
     