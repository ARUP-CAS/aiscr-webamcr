"""
Testy shody mezi ``_FastFedoraWriter`` a :class:`FedoraRepositoryConnector`.

``generate_metadata_fast`` zapisuje do Fedory vlastní, zrychlenou cestou a přitom musí
produkovat stejné RDF a používat stejná Fedora model names jako běžný zápis z aplikace -
jinak by se záznamy vzniklé migrací lišily od záznamů vzniklých v provozu a nic by si
toho nevšimlo (závěrečná kontrola konzistence porovnává jen identifikátory a navíc se
opírá o tytéž názvy, takže by ohlásila falešnou shodu). Dřív tuhle shodu držela pouze
věta v docstringu; tenhle modul ji hlídá testy (review PR #4262).

Data se odebírají tak, jak by odešla na drát - odesílací metoda se nahradí záchytem,
takže se testuje reálné chování obou implementací, ne podoba jejich zdrojáku.
"""

import ast
import inspect
from types import SimpleNamespace
from unittest import mock

from core.management.commands.generate_metadata_fast import _FastFedoraWriter, _get_schema_by_name
from core.repository_connector import FedoraRepositoryConnector, FedoraRequestType
from django.test import SimpleTestCase, override_settings

SERVER_NAME = "AMCR-TEST"
USER_IDENT = "U-000322"
IDENT_CELY = "C-202300001"
MODEL_NAME = "projekt"


@override_settings(
    FEDORA_SERVER_NAME=SERVER_NAME,
    FEDORA_USER="u",
    FEDORA_USER_PASSWORD="p",
    FEDORA_ADMIN_USER="au",
    FEDORA_ADMIN_USER_PASSWORD="ap",
)
class CreatorRdfParityTest(SimpleTestCase):
    """Porovnává creator RDF, SPARQL update a link turtle obou implementací."""

    def _writer(self):
        """
        Vytvoří ``_FastFedoraWriter`` bez síťového spojení.

        :return: Instance ``_FastFedoraWriter``.
        """
        return _FastFedoraWriter(f"https://fedora.example/rest/{SERVER_NAME}", USER_IDENT)

    def _connector(self):
        """
        Vytvoří ``FedoraRepositoryConnector`` s obejitým ``__init__`` (nepotřebuje DB ani transakci).

        :return: Instance ``FedoraRepositoryConnector`` s doplněnými atributy, které
            testované metody čtou.
        """
        connector = FedoraRepositoryConnector.__new__(FedoraRepositoryConnector)
        connector.user = USER_IDENT
        connector.record = SimpleNamespace(ident_cely=IDENT_CELY)
        connector.transaction_uid = None
        connector.transaction = None
        connector.skip_container_check = True
        connector.restored_container = False
        return connector

    @staticmethod
    def _odeslana_data(connector, volani):
        """
        Zachytí ``data`` předaná do ``_send_request`` při zavolání ``volani``.

        :param connector: Instance ``FedoraRepositoryConnector``.
        :param volani: Funkce bez argumentů, která spustí testovanou metodu.
        :return: Seznam dvojic ``(request_type, data)`` v pořadí odeslání.
        """
        zachyceno = []

        def zachyt(url, request_type, headers=None, data=None, **kwargs):
            zachyceno.append((request_type, data))

        with mock.patch.object(connector, "_send_request", side_effect=zachyt), mock.patch.object(
            connector, "_get_request_url", return_value="https://fedora.example/rest/dummy"
        ):
            volani()
        return zachyceno

    def test_creator_turtle_je_shodny(self):
        """Turtle fragment s ``dcterms:creator`` musí být shodný s tím z ``_create_container``."""
        connector = self._connector()
        odeslane = self._odeslana_data(connector, connector._create_container)
        podle_typu = dict(odeslane)
        self.assertIn(FedoraRequestType.CREATE_CONTAINER, podle_typu)
        self.assertEqual(self._writer()._creator_rdf(), podle_typu[FedoraRequestType.CREATE_CONTAINER])

    def test_creator_sparql_update_je_shodny(self):
        """SPARQL update nastavující ``dcterms:creator`` musí být shodný s ``_get_creator_rdf_data``."""
        self.assertEqual(self._writer()._creator_sparql_update(), self._connector()._get_creator_rdf_data())

    def test_link_turtle_je_shodny(self):
        """Turtle fragment link resource (``ore:proxyFor`` + ``dcterms:creator``) musí být shodný."""
        connector = self._connector()
        odeslane = self._odeslana_data(connector, connector.create_link)
        self.assertEqual(len(odeslane), 1)
        ocekavane = odeslane[0][1]

        writer = self._writer()
        zachyceno = []

        def zachyt(method, url, headers, data, tx_url=None):
            zachyceno.append((url, data))
            return mock.Mock()

        with mock.patch.object(writer, "_request", side_effect=zachyt), mock.patch.object(writer, "_zkontroluj_slug"):
            writer.create_member_link(IDENT_CELY, MODEL_NAME)

        link_data = [data for url, data in zachyceno if "/member" in url]
        self.assertEqual(len(link_data), 1, f"očekáván jeden zápis link resource, zachyceno: {zachyceno}")
        self.assertEqual(link_data[0], ocekavane)

    def test_create_record_uz_nezapisuje_link(self):
        """
        ``create_record`` nesmí sahat na ``/model/{model}/member``.

        Je to podmínka toho, aby jedna transakce měla nejvýš jednoho sdíleného rodiče
        v containment indexu, což vylučuje deadlock (viz ``create_member_link``).
        """
        writer = self._writer()
        zachyceno = []

        def zachyt(method, url, headers, data, tx_url=None):
            zachyceno.append(url)
            return mock.Mock()

        with mock.patch.object(writer, "_request", side_effect=zachyt), mock.patch.object(writer, "_zkontroluj_slug"):
            writer.create_record(IDENT_CELY, b"<xml/>", "0" * 128)

        self.assertEqual(
            [u for u in zachyceno if "/member" in u],
            [],
            f"create_record zapsal do /member, tím by se vrátil deadlock: {zachyceno}",
        )


class ModelNameParityTest(SimpleTestCase):
    """
    Hlídá, že Fedora model names migrace odpovídají těm, které používá aplikace.

    ``generate_metadata_fast`` je odvozuje z ``DocumentGenerator._get_schema_dict()``,
    zatímco aplikace má vlastní ruční tabulku v ``FedoraRepositoryConnector._get_model_name``.
    Kdyby se rozešly, migrace by zapsala ``/model/{jméno}/member`` linky pod názvem, na který
    se aplikace nikdy nezeptá - a ``_zkontroluj_konzistenci`` by přitom hlásila shodu, protože
    porovnává proti témže odvozeným názvům (review PR #4262).
    """

    @staticmethod
    def _model_name_z_connectoru(nazev_tridy):
        """
        Zavolá ``FedoraRepositoryConnector._get_model_name`` pro daný název třídy.

        Metoda čte jen ``self.record.__class__.__name__``, takže stačí atrapa se
        správným názvem třídy - není potřeba DB ani instance modelu.

        :param nazev_tridy: Název modelové třídy (např. ``"Projekt"``).
        :return: Fedora model name, nebo ``None`` když ho tabulka nezná.
        """
        connector = FedoraRepositoryConnector.__new__(FedoraRepositoryConnector)
        connector.record = type(nazev_tridy, (), {})()
        return connector._get_model_name()

    def test_vsechny_modely_maji_shodne_fedora_name(self):
        """Pro každý generovaný model musí obě strany dát stejné Fedora model name."""
        schema = _get_schema_by_name()
        self.assertGreater(len(schema), 0)
        rozdily = {}
        for nazev_tridy, (_trida, fedora_name) in schema.items():
            z_connectoru = self._model_name_z_connectoru(nazev_tridy)
            if z_connectoru != fedora_name:
                rozdily[nazev_tridy] = (fedora_name, z_connectoru)
        self.assertEqual(
            rozdily,
            {},
            "Fedora model names se rozešly (model: generátor vs FedoraRepositoryConnector): " f"{rozdily}",
        )

    def test_connector_nezna_zadny_model_navic(self):
        """
        Tabulka v ``_get_model_name`` nesmí obsahovat model, který migrace negeneruje.

        Opačný směr než test výše: název, který zná jen aplikace, by znamenal, že se
        na něj někdo dotazuje, ale migrace pod ním nic nezapsala. Klíče se čtou z AST
        metody - kdyby se přepsala do jiné podoby, test spadne a je to signál, že se
        na tuhle shodu musí někdo podívat.
        """
        strom = ast.parse(inspect.getsource(FedoraRepositoryConnector._get_model_name).lstrip())
        slovniky = [n for n in ast.walk(strom) if isinstance(n, ast.Dict)]
        self.assertEqual(
            len(slovniky),
            1,
            "V `_get_model_name` se nenašel právě jeden slovníkový literál - "
            "metoda se změnila, zkontroluj shodu mapování ručně a uprav tento test.",
        )
        klice_connectoru = {k.value for k in slovniky[0].keys if isinstance(k, ast.Constant)}
        self.assertEqual(len(klice_connectoru), len(slovniky[0].keys))
        self.assertEqual(
            klice_connectoru - set(_get_schema_by_name()),
            set(),
            "FedoraRepositoryConnector zná model(y), které generate_metadata_fast negeneruje.",
        )
