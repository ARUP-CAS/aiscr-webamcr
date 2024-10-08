from core.constants import SPOLUPRACE_AKTIVNI, SPOLUPRACE_NEAKTIVNI, SPOLUPRACE_ZADOST
from core.tests.runner import USER_ARCHEOLOG_EMAIL, USER_ARCHEOLOG_ID
from django.test import RequestFactory, TestCase
from historie.models import Historie
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")

    def test_get_spoluprace(self):
        self.client.force_login(self.existing_user)
        response = self.client.get("/pas/spoluprace/zadost")
        self.assertEqual(200, response.status_code)

    def test_post_spoluprace(self):
        data = {
            "csrfmiddlewaretoken": "9Pw981eCflkJAFviBOe3TWRfk7QCQUoD5EuzF7kB38XwWlvIxA8p7JyY3nBzLpoH",
            "email_uzivatele": USER_ARCHEOLOG_EMAIL,
            "text": "Test poznámka 123",
        }
        self.client.force_login(self.existing_user)
        historie_records_per_count = Historie.objects.filter(
            typ_zmeny=SPOLUPRACE_ZADOST, uzivatel=self.existing_user
        ).count()
        response = self.client.post("/pas/spoluprace/zadost", data, follow=True)
        self.assertEqual(200, response.status_code)

        historie_records_post_query = Historie.objects.filter(typ_zmeny=SPOLUPRACE_ZADOST, uzivatel=self.existing_user)
        self.assertEqual(historie_records_per_count + 1, historie_records_post_query.count())
        historie = historie_records_post_query.last()
        self.assertEqual(historie.poznamka, "Test poznámka 123")

        # local import to avoid circular import issue
        from pas.models import UzivatelSpoluprace

        uzivatel_spoluprace_query = UzivatelSpoluprace.objects.filter(vedouci_id=USER_ARCHEOLOG_ID)
        self.assertEqual(uzivatel_spoluprace_query.count(), 1)

        uzivatel_spoluprace: UzivatelSpoluprace = uzivatel_spoluprace_query.last()
        response = self.client.post(f"/pas/spoluprace/aktivovat/{uzivatel_spoluprace.pk}", {}, follow=True)
        uzivatel_spoluprace.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(uzivatel_spoluprace.stav, SPOLUPRACE_AKTIVNI)

        response = self.client.post(f"/pas/spoluprace/deaktivovat/{uzivatel_spoluprace.pk}", {}, follow=True)
        uzivatel_spoluprace.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(uzivatel_spoluprace.stav, SPOLUPRACE_NEAKTIVNI)
