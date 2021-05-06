import logging

from core.tests.runner import EXISTING_PROJECT_IDENT, add_middleware_to_request
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from historie.views import ProjektHistorieListView
from uzivatel.models import User

logger = logging.getLogger(__name__)


class HistorieTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")

    def test_get_projekt_historie(self):
        request = self.factory.get("/historie/projekt")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request.session.save()

        response = ProjektHistorieListView.as_view()(
            request, ident_cely=EXISTING_PROJECT_IDENT
        )
        self.assertEqual(200, response.status_code)
