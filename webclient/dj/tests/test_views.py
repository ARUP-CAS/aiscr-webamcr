from core.tests.runner import (
    add_middleware_to_request,
)
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from dj.views import zapsat, detail
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")
        self.existing_dj = "C-202000001A-D01"
        self.existing_event = "C-202000001A"

    # def test_get_detail(self):
    #     request = self.factory.get("/dj/detail/")
    #     request.user = self.existing_user
    #     request = add_middleware_to_request(request, SessionMiddleware)
    #     request = add_middleware_to_request(request, MessageMiddleware)
    #     request.session.save()
    #
    #     response = detail(request, ident_cely=self.existing_dj)
    #     self.assertEqual(200, response.status_code)
    #
    # def test_get_zapsat(self):
    #     request = self.factory.get("/dj/zapsat/")
    #     request = add_middleware_to_request(request, SessionMiddleware)
    #     request.user = self.existing_user
    #     request.session.save()
    #
    #     response = zapsat(request, arch_z_ident_cely=self.existing_event)
    #     self.assertEqual(200, response.status_code)

    # def test_post_edit(self):
    #     data = {
    #
    #     }
    #     request = self.factory.post("/dj/edit/", data)
    #     request.user = self.existing_user
    #     request = add_middleware_to_request(request, SessionMiddleware)
    #     request = add_middleware_to_request(request, MessageMiddleware)
    #     request.session.save()
    #
    #     response = edit(request, self.existing_dj)
    #     self.assertEqual(200, response.status_code)
    #     self.assertTrue("error" not in response.content.decode("utf-8"))
