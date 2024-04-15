import time
import datetime
import logging
import unittest

from django.conf import settings
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.constants import D_STAV_ZAPSANY,D_STAV_ODESLANY,D_STAV_ARCHIVOVANY
from core.tests.test_selenium import BaseSeleniumTestClass, Wait_for_page_load
from dokument.models import Dokument
from django.utils.translation import gettext as _
from selenium.common.exceptions import *
logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceDokumenty(BaseSeleniumTestClass):   
    def go_to_form_zapsat(self):
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-dokument > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.dokumenty.zapsat")).click()


    def go_to_form_vybrat(self):
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-dokument > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.dokumenty.vybrat")).click()

    
    def test_zapsani_dokumentu_p_001(self):
        #Scenar_64 Zapsání dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_zapsani_dokumentu_p_001.start")

        self.login("archivar")
        self.go_to_form_zapsat()
        
        count_old=Dokument.objects.count()          

        self.driver.find_element(By.CSS_SELECTOR, "#id-modal-region-div > #div_id_region .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-10-2 > .text").click()
       
        self.driver.find_element(By.CSS_SELECTOR, ".modal-footer > .btn-primary").click()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-selection__rendered").click()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Pavloň")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_rok_vzniku").click()
        self.driver.find_element(By.ID, "id_rok_vzniku").send_keys("2023")   
      
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("Archeologický ústav Brno")
        self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-2-1 > .text").click()
        
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-3-0 > .text").click()
        self.wait(1)
        self.driver.find_element(By.ID, "id_popis").click()
        self.driver.find_element(By.ID, "id_popis").send_keys("test")
        self.driver.find_element(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner").click()
        self.driver.find_element(By.ID, "bs-select-7-1").click()
       
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "newDocumentSubmitBtn").click()

        count_new=Dokument.objects.count()     

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceDokumenty.test_zapsani_dokumentu_p_001.end")
        
        
    def test_zapsani_dokumentu_n_001(self):
        #Scenar_65 Zapsání dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_zapsani_dokumentu_n_001.start")

        self.login("archivar")
        self.go_to_form_zapsat()
        
        count_old=Dokument.objects.count()          

        self.driver.find_element(By.CSS_SELECTOR, "#id-modal-region-div > #div_id_region .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-10-2 > .text").click()
       
        self.driver.find_element(By.CSS_SELECTOR, ".modal-footer > .btn-primary").click()
        #self.driver.find_element(By.CSS_SELECTOR, ".select2-selection__rendered").click()
        #self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Pavloň")
        #self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_rok_vzniku").click()
        self.driver.find_element(By.ID, "id_rok_vzniku").send_keys("2023")   
      
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("Archeologický ústav Brno")
        self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-2-1 > .text").click()
        
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-3-0 > .text").click()
        self.wait(1)
        self.driver.find_element(By.ID, "id_popis").click()
        self.driver.find_element(By.ID, "id_popis").send_keys("test")
        self.driver.find_element(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner").click()
        self.driver.find_element(By.ID, "bs-select-7-1").click()
        try:       
            with Wait_for_page_load(self.driver):
                self.driver.find_element(By.ID, "newDocumentSubmitBtn").click()
        except Exception as e:
            pass    
        count_new=Dokument.objects.count()     

        self.assertEqual(count_old, count_new)
        logger.info("AkceDokumenty.test_zapsani_dokumentu_n_001.end")
        

    def test_odeslani_dokumentu_p_001(self):
        #Scenar_66 Odeslání dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_odeslani_dokumentu_p_001.start")

        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='X-C-TX-202413000').first().stav , D_STAV_ZAPSANY)   
        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-202413000")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "X-C-TX-202413000").click()
        self.driver.find_element(By.CSS_SELECTOR, "#dokument-odeslat > .app-controls-button-text").click()
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "submit-btn").click()
   
        self.assertEqual(Dokument.objects.filter(ident_cely='X-C-TX-202413000').first().stav , D_STAV_ODESLANY)  

        logger.info("AkceDokumenty.test_odeslani_dokumentu_p_001.end")
        
        
    def test_odeslani_dokumentu_n_001(self):
        #Scenar_67 Odeslání dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_odeslani_dokumentu_n_001.start")

        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='X-C-TX-202413001').first().stav , D_STAV_ZAPSANY)   
        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-202413001")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "X-C-TX-202413001").click()
        try:
            with Wait_for_page_load(self.driver):
                self.driver.find_element(By.CSS_SELECTOR, "#dokument-odeslat > .app-controls-button-text").click()
                self.driver.find_element(By.ID, "submit-btn").click()
        except Exception as e:
            pass    
   
        self.assertEqual(Dokument.objects.filter(ident_cely='X-C-TX-202413001').first().stav , D_STAV_ZAPSANY)   
        logger.info("AkceDokumenty.test_odeslani_dokumentu_n_001.end")
        
        
    @unittest.skip    
    def test_archivace_dokumentu_p_001(self):
        #Scenar_68 Archivace dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_archivace_dokumentu_p_001.start")

        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='X-C-TX-202413020').first().stav , D_STAV_ODESLANY)   
        id=Dokument.objects.filter(ident_cely='X-C-TX-202413020').first().id
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-202413020")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "X-C-TX-202413020").click()
        self.driver.find_element(By.CSS_SELECTOR, "#dokument-archivovat > .app-controls-button-text").click()
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "submit-btn").click()
        #self.wait(self.wait_interval+10)
        self.assertEqual(Dokument.objects.filter(id=id).first().stav , D_STAV_ARCHIVOVANY)   
        logger.info("AkceDokumenty.test_archivace_dokumentu_p_001.end")
        
        
    def test_archivace_dokumentu_n_001(self):
        #Scenar_69 Archivace dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_archivace_dokumentu_n_001.start")

        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='X-C-TX-202413013').first().stav , D_STAV_ODESLANY)   
        id=Dokument.objects.filter(ident_cely='X-C-TX-202413013').first().id
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-TX-202413013")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "X-C-TX-202413013").click()
        try:
            with Wait_for_page_load(self.driver):
                self.driver.find_element(By.CSS_SELECTOR, "#dokument-archivovat > .app-controls-button-text").click()
                self.driver.find_element(By.ID, "submit-btn").click()
        except Exception as e:
            pass
        
        self.assertEqual(Dokument.objects.filter(id=id).first().stav , D_STAV_ODESLANY)   
        logger.info("AkceDokumenty.test_archivace_dokumentu_n_001.end")
        
    
    def test_vraceni_odeslaneho_dokumentu_p_001(self):
        #Scenar_70 Vrácení odeslaného dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_vraceni_odeslaneho_dokumentu_p_001.start")

        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='M-TX-201604272').first().stav , D_STAV_ODESLANY)   
        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("M-TX-201604272")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "M-TX-201604272").click()
        self.driver.find_element(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text").click()
        self.wait(1)
        self.driver.find_element(By.ID, "id_reason").click()
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "submit-btn").click()

        self.assertEqual(Dokument.objects.filter(ident_cely='M-TX-201604272').first().stav , D_STAV_ZAPSANY)   
        logger.info("AkceDokumenty.test_vraceni_odeslaneho_dokumentu_p_001.end")    
        
        
    def test_vraceni_odeslaneho_dokumentu_n_001(self):
        #Scenar_71 Vrácení odeslaného dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_vraceni_odeslaneho_dokumentu_n_001.start")

        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='M-TX-201604272').first().stav , D_STAV_ODESLANY)   
        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("M-TX-201604272")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "M-TX-201604272").click()
        self.driver.find_element(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text").click()
        #self.driver.find_element(By.ID, "id_reason").click()
        #self.driver.find_element(By.ID, "id_reason").send_keys("test")
        try:
            with Wait_for_page_load(self.driver):
                self.driver.find_element(By.ID, "submit-btn").click()
        except Exception as e:
            pass
        self.assertEqual(Dokument.objects.filter(ident_cely='M-TX-201604272').first().stav , D_STAV_ODESLANY)   
        logger.info("AkceDokumenty.test_vraceni_odeslaneho_dokumentu_n_001.end")    
        
        
    def test_vraceni_archivovaneho_dokumentu_p_001(self):
        #Scenar_72 Vrácení archivovaného dokumentu (pozitivní scénář 1)
        logger.info("AkceDokumenty.test_vraceni_archivovaneho_dokumentu_p_001.start")

        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='C-TX-202400071').first().stav , D_STAV_ARCHIVOVANY)   
        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-TX-202400071")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "C-TX-202400071").click()
        self.driver.find_element(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text").click()
        self.wait(1)
        self.driver.find_element(By.ID, "id_reason").click()
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "submit-btn").click()        

        self.assertEqual(Dokument.objects.filter(ident_cely='C-TX-202400071').first().stav , D_STAV_ODESLANY)   
        logger.info("AkceDokumenty.test_vraceni_archivovaneho_dokumentu_p_001.end") 
        
        
    def test_vraceni_archivovaneho_dokumentu_n_001(self):
        #Scenar_73 Vrácení archivovaného dokumentu (negativní scénář 1)
        logger.info("AkceDokumenty.test_vraceni_archivovaneho_dokumentu_n_001.start")

        self.login("archivar")
        self.go_to_form_vybrat()
      
        self.assertEqual(Dokument.objects.filter(ident_cely='C-TX-202400071').first().stav , D_STAV_ARCHIVOVANY)   
        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-TX-202400071")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "C-TX-202400071").click()
        self.driver.find_element(By.CSS_SELECTOR, "#dokument-vratit > .app-controls-button-text").click()
        #self.driver.find_element(By.ID, "id_reason").click()
        #self.driver.find_element(By.ID, "id_reason").send_keys("test")
        try:
            with Wait_for_page_load(self.driver):
                self.driver.find_element(By.ID, "submit-btn").click()        
        except Exception as e:
            pass
        self.assertEqual(Dokument.objects.filter(ident_cely='C-TX-202400071').first().stav , D_STAV_ARCHIVOVANY)   

        logger.info("AkceDokumenty.test_vraceni_archivovaneho_dokumentu_n_001.end") 
        

        
     