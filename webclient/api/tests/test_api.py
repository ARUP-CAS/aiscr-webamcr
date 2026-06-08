"""Jednotkové testy API pro PAS endpoints."""

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

from api.models import ApiRequestLog
from api.views import (
    _RECORD_LOCK_PREFIX,
    _XSD_BYTES_CACHE,
    ImportErrorType,
    ImportValidationException,
    SamostatnyNalezEvidencniCisloPatchView,
    SamostatnyNalezXmlImportView,
    _fetch_xsd_bytes,
    _xsd_redis_key,
)
from core.constants import (
    AKTUALIZACE_SN,
    API_REQUEST_LOG_STATUS_FAILURE,
    API_REQUEST_LOG_STATUS_SUCCESS,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_EVIDENCNI_CISLO_PATCH,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_FOTOGRAFIE_UPLOAD,
    ARCHIVACE_SN,
    NAHRANI_SBR,
    ODESLANI_SN,
    POTVRZENI_SN,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    SN_ARCHIVOVANY,
    SN_ODESLANY,
    SN_POTVRZENY,
    SN_ZAPSANY,
    ZAPSANI_SN,
)
from core.models import AntivirusCheckResult, Permissions, Soubor, check_permissions
from core.repository_connector import FedoraNoResponseError
from core.setting_models import CustomAdminSettings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError, IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from heslar.hesla import HESLAR_LICENCE, HESLAR_ORGANIZACE_TYP, HESLAR_PRISTUPNOST
from heslar.hesla_dynamicka import TYP_PROJEKTU_PRUZKUM_ID
from heslar.models import Heslar, HeslarNazev, RuianKatastr
from historie.models import Historie
from lxml import etree
from pas.models import SamostatnyNalez
from pid.exceptions import DoiWriteError
from projekt.models import Projekt
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.test import APIClient
from uzivatel.models import Organizace, Osoba, User

logger = logging.getLogger(__name__)

XML_IMPORT_URL = reverse("api:import-xml")
PATCH_URL_NAME = "api:patch-evidencni-cislo"
FOTO_UPLOAD_URL_NAME = "api:upload-foto"
IDENT_CELY = "C-202600009-N00007"


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
        transaction_patcher = patch("api.views.FedoraTransaction", side_effect=self._build_mock_fedora_transaction)
        transaction_patcher.start()
        self.addCleanup(transaction_patcher.stop)

        repository_connector_patcher = patch(
            "api.views.FedoraRepositoryConnector", side_effect=self._build_mock_repository_connector
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
        """Vyčistí testovací ``CustomAdminSettings``, cache a in-process slovník XSD pro PAS API."""
        CustomAdminSettings.objects.filter(item_group="pas_api").delete()
        cache.delete("pas_api_access_rules")
        cache.delete("pas_api_rate_limits")
        cache.delete("pas_api_access_mode")
        cache.delete("pas_api_allowed_schema_versions")
        _XSD_BYTES_CACHE.clear()

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
        geom_wkt: str = "POINT(14.0667 50.0333)",
        stav: int = 3,
    ) -> bytes:
        """
        Sestaví minimální validní XML pro jeden ``amcr:samostatny_nalez`` ze šablony.

        :param ident_cely: Identifikátor záznamu.
        :param projekt_ident: ``ident_cely`` odkazovaného projektu.
        :param pristupnost_ident: ``ident_cely`` hesláře přístupnosti.
        :param geom_system: Souřadnicový systém (``"4326"`` nebo ``"5514"``).
        :param geom_wkt: WKT geometrie bodu.
        :param stav: Cílový stav záznamu (1, 2 nebo 3).

        :return: Vrací XML dokument jako bajty.
        """
        template = cls._load_xml("minimal_nalez.xml").decode("utf-8")
        return template.format(
            IDENT_CELY=ident_cely,
            PROJEKT_IDENT=projekt_ident,
            PRISTUPNOST_IDENT=pristupnost_ident,
            OBDOBI_IDENT=cls.obdobi.ident_cely,
            OKOLNOSTI_IDENT=cls.okolnosti.ident_cely,
            DRUH_NALEZU_IDENT=cls.druh_nalezu.ident_cely,
            SPECIFIKACE_IDENT=cls.specifikace.ident_cely,
            NALEZCE_IDENT=cls.known_osoba.ident_cely,
            NALEZCE_LABEL=cls.known_osoba.vypis_cely,
            GEOM_SYSTEM=geom_system,
            EPSG=geom_system,
            GEOM_WKT=geom_wkt,
            STAV=stav,
        ).encode("utf-8")

    @classmethod
    def _required_heslar_subs(cls) -> dict:
        """Substitutions for heslar fields required by ``check_pred_odeslanim`` (no nalezce)."""
        return {
            "OBDOBI_IDENT": cls.obdobi.ident_cely,
            "OKOLNOSTI_IDENT": cls.okolnosti.ident_cely,
            "DRUH_NALEZU_IDENT": cls.druh_nalezu.ident_cely,
            "SPECIFIKACE_IDENT": cls.specifikace.ident_cely,
        }

    @classmethod
    def _required_field_subs(cls) -> dict:
        """Substitutions for all fields required by ``check_pred_odeslanim``, including nalezce."""
        return {
            **cls._required_heslar_subs(),
            "NALEZCE_IDENT": cls.known_osoba.ident_cely,
            "NALEZCE_LABEL": cls.known_osoba.vypis_cely,
        }

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
        from heslar.hesla import (
            HESLAR_LICENCE,
            HESLAR_NALEZOVE_OKOLNOSTI,
            HESLAR_OBDOBI,
            HESLAR_ORGANIZACE_TYP,
            HESLAR_PREDMET_DRUH,
            HESLAR_PREDMET_SPECIFIKACE,
            HESLAR_PRISTUPNOST,
        )

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

        heslare_okolnosti, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_NALEZOVE_OKOLNOSTI, defaults={"nazev": "nalezove_okolnosti"}
        )
        cls.okolnosti, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_okolnosti,
            zkratka="OKOL",
            defaults={"ident_cely": "HES-OKOL-001", "heslo": "Náhodný nález"},
        )

        heslare_druh_nalezu, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_PREDMET_DRUH, defaults={"nazev": "predmet_druh"}
        )
        cls.druh_nalezu, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_druh_nalezu,
            zkratka="DRUH",
            defaults={"ident_cely": "HES-DRUH-001", "heslo": "Keramika"},
        )

        heslare_specifikace, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_PREDMET_SPECIFIKACE, defaults={"nazev": "predmet_specifikace"}
        )
        cls.specifikace, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_specifikace,
            zkratka="SPEC",
            defaults={"ident_cely": "HES-SPEC-001", "heslo": "Střep"},
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
        from core.constants import (
            ROLE_ADMIN_ID,
            ROLE_ARCHEOLOG_ID,
            ROLE_ARCHIVAR_ID,
            ROLE_BADATEL_ID,
        )
        from django.contrib.auth.models import Group

        badatel_group, _ = Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        archeolog_group, _ = Group.objects.get_or_create(id=ROLE_ARCHEOLOG_ID, defaults={"name": "archeolog"})
        Group.objects.get_or_create(id=ROLE_ARCHIVAR_ID, defaults={"name": "archivar"})
        Group.objects.get_or_create(id=ROLE_ADMIN_ID, defaults={"name": "admin"})
        for role_group in (badatel_group, archeolog_group):
            Permissions.objects.get_or_create(
                main_role=role_group,
                action=Permissions.actionChoices.pas_edit,
                defaults={"address_in_app": "pas/api/import-xml", "base": True},
            )
            Permissions.objects.get_or_create(
                main_role=role_group,
                action=Permissions.actionChoices.pas_ulozeni_edit,
                defaults={"address_in_app": "pas/api/import-xml", "base": True},
            )
            Permissions.objects.get_or_create(
                main_role=role_group,
                action=Permissions.actionChoices.pas_zapsat_do_projektu,
                defaults={
                    "address_in_app": "pas/api/import-xml",
                    "base": True,
                    "ownership": Permissions.ownershipChoices.our,
                },
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
        cls.user.groups.add(archeolog_group)
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
        from heslar.hesla_dynamicka import (
            TYP_PROJEKTU_PRUZKUM_ID,
            TYP_PROJEKTU_ZACHRANNY_ID,
        )
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
                        Polygon(((13.0, 49.9), (14.5, 49.9), (14.5, 50.2), (13.0, 50.2), (13.0, 49.9))), srid=4326
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
                        Polygon(((13.0, 49.9), (14.5, 49.9), (14.5, 50.2), (13.0, 50.2), (13.0, 49.9))), srid=4326
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
                        Polygon(((13.0, 49.9), (14.5, 49.9), (14.5, 50.2), (13.0, 50.2), (13.0, 49.9))), srid=4326
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
                        "stav": PROJEKT_STAV_ZAHAJENY_V_TERENU,
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

        from django.contrib.gis.geos import MultiPolygon, Point, Polygon
        from heslar.models import RuianOkres

        cls.other_katastr_okres, _ = RuianOkres.objects.get_or_create(
            kod=9998,
            defaults={
                "nazev": "Jiný testovací okres",
                "nazev_en": "Other Test District",
                "spz": "OT",
                "kraj": RuianKatastr.objects.get(kod=999999).okres.kraj,
                "definicni_bod": Point(10.0, 47.0, srid=4326),
                "hranice": MultiPolygon(
                    Polygon(((9.0, 46.5), (11.0, 46.5), (11.0, 47.5), (9.0, 47.5), (9.0, 46.5))), srid=4326
                ),
            },
        )
        cls.other_katastr, _ = RuianKatastr.objects.get_or_create(
            kod=999998,
            defaults={
                "nazev": "Jiný testovací katastr",
                "okres": cls.other_katastr_okres,
                "definicni_bod": Point(10.0, 47.0, srid=4326),
                "hranice": MultiPolygon(
                    Polygon(((9.0, 46.5), (11.0, 46.5), (11.0, 47.5), (9.0, 47.5), (9.0, 46.5))), srid=4326
                ),
            },
        )

    def test_access_mode_closed_returns_503(self):
        """Režim ``closed`` vrátí HTTP 503 ještě před vstupem do DRF permission vrstvy."""
        self._set_pas_api_setting("access_mode", "closed")
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(ApiRequestLog.objects.count(), 0)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())

    def test_access_mode_open_ignores_whitelist_rules(self):
        """Režim ``open`` ignoruje whitelist pravidla a API zůstává dostupné."""
        self._set_pas_api_setting("access_mode", "open")
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "user_whitelist", "value": "other@example.com", "active": True}],
        )
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self._assert_log_success()

    def test_access_mode_whitelist_only_allows_whitelisted_user(self):
        """Režim ``whitelist_only`` povolí import uživateli z whitelistu."""
        self._set_pas_api_setting("access_mode", "whitelist_only")
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "user_whitelist", "value": self.user.email, "active": True}],
        )
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self._assert_log_success()

    def test_access_mode_whitelist_only_without_whitelist_returns_403(self):
        """Režim ``whitelist_only`` bez whitelist pravidel odmítne požadavek."""
        self._set_pas_api_setting("access_mode", "whitelist_only")
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ApiRequestLog.objects.count(), 0)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())

    def test_content_digest_mismatch_returns_400(self):
        """POST s neodpovídající hlavičkou ``Content-Digest`` vrátí HTTP 400."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )
        wrong_digest = f"sha-512=:{base64.b64encode(hashlib.sha512(b'wrong').digest()).decode('ascii')}:"
        response = self._post_xml(xml, content_digest=wrong_digest)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self._assert_log_failure()

    def test_content_digest_invalid_format_returns_400(self):
        """POST s hlavičkou ``Content-Digest`` v neplatném formátu vrátí HTTP 400."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml, content_digest="sha-512=invalid")

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
        schema_instance = object()
        schema_url = "https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd"
        doc = etree.ElementTree(
            etree.fromstring(
                self._minimal_nalez_xml(
                    ident_cely=":tba",
                    projekt_ident=self.projekt.ident_cely,
                    pristupnost_ident=self.pristupnost.ident_cely,
                )
            )
        )

        def build_schema(schema_doc):
            time.sleep(0.05)
            return schema_instance

        try:
            with patch("api.views._fetch_xsd_bytes", return_value=b"<schema/>") as fetch_mock, patch(
                "api.views.etree.XMLSchema", side_effect=build_schema
            ) as xmlschema_mock:
                with ThreadPoolExecutor(max_workers=8) as executor:
                    results = list(executor.map(lambda _: SamostatnyNalezXmlImportView._get_amcr_schema(doc), range(8)))

                self.assertEqual(results, [schema_instance] * 8)
                cached_schema, _ = SamostatnyNalezXmlImportView._amcr_schema_cache[schema_url]
                self.assertIs(cached_schema, schema_instance)
                fetch_mock.assert_called_once_with(schema_url)
                xmlschema_mock.assert_called_once()

                self.assertIs(SamostatnyNalezXmlImportView._get_amcr_schema(doc), schema_instance)
                fetch_mock.assert_called_once_with(schema_url)
                xmlschema_mock.assert_called_once()
        finally:
            SamostatnyNalezXmlImportView._amcr_schema_cache = original_schema_cache

    def test_get_amcr_schema_rejects_disallowed_schema_url(self):
        """Načtení schématu z nepovolené domény vrátí ``INVALID_DATA``."""
        doc = etree.ElementTree(
            etree.fromstring(
                self._minimal_nalez_xml(
                    ident_cely=":tba",
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
        evil_xsd_bytes = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
            b'  <xs:import namespace="urn:evil" schemaLocation="https://evil.example/evil.xsd"/>'
            b"</xs:schema>"
        )
        doc = etree.ElementTree(
            etree.fromstring(
                self._minimal_nalez_xml(
                    ident_cely=":tba",
                    projekt_ident=self.projekt.ident_cely,
                    pristupnost_ident=self.pristupnost.ident_cely,
                )
            )
        )

        original_schema_cache = dict(SamostatnyNalezXmlImportView._amcr_schema_cache)
        SamostatnyNalezXmlImportView._amcr_schema_cache = {}
        try:
            with patch("api.views._fetch_xsd_bytes", return_value=evil_xsd_bytes):
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

    def test_heslar_wrong_group_returns_422(self):
        """Import vrátí HTTP 422, pokud atribut ``id`` odkazuje na položku z jiné skupiny hesláře."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        ).decode("utf-8")
        # Replace the correct okolnosti id with an id from a different heslar group (obdobi)
        # to trigger the wrong-group validation error.
        xml = xml.replace(
            f'id="{self.okolnosti.ident_cely}"',
            f'id="{self.obdobi.ident_cely}"',
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
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
            ident_cely=":tba",
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
            ident_cely=":tba",
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
            IDENT_CELY_1=":tba",
            IDENT_CELY_2=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertTrue("detail" in response.data or "schema_errors" in response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure()

    def test_invalid_root_content_returns_422(self):
        """XML s dalším kořenovým potomkem kromě ``amcr:samostatny_nalez`` vrátí HTTP 422."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        ).decode("utf-8")
        xml = xml.replace(
            "</amcr:amcr>",
            '  <amcr:unexpected xmlns:amcr="https://api.aiscr.cz/schema/amcr/2.2/"/>\n</amcr:amcr>',
        ).encode("utf-8")
        schema = Mock()
        schema.validate.return_value = True
        schema.error_log = []

        with patch("api.views.SamostatnyNalezXmlImportView._get_amcr_schema", return_value=schema):
            response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure(response.data)

    def test_nonexistent_nalezce_returns_404(self):
        """XML s neexistujícím ``nalezce`` vrátí HTTP 404."""
        template = self._load_xml("nalez_nonexistent_nalezce.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("validation_errors", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure()

    def test_nonexistent_pristupnost_returns_422(self):
        """XML s neexistujícím heslem přístupnosti vrátí HTTP 422."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
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
            ident_cely=":tba",
            projekt_ident="NEEXISTUJE-9999",
            pristupnost_ident=self.pristupnost.ident_cely,
        )
        response = self._post_xml(xml)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)
        self._assert_log_failure()

    def test_non_survey_projekt_returns_403(self):
        """XML s projektem mimo typ ``průzkum`` vrátí HTTP 403, protože projekt není v dostupných průzkumných projektech."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.non_survey_projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.non_survey_projekt).exists())
        self._assert_log_failure()

    def test_schema_invalid_xml_returns_422(self):
        """POST s XML, které neodpovídá schématu AMČR, vrátí HTTP 422 se seznamem chyb schématu."""
        response = self._post_xml(self._load_xml("invalid_schema.xml"))
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("schema_errors", response.data)
        self._assert_log_failure()

    def test_allowed_schema_versions_rejects_disallowed_version(self):
        """Import s verzí schématu, která není v ``allowed_schema_versions``, vrátí HTTP 422."""
        self._set_pas_api_setting("allowed_schema_versions", [9.9])
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", response.data)
        self.assertIn("version_not_allowed", response.data["detail"])
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure(response.data)

    def test_allowed_schema_versions_accepts_listed_version(self):
        """Import s verzí schématu obsaženou v ``allowed_schema_versions`` proběhne úspěšně."""
        self._set_pas_api_setting("allowed_schema_versions", [2.2])
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self._assert_log_success()

    def test_allowed_schema_versions_not_set_accepts_any_version(self):
        """Import bez nastavení ``allowed_schema_versions`` v DB neomezuje verzi schématu."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self._assert_log_success()

    def test_missing_stav_fails_xsd_validation(self):
        """POST s jinak validním XML bez elementu ``stav`` vrátí HTTP 422 s chybou validace XSD schématu."""
        template = self._load_xml("minimal_nalez_no_stav.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("schema_errors", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure()

    def test_out_of_range_stav_in_xml_returns_422(self):
        """Import s hodnotou ``stav=99`` v XML vrátí HTTP 422 a záznam se nevytvoří.

        XSD validace neomezuje hodnotu ``stav`` výčtem — hodnota 99 projde schématem.
        Import ji odmítne jako nepodporovanou hodnotu (povoleny jsou pouze 1, 2, 3).
        """
        template = self._load_xml("nalez_invalid_stav.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
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

    def test_non_tba_ident_cely_returns_422(self):
        """Import s hodnotou ``ident_cely`` jinou než ``:tba`` vrátí HTTP 422."""
        xml = self._minimal_nalez_xml(
            ident_cely="SN-XML-EXPLICIT-001",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self.assertEqual(response.data["validation_errors"][0]["error_type"], ImportErrorType.INVALID_DATA.value)
        self.assertFalse(SamostatnyNalez.objects.filter(ident_cely="SN-XML-EXPLICIT-001").exists())
        self._assert_log_failure()

    def test_igsn_in_xml_is_ignored(self):
        """Import s polem ``igsn`` v XML vytvoří záznam, ale ``igsn`` pole záznamu zůstane prázdné."""
        template = self._load_xml("nalez_with_igsn.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            **self._required_field_subs(),
        ).encode("utf-8")

        response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self.assertFalse(nalez.igsn)
        self._assert_log_success()

    def test_katastr_in_xml_is_ignored_uses_coordinates(self):
        """Import s ``katastr`` polem v ``chranene_udaje`` XML ignoruje XML hodnotu a doplní katastr ze souřadnic.

        XML uvádí jiný katastr než odpovídá souřadnicím ``geom_wkt``. Importovaný záznam
        musí mít katastr odvozený ze souřadnic, nikoliv z XML pole.
        """
        template = self._load_xml("nalez_with_wrong_katastr_and_okres.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            WRONG_KATASTR_IDENT=f"ruian-{self.other_katastr.kod}",
            WRONG_OKRES_IDENT=f"ruian-{self.other_katastr_okres.kod}",
            **self._required_field_subs(),
        ).encode("utf-8")

        response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self.assertEqual(nalez.katastr.kod, 999999)
        self.assertNotEqual(nalez.katastr.kod, self.other_katastr.kod)
        self._assert_log_success()

    def test_okres_in_xml_is_ignored_derived_from_katastr(self):
        """Import s ``okres`` polem v XML ignoruje XML hodnotu a okres je odvozen z katastru ze souřadnic.

        XML uvádí jiný okres než odpovídá katastru odvozenému ze souřadnic ``geom_wkt``. Importovaný
        záznam musí mít katastr odvozený ze souřadnic a tedy i správný okres z tohoto katastru.
        """
        template = self._load_xml("nalez_with_wrong_katastr_and_okres.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            WRONG_KATASTR_IDENT=f"ruian-{self.other_katastr.kod}",
            WRONG_OKRES_IDENT=f"ruian-{self.other_katastr_okres.kod}",
            **self._required_field_subs(),
        ).encode("utf-8")

        response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self.assertEqual(nalez.katastr.okres.kod, 9999)
        self.assertNotEqual(nalez.katastr.okres.kod, self.other_katastr_okres.kod)
        self._assert_log_success()

    def test_invalid_geom_wkt_returns_422(self):
        """Import s syntakticky neplatným WKT v ``geom_wkt`` vrátí HTTP 422."""
        template = self._load_xml("nalez_invalid_geom_wkt.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self.assertEqual(response.data["validation_errors"][0]["error_type"], ImportErrorType.INVALID_DATA.value)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure()

    def test_non_point_geom_wkt_returns_422(self):
        """Import s WKT geometrií jiného typu než ``Point`` v ``geom_wkt`` vrátí HTTP 422."""
        template = self._load_xml("nalez_linestring_geom_wkt.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self.assertEqual(response.data["validation_errors"][0]["error_type"], ImportErrorType.INVALID_DATA.value)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure()

    def test_invalid_geom_sjtsk_wkt_returns_422(self):
        """Import s syntakticky neplatným WKT v ``geom_sjtsk_wkt`` vrátí HTTP 422."""
        template = self._load_xml("minimal_nalez_sjtsk.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            GEOM_SJTSK_WKT="NOT_VALID_WKT",
            **self._required_field_subs(),
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self.assertEqual(response.data["validation_errors"][0]["error_type"], ImportErrorType.INVALID_DATA.value)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure()

    def test_get_metadata_failure_returns_500_with_failed_log(self):
        """Selhání čtení metadat z Fedory po uložení záznamu vrátí HTTP 500 a uzavře API log jako neúspěšný."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        connector = Mock()
        connector.get_metadata.side_effect = FedoraNoResponseError(
            "http://fedora.example/rest/record",
            "No Fedora response",
            None,
        )

        with patch("api.views.FedoraRepositoryConnector", return_value=connector):
            response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(
            response.data,
            {"detail": "api.views.SamostatnyNalezXmlImportView.post.fedor_error_reading_data_after_saving"},
        )
        self.assertTrue(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure(response.data)

    def test_tba_nalezce_with_invalid_format_returns_422(self):
        """Import s ``nalezce id=":tba"`` a nevalidním formátem vrátí HTTP 422."""
        template = self._load_xml("nalez_tba_nalezce_invalid_format.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self.assertFalse(Osoba.objects.filter(jmeno="Jan", prijmeni="Novák").exists())
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
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
            ident_cely=":tba",
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

        with patch("api.views.check_permissions", side_effect=permission_side_effect):
            response = self._post_xml(xml, token=self.outsider_token.key)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure()

    def test_user_without_pas_ulozeni_edit_permission_returns_403(self):
        """Uživatel bez oprávnění ``pas_ulozeni_edit`` obdrží HTTP 403."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        def permission_side_effect(action, user, ident=None):
            if action == "pas_edit":
                return True
            if action == "pas_ulozeni_edit":
                return False
            if action == "pas_zapsat_do_projektu" and ident == self.projekt.ident_cely:
                return True
            return True

        with patch("api.views.check_permissions", side_effect=permission_side_effect):
            response = self._post_xml(xml, token=self.outsider_token.key)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure()

    def test_user_without_project_permission_returns_403(self):
        """Uživatel bez oprávnění ``pas_zapsat_do_projektu`` pro daný projekt obdrží HTTP 403."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        def permission_side_effect(action, user, ident=None):
            if action == "pas_ulozeni_edit":
                return True
            if action == "pas_zapsat_do_projektu" and ident == self.projekt.ident_cely:
                return False
            return True

        with patch("api.views.check_permissions", side_effect=permission_side_effect):
            response = self._post_xml(xml, token=self.outsider_token.key)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure()

    def test_valid_file_xml_creates_record_with_correct_values(self):
        """Import souboru ``valid_file.xml`` vytvoří záznam a importovaná data odpovídají obsahu XML."""
        template = self._load_xml("valid_file.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            PREDANO_ORGANIZACE_IDENT=self.organizace.ident_cely,
            **self._required_field_subs(),
        ).encode("utf-8")
        response = self._post_xml(xml)
        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
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
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        historie = list(Historie.objects.filter(vazba=nalez.historie).order_by("datum_zmeny", "id"))

        self.assertEqual(len(historie), 3)
        self.assertEqual([item.typ_zmeny for item in historie], [ZAPSANI_SN, ODESLANI_SN, POTVRZENI_SN])
        self.assertTrue(all(item.poznamka == SamostatnyNalezXmlImportView._IMPORT_HISTORY_NOTE for item in historie))
        self.assertTrue(all(item.uzivatel == self.user for item in historie))
        self.assertTrue(all(item.vazba == nalez.historie for item in historie))
        self._assert_log_success()

    def test_import_stav2_creates_only_two_history_records(self):
        """Import se ``stav=2`` vytvoří pouze záznamy SN01 a SN12, nikoli SN23."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
            stav=2,
        )

        response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self.assertEqual(nalez.stav, SN_ODESLANY)
        historie = list(Historie.objects.filter(vazba=nalez.historie).order_by("datum_zmeny", "id"))
        self.assertEqual(len(historie), 2)
        self.assertEqual([item.typ_zmeny for item in historie], [ZAPSANI_SN, ODESLANI_SN])

    def test_import_stav1_creates_only_one_history_record(self):
        """Import se ``stav=1`` vytvoří pouze záznam SN01."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
            stav=1,
        )

        response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self.assertEqual(nalez.stav, SN_ZAPSANY)
        historie = list(Historie.objects.filter(vazba=nalez.historie).order_by("datum_zmeny", "id"))
        self.assertEqual(len(historie), 1)
        self.assertEqual([item.typ_zmeny for item in historie], [ZAPSANI_SN])

    def test_import_stav2_calls_check_pred_odeslanim(self):
        """Import se ``stav=2`` zavolá ``check_pred_odeslanim`` a nezavolá ``check_pred_potvrzenim``."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
            stav=2,
        )

        with patch.object(
            SamostatnyNalez, "check_pred_odeslanim", autospec=True, return_value=[]
        ) as mock_odeslanim, patch.object(
            SamostatnyNalez, "check_pred_potvrzenim", autospec=True, return_value=[]
        ) as mock_potvrzenim:
            response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_odeslanim.call_count, 1)
        _, kwargs = mock_odeslanim.call_args
        self.assertTrue(kwargs.get("skip_soubory_check"))
        mock_potvrzenim.assert_not_called()

    def test_import_stav3_calls_both_check_pred_odeslanim_and_check_pred_potvrzenim(self):
        """Import se ``stav=3`` zavolá ``check_pred_odeslanim`` i ``check_pred_potvrzenim``."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
            stav=3,
        )

        with patch.object(
            SamostatnyNalez, "check_pred_odeslanim", autospec=True, return_value=[]
        ) as mock_odeslanim, patch.object(
            SamostatnyNalez, "check_pred_potvrzenim", autospec=True, return_value=[]
        ) as mock_potvrzenim:
            response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_odeslanim.call_count, 1)
        _, odeslanim_kwargs = mock_odeslanim.call_args
        self.assertTrue(odeslanim_kwargs.get("skip_soubory_check"))
        self.assertEqual(mock_potvrzenim.call_count, 1)
        _, potvrzenim_kwargs = mock_potvrzenim.call_args
        self.assertTrue(potvrzenim_kwargs.get("skip_soubory_check"))

    def test_import_stav4_returns_422(self):
        """Import se ``stav=4`` selže s HTTP 422 a záznam se nevytvoří (povoleny jsou jen 1, 2, 3)."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
            stav=4,
        )

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure()

    def test_valid_xml_creates_record(self):
        """Validní XML s minimálními poli vytvoří záznam v databázi a vrátí HTTP 200."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )
        response = self._post_xml(xml)
        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self._assert_log_success()

    def test_katastr_filled_from_geom_wkt(self):
        """Import s ``geom_system=4326`` doplní katastr ze souřadnic ``geom_wkt``."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
            geom_wkt="POINT(14.0667 50.0333)",
        )

        response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self.assertEqual(nalez.katastr, RuianKatastr.objects.get(kod=999999))
        self._assert_log_success()

    def test_katastr_filled_from_geom_sjtsk_wkt(self):
        """Import s ``geom_system=5514`` doplní katastr transformací ``geom_sjtsk_wkt`` do WGS-84."""
        template = self._load_xml("minimal_nalez_sjtsk.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            # Transforms to WGS-84 POINT(14.0667 50.0333) — inside the test fixture polygon for kod=999999.
            GEOM_SJTSK_WKT="POINT(-768785.47 -1045458.60)",
            **self._required_field_subs(),
        ).encode("utf-8")

        response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self.assertEqual(nalez.katastr, RuianKatastr.objects.get(kod=999999))
        self._assert_log_success()

    def test_missing_geometry_returns_422(self):
        """Import vrátí HTTP 422, pokud XML neobsahuje žádnou geometrii."""
        template = self._load_xml("minimal_nalez_no_geom.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
        ).encode("utf-8")

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure(response.data)

    def test_geom_outside_cadastre_returns_422(self):
        """Import vrátí HTTP 422, pokud souřadnice nespadají do žádného katastru."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
            # Coordinates in the Atlantic Ocean — outside any cadastre polygon.
            geom_wkt="POINT(0.0 0.0)",
        )

        response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure(response.data)

    def test_valid_xml_with_known_nalezce_links_existing_osoba(self):
        """Import s existujícím ``nalezce`` naváže záznam na existující osobu."""
        template = self._load_xml("nalez_known_nalezce.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            **self._required_field_subs(),
        ).encode("utf-8")

        response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self.assertEqual(nalez.nalezce, self.known_osoba)
        self._assert_log_success()

    def test_valid_xml_with_optional_fields(self):
        """XML s volitelnými poli (hloubka, poznamka, presna_datace) vytvoří záznam se správnými hodnotami."""
        template = self._load_xml("nalez_optional_fields.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            **self._required_field_subs(),
        ).encode("utf-8")
        response = self._post_xml(xml)
        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self.assertEqual(nalez.hloubka, 42)
        self.assertEqual(nalez.poznamka, "testovací poznámka")
        self.assertEqual(nalez.lokalizace, "u lesa")
        self.assertEqual(nalez.presna_datace, "raný středověk")
        self._assert_log_success()

    def test_valid_xml_with_tba_nalezce_creates_osoba_and_links_it(self):
        """Import s ``nalezce id=":tba"`` vytvoří novou osobu a naváže ji na nález."""
        template = self._load_xml("nalez_tba_nalezce.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            **self._required_heslar_subs(),
        ).encode("utf-8")

        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        osoba = Osoba.objects.get(prijmeni="Novák", jmeno="Jan")

        self.assertEqual(osoba.vypis_cely, "Novák, Jan")
        self.assertEqual(osoba.vypis, "Novák, J.")
        self.assertEqual(nalez.nalezce, osoba)
        self._assert_log_success()

    def test_tba_nalezce_reuses_existing_osoba_when_name_matches(self):
        """Import s ``nalezce id=":tba"`` použije existující osobu, pokud shodné jméno a příjmení již existují."""
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            existing_osoba, _ = Osoba.objects.get_or_create(
                prijmeni="Novák",
                jmeno="Jan",
                defaults={
                    "vypis": "Novák, J.",
                    "vypis_cely": "Novák, Jan",
                },
            )
        osoba_count_before = Osoba.objects.count()
        template = self._load_xml("nalez_tba_nalezce.xml").decode("utf-8")
        xml = template.format(
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            **self._required_heslar_subs(),
        ).encode("utf-8")

        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self.assertEqual(nalez.nalezce, existing_osoba)
        self.assertEqual(Osoba.objects.count(), osoba_count_before)
        self._assert_log_success()

    def test_integrity_error_fallback_returns_422(self):
        """``IntegrityError`` způsobená jiným omezením než ``osoba_jmeno_prijmeni_key`` vrátí HTTP 422.

        Ověřuje fallback větev handleru: neznámé omezení integrity vrátí neutrální klíč chybové zprávy
        místo detailní zprávy specifické pro duplicitní osobu.
        """
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )

        with patch("api.views.SamostatnyNalez.save", side_effect=IntegrityError("other constraint violated")):
            response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", response.data)
        self.assertIn("integrity_error", response.data["detail"])
        self.assertNotIn("error", response.data)
        self.assertFalse(SamostatnyNalez.objects.filter(projekt=self.projekt).exists())
        self._assert_log_failure()

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
            ident_cely=":tba",
            projekt_ident=self.projekt.ident_cely,
            pristupnost_ident=self.pristupnost.ident_cely,
        )
        SamostatnyNalezXmlImportView._amcr_schema_cache.clear()

        with patch(
            "api.views._fetch_xsd_bytes",
            side_effect=urllib.error.URLError("simulated network failure"),
        ):
            response = self._post_xml(xml)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("validation_errors", response.data)
        self._assert_log_failure()

    def test_wrong_amcr_namespace_version_returns_422(self):
        """POST s deklarovaným AMČR namespace jiné verze vrátí HTTP 422."""
        xml = self._minimal_nalez_xml(
            ident_cely=":tba",
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
            ident_cely=":tba",
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
            IDENT_CELY=":tba",
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
            IDENT_CELY=":tba",
            PROJEKT_IDENT=self.projekt.ident_cely,
            PRISTUPNOST_IDENT=self.pristupnost.ident_cely,
            **self._required_field_subs(),
        ).encode("utf-8")

        response = self._post_xml(xml)

        nalez = SamostatnyNalez.objects.get(projekt=self.projekt)
        self._assert_xml_success_response(response, nalez.ident_cely)
        self._assert_log_success()


class FetchXsdBytesTests(TestCase):
    """Jednotkové testy pro ``_fetch_xsd_bytes`` a ``_xsd_redis_key``."""

    def setUp(self):
        """Vyčistí Redis cache a in-process slovník před každým testem."""
        cache.clear()
        _XSD_BYTES_CACHE.clear()

    def tearDown(self):
        """Vyčistí Redis cache a in-process slovník po každým testu."""
        cache.clear()
        _XSD_BYTES_CACHE.clear()

    # --- _xsd_redis_key ---

    def test_redis_key_amcr_url_includes_version(self):
        """Klíč pro AMČR URL obsahuje číslo verze."""
        key = _xsd_redis_key("https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd")
        self.assertEqual(key, "xsd_schema:amcr:2.2:https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd")

    def test_redis_key_amcr_url_different_version(self):
        """Klíče pro různé verze AMČR schématu se liší."""
        key_22 = _xsd_redis_key("https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd")
        key_23 = _xsd_redis_key("https://api.aiscr.cz/schema/amcr/2.3/amcr.xsd")
        self.assertNotEqual(key_22, key_23)
        self.assertIn("2.2", key_22)
        self.assertIn("2.3", key_23)

    def test_redis_key_non_amcr_url_uses_full_url(self):
        """Klíč pro W3C URL neobsahuje prefix verze."""
        url = "https://www.w3.org/2001/xml.xsd"
        key = _xsd_redis_key(url)
        self.assertEqual(key, f"xsd_schema:{url}")

    # --- _fetch_xsd_bytes ---

    def test_returns_bytes_from_network_on_cache_miss(self):
        """Při absenci záznamu v cache se bajty stáhnou ze sítě."""

        expected = b"<schema/>"
        mock_response = io.BytesIO(expected)
        with patch("api.views.urllib.request.urlopen", return_value=mock_response) as urlopen_mock:
            result = _fetch_xsd_bytes("https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd")

        self.assertEqual(result, expected)
        urlopen_mock.assert_called_once_with("https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd", timeout=10)

    def test_stores_bytes_in_cache_after_network_fetch(self):
        """Po stažení ze sítě se bajty uloží do cache."""

        url = "https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd"
        expected = b"<schema/>"
        with patch("api.views.urllib.request.urlopen", return_value=io.BytesIO(expected)):
            _fetch_xsd_bytes(url)

        self.assertEqual(cache.get(_xsd_redis_key(url)), expected)

    def test_returns_cached_bytes_without_network_call(self):
        """Při zásahu cache se síť nevolá."""

        url = "https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd"
        cached_bytes = b"<cached/>"
        cache.set(_xsd_redis_key(url), cached_bytes)

        with patch("api.views.urllib.request.urlopen") as urlopen_mock:
            result = _fetch_xsd_bytes(url)

        self.assertEqual(result, cached_bytes)
        urlopen_mock.assert_not_called()

    def test_cache_hit_for_non_amcr_url(self):
        """Cache funguje i pro W3C URL bez verze v klíči."""

        url = "https://www.w3.org/2001/xml.xsd"
        cached_bytes = b"<xml-schema/>"
        cache.set(_xsd_redis_key(url), cached_bytes)

        with patch("api.views.urllib.request.urlopen") as urlopen_mock:
            result = _fetch_xsd_bytes(url)

        self.assertEqual(result, cached_bytes)
        urlopen_mock.assert_not_called()

    def test_propagates_url_error(self):
        """Síťová chyba se propaguje jako ``urllib.error.URLError``."""

        with patch(
            "api.views.urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            with self.assertRaises(urllib.error.URLError):
                _fetch_xsd_bytes("https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd")

    def test_propagates_timeout_error(self):
        """Vypršení časového limitu se propaguje jako ``TimeoutError``."""

        with patch("api.views.urllib.request.urlopen", side_effect=TimeoutError()):
            with self.assertRaises(TimeoutError):
                _fetch_xsd_bytes("https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd")

    def test_network_error_does_not_populate_cache(self):
        """Při síťové chybě se do cache nic neuloží."""

        url = "https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd"
        with patch("api.views.urllib.request.urlopen", side_effect=urllib.error.URLError("err")):
            with self.assertRaises(urllib.error.URLError):
                _fetch_xsd_bytes(url)

        self.assertIsNone(cache.get(_xsd_redis_key(url)))

    def test_second_call_uses_cache(self):
        """Druhé volání se stejnou URL neotevře síťové spojení znovu."""

        url = "https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd"
        content = b"<schema/>"
        with patch("api.views.urllib.request.urlopen", return_value=io.BytesIO(content)) as urlopen_mock:
            _fetch_xsd_bytes(url)
            _fetch_xsd_bytes(url)

        urlopen_mock.assert_called_once()


class SamostatnyNalezEvidencniCisloPatchViewTests(TestCase):
    """Testy pro ``SamostatnyNalezEvidencniCisloPatchView``."""

    databases = {"default", "urgent"}

    def setUp(self):
        """Připraví per-test mocky Fedora repozitáře."""
        super().setUp()
        self._clear_pas_api_settings()

        patcher = patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None)
        patcher.start()
        self.addCleanup(patcher.stop)

        self._fedora_transaction_counter = 0
        transaction_patcher = patch("api.views.FedoraTransaction", side_effect=self._build_mock_fedora_transaction)
        transaction_patcher.start()
        self.addCleanup(transaction_patcher.stop)

        repository_connector_patcher = patch(
            "api.views.FedoraRepositoryConnector", side_effect=self._build_mock_repository_connector
        )
        repository_connector_patcher.start()
        self.addCleanup(repository_connector_patcher.stop)

    def tearDown(self):
        """Po každém testu vyčistí PAS API nastavení a cache."""
        self._clear_pas_api_settings()
        super().tearDown()

    def _build_mock_fedora_transaction(self, *args, **kwargs):
        """
        Vytvoří mock Fedora transakce pro API testy.

        :param args: Poziční argumenty předané při inicializaci ``FedoraTransaction``.
        :param kwargs: Klíčové argumenty předané při inicializaci ``FedoraTransaction``.

        :return: Mock objekt napodobující Fedora transakci.
        """
        self._fedora_transaction_counter += 1
        transaction = Mock()
        transaction.uid = f"test-fedora-transaction-{self._fedora_transaction_counter}"
        transaction.status = Mock()
        return transaction

    def _build_mock_repository_connector(self, record, *args, **kwargs):
        """
        Vytvoří mock repository connector pro čtení XML metadat.

        :param record: Záznam, pro který se metadata čtou.
        :param args: Poziční argumenty předané při inicializaci connectoru.
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
        cache.clear()

    def _patch(self, ident_cely: str, evidencni_cislo: str | None = "EC-TEST-001", token: str | None = None) -> object:
        """
        Odešle PATCH požadavek na endpoint pro aktualizaci evidencni_cislo.

        :param ident_cely: Identifikátor záznamu samostatného nálezu v URL.
        :param evidencni_cislo: Hodnota query parametru ``evidencni_cislo``; ``None`` parametr vynechá.
        :param token: Bearer token; pokud ``None``, použije se ``self.token``.

        :return: Vrací odpověď APIClient.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token or self.token.key}")
        url = reverse(PATCH_URL_NAME, kwargs={"ident_cely": ident_cely})
        params = []
        if evidencni_cislo is not None:
            params.append(f"evidencni_cislo={evidencni_cislo}")
        if params:
            url = f"{url}?{'&'.join(params)}"
        return client.patch(url)

    def _assert_log_entry(self, expected_status: str) -> ApiRequestLog:
        """
        Ověří, že existuje právě jeden log záznam s daným stavem a správným cílem požadavku.

        :param expected_status: Očekávaný stav log záznamu.

        :return: Nalezený log záznam.
        """
        self.assertEqual(ApiRequestLog.objects.count(), 1)
        log_entry = ApiRequestLog.objects.get()
        self.assertEqual(log_entry.status, expected_status)
        self.assertEqual(log_entry.request_target, API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_EVIDENCNI_CISLO_PATCH)
        return log_entry

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená testovací data pro celou třídu."""
        from core.constants import ROLE_ARCHEOLOG_ID, ROLE_BADATEL_ID
        from django.contrib.auth.models import Group
        from django.contrib.gis.geos import MultiPolygon, Point, Polygon
        from heslar.hesla import HESLAR_PROJEKT_TYP
        from heslar.hesla_dynamicka import PRISTUPNOST_ANONYM_ID
        from heslar.models import RuianKatastr, RuianKraj, RuianOkres

        heslare_typ_org, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_ORGANIZACE_TYP, defaults={"nazev": "typ_organizace"}
        )
        cls.typ_organizace, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_typ_org,
            zkratka="T",
            defaults={"ident_cely": "HES-TYPORG-PATCH-001", "heslo": "Testovací typ"},
        )
        heslare_licence, _ = HeslarNazev.objects.get_or_create(id=HESLAR_LICENCE, defaults={"nazev": "licence"})
        cls.licence, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_licence,
            zkratka="L",
            defaults={"ident_cely": "HES-LIC-PATCH-001", "heslo": "Testovací licence"},
        )
        heslare_pristupnost, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_PRISTUPNOST, defaults={"nazev": "pristupnost"}
        )
        cls.pristupnost, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_pristupnost,
            zkratka="A",
            defaults={"ident_cely": "HES-PRST-PATCH-001", "heslo": "Veřejný"},
        )
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

        with patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            cls.organizace, _ = Organizace.objects.get_or_create(
                ident_cely="ORG-TEST-PATCH",
                defaults={
                    "nazev": "Testovací org PATCH",
                    "nazev_zkraceny": "TOPC",
                    "typ_organizace": cls.typ_organizace,
                    "zverejneni_pristupnost": cls.pristupnost,
                    "licence": cls.licence,
                },
            )

        badatel_group, _ = Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        archeolog_group, _ = Group.objects.get_or_create(id=ROLE_ARCHEOLOG_ID, defaults={"name": "archeolog"})

        Permissions.objects.update_or_create(
            main_role=badatel_group,
            action=Permissions.actionChoices.pas_edit,
            defaults={
                "address_in_app": "pas/api/nalez",
                "base": True,
                "status": "<4",
                "ownership": Permissions.ownershipChoices.our,
            },
        )
        Permissions.objects.update_or_create(
            main_role=archeolog_group,
            action=Permissions.actionChoices.pas_edit,
            defaults={
                "address_in_app": "pas/api/nalez",
                "base": True,
                "status": "<4",
                "ownership": Permissions.ownershipChoices.our,
            },
        )

        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="patchuser@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
            )
        cls.user.groups.add(archeolog_group)
        cls.token, _ = Token.objects.get_or_create(user=cls.user)

        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            cls.second_user = User.objects.create_user(  # type: ignore[attr-defined]
                email="patchsecond@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
            )
        cls.second_user.groups.add(archeolog_group)
        cls.second_token, _ = Token.objects.get_or_create(user=cls.second_user)

        with patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None), patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            cls.target_organizace, _ = Organizace.objects.get_or_create(
                ident_cely="ORG-TST-PATCH-TGT",
                defaults={
                    "nazev": "Testovací org PATCH TARGET",
                    "nazev_zkraceny": "TOPT",
                    "typ_organizace": cls.typ_organizace,
                    "zverejneni_pristupnost": cls.pristupnost,
                    "licence": cls.licence,
                },
            )
            cls.outsider_organizace, _ = Organizace.objects.get_or_create(
                ident_cely="ORG-TST-PATCH-OUT",
                defaults={
                    "nazev": "Testovací org PATCH OUTSIDER",
                    "nazev_zkraceny": "TOPO",
                    "typ_organizace": cls.typ_organizace,
                    "zverejneni_pristupnost": cls.pristupnost,
                    "licence": cls.licence,
                },
            )

        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            cls.target_user = User.objects.create_user(  # type: ignore[attr-defined]
                email="patchtarget@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.target_organizace,
            )
        cls.target_user.groups.add(archeolog_group)
        cls.target_token, _ = Token.objects.get_or_create(user=cls.target_user)

        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            cls.badatel_user = User.objects.create_user(  # type: ignore[attr-defined]
                email="patchbadatel@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
            )
        cls.badatel_user.groups.add(badatel_group)
        cls.badatel_token, _ = Token.objects.get_or_create(user=cls.badatel_user)

        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            cls.outsider_user = User.objects.create_user(  # type: ignore[attr-defined]
                email="patchoutsider@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.outsider_organizace,
            )
        cls.outsider_user.groups.add(archeolog_group)
        cls.outsider_token, _ = Token.objects.get_or_create(user=cls.outsider_user)

        kraj, _ = RuianKraj.objects.get_or_create(
            kod=98,
            defaults={
                "nazev": "Testovací kraj PATCH",
                "nazev_en": "Test Region PATCH",
                "rada_id": "P",
                "definicni_bod": Point(15.0, 50.0, srid=4326),
                "hranice": MultiPolygon(Polygon(((15.0, 50.0), (15.1, 50.0), (15.1, 50.1), (15.0, 50.0))), srid=4326),
            },
        )
        okres, _ = RuianOkres.objects.get_or_create(
            kod=9998,
            defaults={
                "nazev": "Testovací okres PATCH",
                "nazev_en": "Test District PATCH",
                "spz": "TP",
                "kraj": kraj,
                "definicni_bod": Point(15.0, 50.0, srid=4326),
                "hranice": MultiPolygon(Polygon(((15.0, 50.0), (15.1, 50.0), (15.1, 50.1), (15.0, 50.0))), srid=4326),
            },
        )
        katastr, _ = RuianKatastr.objects.get_or_create(
            kod=999998,
            defaults={
                "nazev": "Testovací katastr PATCH",
                "okres": okres,
                "definicni_bod": Point(15.0, 50.0, srid=4326),
                "hranice": MultiPolygon(Polygon(((15.0, 50.0), (15.1, 50.0), (15.1, 50.1), (15.0, 50.0))), srid=4326),
            },
        )

        heslare_typ_projektu, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_PROJEKT_TYP, defaults={"nazev": "typ_projektu"}
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
        with patch("projekt.signals.projekt_post_save", lambda **kw: None), patch(
            "xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None
        ):
            cls.projekt, _ = Projekt.objects.get_or_create(
                ident_cely="M-202400098A",
                defaults={
                    "organizace": cls.organizace,
                    "hlavni_katastr": katastr,
                    "typ_projektu": survey_typ_projektu,
                },
            )

        with patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            cls.nalez, _ = SamostatnyNalez.objects.get_or_create(
                ident_cely=IDENT_CELY,
                defaults={
                    "projekt": cls.projekt,
                    "predano_organizace": cls.target_organizace,
                    "pristupnost": cls.pristupnost,
                    "stav": SN_ZAPSANY,
                },
            )
            cls.nalez_second, _ = SamostatnyNalez.objects.get_or_create(
                ident_cely="C-202600009-N00008",
                defaults={
                    "projekt": cls.projekt,
                    "predano_organizace": cls.target_organizace,
                    "pristupnost": cls.pristupnost,
                    "stav": SN_ZAPSANY,
                },
            )

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

    def test_missing_evidencni_cislo_param_returns_400(self):
        """Chybějící query parametr ``evidencni_cislo`` vrátí HTTP 400 a log se stavem FAILURE."""

        response = self._patch(IDENT_CELY, evidencni_cislo=None)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("missing_evidencni_cislo", str(log.errors))
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_empty_evidencni_cislo_param_returns_422(self):
        """Prázdný query parametr ``evidencni_cislo`` vrátí HTTP 422 a log se stavem FAILURE."""

        response = self._patch(IDENT_CELY, evidencni_cislo="")

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("empty_evidencni_cislo", str(log.errors))
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_whitespace_only_evidencni_cislo_returns_422(self):
        """Hodnota ``evidencni_cislo`` tvořená jen bílými znaky vrátí HTTP 422 (po strip = prázdná)."""

        response = self._patch(IDENT_CELY, evidencni_cislo="%20%20")

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("empty_evidencni_cislo", str(log.errors))
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_evidencni_cislo_with_inner_space_returns_422(self):
        """Hodnota ``evidencni_cislo`` obsahující mezeru uvnitř vrátí HTTP 422 a hodnota se neuloží."""

        original_value = self.nalez.evidencni_cislo

        response = self._patch(IDENT_CELY, evidencni_cislo="EC%20TEST%20001")

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("whitespace_in_evidencni_cislo", str(log.errors))
        self.nalez.refresh_from_db()
        self.assertEqual(self.nalez.evidencni_cislo, original_value)
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_evidencni_cislo_is_stripped_before_saving(self):
        """Vedoucí a koncové bílé znaky se před uložením oříznou; do DB se zapíše čistá hodnota."""

        response = self._patch(IDENT_CELY, evidencni_cislo="%20%20EC-STRIP-001%20%20")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.nalez.refresh_from_db()
        self.assertEqual(self.nalez.evidencni_cislo, "EC-STRIP-001")

    def test_evidencni_cislo_too_long_returns_422(self):
        """Příliš dlouhé ``evidencni_cislo`` (přes 255 znaků) vrátí HTTP 422 a log se stavem FAILURE."""

        too_long = "X" * (SamostatnyNalezEvidencniCisloPatchView._MAX_EVIDENCNI_CISLO_LENGTH + 1)

        response = self._patch(IDENT_CELY, evidencni_cislo=too_long)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("evidencni_cislo_too_long", str(log.errors))
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_same_evidencni_cislo_value_returns_422(self):
        """Odeslaná hodnota shodná s aktuální vrátí HTTP 422 a log se stavem FAILURE bez zápisu."""

        self.nalez.evidencni_cislo = "EC-SAME-001"
        self.nalez.save(update_fields=["evidencni_cislo"])

        response = self._patch(IDENT_CELY, evidencni_cislo="EC-SAME-001")

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("no_change", str(log.errors))
        self.nalez.refresh_from_db()
        self.assertEqual(self.nalez.evidencni_cislo, "EC-SAME-001")
        self.assertEqual(Historie.objects.filter(vazba=self.nalez.historie).count(), 0)
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_nonexistent_ident_cely_returns_404(self):
        """Neexistující ``ident_cely`` vrátí HTTP 404 a log se stavem FAILURE."""

        response = self._patch("C-000000000-N99999")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("not_found", str(log.errors))
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}C-000000000-N99999"), 1)

    def test_user_without_pas_edit_permission_returns_403(self):
        """Archeolog mimo vlastnické organizace obdrží HTTP 403 a log se stavem FAILURE."""

        response = self._patch(IDENT_CELY, token=self.outsider_token.key)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("permission_denied", str(log.errors))
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_badatel_with_pas_edit_permission_returns_403(self):
        """Uživatel s rolí Badatel obdrží HTTP 403, i když splňuje vlastnictví i stav ``pas_edit``."""

        response = self._patch(IDENT_CELY, token=self.badatel_token.key)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("permission_denied", str(log.errors))
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_database_error_on_save_returns_500(self):
        """Chyba databáze při ukládání vrátí HTTP 500 a log se stavem FAILURE. Hodnota se neuloží."""

        original_value = self.nalez.evidencni_cislo

        with patch("api.views.SamostatnyNalez.save", side_effect=DatabaseError("db error")):
            response = self._patch(IDENT_CELY)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("detail", response.data)
        self.nalez.refresh_from_db()
        self.assertEqual(self.nalez.evidencni_cislo, original_value)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("internal_error", str(log.errors))
        self.assertEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 0)

    def test_fedora_error_on_save_returns_500(self):
        """Chyba Fedory při ukládání vrátí HTTP 500 a log se stavem FAILURE. Hodnota se neuloží."""

        original_value = self.nalez.evidencni_cislo

        with patch(
            "api.views.SamostatnyNalez.save",
            side_effect=FedoraNoResponseError("http://fedora.example/", "No response", None),
        ):
            response = self._patch(IDENT_CELY)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("detail", response.text)
        self.nalez.refresh_from_db()
        self.assertEqual(self.nalez.evidencni_cislo, original_value)
        self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 0)

    def test_fedora_error_on_read_metadata_returns_500(self):
        """Chyba Fedory při čtení metadat vrátí HTTP 500 a log se stavem FAILURE. Hodnota je uložena v DB."""

        connector = Mock()
        connector.get_metadata.side_effect = FedoraNoResponseError("http://fedora.example/", "No Fedora response", None)

        with patch("api.views.FedoraRepositoryConnector", return_value=connector):
            response = self._patch(IDENT_CELY)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("detail", response.text)
        self.nalez.refresh_from_db()
        self.assertEqual(self.nalez.evidencni_cislo, "EC-TEST-001")
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("fedora_error_reading_metadata", str(log.errors))
        self.assertEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 0)

    def test_valid_request_updates_field_and_returns_200(self):
        """Platný požadavek aktualizuje ``evidencni_cislo``, vrátí HTTP 200 s XML a log se stavem SUCCESS."""
        old_value = self.nalez.evidencni_cislo
        response = self._patch(IDENT_CELY, evidencni_cislo="EC-2024-NEW")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertIn(IDENT_CELY, response.content.decode("utf-8"))

        self.nalez.refresh_from_db()
        self.assertEqual(self.nalez.evidencni_cislo, "EC-2024-NEW")

        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_SUCCESS)
        self.assertEqual(log.ident_cely, IDENT_CELY)

        history = Historie.objects.filter(vazba=self.nalez.historie, typ_zmeny=AKTUALIZACE_SN)
        self.assertEqual(history.count(), 1)
        self.assertEqual(
            history.get().poznamka,
            _("api.views.SamostatnyNalezEvidencniCisloPatchView.history.note")
            % {"old": old_value, "new": "EC-2024-NEW"},
        )

    def test_patch_closes_fedora_transaction_explicitly(self):
        """PATCH uzavře Fedora transakci explicitním voláním ``mark_transaction_as_closed()`` po commitu."""
        fedora_transaction = Mock()

        with patch("api.views.FedoraTransaction", return_value=fedora_transaction):
            response = self._patch(IDENT_CELY, evidencni_cislo="EC-ON-COMMIT-001")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fedora_transaction.mark_transaction_as_closed.assert_called_once()

    def test_igsn_update_called_when_stav_is_sn_archivovany(self):
        """Úspěšný požadavek na archivovaný záznam (SN4) zavolá ``igsn_update`` a vytvoří záznam ``SN34``."""
        self.nalez.stav = SN_ARCHIVOVANY
        self.nalez.save(update_fields=["stav"])
        self.assertFalse(check_permissions(Permissions.actionChoices.pas_edit, self.user, IDENT_CELY))

        with patch("pas.models.SamostatnyNalez.igsn_update") as mock_igsn:
            response = self._patch(IDENT_CELY, evidencni_cislo="EC-ARCHIV-001")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_igsn.assert_called_once_with(False, True)
        self.nalez.refresh_from_db()
        self.assertEqual(self.nalez.evidencni_cislo, "EC-ARCHIV-001")
        archivace = Historie.objects.filter(vazba=self.nalez.historie, typ_zmeny=ARCHIVACE_SN)
        self.assertEqual(archivace.count(), 1)
        self._assert_log_entry(API_REQUEST_LOG_STATUS_SUCCESS)

    def test_doi_write_error_on_archived_record_returns_500(self):
        """Selhání IGSN aktualizace při PATCH na archivovaném záznamu vrátí HTTP 500 a vše vrátí rollbackem."""

        self.nalez.stav = SN_ARCHIVOVANY
        self.nalez.evidencni_cislo = "EC-DOI-OLD-001"
        self.nalez.save(update_fields=["stav", "evidencni_cislo"])

        with patch("pas.models.SamostatnyNalez.igsn_update", side_effect=DoiWriteError("doi write failed")):
            response = self._patch(IDENT_CELY, evidencni_cislo="EC-DOI-NEW-001")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("detail", response.data)
        self.nalez.refresh_from_db()
        self.assertEqual(self.nalez.evidencni_cislo, "EC-DOI-OLD-001")
        self.assertEqual(Historie.objects.filter(vazba=self.nalez.historie, typ_zmeny=AKTUALIZACE_SN).count(), 0)
        self.assertEqual(Historie.objects.filter(vazba=self.nalez.historie, typ_zmeny=ARCHIVACE_SN).count(), 0)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("doi_update_error", str(log.errors))
        self.assertEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 0)

    def test_target_organization_archeolog_can_patch_via_predano_organizace(self):
        """Archeolog cílového muzea je autorizován přes ``predano_organizace``."""
        response = self._patch(IDENT_CELY, evidencni_cislo="EC-TARGET-001", token=self.target_token.key)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.nalez.refresh_from_db()
        self.assertEqual(self.nalez.evidencni_cislo, "EC-TARGET-001")
        self._assert_log_entry(API_REQUEST_LOG_STATUS_SUCCESS)

    def test_igsn_update_not_called_when_stav_is_not_sn_archivovany(self):
        """Úspěšný požadavek na nezarchivovaný záznam nevolá ``igsn_update`` ani nevytváří záznam ``SN34``."""
        with patch("pas.models.SamostatnyNalez.igsn_update") as mock_igsn:
            response = self._patch(IDENT_CELY, evidencni_cislo="EC-NEZARCHIV-001")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_igsn.assert_not_called()
        archivace = Historie.objects.filter(vazba=self.nalez.historie, typ_zmeny=ARCHIVACE_SN)
        self.assertEqual(archivace.count(), 0)
        self._assert_log_entry(API_REQUEST_LOG_STATUS_SUCCESS)

    def test_rate_limit_is_scoped_per_record_for_patch_endpoint(self):
        """Record scope omezuje rychlé PATCH požadavky na jeden záznam napříč různými uživateli."""
        self._set_pas_api_setting(
            "rate_limits",
            [{"scope": "record", "rate": "1/m"}],
        )

        first_response = self._patch(IDENT_CELY, evidencni_cislo="EC-RATE-001")
        second_record_response = self._patch(self.nalez_second.ident_cely, evidencni_cislo="EC-RATE-002")
        throttled_response = self._patch(IDENT_CELY, evidencni_cislo="EC-RATE-003", token=self.second_token.key)

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_record_response.status_code, status.HTTP_200_OK)
        self.assertEqual(throttled_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        self.nalez.refresh_from_db()
        self.nalez_second.refresh_from_db()
        self.assertEqual(self.nalez.evidencni_cislo, "EC-RATE-001")
        self.assertEqual(self.nalez_second.evidencni_cislo, "EC-RATE-002")
        self.assertEqual(ApiRequestLog.objects.count(), 2)

    def test_archeolog_can_patch_archived_record(self):
        """Archeolog smí aktualizovat evidenční číslo záznamu ve stavu SN4 (skip_status=True)."""
        self.nalez.stav = SN_ARCHIVOVANY
        self.nalez.save(update_fields=["stav"])

        with patch("pas.models.SamostatnyNalez.igsn_update"):
            response = self._patch(IDENT_CELY, evidencni_cislo="EC-ARCHIV-SKIP-001")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.nalez.refresh_from_db()
        self.assertEqual(self.nalez.evidencni_cislo, "EC-ARCHIV-SKIP-001")
        self._assert_log_entry(API_REQUEST_LOG_STATUS_SUCCESS)

    def test_badatel_cannot_patch_archived_record(self):
        """Badatel nesmí aktualizovat evidenční číslo záznamu ve stavu SN4, i když splňuje vlastnictví."""

        self.nalez.stav = SN_ARCHIVOVANY
        self.nalez.save(update_fields=["stav"])

        response = self._patch(IDENT_CELY, token=self.badatel_token.key, evidencni_cislo="EC-ARCHIV-BADATEL-001")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("permission_denied", str(log.errors))
        self.nalez.refresh_from_db()
        self.assertNotEqual(self.nalez.evidencni_cislo, "EC-ARCHIV-BADATEL-001")
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_locked_record_returns_429_on_patch(self):
        """PATCH na zamčený záznam vrátí HTTP 429 a nebude čekat ani měnit stav záznamu."""

        self._set_pas_api_setting("record_lock_params", {"max_retries": 1, "retry_delay": 0.001})
        lock_key = f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"
        cache.set(lock_key, 1, timeout=300)

        response = self._patch(IDENT_CELY, evidencni_cislo="EC-LOCKED-001")

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("detail", response.data)
        self.assertIn("record_locked", str(response.data["detail"]))
        self.nalez.refresh_from_db()
        self.assertNotEqual(self.nalez.evidencni_cislo, "EC-LOCKED-001")
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("record_locked", str(log.errors))

    def test_lock_is_released_after_successful_patch(self):
        """Po úspěšném PATCH je Redis zámek uvolněn (hodnota 0)."""

        response = self._patch(IDENT_CELY, evidencni_cislo="EC-UNLOCK-001")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lock_key = f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"
        self.assertEqual(cache.get(lock_key), 0)

    def test_patch_on_different_record_succeeds_while_one_is_locked(self):
        """Zamčení jednoho záznamu neblokuje PATCH na jiný záznam."""

        self._set_pas_api_setting("record_lock_params", {"max_retries": 1, "retry_delay": 0.001})
        lock_key = f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"
        cache.set(lock_key, 1, timeout=300)

        response = self._patch(self.nalez_second.ident_cely, evidencni_cislo="EC-OTHER-001")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.nalez_second.refresh_from_db()
        self.assertEqual(self.nalez_second.evidencni_cislo, "EC-OTHER-001")
        self.assertEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{self.nalez_second.ident_cely}"), 0)
        self.assertEqual(cache.get(lock_key), 1)


class SamostatnyNalezFotografieUploadViewTests(TestCase):
    """Testy pro ``SamostatnyNalezFotografieUploadView``."""

    databases = {"default", "urgent"}

    def setUp(self):
        """Připraví per-test mocky Fedora repozitáře."""
        super().setUp()
        self._clear_pas_api_settings()

        patcher = patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None)
        patcher.start()
        self.addCleanup(patcher.stop)

        self._fedora_transaction_counter = 0
        transaction_patcher = patch("api.views.FedoraTransaction", side_effect=self._build_mock_fedora_transaction)
        transaction_patcher.start()
        self.addCleanup(transaction_patcher.stop)

        repository_connector_patcher = patch(
            "api.views.FedoraRepositoryConnector", side_effect=self._build_mock_repository_connector
        )
        repository_connector_patcher.start()
        self.addCleanup(repository_connector_patcher.stop)

    def tearDown(self):
        """Po každém testu vyčistí PAS API nastavení a cache."""
        self._clear_pas_api_settings()
        super().tearDown()

    def _build_mock_fedora_transaction(self, *args, **kwargs):
        """Vytvoří mock Fedora transakce pro API testy."""
        self._fedora_transaction_counter += 1
        transaction = Mock()
        transaction.uid = f"test-fedora-transaction-{self._fedora_transaction_counter}"
        transaction.status = Mock()
        return transaction

    def _build_mock_repository_connector(self, record, *args, **kwargs):
        """Vytvoří mock repository connector pro uložení fotografie a čtení XML metadat."""
        connector = Mock()
        connector.record = record
        connector.get_metadata.return_value = (
            f"<amcr:amcr><amcr:samostatny_nalez><amcr:ident_cely>{record.ident_cely}</amcr:ident_cely>"
            f"</amcr:samostatny_nalez></amcr:amcr>"
        ).encode("utf-8")
        connector.save_binary_file.side_effect = lambda file_name, content_type, binary_data: self._mock_binary_file(
            record,
            file_name,
            binary_data,
        )
        return connector

    def _clear_pas_api_settings(self) -> None:
        """Vyčistí testovací ``CustomAdminSettings`` a cache pro PAS API."""
        CustomAdminSettings.objects.filter(item_group="pas_api").delete()
        cache.clear()

    @classmethod
    def _minimal_photo_bytes(cls) -> bytes:
        """Vrátí minimální validní PNG obrázek."""
        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/a5sAAAAASUVORK5CYII="
        )

    @staticmethod
    def _content_digest(file_bytes: bytes) -> str:
        """Vrátí hodnotu hlavičky ``Content-Digest`` pro nahrávaný soubor."""
        digest = base64.b64encode(hashlib.sha512(file_bytes).digest()).decode("ascii")
        return f"sha-512=:{digest}:"

    @staticmethod
    def _mock_binary_file(record: SamostatnyNalez, file_name: str, binary_data: io.BytesIO) -> Mock:
        """Vytvoří mock objektu ``RepositoryBinaryFile``."""
        binary_data.seek(0)
        payload = binary_data.getvalue()
        binary_data.seek(0)
        rep_bin_file = Mock()
        rep_bin_file.sha_512 = hashlib.sha512(payload).hexdigest()
        rep_bin_file.size_mb = len(payload) / 1_000_000
        rep_bin_file.url_without_domain = f"/fedora/{record.ident_cely}/{file_name}"
        return rep_bin_file

    def _post_file(
        self,
        ident_cely: str,
        file_bytes: bytes | None,
        filename: str = "photo.png",
        token: str | None = None,
        content_digest: str | None = None,
        include_content_digest: bool = True,
    ):
        """
        Odešle POST požadavek s fotografií na endpoint pro update nálezu.

        :param ident_cely: ``ident_cely`` záznamu v URL.
        :param file_bytes: Obsah souboru jako bajty nebo ``None`` pro požadavek bez souboru.
        :param filename: Název odesílaného souboru.
        :param token: Bearer token; pokud ``None``, použije se ``self.token``.
        :param content_digest: Explicitní hodnota hlavičky ``Content-Digest``.
        :param include_content_digest: Pokud ``False``, hlavička se nepošle.

        :return: Odpověď ``APIClient``.
        """
        client = APIClient()
        resolved_token = self.token.key if token is None else token
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resolved_token}")
        if include_content_digest and file_bytes is not None:
            client.credentials(
                HTTP_AUTHORIZATION=f"Bearer {resolved_token}",
                HTTP_CONTENT_DIGEST=content_digest or self._content_digest(file_bytes),
            )

        url = reverse(FOTO_UPLOAD_URL_NAME, kwargs={"ident_cely": ident_cely})
        data = {}
        if file_bytes is not None:
            data["file"] = SimpleUploadedFile(filename, file_bytes, content_type="application/octet-stream")
        return client.post(url, data, format="multipart")

    def _patch_evidencni_cislo(
        self,
        ident_cely: str,
        evidencni_cislo: str,
        token: str | None = None,
    ):
        """
        Odešle PATCH požadavek na endpoint pro aktualizaci evidenčního čísla.

        :param ident_cely: ``ident_cely`` záznamu v URL.
        :param evidencni_cislo: Nová hodnota query parametru ``evidencni_cislo``.
        :param token: Bearer token; pokud ``None``, použije se ``self.token``.

        :return: Odpověď ``APIClient``.
        """
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token or self.token.key}")
        url = reverse(PATCH_URL_NAME, kwargs={"ident_cely": ident_cely})
        return client.patch(f"{url}?evidencni_cislo={evidencni_cislo}")

    def _assert_log_entry(self, expected_status: str) -> ApiRequestLog:
        """Ověří, že existuje právě jeden log záznam se zadaným stavem a cílem."""
        self.assertEqual(ApiRequestLog.objects.count(), 1)
        log_entry = ApiRequestLog.objects.get()
        self.assertEqual(log_entry.status, expected_status)
        self.assertEqual(log_entry.request_target, API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_FOTOGRAFIE_UPLOAD)
        return log_entry

    def _assert_attached_files(
        self, record: SamostatnyNalez, expected_count: int, expected_name: str | None = None
    ) -> None:
        """Ověří počet připojených fotografií a volitelně i jméno první z nich."""
        files = record.soubory.soubory.order_by("id")
        self.assertEqual(files.count(), expected_count)
        if expected_count == 1:
            soubor = files.get()
            self.assertIsInstance(soubor, Soubor)
            if expected_name is not None:
                self.assertEqual(soubor.nazev, expected_name)

    def _assert_file_upload_history(self, expected_count: int, expected_note: str | None = None) -> None:
        """Ověří záznam historie nahrání na vzniklém souboru."""
        if expected_count == 0:
            self.assertEqual(self.nalez.soubory.soubory.count(), 0)
            return

        soubor = self.nalez.soubory.soubory.get()
        history = Historie.objects.filter(vazba=soubor.historie, typ_zmeny=NAHRANI_SBR).order_by("id")
        self.assertEqual(history.count(), expected_count)
        if expected_count == 1:
            record = history.get()
            self.assertEqual(record.uzivatel, self.user)
            if expected_note is not None:
                self.assertEqual(record.poznamka, expected_note)

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená testovací data pro celou třídu."""
        from core.constants import ROLE_ARCHEOLOG_ID, ROLE_BADATEL_ID
        from django.contrib.auth.models import Group
        from django.contrib.gis.geos import MultiPolygon, Point, Polygon
        from heslar.hesla import HESLAR_PROJEKT_TYP
        from heslar.hesla_dynamicka import PRISTUPNOST_ANONYM_ID
        from heslar.models import RuianKatastr, RuianKraj, RuianOkres

        heslare_typ_org, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_ORGANIZACE_TYP, defaults={"nazev": "typ_organizace"}
        )
        cls.typ_organizace, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_typ_org,
            zkratka="T",
            defaults={"ident_cely": "HES-TYPORG-UPDATE-001", "heslo": "Testovací typ"},
        )
        heslare_licence, _ = HeslarNazev.objects.get_or_create(id=HESLAR_LICENCE, defaults={"nazev": "licence"})
        cls.licence, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_licence,
            zkratka="L",
            defaults={"ident_cely": "HES-LIC-UPDATE-001", "heslo": "Testovací licence"},
        )
        heslare_pristupnost, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_PRISTUPNOST, defaults={"nazev": "pristupnost"}
        )
        cls.pristupnost, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_pristupnost,
            zkratka="A",
            defaults={"ident_cely": "HES-PRST-UPDATE-001", "heslo": "Veřejný"},
        )
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

        with patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            cls.organizace, _ = Organizace.objects.get_or_create(
                ident_cely="ORG-TEST-UPDATE",
                defaults={
                    "nazev": "Testovací org UPDATE",
                    "nazev_zkraceny": "TOUP",
                    "typ_organizace": cls.typ_organizace,
                    "zverejneni_pristupnost": cls.pristupnost,
                    "licence": cls.licence,
                },
            )

        badatel_group, _ = Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        archeolog_group, _ = Group.objects.get_or_create(id=ROLE_ARCHEOLOG_ID, defaults={"name": "archeolog"})

        Permissions.objects.get_or_create(
            main_role=badatel_group,
            action=Permissions.actionChoices.pas_edit,
            defaults={"address_in_app": "pas/api/nalez", "base": True},
        )
        Permissions.objects.get_or_create(
            main_role=archeolog_group,
            action=Permissions.actionChoices.pas_edit,
            defaults={"address_in_app": "pas/api/nalez", "base": True},
        )
        Permissions.objects.get_or_create(
            main_role=archeolog_group,
            action=Permissions.actionChoices.soubor_nahrat_pas,
            defaults={"address_in_app": "pas/api/nalez/upload-foto", "base": True},
        )

        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="xmlupdate@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
            )
        cls.user.groups.add(archeolog_group)
        cls.token, _ = Token.objects.get_or_create(user=cls.user)

        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            cls.second_user = User.objects.create_user(  # type: ignore[attr-defined]
                email="xmlupdate-second@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
            )
        cls.second_user.groups.add(archeolog_group)
        cls.second_token, _ = Token.objects.get_or_create(user=cls.second_user)

        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            cls.outsider_user = User.objects.create_user(  # type: ignore[attr-defined]
                email="xmlupdate-outsider@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
            )
        cls.outsider_token, _ = Token.objects.get_or_create(user=cls.outsider_user)

        kraj, _ = RuianKraj.objects.get_or_create(
            kod=97,
            defaults={
                "nazev": "Testovací kraj UPDATE",
                "nazev_en": "Test Region UPDATE",
                "rada_id": "U",
                "definicni_bod": Point(15.0, 50.0, srid=4326),
                "hranice": MultiPolygon(Polygon(((15.0, 50.0), (15.1, 50.0), (15.1, 50.1), (15.0, 50.0))), srid=4326),
            },
        )
        okres, _ = RuianOkres.objects.get_or_create(
            kod=9997,
            defaults={
                "nazev": "Testovací okres UPDATE",
                "nazev_en": "Test District UPDATE",
                "spz": "TU",
                "kraj": kraj,
                "definicni_bod": Point(15.0, 50.0, srid=4326),
                "hranice": MultiPolygon(Polygon(((15.0, 50.0), (15.1, 50.0), (15.1, 50.1), (15.0, 50.0))), srid=4326),
            },
        )
        katastr, _ = RuianKatastr.objects.get_or_create(
            kod=999997,
            defaults={
                "nazev": "Testovací katastr UPDATE",
                "okres": okres,
                "definicni_bod": Point(15.0, 50.0, srid=4326),
                "hranice": MultiPolygon(Polygon(((15.0, 50.0), (15.1, 50.0), (15.1, 50.1), (15.0, 50.0))), srid=4326),
            },
        )

        heslare_typ_projektu, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_PROJEKT_TYP, defaults={"nazev": "typ_projektu"}
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
        with patch("projekt.signals.projekt_post_save", lambda **kw: None), patch(
            "xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None
        ):
            cls.projekt, _ = Projekt.objects.get_or_create(
                ident_cely="M-202400097A",
                defaults={
                    "organizace": cls.organizace,
                    "hlavni_katastr": katastr,
                    "typ_projektu": survey_typ_projektu,
                },
            )

        with patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            cls.nalez, _ = SamostatnyNalez.objects.get_or_create(
                ident_cely=IDENT_CELY,
                defaults={
                    "projekt": cls.projekt,
                    "pristupnost": cls.pristupnost,
                    "geom": Point(14.42, 50.08, srid=4326),
                    "geom_system": "4326",
                    "stav": SN_ZAPSANY,
                },
            )
            cls.nalez_second, _ = SamostatnyNalez.objects.get_or_create(
                ident_cely="C-202600009-N00009",
                defaults={
                    "projekt": cls.projekt,
                    "pristupnost": cls.pristupnost,
                    "geom": Point(14.43, 50.09, srid=4326),
                    "geom_system": "4326",
                    "stav": SN_ZAPSANY,
                },
            )

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

    def test_missing_file_returns_400(self):
        """POST bez souboru vrátí HTTP 400 a nic nepřipojí."""

        response = self._post_file(IDENT_CELY, file_bytes=None)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("missing_file", str(log.errors))
        self._assert_attached_files(self.nalez, 0)

    def test_multiple_files_returns_400(self):
        """POST s více než jedním souborem v poli ``file`` je explicitně odmítnut HTTP 400."""

        photo = self._minimal_photo_bytes()
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.token.key}",
            HTTP_CONTENT_DIGEST=self._content_digest(photo),
        )
        url = reverse(FOTO_UPLOAD_URL_NAME, kwargs={"ident_cely": IDENT_CELY})
        data = {
            "file": [
                SimpleUploadedFile("first.png", photo, content_type="application/octet-stream"),
                SimpleUploadedFile("second.png", photo, content_type="application/octet-stream"),
            ],
        }

        response = client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("multiple_files", str(log.errors))
        self._assert_attached_files(self.nalez, 0)
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_nonexistent_ident_cely_returns_404(self):
        """Neexistující ``ident_cely`` vrátí HTTP 404 a fotografii nevytvoří."""

        photo = self._minimal_photo_bytes()

        response = self._post_file("C-000000000-N99999", photo)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("not_found", str(log.errors))
        self._assert_attached_files(self.nalez, 0)
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}C-000000000-N99999"), 1)

    def test_content_digest_mismatch_returns_422(self):
        """Neodpovídající ``Content-Digest`` vrátí HTTP 422 a fotografii nevytvoří."""

        photo = self._minimal_photo_bytes()
        wrong_digest = f"sha-512=:{base64.b64encode(hashlib.sha512(b'wrong').digest()).decode('ascii')}:"

        response = self._post_file(IDENT_CELY, photo, content_digest=wrong_digest)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("digest", str(log.errors))
        self._assert_attached_files(self.nalez, 0)
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_missing_content_digest_returns_400(self):
        """Chybějící hlavička ``Content-Digest`` vrátí HTTP 400 a fotografii nevytvoří."""

        photo = self._minimal_photo_bytes()

        response = self._post_file(IDENT_CELY, photo, include_content_digest=False)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("digest", str(log.errors))
        self._assert_attached_files(self.nalez, 0)
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_file_too_large_returns_422(self):
        """Soubor přes limit velikosti vrátí HTTP 422 a fotografii nevytvoří."""

        photo = self._minimal_photo_bytes()

        with patch("api.views.MAX_PAS_API_FOTOGRAFIE_FILE_SIZE_BYTES", 1):
            response = self._post_file(IDENT_CELY, photo)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("file_too_large", str(log.errors))
        self._assert_attached_files(self.nalez, 0)
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_user_without_file_upload_permission_returns_403(self):
        """Uživatel bez oprávnění ``soubor_nahrat_pas`` obdrží HTTP 403."""

        photo = self._minimal_photo_bytes()

        with patch("api.views.check_permissions", return_value=False):
            response = self._post_file(IDENT_CELY, photo, token=self.outsider_token.key)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("permission_denied", str(log.errors))
        self._assert_attached_files(self.nalez, 0)
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_non_image_file_returns_422(self):
        """Soubor s nepovoleným MIME typem vrátí HTTP 422."""

        response = self._post_file(IDENT_CELY, b"plain-text", filename="note.txt")

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("mime", str(log.errors))
        self._assert_attached_files(self.nalez, 0)
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_mime_validation_uses_pas_api_path(self):
        """Upload předá ``check_mime_for_url`` skutečnou cestu PAS API endpointu."""
        photo = self._minimal_photo_bytes()
        expected_path = reverse(FOTO_UPLOAD_URL_NAME, kwargs={"ident_cely": IDENT_CELY})

        with patch("api.views.Soubor.check_mime_for_url", return_value=True) as mock_mime:
            response = self._post_file(IDENT_CELY, photo)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_mime.assert_called_once()
        self.assertEqual(mock_mime.call_args.args[1], expected_path)

    @staticmethod
    def _minimal_heif_container(major_brand: bytes) -> bytes:
        """
        Sestaví minimální ISO BMFF ``ftyp`` box s daným ``major_brand``.

        Výstup je validní úvod HEIC/HEIF souboru (rozpoznatelný podle hlavičky),
        nikoli kompletní obrazový soubor. Pro účely testů endpointu, který kontroluje
        MIME typ a ukládá binární data, je tento prefix dostatečný.

        :param major_brand: Čtyřznaková značka formátu (např. ``b"heic"`` nebo ``b"mif1"``).
        :return: Bajtová sekvence odpovídající minimálnímu ``ftyp`` boxu.
        """
        compatible_brands = b"mif1" + b"heic" + b"heif"
        box_body = major_brand + b"\x00\x00\x00\x00" + compatible_brands
        box_size = (8 + len(box_body)).to_bytes(4, "big")
        return box_size + b"ftyp" + box_body

    def test_heic_mime_is_accepted(self):
        """Soubor s MIME typem ``image/heic`` projde validací a upload skončí HTTP 201."""
        heic_bytes = self._minimal_heif_container(b"heic")

        with patch("api.views.Soubor.get_mime_types", return_value="image/heic"), patch(
            "api.views.Soubor.get_file_extension_by_mime", return_value=("heic", "heif")
        ):
            response = self._post_file(IDENT_CELY, heic_bytes, filename="photo.heic")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self._assert_log_entry(API_REQUEST_LOG_STATUS_SUCCESS)
        self._assert_attached_files(self.nalez, 1)

    def test_heif_mime_is_accepted(self):
        """Soubor s MIME typem ``image/heif`` projde validací a upload skončí HTTP 201."""
        heif_bytes = self._minimal_heif_container(b"mif1")

        with patch("api.views.Soubor.get_mime_types", return_value="image/heif"), patch(
            "api.views.Soubor.get_file_extension_by_mime", return_value=("heic", "heif")
        ):
            response = self._post_file(IDENT_CELY, heif_bytes, filename="photo.heif")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self._assert_log_entry(API_REQUEST_LOG_STATUS_SUCCESS)
        self._assert_attached_files(self.nalez, 1)

    def test_antivirus_virus_found_returns_422(self):
        """Soubor označený antivirem jako škodlivý vrátí HTTP 422."""

        photo = self._minimal_photo_bytes()

        with patch("api.views.Soubor.check_antivirus", return_value=AntivirusCheckResult.VIRUS_FOUND):
            response = self._post_file(IDENT_CELY, photo)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("virus", str(log.errors))
        self._assert_attached_files(self.nalez, 0)
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_antivirus_check_failure_returns_500(self):
        """Selhání antivirové kontroly vrátí HTTP 500."""

        photo = self._minimal_photo_bytes()

        with patch("api.views.Soubor.check_antivirus", return_value=AntivirusCheckResult.CHECK_FAILED):
            response = self._post_file(IDENT_CELY, photo)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("check_failed", str(log.errors))
        self._assert_attached_files(self.nalez, 0)
        self.assertNotEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 1)

    def test_database_error_on_soubor_save_returns_500(self):
        """Chyba databáze při uložení ``Soubor`` vrátí HTTP 500 a fotografii nevytvoří."""

        photo = self._minimal_photo_bytes()

        with patch("core.models.Soubor.save", side_effect=DatabaseError("db error")):
            response = self._post_file(IDENT_CELY, photo)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("internal_error", str(log.errors))
        self._assert_attached_files(self.nalez, 0)
        self.assertEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 0)

    def test_fedora_error_on_save_returns_500(self):
        """Chyba Fedory při ukládání fotografie vrátí HTTP 500."""

        photo = self._minimal_photo_bytes()
        connector = self._build_mock_repository_connector(self.nalez)
        connector.save_binary_file.side_effect = FedoraNoResponseError("http://fedora.example/", "No response", None)

        with patch("api.views.FedoraRepositoryConnector", return_value=connector):
            response = self._post_file(IDENT_CELY, photo)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("internal_error", str(log.errors))
        self._assert_attached_files(self.nalez, 0)
        self.assertEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 0)

    def test_fedora_error_on_read_metadata_returns_500(self):
        """Chyba při čtení metadat z Fedory vrátí HTTP 500, ale fotografie zůstane připojena."""

        photo = self._minimal_photo_bytes()
        save_connector = self._build_mock_repository_connector(self.nalez)
        metadata_connector = Mock()
        metadata_connector.get_metadata.side_effect = FedoraNoResponseError(
            "http://fedora.example/", "No Fedora response", None
        )

        with patch("api.views.FedoraRepositoryConnector", side_effect=[save_connector, metadata_connector]):
            response = self._post_file(IDENT_CELY, photo)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("detail", response.data)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("fedora_error_reading_metadata", str(log.errors))
        self._assert_attached_files(self.nalez, 1, expected_name="C202600009N00007F01.png")
        self._assert_file_upload_history(1, expected_note="photo.png")
        self.assertEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 0)

    def test_success_returns_metadata_and_attaches_photo(self):
        """Platný upload vrátí metadata, uloží fotografii a zapíše historii souboru."""
        photo = self._minimal_photo_bytes()

        response = self._post_file(IDENT_CELY, photo)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertIn(IDENT_CELY, response.content.decode("utf-8"))
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_SUCCESS)
        self.assertEqual(log.ident_cely, IDENT_CELY)
        self._assert_attached_files(self.nalez, 1, expected_name="C202600009N00007F01.png")
        self._assert_file_upload_history(1, expected_note="photo.png")
        archivace = Historie.objects.filter(vazba=self.nalez.historie, typ_zmeny=ARCHIVACE_SN)
        self.assertEqual(archivace.count(), 0)

    def test_igsn_update_called_when_stav_is_sn_archivovany(self):
        """Úspěšný upload archivovaného záznamu (SN4) zavolá ``igsn_update`` a vytvoří záznam ``SN34``."""
        self.nalez.stav = SN_ARCHIVOVANY
        self.nalez.save(update_fields=["stav"])
        photo = self._minimal_photo_bytes()

        with patch("pas.models.SamostatnyNalez.igsn_update") as mock_igsn:
            response = self._post_file(IDENT_CELY, photo)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_igsn.assert_called_once_with(False, True)
        archivace = Historie.objects.filter(vazba=self.nalez.historie, typ_zmeny=ARCHIVACE_SN)
        self.assertEqual(archivace.count(), 1)
        self._assert_log_entry(API_REQUEST_LOG_STATUS_SUCCESS)
        self._assert_attached_files(self.nalez, 1, expected_name="C202600009N00007F01.png")

    def test_doi_write_error_on_archived_record_returns_500(self):
        """Selhání IGSN aktualizace při uploadu na archivovaný záznam vrátí HTTP 500 a soubor se neuloží."""

        self.nalez.stav = SN_ARCHIVOVANY
        self.nalez.save(update_fields=["stav"])
        photo = self._minimal_photo_bytes()

        with patch("pas.models.SamostatnyNalez.igsn_update", side_effect=DoiWriteError("doi write failed")):
            response = self._post_file(IDENT_CELY, photo)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("detail", response.data)
        self._assert_attached_files(self.nalez, 0)
        self.assertEqual(Historie.objects.filter(vazba=self.nalez.historie, typ_zmeny=ARCHIVACE_SN).count(), 0)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("internal_error", str(log.errors))
        self.assertEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"), 0)

    def test_igsn_update_not_called_when_stav_is_not_sn_archivovany(self):
        """Úspěšný upload nezarchivovaného záznamu nevolá ``igsn_update`` ani nevytváří ``SN34``."""
        photo = self._minimal_photo_bytes()

        with patch("pas.models.SamostatnyNalez.igsn_update") as mock_igsn:
            response = self._post_file(IDENT_CELY, photo)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_igsn.assert_not_called()
        archivace = Historie.objects.filter(vazba=self.nalez.historie, typ_zmeny=ARCHIVACE_SN)
        self.assertEqual(archivace.count(), 0)
        self._assert_log_entry(API_REQUEST_LOG_STATUS_SUCCESS)

    def test_rate_limit_is_scoped_per_record_for_binary_upload_endpoint(self):
        """Record scope omezuje rychlé uploady na jeden záznam napříč různými uživateli."""
        self._set_pas_api_setting(
            "rate_limits",
            [{"scope": "record", "rate": "1/m"}],
        )
        first_photo = self._minimal_photo_bytes()
        second_photo = self._minimal_photo_bytes()

        first_response = self._post_file(IDENT_CELY, first_photo, filename="first.png")
        second_record_response = self._post_file(self.nalez_second.ident_cely, second_photo, filename="second.png")
        throttled_response = self._post_file(IDENT_CELY, first_photo, filename="third.png", token=self.second_token.key)

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_record_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(throttled_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        self._assert_attached_files(self.nalez, 1, expected_name="C202600009N00007F01.png")
        self._assert_attached_files(self.nalez_second, 1, expected_name="C202600009N00009F01.png")
        self.assertEqual(ApiRequestLog.objects.count(), 2)

    def test_record_rate_limit_is_shared_between_patch_and_upload_for_same_ident(self):
        """PATCH a upload sdílí stejný record-level limit pro stejné ``ident_cely``."""
        self._set_pas_api_setting(
            "rate_limits",
            [{"scope": "record", "rate": "1/m"}],
        )
        photo = self._minimal_photo_bytes()

        patch_response = self._patch_evidencni_cislo(IDENT_CELY, "EC-CROSS-001")
        throttled_upload_response = self._post_file(IDENT_CELY, photo, filename="cross.png")
        other_record_upload_response = self._post_file(self.nalez_second.ident_cely, photo, filename="other.png")

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(throttled_upload_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(other_record_upload_response.status_code, status.HTTP_201_CREATED)

    def test_record_rate_limit_is_shared_between_upload_and_patch_for_same_ident(self):
        """Upload a PATCH sdílí stejný record-level limit pro stejné ``ident_cely``."""
        self._set_pas_api_setting(
            "rate_limits",
            [{"scope": "record", "rate": "1/m"}],
        )
        photo = self._minimal_photo_bytes()

        upload_response = self._post_file(IDENT_CELY, photo, filename="cross.png")
        throttled_patch_response = self._patch_evidencni_cislo(IDENT_CELY, "EC-CROSS-002")
        other_record_patch_response = self._patch_evidencni_cislo(self.nalez_second.ident_cely, "EC-CROSS-003")

        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(throttled_patch_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(other_record_patch_response.status_code, status.HTTP_200_OK)

    def test_locked_record_returns_429_on_upload(self):
        """Upload na zamčený záznam vrátí HTTP 429 a neuloží žádný soubor."""

        self._set_pas_api_setting("record_lock_params", {"max_retries": 1, "retry_delay": 0.001})
        lock_key = f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"
        cache.set(lock_key, 1, timeout=300)
        photo = self._minimal_photo_bytes()

        response = self._post_file(IDENT_CELY, photo)

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("detail", response.data)
        self.assertIn("record_locked", str(response.data["detail"]))
        self._assert_attached_files(self.nalez, 0)
        log = self._assert_log_entry(API_REQUEST_LOG_STATUS_FAILURE)
        self.assertIn("record_locked", str(log.errors))

    def test_lock_is_released_after_successful_upload(self):
        """Po úspěšném uploadu je Redis zámek uvolněn (hodnota 0)."""

        photo = self._minimal_photo_bytes()
        response = self._post_file(IDENT_CELY, photo)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        lock_key = f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"
        self.assertEqual(cache.get(lock_key), 0)

    def test_upload_on_different_record_succeeds_while_one_is_locked(self):
        """Zamčení jednoho záznamu neblokuje upload na jiný záznam."""

        self._set_pas_api_setting("record_lock_params", {"max_retries": 1, "retry_delay": 0.001})
        lock_key = f"{_RECORD_LOCK_PREFIX}{IDENT_CELY}"
        cache.set(lock_key, 1, timeout=300)
        photo = self._minimal_photo_bytes()

        response = self._post_file(self.nalez_second.ident_cely, photo, filename="other.png")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self._assert_attached_files(self.nalez_second, 1)
        self.assertEqual(cache.get(f"{_RECORD_LOCK_PREFIX}{self.nalez_second.ident_cely}"), 0)
        self.assertEqual(cache.get(lock_key), 1)


class SamostatnyNalezGetCreateOrgTests(TestCase):
    """Testy pro ``SamostatnyNalez.get_create_org``."""

    databases = {"default", "urgent"}

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená testovací data pro celou třídu."""
        from django.contrib.gis.geos import MultiPolygon, Point, Polygon
        from heslar.hesla import HESLAR_PROJEKT_TYP
        from heslar.hesla_dynamicka import (
            PRISTUPNOST_ANONYM_ID,
            TYP_PROJEKTU_PRUZKUM_ID,
        )
        from heslar.models import RuianKatastr, RuianKraj, RuianOkres

        heslare_typ_org, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_ORGANIZACE_TYP, defaults={"nazev": "typ_organizace"}
        )
        typ_organizace, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_typ_org,
            zkratka="T",
            defaults={"ident_cely": "HES-TYPORG-GCORG-001", "heslo": "Testovací typ"},
        )
        heslare_licence, _ = HeslarNazev.objects.get_or_create(id=HESLAR_LICENCE, defaults={"nazev": "licence"})
        licence, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_licence,
            zkratka="L",
            defaults={"ident_cely": "HES-LIC-GCORG-001", "heslo": "Testovací licence"},
        )
        heslare_pristupnost, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_PRISTUPNOST, defaults={"nazev": "pristupnost"}
        )
        cls.pristupnost, _ = Heslar.objects.get_or_create(
            nazev_heslare=heslare_pristupnost,
            zkratka="A",
            defaults={"ident_cely": "HES-PRST-GCORG-001", "heslo": "Veřejný"},
        )
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

        with patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            cls.org_a, _ = Organizace.objects.get_or_create(
                ident_cely="ORG-GCORG-A",
                defaults={
                    "nazev": "Testovací org A",
                    "nazev_zkraceny": "TORA",
                    "typ_organizace": typ_organizace,
                    "zverejneni_pristupnost": cls.pristupnost,
                    "licence": licence,
                },
            )
            cls.org_b, _ = Organizace.objects.get_or_create(
                ident_cely="ORG-GCORG-B",
                defaults={
                    "nazev": "Testovací org B",
                    "nazev_zkraceny": "TORB",
                    "typ_organizace": typ_organizace,
                    "zverejneni_pristupnost": cls.pristupnost,
                    "licence": licence,
                },
            )

        kraj, _ = RuianKraj.objects.get_or_create(
            kod=96,
            defaults={
                "nazev": "Testovací kraj GCORG",
                "nazev_en": "Test Region GCORG",
                "rada_id": "G",
                "definicni_bod": Point(15.0, 50.0, srid=4326),
                "hranice": MultiPolygon(Polygon(((15.0, 50.0), (15.1, 50.0), (15.1, 50.1), (15.0, 50.0))), srid=4326),
            },
        )
        okres, _ = RuianOkres.objects.get_or_create(
            kod=9996,
            defaults={
                "nazev": "Testovací okres GCORG",
                "nazev_en": "Test District GCORG",
                "spz": "TG",
                "kraj": kraj,
                "definicni_bod": Point(15.0, 50.0, srid=4326),
                "hranice": MultiPolygon(Polygon(((15.0, 50.0), (15.1, 50.0), (15.1, 50.1), (15.0, 50.0))), srid=4326),
            },
        )
        katastr, _ = RuianKatastr.objects.get_or_create(
            kod=999996,
            defaults={
                "nazev": "Testovací katastr GCORG",
                "okres": okres,
                "definicni_bod": Point(15.0, 50.0, srid=4326),
                "hranice": MultiPolygon(Polygon(((15.0, 50.0), (15.1, 50.0), (15.1, 50.1), (15.0, 50.0))), srid=4326),
            },
        )

        heslare_typ_projektu, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_PROJEKT_TYP, defaults={"nazev": "typ_projektu"}
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

        with patch("projekt.signals.projekt_post_save", lambda **kw: None), patch(
            "xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None
        ):
            cls.projekt_with_org, _ = Projekt.objects.get_or_create(
                ident_cely="M-202400096A",
                defaults={
                    "organizace": cls.org_a,
                    "hlavni_katastr": katastr,
                    "typ_projektu": survey_typ_projektu,
                },
            )
            cls.projekt_without_org, _ = Projekt.objects.get_or_create(
                ident_cely="M-202400096B",
                defaults={
                    "organizace": None,
                    "hlavni_katastr": katastr,
                    "typ_projektu": survey_typ_projektu,
                },
            )

    def _make_nalez(self, ident_cely, projekt, predano_organizace=None):
        """Vytvoří instanci ``SamostatnyNalez`` bez uložení do DB."""
        nalez = SamostatnyNalez()
        nalez.projekt_id = projekt.pk
        nalez.predano_organizace_id = predano_organizace.pk if predano_organizace else None
        return nalez

    def test_projekt_without_organizace_returns_empty_tuple(self):
        """``get_create_org`` vrátí prázdnou n-tici, pokud projekt nemá organizaci."""
        nalez = self._make_nalez("GCORG-001", self.projekt_without_org)

        result = nalez.get_create_org()

        self.assertEqual(result, ())

    def test_projekt_with_organizace_and_no_predano_returns_single_org(self):
        """``get_create_org`` vrátí n-tici s jednou organizací projektu, pokud není nastavena ``predano_organizace``."""
        nalez = self._make_nalez("GCORG-002", self.projekt_with_org)

        result = nalez.get_create_org()

        self.assertEqual(result, (self.org_a,))

    def test_same_predano_organizace_as_projekt_returns_single_org(self):
        """``get_create_org`` nevrátí duplikát, pokud ``predano_organizace`` je shodná s organizací projektu."""
        nalez = self._make_nalez("GCORG-003", self.projekt_with_org, predano_organizace=self.org_a)

        result = nalez.get_create_org()

        self.assertEqual(result, (self.org_a,))

    def test_different_predano_organizace_returns_both_orgs(self):
        """``get_create_org`` vrátí obě organizace, pokud ``predano_organizace`` se liší od organizace projektu."""
        nalez = self._make_nalez("GCORG-004", self.projekt_with_org, predano_organizace=self.org_b)

        result = nalez.get_create_org()

        self.assertEqual(result, (self.org_a, self.org_b))
