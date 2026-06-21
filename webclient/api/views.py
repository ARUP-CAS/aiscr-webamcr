import base64
import datetime
import hashlib
import io
import ipaddress
import json
import logging
import re
import socket
import threading
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from enum import Enum

import django.utils.timezone
from api.models import ApiRequestLog
from core.constants import (
    AKTUALIZACE_SN,
    API_REQUEST_LOG_STATUS_FAILURE,
    API_REQUEST_LOG_STATUS_PROCESSING,
    API_REQUEST_LOG_STATUS_SUCCESS,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_EVIDENCNI_CISLO_PATCH,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_FOTOGRAFIE_UPLOAD,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_XML_IMPORT,
    ARCHIVACE_SN,
    MAX_PAS_API_FOTOGRAFIE_FILE_SIZE_BYTES,
    ODESLANI_SN,
    POTVRZENI_SN,
    ROLE_BADATEL_ID,
    SN_ARCHIVOVANY,
    SN_ODESLANY,
    SN_POTVRZENY,
    SN_ZAPSANY,
    ZAPSANI_SN,
)
from core.coordTransform import transform_geom_to_sjtsk, transform_geom_to_wgs84
from core.decorators import odstavka_in_progress
from core.ident_cely import get_sn_ident
from core.models import AntivirusCheckResult, Permissions, Soubor, check_permissions
from core.repository_connector import (
    FedoraError,
    FedoraRepositoryConnector,
    FedoraTransaction,
    FedoraTransactionStatus,
)
from core.setting_models import CustomAdminSettings
from core.utils import get_cadastre_from_point
from core.views import get_finds_soubor_name
from django.conf import settings
from django.contrib.gis.geos import GEOSException, GEOSGeometry
from django.contrib.gis.geos import Point as GEOSPoint
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.forms.renderers import BaseRenderer
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from heslar.hesla import (
    HESLAR_NALEZOVE_OKOLNOSTI,
    HESLAR_OBDOBI,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_SPECIFIKACE,
    HESLAR_PRISTUPNOST,
)
from heslar.hesla_dynamicka import TYP_PROJEKTU_PRUZKUM_ID
from heslar.models import Heslar, RuianKatastr
from historie.models import Historie
from lxml import etree
from pas.models import SamostatnyNalez
from pid.exceptions import DoiWriteError
from projekt.models import Projekt
from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.throttling import BaseThrottle
from rest_framework.views import APIView
from uzivatel.models import ROLE_ARCHEOLOG_ID, Organizace, Osoba
from uzivatel.views import TokenAuthenticationBearer
from xml_generator.generator import AMCR_NAMESPACE_URL, AMCR_XSD_URL

logger = logging.getLogger(__name__)

_CACHE_KEY_ACCESS_RULES = "pas_api_access_rules"
_CACHE_KEY_RATE_LIMITS = "pas_api_rate_limits"
_CACHE_KEY_ACCESS_MODE = "pas_api_access_mode"
_CACHE_KEY_TRUSTED_PROXIES = "pas_api_trusted_proxies"
_DEFAULT_CACHE_TTL = 3600  # výchozí hodnota TTL v sekundách; konfigurovatelná přes CustomAdminSettings (cache_ttl)

_RECORD_LOCK_PREFIX = "pas_api_record_lock_"
_RECORD_LOCK_DEFAULT_TTL = (
    300  # výchozí hodnota v sekundách; konfigurovatelná přes CustomAdminSettings (record_lock_ttl)
)
_RECORD_LOCK_DEFAULT_RETRY_DELAY = 0.5  # sekund — výchozí čekací interval; konfigurovatelný přes record_lock_params
_RECORD_LOCK_DEFAULT_MAX_RETRIES = 10  # výchozí maximální počet pokusů; konfigurovatelný přes record_lock_params
_CACHE_KEY_RECORD_LOCK_PARAMS = "pas_api_record_lock_params"
_CACHE_KEY_ALLOWED_SCHEMA_VERSIONS = "pas_api_allowed_schema_versions"
_NOT_CONFIGURED = "__pas_api_not_configured__"  # sentinel: nastavení neexistuje (odliší se od None = cache miss)
_CACHE_KEY_CACHE_TTL = "pas_api_cache_ttl"
_CACHE_KEY_RECORD_LOCK_TTL = "pas_api_record_lock_ttl"
_CACHE_KEY_SCHEMA_FETCH_TIMEOUT = "pas_api_schema_fetch_timeout"
_CACHE_KEY_SCHEMA_CACHE_TTL = "pas_api_schema_cache_ttl"
_CACHE_KEY_MIN_REQUEST_INTERVALS = "pas_api_min_request_intervals"

_PAS_API_GROUP = "pas_api"
_ACCESS_RULES_ID = "access_rules"
_RATE_LIMITS_ID = "rate_limits"
_ACCESS_MODE_ID = "access_mode"
# codeql[py/clear-text-logging-sensitive-data]
_TRUSTED_PROXIES_ID = "trusted_proxies"
_RECORD_LOCK_PARAMS_ID = "record_lock_params"
_ALLOWED_SCHEMA_VERSIONS_ID = "allowed_schema_versions"
_CACHE_TTL_ID = "cache_ttl"
_RECORD_LOCK_TTL_ID = "record_lock_ttl"
_SCHEMA_FETCH_TIMEOUT_ID = "schema_fetch_timeout"
_SCHEMA_CACHE_TTL_ID = "schema_cache_ttl"
_MIN_REQUEST_INTERVALS_ID = "min_request_intervals"
_AMCR_SCHEMA_LOCK = threading.Lock()
_AMCR_SCHEMA_DEFAULT_FETCH_TIMEOUT = (
    10  # výchozí hodnota v sekundách; konfigurovatelná přes CustomAdminSettings (schema_fetch_timeout)
)
_AMCR_SCHEMA_DEFAULT_CACHE_TTL = (
    3600  # výchozí hodnota v sekundách; konfigurovatelná přes CustomAdminSettings (schema_cache_ttl)
)
_ALLOWED_XML_XSD_URLS = frozenset(
    (
        "http://www.w3.org/2001/xml.xsd",
        "https://www.w3.org/2001/xml.xsd",
        "http://www.w3.org/2001/03/xml.xsd",
        "https://www.w3.org/2001/03/xml.xsd",
    )
)
_ALLOWED_SCHEMA_URL_PATTERNS = (
    re.compile(r"^https?://www\.w3\.org/2001/XMLSchema-instance(?:[?#].*)?$"),
    re.compile(r"^https?://www\.w3\.org/2001/(?:03/)?xml\.xsd(?:[?#].*)?$"),
    re.compile(r"^https://api\.aiscr\.cz/schema/amcr/\d+\.\d+/.*$"),
    re.compile(r"^http://www\.opengis\.net/gml/.*$"),
)


_XSD_BYTES_CACHE: dict[str, bytes] = {}
_XSD_BYTES_CACHE_LOCK = threading.Lock()


def _xsd_redis_key(url: str) -> str:
    """
    Sestaví klíč pro Redis cache pro XSD schéma na zadané URL.

    Pro URL AMČR schématu (obsahující ``/schema/amcr/<verze>/``) je klíč ve tvaru
    ``xsd_schema:amcr:<verze>:<url>``, jinak ``xsd_schema:<url>``.

    :param url: URL XSD souboru.

    :return: Řetězec klíče pro Redis cache.
    """
    m = re.search(r"/schema/amcr/(\d+\.\d+)/", url)
    if m:
        return f"xsd_schema:amcr:{m.group(1)}:{url}"
    return f"xsd_schema:{url}"


def _fetch_xsd_bytes(url: str) -> bytes:
    """
    Načte bajty XSD schématu ze zadaného URL.

    Pořadí vyhledávání: in-process slovník → Redis → síť. Výsledek se uloží
    do obou úložišť, takže každá URL je v rámci procesu načtena nejvýše jednou.

    :param url: URL XSD souboru ke stažení.

    :return: Bajty XSD schématu.

    :raises urllib.error.URLError: Pokud se nepodaří navázat spojení s URL.
    :raises TimeoutError: Pokud vyprší časový limit požadavku.
    :raises ValueError: Pokud server vrátí prázdné tělo odpovědi.
    """
    if url in _XSD_BYTES_CACHE:
        return _XSD_BYTES_CACHE[url]
    with _XSD_BYTES_CACHE_LOCK:
        if url in _XSD_BYTES_CACHE:
            return _XSD_BYTES_CACHE[url]
        cache_key = _xsd_redis_key(url)
        cached = cache.get(cache_key)
        if cached is not None:
            _XSD_BYTES_CACHE[url] = cached
            return cached
        response = urllib.request.urlopen(url, timeout=PasApiPermissionMixin.get_schema_fetch_timeout())  # noqa: S310
        with response:
            content = response.read()
        if not content:
            logger.warning("api.views._fetch_xsd_bytes.empty_response", extra={"url": url})
            raise ValueError(f"api.views._fetch_xsd_bytes.empty_response: {url}")
        cache.set(cache_key, content, timeout=PasApiPermissionMixin.get_schema_cache_ttl())
        _XSD_BYTES_CACHE[url] = content
        return content


def _is_valid_ip_rule_value(value: str) -> bool:
    """
    Ověří, zda je hodnota IP pravidla syntakticky platná adresa, CIDR prefix nebo IP rozsah.

    Podporuje IPv4 i IPv6 ve všech třech formátech:
    - jednotlivá adresa (``"192.0.2.1"``, ``"2001:db8::1"``)
    - CIDR prefix (``"192.0.2.0/24"``, ``"2001:db8::/32"``)
    - explicitní rozsah (``"192.168.1.1-192.168.1.5"``; pouze IPv4)

    :param value: Řetězec z pole ``value`` v pravidle ``access_rules`` nebo ``rate_limits``.

    :return: ``True`` pokud je hodnota syntakticky validní.
    """
    value = value.strip()
    if "/" in value:
        try:
            ipaddress.ip_network(value, strict=False)
            return True
        except ValueError:
            return False
    if "-" in value:
        parts = value.split("-", 1)
        try:
            start = ipaddress.ip_address(parts[0].strip())
            end = ipaddress.ip_address(parts[1].strip())
            return start.version == end.version
        except ValueError:
            return False
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


TYPE_IP_BLACKLIST = "ip_blacklist"
TYPE_IP_WHITELIST = "ip_whitelist"
TYPE_USER_BLACKLIST = "user_blacklist"
TYPE_USER_WHITELIST = "user_whitelist"
_ACCESS_RULE_TYPES = {
    TYPE_IP_BLACKLIST,
    TYPE_IP_WHITELIST,
    TYPE_USER_BLACKLIST,
    TYPE_USER_WHITELIST,
}
SCOPE_USER = "user"
SCOPE_IP = "ip"
SCOPE_RECORD = "record"
ACCESS_MODE_OPEN = "open"
ACCESS_MODE_WHITELIST_ONLY = "whitelist_only"
ACCESS_MODE_CLOSED = "closed"
_ACCESS_MODES = {ACCESS_MODE_OPEN, ACCESS_MODE_WHITELIST_ONLY, ACCESS_MODE_CLOSED}
_PAS_API_ITEM_IDS = {
    _ACCESS_RULES_ID,
    _RATE_LIMITS_ID,
    _ACCESS_MODE_ID,
    _TRUSTED_PROXIES_ID,
    _RECORD_LOCK_PARAMS_ID,
    _ALLOWED_SCHEMA_VERSIONS_ID,
    _CACHE_TTL_ID,
    _RECORD_LOCK_TTL_ID,
    _SCHEMA_FETCH_TIMEOUT_ID,
    _SCHEMA_CACHE_TTL_ID,
    _MIN_REQUEST_INTERVALS_ID,
}

# codeql[py/clear-text-logging-sensitive-data]
_DEFAULT_TRUSTED_PROXIES = []


class PasApiPermissionMixin:
    """Sdílené helpery pro permission a throttle logiku PAS XML API."""

    _trusted_proxy_resolve_lock: threading.Lock = threading.Lock()
    _trusted_proxy_resolve_cache: dict[str, tuple[list, float]] = {}
    _trusted_proxy_resolve_ttl: int = 30  # sekund

    @staticmethod
    def _resolve_trusted_networks(entries: list[str]) -> list:
        """
        Přeloží seznam IP adres, CIDR rozsahů nebo DNS názvů na seznam ``ipaddress.IPv4Network`` objektů.

        Výsledky jsou uloženy v cache po dobu ``_trusted_proxy_resolve_ttl`` sekund. Pro Docker service
        jméno (např. ``"proxy"``) se IP adresa zjišťuje přes DNS pomocí ``socket.getaddrinfo``.

        :param entries: Seznam CIDR řetězců, IP adres nebo DNS názvů.

        :return: Seznam ``ipaddress.IPv4Network`` (nebo ``IPv6Network``) objektů.
        """
        cache_key = ",".join(sorted(entries))
        now = time.time()
        with PasApiPermissionMixin._trusted_proxy_resolve_lock:
            cached = PasApiPermissionMixin._trusted_proxy_resolve_cache.get(cache_key)
            if cached and now - cached[1] < PasApiPermissionMixin._trusted_proxy_resolve_ttl:
                return cached[0]

        networks = []
        for entry in entries:
            try:
                networks.append(ipaddress.ip_network(entry, strict=False))
                continue
            except ValueError:
                pass
            try:
                infos = socket.getaddrinfo(entry, None, proto=socket.IPPROTO_TCP)
                for info in infos:
                    addr = info[4][0]
                    networks.append(ipaddress.ip_network(addr, strict=False))
            except OSError:
                logger.warning("api.views.PasApiPermissionMixin._resolve_trusted_networks.dns_failed")

        with PasApiPermissionMixin._trusted_proxy_resolve_lock:
            PasApiPermissionMixin._trusted_proxy_resolve_cache[cache_key] = (networks, time.time())
        return networks

    @staticmethod
    def load_json_setting(item_id: str, raise_validation_error: bool = True):
        """
        Načte JSON hodnotu z ``CustomAdminSettings`` pro skupinu ``pas_api``.

        Nastavení se konfiguruje v Django administraci přes model ``CustomAdminSettings``
        (skupina ``pas_api``). Každý záznam musí mít pole ``value`` obsahující platný JSON.

        Podporované záznamy:

        ``access_rules`` (``item_id="access_rules"``)
            Seznam pravidel přístupu. Každé pravidlo je objekt s klíči:

            - ``rule_type`` *(povinný)* — typ pravidla; povolené hodnoty:
              ``"ip_blacklist"``, ``"ip_whitelist"``, ``"user_blacklist"``, ``"user_whitelist"``
            - ``value`` *(povinný)* — IP adresa, IP rozsah (např. ``"192.168.1.1-192.168.1.5"``),
              CIDR rozsah (např. ``"192.168.1.0/24"``) nebo uživatelské jméno podle ``rule_type``
            - ``active`` *(volitelný, výchozí ``true``)* — ``false`` pravidlo dočasně deaktivuje

            Příklad::

                [
                  {"rule_type": "ip_blacklist", "value": "1.2.3.4"},
                  {"rule_type": "ip_whitelist", "value": "10.0.0.0/8"},
                  {"rule_type": "user_blacklist", "value": "jan.novak", "active": false}
                ]

        ``rate_limits`` (``item_id="rate_limits"``)
            Seznam limitů počtu požadavků. Každý limit je objekt s klíči:

            - ``scope`` *(povinný)* — rozsah pravidla; povolené hodnoty: ``"user"``, ``"ip"``
            - ``value`` *(povinný)* — uživatelské jméno nebo IP adresa, IP rozsah,
              CIDR rozsah
            - ``rate`` *(povinný)* — limit ve formátu ``"počet/jednotka"``;
              jednotky: ``ms`` (milisekunda), ``s`` (sekunda), ``m`` (minuta),
              ``h`` (hodina), ``d`` (den);
              např. ``"5/ms"``, ``"10/m"``, ``"100/h"``, ``"1000/d"``
            - ``active`` *(volitelný, výchozí ``true``)* — ``false`` limit dočasně deaktivuje

            Příklad::

                [
                  {"scope": "user", "value": "jan.novak", "rate": "10/m"},
                  {"scope": "ip", "value": "203.0.113.0/24", "rate": "50/h"}
                ]

        ``access_mode`` (``item_id="access_mode"``)
            Režim globální dostupnosti API. Podporované hodnoty:

            - ``"open"`` — API je otevřené; whitelist pravidla se neaplikují
            - ``"whitelist_only"`` — API je dostupné pouze přes whitelist pravidla
            - ``"closed"`` — API je úplně uzavřené

            Příklad::

                "whitelist_only"

        ``trusted_proxies`` (``item_id="trusted_proxies"``)
            Seznam důvěryhodných proxy serverů stojících před aplikací.
            Každá položka je CIDR řetězec, IP adresa nebo DNS název (např. Docker service jméno).
            Používá se pro správné určení IP adresy klienta z hlavičky ``X-Forwarded-For``.
            Pokud nastavení chybí, použije se výchozí prázdný seznam ``[]``.

            Příklad::

                ["10.0.1.0/24", "proxy"]

        ``record_lock_params`` (``item_id="record_lock_params"``)
            Parametry Redis zámku záznamu. Objekt s klíči:

            - ``retry_delay`` *(volitelný, výchozí ``0.5``)* — čekací interval v sekundách
              mezi pokusy o získání zámku; musí být kladné číslo (``float``)
            - ``max_retries`` *(volitelný, výchozí ``10``)* — maximální počet pokusů;
              musí být kladné celé číslo (``int``)

            Pokud nastavení chybí, použijí se výchozí hodnoty.

            Příklad::

                {"retry_delay": 1.0, "max_retries": 5}

        ``cache_ttl`` (``item_id="cache_ttl"``)
            TTL (v sekundách) pro ukládání ostatních nastavení PAS API do cache.
            Musí být kladné celé číslo. Výchozí hodnota je ``3600``.

            Příklad::

                60

        ``record_lock_ttl`` (``item_id="record_lock_ttl"``)
            TTL (v sekundách) pro Redis zámek záznamu. Musí být kladné celé číslo.
            Výchozí hodnota je ``300`` (5 minut).

            Příklad::

                600

        ``schema_fetch_timeout`` (``item_id="schema_fetch_timeout"``)
            Časový limit (v sekundách) pro stahování XSD schémat ze sítě.
            Musí být kladné celé číslo. Výchozí hodnota je ``10``.

            Příklad::

                30

        ``schema_cache_ttl`` (``item_id="schema_cache_ttl"``)
            TTL (v sekundách) pro Redis cache XSD schémat. Musí být kladné celé číslo.
            Výchozí hodnota je ``3600`` (60 minut).

            Příklad::

                7200

        ``min_request_intervals`` (``item_id="min_request_intervals"``)
            Minimální interval mezi po sobě jdoucími požadavky pro globální throttling.
            Objekt s volitelnými klíči:

            - ``user_ms`` *(volitelný, výchozí ``0``)* — minimální interval v milisekundách
              pro téhož uživatele; hodnota ``0`` limit deaktivuje
            - ``ip_ms`` *(volitelný, výchozí ``0``)* — minimální interval v milisekundách
              pro tutéž IP adresu; hodnota ``0`` limit deaktivuje

            Pokud nastavení chybí, jsou oba limity deaktivovány (hodnota ``0``).

            Příklad::

                {"user_ms": 500, "ip_ms": 200}

        Změny v administraci se projeví do hodnoty ``cache_ttl`` (výchozí ``3600`` sekund); změny provedené přes Django admin se projeví okamžitě díky invalidaci cache signálem ``post_save``.

        :param item_id: Identifikátor záznamu — ``"access_rules"``, ``"rate_limits"``, ``"access_mode"``,
            ``"trusted_proxies"``, ``"record_lock_params"``, ``"cache_ttl"``, ``"record_lock_ttl"``,
            ``"schema_fetch_timeout"``, ``"schema_cache_ttl"`` nebo ``"min_request_intervals"``.

        :param raise_validation_error: Pokud je ``True`` (výchozí), nevalidní JSON vyhodí ``ValidationError``.

        :return: Naparsovaná JSON hodnota nebo ``[]`` při chybě či absenci záznamu.
        """
        try:
            obj = CustomAdminSettings.objects.get(item_group=_PAS_API_GROUP, item_id=item_id)
            return json.loads(obj.value)
        except CustomAdminSettings.DoesNotExist:
            return []
        except (json.JSONDecodeError, TypeError):
            logger.warning("api.views._load_json_setting.invalid_json")
            if raise_validation_error:
                # item_id in the validation message is likewise intentional:
                # it identifies which PAS admin setting is malformed and helps
                # troubleshooting or incident-response review. It is not
                # sensitive data.
                # codeql[py/error-message-exposure]
                raise ValidationError(
                    {
                        "value": _("api.views.PasApiPermissionMixin.load_json_setting.invalid_json").format(
                            item_id=item_id
                        )
                    }
                )
            return []

    @classmethod
    def get_access_rules(cls) -> list[dict]:
        """
        Vrátí přístupová pravidla API z cache nebo ``CustomAdminSettings``.

        Každé pravidlo je slovník s klíči ``rule_type``, ``value`` a volitelně ``active`` (výchozí ``True``).

        :raises ValidationError: Pokud nastavení nemá očekávanou strukturu nebo obsahuje nevalidní pravidlo.
        :return: Seznam aktivních pravidel.
        """
        rules = cache.get(_CACHE_KEY_ACCESS_RULES)
        if rules is None:
            raw_rules = cls.load_json_setting(_ACCESS_RULES_ID)
            cls.validate_access_rules(raw_rules)
            rules = [r for r in raw_rules if r.get("active", True)]
            cache.set(_CACHE_KEY_ACCESS_RULES, rules, cls.get_cache_ttl())
        return rules

    @staticmethod
    def validate_access_rules(raw_rules) -> bool:
        """
        Ověří strukturu a obsah nastavení ``access_rules``.

        :param raw_rules: Naparsovaná JSON hodnota nastavení ``access_rules``.

        :raises ValidationError: Pokud struktura nebo obsah pravidel neodpovídá očekávání.
        :return: ``True`` pokud je nastavení validní.
        """
        if not isinstance(raw_rules, list):
            raise ValidationError({"value": _("api.views.PasApiPermissionMixin.validate_access_rules.not_a_list")})

        for index, rule in enumerate(raw_rules):
            if not isinstance(rule, dict):
                raise ValidationError(
                    {
                        "value": _("api.views.PasApiPermissionMixin.validate_access_rules.item_not_a_dict").format(
                            index=index
                        )
                    }
                )
            if "rule_type" not in rule or "value" not in rule:
                raise ValidationError(
                    {
                        "value": _(
                            "api.views.PasApiPermissionMixin.validate_access_rules.missing_required_keys"
                        ).format(index=index)
                    }
                )
            if rule.get("active") is not None and not isinstance(rule.get("active"), bool):
                raise ValidationError(
                    {
                        "value": _("api.views.PasApiPermissionMixin.validate_access_rules.invalid_active").format(
                            index=index
                        )
                    }
                )
            if rule["rule_type"] not in _ACCESS_RULE_TYPES:
                raise ValidationError(
                    {
                        "value": _(
                            "api.views.PasApiPermissionMixin.validate_access_rules.unsupported_rule_type"
                        ).format(index=index, rule_type=rule["rule_type"])
                    }
                )
            if rule["rule_type"] in {TYPE_IP_BLACKLIST, TYPE_IP_WHITELIST}:
                if not isinstance(rule["value"], str) or not _is_valid_ip_rule_value(rule["value"]):
                    raise ValidationError(
                        {
                            "value": _("api.views.PasApiPermissionMixin.validate_access_rules.invalid_ip_value").format(
                                index=index, value=rule["value"]
                            )
                        }
                    )

        return True

    @classmethod
    def validate_custom_admin_setting(cls, instance: CustomAdminSettings) -> bool:
        """
        Ověří ``CustomAdminSettings`` záznam relevantní pro PAS API před uložením.

        Pokud jde o skupinu ``pas_api``, ověří platnost ``item_id`` a podle něj
        validuje JSON hodnotu příslušným validátorem. Podporovaná ``item_id``:
        ``"access_rules"``, ``"rate_limits"``, ``"access_mode"``, ``"trusted_proxies"``,
        ``"record_lock_params"``.

        :param instance: Ukládaný záznam ``CustomAdminSettings``.

        :raises ValidationError: Pokud ``item_id`` není podporováno nebo JSON/struktura hodnoty nejsou validní.
        :return: ``True`` pokud je záznam validní nebo se na něj validace nevztahuje.
        """
        if instance.item_group != _PAS_API_GROUP:
            return True
        if instance.item_id not in _PAS_API_ITEM_IDS:
            raise ValidationError(
                {
                    "item_id": _(
                        "api.views.PasApiPermissionMixin.validate_custom_admin_setting.invalid_item_id"
                    ).format(item_group=instance.item_group, item_id=instance.item_id)
                }
            )
        try:
            raw_value = json.loads(instance.value)
        except (json.JSONDecodeError, TypeError):
            raise ValidationError(
                {
                    "value": _("api.views.PasApiPermissionMixin.validate_custom_admin_setting.invalid_json").format(
                        item_id=instance.item_id
                    )
                }
            )

        if instance.item_id == _ACCESS_RULES_ID:
            cls.validate_access_rules(raw_value)
        elif instance.item_id == _RATE_LIMITS_ID:
            cls.validate_rate_limits(raw_value)
        elif instance.item_id == _ACCESS_MODE_ID:
            cls.validate_access_mode(raw_value)
        elif instance.item_id == _TRUSTED_PROXIES_ID:
            cls.validate_trusted_proxies(raw_value)
        elif instance.item_id == _RECORD_LOCK_PARAMS_ID:
            cls.validate_record_lock_params(raw_value)
        elif instance.item_id == _ALLOWED_SCHEMA_VERSIONS_ID:
            cls.validate_allowed_schema_versions(raw_value)
        elif instance.item_id in {_CACHE_TTL_ID, _RECORD_LOCK_TTL_ID, _SCHEMA_FETCH_TIMEOUT_ID, _SCHEMA_CACHE_TTL_ID}:
            cls.validate_positive_int_setting(raw_value, instance.item_id)
        elif instance.item_id == _MIN_REQUEST_INTERVALS_ID:
            cls.validate_min_request_intervals(raw_value)
        return True

    @classmethod
    def get_rate_limits(cls) -> list[dict]:
        """
        Vrátí limity počtu požadavků z cache nebo ``CustomAdminSettings``.

        Každý limit je slovník s klíči ``scope``, ``rate`` a volitelně ``active`` (výchozí ``True``).
        Pro scope ``user`` a ``ip`` je navíc povinný klíč ``value``.

        :raises ValidationError: Pokud nastavení nemá očekávanou strukturu nebo obsahuje nevalidní limit.
        :return: Seznam aktivních limitů.
        """
        limits = cache.get(_CACHE_KEY_RATE_LIMITS)
        if limits is None:
            raw_limits = cls.load_json_setting(_RATE_LIMITS_ID)
            cls.validate_rate_limits(raw_limits)
            limits = [r for r in raw_limits if r.get("active", True)]
            cache.set(_CACHE_KEY_RATE_LIMITS, limits, cls.get_cache_ttl())
        return limits

    @staticmethod
    def validate_rate_limits(raw_limits) -> bool:
        """
        Ověří strukturu a obsah nastavení ``rate_limits``.

        :param raw_limits: Naparsovaná JSON hodnota nastavení ``rate_limits``.

        :raises ValidationError: Pokud struktura nebo obsah limitů neodpovídá očekávání.
        :return: ``True`` pokud je nastavení validní.
        """
        if not isinstance(raw_limits, list):
            raise ValidationError({"value": _("api.views.PasApiPermissionMixin.validate_rate_limits.not_a_list")})

        for index, limit in enumerate(raw_limits):
            if not isinstance(limit, dict):
                raise ValidationError(
                    {
                        "value": _("api.views.PasApiPermissionMixin.validate_rate_limits.item_not_a_dict").format(
                            index=index
                        )
                    }
                )
            if "scope" not in limit or "rate" not in limit:
                raise ValidationError(
                    {
                        "value": _("api.views.PasApiPermissionMixin.validate_rate_limits.missing_required_keys").format(
                            index=index
                        )
                    }
                )
            if limit.get("active") is not None and not isinstance(limit.get("active"), bool):
                raise ValidationError(
                    {
                        "value": _("api.views.PasApiPermissionMixin.validate_rate_limits.invalid_active").format(
                            index=index
                        )
                    }
                )
            if _parse_rate(limit["rate"]) is None:
                raise ValidationError(
                    {
                        "value": _("api.views.PasApiPermissionMixin.validate_rate_limits.invalid_rate").format(
                            index=index, rate=limit["rate"]
                        )
                    }
                )
            if limit["scope"] not in {SCOPE_USER, SCOPE_IP, SCOPE_RECORD}:
                raise ValidationError(
                    {
                        "value": _("api.views.PasApiPermissionMixin.validate_rate_limits.unsupported_scope").format(
                            index=index, scope=limit["scope"]
                        )
                    }
                )
            if limit["scope"] in {SCOPE_USER, SCOPE_IP} and "value" not in limit:
                raise ValidationError(
                    {
                        "value": _("api.views.PasApiPermissionMixin.validate_rate_limits.missing_required_keys").format(
                            index=index
                        )
                    }
                )
            if limit["scope"] == SCOPE_RECORD and "value" in limit:
                raise ValidationError(
                    {
                        "value": _(
                            "api.views.PasApiPermissionMixin.validate_rate_limits.record_scope_unexpected_value"
                        ).format(index=index)
                    }
                )
            if limit["scope"] == SCOPE_IP:
                if not isinstance(limit["value"], str) or not _is_valid_ip_rule_value(limit["value"]):
                    raise ValidationError(
                        {
                            "value": _("api.views.PasApiPermissionMixin.validate_rate_limits.invalid_ip_value").format(
                                index=index, value=limit["value"]
                            )
                        }
                    )

        return True

    @classmethod
    def get_access_mode(cls) -> str:
        """
        Vrátí globální režim dostupnosti PAS XML API.

        Hodnota se načítá z ``CustomAdminSettings`` (``pas_api/access_mode``) a kešuje se.
        Neplatná nebo chybějící hodnota znamená výchozí režim ``open``.

        :raises ValidationError: Pokud nastavení neobsahuje podporovanou hodnotu.
        :return: Jeden z režimů ``open``, ``whitelist_only`` nebo ``closed``.
        """
        access_mode = cache.get(_CACHE_KEY_ACCESS_MODE)
        if access_mode is None:
            value = cls.load_json_setting(_ACCESS_MODE_ID)
            cls.validate_access_mode(value)
            access_mode = value if value not in (None, []) else ACCESS_MODE_OPEN
            cache.set(_CACHE_KEY_ACCESS_MODE, access_mode, cls.get_cache_ttl())
        return access_mode

    @staticmethod
    def validate_access_mode(value) -> bool:
        """
        Ověří hodnotu nastavení ``access_mode``.

        :param value: Naparsovaná JSON hodnota nastavení ``access_mode``.

        :raises ValidationError: Pokud hodnota není jedním z podporovaných režimů.
        :return: ``True`` pokud je hodnota validní.
        """
        if value in (None, []):
            return True
        if not isinstance(value, str) or value not in _ACCESS_MODES:
            raise ValidationError(
                {"value": _("api.views.PasApiPermissionMixin.validate_access_mode.invalid_value").format(value=value)}
            )
        return True

    @classmethod
    def get_trusted_proxies(cls) -> list[str]:
        """
        Vrátí seznam důvěryhodných proxy serverů z cache nebo ``CustomAdminSettings``.

        Pokud nastavení ``trusted_proxies`` neexistuje, vrátí výchozí hodnotu
        ``[]``.

        :raises ValidationError: Pokud nastavení má neplatnou strukturu.
        :return: Seznam řetězců — CIDR rozsahy, IP adresy nebo DNS názvy.
        """
        proxies = cache.get(_CACHE_KEY_TRUSTED_PROXIES)
        if proxies is None:
            raw = cls.load_json_setting(_TRUSTED_PROXIES_ID)
            if not raw:
                proxies = _DEFAULT_TRUSTED_PROXIES
            else:
                cls.validate_trusted_proxies(raw)
                proxies = raw
            cache.set(_CACHE_KEY_TRUSTED_PROXIES, proxies, cls.get_cache_ttl())
        return proxies

    @staticmethod
    def validate_trusted_proxies(raw_proxies) -> bool:
        """
        Ověří strukturu nastavení ``trusted_proxies``.

        Každá položka musí být neprázdný řetězec. Hodnoty CIDR rozsahů jsou ověřeny
        pomocí ``ipaddress.ip_network``; ostatní řetězce jsou považovány za DNS názvy
        a v administraci jsou přijaty bez DNS lookup (ten probíhá za běhu).

        :param raw_proxies: Naparsovaná JSON hodnota nastavení ``trusted_proxies``.

        :raises ValidationError: Pokud struktura nebo obsah neodpovídá očekávání.
        :return: ``True`` pokud je nastavení validní.
        """
        if not isinstance(raw_proxies, list):
            raise ValidationError({"value": _("api.views.PasApiPermissionMixin.validate_trusted_proxies.not_a_list")})
        for index, entry in enumerate(raw_proxies):
            if not isinstance(entry, str) or not entry.strip():
                raise ValidationError(
                    {
                        "value": _("api.views.PasApiPermissionMixin.validate_trusted_proxies.invalid_entry").format(
                            index=index
                        )
                    }
                )
            stripped = entry.strip()
            if "/" in stripped or re.match(r"^[\d:]", stripped):
                try:
                    ipaddress.ip_network(stripped, strict=False)
                except ValueError:
                    raise ValidationError(
                        {
                            "value": _("api.views.PasApiPermissionMixin.validate_trusted_proxies.invalid_cidr").format(
                                index=index, value=stripped
                            )
                        }
                    )
        return True

    @classmethod
    def get_record_lock_params(cls) -> tuple[float, int]:
        """
        Vrátí parametry Redis zámku záznamu z cache nebo ``CustomAdminSettings``.

        Pokud nastavení ``record_lock_params`` neexistuje, vrátí výchozí hodnoty
        ``(_RECORD_LOCK_DEFAULT_RETRY_DELAY, _RECORD_LOCK_DEFAULT_MAX_RETRIES)``.

        :raises ValidationError: Pokud nastavení má neplatnou strukturu.
        :return: Dvojice ``(retry_delay, max_retries)``.
        """
        params = cache.get(_CACHE_KEY_RECORD_LOCK_PARAMS)
        if params is None:
            raw = cls.load_json_setting(_RECORD_LOCK_PARAMS_ID)
            if not raw:
                params = (_RECORD_LOCK_DEFAULT_RETRY_DELAY, _RECORD_LOCK_DEFAULT_MAX_RETRIES)
            else:
                cls.validate_record_lock_params(raw)
                retry_delay = float(raw.get("retry_delay", _RECORD_LOCK_DEFAULT_RETRY_DELAY))
                max_retries = int(raw.get("max_retries", _RECORD_LOCK_DEFAULT_MAX_RETRIES))
                params = (retry_delay, max_retries)
            cache.set(_CACHE_KEY_RECORD_LOCK_PARAMS, params, cls.get_cache_ttl())
        return params

    @staticmethod
    def validate_record_lock_params(raw_params) -> bool:
        """
        Ověří strukturu a obsah nastavení ``record_lock_params``.

        Očekávaný formát je objekt s nepovinnými klíči ``retry_delay`` (kladné ``float``)
        a ``max_retries`` (kladné celé číslo ``int``).

        :param raw_params: Naparsovaná JSON hodnota nastavení ``record_lock_params``.

        :raises ValidationError: Pokud struktura nebo hodnoty neodpovídají očekávání.
        :return: ``True`` pokud je nastavení validní.
        """
        if not isinstance(raw_params, dict):
            raise ValidationError(
                {"value": _("api.views.PasApiPermissionMixin.validate_record_lock_params.not_a_dict")}
            )
        if "retry_delay" in raw_params:
            retry_delay = raw_params["retry_delay"]
            if not isinstance(retry_delay, (int, float)) or isinstance(retry_delay, bool) or retry_delay <= 0:
                raise ValidationError(
                    {"value": _("api.views.PasApiPermissionMixin.validate_record_lock_params.invalid_retry_delay")}
                )
        if "max_retries" in raw_params:
            max_retries = raw_params["max_retries"]
            if not isinstance(max_retries, int) or isinstance(max_retries, bool) or max_retries <= 0:
                raise ValidationError(
                    {"value": _("api.views.PasApiPermissionMixin.validate_record_lock_params.invalid_max_retries")}
                )
        return True

    @staticmethod
    def validate_allowed_schema_versions(raw_versions) -> bool:
        """
        Ověří strukturu a obsah nastavení ``allowed_schema_versions``.

        Očekávaný formát je neprázdný seznam čísel (``float`` nebo ``int``),
        například ``[2.2]`` nebo ``[2.2, 2.3]``. Záporné nebo nulové hodnoty nejsou povoleny.

        :param raw_versions: Naparsovaná JSON hodnota nastavení ``allowed_schema_versions``.

        :raises ValidationError: Pokud hodnota není neprázdný seznam kladných čísel.
        :return: ``True`` pokud je nastavení validní.
        """
        if not isinstance(raw_versions, list) or not raw_versions:
            raise ValidationError(
                {"value": _("api.views.PasApiPermissionMixin.validate_allowed_schema_versions.not_a_nonempty_list")}
            )
        for item in raw_versions:
            if isinstance(item, bool) or not isinstance(item, (int, float)) or item <= 0:
                raise ValidationError(
                    {"value": _("api.views.PasApiPermissionMixin.validate_allowed_schema_versions.invalid_version")}
                )
        return True

    @classmethod
    def get_allowed_schema_versions(cls) -> list[float] | None:
        """
        Vrátí seznam povolených verzí AMČR XSD schématu z cache nebo ``CustomAdminSettings``.

        Pokud nastavení ``allowed_schema_versions`` neexistuje, vrátí ``None`` (povoleny jsou
        všechny verze, které projdou ostatními kontrolami). Pokud nastavení existuje, vrátí
        seznam hodnot jako ``float``.

        :return: Seznam povolených verzí nebo ``None``, pokud nastavení není nakonfigurováno.
        """
        versions = cache.get(_CACHE_KEY_ALLOWED_SCHEMA_VERSIONS)
        if versions is None:
            raw = cls.load_json_setting(_ALLOWED_SCHEMA_VERSIONS_ID, raise_validation_error=False)
            if not raw:
                cache.set(_CACHE_KEY_ALLOWED_SCHEMA_VERSIONS, _NOT_CONFIGURED, cls.get_cache_ttl())
                return None
            cls.validate_allowed_schema_versions(raw)
            versions = [float(v) for v in raw]
            cache.set(_CACHE_KEY_ALLOWED_SCHEMA_VERSIONS, versions, cls.get_cache_ttl())
            return versions
        if versions == _NOT_CONFIGURED:
            return None
        return versions

    @staticmethod
    def validate_positive_int_setting(value, item_id: str) -> bool:
        """
        Ověří, že hodnota nastavení je kladné celé číslo.

        Používá se pro nastavení ``cache_ttl``, ``record_lock_ttl``, ``schema_fetch_timeout``
        a ``schema_cache_ttl``.

        :param value: Naparsovaná JSON hodnota nastavení.
        :param item_id: Identifikátor nastavení použitý v chybové zprávě.

        :raises ValidationError: Pokud hodnota není kladné celé číslo.
        :return: ``True`` pokud je hodnota validní.
        """
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValidationError(
                {
                    "value": _("api.views.PasApiPermissionMixin.validate_positive_int_setting.invalid_value").format(
                        item_id=item_id
                    )
                }
            )
        return True

    @staticmethod
    def validate_min_request_intervals(raw) -> bool:
        """
        Ověří strukturu a obsah nastavení ``min_request_intervals``.

        Očekávaný formát je objekt s nepovinnými klíči ``user_ms`` (nezáporné celé číslo)
        a ``ip_ms`` (nezáporné celé číslo). Hodnota ``0`` limit deaktivuje.

        :param raw: Naparsovaná JSON hodnota nastavení ``min_request_intervals``.

        :raises ValidationError: Pokud struktura nebo hodnoty neodpovídají očekávání.
        :return: ``True`` pokud je nastavení validní.
        """
        if not isinstance(raw, dict):
            raise ValidationError(
                {"value": _("api.views.PasApiPermissionMixin.validate_min_request_intervals.not_a_dict")}
            )
        for key in ("user_ms", "ip_ms"):
            if key in raw:
                val = raw[key]
                if not isinstance(val, int) or isinstance(val, bool) or val < 0:
                    raise ValidationError(
                        {
                            "value": _(
                                "api.views.PasApiPermissionMixin.validate_min_request_intervals.invalid_value"
                            ).format(key=key)
                        }
                    )
        return True

    @classmethod
    def get_cache_ttl(cls) -> int:
        """
        Vrátí TTL (v sekundách) pro ukládání nastavení PAS API do cache.

        Hodnota se načítá z ``CustomAdminSettings`` (``pas_api/cache_ttl``) a kešuje se
        po dobu výchozího TTL (``_DEFAULT_CACHE_TTL``). Pokud nastavení neexistuje, vrátí výchozí
        hodnotu ``_DEFAULT_CACHE_TTL`` (``3600`` sekund).

        :return: TTL v sekundách.
        """
        ttl = cache.get(_CACHE_KEY_CACHE_TTL)
        if ttl is None:
            raw = cls.load_json_setting(_CACHE_TTL_ID, raise_validation_error=False)
            if isinstance(raw, int) and not isinstance(raw, bool) and raw > 0:
                ttl = raw
            else:
                ttl = _DEFAULT_CACHE_TTL
            cache.set(_CACHE_KEY_CACHE_TTL, ttl, _DEFAULT_CACHE_TTL)
        return ttl

    @classmethod
    def get_record_lock_ttl(cls) -> int:
        """
        Vrátí TTL (v sekundách) pro Redis zámek záznamu.

        Hodnota se načítá z ``CustomAdminSettings`` (``pas_api/record_lock_ttl``) a kešuje se.
        Pokud nastavení neexistuje, vrátí výchozí hodnotu ``_RECORD_LOCK_DEFAULT_TTL`` (``300`` sekund).

        :return: TTL zámku záznamu v sekundách.
        """
        ttl = cache.get(_CACHE_KEY_RECORD_LOCK_TTL)
        if ttl is None:
            raw = cls.load_json_setting(_RECORD_LOCK_TTL_ID, raise_validation_error=False)
            if isinstance(raw, int) and not isinstance(raw, bool) and raw > 0:
                ttl = raw
            else:
                ttl = _RECORD_LOCK_DEFAULT_TTL
            cache.set(_CACHE_KEY_RECORD_LOCK_TTL, ttl, cls.get_cache_ttl())
        return ttl

    @classmethod
    def get_schema_fetch_timeout(cls) -> int:
        """
        Vrátí časový limit (v sekundách) pro stahování XSD schémat ze sítě.

        Hodnota se načítá z ``CustomAdminSettings`` (``pas_api/schema_fetch_timeout``) a kešuje se.
        Pokud nastavení neexistuje, vrátí výchozí hodnotu ``_AMCR_SCHEMA_DEFAULT_FETCH_TIMEOUT`` (``10`` sekund).

        :return: Časový limit v sekundách.
        """
        timeout = cache.get(_CACHE_KEY_SCHEMA_FETCH_TIMEOUT)
        if timeout is None:
            raw = cls.load_json_setting(_SCHEMA_FETCH_TIMEOUT_ID, raise_validation_error=False)
            if isinstance(raw, int) and not isinstance(raw, bool) and raw > 0:
                timeout = raw
            else:
                timeout = _AMCR_SCHEMA_DEFAULT_FETCH_TIMEOUT
            cache.set(_CACHE_KEY_SCHEMA_FETCH_TIMEOUT, timeout, cls.get_cache_ttl())
        return timeout

    @classmethod
    def get_schema_cache_ttl(cls) -> int:
        """
        Vrátí TTL (v sekundách) pro Redis cache XSD schémat.

        Hodnota se načítá z ``CustomAdminSettings`` (``pas_api/schema_cache_ttl``) a kešuje se.
        Pokud nastavení neexistuje, vrátí výchozí hodnotu ``_AMCR_SCHEMA_DEFAULT_CACHE_TTL`` (``3600`` sekund).

        :return: TTL cache schémat v sekundách.
        """
        ttl = cache.get(_CACHE_KEY_SCHEMA_CACHE_TTL)
        if ttl is None:
            raw = cls.load_json_setting(_SCHEMA_CACHE_TTL_ID, raise_validation_error=False)
            if isinstance(raw, int) and not isinstance(raw, bool) and raw > 0:
                ttl = raw
            else:
                ttl = _AMCR_SCHEMA_DEFAULT_CACHE_TTL
            cache.set(_CACHE_KEY_SCHEMA_CACHE_TTL, ttl, cls.get_cache_ttl())
        return ttl

    @classmethod
    def get_min_request_intervals(cls) -> tuple[int, int]:
        """
        Vrátí minimální intervaly (v ms) mezi požadavky pro throttling per-user a per-IP.

        Hodnota se načítá z ``CustomAdminSettings`` (``pas_api/min_request_intervals``) a kešuje se.
        Pokud nastavení neexistuje, vrátí ``(0, 0)`` (oba limity deaktivovány).

        :return: Dvojice ``(user_ms, ip_ms)``.
        """
        intervals = cache.get(_CACHE_KEY_MIN_REQUEST_INTERVALS)
        if intervals is None:
            raw = cls.load_json_setting(_MIN_REQUEST_INTERVALS_ID, raise_validation_error=False)
            if isinstance(raw, dict):
                user_ms = int(raw.get("user_ms", 0) or 0)
                ip_ms = int(raw.get("ip_ms", 0) or 0)
            else:
                user_ms = 0
                ip_ms = 0
            intervals = (user_ms, ip_ms)
            cache.set(_CACHE_KEY_MIN_REQUEST_INTERVALS, intervals, cls.get_cache_ttl())
        return intervals

    @classmethod
    def get_client_ip(cls, request) -> str:
        """
        Vrátí IP adresu klienta z požadavku.

        Prochází hlavičku ``X-Forwarded-For`` zprava doleva a přeskakuje IP adresy
        důvěryhodných proxy serverů (z nastavení ``pas_api/trusted_proxies``).
        První nedůvěryhodná IP adresa je vrácena jako adresa klienta.

        Pokud hlavička chybí nebo jsou všechny položky důvěryhodné, vrátí ``REMOTE_ADDR``.

        :param request: HTTP požadavek.

        :return: IP adresa klienta jako řetězec.
        """
        remote_addr = request.META.get("REMOTE_ADDR", "")
        # codeql[py/clear-text-logging-sensitive-data]
        trusted_entries = cls.get_trusted_proxies()
        trusted_networks = cls._resolve_trusted_networks(trusted_entries)

        def _is_trusted(ip_str: str) -> bool:
            try:
                addr = ipaddress.ip_address(ip_str.strip())
                return any(addr in net for net in trusted_networks)
            except ValueError:
                return False

        if not _is_trusted(remote_addr):
            return remote_addr

        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        chain = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]
        for ip in reversed(chain):
            if not _is_trusted(ip):
                return ip
        return remote_addr

    @staticmethod
    def get_user_identifier(user) -> str | None:
        """
        Vrátí identifikátor uživatele použitelný pro access-rules a rate-limity.

        Projekt používá vlastní model uživatele s ``USERNAME_FIELD = "email"``.
        Pro kompatibilitu helper preferuje ``email`` a fallbackuje na ``username``.

        :param user: Uživatel navázaný na požadavek.

        :return: Email, username nebo ``None`` pro neautentizovaného uživatele.
        """
        if not user or not getattr(user, "is_authenticated", False):
            return None
        return getattr(user, "email", None) or getattr(user, "username", None)

    @staticmethod
    def ip_matches(client_ip: str, pattern: str) -> bool:
        """
        Porovná IP adresu klienta s konkrétní adresou, IP rozsahem nebo CIDR rozsahem.

        :param client_ip: IP adresa klienta.
        :param pattern: IP adresa, IP rozsah (např. ``192.168.1.1-192.168.1.5``)
                        nebo CIDR rozsah (např. ``192.168.1.0/24"``).

        :return: ``True`` pokud adresa odpovídá vzoru.
        """
        try:
            client = ipaddress.ip_address(client_ip)
            if "-" in pattern and "/" not in pattern:
                start_str, end_str = [part.strip() for part in pattern.split("-", 1)]
                start = ipaddress.ip_address(start_str)
                end = ipaddress.ip_address(end_str)
                if client.version != start.version or client.version != end.version:
                    return False
                if start > end:
                    start, end = end, start
                return start <= client <= end
            if "/" in pattern:
                return client in ipaddress.ip_network(pattern, strict=False)
            return client == ipaddress.ip_address(pattern)
        except ValueError:
            return False


@receiver(post_save, sender=CustomAdminSettings)
@receiver(post_delete, sender=CustomAdminSettings)
def _invalidate_api_cache(sender, instance=None, **kwargs):
    """Vymaže cache pravidel API po změně záznamu ``CustomAdminSettings`` skupiny ``pas_api``."""
    if instance and instance.item_group == _PAS_API_GROUP:
        cache.delete(_CACHE_KEY_ACCESS_RULES)
        cache.delete(_CACHE_KEY_RATE_LIMITS)
        cache.delete(_CACHE_KEY_ACCESS_MODE)
        cache.delete(_CACHE_KEY_TRUSTED_PROXIES)
        cache.delete(_CACHE_KEY_RECORD_LOCK_PARAMS)
        cache.delete(_CACHE_KEY_ALLOWED_SCHEMA_VERSIONS)
        cache.delete(_CACHE_KEY_CACHE_TTL)
        cache.delete(_CACHE_KEY_RECORD_LOCK_TTL)
        cache.delete(_CACHE_KEY_SCHEMA_FETCH_TIMEOUT)
        cache.delete(_CACHE_KEY_SCHEMA_CACHE_TTL)
        cache.delete(_CACHE_KEY_MIN_REQUEST_INTERVALS)


class IpBlacklistPermission(PasApiPermissionMixin, BasePermission):
    """Zamítne přístup IP adresám uvedeným v blacklistu ``CustomAdminSettings`` (``pas_api/access_rules``)."""

    def has_permission(self, request, view=None) -> bool:
        """
        Ověří, zda IP adresa klienta není na blacklistu.

        :param request: HTTP požadavek.
        :param view: Pohled zpracovávající požadavek.

        :return: ``False`` pokud je IP na blacklistu, jinak ``True``.
        """
        client_ip = self.get_client_ip(request)
        rules = self.get_access_rules()
        for rule in rules:
            if rule["rule_type"] == TYPE_IP_BLACKLIST and self.ip_matches(client_ip, rule["value"]):
                # client_ip and the matched rule value are logged intentionally for
                # access-control troubleshooting and incident investigation. They
                # are operational context, not secrets.
                # codeql[py/clear-text-logging-sensitive-data]
                logger.warning(
                    "api.views.IpBlacklistPermission.denied",
                    extra={"ip": client_ip, "rule": rule["value"]},
                )
                return False
        return True


class IpWhitelistPermission(PasApiPermissionMixin, BasePermission):
    """
    Povolí přístup pouze IP adresám uvedeným ve whitelistu ``CustomAdminSettings`` (``pas_api/access_rules``).

    Pokud žádné aktivní whitelist pravidlo neexistuje, propustí všechny požadavky.
    """

    def has_permission(self, request, view=None) -> bool:
        """
        Ověří, zda IP adresa klienta je na whitelistu (pokud je whitelist definován).

        :param request: HTTP požadavek.
        :param view: Pohled zpracovávající požadavek.

        :return: ``True`` pokud whitelist není definován nebo IP na něm je, jinak ``False``.
        """
        if self.get_access_mode() != ACCESS_MODE_WHITELIST_ONLY:
            return True
        rules = self.get_access_rules()
        whitelist = [r for r in rules if r["rule_type"] == TYPE_IP_WHITELIST]
        if not whitelist:
            return True
        client_ip = self.get_client_ip(request)
        for rule in whitelist:
            if self.ip_matches(client_ip, rule["value"]):
                return True
        # client_ip is logged intentionally for whitelist-denial troubleshooting
        # and incident investigation. It is operational context, not a secret.
        # codeql[py/clear-text-logging-sensitive-data]
        logger.warning(
            "api.views.IpWhitelistPermission.denied",
            extra={"ip": client_ip},
        )
        return False


class UserBlacklistPermission(PasApiPermissionMixin, BasePermission):
    """Zamítne přístup uživatelům uvedeným v blacklistu ``CustomAdminSettings`` (``pas_api/access_rules``)."""

    def has_permission(self, request, view=None) -> bool:
        """
        Ověří, zda přihlášený uživatel není na blacklistu.

        :param request: HTTP požadavek.
        :param view: Pohled zpracovávající požadavek.

        :return: ``False`` pokud je uživatel na blacklistu, jinak ``True``.
        """
        if not request.user or not request.user.is_authenticated:
            return True
        user_identifier = self.get_user_identifier(request.user)
        rules = self.get_access_rules()
        for rule in rules:
            if rule["rule_type"] == TYPE_USER_BLACKLIST and rule["value"] == user_identifier:
                # user_identifier is logged intentionally for access-control
                # troubleshooting and incident investigation. It identifies the
                # denied account and is operational context, not a secret.
                # codeql[py/clear-text-logging-sensitive-data]
                logger.warning(
                    "api.views.UserBlacklistPermission.denied",
                    extra={"user": user_identifier},
                )
                return False
        return True


class UserWhitelistPermission(PasApiPermissionMixin, BasePermission):
    """
    Povolí přístup pouze uživatelům uvedeným ve whitelistu ``CustomAdminSettings`` (``pas_api/access_rules``).

    Pokud žádné aktivní whitelist pravidlo neexistuje, propustí všechny požadavky.
    """

    def has_permission(self, request, view=None) -> bool:
        """
        Ověří, zda přihlášený uživatel je na whitelistu (pokud je whitelist definován).

        :param request: HTTP požadavek.
        :param view: Pohled zpracovávající požadavek.

        :return: ``True`` pokud whitelist není definován nebo uživatel na něm je, jinak ``False``.
        """
        if self.get_access_mode() != ACCESS_MODE_WHITELIST_ONLY:
            return True
        rules = self.get_access_rules()
        whitelist = [r for r in rules if r["rule_type"] == TYPE_USER_WHITELIST]
        if not whitelist:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        user_identifier = self.get_user_identifier(request.user)
        for rule in whitelist:
            if rule["value"] == user_identifier:
                return True
        # user_identifier is logged intentionally for whitelist-denial
        # troubleshooting and incident investigation. It is operational
        # context, not a secret.
        # codeql[py/clear-text-logging-sensitive-data]
        logger.warning(
            "api.views.UserWhitelistPermission.denied",
            extra={"user": user_identifier},
        )
        return False


class ApiAccessModePermission(PasApiPermissionMixin, BasePermission):
    """Řídí globální dostupnost PAS XML API podle ``CustomAdminSettings`` (``pas_api/access_mode``)."""

    def has_permission(self, request, view=None) -> bool:
        """
        Ověří globální režim dostupnosti API.

        Režim ``open`` požadavek propustí. Režim ``closed`` vše zamítne.
        Režim ``whitelist_only`` vyžaduje alespoň jedno aktivní whitelist pravidlo.

        :param request: HTTP požadavek.
        :param view: Pohled zpracovávající požadavek.

        :return: ``True`` pokud režim přístup dovoluje, jinak ``False``.
        """
        access_mode = self.get_access_mode()
        if access_mode == ACCESS_MODE_OPEN:
            return True
        if access_mode == ACCESS_MODE_CLOSED:
            self.message = _("api.views.ApiAccessModePermission.closed")
            logger.warning("api.views.ApiAccessModePermission.closed")
            return False

        rules = self.get_access_rules()
        has_whitelist = any(rule["rule_type"] in {TYPE_IP_WHITELIST, TYPE_USER_WHITELIST} for rule in rules)
        if has_whitelist:
            return True

        self.message = _("api.views.ApiAccessModePermission.whitelist_only_without_rules")
        logger.warning("api.views.ApiAccessModePermission.whitelist_only_without_rules")
        return False


def _strip_namespace(tag: str) -> str:
    """
    Vrátí název XML tagu bez namespace prefixu.

    :param tag: XML tag včetně namespace (např. ``{http://example.com}element``).

    :return: Název tagu bez namespace (např. ``element``).
    """
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _parse_rate(rate: str) -> tuple[int, float] | None:
    """
    Naparsuje řetězec limitu ve formátu ``počet/jednotka`` na počet a délku okna v sekundách.

    Podporované jednotky: ``ms`` (milisekunda), ``s`` (sekunda), ``m`` (minuta),
    ``h`` (hodina), ``d`` (den). Pro jednotku ``ms`` je vrácené okno typu ``float``
    (0.001 s); pro ostatní jednotky je ``int``.

    :param rate: Řetězec ve formátu ``10/m``, ``100/h`` apod.

    :return: Dvojice ``(počet, okno_v_sekundách)`` nebo ``None`` při chybě parsování.
    """
    try:
        count_str, period = rate.split("/")
        count = int(count_str)
        periods = {"ms": 0.001, "s": 1, "m": 60, "h": 3600, "d": 86400}
        window = periods.get(period.strip().lower())
        if window is None:
            return None
        return count, window
    except (ValueError, AttributeError):
        return None


class ApiImportThrottle(PasApiPermissionMixin, BaseThrottle):
    """
    Throttle pro API import samostatného nálezu řízený záznamy ``CustomAdminSettings`` (``pas_api/rate_limits``).

    Pravidla jsou načítána z databáze (s cache) a vyhodnocují se nezávisle podle scope:
    ``user``, ``ip`` a ``record``. Požadavek je povolen pouze tehdy, pokud projde všemi
    relevantními limity pro dané volání.

    Scope ``record`` používá ``ident_cely`` z URL jako stabilní identifikátor konkrétního
    záznamu. To je záměrné: jeden limit se tak sdílí mezi různými endpointy a akcemi nad
    týmž ``SamostatnyNalez`` a nelze jej obejít střídáním například PATCH a upload endpointu.
    """

    def allow_request(self, request, view=None) -> bool:
        """
        Rozhodne, zda je požadavek povolen na základě nakonfigurovaných limitů.

        :param request: HTTP požadavek.
        :param view: Pohled zpracovávající požadavek.

        :return: ``True`` pokud nebyl překročen žádný relevantní limit, jinak ``False``.
        """
        limits = self.get_rate_limits()
        client_ip = self.get_client_ip(request)
        user_identifier = self.get_user_identifier(request.user)

        ident_cely = getattr(view, "kwargs", {}).get("ident_cely") if view is not None else None

        user_interval_ms, ip_interval_ms = self.get_min_request_intervals()
        if user_interval_ms > 0 and user_identifier:
            if not self._check_min_interval(
                f"min_interval_user_{user_identifier}", user_interval_ms, scope="user", identifier=user_identifier
            ):
                return False

        if ip_interval_ms > 0 and client_ip:
            if not self._check_min_interval(
                f"min_interval_ip_{client_ip}", ip_interval_ms, scope="ip", identifier=client_ip
            ):
                return False

        for limit in limits:
            if limit["scope"] == SCOPE_USER and limit["value"] == user_identifier:
                if not self._check_limit(f"throttle_user_{user_identifier}", limit["rate"], request):
                    return False
            if limit["scope"] == SCOPE_IP and self.ip_matches(client_ip, limit["value"]):
                if not self._check_limit(f"throttle_ip_{client_ip}", limit["rate"], request):
                    return False
            # Record-level throttle is intentionally keyed by ident_cely so the same
            # limit bucket is shared across different actions/endpoints for one record.
            if limit["scope"] == SCOPE_RECORD and ident_cely:
                if not self._check_limit(f"throttle_record_{ident_cely}", limit["rate"], request):
                    return False
        return True

    def _check_limit(self, cache_key: str, rate: str, request) -> bool:
        """
        Zkontroluje a aktualizuje počítadlo požadavků v cache pro daný klíč a rate.

        Implementace používá fixní časové okno s atomickými operacemi ``cache.add()``
        a ``cache.incr()``. Oproti původnímu ukládání seznamu timestampů tím odpadá
        read-modify-write race condition při souběžných požadavcích.

        :param cache_key: Klíč pro uložení počítadla v cache.
        :param rate: Řetězec limitu ve formátu ``počet/jednotka``.
        :param request: HTTP požadavek (použit pro logování).

        :return: ``True`` pokud limit nebyl překročen, jinak ``False``.
        """
        parsed = _parse_rate(rate)
        if parsed is None:
            # Fail closed: zaměstnaný nevalidním limitem nechceme propustit a tím
            # potenciálně otevřít neomezený přístup k API. Validní formát ``rate``
            # je vynucen v ``validate_rate_limits`` při ukládání; tady jde o pojistku
            # pro případ, že by data v cache/CustomAdminSettings byla poškozená.
            logger.error("api.views.ApiImportThrottle.invalid_rate", extra={"rate": rate})
            self.wait_seconds = None
            return False
        max_requests, window = parsed
        now = time.time()
        window_started_key = f"{cache_key}:window_started"

        if cache.add(cache_key, 1, timeout=window):
            cache.add(window_started_key, now, timeout=window)
            self.wait_seconds = None
            return True

        try:
            current_count = cache.incr(cache_key)
        except ValueError:
            # The counter expired between add() and incr(); restart the window.
            cache.set(cache_key, 1, timeout=window)
            cache.set(window_started_key, now, timeout=window)
            self.wait_seconds = None
            return True

        if current_count > max_requests:
            window_started = cache.get(window_started_key)
            if window_started is None:
                cache.add(window_started_key, now, timeout=window)
                window_started = now
            # Minimum kept above 0 so clients always get a non-zero Retry-After; for the
            # ``ms`` unit the floor is one window (e.g. 0.001 s) so we don't artificially
            # stretch a millisecond limit to a full second.
            self.wait_seconds = max(window - (now - float(window_started)), min(window, 0.001))
            logger.warning(
                "api.views.ApiImportThrottle.throttled",
                extra={"cache_key": cache_key, "rate": rate},
            )
            return False
        self.wait_seconds = None
        return True

    def _check_min_interval(self, cache_key: str, min_interval_ms: int, scope: str, identifier: str) -> bool:
        """
        Ověří, že od posledního požadavku ve stejném scope uplynula minimální doba.

        Limit je globální (aplikuje se na všechny uživatele resp. IP) a konfiguruje se
        přes ``CustomAdminSettings`` (``pas_api/min_request_intervals``). V Redis je uložena časová značka
        posledního povoleného požadavku. Pokud žádná hodnota není uložena (typicky první požadavek
        po startu nebo po vypršení TTL), je limit považován za splněný a aktuální čas se uloží.

        :param cache_key: Klíč v cache (Redis).
        :param min_interval_ms: Minimální interval mezi požadavky v milisekundách.
        :param scope: Logický rozsah limitu (``"user"`` nebo ``"ip"``) — použito v logu.
        :param identifier: Identifikátor (uživatel / IP) — použito v logu.

        :return: ``True`` pokud limit nebyl porušen (a nový časový bod byl uložen), jinak ``False``.
        """
        now = time.time()
        min_interval = min_interval_ms / 1000.0
        # Django cache (django-redis) drops keys when ``timeout`` is fractional ``< 1``;
        # ceil to an integer second TTL with a floor of 1 s so the entry survives the
        # sub-second comparison window (e.g. 500 ms).
        ttl_seconds = max(int(min_interval) + 1, 1)
        # Sub-second timestamp comparison: ``cache.add`` alone cannot enforce a 500 ms
        # window because the TTL must be an integer second. We therefore store the
        # timestamp of the last allowed request and compare against it on each call.
        last = cache.get(cache_key)
        if last is not None:
            elapsed = now - float(last)
            if elapsed < min_interval:
                self.wait_seconds = max(min_interval - elapsed, 0.001)
                logger.warning(
                    "api.views.ApiImportThrottle.min_interval_throttled",
                    extra={"scope": scope, "identifier": identifier, "wait": self.wait_seconds},
                )
                return False
        cache.set(cache_key, now, timeout=ttl_seconds)
        return True

    def wait(self):
        """
        Vrátí počet sekund do dalšího povoleného požadavku.

        :return: Počet sekund nebo ``None``.
        """
        return getattr(self, "wait_seconds", None)


class ImportErrorType(Enum):
    """Typ chyby při importu XML samostatného nálezu."""

    RECORD_DOES_NOT_EXIST = 1
    INVALID_DATA = 2
    PERMISSION_ERROR = 3


@dataclass(frozen=True)
class ImportValidationIssue:
    """Strukturovaná chyba vzniklá při importu XML samostatného nálezu."""

    line: int | None
    column: int | None
    message: str
    error_type: ImportErrorType

    def to_dict(self) -> dict:
        """
        Převede chybu na slovník pro API odpověď.

        :return: Slovníková reprezentace chyby.
        """
        data = asdict(self)
        data["error_type"] = self.error_type.value
        return data


class ImportValidationException(serializers.ValidationError):
    """Validační chyba importu nesoucí již vytvořené ``ImportValidationIssue`` instance."""

    def __init__(self, import_errors: ImportValidationIssue | list[ImportValidationIssue]):
        if isinstance(import_errors, ImportValidationIssue):
            import_errors = [import_errors]
        self.import_errors = list(import_errors)
        super().__init__([error.to_dict() for error in self.import_errors])

    @classmethod
    def from_serializer_errors(cls, errors, line: int | None, column: int | None = None):
        """
        Vytvoří výjimku importu z chyb serializeru.

        :param errors: Chyby vrácené serializerem.
        :param line: Řádek zdrojového XML elementu.
        :param column: Sloupec zdrojového XML elementu.

        :return: Výjimka s naplněnými ``ImportValidationIssue`` instancemi.
        """
        import_errors = []
        for field_name, field_errors in errors.items():
            if not isinstance(field_errors, (list, tuple)):
                field_errors = [field_errors]
            for field_error in field_errors:
                import_errors.append(
                    ImportValidationIssue(
                        line=line,
                        column=column,
                        message=f"{field_name}: {field_error}",
                        error_type=cls._serializer_error_to_error_type(field_name, field_error),
                    )
                )
        return cls(import_errors)

    @staticmethod
    def _serializer_error_to_error_type(field_name, field_error) -> ImportErrorType:
        """
        Určí typ importní chyby podle chyby serializeru.

        :param field_name: Název pole serializeru, na kterém chyba vznikla.
        :param field_error: Jedna chyba serializeru.

        :return: Typ importní chyby.
        """
        if getattr(field_error, "code", None) == "does_not_exist" and field_name in {"projekt", "nalezce"}:
            return ImportErrorType.RECORD_DOES_NOT_EXIST
        return ImportErrorType.INVALID_DATA


class SamostatnyNalezXmlImportSerializer(serializers.ModelSerializer):
    """Serializer pro import záznamu samostatného nálezu z XML; FK pole jsou identifikována přes ident_cely."""

    ident_cely = serializers.CharField(required=False, allow_null=True)
    projekt = serializers.SlugRelatedField(
        slug_field="ident_cely",
        queryset=Projekt.objects.filter(typ_projektu=TYP_PROJEKTU_PRUZKUM_ID),
    )
    katastr = serializers.SlugRelatedField(
        slug_field="kod",
        queryset=RuianKatastr.objects.all(),
        required=False,
        allow_null=True,
    )
    okolnosti = serializers.SlugRelatedField(
        slug_field="ident_cely",
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_NALEZOVE_OKOLNOSTI),
        required=False,
        allow_null=True,
    )
    pristupnost = serializers.SlugRelatedField(
        slug_field="ident_cely",
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST),
    )
    obdobi = serializers.SlugRelatedField(
        slug_field="ident_cely",
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_OBDOBI),
        required=False,
        allow_null=True,
    )
    druh_nalezu = serializers.SlugRelatedField(
        slug_field="ident_cely",
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PREDMET_DRUH),
        required=False,
        allow_null=True,
    )
    specifikace = serializers.SlugRelatedField(
        slug_field="ident_cely",
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PREDMET_SPECIFIKACE),
        required=False,
        allow_null=True,
    )
    nalezce = serializers.SlugRelatedField(
        slug_field="ident_cely",
        queryset=Osoba.objects.all(),
        required=False,
        allow_null=True,
    )
    predano_organizace = serializers.SlugRelatedField(
        slug_field="ident_cely",
        queryset=Organizace.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = SamostatnyNalez
        fields = [
            "ident_cely",
            "projekt",
            "katastr",
            "lokalizace",
            "hloubka",
            "okolnosti",
            "geom",
            "geom_sjtsk",
            "geom_system",
            "pristupnost",
            "obdobi",
            "presna_datace",
            "druh_nalezu",
            "specifikace",
            "poznamka",
            "nalezce",
            "datum_nalezu",
            "stav",
            "predano",
            "predano_organizace",
            "pocet",
            "igsn",
            "evidencni_cislo",
        ]


class PasApiBaseView(PasApiPermissionMixin, APIView):
    """Základní pohled sdílený všemi PAS API endpointy."""

    _record_lock_thread_lock: threading.Lock = threading.Lock()

    authentication_classes = [TokenAuthenticationBearer]
    permission_classes = [
        IsAuthenticated,
        IpBlacklistPermission,
        ApiAccessModePermission,
        IpWhitelistPermission,
        UserBlacklistPermission,
        UserWhitelistPermission,
    ]
    throttle_classes = [ApiImportThrottle]
    parser_classes = [MultiPartParser]

    def dispatch(self, request, *args, **kwargs):
        """
        Zpracuje globální režim ``closed`` ještě před DRF permission vrstvou.

        Tím je zajištěn návratový kód ``503 Service Unavailable`` bez zapojení
        permission mechaniky DRF, která by jinak vracela ``403``.

        :param request: Příchozí HTTP požadavek.
        :param args: Dodatečné poziční argumenty.
        :param kwargs: Dodatečné pojmenované argumenty.

        :return: HTTP odpověď view nebo okamžitá odpověď ``503`` při vypnutém API.
        """
        if self.get_access_mode() == ACCESS_MODE_CLOSED:
            logger.warning("api.views.PasApiBaseView.dispatch.closed")
            return JsonResponse(
                {"detail": _("api.views.ApiAccessModePermission.closed")},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _fail(log_entry: "ApiRequestLog", body: dict, http_status: int) -> Response:
        """
        Označí log záznam jako neúspěšný, vytvoří a vrátí chybovou odpověď.

        :param log_entry: Záznam logu API požadavku.
        :param body: Tělo odpovědi jako slovník.
        :param http_status: HTTP stavový kód odpovědi.

        :return: Chybová HTTP odpověď se zadaným tělem a stavovým kódem.
        """
        log_entry.status = API_REQUEST_LOG_STATUS_FAILURE
        log_entry.finished_at = django.utils.timezone.now()
        log_entry.errors = body
        log_entry.save(update_fields=["status", "finished_at", "errors"])
        return Response(body, status=http_status)

    @classmethod
    def _has_edit_permissions(cls, user, ident_cely) -> bool:
        """
        Ověří, zda má uživatel oprávnění editovat zadaný samostatný nález.

        :param user: Uživatel provádějící požadavek.
        :param ident_cely: Identifikátor záznamu samostatného nálezu.

        :return: Vrací ``True`` pokud má uživatel oprávnění ``pas_edit`` pro daný záznam.
        """
        if not check_permissions(Permissions.actionChoices.pas_edit, user, ident_cely):
            return False
        return True

    @staticmethod
    def _update_igsn_if_archived(instance: "SamostatnyNalez") -> None:
        """
        Pokud je záznam ve stavu SN4 (archivovaný), aktualizuje jeho IGSN metadata.

        :param instance: Aktualizovaný záznam samostatného nálezu.

        :raises DoiWriteError: Pokud aktualizace IGSN selže.
        """
        if instance.stav == SN_ARCHIVOVANY:
            instance.igsn_update(False, True)

    @staticmethod
    def _acquire_record_lock(ident_cely: str) -> tuple[bool, int]:
        """
        Pokusí se získat zámek záznamu v Redis.

        Kombinuje in-process ``threading.Lock`` (``_record_lock_thread_lock``) pro serializaci
        vláken v rámci jednoho Django workeru s atomickým ``cache.add`` pro koordinaci
        mezi více procesy. Pokud klíč neexistuje nebo má hodnotu ``0`` (uvolněno), zámek je
        získán nastavením hodnoty na ``1``. Pokud je klíč ``1`` (zamčeno jiným workerem),
        čeká ``_RECORD_LOCK_RETRY_DELAY`` sekund a zkusí znovu, nejvýše
        ``_RECORD_LOCK_MAX_RETRIES``-krát.

        :param ident_cely: Identifikátor záznamu, jehož zámek se má získat.

        :return: Dvojice ``(úspěch, ttl)`` — TTL se předává do :meth:`_release_record_lock`,
            aby se zamezilo opakovanému čtení z cache při uvolňování zámku.
        """
        retry_delay, max_retries = PasApiBaseView.get_record_lock_params()
        record_lock_ttl = PasApiBaseView.get_record_lock_ttl()
        cache_key = f"{_RECORD_LOCK_PREFIX}{ident_cely}"
        for _ in range(max_retries):  # noqa: F402
            with PasApiBaseView._record_lock_thread_lock:
                if cache.add(cache_key, 1, timeout=record_lock_ttl):
                    return True, record_lock_ttl
                if cache.get(cache_key) != 1:
                    cache.set(cache_key, 1, timeout=record_lock_ttl)
                    return True, record_lock_ttl
            time.sleep(retry_delay)
        return False, record_lock_ttl

    @staticmethod
    def _release_record_lock(ident_cely: str, ttl: int) -> None:
        """
        Uvolní zámek záznamu nastavením Redis hodnoty na ``0``.

        :param ident_cely: Identifikátor záznamu, jehož zámek se má uvolnit.
        :param ttl: TTL v sekundách — hodnota vrácená z :meth:`_acquire_record_lock`;
            předává se přímo, aby se zamezilo zbytečnému čtení z cache.
        """
        cache_key = f"{_RECORD_LOCK_PREFIX}{ident_cely}"
        cache.set(cache_key, 0, timeout=ttl)

    @staticmethod
    def _verify_content_digest(
        request, uploaded_file, mismatch_status: int = status.HTTP_400_BAD_REQUEST
    ) -> tuple[str, int] | None:
        """
        Ověří integritu souboru pomocí hlavičky ``Content-Digest`` (RFC 9530).

        Očekávaný formát hlavičky: ``sha-512=:<base64>:``
        Pokud hlavička chybí nebo neodpovídá skutečnému SHA-512 obsahu souboru,
        vrátí chybovou zprávu.

        :param request: HTTP požadavek obsahující hlavičku ``Content-Digest``.
        :param uploaded_file: Nahraný soubor; po zavolání je pozice čtení na začátku.
        :param mismatch_status: Stavový kód použitý při neodpovídajícím SHA-512 hashi.

        :return: Dvojice ``(zpráva, status)`` nebo ``None`` pokud je digest v pořádku.
        """
        header = request.headers.get("Content-Digest")
        if not header:
            return (
                _("api.views.PasApiBaseView._verify_content_digest.missing_digest"),
                status.HTTP_400_BAD_REQUEST,
            )

        prefix = "sha-512=:"
        if not header.startswith(prefix) or not header.endswith(":"):
            return (
                _("api.views.PasApiBaseView._verify_content_digest.invalid_format"),
                status.HTTP_400_BAD_REQUEST,
            )

        try:
            expected = base64.b64decode(header[len(prefix) : -1])
        except (ValueError, TypeError):
            return (
                _("api.views.PasApiBaseView._verify_content_digest.invalid_base64"),
                status.HTTP_400_BAD_REQUEST,
            )

        actual = hashlib.sha512(uploaded_file.read()).digest()
        uploaded_file.seek(0)
        if actual != expected:
            return _("api.views.PasApiBaseView._verify_content_digest.digest_mismatch"), mismatch_status

        return None

    @staticmethod
    def _success(
        log_entry: "ApiRequestLog",
        instance: "SamostatnyNalez",
        metadata: bytes,
        notes: list[str],
        http_status: int = 200,
    ) -> HttpResponse:
        """
        Označí log záznam jako úspěšný, zaloguje výsledek a vrátí XML odpověď s metadaty.

        Tato metoda vrací surové XML bajty přes ``HttpResponse`` místo DRF ``Response``,
        aby nedošlo k zásahu rendererů DRF do XML výstupu. Chybové odpovědi v téže view
        jsou vytvářeny metodou ``_fail()``, která používá DRF ``Response`` pro standardní
        serializaci strukturovaného JSON těla.

        :param log_entry: Záznam logu API požadavku.
        :param instance: Uložený záznam samostatného nálezu.
        :param metadata: XML metadata vrácená Fedora repozitářem.
        :param notes: Seznam poznámek o ignorovaných atributech ``xml:lang``.

        :return: HTTP odpověď s XML metadaty a stavovým kódem 200.
        """
        log_entry.status = API_REQUEST_LOG_STATUS_SUCCESS
        log_entry.finished_at = django.utils.timezone.now()
        log_entry.ident_cely = instance.ident_cely
        log_entry.samostatny_nalez = instance
        log_entry.save(update_fields=["status", "finished_at", "ident_cely", "samostatny_nalez"])

        user_pk = log_entry.user.pk if log_entry.user else None
        # ident_cely and user_pk are logged intentionally so successful imports
        # can be correlated during troubleshooting and incident investigation.
        # They are audit/operational identifiers, not secrets.
        # codeql[py/clear-text-logging-sensitive-data]
        logger.info(
            "api.views.PasApiBaseView.success",
            extra={"ident_cely": instance.ident_cely, "user": user_pk},
        )
        if notes:
            # ident_cely, ignored xml:lang notes, and user_pk are logged
            # intentionally to support import diagnostics, troubleshooting, and
            # incident investigation. They are operational context, not secrets.
            # codeql[py/clear-text-logging-sensitive-data]
            logger.info(
                "api.views.PasApiBaseView.success.ignored_lang_notes",
                extra={"ident_cely": instance.ident_cely, "notes": notes, "user": user_pk},
            )
        response = HttpResponse(metadata, content_type="application/xml", status=http_status)
        response["X-Record-ID"] = instance.ident_cely
        response["Location"] = f"{settings.OAI_PURL}{instance.ident_cely}"
        return response


class SamostatnyNalezXmlBaseView(PasApiBaseView):
    """Základní pohled pro XML import záznamu samostatného nálezu."""

    http_method_names = ["post"]

    _AMCR_NS = "https://api.aiscr.cz/schema/amcr/2.2/"
    _XML_NS = "http://www.w3.org/XML/1998/namespace"
    _XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
    _amcr_schema_cache: dict[str, tuple[etree.XMLSchema, float]] = {}  # url -> (schema, inserted_at)
    _VALID_IMPORT_STAVS: tuple[int, ...] = (SN_ZAPSANY, SN_ODESLANY, SN_POTVRZENY)

    def _validation_status(self, errors: list[ImportValidationIssue]) -> int:
        """
        Určí HTTP stavový kód odpovědi na základě typů validačních chyb.

        :param errors: Seznam validačních chyb importu.

        :return: HTTP stavový kód odpovídající nejzávažnějšímu typu chyby.
        """
        if any(error.error_type == ImportErrorType.PERMISSION_ERROR for error in errors):
            return status.HTTP_403_FORBIDDEN
        if any(error.error_type == ImportErrorType.RECORD_DOES_NOT_EXIST for error in errors):
            return status.HTTP_404_NOT_FOUND
        return status.HTTP_422_UNPROCESSABLE_ENTITY

    @classmethod
    def _validate_declared_schema_version(
        cls, doc: etree._ElementTree, allowed_versions: list[float] | None = None
    ) -> str | None:
        """
        Ověří, že XML deklaruje podporovanou verzi AMČR schématu.

        Pokud je předán parametr ``allowed_versions``, zkontroluje navíc, zda verze schématu
        v dokumentu patří mezi povolené verze nakonfigurované v nastavení ``allowed_schema_versions``.

        :param doc: Naparsovaný XML dokument.
        :param allowed_versions: Seznam povolených verzí schématu nebo ``None`` (bez omezení).

        :return: Chybová zpráva nebo ``None``, pokud deklarace odpovídá podporované verzi.
        """
        root = doc.getroot()
        amcr_namespace = root.nsmap.get("amcr")
        if amcr_namespace != AMCR_NAMESPACE_URL:
            return _("api.views.SamostatnyNalezXmlImportView._validate_declared_schema_version.unsupported_namespace")

        schema_location = root.get(f"{{{cls._XSI_NS}}}schemaLocation")
        if not schema_location:
            return _("api.views.SamostatnyNalezXmlImportView._validate_declared_schema_version.missing_schema_location")

        schema_parts = schema_location.split()
        if len(schema_parts) % 2 != 0:
            return _("api.views.SamostatnyNalezXmlImportView._validate_declared_schema_version.invalid_schema_location")

        schema_mapping = dict(zip(schema_parts[0::2], schema_parts[1::2]))
        declared_amcr_xsd = schema_mapping.get(amcr_namespace)
        if declared_amcr_xsd != AMCR_XSD_URL:
            return _(
                "api.views.SamostatnyNalezXmlImportView._validate_declared_schema_version.unsupported_schema_location"
            )

        if allowed_versions is not None:
            m = re.search(r"/schema/amcr/(\d+\.\d+)/", amcr_namespace)
            if m is None:
                return _(
                    "api.views.SamostatnyNalezXmlImportView._validate_declared_schema_version.version_not_extractable"
                )
            version = float(m.group(1))
            if version not in allowed_versions:
                return _(
                    "api.views.SamostatnyNalezXmlImportView._validate_declared_schema_version.version_not_allowed"
                ) % {"version": version}

        return None

    @classmethod
    def _get_amcr_schema(cls, doc: etree._ElementTree) -> etree.XMLSchema:
        """
        Vrátí zkompilované XSD schéma AMČR podle URL deklarované v ``xsi:schemaLocation``.

        :param doc: Naparsovaný XML dokument s deklarovaným ``xsi:schemaLocation``.

        :return: Vrací instanci ``etree.XMLSchema`` pro validaci importovaných XML dokumentů.
        """
        root = doc.getroot()
        amcr_namespace = root.nsmap.get("amcr")
        schema_location = root.get(f"{{{cls._XSI_NS}}}schemaLocation", "")
        schema_mapping = dict(zip(schema_location.split()[0::2], schema_location.split()[1::2]))
        schema_url = schema_mapping[amcr_namespace]
        cls._validate_schema_url_allowed(schema_url)

        now = time.time()
        schema_cache_ttl = cls.get_schema_cache_ttl()
        cached = cls._amcr_schema_cache.get(schema_url)
        if cached is not None and now - cached[1] < schema_cache_ttl:
            return cached[0]

        with _AMCR_SCHEMA_LOCK:
            cached = cls._amcr_schema_cache.get(schema_url)
            if cached is not None and time.time() - cached[1] < schema_cache_ttl:
                return cached[0]

            class _LocalResolver(etree.Resolver):
                """Resolver nahrazující vzdálené W3C URL lokálním souborem xml.xsd."""

                def __init__(self):
                    super().__init__()
                    self.blocked_exception: ImportValidationException | None = None

                def resolve(self, url, id, context):
                    """
                    Načte URL XSD schématu ze sítě nebo Redis cache a vrátí obsah resolveru.

                    :param url: URL požadovaného zdroje.
                    :param id: Identifikátor kontextu parseru.
                    :param context: Kontext resolveru.

                    :return: Vrací obsah XSD schématu pro povolená URL, jinak None.
                    """
                    if url in _ALLOWED_XML_XSD_URLS or any(
                        pattern.match(url) for pattern in _ALLOWED_SCHEMA_URL_PATTERNS
                    ):
                        # W3C xml.xsd and all other allowed schema URLs are fetched from the network
                        # (cached in Redis after first fetch). If the remote is unavailable, the import
                        # endpoint returns 422 — this is intentional: we do not bundle local copies.
                        try:
                            content = _fetch_xsd_bytes(url)
                        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                            logger.warning("Nepodařilo se načíst XSD schéma z URL %s: %s", url, exc)
                            self.blocked_exception = ImportValidationException(
                                ImportValidationIssue(
                                    line=None,
                                    column=None,
                                    message=_(
                                        "api.views.SamostatnyNalezXmlImportView._get_amcr_schema.schema_not_available"
                                    )
                                    % {"url": url},
                                    error_type=ImportErrorType.INVALID_DATA,
                                )
                            )
                            self.blocked_exception.__cause__ = exc
                            return None
                        return self.resolve_string(content, context, base_url=url)
                    # Disallowed URL — store the exception for re-raising after XMLSchema()
                    # because lxml swallows Python exceptions raised inside resolver callbacks.
                    self.blocked_exception = ImportValidationException(
                        ImportValidationIssue(
                            line=None,
                            column=None,
                            message=_("api.views.SamostatnyNalezXmlImportView._get_amcr_schema.disallowed_schema_url")
                            % {"url": url},
                            error_type=ImportErrorType.INVALID_DATA,
                        )
                    )
                    return None

            parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
            resolver = _LocalResolver()
            parser.resolvers.add(resolver)
            try:
                xsd_bytes = _fetch_xsd_bytes(schema_url)
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                logger.warning("Nepodařilo se načíst XSD schéma z URL %s: %s", schema_url, exc)
                raise ImportValidationException(
                    ImportValidationIssue(
                        line=None,
                        column=None,
                        message=_("api.views.SamostatnyNalezXmlImportView._get_amcr_schema.schema_not_available")
                        % {"url": schema_url},
                        error_type=ImportErrorType.INVALID_DATA,
                    )
                ) from exc
            try:
                schema_doc = etree.ElementTree(etree.fromstring(xsd_bytes, parser))
            except etree.XMLSyntaxError as exc:
                logger.warning("Stažené XSD schéma z URL %s není validní XML: %s", schema_url, exc)
                raise ImportValidationException(
                    ImportValidationIssue(
                        line=None,
                        column=None,
                        message=_("api.views.SamostatnyNalezXmlImportView._get_amcr_schema.schema_invalid_xml")
                        % {"url": schema_url},
                        error_type=ImportErrorType.INVALID_DATA,
                    )
                ) from exc
            schema = etree.XMLSchema(schema_doc)
            if resolver.blocked_exception is not None:
                raise resolver.blocked_exception
            cls._amcr_schema_cache[schema_url] = (schema, time.time())
            return schema

    @staticmethod
    def _validate_schema_url_allowed(url: str) -> None:
        """
        Ověří, že URL schématu patří mezi povolené URL prefixy.

        :param url: URL schématu nebo importovaného XSD souboru.

        :raises ImportValidationException: Pokud URL míří mimo povolené domény.
        """
        if not any(pattern.match(url) for pattern in _ALLOWED_SCHEMA_URL_PATTERNS):
            raise ImportValidationException(
                ImportValidationIssue(
                    line=None,
                    column=None,
                    message=_("api.views.SamostatnyNalezXmlImportView._get_amcr_schema.disallowed_schema_url")
                    % {"url": url},
                    error_type=ImportErrorType.INVALID_DATA,
                )
            )

    @classmethod
    def _ns(cls, tag: str) -> str:
        """
        Vrátí tag s prefixem jmenného prostoru AMČR.

        :param tag: Název elementu bez prefixu jmenného prostoru.

        :return: Vrací řetězec ve tvaru ``{namespace}tag``.
        """
        return f"{{{cls._AMCR_NS}}}{tag}"

    @classmethod
    def _get_ignored_lang_notes(cls, elem: etree._Element) -> list[str]:
        """
        Vrátí seznam poznámek pro elementy s nepodporovaným ``xml:lang``.

        :param elem: Importovaný element ``amcr:samostatny_nalez``.

        :return: Seznam textových poznámek.
        """

        notes = []
        lang_attr = f"{{{cls._XML_NS}}}lang"
        for child in elem.iter():
            lang_value = child.get(lang_attr)
            if lang_value and lang_value.lower() != "cs":
                notes.append(
                    _("api.views.SamostatnyNalezXmlImportView.post.ignored_lang_attribute")
                    % {"element": _strip_namespace(child.tag), "lang": lang_value}
                )
        return notes

    @staticmethod
    def _parse_bool(value: str | None) -> bool | None:
        """
        Převede textovou hodnotu XML elementu na Python ``bool``, nebo ``None``.

        Přijímá hodnoty ``"true"`` / ``"1"`` jako ``True`` a ``"false"`` / ``"0"`` jako ``False``
        (bez ohledu na velikost písmen). Ostatní hodnoty a ``None`` vrátí ``None``.

        :param value: Textová hodnota z XML elementu.

        :return: ``True``, ``False``, nebo ``None``.
        """
        if value is None:
            return None
        if value.lower() in ("true", "1"):
            return True
        if value.lower() in ("false", "0"):
            return False
        return None

    @classmethod
    def _text(cls, elem: etree._Element, tag: str) -> str | None:
        """
        Vrátí textový obsah prvního podřízeného elementu se zadaným tagem, nebo None.

        :param elem: Rodičovský element, ve kterém se hledá.
        :param tag: Název hledaného podřízeného elementu (bez jmenného prostoru).

        :return: Textový obsah elementu nebo None, pokud element neexistuje nebo je prázdný.
        """
        child = elem.find(cls._ns(tag))
        if child is None:
            return None
        return (child.text or "").strip() or None

    @classmethod
    def _id_attr(cls, elem: etree._Element, tag: str) -> str | None:
        """
        Vrátí hodnotu atributu ``id`` prvního podřízeného elementu se zadaným tagem.

        Používá se pro elementy typu ``refType`` a ``vocabType``, kde atribut ``id``
        nese ``ident_cely`` odkazovaného záznamu.

        :param elem: Rodičovský element, ve kterém se hledá.
        :param tag: Název hledaného podřízeného elementu (bez jmenného prostoru).

        :return: Hodnota atributu ``id`` nebo None, pokud element nebo atribut neexistuje.
        """
        child = elem.find(cls._ns(tag))
        if child is None:
            return None
        return child.get("id") or None

    # Lightweight shape check for a 2D/3D POINT WKT. Pre-validates user input before
    # passing it to the GEOS C parser, which otherwise logs malformed input to the
    # ``django.contrib.gis`` logger at ERROR level even when the resulting exception
    # is caught here.
    _POINT_WKT_RE = re.compile(
        r"^POINT\s*(?:Z|M|ZM)?\s*\("
        r"\s*[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"
        r"(?:\s+[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?){1,3}"
        r"\s*\)$",
        re.IGNORECASE,
    )

    @classmethod
    def _parse_point_wkt(cls, elem: etree._Element, field_name: str) -> str:
        """
        Ověří, že text XML elementu obsahuje platné WKT geometrie typu ``Point``.

        :param elem: XML element obsahující WKT text.
        :param field_name: Název pole pro chybovou zprávu (``"geom_wkt"`` nebo ``"geom_sjtsk_wkt"``).

        :return: WKT řetězec geometrie.

        :raises ImportValidationException: Pokud je WKT syntakticky neplatné, prázdné nebo není typu ``Point``.
        """
        wkt = (elem.text or "").strip()
        if not wkt:
            raise ImportValidationException(
                ImportValidationIssue(
                    line=elem.sourceline,
                    column=None,
                    message=f"{field_name}: " + _("api.views.SamostatnyNalezXmlBaseView._parse_point_wkt.empty_wkt"),
                    error_type=ImportErrorType.INVALID_DATA,
                )
            )
        # Reject obviously malformed WKT before GEOS sees it. This avoids the C-level
        # ``django.contrib.gis`` ERROR log for inputs like ``POINT(15.5 )``.
        if not cls._POINT_WKT_RE.match(wkt):
            raise ImportValidationException(
                ImportValidationIssue(
                    line=elem.sourceline,
                    column=None,
                    message=f"{field_name}: " + _("api.views.SamostatnyNalezXmlBaseView._parse_point_wkt.invalid_wkt"),
                    error_type=ImportErrorType.INVALID_DATA,
                )
            )
        try:
            geom = GEOSGeometry(wkt)
        except (GEOSException, ValueError):
            raise ImportValidationException(
                ImportValidationIssue(
                    line=elem.sourceline,
                    column=None,
                    message=f"{field_name}: " + _("api.views.SamostatnyNalezXmlBaseView._parse_point_wkt.invalid_wkt"),
                    error_type=ImportErrorType.INVALID_DATA,
                )
            ) from None
        if not isinstance(geom, GEOSPoint):
            raise ImportValidationException(
                ImportValidationIssue(
                    line=elem.sourceline,
                    column=None,
                    message=f"{field_name}: " + _("api.views.SamostatnyNalezXmlBaseView._parse_point_wkt.not_a_point"),
                    error_type=ImportErrorType.INVALID_DATA,
                )
            )
        return wkt

    @classmethod
    def _parse_nalez_element(cls, elem: etree._Element, user) -> tuple[dict, Osoba | None]:
        """
        Převede element ``amcr:samostatny_nalez`` na slovník pro deserializaci.

        Elementy typu ``refType`` a ``vocabType`` se mapují pomocí atributu ``id``,
        který nese ``ident_cely`` odkazovaného záznamu. Geometrie se určují vždy
        z jednoho zdrojového elementu podle ``geom_system``:

        - ``geom_system=4326`` — zdrojem je ``geom_wkt``; ``geom_sjtsk`` se vypočítá
          konverzí do S-JTSK, element ``geom_sjtsk_wkt`` se ignoruje.
        - ``geom_system=5514`` — zdrojem je ``geom_sjtsk_wkt``; ``geom`` se vypočítá
          konverzí do WGS-84, element ``geom_wkt`` se ignoruje.

        ``stav`` — musí být jedna z povolených hodnot (1, 2, 3); určuje cílový stav záznamu po importu.

        Následující elementy jsou v XML povoleny, ale při importu se ignorují:

        - ``igsn`` — přiděluje se automaticky po archivaci záznamu.
        - ``okres`` — stanoví se automaticky podle souřadnic.
        - ``katastr`` (v ``chranene_udaje``) — stanoví se automaticky podle souřadnic.
        - ``geom_gml`` (v ``chranene_udaje``) — geometrie se přebírá z ``geom_wkt``.
        - ``geom_sjtsk_gml`` (v ``chranene_udaje``) — geometrie se přebírá z ``geom_sjtsk_wkt``.
        - ``geom_sjtsk_wkt`` (v ``chranene_udaje``) — ignoruje se, pokud ``geom_system=4326``.
        - ``geom_wkt`` (v ``chranene_udaje``) — ignoruje se, pokud ``geom_system=5514``.
        - ``historie`` — generuje se automaticky systémem.
        - ``soubor`` — soubory se nahrávají samostatným endpointem.

        :param elem: Element ``amcr:samostatny_nalez`` z importovaného XML dokumentu.
        :param user: Uživatel provádějící import.

        :return: Dvojice ``(data, nova_osoba)`` připravená pro import.
        """
        chranene = elem.find(cls._ns("chranene_udaje"))
        nalezce_ident, nova_osoba = cls._parse_nalezce(elem, user)
        projekt_ident = cls._id_attr(elem, "projekt")

        if not projekt_ident:
            raise ImportValidationException(
                ImportValidationIssue(
                    line=elem.sourceline,
                    column=None,
                    message="projekt: "
                    + _("api.views.SamostatnyNalezXmlImportView._parse_nalez_element.missing_projekt"),
                    error_type=ImportErrorType.INVALID_DATA,
                )
            )

        raw_ident_cely = cls._text(elem, "ident_cely")
        if raw_ident_cely is not None and raw_ident_cely != ":tba":
            ident_cely_elem = elem.find(cls._ns("ident_cely"))
            raise ImportValidationException(
                ImportValidationIssue(
                    line=ident_cely_elem.sourceline if ident_cely_elem is not None else elem.sourceline,
                    column=None,
                    message="ident_cely: "
                    + _("api.views.SamostatnyNalezXmlImportView._parse_nalez_element.ident_cely_must_be_tba"),
                    error_type=ImportErrorType.INVALID_DATA,
                )
            )

        raw_stav = cls._text(elem, "stav")
        try:
            stav = int(raw_stav) if raw_stav is not None else None
        except (ValueError, TypeError):
            stav = None
        if stav not in cls._VALID_IMPORT_STAVS:
            stav_elem = elem.find(cls._ns("stav"))
            raise ImportValidationException(
                ImportValidationIssue(
                    line=stav_elem.sourceline if stav_elem is not None else elem.sourceline,
                    column=None,
                    message="stav: " + _("api.views.SamostatnyNalezXmlBaseView._parse_nalez_element.unsupported_stav"),
                    error_type=ImportErrorType.INVALID_DATA,
                )
            )

        data = {
            "ident_cely": None,
            "projekt": projekt_ident,
            "evidencni_cislo": cls._text(elem, "evidencni_cislo"),
            "hloubka": cls._text(elem, "hloubka"),
            "okolnosti": cls._id_attr(elem, "okolnosti"),
            "obdobi": cls._id_attr(elem, "obdobi"),
            "presna_datace": cls._text(elem, "presna_datace"),
            "druh_nalezu": cls._id_attr(elem, "druh_nalezu"),
            "specifikace": cls._id_attr(elem, "specifikace"),
            "pocet": cls._text(elem, "pocet"),
            "poznamka": cls._text(elem, "poznamka"),
            "nalezce": nalezce_ident,
            "datum_nalezu": cls._text(elem, "datum_nalezu"),
            "stav": stav,
            "predano": cls._parse_bool(cls._text(elem, "predano")),
            "predano_organizace": cls._id_attr(elem, "predano_organizace"),
            "geom_system": cls._text(elem, "geom_system"),
            "pristupnost": cls._id_attr(elem, "pristupnost"),
        }

        geom_system = data.get("geom_system")
        if geom_system is not None and geom_system not in ("4326", "5514"):
            geom_system_elem = elem.find(cls._ns("geom_system"))
            raise ImportValidationException(
                ImportValidationIssue(
                    line=geom_system_elem.sourceline if geom_system_elem is not None else elem.sourceline,
                    column=None,
                    message="geom_system: "
                    + _("api.views.SamostatnyNalezXmlBaseView._parse_nalez_element.unsupported_geom_system"),
                    error_type=ImportErrorType.INVALID_DATA,
                )
            )

        if chranene is not None:
            if geom_system not in ("4326", "5514"):
                geom_system_elem = elem.find(cls._ns("geom_system"))
                raise ImportValidationException(
                    ImportValidationIssue(
                        line=geom_system_elem.sourceline if geom_system_elem is not None else elem.sourceline,
                        column=None,
                        message="geom_system: "
                        + _("api.views.SamostatnyNalezXmlBaseView._parse_nalez_element.unsupported_geom_system"),
                        error_type=ImportErrorType.INVALID_DATA,
                    )
                )
            data["lokalizace"] = cls._text(chranene, "lokalizace")
            geom, geom_sjtsk = cls._parse_geom_fields(chranene, geom_system)
            if geom is not None:
                data["geom"] = geom
            if geom_sjtsk is not None:
                data["geom_sjtsk"] = geom_sjtsk

        return {k: v for k, v in data.items() if v is not None}, nova_osoba

    @classmethod
    def _parse_geom_fields(cls, chranene: etree._Element, geom_system: str | None) -> tuple[str | None, str | None]:
        """
        Načte a převede geometrie podle ``geom_system``.

        Při ``geom_system="4326"`` se jako zdroj použije ``geom_wkt`` a výsledek se
        konvertuje do S-JTSK (5514). Element ``geom_sjtsk_wkt`` se ignoruje.
        Při ``geom_system="5514"`` se jako zdroj použije ``geom_sjtsk_wkt`` a výsledek
        se konvertuje do WGS-84 (4326). Element ``geom_wkt`` se ignoruje.

        :param chranene: Element ``amcr:chranene_udaje``.
        :param geom_system: Hodnota elementu ``geom_system`` z importovaného dokumentu.

        :return: Dvojice ``(geom_wgs84, geom_sjtsk)`` nebo ``None`` pro každou hodnotu,
            která nebyla nalezena nebo nebyla poskytnuta.

        :raises ImportValidationException: Pokud konverze souřadnic selže.
        """
        if geom_system == "4326":
            wkt_elem = chranene.find(cls._ns("geom_wkt"))
            if wkt_elem is None or not wkt_elem.text:
                return None, None
            wkt = cls._parse_point_wkt(wkt_elem, "geom_wkt")
            try:
                converted, result_status = transform_geom_to_sjtsk(wkt)
                ok = result_status == "OK"
            except Exception as exc:
                logger.warning("api.views._parse_geom_fields.sjtsk_conversion_failed", extra={"exc": str(exc)})
                ok = False
            if not ok:
                raise ImportValidationException(
                    ImportValidationIssue(
                        line=wkt_elem.sourceline,
                        column=None,
                        message="geom_wkt: "
                        + _("api.views.SamostatnyNalezXmlBaseView._parse_geom_fields.conversion_error"),
                        error_type=ImportErrorType.INVALID_DATA,
                    )
                )
            return wkt, converted

        if geom_system == "5514":
            sjtsk_elem = chranene.find(cls._ns("geom_sjtsk_wkt"))
            if sjtsk_elem is None or not sjtsk_elem.text:
                return None, None
            wkt_sjtsk = cls._parse_point_wkt(sjtsk_elem, "geom_sjtsk_wkt")
            try:
                converted, result_status = transform_geom_to_wgs84(wkt_sjtsk)
                ok = result_status == "OK"
            except Exception as exc:
                logger.warning("api.views._parse_geom_fields.wgs84_conversion_failed", extra={"exc": str(exc)})
                ok = False
            if not ok:
                raise ImportValidationException(
                    ImportValidationIssue(
                        line=sjtsk_elem.sourceline,
                        column=None,
                        message="geom_sjtsk_wkt: "
                        + _("api.views.SamostatnyNalezXmlBaseView._parse_geom_fields.conversion_error"),
                        error_type=ImportErrorType.INVALID_DATA,
                    )
                )
            return converted, wkt_sjtsk

        return None, None

    @classmethod
    def _parse_nalezce(cls, elem: etree._Element, user) -> tuple[str | None, Osoba | None]:
        """
        Zpracuje element ``nalezce`` a vrátí ``ident_cely`` osoby pro import.

        Pokud má element atribut ``id=":tba"``, nejprve se prohledá databáze podle
        ``prijmeni`` a ``jmeno``. Pokud osoba existuje, použije se její ``ident_cely``.
        Teprve pokud záznam neexistuje, vytvoří se nová osoba z textu ve formátu
        ``"Příjmení, Jméno"``. Nová osoba se zde pouze připraví, ale uloží se až
        v transakci společně s ``SamostatnyNalez``.
        Vytvoření nové osoby tímto importním tokem nevyžaduje samostatné oprávnění.

        :param elem: Element ``amcr:samostatny_nalez``.
        :param user: Uživatel provádějící import.

        :return: Dvojice ``(ident_cely_osoby, nova_osoba)``.
        """

        def build_osoba_vypis(prijmeni: str, jmeno: str) -> str:
            """
            Sestaví zkrácený výpis osoby ve formátu používaném aplikací.

            :param prijmeni: Příjmení osoby.
            :param jmeno: Jméno osoby.

            :return: Zkrácený výpis osoby.
            """
            vypis = f"{prijmeni},"
            for cast_jmena in jmeno.split():
                if "-" in cast_jmena:
                    iniciály = [f"{cast[0].upper()}." for cast in cast_jmena.split("-") if cast]
                    vypis += f" {'-'.join(iniciály)}"
                else:
                    vypis += f" {cast_jmena.strip()[0].upper()}."
            return vypis

        def get_nalezce_format_error(nalezce_text: str, casti: list[str]) -> ImportValidationIssue:
            """
            Vrátí detail chyby pro nevalidní formát ``nalezce id=":tba"``.

            :param nalezce_text: Původní text elementu ``nalezce``.
            :param casti: Rozdělené části textu podle první čárky.

            :return: Detail chyby s kódem ``invalid_data``.
            """
            if "," not in nalezce_text:
                message = _("api.views.SamostatnyNalezXmlImportView._parse_nalezce.incorrect_format_missing_separator")
            elif len(casti) < 2 or not casti[0]:
                message = _("api.views.SamostatnyNalezXmlImportView._parse_nalezce.incorrect_format_missing_surname")
            elif not casti[1]:
                message = _("api.views.SamostatnyNalezXmlImportView._parse_nalezce.incorrect_format_missing_name")
            else:
                message = _("api.views.SamostatnyNalezXmlImportView._parse_nalezce.incorrect_format")
            return ImportValidationIssue(
                line=nalezce_elem.sourceline if nalezce_elem is not None else elem.sourceline,
                column=None,
                message=f"nalezce: {message}",
                error_type=ImportErrorType.INVALID_DATA,
            )

        nalezce_elem = elem.find(cls._ns("nalezce"))
        if nalezce_elem is None:
            return None, None

        nalezce_id = nalezce_elem.get("id")
        if nalezce_id != ":tba":
            return nalezce_id or None, None

        nalezce_text = (nalezce_elem.text or "").strip()
        casti = [cast.strip() for cast in nalezce_text.split(",", 1)]
        if len(casti) != 2 or not casti[0] or not casti[1]:
            raise ImportValidationException(get_nalezce_format_error(nalezce_text, casti))

        prijmeni, jmeno = casti
        jmeno = " ".join(jmeno.split())

        existing = Osoba.objects.filter(prijmeni=prijmeni, jmeno=jmeno).first()
        if existing is not None:
            return existing.ident_cely, None

        osoba = Osoba(
            prijmeni=prijmeni,
            jmeno=jmeno,
            vypis=build_osoba_vypis(prijmeni, jmeno),
            vypis_cely=f"{prijmeni}, {jmeno}",
        )
        osoba.suppress_signal = True
        return None, osoba


class SamostatnyNalezXmlImportView(SamostatnyNalezXmlBaseView):
    """Pohled pro import záznamu samostatného nálezu z XML souboru přes POST požadavek."""

    _IMPORT_HISTORY_NOTE = gettext_lazy("api.views.SamostatnyNalezXmlImportView.import_history_note")

    def post(self, request, format=None):
        """
        Importuje nový záznam samostatného nálezu z XML souboru.

        Přijímá soubor v parametru ``file`` (multipart/form-data). XML musí projít validací
        proti XSD schématu AMČR deklarovanému v dokumentu (verze 2.2 na URL
        ``https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd`` nebo novější). Volitelné nastavení administrace
        ``allowed_schema_versions`` může omezit povolené číslo verze schématu v namespace
        dokumentu (viz ``PasApiPermissionMixin.get_allowed_schema_versions``).
        Dokument musí obsahovat právě jeden element ``amcr:samostatny_nalez``.

        :param request: HTTP požadavek obsahující XML soubor v poli ``file``.
        :param format: Formát odpovědi.

        :return: Vrací ``Response`` s metadaty vytvořeného záznamu (HTTP 200),
                 nebo chybou syntaxe volání (HTTP 400), chybějícím projektem (HTTP 404),
                 nevalidním XML či datovými chybami (HTTP 422).
        """
        xml_file = request.FILES.get("file")

        log_entry = ApiRequestLog.objects.create(
            user=request.user,
            client_ip=self.get_client_ip(request),
            request_target=API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_XML_IMPORT,
            filename=xml_file.name if xml_file is not None else None,
            file_size=xml_file.size if xml_file is not None else None,
        )

        if xml_file is None:
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezXmlImportView.post.missing_file")},
                status.HTTP_400_BAD_REQUEST,
            )

        digest_error = self._verify_content_digest(request, xml_file)
        if digest_error:
            digest_message, digest_status = digest_error
            return self._fail(log_entry, {"detail": digest_message}, digest_status)

        try:
            parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
            # Read content into bytes first so etree.fromstring() receives a bytes value,
            # not a file-like object. etree.parse() accepts both paths and file objects,
            # causing CodeQL (py/path-injection) to flag it when the argument is
            # user-supplied. etree.fromstring() only accepts str/bytes, breaking the taint
            # path entirely without changing runtime behaviour.
            doc = etree.ElementTree(etree.fromstring(xml_file.read(), parser=parser))
        except etree.XMLSyntaxError as exc:
            # The parser error text and user ID are logged intentionally for XML
            # troubleshooting and incident investigation. They are operational
            # diagnostics, not secrets.
            # codeql[py/clear-text-logging-sensitive-data]
            logger.warning(
                "api.views.SamostatnyNalezXmlImportView.post.xml_syntax_error",
                extra={"error": str(exc), "user": request.user.pk},
            )
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezXmlImportView.post.invalid_xml_syntax")},
                status.HTTP_400_BAD_REQUEST,
            )

        version_error = self._validate_declared_schema_version(doc, allowed_versions=self.get_allowed_schema_versions())
        if version_error:
            return self._fail(log_entry, {"detail": version_error}, status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:
            schema = self._get_amcr_schema(doc)
        except ImportValidationException as exc:
            return self._fail(
                log_entry,
                {"validation_errors": [e.to_dict() for e in exc.import_errors]},
                self._validation_status(exc.import_errors),
            )

        if not schema.validate(doc):
            errors = [
                ImportValidationIssue(
                    line=e.line,
                    column=e.column,
                    message=_("api.views.SamostatnyNalezXmlImportView.post.schema_error_item")
                    % {"line": e.line, "column": e.column, "message": e.message},
                    error_type=ImportErrorType.INVALID_DATA,
                )
                for e in schema.error_log
            ]
            # Schema validation details and user ID are logged intentionally to
            # support import troubleshooting and incident investigation. These
            # are operational diagnostics, not secrets.
            # codeql[py/clear-text-logging-sensitive-data]
            logger.warning(
                "api.views.SamostatnyNalezXmlImportView.post.schema_invalid",
                extra={"errors": [error.to_dict() for error in errors], "user": request.user.pk},
            )
            return self._fail(
                log_entry,
                {"schema_errors": [error.to_dict() for error in errors]},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        root = doc.getroot()
        root_children = list(root)
        nalez_elements = [child for child in root_children if child.tag == self._ns("samostatny_nalez")]
        if not root_children:
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezXmlImportView.post.missing_samostatny_nalez")},
                status.HTTP_400_BAD_REQUEST,
            )
        if len(nalez_elements) > 1:
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezXmlImportView.post.multiple_samostatny_nalez")},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if len(root_children) != 1 or not nalez_elements:
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezXmlImportView.post.invalid_root_content")},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # XML je validní a obsahuje právě jeden záznam — přepneme stav na PROCESSING.
        log_entry.status = API_REQUEST_LOG_STATUS_PROCESSING
        log_entry.save(update_fields=["status"])

        elem = nalez_elements[0]
        notes = self._get_ignored_lang_notes(elem)
        try:
            data, nova_osoba = self._parse_nalez_element(elem, request.user)
        except ImportValidationException as exc:
            return self._fail(
                log_entry,
                {"validation_errors": [e.to_dict() for e in exc.import_errors]},
                self._validation_status(exc.import_errors),
            )

        projekt_ident = data.get("projekt")
        if projekt_ident and not Projekt.objects.filter(ident_cely=projekt_ident).exists():
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezXmlImportView.post.projekt_not_found")},
                status.HTTP_404_NOT_FOUND,
            )

        if not self._has_import_permissions(request.user, data):
            # The denied user ID and referenced project are logged intentionally
            # for authorization troubleshooting and incident investigation.
            # They are audit/operational identifiers, not secrets.
            # codeql[py/clear-text-logging-sensitive-data]
            logger.warning(
                "api.views.SamostatnyNalezXmlImportView.post.permission_denied",
                extra={"user": request.user.pk, "projekt": data.get("projekt")},
            )
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezXmlImportView.post.permission_denied")},
                status.HTTP_403_FORBIDDEN,
            )

        instance = None
        fedora_transaction = FedoraTransaction(transaction_user=request.user)
        try:
            with transaction.atomic():
                serializer_data = dict(data)
                if nova_osoba is not None:
                    nova_osoba.active_transaction = fedora_transaction
                    # active_transaction is an attribute that defines a Fedora transaction attached to the objects,
                    # not a database field, so there is no point in using it as an argument in the save method.
                    nova_osoba.save()  # Osoba must be saved to get ident_cely before the serializer validation
                    serializer_data["nalezce"] = nova_osoba.ident_cely

                serializer = SamostatnyNalezXmlImportSerializer(data=serializer_data)
                if not serializer.is_valid():
                    raise ImportValidationException.from_serializer_errors(serializer.errors, line=elem.sourceline)

                instance = SamostatnyNalez(**serializer.validated_data)
                if not instance.ident_cely:
                    instance.ident_cely = get_sn_ident(instance.projekt)
                # Souřadnice jsou povinné až od stavu SN2 (odeslaný). Ve stavu SN1 (zapsaný)
                # je dovoleno vyplnit jen ``geom_system`` bez ``geom_wkt`` / ``geom_sjtsk_wkt`` —
                # stejně jako v běžné aplikaci AMČR.
                if instance.stav != SN_ZAPSANY and instance.geom is None and instance.geom_sjtsk is None:
                    raise ImportValidationException(
                        ImportValidationIssue(
                            line=elem.sourceline,
                            column=None,
                            message=_("api.views.SamostatnyNalezXmlImportView.post.missing_geom"),
                            error_type=ImportErrorType.INVALID_DATA,
                        )
                    )

                # Pravidla převzatá z ``pas.forms.PotvrditNalezForm`` ("Uložení" v UI):
                # ``pristupnost`` je povinná pro každý importovaný záznam;
                # ``evidencni_cislo``, ``predano`` a ``predano_organizace`` jsou povinné
                # navíc při stavu SN_POTVRZENY. V UI tato validace běží mimo hlavní
                # serializer (v modálním okně), takže ji zde replikujeme pro shodu chování.
                missing_potvrzeni_fields: list[str] = []
                predano_must_be_true = False
                if instance.stav >= SN_POTVRZENY:
                    if not instance.evidencni_cislo:
                        missing_potvrzeni_fields.append("evidencni_cislo")
                    if instance.predano is None:
                        missing_potvrzeni_fields.append("predano")
                    elif instance.predano is False:
                        predano_must_be_true = True
                    if instance.predano_organizace_id is None:
                        missing_potvrzeni_fields.append("predano_organizace")
                if missing_potvrzeni_fields:
                    raise ImportValidationException(
                        ImportValidationIssue(
                            line=elem.sourceline,
                            column=None,
                            message=", ".join(missing_potvrzeni_fields)
                            + ": "
                            + _("api.views.SamostatnyNalezXmlImportView.post.required_potvrzeni_field_missing"),
                            error_type=ImportErrorType.INVALID_DATA,
                        )
                    )
                if predano_must_be_true:
                    raise ImportValidationException(
                        ImportValidationIssue(
                            line=elem.sourceline,
                            column=None,
                            message="predano: " + _("api.views.SamostatnyNalezXmlImportView.post.predano_must_be_true"),
                            error_type=ImportErrorType.INVALID_DATA,
                        )
                    )

                geom_wgs84 = instance.geom
                if geom_wgs84 is None and instance.geom_sjtsk is not None:
                    # Clone so that the stored geom_sjtsk field is never mutated; WGS-84 is
                    # only needed transiently to identify the cadastre.
                    geom_wgs84 = instance.geom_sjtsk.clone()
                    geom_wgs84.transform(4326)
                if geom_wgs84:
                    instance.katastr = get_cadastre_from_point(geom_wgs84)
                    if instance.katastr is None:
                        raise ImportValidationException(
                            ImportValidationIssue(
                                line=elem.sourceline,
                                column=None,
                                message=_("api.views.SamostatnyNalezXmlImportView.post.katastr_not_found"),
                                error_type=ImportErrorType.INVALID_DATA,
                            )
                        )
                if instance.stav in (SN_ODESLANY, SN_POTVRZENY):
                    pred_odeslanim_errors = instance.check_pred_odeslanim(skip_soubory_check=True)
                    if pred_odeslanim_errors:
                        raise ImportValidationException(
                            ImportValidationIssue(
                                line=elem.sourceline,
                                column=None,
                                message=_("api.views.SamostatnyNalezXmlImportView.post.check_pred_odeslanim_failed")
                                + " "
                                + "; ".join(pred_odeslanim_errors),
                                error_type=ImportErrorType.INVALID_DATA,
                            )
                        )
                if instance.stav == SN_POTVRZENY:
                    pred_potvrzenim_errors = instance.check_pred_potvrzenim(skip_soubory_check=True)
                    if pred_potvrzenim_errors:
                        raise ImportValidationException(
                            ImportValidationIssue(
                                line=elem.sourceline,
                                column=None,
                                message=_("api.views.SamostatnyNalezXmlImportView.post.check_pred_potvrzenim_failed")
                                + " "
                                + "; ".join(pred_potvrzenim_errors),
                                error_type=ImportErrorType.INVALID_DATA,
                            )
                        )

                instance.active_transaction = fedora_transaction
                # active_transaction is an attribute that defines a Fedora transaction attached to the objects,
                # not a database field, so there is no point in using it as an argument in the save method.
                instance.save()
                self._create_import_history_records(instance, request.user)
                # Do not set close_active_transaction_when_finished so that fedora_transaction
                # stays open after the DB commit, allowing us to verify the Fedora write below.
                instance.save()
        except ImportValidationException as exc:
            logger.warning("api.views.SamostatnyNalezXmlImportView.post.import_validation_error", extra={"error": exc})
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            return self._fail(
                log_entry,
                {"validation_errors": [e.to_dict() for e in exc.import_errors]},
                self._validation_status(exc.import_errors),
            )
        except IntegrityError as err:
            logger.warning("api.views.SamostatnyNalezXmlImportView.post.integrity_error", extra={"error": err})
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            constraint = getattr(getattr(err.__cause__, "diag", None), "constraint_name", None)
            if constraint == "osoba_jmeno_prijmeni_key":
                detail = _("api.views.SamostatnyNalezXmlImportView.post.nalezce_already_exists")
            else:
                detail = _("api.views.SamostatnyNalezXmlImportView.post.integrity_error")
            return self._fail(
                log_entry,
                {"detail": detail},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except FedoraError as err:
            logger.error("api.views.SamostatnyNalezXmlImportView.post.fedora_error", extra={"error": err})
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezXmlImportView.post.internal_error")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except DatabaseError as err:
            logger.error("api.views.SamostatnyNalezXmlImportView.post.database_error", extra={"error": err})
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezXmlImportView.post.internal_error")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as err:
            logger.error("api.views.SamostatnyNalezXmlImportView.post.unexpected_error", extra={"error": err})
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezXmlImportView.post.internal_error")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # The DB transaction has committed. fedora_transaction is still open because
        # close_active_transaction_when_finished was not set. Read the metadata back from
        # Fedora within the same transaction to verify the save, then commit.
        try:
            metadata = FedoraRepositoryConnector(instance, fedora_transaction).get_metadata()
            fedora_transaction.mark_transaction_as_closed()
        except FedoraError as err:
            logger.error(
                "api.views.SamostatnyNalezXmlImportView.post.fedor_error_reading_data_after_saving",
                extra={"error": err},
            )
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezXmlImportView.post.fedor_error_reading_data_after_saving")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return self._success(log_entry, instance, metadata, notes, http_status=status.HTTP_201_CREATED)

    @staticmethod
    def _has_import_permissions(user, data: dict) -> bool:
        """
        Ověří oprávnění potřebná pro import samostatného nálezu.

        Kontroluje dvě podmínky: stav záznamu musí odpovídat roli uživatele (badatel
        nejvýše stav 1, ostatní role nejvýše stav 3) a projekt musí být součástí
        průzkumných projektů dostupných danému uživateli dle
        :meth:`projekt.models.Projekt.get_pruzkum_projekty_pro_uzivatele`.

        :param user: Uživatel provádějící import.
        :param data: Data jednoho importovaného záznamu jako slovník; očekávají se klíče
            ``stav`` (int) a ``projekt`` (ident_cely projektu).
        :return: ``True`` pokud jsou splněny obě podmínky, jinak ``False``.
        """

        stav = data.get("stav")

        if stav is None or stav > 3:
            return False

        if user.hlavni_role.pk == ROLE_BADATEL_ID and stav > 1:
            return False

        projekt_ident = data.get("projekt")
        return Projekt.get_pruzkum_projekty_pro_uzivatele(user).filter(ident_cely=projekt_ident).exists()

    @classmethod
    def _create_import_history_records(cls, instance: SamostatnyNalez, user) -> None:
        """
        Vytvoří záznamy historie pro importovaný samostatný nález.

        Vytvoří pouze záznamy odpovídající přechodům až do cílového stavu záznamu:
        stav 1 → ZAPSANI_SN, stav 2 → ZAPSANI_SN + ODESLANI_SN,
        stav 3 → ZAPSANI_SN + ODESLANI_SN + POTVRZENI_SN.

        :param instance: Vytvořený záznam samostatného nálezu.
        :param user: Uživatel, který provedl import.
        """
        _all_transitions = [
            (SN_ZAPSANY, ZAPSANI_SN),
            (SN_ODESLANY, ODESLANI_SN),
            (SN_POTVRZENY, POTVRZENI_SN),
        ]
        Historie.objects.bulk_create(
            [
                Historie(
                    typ_zmeny=typ_zmeny,
                    uzivatel=user,
                    vazba=instance.historie,
                    poznamka=cls._IMPORT_HISTORY_NOTE,
                )
                for stav_threshold, typ_zmeny in _all_transitions
                if instance.stav >= stav_threshold
            ]
        )


class SamostatnyNalezEvidencniCisloPatchView(PasApiBaseView):
    """Pohled pro aktualizaci pole ``evidencni_cislo`` záznamu samostatného nálezu přes PATCH požadavek."""

    http_method_names = ["patch"]
    # SamostatnyNalez.evidencni_cislo is a TextField (no max_length in the DB schema).
    # 255 is an API-level policy limit enforced here, not derived from the model field.
    _MAX_EVIDENCNI_CISLO_LENGTH = 255

    @classmethod
    def _has_edit_permissions(cls, user, ident_cely) -> bool:
        """
        Ověří, zda má uživatel oprávnění editovat evidenční číslo záznamu samostatného nálezu.

        Oprávněný je takový uživatel, který splňuje standardní pravidla pro editaci nálezu
        s těmito úpravami:

        - pro aktualizaci ev. čísla nikdy není autorizován badatel (operaci může užívat
          pouze archeolog a výše)
        - pokud je autorizován archeolog, nález může být v libovolném stavu (vč. archivovaného)

        :param user: Uživatel provádějící požadavek.
        :param ident_cely: Identifikátor záznamu samostatného nálezu.

        :return: Vrací ``True`` pokud má uživatel oprávnění ``pas_edit`` pro daný záznam
                 a zároveň je jeho hlavní role Archeolog nebo vyšší.
        """
        if not check_permissions(Permissions.actionChoices.pas_edit, user, ident_cely, skip_status=True):
            return False
        return user.hlavni_role.pk >= ROLE_ARCHEOLOG_ID

    def patch(self, request, ident_cely: str, format=None):
        """
        Aktualizuje pole ``evidencni_cislo`` záznamu samostatného nálezu.

        Přijímá ``ident_cely`` záznamu jako součást URL a novou hodnotu ``evidencni_cislo``
        jako query parametr. Parametr ``evidencni_cislo`` je povinný a jeho
        hodnota musí být neprázdná. Endpoint rozlišuje mezi chybějícím
        parametrem a přítomným parametrem s prázdnou hodnotou, aby klient
        mohl oba validační stavy zpracovat odlišně.

        Příklad volání::

            PATCH /pas/api/nalez/M-202400001-N00001/evidencni-cislo?evidencni_cislo=EC-2024-001

        :param request: HTTP požadavek s povinným query parametrem
                        ``evidencni_cislo``, který nesmí být prázdný.
        :param ident_cely: Identifikátor záznamu samostatného nálezu.
        :param format: Formát odpovědi.

        :return: Vrací XML metadata aktualizovaného záznamu (HTTP 200),
                 nebo chybou syntaxe volání (HTTP 400; chybějící parametr
                 ``evidencni_cislo``), chybou dat (HTTP 422; prázdná nebo příliš
                 dlouhá hodnota), nenalezeným
                 záznamem (HTTP 404), nedostatečnými oprávněními (HTTP 403),
                 nebo interní chybou (HTTP 500).
        """
        log_entry = ApiRequestLog.objects.create(
            user=request.user,
            client_ip=self.get_client_ip(request),
            request_target=API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_EVIDENCNI_CISLO_PATCH,
        )

        if "evidencni_cislo" not in request.query_params:
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezEvidencniCisloPatchView.patch.missing_evidencni_cislo")},
                status.HTTP_400_BAD_REQUEST,
            )

        evidencni_cislo = request.query_params["evidencni_cislo"].strip()

        # "Missing" and "empty" must stay separate so API clients can
        # distinguish an omitted query parameter from an explicitly invalid
        # empty value.
        if evidencni_cislo == "":
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezEvidencniCisloPatchView.patch.empty_evidencni_cislo")},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if len(evidencni_cislo) > self._MAX_EVIDENCNI_CISLO_LENGTH:
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezEvidencniCisloPatchView.patch.evidencni_cislo_too_long")},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        try:
            instance = SamostatnyNalez.objects.get(ident_cely=ident_cely)
        except SamostatnyNalez.DoesNotExist:
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezEvidencniCisloPatchView.patch.not_found")},
                status.HTTP_404_NOT_FOUND,
            )

        if not self._has_edit_permissions(request.user, ident_cely):
            # The denied user ID and ident_cely are logged intentionally for
            # authorization troubleshooting and incident investigation.
            # They are audit/operational identifiers, not secrets.
            # codeql[py/clear-text-logging-sensitive-data]
            logger.warning(
                "api.views.SamostatnyNalezEvidencniCisloPatchView.patch.permission_denied",
                extra={"user": request.user.pk, "ident_cely": ident_cely},
            )
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezEvidencniCisloPatchView.patch.permission_denied")},
                status.HTTP_403_FORBIDDEN,
            )

        if evidencni_cislo == instance.evidencni_cislo:
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezEvidencniCisloPatchView.patch.no_change")},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        acquired, lock_ttl = self._acquire_record_lock(ident_cely)
        if not acquired:
            return self._fail(
                log_entry,
                {"detail": _("api.views.PasApiBaseView.record_locked")},
                status.HTTP_429_TOO_MANY_REQUESTS,
            )

        log_entry.status = API_REQUEST_LOG_STATUS_PROCESSING
        log_entry.save(update_fields=["status"])

        old_evidencni_cislo = instance.evidencni_cislo
        fedora_transaction = FedoraTransaction(transaction_user=request.user)
        try:
            with transaction.atomic():
                instance.evidencni_cislo = evidencni_cislo
                instance.active_transaction = fedora_transaction
                # active_transaction is an attribute that defines a Fedora transaction attached to the objects,
                # not a database field, so there is no point in using it as an argument in the save method.
                instance.save(update_fields=["evidencni_cislo"])
                self._create_history_record(instance, request.user, old_evidencni_cislo, evidencni_cislo)
                self._update_igsn_if_archived(instance)
        except DoiWriteError as err:
            logger.error("api.views.SamostatnyNalezEvidencniCisloPatchView.patch.igsn_error", extra={"error": err})
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            self._release_record_lock(ident_cely, lock_ttl)
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezEvidencniCisloPatchView.patch.doi_update_error")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except FedoraError as err:
            logger.error("api.views.SamostatnyNalezEvidencniCisloPatchView.patch.fedora_error", extra={"error": err})
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            self._release_record_lock(ident_cely, lock_ttl)
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezEvidencniCisloPatchView.patch.internal_error")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except DatabaseError as err:
            logger.error("api.views.SamostatnyNalezEvidencniCisloPatchView.patch.database_error", extra={"error": err})
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            self._release_record_lock(ident_cely, lock_ttl)
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezEvidencniCisloPatchView.patch.internal_error")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as err:
            logger.error(
                "api.views.SamostatnyNalezEvidencniCisloPatchView.patch.unexpected_error", extra={"error": err}
            )
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            self._release_record_lock(ident_cely, lock_ttl)
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezEvidencniCisloPatchView.patch.internal_error")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            metadata = FedoraRepositoryConnector(instance, fedora_transaction).get_metadata()
            fedora_transaction.mark_transaction_as_closed()
        except FedoraError as err:
            logger.error(
                "api.views.SamostatnyNalezEvidencniCisloPatchView.patch.fedora_error_reading_metadata",
                extra={"error": err},
            )
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            self._release_record_lock(ident_cely, lock_ttl)
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezEvidencniCisloPatchView.patch.fedora_error_reading_metadata")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        self._release_record_lock(ident_cely, lock_ttl)
        return self._success(log_entry, instance, metadata, [])

    @staticmethod
    def _create_history_record(instance: SamostatnyNalez, user, old_value: str | None, new_value: str | None) -> None:
        """
        Vytvoří záznam historie pro aktualizaci pole ``evidencni_cislo``.

        Poznámka záznamu má formát ``<přeložený popisek>: old_value -> new_value``. Je-li záznam ve stavu
        SN4 (archivovaný), zapíše se navíc záznam ``SN34``, který obnoví datum archivace.

        :param instance: Aktualizovaný záznam samostatného nálezu.
        :param user: Uživatel, který provedl aktualizaci.
        :param old_value: Původní hodnota pole ``evidencni_cislo``.
        :param new_value: Nová hodnota pole ``evidencni_cislo``.
        """
        Historie.objects.create(
            typ_zmeny=AKTUALIZACE_SN,
            uzivatel=user,
            vazba=instance.historie,
            poznamka="{}: {} -> {}".format(
                _("api.views.SamostatnyNalezEvidencniCisloPatchView.history.note"),
                old_value,
                new_value,
            ),
        )
        if instance.stav == SN_ARCHIVOVANY:
            Historie.objects.create(
                typ_zmeny=ARCHIVACE_SN,
                uzivatel=user,
                vazba=instance.historie,
            )


class SamostatnyNalezFotografieUploadView(PasApiBaseView):
    """Pohled pro nahrání jedné fotografie k existujícímu samostatnému nálezu."""

    http_method_names = ["post"]

    @staticmethod
    def _has_upload_permissions(user, ident_cely) -> bool:
        """
        Ověří, zda má uživatel oprávnění nahrát fotografii k danému nálezu.

        Oprávněný je takový uživatel, který splňuje standardní pravidla pro nahrání
        souboru k samostatnému nálezu (``soubor_nahrat_pas``) s touto úpravou:

        - pro archeologa a vyšší roli je nález povolen v libovolném stavu (vč.
          archivovaného) — tj. ``skip_status=True``
        - pro badatele platí standardní pravidlo AMČR (typicky vlastní nález ve
          stavu 1) — ``skip_status`` se neuplatní

        :param user: Uživatel provádějící požadavek.
        :param ident_cely: Identifikátor záznamu samostatného nálezu.

        :return: ``True`` pokud má uživatel oprávnění ``soubor_nahrat_pas`` pro daný záznam
                 podle pravidel pro svou roli.
        """
        skip_status = user.hlavni_role.pk >= ROLE_ARCHEOLOG_ID
        return check_permissions(Permissions.actionChoices.soubor_nahrat_pas, user, ident_cely, skip_status=skip_status)

    @staticmethod
    def _create_rearchive_history_record(instance: SamostatnyNalez, user) -> None:
        """
        Pro archivovaný nález zapíše do historie tichou reachivaci ``SN34``.

        :param instance: Aktualizovaný záznam samostatného nálezu.
        :param user: Uživatel, který provedl upload fotografie.
        """
        if instance.stav == SN_ARCHIVOVANY:
            Historie.objects.create(
                typ_zmeny=ARCHIVACE_SN,
                uzivatel=user,
                vazba=instance.historie,
            )

    def post(self, request, ident_cely: str, format=None):
        """
        Nahraje fotografii k existujícímu záznamu samostatného nálezu.

        Přijímá ``ident_cely`` záznamu jako součást URL a jeden binární soubor v parametru
        ``file`` (multipart/form-data). Soubor musí projít kontrolou ``Content-Digest``,
        MIME typu a antiviru. Úspěšný upload uloží fotografii do Fedora repository,
        založí záznam ``Soubor`` navázaný na nález a vrátí aktualizovaná XML metadata z Fedory.

        :param request: HTTP požadavek obsahující fotografii v poli ``file``.
        :param ident_cely: Identifikátor aktualizovaného záznamu samostatného nálezu.
        :param format: Formát odpovědi.

        :return: Vrací XML metadata aktualizovaného záznamu (HTTP 201),
                 nebo chybu syntaxe volání (HTTP 400; vč. více než jednoho souboru),
                 nenalezený záznam (HTTP 404), validační chybu souboru (HTTP 422),
                 nebo interní chybu (HTTP 500).
        """
        uploaded_files = request.FILES.getlist("file")
        uploaded_file = uploaded_files[0] if uploaded_files else None

        log_entry = ApiRequestLog.objects.create(
            user=request.user,
            client_ip=self.get_client_ip(request),
            request_target=API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_FOTOGRAFIE_UPLOAD,
            filename=uploaded_file.name if uploaded_file is not None else None,
            file_size=uploaded_file.size if uploaded_file is not None else None,
        )

        try:
            instance = SamostatnyNalez.objects.get(ident_cely=ident_cely)
        except SamostatnyNalez.DoesNotExist:
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezFotografieUploadView.post.not_found")},
                status.HTTP_404_NOT_FOUND,
            )

        if not self._has_upload_permissions(request.user, ident_cely):
            # The denied user ID and ident_cely are logged intentionally for
            # authorization troubleshooting and incident investigation.
            # They are audit/operational identifiers, not secrets.
            # codeql[py/clear-text-logging-sensitive-data]
            logger.warning(
                "api.views.SamostatnyNalezFotografieUploadView.post.permission_denied",
                extra={"user": request.user.pk, "ident_cely": ident_cely},
            )
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezFotografieUploadView.post.permission_denied")},
                status.HTTP_403_FORBIDDEN,
            )

        # File presence is checked after the permission check intentionally: returning 403
        # before 400 avoids leaking whether the endpoint accepts files to unauthorized callers.
        if uploaded_file is None:
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezFotografieUploadView.post.missing_file")},
                status.HTTP_400_BAD_REQUEST,
            )

        # Reject requests carrying more than one upload (either multiple "file" parts
        # or additional unexpected file parts) explicitly, instead of letting them be
        # detected only via the Content-Digest mismatch.
        total_files = sum(len(files) for _, files in request.FILES.lists())
        if len(uploaded_files) > 1 or total_files > 1:
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezFotografieUploadView.post.multiple_files")},
                status.HTTP_400_BAD_REQUEST,
            )

        if uploaded_file.size > MAX_PAS_API_FOTOGRAFIE_FILE_SIZE_BYTES:
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezFotografieUploadView.post.file_too_large")},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        mime_check = Soubor.check_mime_for_url(uploaded_file, request.path)
        if mime_check == "encrypted":
            return self._fail(
                log_entry,
                {"detail": _("core.views.post_upload.encrypted")},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if mime_check is False:
            return self._fail(
                log_entry,
                {"detail": _("core.views.post_upload.mime_check_failed")},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        digest_error = self._verify_content_digest(
            request,
            uploaded_file,
            mismatch_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
        if digest_error:
            digest_message, digest_status = digest_error
            return self._fail(log_entry, {"detail": digest_message}, digest_status)

        binary_data = io.BytesIO(uploaded_file.read())
        antivirus_result = Soubor.check_antivirus(binary_data)
        if antivirus_result == AntivirusCheckResult.VIRUS_FOUND:
            return self._fail(
                log_entry,
                {"detail": _("core.views.post_upload.antivirus_check.virus_found")},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if antivirus_result == AntivirusCheckResult.CHECK_FAILED:
            return self._fail(
                log_entry,
                {"detail": _("core.views.post_upload.antivirus_check.check_failed")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        binary_data.seek(0)
        uploaded_file.seek(0)

        acquired, lock_ttl = self._acquire_record_lock(ident_cely)
        if not acquired:
            return self._fail(
                log_entry,
                {"detail": _("api.views.PasApiBaseView.record_locked")},
                status.HTTP_429_TOO_MANY_REQUESTS,
            )

        log_entry.status = API_REQUEST_LOG_STATUS_PROCESSING
        log_entry.save(update_fields=["status"])

        mimetype = Soubor.get_mime_types(uploaded_file)
        mime_extensions = Soubor.get_file_extension_by_mime(uploaded_file)
        if len(mime_extensions) == 0:
            self._release_record_lock(ident_cely, lock_ttl)
            return self._fail(
                log_entry,
                {"detail": _("core.views.post_upload.mime_rename_failed")},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        new_name = get_finds_soubor_name(instance, uploaded_file.name)
        if new_name is False:
            self._release_record_lock(ident_cely, lock_ttl)
            return self._fail(
                log_entry,
                {
                    "detail": (
                        _("core.views.post_upload.error.maximal_file_name_exceeded_part_1")
                        + f" {ident_cely} "
                        + _("core.views.post_upload.error.maximal_file_name_exceeded_part_2")
                    )
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if mimetype in ["image/png", "image/jpeg", "image/tiff"]:
            binary_data = Soubor.remove_gps_data(binary_data)

        fedora_transaction = FedoraTransaction(transaction_user=request.user)
        try:
            connector = FedoraRepositoryConnector(instance, fedora_transaction, skip_container_check=False)
            rep_bin_file = connector.save_binary_file(new_name, mimetype, binary_data)
            soubor_instance = Soubor(
                vazba=instance.soubory,
                nazev=new_name,
                mimetype=mimetype,
                size_mb=rep_bin_file.size_mb,
                path=rep_bin_file.url_without_domain,
                sha_512=rep_bin_file.sha_512,
            )
            soubor_instance.active_transaction = fedora_transaction
            soubor_instance.binary_data = binary_data
            with transaction.atomic():
                soubor_instance.save()
                soubor_instance.zaznamenej_nahrani(request.user, uploaded_file.name)
                self._create_rearchive_history_record(instance, request.user)
                self._update_igsn_if_archived(instance)
                soubor_instance.save()
        except DoiWriteError as err:
            logger.error("api.views.SamostatnyNalezFotografieUploadView.post.igsn_error", extra={"error": err})
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            self._release_record_lock(ident_cely, lock_ttl)
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezFotografieUploadView.post.internal_error")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except FedoraError as err:
            logger.error("api.views.SamostatnyNalezFotografieUploadView.post.fedora_error", extra={"error": err})
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            self._release_record_lock(ident_cely, lock_ttl)
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezFotografieUploadView.post.internal_error")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except DatabaseError as err:
            logger.error("api.views.SamostatnyNalezFotografieUploadView.post.database_error", extra={"error": err})
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            self._release_record_lock(ident_cely, lock_ttl)
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezFotografieUploadView.post.internal_error")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as err:
            logger.error("api.views.SamostatnyNalezFotografieUploadView.post.unexpected_error", extra={"error": err})
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            self._release_record_lock(ident_cely, lock_ttl)
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezFotografieUploadView.post.internal_error")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            metadata = FedoraRepositoryConnector(instance, fedora_transaction).get_metadata()
            fedora_transaction.mark_transaction_as_closed()
        except FedoraError as err:
            logger.error(
                "api.views.SamostatnyNalezFotografieUploadView.post.fedora_error_reading_metadata", extra={"error": err}
            )
            if fedora_transaction.status == FedoraTransactionStatus.ACTIVE:
                fedora_transaction.rollback_transaction()
            self._release_record_lock(ident_cely, lock_ttl)
            return self._fail(
                log_entry,
                {"detail": _("api.views.SamostatnyNalezFotografieUploadView.post.fedora_error_reading_metadata")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        self._release_record_lock(ident_cely, lock_ttl)
        return self._success(log_entry, instance, metadata, [], http_status=status.HTTP_201_CREATED)


class MyXMLRenderer(BaseRenderer):
    """Override třídy pro nastavení správnych tagů."""

    media_type = "application/xml"
    format = "xml"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders `data` into serialized XML.

        :param data: Kolekce ``data`` zpracovávaná touto funkcí.
        :param accepted_media_type: Parametr ``accepted_media_type`` slouží jako vstup pro logiku funkce ``render``.
        :param renderer_context: Kolekce ``renderer_context`` zpracovávaná touto funkcí.

            :return: Vrací proměnná ``data``.
        """
        return data


@method_decorator(odstavka_in_progress, name="get")
class GetUserInfo(APIView):
    """Třída pohledu pro získaní základních info o uživately."""

    authentication_classes = [TokenAuthenticationBearer]
    permission_classes = [IsAuthenticated]
    renderer_classes = [
        MyXMLRenderer,
    ]
    http_method_names = [
        "get",
    ]

    def get(self, request, format=None):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` pracuje se s atributy ``user``.
        :param format: Parametr ``format`` slouží jako vstup pro logiku funkce ``get``.

            :return: Vrací výsledek volání ``Response()``.
        """
        user = request.user
        return Response(user.metadata)

    def handle_exception(self, exc):
        """
        Zpracuje exception. v aplikaci.

        :param exc: Číselná hodnota ``exc`` použitá při výpočtu nebo transformaci.

            :return: Vrací výsledek volání ``handle_exception()``.
        """
        self.is_exception = True
        return super().handle_exception(exc)

    def perform_content_negotiation(self, request, force=False):
        """
        Provádí operaci perform content negotiation.

        :param request: Parametr ``request`` předává se do volání ``perform_content_negotiation()``, vstupuje do návratové hodnoty.
        :param force: Parametr ``force`` se předává do volání ``perform_content_negotiation()``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: n-tici, výsledek volání ``perform_content_negotiation()``.
        """
        try:
            self.is_exception
            return JSONRenderer(), JSONRenderer.media_type
        except Exception:
            return super().perform_content_negotiation(request, force)

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Provádí operaci finalize response.

        :param request: Parametr ``request`` předává se do volání ``perform_content_negotiation()``, ``finalize_response()``, pracuje se s atributy ``accepted_renderer``, ``accepted_media_type``, vstupuje do návratové hodnoty.
        :param response: Textový nebo strukturální vstup `response` používaný při sestavení nebo zpracování obsahu.
        :param args: Parametr ``args`` se předává do volání ``finalize_response()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``finalize_response()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``finalize_response()``.
        """
        try:
            self.is_exception
            neg = self.perform_content_negotiation(request, force=True)
            request.accepted_renderer, request.accepted_media_type = neg
        finally:
            return super().finalize_response(request, response, *args, **kwargs)


@method_decorator(odstavka_in_progress, name="post")
class ObtainAuthTokenWithUpdate(ObtainAuthToken):
    """Třída pohledu pro získaní tokenu pro API."""

    def post(self, request, *args, **kwargs):
        """
        Obsluhuje HTTP metodu POST.

        :param request: Parametr ``request`` předává se do volání ``get_serializer()``, pracuje se s atributy ``data``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

            :return: Vrací výsledek volání ``Response()``.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        if not token.created + datetime.timedelta(hours=settings.TOKEN_EXPIRATION_HOURS) > timezone.now():
            try:
                with transaction.atomic():
                    Token.objects.filter(user=user).delete()
                    token = Token.objects.create(user=user)
            except IntegrityError:
                # Pokud mezitím druhý request token vytvořil,
                # jen si ho načteme.
                token = Token.objects.get(user=user)
        return Response({"token": token.key})
