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
        cls.safe_grandchild = cls._make_organization("ORG-OWN-SAFE-CHILD", "OWN-SAFE-CHILD", soucast=cls.sibling)
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
        query = queries[0]["sql"].strip().lower()
        self.assertIn("with recursive organizational_subtree(id, parent_id) as", query)
        self.assertTrue(query.endswith("select id, parent_id from organizational_subtree"))
        self.assertEqual(
            set(organization_ids),
            {self.root.pk, self.child.pk, self.grandchild.pk, self.sibling.pk, self.safe_grandchild.pk},
        )
        self.assertNotIn(self.ancestor.pk, organization_ids)
        self.assertNotIn(self.unrelated.pk, organization_ids)
        self.assertEqual(Organizace.get_subtree_ids(None), [])
        self.assertEqual(Organizace.get_subtree_ids(-1), [])

    def test_user_reuses_organization_subtree_for_instance_lifetime(self):
        """Ověří, že opakované čtení podstromu na uživateli provede pouze jeden dotaz."""
        user = User(organizace=self.root)

        with CaptureQueriesContext(connection) as queries:
            first_result = user.organizace_podstrom_ids
            second_result = user.organizace_podstrom_ids

        self.assertEqual(len(queries), 1)
        self.assertIs(first_result, second_result)
        self.assertEqual(
            set(first_result),
            {self.root.pk, self.child.pk, self.grandchild.pk, self.sibling.pk, self.safe_grandchild.pk},
        )

        new_child = self._make_organization("ORG-OWN-NEW-CHILD", "OWN-NEW-CHILD", soucast=self.root)
        with CaptureQueriesContext(connection) as refresh_queries:
            refreshed_result = user.organizace_podstrom_ids

        self.assertEqual(len(refresh_queries), 1)
        self.assertIn(new_child.pk, refreshed_result)

    def test_cyclic_subtree_retains_safe_descendants_and_logs_once_per_user(self):
        """Cyklus neudělí vlastnictví cyklické větvi a zachová bezpečné potomky."""
        Organizace.objects.filter(pk=self.root.pk).update(soucast=self.grandchild)
        user = User(organizace=self.root)
        with self.assertLogs("uzivatel.models", level="ERROR") as logs:
            with CaptureQueriesContext(connection) as queries:
                self.assertEqual(
                    set(user.organizace_podstrom_ids), {self.root.pk, self.sibling.pk, self.safe_grandchild.pk}
                )
                self.assertEqual(
                    set(user.organizace_podstrom_ids), {self.root.pk, self.sibling.pk, self.safe_grandchild.pk}
                )
        self.assertEqual(len(queries), 1)
        self.assertEqual(len(logs.records), 1)
        permission = Permissions(ownership=Permissions.ownershipChoices.our)
        permission.logged_in_user = user
        permission.permission_object = MagicMock()
        permission.permission_object.get_create_user.return_value = ()
        permission.permission_object.get_create_org.return_value = (self.root,)
        self.assertTrue(permission.check_ownership(permission.ownership))
        permission.permission_object.get_create_org.return_value = (self.child,)
        self.assertFalse(permission.check_ownership(permission.ownership))
        permission.permission_object.get_create_org.return_value = (self.safe_grandchild,)
        self.assertTrue(permission.check_ownership(permission.ownership))

    def test_self_cycle_preserves_children_and_other_trees_are_unaffected(self):
        """Vlastní cyklus nevyřadí běžné potomky a nesouvisející strom zůstane dostupný."""
        Organizace.objects.filter(pk=self.root.pk).update(soucast=self.root)
        with self.assertLogs("uzivatel.models", level="ERROR"):
            self.assertEqual(
                set(Organizace.get_subtree_ids(self.root.pk)),
                {self.root.pk, self.child.pk, self.grandchild.pk, self.sibling.pk, self.safe_grandchild.pk},
            )
            self.assertEqual(Organizace.get_subtree_ids(self.unrelated.pk), [self.unrelated.pk])

    def test_child_below_cycle_keeps_its_acyclic_subtree(self):
        """Organizace pod cyklem nezíská předky a zachová vlastní platný podstrom."""
        Organizace.objects.filter(pk=self.root.pk).update(soucast=self.child)
        self.assertEqual(Organizace.get_subtree_ids(self.grandchild.pk), [self.grandchild.pk])

    def test_cycle_branch_is_excluded_but_other_root_children_remain(self):
        """Potomci připojení pouze k cyklu nejsou dosažitelní od původního kořene."""
        cycle_child = self._make_organization("ORG-OWN-CYCLE-CHILD", "OWN-CYCLE-CHILD", soucast=self.root)
        cycle_grandchild = self._make_organization("ORG-OWN-CYC-GRAND", "OWN-CYC-GRAND", soucast=cycle_child)
        Organizace.objects.filter(pk=self.root.pk).update(soucast=cycle_child)

        with self.assertLogs("uzivatel.models", level="ERROR"):
            organization_ids = set(Organizace.get_subtree_ids(self.root.pk))

        self.assertEqual(
            organization_ids,
            {self.root.pk, self.child.pk, self.grandchild.pk, self.sibling.pk, self.safe_grandchild.pk},
        )
        self.assertNotIn(cycle_child.pk, organization_ids)
        self.assertNotIn(cycle_grandchild.pk, organization_ids)

    def test_deep_cycle_fallback_walk_is_iterative(self):
        """Fallback pro hlubokou bezpečnou větev nevyužívá rekurzi Pythonu."""
        rows = [(0, 1), (1, 0), (2, 0)]
        rows.extend((node, node - 1) for node in range(3, 2501))
        cursor = MagicMock()
        cursor.__enter__.return_value = cursor
        cursor.fetchall.return_value = rows
        with patch("uzivatel.models.connection.cursor", return_value=cursor):
            with self.assertLogs("uzivatel.models", level="ERROR"):
                organization_ids = Organizace.get_subtree_ids(0)

        self.assertEqual(len(organization_ids), 2500)
        self.assertEqual(organization_ids[0], 0)
        self.assertEqual(organization_ids[-1], 2500)

    def test_full_hierarchy_check_finds_cycles_once_and_has_no_writes(self):
        """Celková kontrola vrátí každý cyklus pouze jednou včetně uzavíracího uzlu."""
        Organizace.objects.filter(pk=self.root.pk).update(soucast=self.grandchild)
        Organizace.objects.filter(pk=self.unrelated.pk).update(soucast=self.unrelated)
        with self.assertNumQueries(1):
            cycles = Organizace.get_hierarchy_cycles()
        self.assertEqual(len(cycles), 2)
        self.assertIn([self.unrelated.ident_cely, self.unrelated.ident_cely], cycles)
        cycle = next(path for path in cycles if len(path) > 2)
        self.assertEqual(cycle[0], cycle[-1])
        self.assertEqual(set(cycle), {self.root.ident_cely, self.child.ident_cely, self.grandchild.ident_cely})

    def test_deep_cycle_check_does_not_depend_on_python_recursion_limit(self):
        """Hluboká hierarchie se zkontroluje iterativně bez přetečení zásobníku."""
        graph = {node: node + 1 for node in range(2500)}
        graph[2500] = 1000
        cycles = Organizace.find_cycles(graph)
        self.assertEqual(len(cycles), 1)
        self.assertEqual(cycles[0][0], cycles[0][-1])
        self.assertEqual(set(cycles[0]), set(range(1000, 2501)))

    def test_ownership_check_allows_descendants_but_not_ancestors_or_siblings(self):
        """Ověří dědičnost vlastnictví směrem k potomkům."""
        permission = Permissions(ownership=Permissions.ownershipChoices.our)
        permission.logged_in_user = User(organizace=self.root)
        permission.permission_object = MagicMock()
        permission.permission_object.get_create_user.return_value = ()

        for organization in (self.root, self.child, self.grandchild, self.sibling):
            permission.permission_object.get_create_org.return_value = (organization,)
            self.assertTrue(permission.check_ownership(permission.ownership), organization.ident_cely)

        for organization in (self.ancestor, self.unrelated):
            permission.permission_object.get_create_org.return_value = (organization,)
            self.assertFalse(permission.check_ownership(permission.ownership), organization.ident_cely)

    def test_ownership_check_does_not_grant_access_to_records_without_an_organization(self):
        """Ověří, že prázdná organizace záznamu neodpovídá uživatelovu podstromu."""
        permission = Permissions(ownership=Permissions.ownershipChoices.our)
        permission.logged_in_user = User(organizace=self.root)
        permission.permission_object = MagicMock()
        permission.permission_object.get_create_user.return_value = ()
        permission.permission_object.get_create_org.return_value = (None,)

        self.assertFalse(permission.check_ownership(permission.ownership))

    def test_restricted_accessibility_inherits_only_the_ownership_bypass(self):
        """Ověří vlastnickou výjimku pro záznam s omezenou přístupností."""
        permission = Permissions(accessibility=Permissions.ownershipChoices.our)
        permission.logged_in_user = User(organizace=self.root)
        permission.logged_in_user.hlavni_role = SimpleNamespace(pk=ROLE_BADATEL_ID)
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
            user=User(organizace=self.child),
        )
        request.user.hlavni_role = SimpleNamespace(pk=ROLE_ARCHEOLOG_ID)
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

    def test_pian_raw_sql_map_uses_descendant_ids_for_snapshot_and_project_paths(self):
        """Ověří použití potomků v obou vlastnických větvích SQL mapy PIAN."""
        request = SimpleNamespace(user=User(pk=100, organizace=self.child))
        request.user.hlavni_role = SimpleNamespace(id=ROLE_ARCHEOLOG_ID)
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

    def test_pian_heatmap_only_skips_subtree_and_detail_queries_at_threshold(self):
        """Heatmap-only odpověď nepočítá organizační podstrom ani nespouští detailní SQL."""
        request = SimpleNamespace(user=User(pk=100, organizace=self.child))
        request.user.hlavni_role = SimpleNamespace(id=ROLE_ARCHEOLOG_ID)
        cursor = MagicMock()
        cursor.__enter__.return_value = cursor
        cursor.fetchone.return_value = (10,)
        with patch("core.utils.LIMIT_PRVKU_ZOBRAZENI_HEATMAP", 5), patch(
            "django.db.connection.cursor", return_value=cursor
        ), patch.object(Organizace, "get_subtree_ids") as get_subtree_ids:
            pians, count = get_pian_from_envelope(
                {
                    "bottomLeft": {"lng": 14, "lat": 49},
                    "bottomRight": {"lng": 15, "lat": 49},
                    "topRight": {"lng": 15, "lat": 50},
                    "topLeft": {"lng": 14, "lat": 50},
                },
                7,
                request,
            )

        self.assertIsNone(pians)
        self.assertEqual(count, 10)
        self.assertEqual(cursor.execute.call_count, 1)
        get_subtree_ids.assert_not_called()
