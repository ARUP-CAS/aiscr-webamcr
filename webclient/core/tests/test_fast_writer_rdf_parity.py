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

Connector má tentýž turtle fragment rozepsaný na víc místech (čtyřikrát creator, třikrát
link). ``CreatorRdfParityTest`` spouští ta místa, která se obejdou bez DB;
``PocetKopiiTurtleTest`` navíc hlídá, že žádná další kopie nepřibyla - nová kopie by se
jinak mohla rozejít, aniž by o tom kterýkoli test věděl (review PR #4262).
"""

import ast
import inspect
import io
from types import SimpleNamespace
from unittest import mock

from core.management.commands.generate_metadata_fast import _FastFedoraWriter, _get_schema_by_name
from core.repository_connector import FedoraRepositoryConnector, FedoraRequestType
from django.test import SimpleTestCase, override_settings

SERVER_NAME = "AMCR-TEST"
USER_IDENT = "U-000322"
IDENT_CELY = "C-202300001"
#: Ident záznamu tam, kde se turtle skládá z *jiného* identu než z ``record.ident_cely``
#: (``record_ident_change`` bere starý ident) - ať se pozná, že se vzal ten správný.
JINY_IDENT = "C-202399999"
MODEL_NAME = "projekt"

#: Podřetězec, podle kterého se ve zdrojáku connectoru poznává creator turtle fragment.
MARKER_CREATOR = "@prefix dcterms: <http://purl.org/dc/terms/> . <> dcterms:creator"
#: Totéž pro link (proxy) turtle fragment.
MARKER_LINK = "<> ore:proxyFor <info:fedora/"


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

    def _connector(self, ident_cely=IDENT_CELY):
        """
        Vytvoří ``FedoraRepositoryConnector`` s obejitým ``__init__`` (nepotřebuje DB ani transakci).

        :param ident_cely: Identifikátor, který má mít ``connector.record``.
        :return: Instance ``FedoraRepositoryConnector`` s doplněnými atributy, které
            testované metody čtou.
        """
        connector = FedoraRepositoryConnector.__new__(FedoraRepositoryConnector)
        connector.user = USER_IDENT
        connector.record = SimpleNamespace(ident_cely=ident_cely)
        connector.transaction_uid = None
        connector.transaction = None
        connector.skip_container_check = True
        connector.restored_container = False
        return connector

    @staticmethod
    def _odeslana_data(connector, volani, obejit=()):
        """
        Zachytí ``data`` předaná do ``_send_request`` při zavolání ``volani``.

        :param connector: Instance ``FedoraRepositoryConnector``.
        :param volani: Funkce bez argumentů, která spustí testovanou metodu.
        :param obejit: Názvy metod connectoru, které se pro účel testu vyřadí - jde o
            kroky mimo zkoumaný fragment, které by jinak sáhly na DB nebo na síť
            (``_check_binary_file_container``, ``_update_creator``; SPARQL update z
            ``_update_creator`` má vlastní test níž).
        :return: Seznam trojic ``(request_type, headers, data)`` v pořadí odeslání.
        """
        zachyceno = []
        # Některé metody s odpovědí dál pracují (``result.text.split("/")[-1]``,
        # ``result.status_code``), takže atrapa musí vracet reálné hodnoty; 404 drží
        # ``record_deletion`` ve větvi, která marker teprve zakládá.
        odpoved = SimpleNamespace(
            text=f"https://fedora.example/rest/{SERVER_NAME}/record/{IDENT_CELY}/file/uuid-1",
            status_code=404,
        )

        def zachyt(url, request_type, headers=None, data=None, **kwargs):
            zachyceno.append((request_type, headers, data))
            return odpoved

        spravci = [
            mock.patch.object(connector, "_send_request", side_effect=zachyt),
            mock.patch.object(connector, "_get_request_url", return_value="https://fedora.example/rest/dummy"),
        ]
        spravci += [mock.patch.object(connector, nazev) for nazev in obejit]
        for spravce in spravci:
            spravce.start()
        try:
            volani()
        finally:
            for spravce in spravci:
                spravce.stop()
        return zachyceno

    def _data_pozadavku(self, odeslane, request_type):
        """
        Vytáhne ze zachycených požadavků tělo toho jediného daného typu.

        :param odeslane: Návratová hodnota ``_odeslana_data``.
        :param request_type: Hledaný ``FedoraRequestType``.
        :return: Tělo požadavku.
        """
        tela = [data for typ, _hlavicky, data in odeslane if typ == request_type]
        self.assertEqual(len(tela), 1, f"očekáván právě jeden {request_type}, zachyceno: {odeslane}")
        return tela[0]

    def test_creator_turtle_je_shodny(self):
        """
        Každá spustitelná kopie creator turtle v connectoru musí být shodná s ``_creator_rdf``.

        Connector má tenhle fragment rozepsaný na čtyřech místech. Tři z nich se obejdou
        bez DB a porovnávají se tady; čtvrté (``migrate_binary_file``) potřebuje uložený
        ``Soubor``, takže ho hlídá jen ``PocetKopiiTurtleTest``.
        """
        ocekavane = self._writer()._creator_rdf()

        connector = self._connector()
        self.assertEqual(
            self._data_pozadavku(
                self._odeslana_data(connector, connector._create_container), FedoraRequestType.CREATE_CONTAINER
            ),
            ocekavane,
            "_create_container",
        )

        connector = self._connector()
        self.assertEqual(
            self._data_pozadavku(
                self._odeslana_data(connector, connector._create_binary_file_container),
                FedoraRequestType.CREATE_BINARY_FILE_CONTAINER,
            ),
            ocekavane,
            "_create_binary_file_container",
        )

        connector = self._connector()
        odeslane = self._odeslana_data(
            connector,
            lambda: connector.save_binary_file("a.txt", "text/plain", io.BytesIO(b"x"), save_thumbs=False),
            obejit=("_check_binary_file_container", "_update_creator"),
        )
        self.assertEqual(
            self._data_pozadavku(odeslane, FedoraRequestType.CREATE_BINARY_FILE), ocekavane, "save_binary_file"
        )

    def test_creator_sparql_update_je_shodny(self):
        """SPARQL update nastavující ``dcterms:creator`` musí být shodný s ``_get_creator_rdf_data``."""
        self.assertEqual(self._writer()._creator_sparql_update(), self._connector()._get_creator_rdf_data())

    def _link_turtle_z_writeru(self):
        """
        Vrátí turtle fragment, který pro link resource pošle ``_FastFedoraWriter``.

        :return: Tělo požadavku na ``/model/{model}/member``.
        """
        writer = self._writer()
        zachyceno = []

        def zachyt(method, url, headers, data, tx_url=None):
            zachyceno.append((url, data))
            return mock.Mock()

        with mock.patch.object(writer, "_request", side_effect=zachyt), mock.patch.object(writer, "_zkontroluj_slug"):
            writer.create_member_link(IDENT_CELY, MODEL_NAME)

        link_data = [data for url, data in zachyceno if "/member" in url]
        self.assertEqual(len(link_data), 1, f"očekáván jeden zápis link resource, zachyceno: {zachyceno}")
        return link_data[0]

    def test_link_turtle_je_shodny(self):
        """
        Všechny tři kopie link turtle v connectoru musí být shodné s ``create_member_link``.

        Liší se jen tím, odkud berou ident do ``ore:proxyFor``: ``create_link`` a
        ``record_deletion`` z ``record.ident_cely``, ``record_ident_change`` ze starého
        identu. Connectory se proto staví tak, aby ve všech třech případech šel do
        fragmentu tentýž ``IDENT_CELY``.
        """
        ocekavane = self._link_turtle_z_writeru()

        connector = self._connector()
        self.assertEqual(
            self._data_pozadavku(self._odeslana_data(connector, connector.create_link), FedoraRequestType.CREATE_LINK),
            ocekavane,
            "create_link",
        )

        connector = self._connector()
        self.assertEqual(
            self._data_pozadavku(
                self._odeslana_data(connector, connector.record_deletion),
                FedoraRequestType.RECORD_DELETION_ADD_MARK,
            ),
            ocekavane,
            "record_deletion",
        )

        connector = self._connector(JINY_IDENT)
        self.assertEqual(
            self._data_pozadavku(
                self._odeslana_data(
                    connector, lambda: connector.record_ident_change(IDENT_CELY, delete_container=False)
                ),
                FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_4,
            ),
            ocekavane,
            "record_ident_change",
        )

    def test_nazev_nahledu_je_shodny(self):
        """
        Jméno souboru náhledu musí obě implementace odvodit z ``Soubor.nazev`` stejně.

        Jde do ``Content-Disposition``, takže rozdíl by znamenal, že náhled vytvořený
        migrací se jmenuje jinak než tentýž náhled vytvořený aplikací. Obě strany počítají
        ``file_name[: file_name.rfind(".")]``; tenhle test drží, aby jedna z nich nezačala
        počítat něco jiného (review PR #4262).
        """
        # Druhé jméno má víc teček - odliší `rfind` od `find`, tedy tu záměnu, která by
        # se jinak na běžném jméně s jedinou příponou vůbec neprojevila.
        for nazev in ("C202300001F01.png", "C202300001F01.tar.gz"):
            with self.subTest(nazev=nazev):
                writer = self._writer()
                zachyceno = []

                def zachyt(method, url, headers, data, tx_url=None):
                    zachyceno.append((headers or {}).get("Content-Disposition"))
                    return mock.Mock()

                with mock.patch.object(writer, "_request", side_effect=zachyt):
                    writer.create_binary_file(
                        IDENT_CELY, "uuid-1", nazev, "image/png", b"orig", "a" * 128, b"t", "b" * 128, b"tl", "c" * 128
                    )
                z_migrace = {d for d in zachyceno if d}

                connector = self._connector()
                odeslane = self._odeslana_data(
                    connector,
                    lambda: connector.save_thumbs(
                        nazev, io.BytesIO(b""), "uuid-1", source_thumbs={True: b"tl", False: b"t"}
                    ),
                    obejit=("get_binary_file", "_update_creator"),
                )
                z_aplikace = {(h or {}).get("Content-Disposition") for _typ, h, _data in odeslane}
                z_aplikace.discard(None)

                self.assertTrue(z_aplikace, "ze save_thumbs se nezachytila žádná Content-Disposition")
                # Migrace posílá navíc originál souboru, aplikace v `save_thumbs` jen náhledy.
                self.assertTrue(
                    z_aplikace <= z_migrace,
                    f"jména náhledů se rozešla: aplikace {sorted(z_aplikace)} vs migrace {sorted(z_migrace)}",
                )

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


class PocetKopiiTurtleTest(SimpleTestCase):
    """
    Hlídá, že v connectoru nepřibyla další kopie turtle fragmentu.

    ``CreatorRdfParityTest`` porovnává chování, ale umí spustit jen ta místa, která se
    obejdou bez DB. Kdyby někdo přidal pátou kopii creator turtle (nebo čtvrtou link),
    prošlo by to bez povšimnutí a nová kopie by se mohla rozejít. Tenhle test proto ještě
    váže výskyty ve zdrojáku na konkrétní metody: jakákoli změna toho seznamu je signál,
    že se musí ručně zkontrolovat shoda s ``_FastFedoraWriter``.
    """

    #: Metody, které smí obsahovat creator turtle. Tři z nich pokrývá parity test,
    #: ``migrate_binary_file`` potřebuje uložený ``Soubor``, takže jen tady.
    OCEKAVANE_CREATOR = {
        "_create_container",
        "_create_binary_file_container",
        "save_binary_file",
        "migrate_binary_file",
    }
    #: Metody, které smí obsahovat link (proxy) turtle - všechny pokrývá parity test.
    OCEKAVANE_LINK = {"create_link", "record_deletion", "record_ident_change"}

    @staticmethod
    def _metody_s_markerem(marker):
        """
        Najde metody ``FedoraRepositoryConnector``, v jejichž těle se marker vyskytuje.

        :param marker: Hledaný podřetězec zdrojového kódu.
        :return: Množina názvů metod.
        """
        import core.repository_connector as modul

        zdroj = inspect.getsource(modul)
        radky = {i for i, radek in enumerate(zdroj.splitlines(), 1) if marker in radek}
        nalezene = set()
        for uzel in ast.walk(ast.parse(zdroj)):
            if isinstance(uzel, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(uzel.lineno <= radek <= uzel.end_lineno for radek in radky):
                    nalezene.add(uzel.name)
        return nalezene

    def test_creator_turtle_jen_ve_znamych_metodach(self):
        """Creator turtle se smí vyskytovat jen ve známých metodách."""
        self.assertEqual(
            self._metody_s_markerem(MARKER_CREATOR),
            self.OCEKAVANE_CREATOR,
            "Změnil se seznam metod s creator turtle. Zkontroluj shodu s `_FastFedoraWriter._creator_rdf` "
            "a uprav `OCEKAVANE_CREATOR` (a pokud se metoda obejde bez DB, přidej ji i do parity testu).",
        )

    def test_link_turtle_jen_ve_znamych_metodach(self):
        """Link (proxy) turtle se smí vyskytovat jen ve známých metodách."""
        self.assertEqual(
            self._metody_s_markerem(MARKER_LINK),
            self.OCEKAVANE_LINK,
            "Změnil se seznam metod s link turtle. Zkontroluj shodu s "
            "`_FastFedoraWriter.create_member_link` a uprav `OCEKAVANE_LINK`.",
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
