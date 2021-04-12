from core.tests.runner import (
    AREAL_HRADISTE_ID,
    OBDOBI_STREDNI_PALEOLIT_ID,
    add_middleware_to_request,
)
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from komponenta.models import Komponenta
from komponenta.views import zapsat
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")
        self.existing_dj = "C-202000001A-D01"

    def test_post_zapsat(self):
        data = {
            "csrfmiddlewaretoken": "EnxpCIUt1PwHXwqP7FOtsaMGqlZJFQsIFy0fdKAjiBdInnJNBt2Fluk0Rl9DnC9t",
            "obdobi": str(OBDOBI_STREDNI_PALEOLIT_ID),
            "areal": str(AREAL_HRADISTE_ID),
        }

        request = self.factory.post("/komponenta/zapsat/", data)
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.META["HTTP_REFERER"] = "/dj/detail/C-202000001A-D01"
        request.session.save()

        response = zapsat(request, dj_ident_cely=self.existing_dj)
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            Komponenta.objects.filter(ident_cely="C-202000001A-K01").count(),
            1,
        )
