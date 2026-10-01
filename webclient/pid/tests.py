"""Testy aplikace PID."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import requests
from django.test import SimpleTestCase, TestCase
from heslar.hesla_dynamicka import DOKUMENT_RADA_DATA_3D
from pid.model_serializers import DokumentSerializer, dedup_geo_locations, frozenset_sort_key, sorted_unique
from pid.views import DoiAutocompleteView, WikiDataAutocompleteView


class DoiAutocompleteViewApiCallTest(TestCase):
    """Testy metody ``api_call`` třídy ``DoiAutocompleteView``."""

    @patch.object(DoiAutocompleteView, "_doi_item_exists", return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock)
    def test_title_search_returns_doi_wildcard_results_first(self, mock_doi, mock_title, mock_crossref, mock_exists):
        """
        Výsledky DOI wildcard dotazu jsou vráceny jako první.

        :param mock_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_title: Mock pro ``_api_call_data_cite``.
        :param mock_crossref: Mock pro ``_api_call_cross_ref_title``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        mock_doi.return_value = [["10.1/aaa", "Title A (10.1/aaa)"], ["10.1/bbb", "Title B (10.1/bbb)"]]

        results = DoiAutocompleteView.api_call("some title")

        self.assertEqual(results[0][0], "10.1/aaa")
        self.assertEqual(results[1][0], "10.1/bbb")
        mock_exists.assert_not_called()

    @patch.object(DoiAutocompleteView, "_doi_item_exists", return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock)
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock)
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock)
    def test_title_search_result_order_doi_then_title_then_crossref(
        self, mock_doi, mock_title, mock_crossref, mock_exists
    ):
        """
        Pořadí výsledků: DOI wildcard, DataCite název, CrossRef název.

        :param mock_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_title: Mock pro ``_api_call_data_cite``.
        :param mock_crossref: Mock pro ``_api_call_cross_ref_title``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        mock_doi.return_value = [["10.1/doi", "DOI result (10.1/doi)"]]
        mock_title.return_value = [["10.1/title", "Title result (10.1/title)"]]
        mock_crossref.return_value = [["10.1/crossref", "CrossRef result (10.1/crossref)"]]

        results = DoiAutocompleteView.api_call("enclosure Babina")

        self.assertEqual([r[0] for r in results], ["10.1/doi", "10.1/title", "10.1/crossref"])

    @patch.object(DoiAutocompleteView, "_doi_item_exists", return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock)
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock)
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock)
    def test_duplicates_are_removed_keeping_first_occurrence(self, mock_doi, mock_title, mock_crossref, mock_exists):
        """
        Duplicitní DOI jsou odstraněna; zachová se první výskyt.

        :param mock_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_title: Mock pro ``_api_call_data_cite``.
        :param mock_crossref: Mock pro ``_api_call_cross_ref_title``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        mock_doi.return_value = [["10.1/dup", "From DOI (10.1/dup)"]]
        mock_title.return_value = [["10.1/dup", "From Title (10.1/dup)"], ["10.1/unique", "Unique (10.1/unique)"]]
        mock_crossref.return_value = []

        results = DoiAutocompleteView.api_call("some title")

        dois = [r[0] for r in results]
        self.assertEqual(dois.count("10.1/dup"), 1)
        self.assertEqual(results[0], ["10.1/dup", "From DOI (10.1/dup)"])

    @patch.object(DoiAutocompleteView, "_doi_item_exists", return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_doi")
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock, return_value=[])
    def test_doi_format_input_uses_crossref_doi_path(
        self, mock_dc_doi, mock_dc_title, mock_cr_title, mock_cr_doi, mock_exists
    ):
        """
        Vstup ve formátu DOI volá ``_api_call_cross_ref_doi`` a přeskočí async volání.

        :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_dc_title: Mock pro ``_api_call_data_cite``.
        :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
        :param mock_cr_doi: Mock pro ``_api_call_cross_ref_doi``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        mock_cr_doi.return_value = [["10.1234/abc", "Found (10.1234/abc)"]]

        results = DoiAutocompleteView.api_call("10.1234/abc")

        mock_cr_doi.assert_called_once_with("10.1234/abc")
        mock_dc_doi.assert_not_called()
        self.assertEqual(results[0][0], "10.1234/abc")

    @patch.object(DoiAutocompleteView, "_doi_item_exists", return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_doi")
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock, return_value=[])
    def test_doi_format_with_no_crossref_result_falls_back_to_async(
        self, mock_dc_doi, mock_dc_title, mock_cr_title, mock_cr_doi, mock_exists
    ):
        """
        Pokud ``_api_call_cross_ref_doi`` vrátí prázdný seznam, provedou se async volání.

        :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_dc_title: Mock pro ``_api_call_data_cite``.
        :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
        :param mock_cr_doi: Mock pro ``_api_call_cross_ref_doi``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        mock_cr_doi.return_value = []

        DoiAutocompleteView.api_call("10.1234/unknown")

        mock_dc_doi.assert_called_once()

    @patch.object(DoiAutocompleteView, "_doi_item_exists")
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock, return_value=[])
    def test_doi_item_exists_prepended_when_exact_doi_not_in_results(
        self, mock_dc_doi, mock_dc_title, mock_cr_title, mock_exists
    ):
        """
        Pokud výsledky neobsahují přesné DOI, je zavoláno ``_doi_item_exists`` a výsledek přidán na začátek.

        :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_dc_title: Mock pro ``_api_call_data_cite``.
        :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        mock_exists.return_value = [["10.1234/exact", "10.1234/exact"]]

        results = DoiAutocompleteView.api_call("10.1234/exact")

        self.assertEqual(results[0][0], "10.1234/exact")
        mock_exists.assert_called_once_with("10.1234/exact")

    @patch.object(DoiAutocompleteView, "_doi_item_exists", return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock, return_value=[])
    def test_empty_query_returns_empty_list(self, mock_dc_doi, mock_dc_title, mock_cr_title, mock_exists):
        """
        Prázdný nebo jen mezerami tvořený dotaz vrátí prázdný seznam bez volání backendu.

        :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_dc_title: Mock pro ``_api_call_data_cite``.
        :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        results = DoiAutocompleteView.api_call("   ")

        self.assertEqual(results, [])
        mock_dc_doi.assert_not_called()
        mock_dc_title.assert_not_called()
        mock_cr_title.assert_not_called()
        mock_exists.assert_not_called()

    @patch.object(DoiAutocompleteView, "_doi_item_exists", return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_cross_ref_title", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite", new_callable=AsyncMock, return_value=[])
    @patch.object(DoiAutocompleteView, "_api_call_data_cite_doi", new_callable=AsyncMock, return_value=[])
    def test_none_query_returns_empty_list(self, mock_dc_doi, mock_dc_title, mock_cr_title, mock_exists):
        """
        ``None`` jako dotaz vrátí prázdný seznam bez volání backendu.

        :param mock_dc_doi: Mock pro ``_api_call_data_cite_doi``.
        :param mock_dc_title: Mock pro ``_api_call_data_cite``.
        :param mock_cr_title: Mock pro ``_api_call_cross_ref_title``.
        :param mock_exists: Mock pro ``_doi_item_exists``.
        """
        results = DoiAutocompleteView.api_call(None)

        self.assertEqual(results, [])
        mock_dc_doi.assert_not_called()
        mock_dc_title.assert_not_called()
        mock_cr_title.assert_not_called()
        mock_exists.assert_not_called()


class WikiDataAutocompleteViewApiCallTest(TestCase):
    """Testy metody ``api_call`` a pomocných metod třídy ``WikiDataAutocompleteView``."""

    @patch.object(WikiDataAutocompleteView, "_search_humans", new_callable=AsyncMock)
    @patch.object(WikiDataAutocompleteView, "_get_item_result")
    def test_exact_qid_routes_to_item_lookup(self, mock_item, mock_search):
        """
        Dotaz tvořený pouze identifikátorem ``Q`` se ověří přes ``_get_item_result``.

        :param mock_item: Mock pro ``_get_item_result``.
        :param mock_search: Mock pro ``_search_humans``.
        """
        mock_item.return_value = [["Q868", "Aristotelés (Q868)"]]

        results = WikiDataAutocompleteView.api_call(" Q868 ")

        self.assertEqual(results, [["Q868", "Aristotelés (Q868)"]])
        mock_item.assert_called_once_with("Q868")
        mock_search.assert_not_called()

    @patch.object(WikiDataAutocompleteView, "_search_humans", new_callable=AsyncMock, return_value=[])
    @patch.object(WikiDataAutocompleteView, "_get_item_result")
    def test_free_text_with_embedded_qid_routes_to_name_search(self, mock_item, mock_search):
        """
        Volný text obsahující ``Q`` s číslicemi se vyhledává podle jména, ne podle identifikátoru.

        :param mock_item: Mock pro ``_get_item_result``.
        :param mock_search: Mock pro ``_search_humans``.
        """
        WikiDataAutocompleteView.api_call("Aristoteles Q868")

        mock_item.assert_not_called()
        mock_search.assert_called_once()

    @patch.object(WikiDataAutocompleteView, "_search_humans", new_callable=AsyncMock)
    @patch.object(WikiDataAutocompleteView, "_get_item_result", return_value=[])
    def test_entity_url_routes_to_item_lookup(self, mock_item, mock_search):
        """
        URL entity Wikidata se převede na identifikátor a ověří přes ``_get_item_result``.

        :param mock_item: Mock pro ``_get_item_result``.
        :param mock_search: Mock pro ``_search_humans``.
        """
        WikiDataAutocompleteView.api_call("https://www.wikidata.org/entity/Q868")

        mock_item.assert_called_once_with("Q868")
        mock_search.assert_not_called()

    @patch.object(WikiDataAutocompleteView, "_search_humans", new_callable=AsyncMock)
    @patch.object(WikiDataAutocompleteView, "_get_item_result")
    def test_empty_query_returns_empty_list(self, mock_item, mock_search):
        """
        Prázdný dotaz vrátí prázdný seznam bez volání backendu.

        :param mock_item: Mock pro ``_get_item_result``.
        :param mock_search: Mock pro ``_search_humans``.
        """
        results = WikiDataAutocompleteView.api_call("")

        self.assertEqual(results, [])
        mock_item.assert_not_called()
        mock_search.assert_not_called()

    @patch.object(WikiDataAutocompleteView, "_search_humans", new_callable=AsyncMock)
    @patch.object(WikiDataAutocompleteView, "_get_item_result")
    def test_whitespace_only_query_returns_empty_list(self, mock_item, mock_search):
        """
        Dotaz tvořený jen mezerami vrátí prázdný seznam bez volání backendu.

        :param mock_item: Mock pro ``_get_item_result``.
        :param mock_search: Mock pro ``_search_humans``.
        """
        results = WikiDataAutocompleteView.api_call("   ")

        self.assertEqual(results, [])
        mock_item.assert_not_called()
        mock_search.assert_not_called()

    def test_search_language_request_error_returns_empty_list(self):
        """Chyba spojení při vyhledávání vrátí prázdný seznam místo výjimky."""
        client = SimpleNamespace(get=AsyncMock(side_effect=httpx.RequestError("boom")))

        results = asyncio.run(WikiDataAutocompleteView._search_language(client, "test", "cs"))

        self.assertEqual(results, [])

    def test_search_language_non_dict_payload_returns_empty_list(self):
        """Neslovníková JSON odpověď vyhledávání vrátí prázdný seznam místo výjimky."""
        response = SimpleNamespace(status_code=200, json=lambda: ["unexpected"])
        client = SimpleNamespace(get=AsyncMock(return_value=response))

        results = asyncio.run(WikiDataAutocompleteView._search_language(client, "test", "cs"))

        self.assertEqual(results, [])

    def test_item_is_human_request_error_returns_false(self):
        """Chyba spojení při ověření výroku ``P31`` se vyhodnotí jako ``False``."""
        client = SimpleNamespace(get=AsyncMock(side_effect=httpx.RequestError("boom")))

        result = asyncio.run(WikiDataAutocompleteView._item_is_human(client, "Q868"))

        self.assertFalse(result)

    @patch("pid.views.requests.get")
    def test_check_availability_raises_on_connection_error(self, mock_get):
        """Kontrola dostupnosti propaguje chybu spojení volajícímu.

        :param mock_get: Mock pro ``requests.get``.
        """
        mock_get.side_effect = requests.ConnectionError("boom")

        with self.assertRaises(requests.RequestException):
            WikiDataAutocompleteView.check_availability()

    @patch("pid.views.requests.get")
    def test_check_availability_raises_on_http_error(self, mock_get):
        """Kontrola dostupnosti vyhazuje výjimku při chybovém stavovém kódu.

        :param mock_get: Mock pro ``requests.get``.
        """
        response = requests.Response()
        response.status_code = 503
        mock_get.return_value = response

        with self.assertRaises(requests.RequestException):
            WikiDataAutocompleteView.check_availability()

    @patch("pid.views.requests.get")
    def test_check_availability_passes_on_success(self, mock_get):
        """Kontrola dostupnosti při úspěšné odpovědi nevyhazuje výjimku.

        :param mock_get: Mock pro ``requests.get``.
        """
        response = requests.Response()
        response.status_code = 200
        mock_get.return_value = response

        WikiDataAutocompleteView.check_availability()
        mock_get.assert_called_once()


class DedupGeoLocationsTest(SimpleTestCase):
    """
    Testy deterministického odstranění duplicit v ``geoLocations``.

    Původní implementace používala ``list(set(...))``. Iterační pořadí množiny závisí na hashích
    řetězců, které Python randomizuje pro každý proces, takže každý uWSGI i Celery worker
    generoval pro tentýž záznam jiné pořadí prvků v metadatech odesílaných do DataCite.
    """

    @staticmethod
    def _misto(nazev):
        """
        Sestaví lokalizaci obsahující pouze ``geoLocationPlace``.

        :param nazev: Textový popis polohy vkládaný do ``geoLocationPlace``.
        :return: Lokalizace ve tvaru ``frozenset`` odpovídajícím ``serialize_geom``.
        """
        return frozenset({"geoLocationPlace": nazev}.items())

    @staticmethod
    def _bod(nazev, sirka, delka):
        """
        Sestaví lokalizaci s popisem polohy i souřadnicemi.

        :param nazev: Textový popis polohy vkládaný do ``geoLocationPlace``.
        :param sirka: Zeměpisná šířka centroidu geometrie.
        :param delka: Zeměpisná délka centroidu geometrie.
        :return: Lokalizace ve tvaru ``frozenset`` odpovídajícím ``serialize_geom``.
        """
        return frozenset(
            {
                "geoLocationPlace": nazev,
                "geoLocationPoint": frozenset({"pointLatitude": sirka, "pointLongitude": delka}.items()),
            }.items()
        )

    def test_odstrani_duplicity(self):
        """Shodné lokalizace se ve výsledku objeví jen jednou."""
        misto = self._misto("Praha, Czech Republic")
        self.assertEqual(dedup_geo_locations([misto, misto, misto]), [{"geoLocationPlace": "Praha, Czech Republic"}])

    def test_poradi_je_pevne_dane(self):
        """
        Lokalizace jsou seřazené podle kanonického klíče, nikoli v pořadí množiny.

        Porovnání dvou volání v jednom procesu by regresi nezachytilo, protože ``list(set(...))``
        dává v rámci procesu pokaždé stejné pořadí. Test proto fixuje očekávané pořadí; se šesti
        prvky je šance, že se s ním pořadí množiny shoduje náhodou, 1 : 720.
        """
        mista = ["Praha", "Ostrava", "Brno", "Plzeň", "Olomouc", "Liberec"]
        vysledek = dedup_geo_locations([self._misto(m) for m in mista])
        self.assertEqual(
            [d["geoLocationPlace"] for d in vysledek],
            ["Brno", "Liberec", "Olomouc", "Ostrava", "Plzeň", "Praha"],
        )

    def test_poradi_lokalizaci_se_souradnicemi(self):
        """Shodné místo s různými souřadnicemi se řadí podle ``geoLocationPoint``."""
        vysledek = dedup_geo_locations(
            [
                self._bod("Praha", 50.1, 14.4),
                self._bod("Brno", 49.3, 16.7),
                self._bod("Brno", 49.2, 16.6),
            ]
        )
        self.assertEqual(
            [(d["geoLocationPlace"], d["geoLocationPoint"]["pointLatitude"]) for d in vysledek],
            [("Brno", 49.2), ("Brno", 49.3), ("Praha", 50.1)],
        )

    def test_vnorene_souradnice_jsou_prevedeny_na_slovnik(self):
        """Vnořený ``frozenset`` souřadnic je ve výstupu převeden na slovník."""
        vysledek = dedup_geo_locations([self._bod("Praha", 50.1, 14.4)])
        self.assertEqual(
            vysledek,
            [
                {
                    "geoLocationPlace": "Praha",
                    "geoLocationPoint": {"pointLatitude": 50.1, "pointLongitude": 14.4},
                }
            ],
        )

    def test_prazdny_vstup(self):
        """Prázdná kolekce vrátí prázdný seznam."""
        self.assertEqual(dedup_geo_locations([]), [])


class SortedUniqueTest(SimpleTestCase):
    """Testy deterministického odstranění duplicit v ``dates`` a ``subjects`` DataCite metadat."""

    @staticmethod
    def _datum(datum, typ):
        """
        Sestaví položku ``dates`` ve tvaru, v jakém ji skládají serializery.

        :param datum: Hodnota pole ``date``.
        :param typ: Hodnota pole ``dateType``.
        :return: Položka ve tvaru ``frozenset``.
        """
        return frozenset({"date": datum, "dateType": typ}.items())

    @staticmethod
    def _heslo(ident):
        """
        Sestaví předmětové heslo ve tvaru vraceném funkcí ``serialize_subject``.

        :param ident: Identifikátor hesla použitý jako ``subject``, ``classificationCode`` i v ``valueUri``.
        :return: Položka ve tvaru ``frozenset`` se stejnými klíči, jaké vrací ``serialize_subject``.
        """
        return frozenset(
            {
                "subject": ident,
                "valueUri": f"https://api.aiscr.cz/id/{ident}",
                "schemeUri": "https://api.aiscr.cz/id/",
                "subjectScheme": "AMCR",
                "lang": "en",
                "classificationCode": ident,
            }.items()
        )

    def test_poradi_dat_je_pevne_dane(self):
        """Data jsou seřazená podle hodnoty ``date``, nikoli v pořadí množiny."""
        polozky = [
            self._datum("2024-06-01", "Issued"),
            self._datum("2024-05-01", "Created"),
            self._datum("-5500/-4900", "Coverage"),
            self._datum("2024-05-20", "Submitted"),
            self._datum("2024-07-01", "Withdrawn"),
            self._datum("-1200/-800", "Coverage"),
        ]
        self.assertEqual(
            [dict(item)["date"] for item in sorted_unique(polozky)],
            ["-1200/-800", "-5500/-4900", "2024-05-01", "2024-05-20", "2024-06-01", "2024-07-01"],
        )

    def test_hesla_bez_duplicit_v_pevnem_poradi(self):
        """Opakovaná hesla z více komponent se objeví jednou a v pevně daném pořadí."""
        idents = ["HES-000123", "HES-000045", "HES-000900", "HES-000123", "HES-000001", "HES-000450", "HES-000045"]
        self.assertEqual(
            [dict(item)["classificationCode"] for item in sorted_unique(self._heslo(i) for i in idents)],
            ["HES-000001", "HES-000045", "HES-000123", "HES-000450", "HES-000900"],
        )

    def test_klic_rozlisi_hodnotu_s_oddelovacem(self):
        """Hodnota obsahující znaky oddělovače nedá stejný klíč jako jiná kombinace dvojic."""
        a = frozenset({"a": "b", "c": "d"}.items())
        b = frozenset({"a": "b|c=d"}.items())
        self.assertNotEqual(frozenset_sort_key(a), frozenset_sort_key(b))

    def test_klic_rozlisi_typ_hodnoty(self):
        """Číslo a stejně vypadající text dají různé klíče."""
        self.assertNotEqual(
            frozenset_sort_key(frozenset({"x": 1}.items())), frozenset_sort_key(frozenset({"x": "1"}.items()))
        )

    def test_prazdne_heslo_zustane_pro_filtraci_volajicim(self):
        """Prázdný ``frozenset`` (heslo ``None``) se neodstraňuje; filtruje ho až volající přes ``if item``."""
        vysledek = [dict(item) for item in sorted_unique([frozenset(), self._heslo("HES-1")]) if item]
        self.assertEqual(vysledek, [dict(self._heslo("HES-1"))])


class GetFormatsTest(SimpleTestCase):
    """Testy deterministického pořadí prvků ``formats`` v metadatech dokumentu."""

    def _formats(self, mimetypy, format_3d=None):
        """
        Zavolá ``_get_formats`` nad serializerem s podvrženými soubory.

        :param mimetypy: Seznam mimetypů souborů navázaných na dokument.
        :param format_3d: Formát z ``extra_data`` 3D dokumentu; ``None`` znamená dokument jiné řady.
        :return: Seznam formátů vrácený metodou ``_get_formats``.
        """
        soubory = [SimpleNamespace(mimetype=mimetype) for mimetype in mimetypy]
        queryset = SimpleNamespace(exists=lambda: bool(soubory), all=lambda: soubory)
        serializer = DokumentSerializer.__new__(DokumentSerializer)
        if format_3d is None:
            # Sentinel místo None: DOKUMENT_RADA_DATA_3D je None, když selže načtení z heslaře
            # (např. prázdná testovací DB), a pk=None by se pak omylem vyhodnotilo jako 3D řada.
            serializer.record = SimpleNamespace(rada=SimpleNamespace(pk=object()))
        else:
            serializer.record = SimpleNamespace(
                rada=SimpleNamespace(pk=DOKUMENT_RADA_DATA_3D),
                extra_data=SimpleNamespace(format=SimpleNamespace(heslo_en=format_3d)),
            )
        serializer._get_soubory_queryset = lambda: queryset
        return serializer._get_formats()

    def test_formaty_jsou_serazene(self):
        """Mimetypy jsou vráceny abecedně seřazené, nikoli v pořadí množiny."""
        self.assertEqual(
            self._formats(
                ["text/plain", "image/jpeg", "application/zip", "application/pdf", "image/png", "image/tiff"]
            ),
            ["application/pdf", "application/zip", "image/jpeg", "image/png", "image/tiff", "text/plain"],
        )

    def test_format_3d_je_zarazen_do_serazeni(self):
        """Formát 3D dokumentu se řadí spolu s mimetypy a nepřipojuje se na konec."""
        self.assertEqual(
            self._formats(["image/jpeg", "text/plain"], format_3d="model/obj"),
            ["image/jpeg", "model/obj", "text/plain"],
        )

    def test_format_3d_se_neopakuje(self):
        """Formát 3D dokumentu shodný s mimetypem souboru se ve ``formats`` objeví jen jednou."""
        self.assertEqual(self._formats(["model/obj"], format_3d="model/obj"), ["model/obj"])

    def test_duplicitni_mimetypy_se_neopakuji(self):
        """Více souborů se shodným mimetypem se ve ``formats`` objeví jen jednou."""
        self.assertEqual(self._formats(["application/pdf", "application/pdf"]), ["application/pdf"])

    def test_bez_souboru_vraci_prazdny_seznam(self):
        """Dokument bez souborů nemá žádné formáty."""
        self.assertEqual(self._formats([]), [])
