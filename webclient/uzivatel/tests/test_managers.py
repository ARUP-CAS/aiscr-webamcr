from django.contrib.auth import get_user_model
from django.test import TestCase
from heslar.models import Heslar, HeslarNazev
from uzivatel.models import Organizace


class UsersManagersTests(TestCase):
    def setUp(self):
        hn = HeslarNazev(id=39, heslar="testovaci_heslar")
        hn.save()
        h = Heslar(
            id=1120, heslo="ostatní", nazev_heslare=hn, heslo_en="to be translated"
        )
        zp = Heslar(id=859, nazev_heslare=hn, heslo_en="to be translated")
        zp.save()
        h.save()
        o = Organizace(
            id=769066,
            nazev="Space Systems Czech, s.r.o.",
            nazev_zkraceny="Testing organizations SSC",
            typ_organizace=h,
            zverejneni_pristupnost=zp,
        )
        o.save()

    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            email="normal@user.com",
            password="foo",
            organizace=Organizace.objects.get(id=769066),
        )
        self.assertEqual(user.email, "normal@user.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        with self.assertRaises(TypeError):
            User.objects.create_user()
        with self.assertRaises(TypeError):
            User.objects.create_user(email="")
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="foo")

    def test_create_superuser(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            "super@user.com", "foo", organizace=Organizace.objects.get(id=769066)
        )
        self.assertEqual(admin_user.email, "super@user.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="super@user.com", password="foo", is_superuser=False
            )
