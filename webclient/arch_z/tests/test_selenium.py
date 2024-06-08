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

from core.tests.test_selenium import BaseSeleniumTestClass, Wait_for_page_load
from arch_z.models import Akce,ExterniOdkaz
from dokument.models import DokumentCast
from dj.models import DokumentacniJednotka
from komponenta.models import Komponenta
from pian.models import Pian
from nalez.models import NalezObjekt, NalezPredmet
from django.utils.translation import gettext as _
from selenium.common.exceptions import *
logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceProjektoveAkce(BaseSeleniumTestClass):   
    def go_to_Projekty_vyper(self):
        self.ElementClick(By.CSS_SELECTOR, ".card:nth-child(1) .btn")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.projekty.vybratProjekty")) 

    def  draw_polygon(self):       
        self.wait(1)
        self.driver.execute_script('''map.setZoom(16); return map.getZoom();''')
        self.wait(2)  
        self.ElementClick(By.LINK_TEXT, _("mapa.EditAddPolygon"))
        self.clickAt(self.driver.find_element(By.ID, "djMap"),0,0)
        self.wait(0.2) 
        self.clickAt(self.driver.find_element(By.ID, "djMap"),0,20)
        self.wait(0.2) 
        self.clickAt(self.driver.find_element(By.ID, "djMap"),20,20)
        self.wait(0.2) 
        self.clickAt(self.driver.find_element(By.ID, "djMap"),20,0)
        self.wait(0.2) 
        self.ElementClick(By.LINK_TEXT, _("mapa.EditFinishText"))
        self.wait(0.2) 
    
    def test_024_pridani_dokumentacni_jednotky_p_001(self):
        #Scenar_24 Přidání dokumentační jednotky celek akce (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_024_pridani_dokumentacni_jednotky_p_001.start")

        self.login()
        self.go_to_Projekty_vyper()
        
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202307816A").count()
        
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202307816")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202307816")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")       
        self.ElementClick(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "newDjSubmitButton")            
        
        self.assertNotEqual(self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202307816A_D01 > strong"), None)
        count_new=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202307816A").count()

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceProjektoveAkce.test_024_pridani_dokumentacni_jednotky_p_001.end")
        
        
    def test_034_pridani_dokumentacni_jednotky_n_001(self):
        #Scenar_34 Přidání dokumentační jednotky celek akce (negativní scénář 1)
        logger.info("AkceProjektoveAkce.test_034_pridani_dokumentacni_jednotky_n_001.start")
        self.login()
        self.go_to_Projekty_vyper()
        #ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202401502A").count()
        
        self.ElementClick(By.CSS_SELECTOR, ".btn > .mr-1")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_stav .filter-option-inner-inner")
        self.ElementClick(By.XPATH, "//span[contains(.,\'"+_("projekt.models.projekt.states.zahajenVTerenu.label")+"\')]")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202401502")   
             
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        #self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        #self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")
       
        try:
            with Wait_for_page_load(self.driver):
                self.ElementClick(By.ID, "newDjSubmitButton")       
        except Exception as e:
            pass       
        
        #self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401502A_D01 > strong"), None)
        count_new=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202401502A").count()

        self.assertEqual(count_old , count_new)
        logger.info("AkceProjektoveAkce.test_034_pridani_dokumentacni_jednotky_n_001.end")
        
        
    def test_035_pridani_dokumentacni_jednotky_p_002(self):
        #Scenar_35 Přidání dokumentační jednotky část akce (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_035_pridani_dokumentacni_jednotky_p_002.start")
        self.login()
        self.go_to_Projekty_vyper()
        #ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()
        
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202309552")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        
        self.ElementClick(By.LINK_TEXT, "C-202309552")

        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")  
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")        
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")       
        self.ElementClick(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner")       
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")  
        with Wait_for_page_load(self.driver):     
            self.ElementClick(By.ID, "newDjSubmitButton")  
          
        self.assertNotEqual(self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202309552A_D02 > strong"), None)
        count_new=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceProjektoveAkce.test_035_pridani_dokumentacni_jednotky_p_002.end")
        
        
    def test_036_pridani_dokumentacni_jednotky_n_002(self):
        #Scenar_36 Přidání dokumentační jednotky část akce (negativní scénář 1)
        logger.info("AkceProjektoveAkce.test_036_pridani_dokumentacni_jednotky_n_002.start")
        self.login()
        self.go_to_Projekty_vyper()
        #ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()
        
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202309552")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        
        self.ElementClick(By.LINK_TEXT, "C-202309552")

        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")  
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        #self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")        
        #self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")       
        self.ElementClick(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner")       
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-1 > .text")       
 
        try:
            with Wait_for_page_load(self.driver):
                self.ElementClick(By.ID, "newDjSubmitButton")       
        except Exception as e:
            pass
          
        #self.assertNotEqual(self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202309552A_D02 > strong"), None)
        count_new=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()

        self.assertEqual(count_old , count_new)
        logger.info("AkceProjektoveAkce.test_036_pridani_dokumentacni_jednotky_n_002.end")


    def test_037_pridani_komponenty_dokumentacni_jednotky_p_001(self):
        #Scenar_37 Přidání komponenty k dokumentační jednotce celek akce (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_037_pridani_komponenty_dokumentacni_jednotky_p_001.start")
        self.login()
        self.go_to_Projekty_vyper() #C-202309027
        #ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        #count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()
        count_old=Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202309027A-D01").count()

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202309027")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202309027")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202309027A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_C-202309027A-D01 .btn-group:nth-child(1) .material-icons")
        self.ElementClick(By.LINK_TEXT, _("arch_z.templates.arch_z.dj.partials.dj_update.editButtons.pridatKomponentu.label"))
        self.ElementClick(By.CSS_SELECTOR, "#div_id_obdobi .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("ún")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_jistota .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-2-0")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-3 > .text")
        
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "createCompotSubmitButton")  
                      
        self.assertNotEqual(self.driver.find_element(By.ID, "el_komponenta_C_202309027A_K001"), None)
        count_new=Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202309027A-D01").count()

        self.assertEqual(count_old+1 , count_new)
        logger.info("AkceProjektoveAkce.test_037_pridani_komponenty_dokumentacni_jednotky_p_001.end")


    def test_040_pridani_komponenty_dokumentacni_jednotky_n_001(self):
        #Scenar_40 Přidání komponenty k dokumentační jednotce celek akce (negativní scénář 1)
        logger.info("AkceProjektoveAkce.test_040_pridani_komponenty_dokumentacni_jednotky_n_001.start")
        self.login()
        self.go_to_Projekty_vyper() #C-202309027
        #ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        #count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()
        count_old=Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202309027A-D01").count()

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202309027")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202309027")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202309027A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_C-202309027A-D01 .btn-group:nth-child(1) .material-icons")
        self.ElementClick(By.LINK_TEXT, _("arch_z.templates.arch_z.dj.partials.dj_update.editButtons.pridatKomponentu.label"))
        self.ElementClick(By.CSS_SELECTOR, "#div_id_obdobi .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("ún")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_jistota .filter-option-inner-inner")
        self.ElementClick(By.ID, "bs-select-2-0")
        #self.ElementClick(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner")
        #self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-3 > .text")
        
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "createCompotSubmitButton")    
          
        #self.assertNotEqual(self.driver.find_element(By.ID, "el_komponenta_C_202309027A_K001"), None)
        self.assertEqual(len(self.driver.find_elements(By.ID, "el_komponenta_C_202309027A_K001")),0)
        count_new=Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202309027A-D01").count()

        self.assertEqual(count_old , count_new)
        logger.info("AkceProjektoveAkce.test_040_pridani_komponenty_dokumentacni_jednotky_n_001.end")


    def test_041_pridani_objektu_komponente_p_001(self):
        #Scenar_41 Přidání objektu k pozitivní komponentě (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_041_pridani_objektu_komponente_p_001.start")
        self.login()
        self.go_to_Projekty_vyper() #C-202309027
        count_old=NalezObjekt.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202004814A-D01").count()

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202004814")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202004814")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.ID, "el_komponenta_C_202004814A_K001")
        #with Wait_for_page_load(self.driver):
        self.ElementClick(By.CSS_SELECTOR, "#div_id_C-202004814A-K001_o-0-druh .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-7-6 > .text")
        self.ElementClick(By.ID, "id_C-202004814A-K001_o-0-pocet")
        self.driver.find_element(By.ID, "id_C-202004814A-K001_o-0-pocet").send_keys("1")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton") 

        count_new=NalezObjekt.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202004814A-D01").count()
        self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, ".badge.badge-primary.badge-pill").text,'1')
        self.assertEqual(count_old+1 , count_new)
        logger.info("AkceProjektoveAkce.test_041_pridani_objektu_komponente_p_001.end")
        
        
    def test_042_pridani_predmetu_komponente_p_001(self):
        #Scenar_42 Přidání předmětu k pozitivní komponentě (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_042_pridani_predmetu_komponente_p_001.start")
        self.login()
        self.go_to_Projekty_vyper() #C-202309027

        count_old=NalezPredmet.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202004814A-D01").count()

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202004814")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202004814")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "el_komponenta_C_202004814A_K001")
       
        self.ElementClick(By.CSS_SELECTOR, "#div_id_C-202004814A-K001_p-0-druh .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-11-82 > .text")

        self.ElementClick(By.CSS_SELECTOR, "#div_id_C-202004814A-K001_p-0-specifikace .filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-12-15 > .text")

        self.ElementClick(By.ID, "id_C-202004814A-K001_p-0-pocet")
        self.driver.find_element(By.ID, "id_C-202004814A-K001_p-0-pocet").send_keys("1")
        
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton") 

        count_new=NalezPredmet.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202004814A-D01").count()
        self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, ".badge.badge-primary.badge-pill").text,'1')
        self.assertEqual(count_old+1 , count_new)
        logger.info("AkceProjektoveAkce.test_042_pridani_predmetu_komponente_p_001.end")
        
    def test_043_smazani_objektu_komponente_p_001(self):
        #Scenar_43 Smazání objektu u projektové akce (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_043_smazani_objektu_komponente_p_001.start")
        self.login()

        count_old=NalezObjekt.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-91277520A-D01").count()
        self.ElementClick(By.CSS_SELECTOR, ".app-entity-akce > .card-body")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneAkce.vybrat"))

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-91277520A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-91277520A")
        self.ElementClick(By.ID, "el_komponenta_X_C_91277520A_K001")
        self.ElementClick(By.CSS_SELECTOR, "#objekt-smazat-101441 > .material-icons")
        self.wait(self.wait_interval)
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")
       
        count_new=NalezObjekt.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-91277520A-D01").count()
        #self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, ".badge.badge-primary.badge-pill").text,'1')
        self.assertEqual(count_old , count_new+1)
        logger.info("AkceProjektoveAkce.test_043_smazani_objektu_komponente_p_001.end")
        
        
    def test_044_smazani_predmetu_komponente_p_001(self):
        #Scenar_44 Smazání předmětu u projektové akce (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_044_smazani_predmetu_komponente_p_001.start")
        self.login()

        count_old=NalezPredmet.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-91277520A-D01").count()

        self.ElementClick(By.CSS_SELECTOR, ".app-entity-akce > .card-body")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneAkce.vybrat"))
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-91277520A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-91277520A")
        self.ElementClick(By.ID, "el_komponenta_X_C_91277520A_K001")

        self.ElementClick(By.CSS_SELECTOR, "#objekt-smazat-161256 > .material-icons")
        self.wait(1)
        with Wait_for_page_load(self.driver):
          self.ElementClick(By.ID, "submit-btn")
       
        count_new=NalezPredmet.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-91277520A-D01").count()
        #self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, ".badge.badge-primary.badge-pill").text,'1')
        self.assertEqual(count_old , count_new+1)
        logger.info("AkceProjektoveAkce.test_044_smazani_predmetu_komponente_p_001.end")
        
    #C-202207641A    
    def test_079_pridani_dokumentu_projektove_akci_p_001(self):
        #Scenar_79 Přidání dokumentu (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_079_pridani_dokumentu_projektove_akci_p_001.start")
        self.login("archeolog")       
       
        count_old=DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="C-202207641A").count()
        self.go_to_Projekty_vyper()
        
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202207641")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202207641")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#others > .material-icons")
        self.ElementClick(By.LINK_TEXT, _("dokument.templates.dokument_table.pridatNovyDokument.label"))
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Absolon")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vzniku")
        self.driver.find_element(By.ID, "id_rok_vzniku").send_keys("2023")        
        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("Moravské zemské muzeum")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("Investorsk")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("di")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.ID, "id_popis")
        self.driver.find_element(By.ID, "id_popis").send_keys("test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("anonym")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")
       
        count_new =DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="C-202207641A").count()
        self.assertEqual(count_old+1, count_new)
        logger.info("AkceProjektoveAkce.test_079_pridani_dokumentu_projektove_akci_p_001.end")  
        
        
    def test_080_pridani_existujiciho_dokumentu_projektove_akci_p_001(self):
        #Scenar_80 Připojení existujícího dokumentu (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_080_pridani_existujiciho_dokumentu_projektove_akci_p_001.start")
        self.login("archeolog")       
       
        count_old=DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="C-202207641A").count()
        self.go_to_Projekty_vyper()
        
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202207641")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202207641")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#others > .material-icons")
        self.ElementClick(By.ID, "dokument-pripojit")
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("M-TX-194300151")
        self.wait(3)
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)

        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")
       
        count_new =DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="C-202207641A").count()
        self.assertEqual(count_old+1, count_new)
        logger.info("AkceProjektoveAkce.test_080_pridani_existujiciho_dokumentu_projektove_akci_p_001.end")  

        
    def test_081_pridani_existujiciho_dokumentu_z_projektu_projektove_akci_p_001(self):
        #Scenar_81 Připojení existujícího dokumentu z projektu (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_081_pridani_existujiciho_dokumentu_z_projektu_projektove_akci_p_001.start")

        self.login("archeolog")       
       
        count_old=DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="C-202401979B").count()
        self.go_to_Projekty_vyper()
        
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202401979")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202401979")
        self.ElementClick(By.CSS_SELECTOR, ".app-card-akce > .card-body")
        self.ElementClick(By.CSS_SELECTOR, "tr:nth-child(2) a")
        self.ElementClick(By.CSS_SELECTOR, "#others > .material-icons")
        self.ElementClick(By.ID, "dokument-pripojit-z-projektu")
        self.ElementClick(By.NAME, "dokument")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")        
       
        count_new =DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="C-202401979B").count()
        self.assertEqual(count_old+1, count_new)
        logger.info("AkceProjektoveAkce.test_081_pridani_existujiciho_dokumentu_z_projektu_projektove_akci_p_001.end")
    
    
    def test_084_pripojeni_externiho_zdroje_projektove_akci_p_001(self):
        #Scenar_84 Připojení externího zdroje k projektové akci (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_084_pripojeni_externiho_zdroje_projektove_akci_p_001.start")
        self.login("archeolog")       
       
        count_old=ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely="C-202301164A").count()
        self.go_to_Projekty_vyper()
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202301164")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202301164")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#eo-pripojit-do-az > .material-icons")
        self.ElementClick(By.ID, "select2-id_ez-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("X-BIB-1295324")        
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.wait(3)
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        
        self.ElementClick(By.CSS_SELECTOR, "#eo-pripojit-do-az > .material-icons")
        self.ElementClick(By.ID, "select2-id_ez-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("X-BIB-1295325")        
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.wait(3)
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")
       
        count_new =ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely="C-202301164A").count()
        self.assertEqual(count_old+2, count_new)
        logger.info("AkceProjektoveAkce.test_084_pripojeni_externiho_zdroje_projektove_akci_p_001.end")
        
              
    def test_086_vytvoreni_PIAN_projektove_akce_p_001(self):
        #Scenar_86 Vytvoření PIAN u projektové akce (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_086_vytvoreni_PIAN_projektove_akce_p_001.start")
        self.login("archeolog")       
        pian_old=DokumentacniJednotka.objects.filter(ident_cely='C-202401980A-D01')[0].pian
        self.assertEqual(pian_old, None)
        
        self.go_to_Projekty_vyper()
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202401980")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202401980")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401980A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_C-202401980A-D01 .btn-group:nth-child(1) .material-icons")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "show_menu_pian_new_id")
        self.draw_polygon()
        self.ElementClick(By.CSS_SELECTOR, ".filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "createPianSubmitButton")
       
        pian_new =DokumentacniJednotka.objects.filter(ident_cely='C-202401980A-D01')[0].pian

        self.assertNotEqual(pian_new, None)
        logger.info("AkceProjektoveAkce.test_086_vytvoreni_PIAN_projektove_akce_p_001.end")
        

    def test_087_editace_PIAN_projektove_akce_p_001(self):
        #Scenar_87 Editace PIAN u projektové akce (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_087_editace_PIAN_projektove_akce_p_001.start")
        self.login("archeolog")       
        pian_old=str(DokumentacniJednotka.objects.filter(ident_cely='C-202401981A-D01')[0].pian.geom)        

        self.go_to_Projekty_vyper()
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202401981")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202401981")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401981A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")
        
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "pian-upravit-N-1212-000000002")
        self.draw_polygon()
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "editPianButton")
       
        pian_new =str(DokumentacniJednotka.objects.filter(ident_cely='C-202401981A-D01')[0].pian.geom)

        self.assertNotEqual(pian_new, pian_old)
        logger.info("AkceProjektoveAkce.test_087_editace_PIAN_projektove_akce_p_001.end")
        
        
    def test_088_smazani_PIAN_projektove_akce_p_001(self):
        #Scenar_88 Smazání PIAN u projektové akce (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_088_smazani_PIAN_projektove_akce_p_001.start")
        self.login("archeolog")       
        pian =DokumentacniJednotka.objects.filter(ident_cely='C-202401981A-D01')[0].pian
        self.assertNotEqual(pian, None)      

        self.go_to_Projekty_vyper()
        
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202401981")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")

        self.ElementClick(By.LINK_TEXT, "C-202401981")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401981A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")
        self.ElementClick(By.ID, "pian-odpojit-N-1212-000000002")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn") 
 
        pian=DokumentacniJednotka.objects.filter(ident_cely='C-202401981A-D01')[0].pian
        self.assertEqual(pian, None)
        logger.info("AkceProjektoveAkce.test_088_smazani_PIAN_projektove_akce_p_001.end")
        
        
    def test_089_pripojeni_PIAN_projektove_akce_p_001(self):
        #Scenar_89 Připojení PIAN z mapy u projektové akce (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_089_pripojeni_PIAN_projektove_akce_p_001.start")
        self.login("archeolog")       
        pian_old=DokumentacniJednotka.objects.filter(ident_cely='C-202401980A-D01')[0].pian
        self.assertEqual(pian_old, None)
        
        self.go_to_Projekty_vyper()
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202401980")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202401980")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401980A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_C-202401980A-D01 .btn-group:nth-child(1) .material-icons")
        self.ElementClick(By.ID, "show_menu_pian_from_map_id")
        self.wait(0.5)
        self.driver.execute_script('''map.setView([50.357377039,  13.795522698],19)''')
        self.wait(2)  
        self.driver.execute_script('''Object.values(poi_pian._layers)[0].fire("click");''')     
        self.wait(0.5)
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "editDjSubmitButton")
       
        pian_new =DokumentacniJednotka.objects.filter(ident_cely='C-202401980A-D01')[0].pian

        self.assertNotEqual(pian_new, None)
        logger.info("AkceProjektoveAkce.test_089_pripojeni_PIAN_projektove_akce_p_001.end")
        
       # 90 C-202307816A 202007232A
    def test_090_odpojeni_PIAN_projektove_akce_p_001(self):    
        #Scenar_90 Odpojení potvrzeného PIAN u projektové akce (pozitivní scénář 1)        
        logger.info("AkceProjektoveAkce.test_090_odpojeni_PIAN_projektove_akce_p_001.start")
        self.login("archeolog") 
        pian =DokumentacniJednotka.objects.filter(ident_cely='C-202007232A-D01')[0].pian
        self.assertNotEqual(pian, None) 
        
        self.go_to_Projekty_vyper()
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202007232")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202007232")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202007232A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")
        self.ElementClick(By.ID, "pian-odpojit-P-1221-100589")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        
        pian=DokumentacniJednotka.objects.filter(ident_cely='C-202007232A-D01')[0].pian
        self.assertEqual(pian, None)
        logger.info("AkceProjektoveAkce.test_090_odpojeni_PIAN_projektove_akce_p_001.end")
        
      #C-202309724  
    def test_091_import_PIAN_projektove_akce_p_001(self):
        #Scenar_91 Import PIAN k projektové akci (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_091_import_PIAN_projektove_akce_p_001.start")
        self.login("archeolog")       
        pian=DokumentacniJednotka.objects.filter(ident_cely='C-202309724A-D01')[0].pian
        self.assertEqual(pian, None)
        
        
        self.go_to_Projekty_vyper()
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202309724")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202309724")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202309724A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_C-202309724A-D01 .btn-group:nth-child(1) .material-icons")
        self.ElementClick(By.CSS_SELECTOR, ".show > .dropdown-item:nth-child(2)")
        with open("arch_z/tests/resources/geom.csv", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        self.addFileToDropzone("#my-awesome-dropzone",'geom.csv',encoded_string)
        self.wait(1) 
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "createPianSubmitButton")
              
        pian =DokumentacniJednotka.objects.filter(ident_cely='C-202309724A-D01')[0].pian

        self.assertNotEqual(pian, None) 
        logger.info("AkceProjektoveAkce.test_091_import_PIAN_projektove_akce_p_001.end")
        
        #202005190A
    def test_092_editace_PIAN_projektove_akce_importem_p_001(self):
        #Scenar_92 Editace PIAN k projektové akci importem (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_092_editace_PIAN_projektove_akce_importem_p_001.start")
        self.login("archeolog")       
        pian_old=str(DokumentacniJednotka.objects.filter(ident_cely='C-202005190A-D01')[0].pian.geom)    
        self.go_to_Projekty_vyper()           
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202005190")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202005190")        
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202005190A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")  
        self.ElementClick(By.CSS_SELECTOR, ".show > .dropdown-item:nth-child(2)")        
        with open("arch_z/tests/resources/geom.csv", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        self.addFileToDropzone("#my-awesome-dropzone",'geom.csv',encoded_string)
        self.wait(1) 
        with Wait_for_page_load(self.driver):    
            self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "editPianButton") 
       
        pian_new =str(DokumentacniJednotka.objects.filter(ident_cely='C-202005190A-D01')[0].pian.geom)
        self.assertNotEqual(pian_new, pian_old)
        logger.info("AkceProjektoveAkce.test_092_editace_PIAN_projektove_akce_importem_p_001.end")
        
        
    def test_093_pripojeni_PIAN_projektove_akce_p_001(self):
        #Scenar_93 Připojení PIAN k projektové akci podle ID (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_093_pripojeni_PIAN_projektove_akce_p_001.start")
        self.login("archivar")       
        pian_old=DokumentacniJednotka.objects.filter(ident_cely='C-202401980A-D01')[0].pian
        self.assertEqual(pian_old, None)
        
        self.go_to_Projekty_vyper()
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202401980")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202401980")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401980A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_C-202401980A-D01 .btn-group:nth-child(1) .material-icons")
        self.ElementClick(By.ID, "pian-pripojit-")
        self.ElementClick(By.ID, "select2-id_C-202401980A-D01-pian-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("P-0134-00000")
        self.wait(0.5) 
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "editDjSubmitButton")
       
        pian_new =DokumentacniJednotka.objects.filter(ident_cely='C-202401980A-D01')[0].pian

        self.assertNotEqual(pian_new, None)
        logger.info("AkceProjektoveAkce.test_093_pripojeni_PIAN_projektove_akce_p_001.end")
     
    #C-201015104   
    def test_094_smazani_komponenty_projektove_akce_p_001(self):
        #Scenar_94 Smazání komponenty u projektové akce (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_094_smazani_komponenty_projektove_akce_p_001.start")
        self.login("archeolog")       
        count_old=Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="C-201015104A-D01").count()   
        self.go_to_Projekty_vyper()
        
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-201015104")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-201015104")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.ID, "el_komponenta_C_201015104A_K001")
        self.ElementClick(By.CSS_SELECTOR, "#detail_komponenta_form_C-201015104A-K001 #others > .material-icons")
        self.ElementClick(By.ID, "komponenta-smazat-C-201015104A-K001")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")

        count_new=Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="C-201015104A-D01").count()
        self.assertEqual(count_old-1 , count_new)
        logger.info("AkceProjektoveAkce.test_094_smazani_komponenty_projektove_akce_p_001.end")  
        
        
    #C-202401980 
    def test_095_smazani_DJ_projektove_akce_p_001(self):
        #Scenar_95 Smazání dokumentační jednotky u projektové akce (pozitivní scénář 1)
        logger.info("AkceProjektoveAkce.test_095_smazani_DJ_projektove_akce_p_001.start")
        self.login("archeolog")       
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202401980A").count()   
        self.go_to_Projekty_vyper()
        
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202401980")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "C-202401980")
        self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401980A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")
        self.ElementClick(By.ID, "dj-smazat-C-202401980A-D01")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")


        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202401980A").count()
        self.assertEqual(count_old-1 , count_new)
        logger.info("AkceProjektoveAkce.test_095_smazani_DJ_projektove_akce_p_001.end")   

@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkceSamostatneAkce(AkceProjektoveAkce): 
    def go_to_Akce_zapsat(self):
        self.ElementClick(By.CSS_SELECTOR, ".app-entity-akce > .card-body")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneAkce.zapsat")) 
    
    def go_to_Akce_vybrat(self):
        self.ElementClick(By.CSS_SELECTOR, ".app-entity-akce > .card-body")
        self.ElementClick(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneAkce.vybrat"))
        
        
    def test_046_vytvoreni_samostatne_akce_p_001(self):
        #Scenar_46 Vytvoření samostané akce (pozitivní scénář 1)
        logger.info("AkceSamostatneAkce.test_046_vytvoreni_samostatne_akce_p_001.start")
        self.login("badatel")
       
        arch_z_count_old = Akce.objects.count()
        
        self.go_to_Akce_zapsat()
        self.ElementClick(By.ID, "select2-id_hlavni_katastr-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys("Velká Do")
        self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "select2-id_hlavni_vedouci-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys("Švejcar")
        self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("archeologický")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-29 > .text")
       
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("sonda")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-22 > .text")
     
        self.ElementClick(By.ID, "id_datum_zahajeni")
        self.driver.find_element(By.ID, "id_datum_zahajeni").send_keys("07.03.2024")
        self.ElementClick(By.ID, "id_datum_ukonceni")
        self.driver.find_element(By.ID, "id_datum_ukonceni").send_keys("07.03.2024")
        self.ElementClick(By.ID, "id_lokalizace_okolnosti")
        self.driver.find_element(By.ID, "id_lokalizace_okolnosti").send_keys("Hora")
        with Wait_for_page_load(self.driver):
          self.ElementClick(By.ID, "actionSubmitBtn")       
       
        arch_z_count_new = Akce.objects.count()
        self.assertEqual(arch_z_count_old + 1, arch_z_count_new)
        logger.info("AkceSamostatneAkce.test_046_vytvoreni_samostatne_akce_p_001.end")
        
        
    def test_047_vytvoreni_samostatne_akce_n_001(self):
        #Scenar_47 Vytvoření samostatné akce (negativní scénář 1)
        logger.info("AkceSamostatneAkce.test_047_vytvoreni_samostatne_akce_n_001.start")
        self.login("badatel")
       
        arch_z_count_old = Akce.objects.count()
        
        self.go_to_Akce_zapsat()
        #self.ElementClick(By.ID, "select2-id_hlavni_katastr-container")
        #self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys("Velká Do")
        #self.wait(self.wait_interval)
        #self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "select2-id_hlavni_vedouci-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys("Švejcar")
        self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("archeologický")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-29 > .text")
       
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("sonda")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-2-22 > .text")
     
        self.ElementClick(By.ID, "id_datum_zahajeni")
        self.driver.find_element(By.ID, "id_datum_zahajeni").send_keys("07.03.2024")
        self.ElementClick(By.ID, "id_datum_ukonceni")
        self.driver.find_element(By.ID, "id_datum_ukonceni").send_keys("07.03.2024")
        self.ElementClick(By.ID, "id_lokalizace_okolnosti")
        self.driver.find_element(By.ID, "id_lokalizace_okolnosti").send_keys("Hora")
        try:
            with Wait_for_page_load(self.driver):
                self.ElementClick(By.ID, "actionSubmitBtn")       
        except Exception as e:
            pass
        arch_z_count_new = Akce.objects.count()
        self.assertEqual(arch_z_count_old, arch_z_count_new)
        logger.info("AkceSamostatneAkce.test_047_vytvoreni_samostatne_akce_n_001.end")
        

    def test_048_pridani_dokumentacni_jednotky_samostatne_akce_p_001(self):
        #Scenar_48 Přidání dokumentační jednotky celek akce (pozitivní scénář 1) 
        logger.info("AkceSamostatneAkce.test_048_pridani_dokumentacni_jednotky_samostatne_akce_p_001.start")
        self.login("badatel")       
        
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.go_to_Akce_vybrat()
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000001A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11) > .material-icons")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000001A")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "newDjSubmitButton")
            
        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceSamostatneAkce.test_048_pridani_dokumentacni_jednotky_samostatne_akce_p_001.end")
   
   
    def test_049_pridani_dokumentacni_jednotky_samostatne_akce_n_001(self):
        #Scenar_49 Přidání dokumentační jednotky “Celek akce” (negativní scénář 1) 
        logger.info("AkceSamostatneAkce.test_049_pridani_dokumentacni_jednotky_samostatne_akce_n_001.start")
        self.login("badatel")       
        
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.go_to_Akce_vybrat()
        self.ElementClick(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000001A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11) > .material-icons")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000001A")
        self.ElementClick(By.CSS_SELECTOR, "#button-add-dj > .material-icons")
        
        #self.ElementClick(By.CSS_SELECTOR, ".bs-placeholder")
        #self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        try:
            with Wait_for_page_load(self.driver):
                self.ElementClick(By.ID, "newDjSubmitButton")
        except Exception as e:
            pass
        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.assertEqual(count_old, count_new)
        logger.info("AkceSamostatneAkce.test_049_pridani_dokumentacni_jednotky_samostatne_akce_n_001.end")
   
   
    def test_050_pridani_komponenty_DJ_samostatne_akce_p_001(self):
        #Scenar_50 Přidání komponenty k DJ u samostatné akce (pozitivní scénář 1) 
        logger.info("AkceSamostatneAkce.test_050_pridani_komponenty_DJ_samostatne_akce_p_001.start")
        self.login("badatel")
       
        count_old=Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000002A-D01").count()
        #count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.go_to_Akce_vybrat()

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000002A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000002A")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_9000000002A_D01 > strong")
        #self.driver.execute_script("window.scrollTo(0,0)")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_X-C-9000000002A-D01 .btn-group:nth-child(1) .material-icons")
        self.ElementClick(By.LINK_TEXT, _("arch_z.templates.arch_z.dj.partials.dj_update.editButtons.pridatKomponentu.label"))
        self.ElementClick(By.CSS_SELECTOR, "#div_id_obdobi .btn")
        self.ElementClick(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control")
        #self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.DOWN)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("únětická kultura")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("poh")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        #self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-39 > .text")

        #self.driver.execute_script("window.scrollTo(0,0)")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "createCompotSubmitButton")
       
        count_new =Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000002A-D01").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkceSamostatneAkce.test_050_pridani_komponenty_DJ_samostatne_akce_p_001.end")
    
    
    def test_074_pridani_komponenty_DJ_samostatne_akce_n_001(self):
        #Scenar_74 Přidání komponenty k DJ u samostatné akce (negativní scénář 1) 
        logger.info("AkceSamostatneAkce.test_074_pridani_komponenty_DJ_samostatne_akce_n_001.start")
        self.login("badatel")
       
        count_old=Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000002A-D01").count()
        #count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.go_to_Akce_vybrat()

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000002A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000002A")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_9000000002A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_X-C-9000000002A-D01 .btn-group:nth-child(1) .material-icons")
        self.ElementClick(By.LINK_TEXT, _("arch_z.templates.arch_z.dj.partials.dj_update.editButtons.pridatKomponentu.label"))
        self.ElementClick(By.CSS_SELECTOR, "#div_id_obdobi .btn")
        self.ElementClick(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control")
        #self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.DOWN)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("únětická kultura")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        #self.ElementClick(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner")
        #self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("poh")
        #self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        #self.ElementClick(By.CSS_SELECTOR, "#bs-select-3-39 > .text")


        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "createCompotSubmitButton")
       
        count_new =Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000002A-D01").count()
        self.assertEqual(count_old, count_new)
        logger.info("AkceSamostatneAkce.test_074_pridani_komponenty_DJ_samostatne_akce_n_001.end")    

        
    def test_075_pridani_objektu_komponente_DJ_samostatna_akce_p_001(self):
        #Scenar_75 Přidání objektu k pozitivní komponentě (pozitivní scénář 1)
        logger.info("AkceSamostatneAkce.test_075_pridani_objektu_komponente_DJ_samostatna_akce_p_001.start")
        self.login("badatel")       
       
        count_old=NalezObjekt.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000003A-D01").count()
        
        self.go_to_Akce_vybrat()

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000003A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000003A")
        self.ElementClick(By.ID, "el_komponenta_X_C_9000000003A_K001")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-9000000003A-K001_o-0-druh .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("polo")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_X-C-9000000003A-K001_o-0-pocet")
        self.driver.find_element(By.ID, "id_X-C-9000000003A-K001_o-0-pocet").send_keys("1")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")       
       
        count_new =NalezObjekt.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000003A-D01").count()
        self.assertEqual(count_old+1, count_new)
        logger.info("AkceSamostatneAkce.test_075_pridani_objektu_komponente_DJ_samostatna_akce_p_001.end") 
        
        
    def test_076_pridani_predmetu_komponente_DJ_samostatna_akce_p_001(self):
        #Scenar_76 Přidání předmětu k pozitivní komponentě (pozitivní scénář 1)
        logger.info("AkceSamostatneAkce.test_076_pridani_predmetu_komponente_DJ_samostatna_akce_p_001.start")
        self.login("badatel")       
       
        count_old=NalezPredmet.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000003A-D01").count()
        
        self.go_to_Akce_vybrat()

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000003A")
        
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000003A")
        self.ElementClick(By.ID, "el_komponenta_X_C_9000000003A_K001")
        self.ElementClick(By.CSS_SELECTOR, "#div_id_X-C-9000000003A-K001_p-0-druh .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("dž")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        
        self.ElementClick(By.CSS_SELECTOR, ".dropup .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("keramika")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.ID, "id_X-C-9000000003A-K001_p-0-pocet")
        self.driver.find_element(By.ID, "id_X-C-9000000003A-K001_p-0-pocet").send_keys("1")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
       
        count_new =NalezPredmet.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000003A-D01").count()
        self.assertEqual(count_old+1, count_new)
        logger.info("AkceSamostatneAkce.test_076_pridani_predmetu_komponente_DJ_samostatna_akce_p_001.end")    
   
   
    def test_077_smazani_objektu_komponenty_DJ_samostatna_akce_p_001(self):
        #Scenar_77 Smazání objektu u samostatné akce (pozitivní scénář 1)
        logger.info("AkceSamostatneAkce.test_077_smazani_objektu_komponenty_DJ_samostatna_akce_p_001.start")
        self.login("badatel")       
       
        count_old=NalezObjekt.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000004A-D01").count()
        
        self.go_to_Akce_vybrat()

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000004A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000004A")
        self.ElementClick(By.ID, "el_komponenta_X_C_9000000004A_K001")
        self.ElementClick(By.CSS_SELECTOR, "#objekt-smazat-180491 > .material-icons")
        self.ElementClick(By.ID, "submit-btn")
        
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
       
        count_new =NalezObjekt.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000004A-D01").count()
        self.assertEqual(count_old, count_new+1)
        logger.info("AkceSamostatneAkce.test_077_smazani_objektu_komponenty_DJ_samostatna_akce_p_001.end")  
        

    def test_078_smazani_predmetu_komponenty_DJ_samostatna_akce_p_001(self):
        #Scenar_78 Smazání předmětu u samostatné akce (pozitivní scénář 1)
        logger.info("AkceSamostatneAkce.test_078_smazani_predmetu_komponenty_DJ_samostatna_akce_p_001.start")
        self.login("badatel")       
       
        count_old=NalezPredmet.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000004A-D01").count()
        
        self.go_to_Akce_vybrat()

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000004A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000004A")
        self.ElementClick(By.ID, "el_komponenta_X_C_9000000004A_K001")
        self.ElementClick(By.CSS_SELECTOR, "#objekt-smazat-175762 > .material-icons")
        self.ElementClick(By.ID, "submit-btn")
        
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "editKompSubmitButton")
       
        count_new =NalezPredmet.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000004A-D01").count()
        self.assertEqual(count_old, count_new+1)
        logger.info("AkceSamostatneAkce.test_078_smazani_predmetu_komponenty_DJ_samostatna_akce_p_001.end")  
        
    
      
#82 a 83 X-C-9000000003A

    def test_082_pridani_dokumentu_samostatne_akci_p_001(self):
        #Scenar_82 Přidání dokumentu k samostatné akci (pozitivní scénář 1)
        logger.info("AkceSamostatneAkce.test_082_pridani_dokumentu_samostatne_akci_p_001.start")
        self.login("badatel")       
       
        count_old=DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000003A").count()
        self.go_to_Akce_vybrat()

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000003A")
        
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000003A")
    
        #self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        self.ElementClick(By.CSS_SELECTOR, "#others > .material-icons")
        self.ElementClick(By.LINK_TEXT, _("dokument.templates.dokument_table.pridatNovyDokument.label"))
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("Absolon")
        self.wait(1)
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.ElementClick(By.ID, "id_rok_vzniku")
        self.driver.find_element(By.ID, "id_rok_vzniku").send_keys("2023")        
        self.ElementClick(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("Moravské zemské muzeum")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_typ_dokumentu .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("Investorsk")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.CSS_SELECTOR, "#div_id_material_originalu .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("di")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.ElementClick(By.ID, "id_popis")
        self.driver.find_element(By.ID, "id_popis").send_keys("test")
        self.ElementClick(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("anonym")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "newDocumentSubmitBtn")

       
        count_new =DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000003A").count()
        self.assertEqual(count_old+1, count_new)
        logger.info("AkceSamostatneAkce.test_082_pridani_dokumentu_samostatne_akci_p_001.end")
        
        
    def test_083_pridani_existujiciho_dokumentu_samostatne_akci_p_001(self):
        #Scenar_83 Připojení existujícího dokumentu k samostatné akci (pozitivní scénář 1)
        logger.info("AkceSamostatneAkce.test_083_pridani_existujiciho_dokumentu_samostatne_akci_p_001.start")
        self.login("badatel")       
       
        count_old=DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000004A").count()
        self.go_to_Akce_vybrat()

        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000004A")
        
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000004A")
    

        self.ElementClick(By.CSS_SELECTOR, "#others > .material-icons")
        self.driver.execute_script('$("#app-wrapper").scrollTop($("#app-wrapper")[0].scrollHeight);')
        self.ElementClick(By.ID, "dokument-pripojit")
       
        self.ElementClick(By.CSS_SELECTOR, ".select2-selection__rendered")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("X-C-TX-000000003")
        self.wait(3)
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)

        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")
       
        count_new =DokumentCast.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000004A").count()
        self.assertEqual(count_old+1, count_new)
        logger.info("AkceSamostatneAkce.test_083_pridani_existujiciho_dokumentu_samostatne_akci_p_001.end")
                
                
        #X-C-9000000003A         
    def test_085_pripojeni_externiho_zdroje_samostatne_akci_p_001(self):
        #Scenar_85 Připojení externího zdroje k samostatné akci (pozitivní scénář 1)
        logger.info("AkceSamostatneAkce.test_085_pripojeni_externiho_zdroje_samostatne_akci_p_001.start")
        self.login("badatel")       
       
        count_old=ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000003A").count()
        self.go_to_Akce_vybrat()
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000003A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000003A")
        self.ElementClick(By.CSS_SELECTOR, "#eo-pripojit-do-az > .material-icons")
        self.ElementClick(By.ID, "select2-id_ez-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("X-BIB-1295324")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.wait(3)
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")
        self.ElementClick(By.CSS_SELECTOR, "#eo-pripojit-do-az > .material-icons")
        self.ElementClick(By.ID, "select2-id_ez-container")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("X-BIB-1295325")
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys(Keys.ENTER)
        self.wait(3)
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "submit-btn")
       
        count_new =ExterniOdkaz.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000003A").count()
        self.assertEqual(count_old+2, count_new)
        logger.info("AkceSamostatneAkce.test_085_pripojeni_externiho_zdroje_samostatne_akci_p_001.end")
    
           
    def test_096_vytvoreni_PIAN_samostatne_akce_p_001(self):
        #Scenar_96 Vytvoření PIAN u samostatné akce (pozitivní scénář 1)
        logger.info("AkceSamostatneAkce.test_096_vytvoreni_PIAN_samostatne_akce_p_001.start")
        self.login("badatel")       
        pian_old=DokumentacniJednotka.objects.filter(ident_cely='X-C-9000000002A-D01')[0].pian
        self.assertEqual(pian_old, None)

        self.go_to_Akce_vybrat()
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000002A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000002A")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_9000000002A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, "#detail_dj_form_X-C-9000000002A-D01 .btn-group:nth-child(1) .material-icons")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "show_menu_pian_new_id")
        self.draw_polygon()

        self.ElementClick(By.CSS_SELECTOR, ".filter-option-inner-inner")
        self.ElementClick(By.CSS_SELECTOR, "#bs-select-1-1 > .text")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "createPianSubmitButton")
       
        pian_new =DokumentacniJednotka.objects.filter(ident_cely='X-C-9000000002A-D01')[0].pian

        self.assertNotEqual(pian_new, None)
        logger.info("AkceSamostatneAkce.test_096_vytvoreni_PIAN_samostatne_akce_p_001.end")


    def test_097_editace_PIAN_samostatne_akce_p_001(self):
        #Scenar_97 Editace PIAN u samostatné akce (pozitivní scénář 1)
        logger.info("AkceSamostatneAkce.test_097_editace_PIAN_samostatne_akce_p_001.start")
        self.login("badatel")       
        pian_old=str(DokumentacniJednotka.objects.filter(ident_cely='X-C-9000000006A-D01')[0].pian.geom)        

        self.go_to_Akce_vybrat()
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")      
        
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000006A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000006A")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_9000000006A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")
        
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "pian-upravit-N-1212-000000001")
        self.draw_polygon()
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "editPianButton")
       
        pian_new =str(DokumentacniJednotka.objects.filter(ident_cely='X-C-9000000006A-D01')[0].pian.geom)

        self.assertNotEqual(pian_new, pian_old)
        logger.info("AkceSamostatneAkce.test_097_editace_PIAN_samostatne_akce_p_001.end")
        
    def test_098_editace_PIAN_samostatne_akce_importem_p_001(self):
        #Scenar_98 Editace PIAN k samostatné akci importem (pozitivní scénář 1)
        logger.info("AkceSamostatneAkce.test_098_editace_PIAN_samostatne_akce_importem_p_001.start")
        self.login("badatel")       
        pian_old=str(DokumentacniJednotka.objects.filter(ident_cely='X-C-9000000006A-D01')[0].pian.geom)        

        self.go_to_Akce_vybrat()
        self.ElementClick(By.CSS_SELECTOR, ".mt-1")
        self.ElementClick(By.ID, "id_ident_cely")     
        
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000006A")
        self.ElementClick(By.CSS_SELECTOR, ".btn:nth-child(11)")
        self.ElementClick(By.LINK_TEXT, "X-C-9000000006A")
        self.ElementClick(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_9000000006A_D01 > strong")
        self.ElementClick(By.CSS_SELECTOR, ".btn-group:nth-child(2) .material-icons")       

        self.ElementClick(By.CSS_SELECTOR, ".show > .dropdown-item:nth-child(2)")
        
        with open("arch_z/tests/resources/geom.csv", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()

        self.addFileToDropzone("#my-awesome-dropzone",'geom.csv',encoded_string)
        self.wait(1) 
        with Wait_for_page_load(self.driver):    
            self.ElementClick(By.CSS_SELECTOR, ".app-ident-cely > a")
        with Wait_for_page_load(self.driver):
            self.ElementClick(By.ID, "editPianButton") 
       
        pian_new =str(DokumentacniJednotka.objects.filter(ident_cely='X-C-9000000006A-D01')[0].pian.geom)

        self.assertNotEqual(pian_new, pian_old)
        logger.info("AkceSamostatneAkce.test_098_editace_PIAN_samostatne_akce_importem_p_001.end")
        