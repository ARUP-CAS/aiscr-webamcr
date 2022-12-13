from django.urls import reverse
from ez.models import ExterniZdroj
from core.tests.runner import (
    EL_CHEFE_ID,
    EXISTIN_EO_ID,
    EXISTING_EVENT_IDENT,
    EXISTING_EZ_IDENT,
    EXISTING_EZ_ODESLANY,
    EZ_TYP,
    EZ_TYP_NEW,
    add_middleware_to_request,
)
from django.test import RequestFactory, TestCase
from django.utils.translation import gettext as _
from uzivatel.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from ez.views import ExterniZdrojDetailView
from core.constants import EZ_STAV_ODESLANY, EZ_STAV_POTVRZENY, EZ_STAV_ZAPSANY
from arch_z.models import ArcheologickyZaznam, ExterniOdkaz


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")

    def test_get_ez_detail(self):
        request = self.factory.get("/ext-zdroj/detail/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request.session.save()

        response = ExterniZdrojDetailView.as_view()(request, slug=EXISTING_EZ_IDENT)
        self.assertEqual(200, response.status_code)

    def test_get_ez_vyber(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("ez:list"))
        self.assertEqual(200, response.status_code)

    def test_get_ez_zapsat(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(f"/ext-zdroj/zapsat")
        self.assertEqual(200, response.status_code)

    def test_post_ez_zapsat(self):
        ez_last = ExterniZdroj.objects.all().order_by("pk").last()
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "typ": str(EZ_TYP),
            "rok_vydani_vzniku": "2010",
            "nazev": "nazev knihy",
            "autori": str(EL_CHEFE_ID),
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(f"/ext-zdroj/zapsat", data, follow=True)
        ez = ExterniZdroj.objects.get(pk=ez_last.pk + 1)
        self.assertEqual(200, response.status_code)
        self.assertEqual(ez.typ.pk, EZ_TYP)
        self.assertEqual(ez.nazev, "nazev knihy")

    def test_get_ez_editovat(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(f"/ext-zdroj/edit/{EXISTING_EZ_IDENT}")
        self.assertEqual(200, response.status_code)

    def test_post_ez_editovat(self):
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "typ": str(EZ_TYP_NEW),
            "rok_vydani_vzniku": "2000",
            "nazev": "nazev casopisu",
            "autori": str(EL_CHEFE_ID),
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/ext-zdroj/edit/{EXISTING_EZ_IDENT}", data, follow=True
        )
        ez = ExterniZdroj.objects.filter(ident_cely=EXISTING_EZ_IDENT).first()
        ez.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(ez.typ.pk, EZ_TYP_NEW)
        self.assertEqual(ez.nazev, "nazev casopisu")
        self.assertEqual(ez.rok_vydani_vzniku, "2000")
        self.assertTrue(
            len(ExterniZdroj.objects.filter(ident_cely=EXISTING_EZ_IDENT)) == 1
        )

    def test_get_ez_odelsat(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            "%s?sent_stav=1"
            % reverse(
                "ez:odeslat",
                kwargs={"ident_cely": EXISTING_EZ_IDENT},
            ),
        )
        self.assertEqual(200, response.status_code)

    def test_post_ez_odeslat(self):
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "old_stav": str(EZ_STAV_ZAPSANY),
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/ext-zdroj/odeslat/{EXISTING_EZ_IDENT}", data, follow=True
        )
        ez = ExterniZdroj.objects.get(ident_cely=EXISTING_EZ_IDENT)
        ez.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(ez.stav, EZ_STAV_ODESLANY)

    def test_get_ez_potvrdit(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            "%s?sent_stav=2"
            % reverse(
                "ez:potvrdit",
                kwargs={"ident_cely": EXISTING_EZ_ODESLANY},
            ),
        )
        self.assertEqual(200, response.status_code)

    def test_post_ez_potvrdit(self):
        ez = ExterniZdroj.objects.get(ident_cely=EXISTING_EZ_ODESLANY)
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "old_stav": str(EZ_STAV_ODESLANY),
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/ext-zdroj/potvrdit/{EXISTING_EZ_ODESLANY}", data, follow=True
        )
        ez.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(ez.stav, EZ_STAV_POTVRZENY)

    def test_get_ez_vratit(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            "%s?sent_stav=2"
            % reverse(
                "ez:vratit",
                kwargs={"ident_cely": EXISTING_EZ_ODESLANY},
            ),
        )
        self.assertEqual(200, response.status_code)

    def test_post_ez_vratit(self):
        ez = ExterniZdroj.objects.get(ident_cely=EXISTING_EZ_ODESLANY)
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "old_stav": str(EZ_STAV_ODESLANY),
            "reason": "vraceni",
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/ext-zdroj/vratit/{EXISTING_EZ_ODESLANY}", data, follow=True
        )
        ez.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(ez.stav, EZ_STAV_ZAPSANY)

    def test_get_ez_smazat(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            "%s?sent_stav=2"
            % reverse(
                "ez:smazat",
                kwargs={"ident_cely": EXISTING_EZ_ODESLANY},
            ),
        )
        self.assertEqual(200, response.status_code)

    def test_post_ez_smazat(self):
        ez = ExterniZdroj.objects.get(ident_cely=EXISTING_EZ_ODESLANY)
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "old_stav": str(EZ_STAV_ODESLANY),
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/ext-zdroj/smazat/{EXISTING_EZ_ODESLANY}", data, follow=True
        )
        self.assertEqual(200, response.status_code)
        with self.assertRaises(ExterniZdroj.DoesNotExist):
            ExterniZdroj.objects.get(ident_cely=EXISTING_EZ_ODESLANY)

    def test_get_ez_pripojit(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            reverse(
                "ez:pripojit_eo",
                kwargs={"ident_cely": EXISTING_EZ_IDENT},
            ),
        )
        self.assertEqual(200, response.status_code)

    def test_post_ez_pripojit(self):
        az = ArcheologickyZaznam.objects.get(ident_cely=EXISTING_EVENT_IDENT)
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "old_stav": str(EZ_STAV_ZAPSANY),
            "arch_z": str(az.id),
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/ext-zdroj/pripojit-externi-odkaz/{EXISTING_EZ_IDENT}?type=akce",
            data,
            follow=True,
        )
        eo_count = ExterniOdkaz.objects.all().count()
        self.assertEqual(200, response.status_code)
        self.assertEqual(eo_count, 2)

    def test_get_eo_zmenit(self):
        eo = ExterniOdkaz.objects.get(id=EXISTIN_EO_ID)
        self.client.force_login(self.existing_user)
        response = self.client.get(
            reverse(
                "ez:zmenit_eo",
                kwargs={"slug": eo.pk},
            ),
        )
        self.assertEqual(200, response.status_code)

    def test_post_ez_zmenit(self):
        eo = ExterniOdkaz.objects.get(id=EXISTIN_EO_ID)
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "paginace": "177-190",
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/ext-zdroj/edit-paginace/{eo.pk}",
            data,
            follow=True,
        )
        eo.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(eo.paginace, "177-190")

    def test_get_ez_odpojit(self):
        eo = ExterniOdkaz.objects.get(id=EXISTIN_EO_ID)
        self.client.force_login(self.existing_user)
        response = self.client.get(
            reverse(
                "ez:odpojit_eo",
                kwargs={"ident_cely": EXISTING_EZ_IDENT, "eo_id": eo.pk},
            ),
        )
        self.assertEqual(200, response.status_code)

    def test_post_ez_odpojit(self):
        eo = ExterniOdkaz.objects.get(id=EXISTIN_EO_ID)
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "old_stav": str(EZ_STAV_ZAPSANY),
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/ext-zdroj/odpojit-externi-odkaz/{EXISTING_EZ_IDENT}/{eo.pk}",
            data,
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        with self.assertRaises(ExterniOdkaz.DoesNotExist):
            ExterniOdkaz.objects.get(id=eo.pk)

    def test_get_ez_pripojit_doaz(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            reverse(
                "ez:pripojit_eo_do_az",
                kwargs={"ident_cely": EXISTING_EVENT_IDENT},
            ),
        )
        self.assertEqual(200, response.status_code)

    def test_post_ez_pripojit_doaz(self):
        ez = ExterniZdroj.objects.get(ident_cely=EXISTING_EZ_IDENT)
        az = ArcheologickyZaznam.objects.get(ident_cely=EXISTING_EVENT_IDENT)
        eo_count_old = ExterniOdkaz.objects.all().count()
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "old_stav": str(az.stav),
            "ez": str(ez.id),
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/ext-zdroj/pripojit-externi-odkaz-do-az/{EXISTING_EVENT_IDENT}",
            data,
            follow=True,
        )
        eo_count = ExterniOdkaz.objects.all().count()
        self.assertEqual(200, response.status_code)
        self.assertEqual(eo_count, eo_count_old + 1)

    def test_get_ez_odpojit_zaz(self):
        eo = ExterniOdkaz.objects.all().first()
        self.client.force_login(self.existing_user)
        response = self.client.get(
            reverse(
                "ez:odpojit_eo_az",
                kwargs={
                    "ident_cely": eo.archeologicky_zaznam.ident_cely,
                    "eo_id": eo.pk,
                },
            ),
        )
        self.assertEqual(200, response.status_code)

    def test_post_ez_odpojit_zaz(self):
        eo = ExterniOdkaz.objects.all().first()
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "old_stav": str(eo.archeologicky_zaznam.stav),
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/ext-zdroj/odpojit-externi-odkaz-az/{eo.archeologicky_zaznam.ident_cely}/{eo.pk}",
            data,
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        with self.assertRaises(ExterniOdkaz.DoesNotExist):
            ExterniOdkaz.objects.get(id=eo.pk)