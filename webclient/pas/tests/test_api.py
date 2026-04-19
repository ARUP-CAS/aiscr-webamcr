"""Jednotkové testy API pro import samostatného nálezu z XML."""

import base64
import hashlib
import io
import json
import logging
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch

from core.constants import (
    API_REQUEST_LOG_STATUS_FAILURE,
    API_REQUEST_LOG_STATUS_SUCCESS,
    ODESLANI_SN,
    POTVRZENI_SN,
    SN_POTVRZENY,
    ZAPSANI_SN,
)
from core.models import ApiRequestLog, Permissions
from core.repository_connector import FedoraNoResponseError
from core.setting_models import CustomAdminSettings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from heslar.models import Heslar, HeslarNazev, RuianKatastr
from historie.models import Historie
from lxml import etree
from pas.api import ImportErrorType, ImportValidationException, SamostatnyNalezXmlImportView
from pas.models import SamostatnyNalez
from projekt.models import Projekt
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from uzivatel.models import Organizace, Osoba, User

logger = logging.getLogger(__name__)

XML_IMPORT_URL = reverse("pas:api-import-xml")


class SamostatnyNalezXmlImportViewTests(TestCase):
    """Testy pro ``SamostatnyNalezXmlImportView``."""

    databases = {"default", "urgent"}
    xml_url = XML_IMPORT_URL
    _DATA_DIR = Path(__file__).parent / "data"

    def setUp(self):
        """Připraví per-test PAS API nastavení a mocky Fedora repozitáře."""
        super().setUp()
        self._clear_pas_api_settings()

        patcher = patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None)
        patcher.start()
        self.addCleanup(patcher.stop)

        self._fedora_transaction_counter = 0
        transaction_patcher = patch("pas.api.FedoraTransaction", side_effect=self._build_mock_fedora_transaction)
        transaction_patcher.start()
        self.addCleanup(transaction_patcher.stop)

        repository_connector_patcher = patch(
            "pas.api.FedoraRepositoryConnector", side_effect=self._build_mock_repository_connector
        )
        repository_connector_patcher.start()
        self.addCleanup(repository_connector_patcher.stop)

    def tearDown(self):
        """Po každém testu znovu vyčistí PAS API nastavení a cache."""
        self._clear_pas_api_settings()
        super().tearDown()

    def _assert_log_failure(self, expected_errors: dict | None = None) -> None:
        """Ověří, že byl vytvořen jeden log záznam se stavem ``FAILURE`` a volitelně i uloženými chybami."""
        self.assertEqual(ApiRequestLog.objects.count(), 1)
        log_entry = ApiRequestLog.objects.get()
        self.assertEqual(log_entry.status, API_REQUEST_LOG_STATUS_FAILURE)
        if expected_errors is not None:
            self.assertEqual(log_entry.errors, expected_errors)

    def _assert_log_success(self) -> None:
        """Ověří, že byl vytvořen jeden log záznam se stavem ``SUCCESS``."""
        self.assertEqual(ApiRequestLog.objects.count(), 1)
        self.assertEqual(ApiRequestLog.objects.get().status, API_REQUEST_LOG_STATUS_SUCCESS)

    def _assert_xml_success_response(self, response, ident_cely: str) -> None:
        """
        Ověří, že úspěšná odpověď obsahuje pouze XML metadata z Fedory.

        :param response: HTTP odpověď importního endpointu.
        :param ident_cely: Očekávaný identifikátor obsažený v XML metadatech.
        """
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertIn(ident_cely, response.content.decode("utf-8"))

    def _build_mock_fedora_transaction(self, *args, **kwargs):
        """
        Vytvoří mock Fedora transakce pro API testy.

        :param args: Pozice předané při inicializaci ``FedoraTransaction``.
        :param kwargs: Klíčové argumenty předané při inicializaci ``FedoraTransaction``.

        :return: Mock objekt napodobující Fedora transakci.
        """
        self._fedora_transaction_counter += 1
        transaction = Mock()
        transaction.uid = f"test-fedora-transaction-{self._fedora_transaction_counter}"
        transaction.main_record = kwargs.get("main_record") or (args[0] if args else None)
        transaction.redirect_on_error = kwargs.get("redirect_on_error", False)
        transaction.redirect_url = kwargs.get("redirect_url")
        return transaction

    def _build_mock_repository_connector(self, record, *args, **kwargs):
        """
        Vytvoří mock repository connector pro čtení XML metadat.

        :param record: Záznam, pro který se metadata čtou.
        :param args: Pozice předané při inicializaci connectoru.
        :param kwargs: Klíčové argumenty předané při inicializaci connectoru.

        :return: Mock objekt s metodou ``get_metadata``.
        """
        connector = Mock()
        connector.record = record
        connector.get_metadata.return_value = (
            f"<amcr:amcr><amcr:samostatny_nalez><amcr:ident_cely>{record.ident_cely}</amcr:ident_cely>"
            f"</amcr:samostatny_nalez></amcr:amcr>"
        ).encode("utf-8")
        return connector

    def _clear_pas_api_settings(self) -> None:
        """Vyčistí testovací ``CustomAdminSettings`` a cache pro PAS API."""
        CustomAdminSettings.objects.filter(item_group="pas_api").delete()
        cache.delete("pas_api_access_rules")
        cache.delete("pas_api_rate_limits")
        cache.delete("pas_api_access_mode")

    @classmethod
    def _load_xml(cls, filename: str) -> bytes:
        """
        Načte XML soubor z adresáře ``data`` vedle tohoto modulu.

        :param filename: Název souboru v adresáři ``data``.

        :return: Vrací obsah souboru jako bajty.
        """
        return (cls._DATA_DIR / filename).read_bytes()

    @classmethod
    def _minimal_nalez_xml(
        cls,
        ident_cely: str,
        projekt_ident: str,
        pristupnost_ident: str,
        geom_system: str = "4326",
        geom_wkt: str = "POINT(14.42 50.08)",
    ) -> bytes:
        """
        Sestaví minimální validní XML pro jeden ``amcr:samostatny_nalez`` ze šablony.

        :param ident_cely: Identifikátor záznamu.
        :param projekt_ident: ``ident_cely`` odkazovaného projektu.
        :param pristupnost_ident: ``ident_cely`` hesláře přístupnosti.
        :param geom_system: Souřadnicový systém (``"4326"`` nebo ``"5514"``).
        :param geom_wkt: WKT geometrie bodu.

        :return: Vrací XML dokument jako bajty.
        """
        template = cls._load_xml("minimal_nalez.xml").decode("utf-8")
        return template.format(
            IDENT_CELY=ident_cely,
            PROJEKT_IDENT=projekt_ident,
            PRISTUPNOST_IDENT=pristupnost_ident,
            GEOM_SYSTEM=geom_system,
            EPSG=geom_system,
            GEOM_WKT=geom_wkt,
        ).encode("utf-8")

    def _post_xml(
        self,
        xml_bytes: bytes,
        token: str | None = None,
        content_digest: str | None = None,
        include_content_digest: bool = True,
    ) -> Response:
        """
        Odešle POST požadavek s XML souborem na endpoint pro import XML.

        :param xml_bytes: XML dokument jako bajty odesílaný jako multipart soubor.
        :param token: Bearer token pro autentizaci; pokud None, použije se ``self.token``.
        :param content_digest: Volitelná explicitní hodnota hlavičky ``Content-Digest``.
        :param include_content_digest: Pokud ``False``, hlavička ``Content-Digest`` se nepošle.

        :return: Vrací odpověď APIClient.
        """
        client = APIClient()
        if token is None:
            token = self.token.key
        if token:
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        if include_content_digest:
            if content_digest is None:
                digest = base64.b64encode(hashlib.sha512(xml_bytes).digest()).decode("ascii")
                content_digest = f"sha-512=:{digest}:"
            client.credentials(
                HTTP_AUTHORIZATION=f"Bearer {token}",
                HTTP_CONTENT_DIGEST=content_digest,
            )
        xml_file = io.BytesIO(xml_bytes)
        xml_file.name = "import.xml"
        return client.post(self.xml_url, {"file": xml_file}, format="multipart")

    def _set_pas_api_setting(self, item_id: str, value) -> None:
        """
        Uloží testovací hodnotu ``CustomAdminSettings`` pro skupinu ``pas_api``.

        :param item_id: Identifikátor položky nastavení.
        :param value: Python hodnota serializovatelná do JSON.
        """
        CustomAdminSettings.objects.update_or_create(
            item_group="pas_api",
            item_id=item_id,
            defaults={"value": json.dumps(value)},
        )

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená testovací data pro celou třídu."""
        from core.models import Permissions
        from heslar.hesla import HESLAR_LICENCE, HESLAR_OBDOBI, HESLAR_ORGANIZACE_TYP, HESLAR_PRISTUPNOST

        heslare_typ_org, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_ORGANIZACE_TYP, defaults={"nazev": "typ_organizace"}
        )
        cls.typ_organizace, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_typ_org,
            zkratka="T",
            defaults={"ident_cely": "HES-TYPORG-001", "heslo": "Testovací typ"},
        )

        heslare_pristupnost, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_PRISTUPNOST, defaults={"nazev": "pristupnost"}
        )
        cls.pristupnost, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_pristupnost,
            zkratka="A",
            defaults={"ident_cely": "HES-PRST-001", "heslo": "Veřejný"},
        )
        cls.zverejneni_pristupnost = cls.pristupnost

        heslare_licence, _ = HeslarNazev.objects.get_or_create(id=HESLAR_LICENCE, defaults={"nazev": "licence"})
        cls.licence, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_licence,
            zkratka="L",
            defaults={"ident_cely": "HES-LIC-001", "heslo": "Testovací licence"},
        )

        heslare_obdobi, _ = HeslarNazev.objects.get_or_create(id=HESLAR_OBDOBI, defaults={"nazev": "obdobi"})
        cls.obdobi, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_obdobi,
            zkratka="OBD",
            defaults={"ident_cely": "HES-OBD-001", "heslo": "Doba bronzová"},
        )

        with patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            cls.organizace, _ = Organizace.objects.get_or_create(
                ident_cely="ORG-TEST-XML",
                defaults={
                    "nazev": "Testovací org XML",
                    "nazev_zkraceny": "TOXL",
                    "typ_organizace": cls.typ_organizace,
                    "zverejneni_pristupnost": cls.zverejneni_pristupnost,
                    "licence": cls.licence,
                },
            )
        from core.constants import ROLE_BADATEL_ID
        from django.contrib.auth.models import Group

        badatel_group, _ = Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        Permissions.objects.get_or_create(
            main_role=badatel_group,
            action=Permissions.actionChoices.pas_edit,
            defaults={"address_in_app": "pas/api/import-xml", "base": True},
        )
        Permissions.objects.get_or_create(
            main_role=badatel_group,
            action=Permissions.actionChoices.pas_ulozeni_edit,
            defaults={"address_in_app": "pas/api/import-xml", "base": True},
        )
        Permissions.objects.get_or_create(
            main_role=badatel_group,
            action=Permissions.actionChoices.pas_zapsat_do_projektu,
            defaults={
                "address_in_app": "pas/api/import-xml",
                "base": True,
                "ownership": Permissions.ownershipChoices.our,
            },
        )
        Permissions.objects.get_or_create(
            main_role=badatel_group,
            action=Permissions.actionChoices.model_edit,
            defaults={"address_in_app": "heslar/osoba/zapsat", "base": True},
        )

        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="xmluser@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
            )
        cls.token, _ = Token.objects.get_or_create(user=cls.user)

        with patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            cls.outsider_organizace, _ = Organizace.objects.get_or_create(
                ident_cely="ORG-TEST-XML-OUT",
                defaults={
                    "nazev": "Cizi org XML",
                    "nazev_zkraceny": "COXL",
                    "typ_organizace": cls.typ_organizace,
                    "zverejneni_pristupnost": cls.zverejneni_pristupnost,
                    "licence": cls.licence,
                },
            )
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            cls.outsider_user = User.objects.create_user(  # type: ignore[attr-defined]
                email="xmloutsider@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.outsider_organizace,
            )
        cls.outsider_token, _ = Token.objects.get_or_create(user=cls.outsider_user)

        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            cls.known_osoba, _ = Osoba.objects.get_or_create(
                prijmeni="Známý",
                jmeno="Nálezce",
                defaults={
                    "vypis": "Známý, N.",
                    "vypis_cely": "Známý, Nálezce",
                },
            )

        from heslar.hesla_dynamicka import PRISTUPNOST_ANONYM_ID

        Heslar.objects.get_or_create(
            id=PRISTUPNOST_ANONYM_ID,
            defaults={
                "ident_cely": "HES-000865",
                "nazev_heslare": heslare_pristupnost,
                "zkratka": "AN",
                "heslo": "Anonym",
                "heslo_en": "Anonymous",
            },
        )

        from heslar.hesla import HESLAR_PROJEKT_TYP
        from heslar.hesla_dynamicka import TYP_PROJEKTU_PRUZKUM_ID, TYP_PROJEKTU_ZACHRANNY_ID
        from heslar.models import RuianKatastr

        heslare_typ_projektu, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_PROJEKT_TYP, defaults={"nazev": "typ_projektu"}
        )
        typ_projektu, _ = Heslar.objects.get_or_create(
            id=TYP_PROJEKTU_ZACHRANNY_ID,
            defaults={
                "ident_cely": "HES-001136",
                "nazev_heslare": heslare_typ_projektu,
                "zkratka": "Z",
                "heslo": "Záchranný",
                "heslo_en": "Rescue",
            },
        )
        survey_typ_projektu, _ = Heslar.objects.get_or_create(
            id=TYP_PROJEKTU_PRUZKUM_ID,
            defaults={
                "ident_cely": TYP_PROJEKTU_PRUZKUM_ID,
                "nazev_heslare": heslare_typ_projektu,
                "zkratka": "P",
                "heslo": "Průzkum",
                "heslo_en": "Survey",
            },
        )

        if not Projekt.objects.filter(ident_cely="M-202400099A").exists():
            from django.contrib.gis.geos import MultiPolygon, Point, Polygon
            from heslar.models import RuianKraj, RuianOkres

            kraj, _ = RuianKraj.objects.get_or_create(
                kod=99,
                defaults={
                    "nazev": "Testovací kraj",
                    "nazev_en": "Test Region",
                    "rada_id": "T",
                    "definicni_bod": Point(14.0, 50.0, srid=4326),
                    "hranice": MultiPolygon(
                        Polygon(((14.0, 50.0), (14.1, 50.0), (14.1, 50.1), (14.0, 50.0))), srid=4326
                    ),
                },
            )
            okres, _ = RuianOkres.objects.get_or_create(
                kod=9999,
                defaults={
                    "nazev": "Testovací okres",
                    "nazev_en": "Test District",
                    "spz": "TE",
                    "kraj": kraj,
                    "definicni_bod": Point(14.0, 50.0, srid=4326),
                    "hranice": MultiPolygon(
                        Polygon(((14.0, 50.0), (14.1, 50.0), (14.1, 50.1), (14.0, 50.0))), srid=4326
                    ),
                },
            )
            katastr, _ = RuianKatastr.objects.get_or_create(
                kod=999999,
                defaults={
                    "nazev": "Testovací katastr",
                    "okres": okres,
                    "definicni_bod": Point(14.0, 50.0, srid=4326),
                    "hranice": MultiPolygon(
                        Polygon(((14.0, 50.0), (14.1, 50.0), (14.1, 50.1), (14.0, 50.0))), srid=4326
                    ),
                },
            )
            with patch("projekt.signals.projekt_post_save", lambda **kw: None), patch(
                "xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None
            ):
                Projekt.objects.get_or_create(
                    ident_cely="M-202400099A",
                    defaults={
                        "organizace": cls.organizace,
                        "hlavni_katastr": katastr,
                        "typ_projektu": survey_typ_projektu,
                    },
                )
                Projekt.objects.get_or_create(
                    ident_cely="M-202400099B",
                    defaults={
                        "organizace": cls.organizace,
                        "hlavni_katastr": katastr,
                        "typ_projektu": typ_projektu,
                    },
                )
        cls.projekt = Projekt.objects.get(ident_cely="M-202400099A")
        cls.non_survey_projekt = Projekt.objects.get(ident_cely="M-202400099B")

    def test_access_mode_closed_returns_503(self):
        """Režim ``closed`` vrátí HTTP 503 ještě před vstupem do DRF permission vrstvy."""
        self._set_pas_api_setting("access_mode", "closed")
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-CLOSED-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(ApiRequestLog.objects.count(), 0)
        self.assertFalse(SamostatnyNalez.objects.filter(ident_cely="SN-XML-CLOSED-001").exists())

    def test_access_mode_open_ignores_whitelist_rules(self):
        """Režim ``open`` ignoruje whitelist pravidla a API zůstává dostupné."""
        self._set_pas_api_setting("access_mode", "open")
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "user_whitelist", "value": "other@example.com", "active": True}],
        )
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-OPEN-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        self._assert_xml_success_response(response, "SN-XML-OPEN-001")
        self.assertTrue(SamostatnyNalez.objects.filter(ident_cely="SN-XML-OPEN-001").exists())
        self._assert_log_success()

    def test_access_mode_whitelist_only_allows_whitelisted_user(self):
        """Režim ``whitelist_only`` povolí import uživateli z whitelistu."""
        self._set_pas_api_setting("access_mode", "whitelist_only")
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "user_whitelist", "value": self.user.email, "active": True}],
        )
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-WHITELIST-ALLOW-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        self._assert_xml_success_response(response, "SN-XML-WHITELIST-ALLOW-001")
        self.assertTrue(SamostatnyNalez.objects.filter(ident_cely="SN-XML-WHITELIST-ALLOW-001").exists())
        self._assert_log_success()

    def test_access_mode_whitelist_only_without_whitelist_returns_403(self):
        """Režim ``whitelist_only`` bez whitelist pravidel odmítne požadavek."""
        self._set_pas_api_setting("access_mode", "whitelist_only")
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-WHITELIST-REQUIRED-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ApiRequestLog.objects.count(), 0)
        self.assertFalse(SamostatnyNalez.objects.filter(ident_cely="SN-XML-WHITELIST-REQUIRED-001").exists())

    def test_content_digest_mismatch_returns_400(self):
        """POST s neodpovídající hlavičkou ``Content-Digest`` vrátí HTTP 400."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-BADDIGEST-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )
        wrong_digest = f"sha-512=:{base64.b64encode(hashlib.sha512(b'wrong').digest()).decode('ascii')}:"
        response = self._post_xml(xml, content_digest=wrong_digest)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self._assert_log_failure()

    def test_empty_document_returns_400(self):
        """XML bez elementu ``amcr:samostatny_nalez`` vrátí HTTP 400."""
        response = self._post_xml(self._load_xml("empty_document.xml"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self._assert_log_failure(response.data)

    def test_get_amcr_schema_initializes_schema_only_once_across_threads(self):
        """Paralelní volání ``_get_amcr_schema`` zkompiluje schéma právě jednou."""
        original_schema_cache = dict(SamostatnyNalezXmlImportView._amcr_schema_cache)
        SamostatnyNalezXmlImportView._amcr_schema_cache = {}
        schema_doc = object()
        schema_instance = object()
        schema_url = "https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd"
        doc = etree.ElementTree(
            etree.fromstring(
                self._minimal_nalez_xml(
                    ident_cely="SN-XML-SCHEMA-001",
                    projekt_ident=self.projekt.ident_cely,
                    pristupnost_ident=self.pristupnost.ident_cely,
                )
            )
        )

        def build_schema(doc):
            time.sleep(0.05)
            self.assertIs(doc, schema_doc)
            return schema_instance

        try:
            with patch("pas.api.etree.parse", return_value=schema_doc) as parse_mock, patch(
                "pas.api.urllib.request.urlopen"
            ) as urlopen_mock, patch("pas.api.etree.XMLSchema", side_effect=build_schema) as xmlschema_mock:
                urlopen_mock.return_value.__enter__.return_value = object()

                with ThreadPoolExecutor(max_workers=8) as executor:
                    results = list(executor.map(lambda _: SamostatnyNalezXmlImportView._get_amcr_schema(doc), range(8)))

                self.assertEqual(results, [schema_instance] * 8)
                cached_schema, _ = SamostatnyNalezXmlImportView._amcr_schema_cache[schema_url]
                self.assertIs(cached_schema, schema_instance)
                urlopen_mock.assert_called_once_with(schema_url, timeout=10)
                parse_mock.assert_called_once()
                xmlschema_mock.assert_called_once_with(schema_doc)

                self.assertIs(SamostatnyNalezXmlImportView._get_amcr_schema(doc), schema_instance)
                urlopen_mock.assert_called_once_with(schema_url, timeout=10)
                parse_mock.assert_called_once()
                xmlschema_mock.assert_called_once_with(schema_doc)
        finally:
            SamostatnyNalezXmlImportView._amcr_schema_cache = original_schema_cache

    def test_get_amcr_schema_rejects_disallowed_schema_url(self):
        """Načtení schématu z nepovolené domény vrátí ``INVALID_DATA``."""
        doc = etree.ElementTree(
            etree.fromstring(
                self._minimal_nalez_xml(
                    ident_cely="SN-XML-SCHEMA-BAD-001",
                    projekt_ident=self.projekt.ident_cely,
                    pristupnost_ident=self.pristupnost.ident_cely,
                ).replace(
                    b"https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd",
                    b"https://evil.example/amcr.xsd",
                )
            )
        )

        with self.assertRaises(ImportValidationException) as exc_ctx:
            SamostatnyNalezXmlImportView._get_amcr_schema(doc)

        self.assertEqual(len(exc_ctx.exception.import_errors), 1)
        self.assertEqual(exc_ctx.exception.import_errors[0].error_type, ImportErrorType.INVALID_DATA)

    def test_local_resolver_rejects_disallowed_url_in_xsd_import(self):
        """Resolver odmítne nepovolenou URL v ``xs:import`` uvnitř staženého XSD jako ``INVALID_DATA``."""
        xsd_with_disallowed_import = io.BytesIO(
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
            b'  <xs:import namespace="urn:evil" schemaLocation="https://evil.example/evil.xsd"/>'
            b"</xs:schema>"
        )
        doc = etree.ElementTree(
            etree.fromstring(
                self._minimal_nalez_xml(
                    ident_cely="SN-XML-RESOLVER-BAD-001",
                    projekt_ident=self.projekt.ident_cely,
                    pristupnost_ident=self.pristupnost.ident_cely,
                )
            )
        )

        original_schema_cache = dict(SamostatnyNalezXmlImportView._amcr_schema_cache)
        SamostatnyNalezXmlImportView._amcr_schema_cache = {}
        try:
            with patch("pas.api.urllib.request.urlopen", return_value=xsd_with_disallowed_import):
                with self.assertRaises(ImportValidationException) as exc_ctx:
                    SamostatnyNalezXmlImportView._get_amcr_schema(doc)
        finally:
            SamostatnyNalezXmlImportView._amcr_schema_cache = original_schema_cache

        self.assertEqual(len(exc_ctx.exception.import_errors), 1)
        self.assertEqual(exc_ctx.exception.import_errors[0].error_type, ImportErrorType.INVALID_DATA)

    def test_get_method_not_allowed(self):
        """GET požadavek na XML endpoint vrátí HTTP 405. Log záznam se nevytvoří — metoda je odmítnuta před view."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token.key}")
        response = client.get(self.xml_url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(ApiRequestLog.objects.count(), 0)

    def test_heslar_value_mismatch_returns_422(self):
        """Import vrátí HTTP 422, pokud text hodnoty neodpovídá ``heslo`` na odkazovaném hesláři."""
        template = self._load_xml("nalez_heslar_mismatch.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY="SN-XML-HES-MISMATCH-001",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            OBDOBI_IDENT=self.obdobi.ident_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(ident_cely="SN-XML-HES-MISMATCH-001").exists())
        self._assert_log_failure(response.data)

    def test_invalid_token_returns_401(self):
        """Požadavek s neplatným tokenem vrátí HTTP 401. Log záznam se nevytvoří — autentizace selže před view."""
        response = self._post_xml(b"<x/>", token="neplatnytoken")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(ApiRequestLog.objects.count(), 0)

    def test_malformed_xml_returns_400(self):
        """POST s poškozeným XML vrátí HTTP 400 se zprávou o syntaktické chybě."""
        response = self._post_xml(self._load_xml("malformed.xml"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self._assert_log_failure()

    def test_missing_content_digest_returns_400(self):
        """POST bez hlavičky ``Content-Digest`` vrátí HTTP 400."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-NODIGEST-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )
        response = self._post_xml(xml, include_content_digest=False)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self._assert_log_failure()

    def test_missing_file_returns_400(self):
        """POST bez souboru vrátí HTTP 400. Log záznam se vytvoří se stavem FAILURE."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token.key}")
        response = client.post(self.xml_url, {}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self._assert_log_failure()

    def test_missing_projekt_returns_422(self):
        """XML bez elementu ``projekt`` vrátí HTTP 422 jako datovou chybu."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-BAD-MISSING-PROJEKT",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        ).decode("utf-8")
        xml = xml.replace(
            f'    <amcr:projekt id="{self.projekt.ident_cely}">{self.projekt.ident_cely}</amcr:projekt>\n',
            "",
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("schema_errors", response.data)
        self._assert_log_failure()

    def test_multiple_samostatny_nalez_elements_return_422(self):
        """XML s více elementy ``amcr:samostatny_nalez`` vrátí HTTP 422."""
        template = self._load_xml("multiple_samostatny_nalez.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY_1="SN-XML-MULTI-001",
            IDENT_CELY_2="SN-XML-MULTI-002",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertTrue("detail" in response.data or "schema_errors" in response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(ident_cely="SN-XML-MULTI-001").exists())
        self.assertFalse(SamostatnyNalez.objects.filter(ident_cely="SN-XML-MULTI-002").exists())
        self._assert_log_failure()

    def test_nonexistent_nalezce_returns_404(self):
        """XML s neexistujícím ``nalezce`` vrátí HTTP 404."""
        template = self._load_xml("nalez_nonexistent_nalezce.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY="SN-XML-OS-BAD-001",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("validation_errors", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(ident_cely="SN-XML-OS-BAD-001").exists())
        self._assert_log_failure()

    def test_nonexistent_pristupnost_returns_422(self):
        """XML s neexistujícím heslem přístupnosti vrátí HTTP 422."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-BAD-2",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident="HES-NEEXISTUJE",
        )
        response = self._post_xml(xml)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self._assert_log_failure()

    def test_nonexistent_projekt_returns_404(self):
        """XML s neexistujícím projektem vrátí HTTP 404."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-BAD-1",
            projekt_ident="NEEXISTUJE-9999",
            pristupnost_ident=self.pristupnost.ident_cely,
        )
        response = self._post_xml(xml)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("validation_errors", response.data)
        self._assert_log_failure()

    def test_non_survey_projekt_returns_404(self):
        """XML s projektem mimo typ ``průzkum`` vrátí HTTP 404 stejně jako neexistující projekt."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-BAD-NON-SURVEY-001",
            projekt_ident=self.non_survey_projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("validation_errors", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(ident_cely="SN-XML-BAD-NON-SURVEY-001").exists())
        self._assert_log_failure()

    def test_schema_invalid_xml_returns_422(self):
        """POST s XML, které neodpovídá schématu AMČR, vrátí HTTP 422 se seznamem chyb schématu."""
        response = self._post_xml(self._load_xml("invalid_schema.xml"))
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("schema_errors", response.data)
        self._assert_log_failure()

    def test_stav_element_returns_422(self):
        """POST s nepovoleným elementem ``stav`` vrátí HTTP 422."""
        template = self._load_xml("nalez_with_stav.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY="SN-XML-STAV-001",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self.assertEqual(response.data["validation_errors"][0]["error_type"], ImportErrorType.INVALID_DATA.value)
        self.assertFalse(SamostatnyNalez.objects.filter(ident_cely="SN-XML-STAV-001").exists())
        self._assert_log_failure()

    def test_tba_ident_cely_is_generated_automatically(self):
        """Import s ``ident_cely=":tba"`` vygeneruje identifikátor automaticky."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SamostatnyNalez.objects.filter(projekt=self.projekt).count(), 1)
        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self.assertNotEqual(nalez.ident_cely, ":tba")
        self.assertIn(nalez.ident_cely, response.content.decode("utf-8"))
        self._assert_log_success()

    def test_tba_nalezce_is_rolled_back_when_samostatny_nalez_save_fails(self):
        """Při chybě ukládání nálezu se vrátí HTTP 500 a nově vytvořená osoba se vrátí rollbackem."""
        template = self._load_xml("nalez_tba_nalezce.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY="SN-XML-TBA-ROLLBACK-001",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")
        digest = base64.b64encode(hashlib.sha512(xml).digest()).decode("ascii")
        xml_file = SimpleUploadedFile("import.xml", xml, content_type="application/xml")
        request = APIRequestFactory().post(
            self.xml_url,
            {"file": xml_file},
            format="multipart",
            HTTP_CONTENT_DIGEST=f"sha-512=:{digest}:",
        )
        force_authenticate(request, user=self.user, token=self.token)

        with patch("pas.api.SamostatnyNalez.save", side_effect=RuntimeError("save failed")):
            response = SamostatnyNalezXmlImportView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(
            response.data,
            {"detail": "pas.api.SamostatnyNalezXmlImportView.post.internal_error"},
        )
        self.assertFalse(Osoba.objects.filter(prijmeni="Novák", jmeno="Jan").exists())
        self.assertFalse(SamostatnyNalez.objects.filter(ident_cely="SN-XML-TBA-ROLLBACK-001").exists())
        self._assert_log_failure(response.data)

    def test_get_metadata_failure_returns_500_with_failed_log(self):
        """Selhání čtení metadat z Fedory po uložení záznamu vrátí HTTP 500 a uzavře API log jako neúspěšný."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-METADATA-FAIL-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        connector = Mock()
        connector.get_metadata.side_effect = FedoraNoResponseError(
            "http://fedora.example/rest/record/SN-XML-METADATA-FAIL-001",
            "No Fedora response",
            None,
        )

        with patch("pas.api.FedoraRepositoryConnector", return_value=connector):
            response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(
            response.data,
            {"detail": "pas.api.SamostatnyNalezXmlImportView.post.fedor_error_reading_data_after_saving"},
        )
        self.assertTrue(SamostatnyNalez.objects.filter(ident_cely="SN-XML-METADATA-FAIL-001").exists())
        self._assert_log_failure(response.data)

    def test_tba_nalezce_with_invalid_format_returns_422(self):
        """Import s ``nalezce id=":tba"`` a nevalidním formátem vrátí HTTP 422."""
        template = self._load_xml("nalez_tba_nalezce_invalid_format.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY="SN-XML-TBA-BAD-001",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self.assertFalse(Osoba.objects.filter(jmeno="Jan", prijmeni="Novák").exists())
        self.assertFalse(SamostatnyNalez.objects.filter(ident_cely="SN-XML-TBA-BAD-001").exists())
        self._assert_log_failure()

    def test_tba_nalezce_without_model_edit_permission_returns_403(self):
        """Import s ``nalezce id=":tba"`` bez oprávnění na vytvoření osoby vrátí HTTP 403."""
        template = self._load_xml("nalez_tba_nalezce.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY="SN-XML-TBA-002",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        def permission_side_effect(action, user, ident=None):
            if action == Permissions.actionChoices.model_edit:
                return False
            return True

        with patch("pas.api.check_permissions", side_effect=permission_side_effect):
            response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("validation_errors", response.data)
        self.assertEqual(response.data["validation_errors"][0]["error_type"], ImportErrorType.PERMISSION_ERROR.value)
        self.assertFalse(Osoba.objects.filter(prijmeni="Novák", jmeno="Jan").exists())
        self.assertFalse(SamostatnyNalez.objects.filter(ident_cely="SN-XML-TBA-002").exists())
        self._assert_log_failure()

    def test_unauthenticated_returns_401(self):
        """Požadavek bez tokenu vrátí HTTP 401. Log záznam se nevytvoří — požadavek je odmítnut před view."""
        client = APIClient()
        xml_file = io.BytesIO(b"<x/>")
        xml_file.name = "f.xml"
        response = client.post(self.xml_url, {"file": xml_file}, format="multipart")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(ApiRequestLog.objects.count(), 0)

    def test_user_without_pas_edit_permission_returns_403(self):
        """Uživatel bez oprávnění ``pas_edit`` obdrží HTTP 403."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-FORBIDDEN-002",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        def permission_side_effect(action, user, ident=None):
            if action == "pas_edit":
                return False
            if action == "pas_ulozeni_edit":
                return True
            if action == "pas_zapsat_do_projektu" and ident == self.projekt.ident_cely:
                return True
            return True

        with patch("pas.api.check_permissions", side_effect=permission_side_effect):
            response = self._post_xml(xml, token=self.outsider_token.key)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(ident_cely="SN-XML-FORBIDDEN-002").exists())
        self._assert_log_failure()

    def test_user_without_project_permission_returns_403(self):
        """Uživatel bez oprávnění ``pas_zapsat_do_projektu`` pro daný projekt obdrží HTTP 403."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-FORBIDDEN-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        def permission_side_effect(action, user, ident=None):
            if action == "pas_ulozeni_edit":
                return True
            if action == "pas_zapsat_do_projektu" and ident == self.projekt.ident_cely:
                return False
            return True

        with patch("pas.api.check_permissions", side_effect=permission_side_effect):
            response = self._post_xml(xml, token=self.outsider_token.key)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(ident_cely="SN-XML-FORBIDDEN-001").exists())
        self._assert_log_failure()

    def test_valid_file_xml_creates_record_with_correct_values(self):
        """Import souboru ``valid_file.xml`` vytvoří záznam a importovaná data odpovídají obsahu XML."""
        template = self._load_xml("valid_file.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY="SN-XML-VF-001",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            PREDANO_ORGANIZACE_IDENT=self.organizace.ident_cely,
        ).encode("utf-8")
        response = self._post_xml(xml)
        self._assert_xml_success_response(response, "SN-XML-VF-001")
        nalez = SamostatnyNalez.objects.get(ident_cely="SN-XML-VF-001")
        self.assertEqual(nalez.hloubka, 21)
        self.assertEqual(str(nalez.datum_nalezu), "2026-04-06")
        self.assertFalse(nalez.predano)
        self.assertEqual(nalez.predano_organizace, self.organizace)
        self.assertEqual(nalez.pristupnost, self.pristupnost)
        self.assertEqual(nalez.lokalizace, "test")
        self.assertAlmostEqual(nalez.geom.x, 13.2311182, places=5)
        self.assertAlmostEqual(nalez.geom.y, 49.9914407, places=5)
        self.assertAlmostEqual(nalez.geom_sjtsk.x, -828708.49, places=1)
        self.assertAlmostEqual(nalez.geom_sjtsk.y, -1041287.69, places=1)
        self.assertEqual(nalez.stav, SN_POTVRZENY)
        self._assert_log_success()

    def test_valid_xml_creates_import_history_records(self):
        """Import vytvoří tři položky historie s importní poznámkou a vazbou na záznam."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-HIST-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        self._assert_xml_success_response(response, "SN-XML-HIST-001")
        nalez = SamostatnyNalez.objects.get(ident_cely="SN-XML-HIST-001")
        historie = list(Historie.objects.filter(vazba=nalez.historie).order_by("datum_zmeny", "id"))

        self.assertEqual(len(historie), 3)
        self.assertEqual([item.typ_zmeny for item in historie], [ZAPSANI_SN, ODESLANI_SN, POTVRZENI_SN])
        self.assertTrue(all(item.poznamka == SamostatnyNalezXmlImportView._IMPORT_HISTORY_NOTE for item in historie))
        self.assertTrue(all(item.uzivatel == self.user for item in historie))
        self.assertTrue(all(item.vazba == nalez.historie for item in historie))
        self._assert_log_success()

    def test_valid_xml_creates_record(self):
        """Validní XML s minimálními poli vytvoří záznam v databázi a vrátí HTTP 200."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )
        response = self._post_xml(xml)
        self._assert_xml_success_response(response, "SN-XML-001")
        self.assertTrue(SamostatnyNalez.objects.filter(ident_cely="SN-XML-001").exists())
        self._assert_log_success()

    def test_duplicate_ident_cely_returns_422(self):
        """Opakovaný import stejného ``ident_cely`` vrátí validační chybu HTTP 422."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-DUP-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        first_response = self._post_xml(xml)

        self._assert_xml_success_response(first_response, "SN-XML-DUP-001")
        self.assertTrue(SamostatnyNalez.objects.filter(ident_cely="SN-XML-DUP-001").exists())

        duplicate_response = self._post_xml(xml)

        self.assertEqual(duplicate_response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", duplicate_response.data)
        self.assertEqual(
            duplicate_response.data["validation_errors"][0]["error_type"], ImportErrorType.INVALID_DATA.value
        )
        self.assertEqual(SamostatnyNalez.objects.filter(ident_cely="SN-XML-DUP-001").count(), 1)

        logs = list(ApiRequestLog.objects.order_by("received_at", "id"))
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0].status, API_REQUEST_LOG_STATUS_SUCCESS)
        self.assertEqual(logs[1].status, API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIsNotNone(logs[1].finished_at)
        self.assertEqual(logs[1].errors, duplicate_response.data)

    def test_valid_xml_links_katastr_by_ruian_id(self):
        """Import naváže ``katastr`` podle XML ``id="ruian-..."`` na unikátní RÚIAN kód."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-KATASTR-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        ).decode("utf-8")
        xml = xml.replace(
            "<amcr:chranene_udaje>\n      <amcr:geom_wkt",
            '<amcr:chranene_udaje>\n      <amcr:katastr id="ruian-999999" xml:lang="cs">Testovací katastr</amcr:katastr>\n      <amcr:geom_wkt',
        ).encode("utf-8")

        response = self._post_xml(xml)

        self._assert_xml_success_response(response, "SN-XML-KATASTR-001")
        nalez = SamostatnyNalez.objects.get(ident_cely="SN-XML-KATASTR-001")
        self.assertEqual(nalez.katastr, RuianKatastr.objects.get(kod=999999))
        self._assert_log_success()

    def test_valid_xml_with_known_nalezce_links_existing_osoba(self):
        """Import s existujícím ``nalezce`` naváže záznam na existující osobu."""
        template = self._load_xml("nalez_known_nalezce.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY="SN-XML-OS-001",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            NALEZCE_IDENT=self.known_osoba.ident_cely,
            NALEZCE_LABEL=self.known_osoba.vypis_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self._assert_xml_success_response(response, "SN-XML-OS-001")
        nalez = SamostatnyNalez.objects.get(ident_cely="SN-XML-OS-001")
        self.assertEqual(nalez.nalezce, self.known_osoba)
        self._assert_log_success()

    def test_valid_xml_with_optional_fields(self):
        """XML s volitelnými poli (hloubka, poznamka, presna_datace) vytvoří záznam se správnými hodnotami."""
        template = self._load_xml("nalez_optional_fields.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY="SN-XML-003",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")
        response = self._post_xml(xml)
        self._assert_xml_success_response(response, "SN-XML-003")
        nalez = SamostatnyNalez.objects.get(ident_cely="SN-XML-003")
        self.assertEqual(nalez.hloubka, 42)
        self.assertEqual(nalez.poznamka, "testovací poznámka")
        self.assertEqual(nalez.lokalizace, "u lesa")
        self.assertEqual(nalez.presna_datace, "raný středověk")
        self._assert_log_success()

    def test_valid_xml_with_tba_nalezce_creates_osoba_and_links_it(self):
        """Import s ``nalezce id=":tba"`` vytvoří novou osobu a naváže ji na nález."""
        template = self._load_xml("nalez_tba_nalezce.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY="SN-XML-TBA-001",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            response = self._post_xml(xml)

        self._assert_xml_success_response(response, "SN-XML-TBA-001")
        osoba = Osoba.objects.get(prijmeni="Novák", jmeno="Jan")
        nalez = SamostatnyNalez.objects.get(ident_cely="SN-XML-TBA-001")

        self.assertEqual(osoba.vypis_cely, "Novák, Jan")
        self.assertEqual(osoba.vypis, "Novák, J.")
        self.assertEqual(nalez.nalezce, osoba)
        self._assert_log_success()

    def test_validate_schema_url_allowed_accepts_configured_prefixes(self):
        """Allowlist přijímá povolené URL rodiny pro W3C, AMČR a GML."""
        allowed_urls = (
            "https://www.w3.org/2001/XMLSchema-instance",
            "http://www.w3.org/2001/xml.xsd",
            "https://www.w3.org/2001/03/xml.xsd",
            "https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd",
            "https://api.aiscr.cz/schema/amcr/12.4/other.xsd",
            "http://www.opengis.net/gml/3.2",
        )

        for url in allowed_urls:
            with self.subTest(url=url):
                SamostatnyNalezXmlImportView._validate_schema_url_allowed(url)

    def test_schema_fetch_network_error_returns_422(self):
        """Síťová chyba při načítání XSD schématu vrátí HTTP 422 místo 500."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-NETERR-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )
        # Vyčistíme cache schématu, aby se urlopen skutečně zavolal.
        SamostatnyNalezXmlImportView._amcr_schema_cache.clear()

        with patch(
            "pas.api.urllib.request.urlopen",
            side_effect=urllib.error.URLError("simulated network failure"),
        ):
            response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self._assert_log_failure()

    def test_wrong_amcr_namespace_version_returns_422(self):
        """POST s deklarovaným AMČR namespace jiné verze vrátí HTTP 422."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-BADNS-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        ).decode("utf-8")
        xml = xml.replace(
            "https://api.aiscr.cz/schema/amcr/2.2/",
            "https://api.aiscr.cz/schema/amcr/2.1/",
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", response.data)
        self._assert_log_failure()

    def test_wrong_amcr_schema_location_version_returns_422(self):
        """POST s deklarovanou XSD URL jiné AMČR verze vrátí HTTP 422."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-BADXSD-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        ).decode("utf-8")
        xml = xml.replace(
            "https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd",
            "https://api.aiscr.cz/schema/amcr/2.1/amcr.xsd",
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", response.data)
        self._assert_log_failure()

    def test_wrong_heslar_type_for_obdobi_returns_422(self):
        """XML s hodnotou hesláře špatného typu v poli ``obdobi`` vrátí HTTP 422.

        Do pole ``obdobi`` je předána položka hesláře typu ``licence``, která nepatří
        do hesláře ``HESLAR_OBDOBI`` — serializer ji musí odmítnout.
        """
        template = self._load_xml("nalez_with_obdobi.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY="SN-XML-BAD-3",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            OBDOBI_IDENT=self.licence.ident_cely,
        ).encode("utf-8")
        response = self._post_xml(xml)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self._assert_log_failure()

    def test_xml_lang_different_from_cs_is_ignored_with_note(self):
        """Import s ``xml:lang`` odlišným od ``cs`` uspěje a vrátí poznámku o ignorování."""
        template = self._load_xml("nalez_lang_ignored.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY="SN-XML-LANG-001",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self._assert_xml_success_response(response, "SN-XML-LANG-001")
        self.assertTrue(SamostatnyNalez.objects.filter(ident_cely="SN-XML-LANG-001").exists())
        self._assert_log_success()
