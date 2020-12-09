from django.test import RequestFactory, TestCase
from oznameni.views import index


class UrlTests(TestCase):
    def test_index(self):
        factory = RequestFactory()
        request = factory.get("/oznameni/")

        response = index(request)
        self.assertEqual(200, response.status_code)
