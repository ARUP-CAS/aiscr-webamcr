import csv
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.constants import ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID, SPOLUPRACE_AKTIVNI, SPOLUPRACE_NEAKTIVNI
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse
from pas.models import UzivatelSpoluprace
from pas.views import AktivaceEmailView, aktivace


def _user(pk, organizace_id, hlavni_role_id=2):
    user = MagicMock()
    user.pk = pk
    user.organizace_id = organizace_id
    user.hlavni_role.pk = hlavni_role_id
    user.is_authenticated = True
    return user


def _spoluprace(vedouci_pk=1, vedouci_org=10):
    spoluprace = UzivatelSpoluprace(id=5, stav=SPOLUPRACE_NEAKTIVNI)
    spoluprace.vedouci_id = vedouci_pk
    vedouci = MagicMock()
    vedouci.organizace_id = vedouci_org
    spoluprace._state.fields_cache["vedouci"] = vedouci
    return spoluprace


class MuzePotvrditTest(SimpleTestCase):
    """Testy pravidla, kdo smí potvrdit žádost o spolupráci."""

    def test_vedouci(self):
        """Určený vedoucí smí žádost potvrdit."""
        self.assertTrue(_spoluprace().muze_potvrdit(_user(1, 99)))

    def test_stejna_organizace(self):
        """Uživatel z organizace vedoucího smí žádost potvrdit."""
        self.assertTrue(_spoluprace().muze_potvrdit(_user(2, 10)))

    def test_cizi_organizace(self):
        """Uživatel z cizí organizace nesmí žádost potvrdit."""
        self.assertFalse(_spoluprace().muze_potvrdit(_user(2, 11)))

    def test_archivar_a_admin_z_cizi_organizace(self):
        """Archivář a administrátor smí potvrdit žádost i z cizí organizace."""
        for role in (ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID):
            self.assertTrue(_spoluprace().muze_potvrdit(_user(2, 11, role)))

    def test_bez_organizace(self):
        """Uživatel bez organizace nesmí potvrdit žádost vedoucího bez organizace."""
        spoluprace = _spoluprace(vedouci_org=None)
        self.assertFalse(spoluprace.muze_potvrdit(_user(2, None)))

    def test_set_aktivni_cizi_nezmeni_stav(self):
        """Cizí uživatel nezmění stav ani neuloží spolupráci přes set_aktivni()."""
        spoluprace = _spoluprace()
        with patch.object(UzivatelSpoluprace, "save") as save:
            with self.assertRaises(PermissionDenied):
                spoluprace.set_aktivni(_user(2, 11))
        save.assert_not_called()
        self.assertEqual(spoluprace.stav, SPOLUPRACE_NEAKTIVNI)

    def test_set_aktivni_vedouci(self):
        """Vedoucí aktivuje spolupráci přes set_aktivni()."""
        spoluprace = _spoluprace()
        with patch.object(UzivatelSpoluprace, "save"), patch("pas.models.Historie"):
            spoluprace.set_aktivni(_user(1, 10))
        self.assertEqual(spoluprace.stav, SPOLUPRACE_AKTIVNI)


class AktivaceViewsPermissionTest(SimpleTestCase):
    """Testy kontroly oprávnění v pohledech potvrzujících spolupráci."""

    def _request(self, method, user):
        request = getattr(RequestFactory(), method)("/x")
        request.user = user
        return request

    def test_email_view_cizi_get_i_post(self):
        """AktivaceEmailView odmítne cizího uživatele při GET i POST."""
        for method in ("get", "post"):
            view = AktivaceEmailView()
            view.setup(self._request(method, _user(2, 11)), pk=5)
            with patch("pas.views.UzivatelSpoluprace.objects.all"), patch(
                "django.views.generic.detail.SingleObjectMixin.get_object", return_value=_spoluprace()
            ):
                with self.assertRaises(PermissionDenied):
                    view.get_object()

    def test_email_view_vedouci(self):
        """AktivaceEmailView vrátí spolupráci vedoucímu."""
        view = AktivaceEmailView()
        view.setup(self._request("get", _user(1, 10)), pk=5)
        spoluprace = _spoluprace()
        with patch("django.views.generic.detail.SingleObjectMixin.get_object", return_value=spoluprace):
            self.assertIs(view.get_object(), spoluprace)

    def test_aktivace_modal_cizi(self):
        """Funkce aktivace() odmítne cizího uživatele při GET i POST."""
        for method in ("get", "post"):
            with patch("pas.views.get_object_or_404", return_value=_spoluprace()):
                response = aktivace(self._request(method, _user(2, 11)), pk=5)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(json.loads(response.content), {"redirect": reverse("pas:spoluprace_list")})

    def test_aktivace_modal_nezmeni_stav_cizimu(self):
        """Funkce aktivace() při odmítnutí neuloží spolupráci."""
        spoluprace = _spoluprace()
        with patch("pas.views.get_object_or_404", return_value=spoluprace), patch.object(
            UzivatelSpoluprace, "save"
        ) as save:
            aktivace(self._request("post", _user(2, 11)), pk=5)
        save.assert_not_called()
        self.assertEqual(spoluprace.stav, SPOLUPRACE_NEAKTIVNI)


class MaticePravSpolupraceTest(SimpleTestCase):
    """Testy matice práv, na které závisí ``UzivatelSpoluprace.muze_potvrdit()``."""

    TRASY = ("spoluprace/aktivace-email/<int:pk>", "spoluprace/aktivovat/<int:pk>")

    def _radky(self):
        cesta = Path(__file__).resolve().parents[2] / "core" / "resources" / "uzivatelska_prava.csv"
        with open(cesta, encoding="utf-8", newline="") as soubor:
            radky = {r["URL"]: r for r in csv.DictReader(soubor) if r["app"] == "pas"}
        return [radky[trasa] for trasa in self.TRASY]

    def test_badatel_nema_pristup(self):
        """Badatel nemá přístup na žádnou z tras potvrzující spolupráci."""
        for radek in self._radky():
            self.assertEqual(radek["Základní_B"], "X", radek["URL"])

    def test_archeolog_jen_vlastni_organizace(self):
        """Archeolog smí potvrzovat jen v rámci své organizace."""
        for radek in self._radky():
            self.assertEqual(radek["Vlastnictví_C"], "US.ours", radek["URL"])
