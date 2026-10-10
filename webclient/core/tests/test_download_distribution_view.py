"""
Testy stahování alternativních distribucí souboru přes ``core.views.DownloadFile`` (issue #3527).

Pokrývají hlídání názvu distribuce proti seznamu dostupných distribucí souboru, předání
víceúrovňového názvu GET parametrem ``distribution``, zachování původního chování při stahování
bez distribuce a uplatnění stejných oprávnění jako u běžného stažení (``PermissionMiddleware``).
Testy nepotřebují databázi ani běžící Fedoru – využívají mock ``Soubor`` a ``RequestFactory``.
"""

from unittest import mock

from core.middleware import PermissionMiddleware
from core.views import DownloadFile
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve, reverse

TYP_VAZBY = "dokument"
IDENT_CELY = "C-DL-202500001"
SOUBOR_PK = 5
# Route of the standard download; its permission rows must also cover distribution downloads.
DOWNLOAD_FILE_ROUTE = "soubor/stahnout/<str:typ_vazby>/<str:ident_cely>/<int:pk>"


class DownloadDistributionViewTest(SimpleTestCase):
    """Testy pro stahování distribucí přes ``DownloadFile``."""

    def _soubor(self, available=("orig", "ocr"), repository_uuid="uuid-1"):
        """Vytvoří mock ``Soubor`` se seznamem dostupných distribucí.

        :param available: Názvy distribucí, které soubor nabízí ke stažení.
        :param repository_uuid: UUID souboru ve Fedoře; ``None`` znamená soubor mimo repozitář.
        :return: Mock nahrazující ``Soubor``.
        """
        soubor = mock.Mock()
        soubor.repository_uuid = repository_uuid
        soubor.small_thumbnail = None
        soubor.large_thumbnail = None
        soubor.content_file_response = mock.sentinel.original_content
        soubor.available_distributions.return_value = list(available)
        soubor.get_distribution_response.return_value = mock.sentinel.distribution_content
        return soubor

    def _request(self, distribution=None):
        """Sestaví GET request na stažení souboru, případně jeho distribuce.

        :param distribution: Název distribuce; ``None`` znamená stažení původního obsahu.
        :return: Request s přihlášeným uživatelem.
        """
        path = reverse("core:download_file", kwargs={"typ_vazby": TYP_VAZBY, "ident_cely": IDENT_CELY, "pk": SOUBOR_PK})
        query = {"distribution": distribution} if distribution else {}
        request = RequestFactory().get(path, query)
        request.user = mock.Mock(is_authenticated=True, pk=1)
        return request

    def _call_view(self, soubor, distribution=None):
        """Zavolá ``DownloadFile.get`` s mocknutým souborem a vazbou.

        :param soubor: Mock ``Soubor`` vracený z ``get_object_or_404``.
        :param distribution: Název distribuce předaný GET parametrem ``distribution``.
        :return: Odpověď pohledu.
        """
        with mock.patch("core.views.get_object_or_404", return_value=soubor), mock.patch(
            "core.views.check_soubor_vazba"
        ):
            return DownloadFile().get(self._request(distribution), TYP_VAZBY, IDENT_CELY, SOUBOR_PK)

    def test_available_distribution_is_returned(self):
        """Distribuce uvedená mezi dostupnými se stáhne z repozitáře."""
        soubor = self._soubor(available=("orig", "ocr"))

        response = self._call_view(soubor, distribution="ocr")

        self.assertIs(response, mock.sentinel.distribution_content)
        soubor.get_distribution_response.assert_called_once_with("ocr")

    def test_unavailable_distribution_raises_404_without_touching_repository(self):
        """Distribuce mimo seznam dostupných musí skončit 404 a vůbec se nedotknout Fedory.

        Název přichází přímo z GET parametru, takže bez této kontroly by adresoval libovolný kontejner
        pod souborem — včetně těch, které soubor uživateli nenabízí.
        """
        soubor = self._soubor(available=("orig", "ocr"))

        with self.assertRaises(Http404):
            self._call_view(soubor, distribution="paradata")

        soubor.get_distribution_response.assert_not_called()

    def test_thumbnail_container_raises_404(self):
        """Náhled se přes tuto routu stáhnout nedá — ``available_distributions`` ho nenabízí.

        Náhledy mají vlastní endpointy (``core:download_thumbnail``,
        ``core:download_thumbnail_large``); zde se ověřuje, že je gate na seznam dostupných
        distribucí odmítne i přesto, že jejich kontejner ve Fedoře existuje.
        """
        soubor = self._soubor(available=("orig", "ocr"))

        with self.assertRaises(Http404):
            self._call_view(soubor, distribution="thumb")

        soubor.get_distribution_response.assert_not_called()

    def test_distribution_of_file_outside_repository_raises_404(self):
        """Soubor bez UUID ve Fedoře nesmí nabídnout ke stažení žádnou distribuci."""
        soubor = self._soubor(available=("orig", "ocr"), repository_uuid=None)

        with self.assertRaises(Http404):
            self._call_view(soubor, distribution="ocr")

        soubor.get_distribution_response.assert_not_called()

    def test_unreadable_distribution_raises_404(self):
        """Pokud se obsah distribuce nepodaří načíst, pohled vrátí 404 místo prázdné odpovědi."""
        soubor = self._soubor(available=("orig", "ocr"))
        soubor.get_distribution_response.return_value = None

        with self.assertRaises(Http404):
            self._call_view(soubor, distribution="ocr")

    def test_download_without_distribution_returns_original_content(self):
        """Stažení bez názvu distribuce musí zachovat původní chování pohledu."""
        soubor = self._soubor()

        response = self._call_view(soubor)

        self.assertIs(response, mock.sentinel.original_content)
        soubor.get_distribution_response.assert_not_called()

    def test_nested_distribution_name_is_passed_and_returned(self):
        """Víceúrovňový název distribuce projde GET parametrem i kontrolou dostupnosti."""
        soubor = self._soubor(available=("orig", "ocr/alto-xml"))

        response = self._call_view(soubor, distribution="ocr/alto-xml")

        self.assertIs(response, mock.sentinel.distribution_content)
        soubor.get_distribution_response.assert_called_once_with("ocr/alto-xml")

    def test_distribution_query_parameter_preserves_slashes(self):
        """Víceúrovňový název dorazí do pohledu z GET parametru beze změny, včetně lomítek."""
        request = self._request(distribution="ocr/alto-xml")

        self.assertEqual(request.GET.get("distribution"), "ocr/alto-xml")

    def test_anonymous_user_is_redirected_to_login(self):
        """Nepřihlášený uživatel se ke stažení distribuce nedostane."""
        request = self._request(distribution="ocr")
        request.user = mock.Mock(is_authenticated=False)

        response = DownloadFile.as_view()(request, typ_vazby=TYP_VAZBY, ident_cely=IDENT_CELY, pk=SOUBOR_PK)

        self.assertEqual(response.status_code, 302)


class DownloadDistributionPermissionTest(SimpleTestCase):
    """Testy, že stažení distribuce podléhá stejným oprávněním jako běžné stažení souboru.

    ``PermissionMiddleware`` hledá oprávnění podle routy (``resolver.route``) a routu bez
    záznamů v oprávněních propustí. Distribuce se proto vybírá GET parametrem na routě
    ``download_file``, ke které už oprávnění ``soubor_stahnout_*`` existují.
    """

    def _process_view(self, distribution, allowed):
        """Projde požadavek na stažení distribuce přes ``PermissionMiddleware.process_view``.

        :param distribution: Název distribuce v GET parametru ``distribution``.
        :param allowed: Výsledek ``check_concrete_permission`` jediného nalezeného oprávnění.
        :return: Dvojice (mock ``Permissions.objects.filter``, mock nalezeného oprávnění).
        :raises PermissionDenied: Pokud oprávnění požadavek zamítne.
        """
        path = reverse("core:download_file", kwargs={"typ_vazby": TYP_VAZBY, "ident_cely": IDENT_CELY, "pk": SOUBOR_PK})
        request = RequestFactory().get(path, {"distribution": distribution})
        request.user = mock.Mock(is_authenticated=True, hlavni_role=mock.sentinel.role)
        request.resolver_match = resolve(request.path)
        permission = mock.Mock()
        permission.check_concrete_permission.return_value = allowed
        permission_set = mock.MagicMock()
        permission_set.count.return_value = 1
        permission_set.__iter__.return_value = iter([permission])
        with mock.patch("core.models.Permissions.objects.filter", return_value=permission_set) as filter_mock:
            middleware = PermissionMiddleware(get_response=mock.Mock())
            middleware.process_view(request, DownloadFile.as_view(), (), request.resolver_match.kwargs)
        return filter_mock, permission

    def test_distribution_request_resolves_to_standard_download_route(self):
        """Požadavek na distribuci se vyhodnotí na stejné routě jako běžné stažení souboru."""
        path = reverse("core:download_file", kwargs={"typ_vazby": TYP_VAZBY, "ident_cely": IDENT_CELY, "pk": SOUBOR_PK})

        match = resolve(path)

        self.assertEqual(match.url_name, "download_file")
        self.assertEqual(match.route, DOWNLOAD_FILE_ROUTE)

    def test_standard_download_permissions_are_looked_up(self):
        """Middleware hledá oprávnění běžného stažení a ověřuje je vůči identu záznamu."""
        filter_mock, permission = self._process_view("ocr/alto-xml", allowed=True)

        filter_mock.assert_called_once_with(
            main_role=mock.sentinel.role, address_in_app=DOWNLOAD_FILE_ROUTE, action__endswith=TYP_VAZBY
        )
        permission.check_concrete_permission.assert_called_once_with(mock.ANY, IDENT_CELY, None)

    def test_distribution_download_is_denied_without_download_permission(self):
        """Bez oprávnění k běžnému stažení nelze stáhnout ani alternativní distribuci."""
        with self.assertRaises(PermissionDenied):
            self._process_view("ocr/alto-xml", allowed=False)

    def test_original_download_via_parameter_is_denied_without_download_permission(self):
        """Ani ``?distribution=orig`` neobejde oprávnění k běžnému stažení původního souboru."""
        with self.assertRaises(PermissionDenied):
            self._process_view("orig", allowed=False)
