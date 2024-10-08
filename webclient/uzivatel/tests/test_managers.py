from django.contrib.auth import get_user_model
from django.test import TestCase
from uzivatel.models import Organizace


class UsersManagersTests(TestCase):
    def setUp(self):
        pass

    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            email="normal@user.com",
            password="foo",
            organizace=Organizace.objects.get(id=769066),
        )
        self.assertEqual(user.email, "normal@user.com")
        self.assertTrue(not user.is_active)
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
            User.objects.create_superuser(email="super@user.com", password="foo", is_superuser=False)
