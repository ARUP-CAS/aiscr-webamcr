from core.tests.runner import TYP_DJ_CELEK_AKCE_ID, add_middleware_to_request
from dj.models import DokumentacniJednotka
from dj.views import zapsat
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from pian.models import Pian
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")
        self.existing_dj = "C-202000001A-D01"
        self.existing_event = "C-202000001A"
        self.pian = Pian.objects.first()

    def test_post_zapsat(self):
        data = {
            "csrfmiddlewaretoken": "EnxpCIUt1PwHXwqP7FOtsaMGqlZJFQsIFy0fdKAjiBdInnJNBt2Fluk0Rl9DnC9t",
            "typ": str(TYP_DJ_CELEK_AKCE_ID),
            "pian": self.pian.pk,
        }

        request = self.factory.post("/dj/zapsat/", data)
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = zapsat(request, arch_z_ident_cely=self.existing_event)
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            DokumentacniJednotka.objects.filter(ident_cely="C-202000001A-D02").count(),
            1,
        )
