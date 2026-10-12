"""
Testy přechodu dočasného identifikátoru dokumentu na trvalý a zápisu dokumentu (issue #4291).

Hlídají, že archivace používá sdíleného pomocníka ``Dokument.set_permanent_identificator``, že pomocník
při vyčerpání identifikátorů ohlásí chybu přes Fedora transakci a že neúspěšná kontrola kontejneru
při zápisu dokumentu zobrazí hlášku a zruší transakci. Databáze se nepoužívá – dotazy jsou nahrazeny mockem.
"""

from unittest import mock

from core.constants import D_STAV_ODESLANY, IDENTIFIKATOR_DOCASNY_PREFIX
from core.exceptions import MaximalIdentNumberError
from core.message_constants import MAXIMUM_IDENT_DOSAZEN, ZAZNAM_SE_NEPOVEDLO_VYTVORIT
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory, SimpleTestCase


def _uzivatel():
    """
    Vytvoří přihlášeného uživatele pro dekorátor ``login_required``.

    :return: Mock uživatele s nastaveným příznakem přihlášení.
    """
    return mock.Mock(is_authenticated=True)


class SetPermanentIdentificatorTest(SimpleTestCase):
    """Testy metody :meth:`dokument.models.Dokument.set_permanent_identificator`."""

    def _zavolej(self, dokument, transakce):
        """
        Zavolá pomocníka s náhradními parametry.

        :param dokument: Náhradní dokument.
        :param transakce: Náhradní Fedora transakce.
        :return: Návratová hodnota pomocníka.
        """
        from dokument.models import Dokument

        return Dokument.set_permanent_identificator(dokument, mock.Mock(), mock.Mock(), transakce)

    def test_docasny_ident_se_ztrvali(self):
        """Dočasný identifikátor se nahradí trvalým a dokument se uloží."""
        dokument = mock.Mock(ident_cely=f"{IDENTIFIKATOR_DOCASNY_PREFIX}M-9000001")
        self.assertIsNone(self._zavolej(dokument, mock.Mock()))
        dokument.set_permanent_ident_cely.assert_called_once()
        dokument.save.assert_called_once()

    def test_trvaly_ident_zustava(self):
        """Dokument s trvalým identifikátorem se nemění."""
        dokument = mock.Mock(ident_cely="M-TX-202500001")
        self.assertIsNone(self._zavolej(dokument, mock.Mock()))
        dokument.set_permanent_ident_cely.assert_not_called()

    @mock.patch("dokument.views.get_detail_json_view", return_value="/detail")
    def test_vycerpani_identu_ohlasi_chybu_pres_transakci(self, _detail):
        """
        Při vyčerpání identifikátorů se transakci nastaví chybová hláška a transakce se zruší.

        :param _detail: Mock funkce ``get_detail_json_view``, aby se nesestavovala skutečná URL.
        """
        dokument = mock.Mock(ident_cely=f"{IDENTIFIKATOR_DOCASNY_PREFIX}M-9000001")
        dokument.set_permanent_ident_cely.side_effect = MaximalIdentNumberError(9999)
        transakce = mock.Mock(error_message=None)
        odpoved = self._zavolej(dokument, transakce)
        self.assertIsInstance(odpoved, JsonResponse)
        self.assertEqual(odpoved.status_code, 403)
        self.assertEqual(transakce.error_message, MAXIMUM_IDENT_DOSAZEN)
        transakce.rollback_transaction.assert_called_once()
        dokument.save.assert_not_called()


class ArchivovatTest(SimpleTestCase):
    """Testy pohledu :func:`dokument.views.archivovat`."""

    def _post(self, dokument):
        """
        Odešle POST na archivaci s náhradním dokumentem.

        :param dokument: Náhradní dokument vrácený místo dotazu do databáze.
        :return: Odpověď pohledu.
        """
        from dokument import views

        request = RequestFactory().post("/dokument/archivovat/X")
        request.user = _uzivatel()
        with (
            mock.patch.object(views, "get_object_or_404", return_value=dokument),
            mock.patch.object(views, "check_stav_changed", return_value=False),
            mock.patch.object(views.transaction, "atomic"),
            mock.patch.object(views, "get_detail_json_view", return_value="/detail"),
        ):
            return views.archivovat(request, dokument.ident_cely)

    def test_pouziva_sdileneho_pomocnika(self):
        """Archivace ztrvalí identifikátor přes sdíleného pomocníka a při jeho chybě skončí."""
        dokument = mock.Mock(ident_cely=f"{IDENTIFIKATOR_DOCASNY_PREFIX}M-9000001", stav=D_STAV_ODESLANY)
        dokument.casti.all.return_value = []
        chyba = JsonResponse({"redirect": "/detail"}, status=403)
        with mock.patch("dokument.views.Dokument.set_permanent_identificator", return_value=chyba) as pomocnik:
            odpoved = self._post(dokument)
        pomocnik.assert_called_once()
        self.assertIs(pomocnik.call_args.args[0], dokument)
        self.assertIs(odpoved, chyba)
        dokument.set_archivovany.assert_not_called()


class ZapsatCheckContainerTest(SimpleTestCase):
    """Testy větve neúspěšné kontroly kontejneru v pohledu :func:`dokument.views.zapsat`."""

    def test_existujici_kontejner_zobrazi_hlasku_a_zrusi_transakci(self):
        """Pokud kontejner ve Fedoře existuje, uživatel dostane hlášku a transakce se zruší."""
        from dokument import views

        request = RequestFactory().post("/dokument/zapsat")
        request.user = _uzivatel()
        transakce = mock.Mock()
        form = mock.MagicMock()
        form.is_valid.return_value = True
        form.cleaned_data = {}
        form.save.return_value.create_transaction.return_value = transakce
        with (
            mock.patch.object(views, "get_required_fields_dokument", return_value=[]),
            mock.patch.object(views, "check_permissions", return_value=False),
            mock.patch.object(views, "get_region_zaznamu", return_value=None),
            mock.patch.object(views, "EditDokumentForm", return_value=form),
            mock.patch.object(views.Heslar.objects, "get"),
            mock.patch.object(views, "get_temp_dokument_ident", return_value="X-M-9000001"),
            mock.patch.object(
                views.FedoraRepositoryConnector, "check_container_deleted_or_not_exists", return_value=False
            ),
            mock.patch.object(views, "RegionForm"),
            mock.patch.object(views, "get_hierarchie_dokument_typ"),
            mock.patch.object(views, "render", return_value=HttpResponse()),
            mock.patch.object(views.messages, "add_message") as add_message,
        ):
            views.zapsat(request)
        add_message.assert_called_once_with(request, views.messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)
        transakce.rollback_transaction.assert_called_once()
        form.save.return_value.save.assert_not_called()
