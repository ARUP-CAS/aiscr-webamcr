from arch_z.views import detail
from core.tests.runner import add_middleware_to_request
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_detail(self):
        test_ident = "C-202000001A"
        request = self.factory.get("/arch_z/detail/")
        request.user = User.objects.get(email="amcr@arup.cas.cz")
        request = add_middleware_to_request(request, SessionMiddleware)
        request.session.save()

        response = detail(request, test_ident)
        self.assertEqual(200, response.status_code)
