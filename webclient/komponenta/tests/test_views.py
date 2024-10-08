import logging

from core.tests.runner import AREAL_HRADISTE_ID, EXISTING_EVENT_IDENT, OBDOBI_STREDNI_PALEOLIT_ID
from django.test import RequestFactory, TestCase
from django.urls import reverse
from komponenta.models import Komponenta
from uzivatel.models import User

logger = logging.getLogger(__name__)


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")
        self.existing_akce = EXISTING_EVENT_IDENT
        self.existing_dj = "C-202000001A-D01"

    def test_post_zapsat(self):
        data = {
            "csrfmiddlewaretoken": "EnxpCIUt1PwHXwqP7FOtsaMGqlZJFQsIFy0fdKAjiBdInnJNBt2Fluk0Rl9DnC9t",
            "obdobi": str(OBDOBI_STREDNI_PALEOLIT_ID),
            "areal": str(AREAL_HRADISTE_ID),
        }

        self.client.force_login(self.existing_user)
        response = self.client.post(
            reverse("komponenta:zapsat", kwargs={"dj_ident_cely": "C-202000001A-D01"}),
            data,
            HTTP_REFERER="/dj/detail/C-202000001A-D01",
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            Komponenta.objects.filter(ident_cely="C-202000001A-K001").count(),
            1,
        )

        # Testing that I can delete the component
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("komponenta:smazat", kwargs={"ident_cely": "C-202000001A-K001"}))
        self.assertEqual(200, response.status_code)

        response = self.client.post(
            reverse("komponenta:smazat", kwargs={"ident_cely": "C-202000001A-K001"}),
            {"csrfmiddlewaretoken": "EnxpCIUt1PwHXwqP7FOtsaMGqlZJFQsIFy0fdKAjiBdInnJNBt2Fluk0Rl9DnC9t"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            Komponenta.objects.filter(ident_cely="C-202000001A-K001").count(),
            0,
        )
