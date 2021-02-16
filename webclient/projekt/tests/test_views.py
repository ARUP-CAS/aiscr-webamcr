from core.tests.runner import add_middleware_to_request
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404
from django.test import RequestFactory, TestCase
from projekt.views import detail
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_detail_not_found(self):
        # Setting up the request like this whenever login_required
        request = self.factory.get("/projekt/detail/")
        request.user = User.objects.get(email="amcr@arup.cas.cz")
        request = add_middleware_to_request(request, SessionMiddleware)
        request.session.save()

        with self.assertRaises(Http404, msg="No Projekt matches the given query."):
            detail(request, ident_cely="not_existing_project_ident")

    def test_check_pred_uzavrenim(self):
        pass
        # TODO napsat test na check projektu pred uzavrenim
