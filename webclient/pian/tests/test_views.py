from django.test import RequestFactory, TestCase
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")
        self.existing_dj = "C-202000001A-D01"

    """
    This test cannot be run as the view uses a custom SQL procedure
    """
    # def test_post_create(self):
    #     presnost: Heslar = Heslar.objects.filter(nazev_heslare__id=HESLAR_PIAN_PRESNOST).first()
    #     data = {
    #         "csrfmiddlewaretoken": "EnxpCIUt1PwHXwqP7FOtsaMGqlZJFQsIFy0fdKAjiBdInnJNBt2Fluk0Rl9DnC9t",
    #         "presnost": str(PRESNOST_DESITKY_METRU_ID),
    #         "typ": str(GEOMETRY_BOD),
    #         "stav": "2",
    #         "geom": "SRID=4326;POINT (14.4268084 50.0846009)",
    #     }
    #     request = self.factory.post("/pian/zapsat/", data)
    #     request.user = self.existing_user
    #     request = add_middleware_to_request(request, SessionMiddleware)
    #     request = add_middleware_to_request(request, MessageMiddleware)
    #     request.session.save()
    #     request.META["HTTP_REFERER"] = "/arch_z/detail/C-202000001A"
    #
    #     pian_count_before = Pian.objects.all().count()
    #     response = create(request, self.existing_dj)
    #     pian_count_after = Pian.objects.all().count()
    #     self.assertEqual(302, response.status_code)
    #     self.assertTrue(pian_count_before < pian_count_after)
