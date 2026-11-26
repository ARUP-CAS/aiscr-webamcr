"""Regresní testy stávajícího vyhodnocení matice oprávnění a Rosetty."""

from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from core.constants import ROLE_UPRAVA_TEXTU
from core.middleware import PermissionMiddleware
from core.models import Permissions, check_permissions
from core.services import PermissionService
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import resolve
from rosetta.access import can_translate, get_access_control_function
from rosetta.views import RosettaBaseMixin, TranslationFileListView
from uzivatel.models import User


class _Membership:
    """Minimální sada členství pro ověření výběru hlavní a doplňkové role."""

    def __init__(self, groups):
        self.groups = sorted(groups, key=lambda group: group.pk)

    def filter(self, **kwargs):
        """Vybere skupiny podle podmínek používaných aplikací a Rosettou."""
        ids = kwargs.get("id__in")
        group_id = kwargs.get("id")
        return _Membership(
            [group for group in self.groups if group.pk in ids]
            if ids is not None
            else [group for group in self.groups if group.pk == group_id]
        )

    def count(self):
        """Vrátí počet vybraných skupin."""
        return len(self.groups)

    def last(self):
        """Vrátí poslední skupinu v pořadí podle ID."""
        return self.groups[-1] if self.groups else None


class _User:
    """Aktivní uživatel se skutečnou implementací výběru hlavní role."""

    is_active = True
    is_authenticated = True

    def __init__(self, groups):
        self.groups = _Membership(groups)

    @property
    def hlavni_role(self):
        """Použije stejný výběr role jako model uživatele."""
        return User.hlavni_role.func(self)


class PermissionPolicyCharacterizationTest(TestCase):
    """Ověří skutečný import, kompakci, pomocníka a middleware."""

    @classmethod
    def setUpTestData(cls):
        """Načte verzovanou matici do izolované testovací databáze."""
        cls.roles = {
            pk: Group.objects.get_or_create(pk=pk, defaults={"name": name})[0]
            for pk, name in ((1, "Badatel"), (2, "Archeolog"), (3, "Archivář"), (4, "Admin"))
        }
        cls.translation_group = Group.objects.get_or_create(pk=ROLE_UPRAVA_TEXTU, defaults={"name": "Překlady"})[0]
        Permissions.objects.all().delete()
        source = Path(__file__).resolve().parents[1] / "resources" / "uzivatelska_prava.csv"
        PermissionService().run(SimpleUploadedFile(source.name, source.read_bytes()))

    def test_import_compacts_unrestricted_actions_but_preserves_allows(self):
        """Kompakce nesmí změnit povolení staré ani nově zavedené akce."""
        for role_id, action in ((4, "mapa_pas"), (4, "dok_zapsat_vlastni_ident"), (3, "dok_zapsat_vlastni_ident")):
            with self.subTest(role=role_id, action=action):
                self.assertFalse(Permissions.objects.filter(main_role=self.roles[role_id], action=action).exists())
                self.assertTrue(check_permissions(action, _User([self.roles[role_id]])))
        self.assertFalse(check_permissions("dok_zapsat_vlastni_ident", _User([self.roles[1]])))

    def test_helper_and_middleware_preserve_empty_and_or_results(self):
        """Prázdná sada povolí, samé zákazy zamítnou a jedno povolení stačí."""
        role = self.roles[1]
        user = _User([role])
        action = "dok_edit"
        address = "test/permission-or/"
        Permissions.objects.filter(main_role=role, action=action).delete()
        self.assertTrue(check_permissions(action, user))
        request = RequestFactory().get("/" + address)
        request.user = user
        request.resolver_match = SimpleNamespace(route=address, kwargs={})
        middleware = PermissionMiddleware(lambda request: HttpResponse())
        self.assertIsNone(middleware.process_view(request, None, (), {}))
        Permissions.objects.create(main_role=role, action=action, address_in_app=address, base=False)
        self.assertFalse(check_permissions(action, user))
        with self.assertRaises(PermissionDenied):
            middleware.process_view(request, None, (), {})
        Permissions.objects.create(main_role=role, action=action, address_in_app=address, base=True)
        self.assertTrue(check_permissions(action, user))
        self.assertIsNone(middleware.process_view(request, None, (), {}))

    def test_supplementary_group_does_not_change_main_role(self):
        """Překladová skupina nepřepisuje hlavní roli matice."""
        for role_id, role in self.roles.items():
            with self.subTest(role=role_id):
                plain = _User([role])
                translator = _User([role, self.translation_group])
                self.assertEqual(translator.hlavni_role, role)
                self.assertEqual(
                    check_permissions("dok_zapsat_vlastni_ident", plain),
                    check_permissions("dok_zapsat_vlastni_ident", translator),
                )
                self.assertFalse(can_translate(plain))
                self.assertTrue(can_translate(translator))

    def test_translation_file_list_combines_matrix_and_rosetta_guards(self):
        """Správce potřebuje překladovou skupinu; nižší role zamítne matice."""
        path = "/rosetta/files/project/"
        match = resolve(path)
        middleware = PermissionMiddleware(lambda request: HttpResponse())
        for role_id, role in self.roles.items():
            for has_translation in (False, True):
                with self.subTest(role=role_id, has_translation=has_translation):
                    groups = [role] + ([self.translation_group] if has_translation else [])
                    request = RequestFactory().get(path)
                    request.user = _User(groups)
                    request.resolver_match = match
                    if role_id != 4:
                        with self.assertRaises(PermissionDenied):
                            middleware.process_view(request, match.func, (), match.kwargs)
                    else:
                        self.assertIsNone(middleware.process_view(request, match.func, (), match.kwargs))
                        with mock.patch.object(TranslationFileListView, "get", return_value=HttpResponse("ok")):
                            response = match.func(request, **match.kwargs)
                        self.assertEqual(response.status_code, 200 if has_translation else 302)

    def test_unicode_package_routes_keep_their_independent_translation_guard(self):
        """Balíčkové routy s ne-ASCII indexem zachovávají dosavadní kontrolu skupiny."""
        middleware = PermissionMiddleware(lambda request: HttpResponse())
        for suffix in ("", "download/"):
            path = f"/rosetta/files/all/cs/١/{suffix}"
            match = resolve(path)
            for has_translation in (False, True):
                with self.subTest(suffix=suffix, has_translation=has_translation):
                    groups = [self.roles[1]] + ([self.translation_group] if has_translation else [])
                    request = RequestFactory().get(path)
                    request.user = _User(groups)
                    request.resolver_match = match
                    self.assertIsNone(middleware.process_view(request, match.func, (), match.kwargs))
                    with mock.patch.object(match.func.view_class, "get", return_value=HttpResponse("ok")):
                        response = match.func(request, **match.kwargs)
                    self.assertEqual(response.status_code, 200 if has_translation else 302)


class PermissionConditionCharacterizationTest(SimpleTestCase):
    """Ověří zachování stavových podmínek, vlastnictví a výjimek."""

    def _permission(self, **kwargs):
        """Připraví oprávnění s objektem bez závislosti na úložišti."""
        permission = Permissions(base=True, address_in_app="test", action="dok_edit", **kwargs)
        obj = SimpleNamespace(stav=2, ident_cely="TEST-1", pristupnost=SimpleNamespace(pk=99))
        obj.get_create_user = lambda: []
        obj.get_create_org = lambda: []
        permission.get_permission_object = lambda: setattr(permission, "permission_object", obj)
        return permission

    def test_status_and_skip_status(self):
        """Stavový nesoulad zamítne, volitelné přeskočení stavu povolí."""
        permission = self._permission(status="D1")
        user = SimpleNamespace(hlavni_role=SimpleNamespace(pk=2))
        self.assertFalse(permission.check_concrete_permission(user, "TEST-1"))
        self.assertTrue(permission.check_concrete_permission(user, "TEST-1", skip_status=True))

    def test_ownership_and_accessibility_restrictions(self):
        """Nedostatečné vlastnictví nebo přístupnost může oprávnění zamítnout."""
        user = SimpleNamespace(hlavni_role=SimpleNamespace(pk=1), organizace_podstrom_ids=[])
        for fields in ({"ownership": "my"}, {"accessibility": "my"}):
            with self.subTest(fields=fields):
                permission = self._permission(**fields)
                with mock.patch.object(permission, "check_permission_skip", return_value=False):
                    self.assertFalse(permission.check_concrete_permission(user, "TEST-1"))

    def test_explicit_skip_and_file_override(self):
        """Výjimka záznamu a právo číst dokumenty zachovají stávající obejití."""
        user = SimpleNamespace(hlavni_role=SimpleNamespace(pk=2), organizace=SimpleNamespace(cteni_dokumentu=True))
        permission = self._permission(ownership="my")
        with mock.patch("core.models.PermissionsSkip.objects.filter") as skips:
            skips.return_value.values_list.return_value = ["TEST-1"]
            self.assertTrue(permission.check_concrete_permission(user, "TEST-1"))
            skips.return_value.values_list.return_value = []
            self.assertFalse(permission.check_concrete_permission(user, "TEST-1"))
        permission.action = Permissions.actionChoices.soubor_stahnout_dokument
        with mock.patch.object(permission, "check_permission_skip", return_value=False):
            self.assertTrue(permission.check_concrete_permission(user, "TEST-1"))


class RosettaRouteCharacterizationTest(SimpleTestCase):
    """Zachytí pořadí URL a nezávislou kontrolu přístupu balíčku Rosetta."""

    def test_redirects_resolve_to_amcr_file_list(self):
        """Staré vstupy přesměrují na seznam chráněný aplikací AMČR."""
        for path in ("/rosetta/", "/rosetta/files/"):
            with self.subTest(path=path):
                response = resolve(path).func(RequestFactory().get(path))
                self.assertEqual(response.status_code, 302)
                destination = resolve(response.url)
                self.assertEqual(destination.view_name, "core:rosetta-file-list")

    def test_ascii_and_unicode_indexes_can_resolve_to_different_views(self):
        """Číslice mimo ASCII zpřístupní balíčkový pohled se samostatnou kontrolou Rosetty."""
        for suffix, core_name, package_name in (
            ("", "core:rosetta-form", "rosetta-form"),
            ("download/", "core:rosetta-download-file", "rosetta-download-file"),
        ):
            with self.subTest(suffix=suffix):
                self.assertEqual(resolve(f"/rosetta/files/all/cs/0/{suffix}").view_name, core_name)
                package = resolve(f"/rosetta/files/all/cs/١/{suffix}")
                self.assertEqual(package.view_name, package_name)
                self.assertTrue(issubclass(package.func.view_class, RosettaBaseMixin))
                request = RequestFactory().get(f"/rosetta/files/all/cs/١/{suffix}")
                request.user = _User([])
                self.assertEqual(package.func(request, **package.kwargs).status_code, 302)

    def test_translation_endpoint_uses_configured_guard(self):
        """Balíčkový překladač používá nakonfigurovanou kontrolu skupiny."""
        self.assertEqual(get_access_control_function().__name__, "rosetta_translation_rights")
        match = resolve("/rosetta/translate/")
        request = RequestFactory().get("/rosetta/translate/")
        request.user = _User([])
        self.assertEqual(match.func(request).status_code, 302)
