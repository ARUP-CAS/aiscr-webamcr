from django.test import RequestFactory, TestCase
from oznameni.views import index


class UrlTests(TestCase):
    def setUp(self):
        pass

    def test_get_index(self):
        factory = RequestFactory()
        request = factory.get("/oznameni/")

        response = index(request)
        self.assertEqual(200, response.status_code)

    def test_post_index(self):
        pass
