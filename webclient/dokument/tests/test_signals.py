from core.constants import D_STAV_ZAPSANY
from core.tests.runner import (
    AMCR_TESTOVACI_ORGANIZACE_ID,
    MATERIAL_DOKUMENTU_DIGI_SOUBOR_ID,
    RADA_DOKUMENTU_TEXT_ID,
    TYP_DOKUMENTU_PLAN_SONDY_ID,
)
from django.test import TestCase
from dokument.models import Dokument
from heslar.hesla import PRISTUPNOST_ANONYM_ID
from heslar.models import Heslar
from uzivatel.models import Organizace


class TestDokumentSignals(TestCase):
    def setUp(self):
        pass

    def test_create_dokument_vazby(self):
        d = Dokument(
            rada=Heslar.objects.get(id=RADA_DOKUMENTU_TEXT_ID),
            typ_dokumentu=Heslar.objects.get(id=TYP_DOKUMENTU_PLAN_SONDY_ID),
            organizace=Organizace.objects.get(id=AMCR_TESTOVACI_ORGANIZACE_ID),
            pristupnost=Heslar.objects.get(id=PRISTUPNOST_ANONYM_ID),
            ident_cely="C-TX-201501111",
            stav=D_STAV_ZAPSANY,
            material_originalu=Heslar.objects.get(id=MATERIAL_DOKUMENTU_DIGI_SOUBOR_ID),
        )
        d.save()
        self.assertTrue(d.historie)
        self.assertTrue(d.soubory)
