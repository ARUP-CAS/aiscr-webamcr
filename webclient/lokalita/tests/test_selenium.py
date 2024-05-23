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
from core.constants import AZ_STAV_ZAPSANY,AZ_STAV_ODESLANY,AZ_STAV_ARCHIVOVANY

from core.tests.test_selenium import BaseSeleniumTestClass, Wait_for_page_load

from arch_z.models import ArcheologickyZaznam
from dj.models import DokumentacniJednotka
from komponenta.models import Komponenta

from lokalita.models import Lokalita
from django.utils.translation import gettext as _
from selenium.common.exceptions import *
logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceLokality(BaseSeleniumTestClass):   
    def go_to_form_zapsat(self):
        self.ElementClick(By.CSS_SELECTOR, ".app-entity-lokalita > .card-body")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.lokality.zapsat"))


    def go_to_form_vybrat(self):
        self.ElementClick(By.CSS_SELECTOR, ".app-entity-lokalita > .card-body")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.lokality.vybrat"))
 
        
    def test_051_zapsani_lokality_p_001(self):
        #Scenar_51 Zapsání lokality (pozitivní scénář 1)
        logger.info("AkceLokality.test_051_zapsani_lokality_p_001.start")
        self.login("archeolog")       
        self.go_to_form_zapsat()
        count_old=Lokalita.objects.count()       

        self.ElementClick(By.ID, "select2-id_hlavni_katastr-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Křtiny")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_druh .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("pol")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-5-0 > .text")
        #self.ElementClick(By.ID, "div_id_nazev")
        self.wait(1)
        self.ElementClick(By.ID, "id_nazev")
        self.driver.find_element(By.ID, "id_nazev").send_keys("test")
        
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "newEntitySubmitBtn")
       
        count_new = Lokalita.objects.count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceLokality.test_051_zapsani_lokality_p_001.end")
        
        
    def test_052_zapsani_lokality_n_001(self):
        #Scenar_52 Zapsání lokality (negativní scénář 1)
        logger.info("AkceLokality.test_052_zapsani_lokality_n_001.start")
        self.login("archeolog")       
        self.go_to_form_zapsat()
        count_old=Lokalita.objects.count()       

        self.ElementClick(By.ID, "select2-id_hlavni_katastr-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Křtiny")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_druh .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("pol")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_pristupnost .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-5-0 > .text")
        #self.ElementClick(By.ID, "div_id_nazev")
        #self.ElementClick(By.ID, "id_nazev")
        #self.driver.find_element(By.ID, "id_nazev").send_keys("test")
        try:
            with Wait_for_page_load(self.driver):
                self.ElementClick(By.ID, "newEntitySubmitBtn")
        except Exception as e:
            pass
       
        count_new = Lokalita.objects.count()
        self.assertEqual(count_old , count_new)
        logger.info("AkceLokality.test_052_zapsani_lokality_n_001.end")
        
        
    def test_053_pridani_DJ_lokality_p_001(self):
        #Scenar_53 Přidání dokumentační jednotky lokalita (pozitivní scénář 1)
        logger.info("AkceLokality.test_053_pridani_DJ_lokality_p_001.start")
        self.login("archeolog")       
        self.go_to_form_vybrat()
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-L000000001").count()     

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-L000000001")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")

        self.ElementClick(By.LINK_TEXT, "X-C-L000000001")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-2 > .text")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-2-0")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "newDjSubmitButton")
       
        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-L000000001").count()     
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceLokality.test_053_pridani_DJ_lokality_p_001.end")
        
        
    def test_054_pridani_DJ_lokality_n_001(self):
        #Scenar_54 Přidání dokumentační jednotky lokalita (negativní scénář 1)
        logger.info("AkceLokality.test_054_pridani_DJ_lokality_n_001.start")
        self.login("archeolog")       
        self.go_to_form_vybrat()
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-L000000001").count()     

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-L000000001")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")

        self.ElementClick(By.LINK_TEXT, "X-C-L000000001")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        #self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        #self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-2 > .text")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-2-0")
        try:
            with Wait_for_page_load(self.driver):
                self.ElementClick(By.ID, "newDjSubmitButton")
        except Exception as e:
            pass   
       
        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-L000000001").count()     
        self.assertEqual(count_old , count_new)
        logger.info("AkceLokality.test_054_pridani_DJ_lokality_n_001.end")
        
        
    def test_055_pridani_komponenty_DJ_lokality_p_001(self):
        #Scenar_55 Přidání komponenty k dokumentační jednotce lokalita (pozitivní scénář 1)
        logger.info("AkceLokality.test_055_pridani_komponenty_DJ_lokality_p_001.start")
        self.login("archeolog")       
        self.go_to_form_vybrat()
        count_old=Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-L000000002-D01").count()

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")

        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-L000000002")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "X-C-L000000002")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_L000000002_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_X-C-L000000002-D01 > .card-header .material-icons")
        self.ElementClick(By.LINK_TEXT, _("lokalita.templates.dj.djUpdate.moreActions.pridatKomponentu.label"))
        self.ElementClick(By.CSS_SELECTOR, "#div_id_obdobi .filter-option-inner-inner")        
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("úně")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.DOWN)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
       
        self.ElementClick(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("s")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "createCompotSubmitButton")
    
        count_new = Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-L000000002-D01").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceLokality.test_055_pridani_komponenty_DJ_lokality_p_001.end")
        

    def test_056_odeslani_lokality_p_001(self):
        #Scenar_56 Odeslání lokality (pozitivní scénář 1)
        logger.info("AkceLokality.test_056_odeslani_lokality_p_001.start")
        self.login("archeolog")       
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N9000579').first().stav , AZ_STAV_ZAPSANY)   

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")

        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N9000579")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N9000579")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-odeslat > .app-controls-button-text")
        self.wait(1)
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")
  
    
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N9000579').first().stav , AZ_STAV_ODESLANY)   
        logger.info("AkceLokality.test_056_odeslani_lokality_p_001.end")
        
        
    def test_057_odeslani_lokality_n_001(self):
        #Scenar_57 Odeslání lokality (negativní scénář 1)
        logger.info("AkceLokality.test_057_odeslani_lokality_n_001.start")

        self.login("archeolog")       
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N9000145').first().stav , AZ_STAV_ZAPSANY)   

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")

        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N9000145")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N9000145")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-odeslat > .app-controls-button-text")
        try:
            with Wait_for_page_load(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        except Exception as e:
            pass    
    
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N9000145').first().stav , AZ_STAV_ZAPSANY) 
        logger.info("AkceLokality.test_057_odeslani_lokality_n_001.end")
        
        
    def test_058_archivace_lokality_p_001(self):
        #Scenar_58 Archivace lokality (pozitivní scénář 1)
        logger.info("AkceLokality.test_058_archivace_lokality_p_001.start")
        self.login("archivar")       
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N1000003').first().stav , AZ_STAV_ODESLANY)   
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-archivovat > .material-icons")
        self.wait(1)
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")  
    
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N1000003').first().stav , AZ_STAV_ARCHIVOVANY)   
        logger.info("AkceLokality.test_058_archivace_lokality_p_001.end")
        
        
    def test_059_archivace_lokality_n_001(self):
        #Scenar_59 Archivace lokality (negativní scénář 1)
        logger.info("AkceLokality.test_059_archivace_lokality_n_001.start")
        self.login("archivar")       
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N1000109').first().stav , AZ_STAV_ODESLANY)   
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N1000109")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N1000109")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-archivovat > .material-icons")
        try:
            with Wait_for_page_load(self.driver):
                self.ElementClick(By.ID, "submit-btn")  
        except Exception as e:
            pass
            
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N1000109').first().stav , AZ_STAV_ODESLANY)   
        logger.info("AkceLokality.test_059_archivace_lokality_n_001.end")
        
        
    def test_060_vraceni_odeslane_lokality_p_001(self):
        #Scenar_60 Vrácení odeslané lokality (pozitivní scénář 1)
        logger.info("AkceLokality.test_060_vraceni_odeslane_lokality_p_001.start")
        self.login("archivar")       
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N1000003').first().stav , AZ_STAV_ODESLANY)   

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-vratit > .app-controls-button-text")
        self.wait(1)
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")
                    
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N1000003').first().stav , AZ_STAV_ZAPSANY)   
        logger.info("AkceLokality.test_060_vraceni_odeslane_lokality_p_001.end")
        
        
    def test_061_vraceni_odeslane_lokality_n_001(self):
        #Scenar_61 Vrácení odeslané lokality (negativní scénář 1)
        logger.info("AkceLokality.test_061_vraceni_odeslane_lokality_n_001.start")
        self.login("archivar")       
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N1000003').first().stav , AZ_STAV_ODESLANY)   

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N1000003")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-vratit > .app-controls-button-text")
        #self.ElementClick(By.ID, "id_reason")
        #self.driver.find_element(By.ID, "id_reason").send_keys("test")
        try:
            with Wait_for_page_load(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        except Exception as e:
            pass            
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N1000003').first().stav , AZ_STAV_ODESLANY)   
        logger.info("AkceLokality.test_061_vraceni_odeslane_lokality_n_001.end")
    
        
    def test_062_vraceni_archivovane_lokality_p_001(self):
        #Scenar_62 Vrácení archivované lokality (pozitivní scénář 1)
        logger.info("AkceLokality.test_062_vraceni_archivovane_lokality_p_001.start")

        self.login("archivar")       
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N9000593').first().stav , AZ_STAV_ARCHIVOVANY)   

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N9000593")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N9000593")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-vratit > .app-controls-button-text")
        self.wait(1)
        self.ElementClick(By.ID, "id_reason")
        self.driver.find_element(By.ID, "id_reason").send_keys("test")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")
                    
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N9000593').first().stav , AZ_STAV_ODESLANY)   
        logger.info("AkceLokality.test_062_vraceni_archivovane_lokality_p_001.end")
        
        
    def test_063_vraceni_archivovane_lokality_n_001(self):
        #Scenar_63 Vrácení archivované lokality (negativní scénář 1)
        logger.info("AkceLokality.test_063_vraceni_archivovane_lokality_n_001.start")

        self.login("archivar")       
        self.go_to_form_vybrat()
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N9000593').first().stav , AZ_STAV_ARCHIVOVANY)   

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-N9000593")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(10)")
        self.ElementClick(By.LINK_TEXT, "C-N9000593")
        self.ElementClick(By.CSS_SELECTOR, "#lokalita-vratit > .app-controls-button-text")
        #self.ElementClick(By.ID, "id_reason")
        #self.driver.find_element(By.ID, "id_reason").send_keys("test")
        try:
            with Wait_for_page_load(self.driver):
                self.ElementClick(By.ID, "submit-btn")
        except Exception as e:
            pass                        
        self.assertEqual(ArcheologickyZaznam.objects.filter(ident_cely='C-N9000593').first().stav , AZ_STAV_ARCHIVOVANY)  
        logger.info("AkceLokality.test_063_vraceni_archivovane_lokality_n_001.end")
  