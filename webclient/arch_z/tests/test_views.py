from arch_z.models import Akce, ArcheologickyZaznam
from core.tests.runner import (
    AMCR_TESTOVACI_ORGANIZACE_ID,
    EL_CHEFE_ID,
    EXISTING_DOCUMENT_ID,
    EXISTING_EVENT_IDENT,
    EXISTING_EVENT_IDENT2,
    EXISTING_EVENT_IDENT_INCOMPLETE,
    EXISTING_SAM_EVENT_IDENT,
    HLAVNI_TYP_SONDA_ID,
)
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _
from dokument.models import Dokument
from heslar.hesla_dynamicka import PRISTUPNOST_ANONYM_ID, SPECIFIKACE_DATA_PRESNE
from heslar.models import RuianKatastr
from projekt.models import Projekt
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.existing_projekt_ident = "C-202000001"
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")

    def test_get_detail(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("arch_z:detail", kwargs={"ident_cely": EXISTING_EVENT_IDENT}))
        self.assertEqual(200, response.status_code)

    def test_get_zapsat(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("arch_z:zapsat-akci"))
        self.assertEqual(200, response.status_code)

    def test_post_zapsat(self):
        data = {
            "csrfmiddlewaretoken": "27ZVK57GOldButY8IAxsDdqBlpUtsWBcpykJT7DgTENfOsy7uqkfoSoYWkbXmcu2",
            "hlavni_katastr": str(RuianKatastr.objects.filter(nazev="ODROVICE").first().pk),
            "pristupnost": str(PRISTUPNOST_ANONYM_ID),
            "uzivatelske_oznaceni": "",
            "hlavni_vedouci": str(EL_CHEFE_ID),
            "datum_zahajeni": "15.11.2020",
            "datum_ukonceni": "15.12.2020",
            "specifikace_data": SPECIFIKACE_DATA_PRESNE,
            "lokalizace_okolnosti": "Nekde proste to je",
            "ulozeni_nalezu": "",
            "hlavni_typ": str(HLAVNI_TYP_SONDA_ID),
            "vedlejsi_typ": "",
            "_osv-TOTAL_FORMS": 2,
            "_osv-INITIAL_FORMS": 1,
            "_osv-MIN_NUM_FORMS": 0,
            "_osv-MAX_NUM_FORMS": 1000,
            "_osv-__prefix__-vedouci": "",
            "_osv-__prefix__-organizace": "",
            "_osv-__prefix__-id": "",
            "_osv-__prefix__-akce": 1276681,
            "_osv-0-vedouci": EL_CHEFE_ID,
            "_osv-0-organizace": AMCR_TESTOVACI_ORGANIZACE_ID,
            "_osv-0-id": "",
            "_osv-0-akce": "",
            "_osv-1-vedouci": "",
            "_osv-1-organizace": "",
            "_osv-1-id": "",
            "_osv-1-akce": "",
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            reverse(
                "arch_z:zapsat",
                kwargs={"projekt_ident_cely": self.existing_projekt_ident},
            ),
            data,
        )
        az = ArcheologickyZaznam.objects.filter(ident_cely="C-202000001B").first()
        az.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(az.akce.specifikace_data.pk, SPECIFIKACE_DATA_PRESNE)
        self.assertEqual(az.pristupnost.pk, PRISTUPNOST_ANONYM_ID)
        self.assertTrue(len(ArcheologickyZaznam.objects.filter(ident_cely="C-202000001B")) == 1)

    def test_get_odeslat_s_chybami(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            reverse(
                "arch_z:odeslat",
                args=[
                    EXISTING_EVENT_IDENT_INCOMPLETE,
                ],
            )
        )

        self.assertTrue(_("Datum zahájení není vyplněn.") in self.client.session["temp_data"])
        self.assertTrue(_("Datum ukončení není vyplněn.") in self.client.session["temp_data"])
        self.assertTrue(_("Lokalizace okolností není vyplněna.") in self.client.session["temp_data"])
        self.assertTrue(_("Hlavní typ není vyplněn.") in self.client.session["temp_data"])
        self.assertTrue(_("Hlavní vedoucí není vyplněn.") in self.client.session["temp_data"])
        self.assertEqual(403, response.status_code)

    def test_get_odeslat(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            "%s?sent_stav=1"
            % reverse(
                "arch_z:odeslat",
                kwargs={"ident_cely": EXISTING_EVENT_IDENT},
            ),
        )
        self.assertEqual(200, response.status_code)

    def test_get_vratit(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("arch_z:vratit", kwargs={"ident_cely": EXISTING_EVENT_IDENT}))
        self.assertEqual(403, response.status_code)

    def test_get_pripojit_dokument(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            reverse(
                "arch_z:pripojit_dokument",
                kwargs={"arch_z_ident_cely": EXISTING_EVENT_IDENT},
            )
        )
        self.assertEqual(200, response.status_code)

    def test_post_pripojit_dokument(self):
        data = {
            "csrfmiddlewaretoken": "27ZVK57GOldButY8IAxsDdqBlpUtsWBcpykJT7DgTENfOsy7uqkfoSoYWkbXmcu2",
            "dokument": str(EXISTING_DOCUMENT_ID),
        }
        self.client.force_login(self.existing_user)

        documents_before = Dokument.objects.filter(casti__archeologicky_zaznam__ident_cely=EXISTING_EVENT_IDENT).count()
        response = self.client.post(
            reverse(
                "arch_z:pripojit_dokument",
                kwargs={"arch_z_ident_cely": EXISTING_EVENT_IDENT},
            ),
            data,
        )
        documents_after = Dokument.objects.filter(casti__archeologicky_zaznam__ident_cely=EXISTING_EVENT_IDENT).count()
        self.assertEqual(200, response.status_code)
        self.assertTrue("error" not in response.content.decode("utf-8"))
        self.assertEqual(documents_before + 1, documents_after)

    def test_get_akce_vyber(self):
        self.client.force_login(self.existing_user)
        response = self.client.get("/arch-z/akce/vyber")
        self.assertEqual(200, response.status_code)

    def test_get_zmenit_proj_akci(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("arch_z:zmenit-proj-akci", kwargs={"ident_cely": EXISTING_EVENT_IDENT2}))
        self.assertEqual(200, response.status_code)

    def test_post_zmenit_proj_akci(self):
        data = {
            "csrfmiddlewaretoken": "27ZVK57GOldButY8IAxsDdqBlpUtsWBcpykJT7DgTENfOsy7uqkfoSoYWkbXmcu2",
            "old_stav": str(1),
        }
        akce_count = Akce.objects.filter(typ=Akce.TYP_AKCE_SAMOSTATNA).count()
        stav = ArcheologickyZaznam.objects.get(ident_cely=EXISTING_EVENT_IDENT2).stav
        self.client.force_login(self.existing_user)
        response = self.client.post(
            "%s?sent_stav=%s"
            % (
                reverse(
                    "arch_z:zmenit-proj-akci",
                    kwargs={"ident_cely": EXISTING_EVENT_IDENT2},
                ),
                stav,
            ),
            data,
        )
        new_akce_count = Akce.objects.filter(typ=Akce.TYP_AKCE_SAMOSTATNA).count()
        self.assertEqual(200, response.status_code)
        self.assertEqual(akce_count + 1, new_akce_count)

    def test_get_zmenit_sam_akci(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            "%s?sent_stav=1"
            % reverse(
                "arch_z:zmenit-proj-akci",
                kwargs={"ident_cely": EXISTING_SAM_EVENT_IDENT},
            ),
        )
        self.assertEqual(200, response.status_code)

    def test_post_zmenit_sam_akci(self):
        projekt_id = Projekt.objects.get(ident_cely=self.existing_projekt_ident).id
        data = {
            "csrfmiddlewaretoken": "27ZVK57GOldButY8IAxsDdqBlpUtsWBcpykJT7DgTENfOsy7uqkfoSoYWkbXmcu2",
            "old_stav": str(1),
            "projekt": projekt_id,
        }
        akce_count = Akce.objects.filter(typ=Akce.TYP_AKCE_PROJEKTOVA).count()
        self.client.force_login(self.existing_user)
        response = self.client.post(
            "%s?sent_stav=1"
            % reverse(
                "arch_z:zmenit-sam-akci",
                kwargs={"ident_cely": EXISTING_SAM_EVENT_IDENT},
            ),
            data,
        )
        new_akce_count = Akce.objects.filter(typ=Akce.TYP_AKCE_PROJEKTOVA).count()
        self.assertEqual(302, response.status_code)
        self.assertEqual(akce_count + 1, new_akce_count)
