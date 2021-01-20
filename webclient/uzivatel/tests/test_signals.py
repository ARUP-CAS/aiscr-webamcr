from django.test import TestCase
from heslar.models import Heslar
from uzivatel.models import AuthUser, Organizace


class TestProjektSignals(TestCase):
    def setUp(self):
        pass

    def test_create_ident_cely(self):
        huld = Organizace(
            nazev="Huld s.r.o.",
            nazev_zkraceny="Huld",
            typ_organizace=Heslar.objects.get(id=1116),  # Ustav pamatkove pece
            oao=True,
        )
        huld.save()
        tester = AuthUser(
            password="pbkdf2_sha256$216000$8fyTVvI62PeB$p237Rd85fhMkW6wCjzJIZ1M9J0n1UrsWN+oSotdhPd0=",
            is_superuser=False,
            first_name="Juraj",
            last_name="Tester",
            email="tester@example.com",
            is_staff=False,
            is_active=True,
            organizace=huld,
        )
        tester.save()
        self.assertEqual(tester.ident_cely, "U-000001")
        print(AuthUser.objects.all())
        tester2 = AuthUser(
            password="pbkdf2_sha256$216000$8fyTVvI62PeB$p237Rd85fhMkW6wCjzJIZ1M9J0n1UrsWN+oSotdhPd0=",
            ident_cely="U-000009",
            is_superuser=False,
            first_name="Juraj",
            last_name="Tester2",
            email="tester2@example.com",
            is_staff=False,
            is_active=True,
            organizace=huld,
        )
        tester2.save()
        self.assertEqual(tester2.ident_cely, "U-000009")
        tester3 = AuthUser(
            password="pbkdf2_sha256$216000$8fyTVvI62PeB$p237Rd85fhMkW6wCjzJIZ1M9J0n1UrsWN+oSotdhPd0=",
            is_superuser=False,
            first_name="Juraj",
            last_name="Tester3",
            email="tester3@example.com",
            is_staff=False,
            is_active=True,
            organizace=huld,
        )
        tester3.save()
        self.assertEqual(tester3.ident_cely, "U-000010")
