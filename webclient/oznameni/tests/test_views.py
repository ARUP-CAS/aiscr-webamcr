import json

from django.test import RequestFactory, TestCase
from oznameni.views import index, post_poi2kat


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_index(self):
        request = self.factory.get("/oznameni/")

        response = index(request)
        self.assertEqual(200, response.status_code)

    def test_post_index(self):
        # TODO add test
        pass

    def test_post_poi2kat(self):
        josefov = (14.417222, 50.089616)
        request = self.factory.post(
            "/oznameni/get-katastr-from-point",
            {"corY": josefov[0], "corX": josefov[1]},
            content_type="application/json",
        )
        response = post_poi2kat(request)
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(data["cadastre"], "JOSEFOV (Praha)")
