"""Testy ošetření neplatných vstupů, které dříve končily HTTP 500 (issue #4529)."""

from unittest import mock

from core.constants import PROJEKT_STAV_OZNAMENY, PROJEKT_STAV_VYTVORENY
from core.repository_connector import FedoraUpdatedByAnotherTransactionError
from core.views import SearchListView
from django.core.exceptions import PermissionDenied
from django.db.models.query import QuerySet
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase
from dokument.views import DokumentyAzTableView
from oznameni.views import OznameniDokumentaceView
from projekt.models import Projekt


class FilterValidSortParamsTest(SimpleTestCase):
    """Neplatné pole v parametru ``sort`` se vynechá, místo aby ``order_by()`` skončilo ``FieldError``."""

    def test_neplatne_pole_je_vynechano(self):
        """Překlep v názvu pole z URL (``katasgettr``) se zahodí, platná pole zůstanou v původním pořadí."""
        qs = Projekt.objects.all()
        vysledek = SearchListView.filter_valid_sort_params(qs, ["katasgettr", "ident_cely", "-stav"])
        self.assertEqual(vysledek, ["ident_cely", "-stav"])

    def test_pole_pres_vazbu(self):
        """Pole přes cizí klíč (``hlavni_katastr__nazev``) je platné, neexistující pole přes vazbu ne."""
        qs = Projekt.objects.all()
        vysledek = SearchListView.filter_valid_sort_params(qs, ["hlavni_katastr__nazev", "hlavni_katastr__neexistuje"])
        self.assertEqual(vysledek, ["hlavni_katastr__nazev"])

    def test_get_sort_params_omezi_pocet_a_zahodi_duplicity(self):
        """Z URL se zohlední nejvýše ``max_sort_params`` unikátních termínů v původním pořadí."""
        view = SearchListView()
        hodnoty = ["a", "b", "a"] + [f"pole{i}" for i in range(20)]
        view.request = RequestFactory().get("/", {"sort": hodnoty})
        vysledek = view._get_sort_params()
        self.assertEqual(SearchListView.max_sort_params, 8)
        self.assertEqual(vysledek, ["a", "b"] + [f"pole{i}" for i in range(6)])

    def test_prazdny_seznam(self):
        """Bez parametru ``sort`` se vrací prázdný seznam."""
        self.assertEqual(SearchListView.filter_valid_sort_params(Projekt.objects.all(), []), [])


class ExportBezSuffixuTest(SimpleTestCase):
    """Export seznamu bez ``export_suffix_string`` vrací 400, ne 500."""

    def test_chybejici_export_suffix_string(self):
        """Parametr se kontroluje dřív, než se vytvoří spojení do Redisu nebo načtou data."""
        view = SearchListView()
        view.redis_value_list_field = "ident_cely"
        view.redis_snapshot_prefix = "lokalita"
        view.request = RequestFactory().get("/arch-z/lokalita/vyber", {"_export": "json"})
        with mock.patch("core.views.RedisConnector") as redis_connector:
            response = view.create_export("json")
        self.assertEqual(response.status_code, 400)
        redis_connector.get_connection_decode.assert_not_called()


class DokumentyAzTableViewTest(SimpleTestCase):
    """Neexistující záznam v tabulce dokumentů vrací 404."""

    def _get(self, typ_vazby):
        """
        Zavolá pohled s ident_cely, který v databázi neexistuje.

        :param typ_vazby: Typ vazby v URL (``arch_z`` nebo ``projekt``).
        :raises Http404: Pokud pohled správně odmítne neexistující záznam.
        """
        request = RequestFactory().get("/")
        with mock.patch.object(QuerySet, "get", autospec=True, side_effect=_raise_does_not_exist):
            DokumentyAzTableView().get(request, typ_vazby, "C-202205552A")

    def test_neexistujici_akce(self):
        """Pro ``arch_z`` se neexistující záznam změní na ``Http404``."""
        with self.assertRaises(Http404):
            self._get("arch_z")

    def test_neexistujici_projekt(self):
        """Pro ostatní vazby (projekt) se neexistující záznam změní na ``Http404``."""
        with self.assertRaises(Http404):
            self._get("projekt")


def _raise_does_not_exist(queryset, *args, **kwargs):
    """
    Napodobí ``QuerySet.get()`` bez shody.

    :param queryset: Queryset, nad kterým se ``get()`` volá.
    :param args: Poziční argumenty ``get()``, nepoužité.
    :param kwargs: Pojmenované argumenty ``get()``, nepoužité.
    :raises DoesNotExist: Vždy, výjimka modelu querysetu.
    """
    raise queryset.model.DoesNotExist


class OznameniDokumentacePostTest(SimpleTestCase):
    """POST druhého kroku oznámení: neexistující projekt a souběh s jinou transakcí Fedory."""

    def _post(self):
        """
        Vytvoří pohled a POST požadavek s ident_cely z formuláře.

        :return: Dvojice (pohled, požadavek).
        """
        view = OznameniDokumentaceView()
        view.session_identifier = mock.MagicMock()
        view.session_identifier.get_ident.return_value = "X-C-000027078"
        view.ident_cely = "X-C-000027078"
        request = RequestFactory().post("/", {"ident_cely": "X-C-000027078"})
        return view, request

    def test_ident_z_formulare_neodpovida_url(self):
        """Ident v těle POST jiný než v URL se odmítne ještě před načtením projektu."""
        view, request = self._post()
        view.ident_cely = "X-C-000000001"
        view.session_identifier.get_ident.return_value = "X-C-000000001"
        with mock.patch("oznameni.views.get_object_or_404") as get_projekt:
            with self.assertRaises(PermissionDenied):
                view.post(request)
        get_projekt.assert_not_called()

    def test_ident_neodpovida_projektu_v_session(self):
        """Projekt, který uživatel v této session nerozepsal, nelze oznámit."""
        view, request = self._post()
        view.session_identifier.get_ident.return_value = None
        with mock.patch("oznameni.views.get_object_or_404") as get_projekt:
            with self.assertRaises(PermissionDenied):
                view.post(request)
        get_projekt.assert_not_called()

    @mock.patch("oznameni.views.Mailer")
    @mock.patch("oznameni.views.get_object_or_404")
    def test_projekt_ve_spatnem_stavu(self, get_projekt, mailer):
        """Projekt, který už není ve stavu vytvořený, se znovu neoznamuje a nespouští e-maily.

        :param get_projekt: Mock ``get_object_or_404``, vrací už oznámený projekt.
        :param mailer: Mock ``Mailer``, nesmí se zavolat.
        """
        projekt = get_projekt.return_value
        projekt.stav = PROJEKT_STAV_OZNAMENY
        view, request = self._post()
        with self.assertRaises(PermissionDenied):
            view.post(request)
        projekt.set_oznameny.assert_not_called()
        mailer.send_eo01.assert_not_called()
        mailer.send_eo02.assert_not_called()

    def test_neexistujici_projekt(self):
        """Projekt z formuláře, který neexistuje, vrací 404 místo ``DoesNotExist`` a 500."""
        view, request = self._post()
        with mock.patch.object(QuerySet, "get", autospec=True, side_effect=_raise_does_not_exist):
            with self.assertRaises(Http404):
                view.post(request)

    @mock.patch("oznameni.views.Mailer")
    @mock.patch("oznameni.views.messages")
    @mock.patch("oznameni.views.transaction")
    @mock.patch("oznameni.views.FedoraTransaction")
    @mock.patch("oznameni.views.get_object_or_404")
    def test_fedora_409_nevraci_500(self, get_projekt, fedora_transaction, db_transaction, messages, mailer):
        """
        409 z Fedory při souběžném uploadu se zaloguje, DB změna se odroluje a uživatel dostane chybovou hlášku.

        :param get_projekt: Mock ``get_object_or_404``, vrací projekt, jehož ``set_oznameny`` selže.
        :param fedora_transaction: Mock třídy ``FedoraTransaction``.
        :param db_transaction: Mock modulu ``django.db.transaction`` (savepoint bez DB).
        :param messages: Mock ``django.contrib.messages``.
        :param mailer: Mock ``Mailer``, nesmí se zavolat.
        """
        projekt = get_projekt.return_value
        projekt.ident_cely = "X-M-000027426"
        projekt.stav = PROJEKT_STAV_VYTVORENY
        projekt.set_oznameny.side_effect = FedoraUpdatedByAnotherTransactionError(
            "url", "conflict", 409, {}, fedora_transaction.return_value
        )
        db_transaction.atomic.return_value.__exit__.return_value = False
        view, request = self._post()
        response = view.post(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/oznameni/dokumentace/X-M-000027426")
        messages.add_message.assert_called_once()
        mailer.send_eo01.assert_not_called()
        mailer.send_eo02.assert_not_called()
        view.session_identifier.clear_cached_files.assert_not_called()
