from core.tests.runner import add_middleware_to_request
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from dokument.views import detail
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")

    def test_get_detail(self):
        existing_dokument = "C-TX-201501985"

        request = self.factory.get("/dokument/detail/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = detail(request, ident_cely=existing_dokument)
        self.assertEqual(200, response.status_code)

    def test_get_edit(self):
        # TODO
        pass

    def test_post_edit(self):
        pass
