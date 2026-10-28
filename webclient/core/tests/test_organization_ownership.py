from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock, patch

from core.constants import ROLE_ARCHEOLOG_ID, ROLE_BADATEL_ID
from core.models import Permissions
from core.utils import get_pian_from_envelope
from core.views import PermissionFilterMixin
from django.db import connection
from django.db.models import Q, QuerySet
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from heslar.hesla import HESLAR_LICENCE, HESLAR_ORGANIZACE_TYP, HESLAR_PIAN_PRESNOST, HESLAR_PRISTUPNOST
from heslar.models import Heslar, HeslarNazev
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from pas.views import PasPermissionFilterMixin, UzivatelSpolupraceListView
from pian.models import Pian
from pian.views import PianPermissionFilterMixin
from projekt.views import ProjectTableRowView, ProjektPermissionFilterMixin
from uzivatel.models import Organizace, User


class OrganizationOwnershipTest(TestCase):
    """Testy sdíleného vyhledávání hierarchie a oprávnění organizací."""

    @classmethod
    def setUpTestData(cls):
        """Vytvoří pomocné číselníky a hierarchii organizací."""
        for heslar_id, name, ident, label in (
            (HESLAR_ORGANIZACE_TYP, "typ_organizace", "HES-ORG-TYP-001", "Typ"),
            (HESLAR_PRISTUPNOST, "pristupnost", "HES-ORG-PRIST-001", "Veřejná"),
            (HESLAR_LICENCE, "licence", "HES-ORG-LIC-001", "Licence"),
            (HESLAR_PIAN_PRESNOST, "pian_presnost", "HES-ORG-PIAN-001", "Přesnost"),
        ):
            nazev, _ = HeslarNazev.objects.get_or_create(id=heslar_id, defaults={"nazev": name})
            Heslar.objects.get_or_create(
                ident_cely=ident,
                defaults={"nazev_heslare": nazev, "heslo": label, "heslo_en": label},
            )
        cls.typ_org = Heslar.objects.get(ident_cely="HES-ORG-TYP-001")
        cls.pristupnost = Heslar.objects.get(ident_cely="HES-ORG-PRIST-001")
        cls.licence = Heslar.objects.get(ident_cely="HES-ORG-LIC-001")

        cls.ancestor = cls._make_organization("ORG-OWN-ANCESTOR", "OWN-ANCESTOR")
        cls.root = cls._make_organization("ORG-OWN-ROOT", "OWN-ROOT", soucast=cls.ancestor)
        cls.child = cls._make_organization("ORG-OWN-CHILD", "OWN-CHILD", soucast=cls.root)
        cls.grandchild = cls._make_organization("ORG-OWN-GRANDCHILD", "OWN-GRANDCHILD", soucast=cls.child)
        cls.sibling = cls._make_organization("ORG-OWN-SIBLING", "OWN-SIBLING", soucast=cls.root)
        cls.unrelated = cls._make_organization("ORG-OWN-OTHER", "OWN-OTHER")

    @classmethod
    def _make_organization(cls, ident_cely, short_name, soucast=None):
        organization = Organizace(
            ident_cely=ident_cely,
            nazev=short_name,
            nazev_zkraceny=short_name,
            nazev_zkraceny_en=short_name,
            typ_organizace=cls.typ_org,
            zverejneni_pristupnost=cls.pristupnost,
            licence=cls.licence,
            soucast=soucast,
        )
        organization.suppress_signal = True
        organization.save()
        return organization

    def test_subtree_contains_root_and_all_descendants_only_with_one_query(self):
        """Ověří, že podstrom obsahuje kořen a pouze jeho potomky."""
        with CaptureQueriesContext(connection) as queries:
            organization_ids = Organizace.get_subtree_ids(self.root.pk)

        self.assertEqual(len(queries), 1)
        self.assertEqual(set(organization_ids), {self.root.pk, self.child.pk, self.grandchild.pk, self.sibling.pk})
        self.assertNotIn(self.ancestor.pk, organization_ids)
        self.assertNotIn(self.unrelated.pk, organization_ids)
        self.assertEqual(Organizace.get_subtree_ids(None), [])
        self.assertEqual(Organizace.get_subtree_ids(-1), [])

    def test_ownership_check_allows_descendants_but_not_ancestors_or_siblings(self):
        """Ověří dědičnost vlastnictví směrem k potomkům."""
        permission = Permissions(ownership=Permissions.ownershipChoices.our)
        permission.logged_in_user = SimpleNamespace(organizace=self.root, organizace_id=self.root.pk)
        permission.permission_object = MagicMock()
        permission.permission_object.get_create_user.return_value = ()

        for organization in (self.root, self.child, self.grandchild, self.sibling):
            permission.permission_object.get_create_org.return_value = (organization,)
            self.assertTrue(permission.check_ownership(permission.ownership), organization.ident_cely)

        for organization in (self.ancestor, self.unrelated):
            permission.permission_object.get_create_org.return_value = (organization,)
            self.assertFalse(permission.check_ownership(permission.ownership), organization.ident_cely)

    def test_ownership_check_preserves_missing_owner_and_missing_user_organization(self):
        """Ověří chování pro prázdnou organizaci uživatele či záznamu."""
        permission = Permissions(ownership=Permissions.ownershipChoices.our)
        permission.logged_in_user = SimpleNamespace(organizace=None, organizace_id=None)
        permission.permission_object = MagicMock()
        permission.permission_object.get_create_user.return_value = ()
        permission.permission_object.get_create_org.return_value = (None,)

        self.assertTrue(permission.check_ownership(permission.ownership))

        permission.permission_object.get_create_org.return_value = (self.root,)
        self.assertFalse(permission.check_ownership(permission.ownership))

    def test_restricted_accessibility_inherits_only_the_ownership_bypass(self):
        """Ověří vlastnickou výjimku pro záznam s omezenou přístupností."""
        permission = Permissions(accessibility=Permissions.ownershipChoices.our)
        permission.logged_in_user = SimpleNamespace(
            organizace=self.root,
            organizace_id=self.root.pk,
            hlavni_role=SimpleNamespace(pk=ROLE_BADATEL_ID),
        )
        permission.permission_object = MagicMock()
        permission.permission_object.get_create_user.return_value = ()
        permission.permission_object.get_create_org.return_value = (self.grandchild,)
        permission.permission_object.pristupnost.pk = 999999

        self.assertTrue(permission.check_accessibility())

        permission.permission_object.get_create_org.return_value = (self.ancestor,)
        self.assertFalse(permission.check_accessibility())

    @staticmethod
    def _organization_ids_from_q(query):
        organization_ids = set()
        for child in query.children:
            if isinstance(child, Q):
                organization_ids.update(OrganizationOwnershipTest._organization_ids_from_q(child))
            elif isinstance(child, tuple):
                value = child[1]
                if isinstance(value, QuerySet):
                    organization_ids.update(
                        parameter for parameter in value.query.sql_with_params()[1] if isinstance(parameter, int)
                    )
                elif isinstance(value, (list, tuple, set)):
                    organization_ids.update(value)
        return organization_ids

    @staticmethod
    def _lookup_names(query):
        names = set()
        for child in query.children:
            if isinstance(child, Q):
                names.update(OrganizationOwnershipTest._lookup_names(child))
            elif isinstance(child, tuple):
                names.add(child[0])
        return names

    def _request_for(self, organization):
        return SimpleNamespace(
            user=User(pk=100, organizace=organization),
        )

    def test_all_ownership_queryset_branches_expand_only_the_selected_root(self):
        """Ověří rozšíření querysetů jen o potomky zvoleného kořene."""
        expected = {self.child.pk, self.grandchild.pk}
        denied = {self.ancestor.pk, self.root.pk, self.sibling.pk, self.unrelated.pk}

        core_view = PermissionFilterMixin()
        core_view.request = self._request_for(self.child)
        core_query = core_view.add_ownership_lookup(Permissions.ownershipChoices.our)
        core_ids = self._organization_ids_from_q(core_query)
        self.assertTrue(expected.issubset(core_ids))
        self.assertTrue(denied.isdisjoint(core_ids))

        project_view = ProjektPermissionFilterMixin()
        project_view.request = self._request_for(self.child)
        project_ids = self._organization_ids_from_q(project_view.add_ownership_lookup("our"))
        self.assertEqual(project_ids, expected)

        pas_view = PasPermissionFilterMixin()
        pas_view.request = self._request_for(self.child)
        pas_ids = self._organization_ids_from_q(pas_view.add_ownership_lookup("our", SamostatnyNalez.objects.all()))
        self.assertEqual(pas_ids, expected)

        pian_view = PianPermissionFilterMixin()
        pian_view.request = self._request_for(self.child)
        pian_query = pian_view.add_ownership_lookup("our", Pian.objects.all())
        pian_ids = self._organization_ids_from_q(pian_query)
        self.assertTrue(expected.issubset(pian_ids))
        self.assertTrue(denied.isdisjoint(pian_ids))
        self.assertIn(
            "dokumentacni_jednotky_pianu__archeologicky_zaznam__historie__historie__organizace_snapshot__in",
            self._lookup_names(pian_query),
        )

        cooperation_view = UzivatelSpolupraceListView()
        cooperation_view.request = self._request_for(self.child)
        cooperation_ids = self._organization_ids_from_q(
            cooperation_view.add_ownership_lookup("our", UzivatelSpoluprace.objects.all())
        )
        self.assertEqual(cooperation_ids, expected)

    def test_project_row_uses_current_organization_and_descendants_after_transfer(self):
        """Ověří výběr projektů podle současné organizace po převodu."""
        request = SimpleNamespace(
            GET={"id": "42"},
            user=SimpleNamespace(
                hlavni_role=SimpleNamespace(pk=ROLE_ARCHEOLOG_ID),
                organizace=self.child,
                organizace_id=self.child.pk,
            ),
        )
        queryset = MagicMock()
        queryset.exists.return_value = True
        queryset.get.return_value = SimpleNamespace()
        with patch("projekt.views.Projekt.objects.filter", return_value=queryset) as filter_projects, patch(
            "projekt.views.render_to_string", return_value=""
        ):
            ProjectTableRowView().get(request)

        self.assertEqual(set(filter_projects.call_args.kwargs["organizace__in"]), {self.child.pk, self.grandchild.pk})

    def test_collaborating_organization_list_includes_descendants(self):
        """Ověří zahrnutí potomků do seznamu spolupracujících organizací."""
        badatel, archeolog, archivar, admin = [SimpleNamespace() for _ in range(4)]
        collaborations = MagicMock()
        collaborations.filter.return_value.select_related.return_value.values_list.return_value = [self.unrelated.pk]
        user = User(organizace=self.child)
        user.hlavni_role = archeolog

        with patch(
            "uzivatel.models.Group.objects.get", side_effect=[badatel, archeolog, archivar, admin]
        ), patch.object(User, "spoluprace_badatelu", new_callable=PropertyMock, return_value=collaborations):
            organization_ids = user.moje_spolupracujici_organizace()

        self.assertEqual(set(organization_ids), {self.child.pk, self.grandchild.pk, self.unrelated.pk})
        self.assertNotIn(self.root.pk, organization_ids)
        self.assertNotIn(self.sibling.pk, organization_ids)

    def test_collaborating_organization_list_preserves_users_without_organization(self):
        """Ověří chování spolupráce u uživatele bez organizace."""
        badatel, archeolog, archivar, admin = [SimpleNamespace() for _ in range(4)]
        collaborations = MagicMock()
        collaborations.filter.return_value.select_related.return_value.values_list.return_value = [self.unrelated.pk]
        user = User(pk=101, organizace=None)
        user.hlavni_role = archeolog

        with patch(
            "uzivatel.models.Group.objects.get", side_effect=[badatel, archeolog, archivar, admin]
        ), patch.object(User, "spoluprace_badatelu", new_callable=PropertyMock, return_value=collaborations):
            organization_ids = user.moje_spolupracujici_organizace()

        self.assertEqual(set(organization_ids), {self.unrelated.pk, None})

    def test_pian_raw_sql_map_uses_descendant_ids_for_snapshot_and_project_paths(self):
        """Ověří použití potomků v obou vlastnických větvích SQL mapy PIAN."""
        request = SimpleNamespace(
            user=SimpleNamespace(
                hlavni_role=SimpleNamespace(id=ROLE_ARCHEOLOG_ID),
                organizace_id=self.child.pk,
                id=100,
            )
        )
        cursor = MagicMock()
        cursor.__enter__.return_value = cursor
        cursor.fetchone.return_value = (0,)
        cursor.fetchall.return_value = []
        cursor.description = []
        with patch("heslar.models.Heslar.objects.filter") as filter_heslar, patch(
            "django.db.connection.cursor", return_value=cursor
        ), patch.object(
            Organizace, "get_subtree_ids", return_value=[self.child.pk, self.grandchild.pk]
        ) as get_subtree_ids:
            filter_heslar.return_value.first.return_value.id = self.pristupnost.pk
            get_pian_from_envelope(
                {
                    "bottomLeft": {"lng": 14, "lat": 49},
                    "bottomRight": {"lng": 15, "lat": 49},
                    "topRight": {"lng": 15, "lat": 50},
                    "topLeft": {"lng": 14, "lat": 50},
                },
                8,
                request,
            )

        get_subtree_ids.assert_called_once_with(self.child.pk)
        map_query, map_params = cursor.execute.call_args_list[1].args
        self.assertEqual(map_query.count("= ANY(%s)"), 3)
        self.assertIn("h.organizace_snapshot_id", map_query)
        self.assertIn("p1.organizace", map_query)
        self.assertEqual(
            map_params[-3:],
            [[self.child.pk, self.grandchild.pk]] * 3,
        )
