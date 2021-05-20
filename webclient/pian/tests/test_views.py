from core.tests.runner import (
    PRESNOST_DESITKY_METRU_ID,
    TYP_PIAN_BOD_ID,
    add_middleware_to_request,
)
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from pian.models import Pian
from pian.views import create
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")
        self.existing_dj = "C-202000001A-D01"

    def test_post_create(self):
        data = {
            "csrfmiddlewaretoken": "EnxpCIUt1PwHXwqP7FOtsaMGqlZJFQsIFy0fdKAjiBdInnJNBt2Fluk0Rl9DnC9t",
            "presnost": str(PRESNOST_DESITKY_METRU_ID),
            "typ": str(TYP_PIAN_BOD_ID),
            "stav": "2",
            "geom": "SRID=4326;POINT (13.21198546245427 50.58080006469174)",
        }

        request = self.factory.post("/pian/create/", data)
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        pian_count_before = Pian.objects.all().count()
        response = create(request)
        pian_count_after = Pian.objects.all().count()
        self.assertEqual(200, response.status_code)
        self.assertTrue(pian_count_before < pian_count_after)
