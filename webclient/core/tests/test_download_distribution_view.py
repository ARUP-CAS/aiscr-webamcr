"""
Testy stahování alternativních distribucí souboru přes ``core.views.DownloadFile`` (issue #3527).

Pokrývají hlídání názvu distribuce proti seznamu dostupných distribucí souboru, průchod
víceúrovňového názvu URL routou a zachování původního chování při stahování bez distribuce.
Testy nepotřebují databázi ani běžící Fedoru – využívají mock ``Soubor`` a ``RequestFactory``.
"""

from unittest import mock

from core.views import DownloadFile
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse

TYP_VAZBY = "dokument"
IDENT_CELY = "C-DL-202500001"
SOUBOR_PK = 5


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
        path = "/soubor/stahnout/{}/{}/{}".format(TYP_VAZBY, IDENT_CELY, SOUBOR_PK)
        if distribution:
            path = "{}/{}".format(path, distribution)
        request = RequestFactory().get(path)
        request.user = mock.Mock(is_authenticated=True, pk=1)
        return request

    def _call_view(self, soubor, distribution=None):
        """Zavolá ``DownloadFile.get`` s mocknutým souborem a vazbou.

        :param soubor: Mock ``Soubor`` vracený z ``get_object_or_404``.
        :param distribution: Název distribuce předaný z URL.
        :return: Odpověď pohledu.
        """
        kwargs = {"distribution": distribution} if distribution is not None else {}
        with mock.patch("core.views.get_object_or_404", return_value=soubor), mock.patch(
            "core.views.check_soubor_vazba"
        ):
            return DownloadFile().get(self._request(distribution), TYP_VAZBY, IDENT_CELY, SOUBOR_PK, **kwargs)

    def test_available_distribution_is_returned(self):
        """Distribuce uvedená mezi dostupnými se stáhne z repozitáře."""
        soubor = self._soubor(available=("orig", "ocr"))

        response = self._call_view(soubor, distribution="ocr")

        self.assertIs(response, mock.sentinel.distribution_content)
        soubor.get_distribution_response.assert_called_once_with("ocr")

    def test_unavailable_distribution_raises_404_without_touching_repository(self):
        """Distribuce mimo seznam dostupných musí skončit 404 a vůbec se nedotknout Fedory.

        Název přichází přímo z URL, takže bez této kontroly by adresoval libovolný kontejner
        pod souborem — včetně těch, které soubor uživateli nenabízí.
        """
        soubor = self._soubor(available=("orig", "ocr"))

        with self.assertRaises(Http404):
            self._call_view(soubor, distribution="paradata")

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

    def test_nested_distribution_name_is_routed_and_returned(self):
        """Víceúrovňový název distribuce projde URL routou i kontrolou dostupnosti."""
        soubor = self._soubor(available=("orig", "ocr/alto-xml"))

        response = self._call_view(soubor, distribution="ocr/alto-xml")

        self.assertIs(response, mock.sentinel.distribution_content)
        soubor.get_distribution_response.assert_called_once_with("ocr/alto-xml")

    def test_distribution_url_preserves_slashes(self):
        """URL routa pro distribuci nesmí lomítka v názvu enkódovat — používá ``<path:...>``."""
        url = reverse(
            "core:download_file_distribution",
            kwargs={
                "typ_vazby": TYP_VAZBY,
                "ident_cely": IDENT_CELY,
                "pk": SOUBOR_PK,
                "distribution": "ocr/alto-xml",
            },
        )

        self.assertTrue(url.endswith("/{}/ocr/alto-xml".format(SOUBOR_PK)), url)

    def test_anonymous_user_is_redirected_to_login(self):
        """Nepřihlášený uživatel se ke stažení distribuce nedostane."""
        request = self._request(distribution="ocr")
        request.user = mock.Mock(is_authenticated=False)

        response = DownloadFile.as_view()(
            request, typ_vazby=TYP_VAZBY, ident_cely=IDENT_CELY, pk=SOUBOR_PK, distribution="ocr"
        )

        self.assertEqual(response.status_code, 302)
