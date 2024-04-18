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

from core.tests.test_selenium import BaseSeleniumTestClass, Wait_for_page_load
from arch_z.models import Akce
from dj.models import DokumentacniJednotka
from komponenta.models import Komponenta
from nalez.models import NalezObjekt, NalezPredmet
from django.utils.translation import gettext as _
from selenium.common.exceptions import *
logger = logging.getLogger("tests")


@unittest.skipIf(settings.SKIP_SELENIUM_TESTS, "Skipping Selenium tests")
class AkcePridaniDokumentacniJednotky(BaseSeleniumTestClass):   
    def go_to_form(self):
        self.driver.find_element(By.CSS_SELECTOR, ".card:nth-child(1) .btn").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.projekty.vybratProjekty")).click() 

    
    def test_pridani_dokumentacni_jednotky_p_001(self):
        #Scenar_24 Přidání dokumentační jednotky celek akce (pozitivní scénář 1)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_dokumentacni_jednotky_p_001.start")
        self.test_number=24

        self.login()
        self.go_to_form()
        #ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202401502A").count()
        #arch_z_count_old = Akce.objects.count()
        self.driver.find_element(By.CSS_SELECTOR, ".btn > .mr-1").click()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_stav .filter-option-inner-inner").click()
        self.driver.find_element(By.XPATH, "//span[contains(.,\'"+_("projekt.models.projekt.states.zahajenVTerenu.label")+"\')]").click()
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "C-202401502").click()   
             
        self.driver.find_element(By.CSS_SELECTOR, ".app-ident-cely > a").click()
        self.driver.find_element(By.CSS_SELECTOR, "#button-add-dj > .material-icons").click()
        self.driver.find_element(By.CSS_SELECTOR, ".bs-placeholder").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-1-1 > .text").click()

        self.driver.find_element(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-2-1 > .text").click()
       
        self.driver.find_element(By.ID, "newDjSubmitButton").click()        
        
        self.assertNotEqual(self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401502A_D01 > strong"), None)
        count_new=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202401502A").count()

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_dokumentacni_jednotky_p_001.end")
        
        
    def test_pridani_dokumentacni_jednotky_n_001(self):
        #Scenar_34 Přidání dokumentační jednotky celek akce (negativní scénář 1)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_dokumentacni_jednotky_n_001.start")
        self.test_number=34
        self.login()
        self.go_to_form()
        #ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202401502A").count()
        
        self.driver.find_element(By.CSS_SELECTOR, ".btn > .mr-1").click()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_stav .filter-option-inner-inner").click()
        self.driver.find_element(By.XPATH, "//span[contains(.,\'"+_("projekt.models.projekt.states.zahajenVTerenu.label")+"\')]").click()
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "C-202401502").click()   
             
        self.driver.find_element(By.CSS_SELECTOR, ".app-ident-cely > a").click()
        self.driver.find_element(By.CSS_SELECTOR, "#button-add-dj > .material-icons").click()
        #self.driver.find_element(By.CSS_SELECTOR, ".bs-placeholder").click()
        #self.driver.find_element(By.CSS_SELECTOR, "#bs-select-1-1 > .text").click()

        self.driver.find_element(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-2-1 > .text").click()
       
        try:
            with Wait_for_page_load(self.driver):
                self.driver.find_element(By.ID, "newDjSubmitButton").click()       
        except Exception as e:
            pass       
        
        #self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202401502A_D01 > strong"), None)
        count_new=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202401502A").count()

        self.assertEqual(count_old , count_new)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_dokumentacni_jednotky_n_001.end")
        
        
    def test_pridani_dokumentacni_jednotky_p_002(self):
        #Scenar_35 Přidání dokumentační jednotky část akce (pozitivní scénář 1)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_dokumentacni_jednotky_p_002.start")
        self.test_number=35
        self.login()
        self.go_to_form()
        #ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()
        
        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202309552")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        
        self.driver.find_element(By.LINK_TEXT, "C-202309552").click()

        self.driver.find_element(By.CSS_SELECTOR, ".app-ident-cely > a").click()  
        self.driver.find_element(By.CSS_SELECTOR, "#button-add-dj > .material-icons").click()
        self.driver.find_element(By.CSS_SELECTOR, ".bs-placeholder").click()        
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-1-1 > .text").click()       
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner").click()       
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-2-1 > .text").click()       
        self.driver.find_element(By.ID, "newDjSubmitButton").click()  
          
        self.assertNotEqual(self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202309552A_D02 > strong"), None)
        count_new=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()

        self.assertEqual(count_old + 1, count_new)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_dokumentacni_jednotky_p_002.end")
        
        
    def test_pridani_dokumentacni_jednotky_n_002(self):
        #Scenar_36 Přidání dokumentační jednotky část akce (negativní scénář 1)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_dokumentacni_jednotky_n_002.start")
        self.test_number=36
        self.login()
        self.go_to_form()
        #ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()
        
        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202309552")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        
        self.driver.find_element(By.LINK_TEXT, "C-202309552").click()

        self.driver.find_element(By.CSS_SELECTOR, ".app-ident-cely > a").click()  
        self.driver.find_element(By.CSS_SELECTOR, "#button-add-dj > .material-icons").click()
        #self.driver.find_element(By.CSS_SELECTOR, ".bs-placeholder").click()        
        #self.driver.find_element(By.CSS_SELECTOR, "#bs-select-1-1 > .text").click()       
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_negativni_jednotka .filter-option-inner-inner").click()       
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-2-1 > .text").click()       
 
        try:
            with Wait_for_page_load(self.driver):
                self.driver.find_element(By.ID, "newDjSubmitButton").click()       
        except Exception as e:
            pass
          
        #self.assertNotEqual(self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202309552A_D02 > strong"), None)
        count_new=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()

        self.assertEqual(count_old , count_new)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_dokumentacni_jednotky_n_002.end")


    def test_pridani_komponenty_dokumentacni_jednotky_p_001(self):
        #Scenar_37 Přidání komponenty k dokumentační jednotce celek akce (pozitivní scénář 1)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_komponenty_dokumentacni_jednotky_p_001.start")
        self.test_number=37
        self.login()
        self.go_to_form() #C-202309027
        #ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        #count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()
        count_old=Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202309027A-D01").count()

        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202309027")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "C-202309027").click()
        self.driver.find_element(By.CSS_SELECTOR, ".app-ident-cely > a").click()
        self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202309027A_D01 > strong").click()
        self.driver.find_element(By.CSS_SELECTOR, "#detail_dj_form_C-202309027A-D01 .btn-group:nth-child(1) .material-icons").click()
        self.driver.find_element(By.LINK_TEXT, _("arch_z.templates.arch_z.dj.partials.dj_update.editButtons.pridatKomponentu.label")).click()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_obdobi .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-1-73 > .text").click()

        self.driver.find_element(By.CSS_SELECTOR, "#div_id_jistota .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").click()
        self.driver.find_element(By.ID, "hint_id_presna_datace").click()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-3-3 > .text").click()
        
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "createCompotSubmitButton").click()  
                      
        self.assertNotEqual(self.driver.find_element(By.ID, "el_komponenta_C_202309027A_K001"), None)
        count_new=Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202309027A-D01").count()

        self.assertEqual(count_old+1 , count_new)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_komponenty_dokumentacni_jednotky_p_001.end")


    def test_pridani_komponenty_dokumentacni_jednotky_n_001(self):
        #Scenar_40 Přidání komponenty k dokumentační jednotce celek akce (negativní scénář 1)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_komponenty_dokumentacni_jednotky_n_001.start")
        self.test_number=40
        self.login()
        self.go_to_form() #C-202309027
        #ArcheologickyZaznam.filter(ident_cely="C-202401502A")
        #count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="C-202309552A").count()
        count_old=Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202309027A-D01").count()

        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202309027")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "C-202309027").click()
        self.driver.find_element(By.CSS_SELECTOR, ".app-ident-cely > a").click()
        self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_C_202309027A_D01 > strong").click()
        self.driver.find_element(By.CSS_SELECTOR, "#detail_dj_form_C-202309027A-D01 .btn-group:nth-child(1) .material-icons").click()
        self.driver.find_element(By.LINK_TEXT, _("arch_z.templates.arch_z.dj.partials.dj_update.editButtons.pridatKomponentu.label")).click()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_obdobi .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-1-73 > .text").click()

        self.driver.find_element(By.CSS_SELECTOR, "#div_id_jistota .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").click()
        self.driver.find_element(By.ID, "hint_id_presna_datace").click()
        #self.driver.find_element(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner").click()
        #self.driver.find_element(By.CSS_SELECTOR, "#bs-select-3-3 > .text").click()
        
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "createCompotSubmitButton").click()    
          
        #self.assertNotEqual(self.driver.find_element(By.ID, "el_komponenta_C_202309027A_K001"), None)
        self.assertEqual(len(self.driver.find_elements(By.ID, "el_komponenta_C_202309027A_K001")),0)
        count_new=Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202309027A-D01").count()

        self.assertEqual(count_old , count_new)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_komponenty_dokumentacni_jednotky_n_001.end")


    def test_pridani_objektu_komponente_p_001(self):
        #Scenar_41 Přidání objektu k pozitivní komponentě (pozitivní scénář 1)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_objektu_komponente_p_001.start")
        self.test_number=41
        self.login()
        self.go_to_form() #C-202309027
        count_old=NalezObjekt.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202004814A-D01").count()

        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202004814")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "C-202004814").click()
        self.driver.find_element(By.CSS_SELECTOR, ".app-ident-cely > a").click()
        self.driver.find_element(By.ID, "el_komponenta_C_202004814A_K001").click()
        #with Wait_for_page_load(self.driver):
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_C-202004814A-K001_o-0-druh .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-7-6 > .text").click()
        self.driver.find_element(By.ID, "id_C-202004814A-K001_o-0-pocet").click()
        self.driver.find_element(By.ID, "id_C-202004814A-K001_o-0-pocet").send_keys("1")
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "editKompSubmitButton").click() 

        count_new=NalezObjekt.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202004814A-D01").count()
        self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, ".badge.badge-primary.badge-pill").text,'1')
        self.assertEqual(count_old+1 , count_new)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_objektu_komponente_p_001.end")
        
        
    def test_pridani_predmetu_komponente_p_001(self):
        #Scenar_42 Přidání předmětu k pozitivní komponentě (pozitivní scénář 1)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_predmetu_komponente_p_001.start")
        self.test_number=42
        self.login()
        self.go_to_form() #C-202309027

        count_old=NalezPredmet.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202004814A-D01").count()

        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("C-202004814")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "C-202004814").click()
        self.driver.find_element(By.CSS_SELECTOR, ".app-ident-cely > a").click()
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "el_komponenta_C_202004814A_K001").click()
       
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_C-202004814A-K001_p-0-druh .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-11-82 > .text").click()

        self.driver.find_element(By.CSS_SELECTOR, "#div_id_C-202004814A-K001_p-0-specifikace .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-12-15 > .text").click()

        self.driver.find_element(By.ID, "id_C-202004814A-K001_p-0-pocet").click()
        self.driver.find_element(By.ID, "id_C-202004814A-K001_p-0-pocet").send_keys("1")
        
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "editKompSubmitButton").click() 

        count_new=NalezPredmet.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="C-202004814A-D01").count()
        self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, ".badge.badge-primary.badge-pill").text,'1')
        self.assertEqual(count_old+1 , count_new)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_predmetu_komponente_p_001.end")


    def test_smazani_objektu_komponente_p_001(self):
        #Scenar_43 Smazání objektu k pozitivní komponentě (pozitivní scénář 1)
        logger.info("AkcePridaniDokumentacniJednotky.test_smazani_objektu_komponente_p_001.start")
        self.test_number=43
        self.login()
        #self.go_to_form() X-C-91277520A
        count_old=NalezObjekt.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-91277520A-D01").count()

        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-akce > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneAkce.vybrat")).click()
        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-91277520A")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "X-C-91277520A").click()
        self.driver.find_element(By.ID, "el_komponenta_X_C_91277520A_K001").click()
        self.driver.find_element(By.CSS_SELECTOR, "#objekt-smazat-101441 > .material-icons").click()
        self.wait(self.wait_interval)
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "submit-btn").click()
       
        count_new=NalezObjekt.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-91277520A-D01").count()
        #self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, ".badge.badge-primary.badge-pill").text,'1')
        self.assertEqual(count_old , count_new+1)
        logger.info("AkcePridaniDokumentacniJednotky.test_smazani_objektu_komponente_p_001.end")
        
        
    def test_smazani_predmetu_komponente_p_001(self):
        #Scenar_44 Smazání předmětu k pozitivní komponentě (pozitivní scénář 1)
        logger.info("AkcePridaniDokumentacniJednotky.test_smazani_predmetu_komponente_p_001.start")
        self.test_number=44
        self.login()
        #self.go_to_form() X-C-91277520A
        count_old=NalezPredmet.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-91277520A-D01").count()

        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-akce > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneAkce.vybrat")).click()
        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-91277520A")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "X-C-91277520A").click()
        self.driver.find_element(By.ID, "el_komponenta_X_C_91277520A_K001").click()

        self.driver.find_element(By.CSS_SELECTOR, "#objekt-smazat-161256 > .material-icons").click()
        self.wait(1)
        with Wait_for_page_load(self.driver):
          self.driver.find_element(By.ID, "submit-btn").click()
       
        count_new=NalezPredmet.objects.filter(komponenta__komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-91277520A-D01").count()
        #self.assertEqual(self.driver.find_element(By.CSS_SELECTOR, ".badge.badge-primary.badge-pill").text,'1')
        self.assertEqual(count_old , count_new+1)
        logger.info("AkcePridaniDokumentacniJednotky.test_smazani_predmetu_komponente_p_001.end")
        
        
    def test_vytvoreni_samostatne_akce_p_001(self):
        #Scenar_46 Vytvoření samostané akce (pozitivní scénář 1)
        logger.info("AkcePridaniDokumentacniJednotky.test_vytvoreni_samostatne_akce_p_001.start")
        self.test_number=46
        self.login("badatel")
       
        arch_z_count_old = Akce.objects.count()
        
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-akce > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneAkce.zapsat")).click()
        self.driver.find_element(By.ID, "select2-id_hlavni_katastr-container").click()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys("Velká Do")
        self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "select2-id_hlavni_vedouci-container").click()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys("Švejcar")
        self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(Keys.ENTER)
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("archeologický")
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-1-29 > .text").click()
       
        self.driver.find_element(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("sonda")
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-2-22 > .text").click()
     
        self.driver.find_element(By.ID, "id_datum_zahajeni").click()
        self.driver.find_element(By.ID, "id_datum_zahajeni").send_keys("07.03.2024")
        self.driver.find_element(By.ID, "id_datum_ukonceni").click()
        self.driver.find_element(By.ID, "id_datum_ukonceni").send_keys("07.03.2024")
        self.driver.find_element(By.ID, "id_lokalizace_okolnosti").click()
        self.driver.find_element(By.ID, "id_lokalizace_okolnosti").send_keys("Hora")
        with Wait_for_page_load(self.driver):
          self.driver.find_element(By.ID, "actionSubmitBtn").click()       
       
        arch_z_count_new = Akce.objects.count()
        self.assertEqual(arch_z_count_old + 1, arch_z_count_new)
        logger.info("AkcePridaniDokumentacniJednotky.test_vytvoreni_samostatne_akce_p_001.end")
        
        
    def test_vytvoreni_samostatne_akce_n_001(self):
        #Scenar_47 Vytvoření samostatné akce (negativní scénář 1)
        logger.info("AkcePridaniDokumentacniJednotky.test_vytvoreni_samostatne_akce_n_001.start")
        self.test_number=47
        self.login("badatel")
       
        arch_z_count_old = Akce.objects.count()
        
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-akce > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneAkce.zapsat")).click()
        #self.driver.find_element(By.ID, "select2-id_hlavni_katastr-container").click()
        #self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys("Velká Do")
        #self.wait(self.wait_interval)
        #self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "select2-id_hlavni_vedouci-container").click()
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys("Švejcar")
        self.wait(self.wait_interval)
        self.driver.find_element(By.CSS_SELECTOR, ".select2-search--dropdown > .select2-search__field").send_keys(Keys.ENTER)
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_organizace .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("archeologický")
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-1-29 > .text").click()
       
        self.driver.find_element(By.CSS_SELECTOR, ".required-next > .bs-placeholder .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("sonda")
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-2-22 > .text").click()
     
        self.driver.find_element(By.ID, "id_datum_zahajeni").click()
        self.driver.find_element(By.ID, "id_datum_zahajeni").send_keys("07.03.2024")
        self.driver.find_element(By.ID, "id_datum_ukonceni").click()
        self.driver.find_element(By.ID, "id_datum_ukonceni").send_keys("07.03.2024")
        self.driver.find_element(By.ID, "id_lokalizace_okolnosti").click()
        self.driver.find_element(By.ID, "id_lokalizace_okolnosti").send_keys("Hora")
        try:
            with Wait_for_page_load(self.driver):
                self.driver.find_element(By.ID, "actionSubmitBtn").click()       
        except Exception as e:
            pass
        arch_z_count_new = Akce.objects.count()
        self.assertEqual(arch_z_count_old, arch_z_count_new)
        logger.info("AkcePridaniDokumentacniJednotky.test_vytvoreni_samostatne_akce_n_001.end")
        

    def test_pridani_dokumentacni_jednotky_samostatne_akce_p_001(self):
        #Scenar_48 Přidání dokumentační jednotky celek akce (pozitivní scénář 1) 
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_dokumentacni_jednotky_samostatne_akce_p_001.start")
        self.test_number=48
        self.login("badatel")       
        
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-akce > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneAkce.vybrat")).click()
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000001A")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11) > .material-icons").click()
        self.driver.find_element(By.LINK_TEXT, "X-C-9000000001A").click()
        self.driver.find_element(By.CSS_SELECTOR, "#button-add-dj > .material-icons").click()
        self.driver.find_element(By.CSS_SELECTOR, ".bs-placeholder").click()
        self.driver.find_element(By.CSS_SELECTOR, "#bs-select-1-1 > .text").click()
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "newDjSubmitButton").click()
            
        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_dokumentacni_jednotky_samostatne_akce_p_001.end")
   
   
    def test_pridani_dokumentacni_jednotky_samostatne_akce_n_001(self):
        #Scenar_49 Přidání dokumentační jednotky “Celek akce” (negativní scénář 1) 
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_dokumentacni_jednotky_samostatne_akce_p_001.start")
        self.test_number=49
        self.login("badatel")       
        
        count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-akce > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneAkce.vybrat")).click()
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary > .app-icon-expand").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000001A")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11) > .material-icons").click()
        self.driver.find_element(By.LINK_TEXT, "X-C-9000000001A").click()
        self.driver.find_element(By.CSS_SELECTOR, "#button-add-dj > .material-icons").click()
        
        #self.driver.find_element(By.CSS_SELECTOR, ".bs-placeholder").click()
        #self.driver.find_element(By.CSS_SELECTOR, "#bs-select-1-1 > .text").click()
        try:
            with Wait_for_page_load(self.driver):
                self.driver.find_element(By.ID, "newDjSubmitButton").click()
        except Exception as e:
            pass
        count_new = DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.assertEqual(count_old, count_new)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_dokumentacni_jednotky_samostatne_akce_p_001.end")
   
   
    def test_pridani_komponenty_DJ_samostatne_akce_p_001(self):
        #Scenar_50 Přidání komponenty k DJ u samostatné akce (pozitivní scénář 1) 
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_komponenty_DJ_samostatne_akce_p_001.start")
        self.test_number=50
        self.login("badatel")
       
        count_old=Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000002A-D01").count()
        #count_old=DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely="X-C-9000000001A").count()
        self.driver.find_element(By.CSS_SELECTOR, ".app-entity-akce > .card-body").click()
        self.driver.find_element(By.LINK_TEXT, _("templates.baseLogedIn.sidebar.samostatneAkce.vybrat")).click()

        self.driver.find_element(By.CSS_SELECTOR, ".mt-1").click()
        self.driver.find_element(By.ID, "id_ident_cely").click()
        self.driver.find_element(By.ID, "id_ident_cely").send_keys("X-C-9000000002A")
        self.driver.find_element(By.CSS_SELECTOR, ".btn:nth-child(11)").click()
        self.driver.find_element(By.LINK_TEXT, "X-C-9000000002A").click()
        self.driver.find_element(By.CSS_SELECTOR, "#el_dokumentacni_jednotka_X_C_9000000002A_D01 > strong").click()
        #self.driver.execute_script("window.scrollTo(0,0)")
        self.driver.find_element(By.CSS_SELECTOR, "#detail_dj_form_X-C-9000000002A-D01 .btn-group:nth-child(1) .material-icons").click()
        self.driver.find_element(By.LINK_TEXT, "Přidat komponentu").click()
        self.driver.find_element(By.CSS_SELECTOR, "#div_id_obdobi .btn").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").click()
        #self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.DOWN)
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("únětická kultura")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)

        self.driver.find_element(By.CSS_SELECTOR, "#div_id_areal .filter-option-inner-inner").click()
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys("poh")
        self.driver.find_element(By.CSS_SELECTOR, ".show > .bs-searchbox > .form-control").send_keys(Keys.ENTER)
        #self.driver.find_element(By.CSS_SELECTOR, "#bs-select-3-39 > .text").click()

        #self.driver.execute_script("window.scrollTo(0,0)")
        with Wait_for_page_load(self.driver):
            self.driver.find_element(By.ID, "createCompotSubmitButton").click()
       
        count_new =Komponenta.objects.filter(komponenta_vazby__dokumentacni_jednotka__ident_cely="X-C-9000000002A-D01").count()
        self.assertEqual(count_old + 1, count_new)
        logger.info("AkcePridaniDokumentacniJednotky.test_pridani_komponenty_DJ_samostatne_akce_p_001.end")
        
   