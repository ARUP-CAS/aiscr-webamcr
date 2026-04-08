import base64
import hashlib
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
from core.constants import (
    API_REQUEST_LOG_STATUS_FAILURE,
    API_REQUEST_LOG_STATUS_PROCESSING,
    API_REQUEST_LOG_STATUS_SUCCESS,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_XML_IMPORT,
    ODESLANI_SN,
    POTVRZENI_SN,
    SN_ZAPSANY,
    ZAPSANI_SN,
)
from core.ident_cely import get_sn_ident
from core.models import ApiRequestLog, Permissions, check_permissions
from core.repository_connector import FedoraRepositoryConnector, FedoraTransaction
from core.setting_models import CustomAdminSettings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l
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
from projekt.models import Projekt
from rest_framework import serializers, status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import BaseThrottle
from rest_framework.views import APIView
from uzivatel.models import Organizace, Osoba
from uzivatel.views import TokenAuthenticationBearer
from xml_generator.generator import AMCR_NAMESPACE_URL, AMCR_XSD_URL

from .models import SamostatnyNalez

logger = logging.getLogger(__name__)

_CACHE_KEY_ACCESS_RULES = "pas_api_access_rules"
_CACHE_KEY_RATE_LIMITS = "pas_api_rate_limits"
_CACHE_KEY_ACCESS_MODE = "pas_api_access_mode"
_CACHE_KEY_TRUSTED_PROXIES = "pas_api_trusted_proxies"
_CACHE_TTL = 30  # sekund

_PAS_API_GROUP = "pas_api"
_ACCESS_RULES_ID = "access_rules"
_RATE_LIMITS_ID = "rate_limits"
_ACCESS_MODE_ID = "access_mode"
# codeql[py/clear-text-logging-sensitive-data]
_TRUSTED_PROXIES_ID = "trusted_proxies"
_AMCR_SCHEMA_LOCK = threading.Lock()
_AMCR_SCHEMA_FETCH_TIMEOUT = 10
_AMCR_SCHEMA_CACHE_TTL = 3600  # sekund — schéma se znovu načte po 60 minutách
_ALLOWED_SCHEMA_URL_PATTERNS = (
    re.compile(r"^https?://www\.w3\.org/2001/XMLSchema-instance(?:[?#].*)?$"),
    re.compile(r"^https?://www\.w3\.org/2001/(?:03/)?xml\.xsd(?:[?#].*)?$"),
    re.compile(r"^https://api\.aiscr\.cz/schema/amcr/\d+\.\d+/.*$"),
    re.compile(r"^http://www\.opengis\.net/gml/.*$"),
)


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
ACCESS_MODE_OPEN = "open"
ACCESS_MODE_WHITELIST_ONLY = "whitelist_only"
ACCESS_MODE_CLOSED = "closed"
_ACCESS_MODES = {ACCESS_MODE_OPEN, ACCESS_MODE_WHITELIST_ONLY, ACCESS_MODE_CLOSED}
_PAS_API_ITEM_IDS = {_ACCESS_RULES_ID, _RATE_LIMITS_ID, _ACCESS_MODE_ID, _TRUSTED_PROXIES_ID}

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
                logger.warning("pas.api.PasApiPermissionMixin._resolve_trusted_networks.dns_failed")

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
            - ``active`` *(volitelný, výchozí* ``true``*)* — ``false`` pravidlo dočasně deaktivuje

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
              jednotky: ``s`` (sekunda), ``m`` (minuta), ``h`` (hodina), ``d`` (den);
              např. ``"10/m"``, ``"100/h"``, ``"1000/d"``
            - ``active`` *(volitelný, výchozí* ``true``*)* — ``false`` limit dočasně deaktivuje

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

        Změny v administraci se projeví do ``30`` sekund (TTL cache).

        :param item_id: Identifikátor záznamu — ``"access_rules"``, ``"rate_limits"`` nebo ``"access_mode"``.

        :param raise_validation_error: Pokud je ``True`` (výchozí), nevalidní JSON vyhodí ``ValidationError``.

        :return: Naparsovaná JSON hodnota nebo ``[]`` při chybě či absenci záznamu.
        """
        try:
            obj = CustomAdminSettings.objects.get(item_group=_PAS_API_GROUP, item_id=item_id)
            return json.loads(obj.value)
        except CustomAdminSettings.DoesNotExist:
            return []
        except (json.JSONDecodeError, TypeError):
            logger.error("pas.api._load_json_setting.invalid_json")
            if raise_validation_error:
                # item_id in the validation message is likewise intentional:
                # it identifies which PAS admin setting is malformed and helps
                # troubleshooting or incident-response review. It is not
                # sensitive data.
                # codeql[py/error-message-exposure]
                raise ValidationError(
                    {"value": _("pas.api.PasApiPermissionMixin.load_json_setting.invalid_json").format(item_id=item_id)}
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
            cache.set(_CACHE_KEY_ACCESS_RULES, rules, _CACHE_TTL)
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
            raise ValidationError({"value": _("pas.api.PasApiPermissionMixin.validate_access_rules.not_a_list")})

        for index, rule in enumerate(raw_rules):
            if not isinstance(rule, dict):
                raise ValidationError(
                    {
                        "value": _("pas.api.PasApiPermissionMixin.validate_access_rules.item_not_a_dict").format(
                            index=index
                        )
                    }
                )
            if "rule_type" not in rule or "value" not in rule:
                raise ValidationError(
                    {
                        "value": _("pas.api.PasApiPermissionMixin.validate_access_rules.missing_required_keys").format(
                            index=index
                        )
                    }
                )
            if rule.get("active") is not None and not isinstance(rule.get("active"), bool):
                raise ValidationError(
                    {
                        "value": _("pas.api.PasApiPermissionMixin.validate_access_rules.invalid_active").format(
                            index=index
                        )
                    }
                )
            if rule["rule_type"] not in _ACCESS_RULE_TYPES:
                raise ValidationError(
                    {
                        "value": _("pas.api.PasApiPermissionMixin.validate_access_rules.unsupported_rule_type").format(
                            index=index, rule_type=rule["rule_type"]
                        )
                    }
                )
            if rule["rule_type"] in {TYPE_IP_BLACKLIST, TYPE_IP_WHITELIST}:
                if not isinstance(rule["value"], str) or not _is_valid_ip_rule_value(rule["value"]):
                    raise ValidationError(
                        {
                            "value": _("pas.api.PasApiPermissionMixin.validate_access_rules.invalid_ip_value").format(
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
        validuje JSON hodnotu příslušným validátorem.

        :param instance: Ukládaný záznam ``CustomAdminSettings``.

        :raises ValidationError: Pokud ``item_id`` není podporováno nebo JSON/struktura hodnoty nejsou validní.
        :return: ``True`` pokud je záznam validní nebo se na něj validace nevztahuje.
        """
        if instance.item_group != _PAS_API_GROUP:
            return True
        if instance.item_id not in _PAS_API_ITEM_IDS:
            raise ValidationError(
                {
                    "item_id": _("pas.api.PasApiPermissionMixin.validate_custom_admin_setting.invalid_item_id").format(
                        item_group=instance.item_group, item_id=instance.item_id
                    )
                }
            )
        try:
            raw_value = json.loads(instance.value)
        except (json.JSONDecodeError, TypeError):
            raise ValidationError(
                {
                    "value": _("pas.api.PasApiPermissionMixin.validate_custom_admin_setting.invalid_json").format(
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
        return True

    @classmethod
    def get_rate_limits(cls) -> list[dict]:
        """
        Vrátí limity počtu požadavků z cache nebo ``CustomAdminSettings``.

        Každý limit je slovník s klíči ``scope``, ``value``, ``rate`` a volitelně ``active`` (výchozí ``True``).

        :raises ValidationError: Pokud nastavení nemá očekávanou strukturu nebo obsahuje nevalidní limit.
        :return: Seznam aktivních limitů.
        """
        limits = cache.get(_CACHE_KEY_RATE_LIMITS)
        if limits is None:
            raw_limits = cls.load_json_setting(_RATE_LIMITS_ID)
            cls.validate_rate_limits(raw_limits)
            limits = [r for r in raw_limits if r.get("active", True)]
            cache.set(_CACHE_KEY_RATE_LIMITS, limits, _CACHE_TTL)
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
            raise ValidationError({"value": _("pas.api.PasApiPermissionMixin.validate_rate_limits.not_a_list")})

        for index, limit in enumerate(raw_limits):
            if not isinstance(limit, dict):
                raise ValidationError(
                    {
                        "value": _("pas.api.PasApiPermissionMixin.validate_rate_limits.item_not_a_dict").format(
                            index=index
                        )
                    }
                )
            if "scope" not in limit or "value" not in limit or "rate" not in limit:
                raise ValidationError(
                    {
                        "value": _("pas.api.PasApiPermissionMixin.validate_rate_limits.missing_required_keys").format(
                            index=index
                        )
                    }
                )
            if limit.get("active") is not None and not isinstance(limit.get("active"), bool):
                raise ValidationError(
                    {
                        "value": _("pas.api.PasApiPermissionMixin.validate_rate_limits.invalid_active").format(
                            index=index
                        )
                    }
                )
            if limit["scope"] not in {SCOPE_USER, SCOPE_IP}:
                raise ValidationError(
                    {
                        "value": _("pas.api.PasApiPermissionMixin.validate_rate_limits.unsupported_scope").format(
                            index=index, scope=limit["scope"]
                        )
                    }
                )
            if limit["scope"] == SCOPE_IP:
                if not isinstance(limit["value"], str) or not _is_valid_ip_rule_value(limit["value"]):
                    raise ValidationError(
                        {
                            "value": _("pas.api.PasApiPermissionMixin.validate_rate_limits.invalid_ip_value").format(
                                index=index, value=limit["value"]
                            )
                        }
                    )
            if _parse_rate(limit["rate"]) is None:
                raise ValidationError(
                    {
                        "value": _("pas.api.PasApiPermissionMixin.validate_rate_limits.invalid_rate").format(
                            index=index, rate=limit["rate"]
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
            cache.set(_CACHE_KEY_ACCESS_MODE, access_mode, _CACHE_TTL)
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
                {"value": _("pas.api.PasApiPermissionMixin.validate_access_mode.invalid_value").format(value=value)}
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
            cache.set(_CACHE_KEY_TRUSTED_PROXIES, proxies, _CACHE_TTL)
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
            raise ValidationError({"value": _("pas.api.PasApiPermissionMixin.validate_trusted_proxies.not_a_list")})
        for index, entry in enumerate(raw_proxies):
            if not isinstance(entry, str) or not entry.strip():
                raise ValidationError(
                    {
                        "value": _("pas.api.PasApiPermissionMixin.validate_trusted_proxies.invalid_entry").format(
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
                            "value": _("pas.api.PasApiPermissionMixin.validate_trusted_proxies.invalid_cidr").format(
                                index=index, value=stripped
                            )
                        }
                    )
        return True

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
                    "pas.api.IpBlacklistPermission.denied",
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
            "pas.api.IpWhitelistPermission.denied",
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
                    "pas.api.UserBlacklistPermission.denied",
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
            "pas.api.UserWhitelistPermission.denied",
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
            self.message = _("pas.api.ApiAccessModePermission.closed")
            logger.warning("pas.api.ApiAccessModePermission.closed")
            return False

        rules = self.get_access_rules()
        has_whitelist = any(rule["rule_type"] in {TYPE_IP_WHITELIST, TYPE_USER_WHITELIST} for rule in rules)
        if has_whitelist:
            return True

        self.message = _("pas.api.ApiAccessModePermission.whitelist_only_without_rules")
        logger.warning("pas.api.ApiAccessModePermission.whitelist_only_without_rules")
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


def _parse_rate(rate: str) -> tuple[int, int] | None:
    """
    Naparsuje řetězec limitu ve formátu ``počet/jednotka`` na počet a délku okna v sekundách.

    Podporované jednotky: ``s`` (sekunda), ``m`` (minuta), ``h`` (hodina), ``d`` (den).

    :param rate: Řetězec ve formátu ``10/m``, ``100/h`` apod.

    :return: Dvojice ``(počet, okno_v_sekundách)`` nebo ``None`` při chybě parsování.
    """
    try:
        count_str, period = rate.split("/")
        count = int(count_str)
        periods = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        window = periods.get(period.strip().lower())
        if window is None:
            return None
        return count, window
    except (ValueError, AttributeError):
        return None


class ApiImportThrottle(PasApiPermissionMixin, BaseThrottle):
    """
    Throttle pro API import samostatného nálezu řízený záznamy ``CustomAdminSettings`` (``pas_api/rate_limits``).

    Pravidla jsou načítána z databáze (s cache) a aplikována v pořadí:
    nejdříve pravidlo pro konkrétního uživatele, pak pro IP adresu.
    Pokud žádné pravidlo neexistuje, požadavek je povolen.
    """

    def allow_request(self, request, view=None) -> bool:
        """
        Rozhodne, zda je požadavek povolen na základě nakonfigurovaných limitů.

        :param request: HTTP požadavek.
        :param view: Pohled zpracovávající požadavek.

        :return: ``True`` pokud limit nebyl překročen nebo neexistuje, jinak ``False``.
        """
        limits = self.get_rate_limits()
        client_ip = self.get_client_ip(request)
        user_identifier = self.get_user_identifier(request.user)

        for limit in limits:
            if limit["scope"] == SCOPE_USER and limit["value"] == user_identifier:
                return self._check_limit(f"throttle_user_{user_identifier}", limit["rate"], request)
            if limit["scope"] == SCOPE_IP and self.ip_matches(client_ip, limit["value"]):
                return self._check_limit(f"throttle_ip_{client_ip}", limit["rate"], request)
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
            logger.error("pas.api.ApiImportThrottle.invalid_rate", extra={"rate": rate})
            return True
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
            self.wait_seconds = max(window - (now - float(window_started)), 1)
            logger.warning(
                "pas.api.ApiImportThrottle.throttled",
                extra={"cache_key": cache_key, "rate": rate},
            )
            return False
        self.wait_seconds = None
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
    SAVED_PROVIDED_MISMATCH = 4


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


class SamostatnyNalezXmlImportView(PasApiPermissionMixin, APIView):
    """Pohled pro import záznamu samostatného nálezu z XML souboru přes POST požadavek."""

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
    http_method_names = ["post"]

    _AMCR_NS = "https://api.aiscr.cz/schema/amcr/2.2/"
    _XML_NS = "http://www.w3.org/XML/1998/namespace"
    _XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
    _IMPORT_HISTORY_NOTE = _l("pas.api.SamostatnyNalezXmlImportView.import_history_note")
    _amcr_schema_cache: dict[str, tuple[etree.XMLSchema, float]] = {}  # url -> (schema, inserted_at)

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
            logger.warning("pas.api.SamostatnyNalezXmlImportView.dispatch.closed")
            return JsonResponse(
                {"detail": _("pas.api.ApiAccessModePermission.closed")},
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

    @staticmethod
    def _success(
        log_entry: "ApiRequestLog", instance: "SamostatnyNalez", metadata: bytes, notes: list[str]
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
            "pas.api.SamostatnyNalezXmlImportView.post.created",
            extra={"ident_cely": instance.ident_cely, "user": user_pk},
        )
        if notes:
            # ident_cely, ignored xml:lang notes, and user_pk are logged
            # intentionally to support import diagnostics, troubleshooting, and
            # incident investigation. They are operational context, not secrets.
            # codeql[py/clear-text-logging-sensitive-data]
            logger.info(
                "pas.api.SamostatnyNalezXmlImportView.post.ignored_lang_notes",
                extra={"ident_cely": instance.ident_cely, "notes": notes, "user": user_pk},
            )
        return HttpResponse(metadata, content_type="application/xml", status=200)

    def post(self, request, format=None):
        """
        Importuje nový záznam samostatného nálezu z XML souboru.

        Přijímá soubor v parametru ``file`` (multipart/form-data). XML musí odpovídat
        schématu AMČR 2.2 (https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd).
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
                {"detail": _("pas.api.SamostatnyNalezXmlImportView.post.missing_file")},
                status.HTTP_400_BAD_REQUEST,
            )

        digest_error = self._verify_content_digest(request, xml_file)
        if digest_error:
            return self._fail(log_entry, {"detail": digest_error}, status.HTTP_400_BAD_REQUEST)
        xml_file.seek(0)

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
                "pas.api.SamostatnyNalezXmlImportView.post.xml_syntax_error",
                extra={"error": str(exc), "user": request.user.pk},
            )
            return self._fail(
                log_entry,
                {"detail": _("pas.api.SamostatnyNalezXmlImportView.post.invalid_xml_syntax")},
                status.HTTP_400_BAD_REQUEST,
            )

        version_error = self._validate_declared_schema_version(doc)
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

        validation_doc = self._build_schema_validation_doc(doc)
        if not schema.validate(validation_doc):
            errors = [
                ImportValidationIssue(
                    line=e.line,
                    column=e.column,
                    message=_("pas.api.SamostatnyNalezXmlImportView.post.schema_error_item")
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
                "pas.api.SamostatnyNalezXmlImportView.post.schema_invalid",
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
                {"detail": _("pas.api.SamostatnyNalezXmlImportView.post.missing_samostatny_nalez")},
                status.HTTP_400_BAD_REQUEST,
            )
        if len(nalez_elements) > 1:
            return self._fail(
                log_entry,
                {"detail": _("pas.api.SamostatnyNalezXmlImportView.post.multiple_samostatny_nalez")},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if len(root_children) != 1 or not nalez_elements:
            return self._fail(
                log_entry,
                {"detail": _("pas.api.SamostatnyNalezXmlImportView.post.invalid_root_content")},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # XML je validní a obsahuje právě jeden záznam — přepneme stav na PROCESSING.
        log_entry.status = API_REQUEST_LOG_STATUS_PROCESSING
        log_entry.save(update_fields=["status"])

        elem = nalez_elements[0]
        notes = self._get_ignored_lang_notes(elem)
        try:
            self._validate_disallowed_elements(elem)
            data, nova_osoba = self._parse_nalez_element(elem, request.user)
        except ImportValidationException as exc:
            return self._fail(
                log_entry,
                {"validation_errors": [e.to_dict() for e in exc.import_errors]},
                self._validation_status(exc.import_errors),
            )

        if not self._has_import_permissions(request.user, data):
            # The denied user ID and referenced project are logged intentionally
            # for authorization troubleshooting and incident investigation.
            # They are audit/operational identifiers, not secrets.
            # codeql[py/clear-text-logging-sensitive-data]
            logger.warning(
                "pas.api.SamostatnyNalezXmlImportView.post.permission_denied",
                extra={"user": request.user.pk, "projekt": data.get("projekt")},
            )
            return self._fail(
                log_entry,
                {"detail": _("pas.api.SamostatnyNalezXmlImportView.post.permission_denied")},
                status.HTTP_403_FORBIDDEN,
            )

        validation_error: tuple[dict, int] | None = None
        instance = None
        with transaction.atomic():
            fedora_transaction = FedoraTransaction(transaction_user=request.user)
            serializer_data = dict(data)
            if nova_osoba is not None:
                nova_osoba.active_transaction = fedora_transaction
                nova_osoba.save()  # Osoba must be saved to get ident_cely before the serializer validation
                serializer_data["nalezce"] = nova_osoba.ident_cely

            try:
                serializer = SamostatnyNalezXmlImportSerializer(data=serializer_data)
                if not serializer.is_valid():
                    raise ImportValidationException.from_serializer_errors(serializer.errors, line=elem.sourceline)
                self._validate_heslar_value_matches(serializer.validated_data, elem)
            except ImportValidationException as exc:
                # Store the error and mark the transaction for rollback. _fail() must be called
                # outside the atomic() block — set_rollback(True) prevents any further DB queries.
                validation_error = (
                    {"validation_errors": [e.to_dict() for e in exc.import_errors]},
                    self._validation_status(exc.import_errors),
                )
                transaction.set_rollback(True)

            if validation_error is None:
                if (
                    serializer.validated_data.get("ident_cely")
                    and SamostatnyNalez.objects.filter(ident_cely=serializer.validated_data["ident_cely"]).exists()
                ):
                    validation_error = (
                        {
                            "validation_errors": [
                                ImportValidationIssue(
                                    line=elem.sourceline,
                                    column=None,
                                    message="ident_cely: "
                                    + _("pas.api.SamostatnyNalezXmlImportView.post.ident_cely_already_exists"),
                                    error_type=ImportErrorType.INVALID_DATA,
                                ).to_dict()
                            ]
                        },
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                    )
                    transaction.set_rollback(True)

            if validation_error is None:
                instance = SamostatnyNalez(**serializer.validated_data)
                if not instance.ident_cely:
                    instance.ident_cely = get_sn_ident(instance.projekt)
                instance.active_transaction = fedora_transaction
                instance.save()
                self._create_import_history_records(instance, request.user)

        if validation_error is not None:
            return self._fail(log_entry, *validation_error)
        if instance is None:
            return self._fail(
                log_entry,
                {"detail": _("pas.api.SamostatnyNalezXmlImportView.post.invalid_data")},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        fedora_transaction.mark_transaction_as_closed()

        metadata = FedoraRepositoryConnector(instance).get_metadata(update=False)

        return self._success(log_entry, instance, metadata, notes)

    @staticmethod
    def _has_import_permissions(user, data: dict) -> bool:
        """
        Ověří oprávnění potřebná pro import samostatného nálezu.

        :param user: Uživatel provádějící import.
        :param data: Data jednoho importovaného záznamu.

        :return: Vrací ``True`` pokud má uživatel všechna vyžadovaná oprávnění.
        """
        if not check_permissions(Permissions.actionChoices.pas_edit, user):
            return False

        if not check_permissions(Permissions.actionChoices.pas_ulozeni_edit, user):
            return False

        projekt_ident = data.get("projekt")
        if projekt_ident and not check_permissions(
            Permissions.actionChoices.pas_zapsat_do_projektu, user, projekt_ident
        ):
            return False

        return True

    @classmethod
    def _create_import_history_records(cls, instance: SamostatnyNalez, user) -> None:
        """
        Vytvoří historii pro importovaný záznam samostatného nálezu.

        :param instance: Vytvořený záznam samostatného nálezu.
        :param user: Uživatel, který provedl import.
        """
        Historie.objects.bulk_create(
            [
                Historie(
                    typ_zmeny=ZAPSANI_SN,
                    uzivatel=user,
                    vazba=instance.historie,
                    poznamka=cls._IMPORT_HISTORY_NOTE,
                ),
                Historie(
                    typ_zmeny=ODESLANI_SN,
                    uzivatel=user,
                    vazba=instance.historie,
                    poznamka=cls._IMPORT_HISTORY_NOTE,
                ),
                Historie(
                    typ_zmeny=POTVRZENI_SN,
                    uzivatel=user,
                    vazba=instance.historie,
                    poznamka=cls._IMPORT_HISTORY_NOTE,
                ),
            ]
        )

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
    def _validate_disallowed_elements(cls, elem: etree._Element) -> None:
        """
        Ověří, že importovaný element neobsahuje nepovolené podřízené elementy.

        :param elem: Importovaný element ``amcr:samostatny_nalez``.

        :raises ImportValidationException: Pokud je nalezen nepovolený element.
        """
        stav_elem = elem.find(cls._ns("stav"))
        if stav_elem is not None:
            raise ImportValidationException(
                ImportValidationIssue(
                    line=stav_elem.sourceline,
                    column=None,
                    message="stav: " + _("pas.api.SamostatnyNalezXmlImportView.post.stav_element_not_allowed"),
                    error_type=ImportErrorType.INVALID_DATA,
                )
            )

    @classmethod
    def _build_schema_validation_doc(cls, doc: etree._ElementTree) -> etree._ElementTree:
        """
        Vytvoří kopii dokumentu upravenou pro validaci proti XSD schématu.

        Importní API nepovoluje element ``stav``, ale XSD jej vyžaduje.
        Pro validaci proto doplní chybějící ``stav`` do kopie dokumentu.

        :param doc: Původní XML dokument.

        :return: Kopie XML dokumentu určená pro schema validaci.
        """

        parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
        validation_doc = etree.ElementTree(etree.fromstring(etree.tostring(doc.getroot()), parser=parser))
        for elem in validation_doc.findall(f".//{cls._ns('samostatny_nalez')}"):
            if elem.find(cls._ns("stav")) is not None:
                continue

            stav_elem = etree.Element(cls._ns("stav"))
            stav_elem.text = str(SN_ZAPSANY)
            insert_before_tags = (
                "predano",
                "predano_organizace",
                "geom_system",
                "pristupnost",
                "chranene_udaje",
                "historie",
                "soubor",
            )
            insert_index = len(elem)
            for index, child in enumerate(elem):
                if _strip_namespace(child.tag) in insert_before_tags:
                    insert_index = index
                    break
            elem.insert(insert_index, stav_elem)

        return validation_doc

    @classmethod
    def _validate_heslar_value_matches(cls, validated_data: dict, elem: etree._Element) -> None:
        """
        Ověří shodu textové hodnoty XML a ``heslo`` na navázaném hesláři.

        :param validated_data: Validovaná data serializeru.
        :param elem: Importovaný XML element.

        :raises ImportValidationException: Pokud text elementu neodpovídá ``heslo``.
        """
        heslar_fields = ("okolnosti", "obdobi", "druh_nalezu", "specifikace")
        errors = []
        for field_name in heslar_fields:
            field_elem = elem.find(cls._ns(field_name))
            provided_value = cls._text(elem, field_name)
            validated_heslar = validated_data.get(field_name)
            if provided_value and validated_heslar and provided_value != validated_heslar.heslo:
                errors.append(
                    ImportValidationIssue(
                        line=field_elem.sourceline if field_elem is not None else elem.sourceline,
                        column=None,
                        message=f"{field_name}: "
                        + _(
                            "pas.api.SamostatnyNalezXmlImportView._validate_heslar_value_matches.saved_provided_mismatch"
                        )
                        % {
                            "provided": provided_value,
                            "saved": validated_heslar.heslo,
                        },
                        error_type=ImportErrorType.SAVED_PROVIDED_MISMATCH,
                    )
                )
        if errors:
            raise ImportValidationException(errors)

    @staticmethod
    def _verify_content_digest(request, xml_file) -> str | None:
        """
        Ověří integritu souboru pomocí hlavičky ``Content-Digest`` (RFC 9530).

        Očekávaný formát hlavičky: ``sha-512=:<base64>:``
        Pokud hlavička chybí nebo neodpovídá skutečnému SHA-512 obsahu souboru,
        vrátí chybovou zprávu.

        :param request: HTTP požadavek obsahující hlavičku ``Content-Digest``.
        :param xml_file: Nahraný soubor; po zavolání je pozice čtení na začátku.

        :return: Chybová zpráva jako řetězec, nebo None pokud je digest v pořádku.
        """
        header = request.headers.get("Content-Digest")
        if not header:
            return _("pas.api.SamostatnyNalezXmlImportView._verify_content_digest.missing_digest")

        prefix = "sha-512=:"
        if not header.startswith(prefix) or not header.endswith(":"):
            return _("pas.api.SamostatnyNalezXmlImportView._verify_content_digest.invalid_format")

        try:
            expected = base64.b64decode(header[len(prefix) : -1])
        except (ValueError, TypeError):
            return _("pas.api.SamostatnyNalezXmlImportView._verify_content_digest.invalid_base64")

        actual = hashlib.sha512(xml_file.read()).digest()
        if actual != expected:
            return _("pas.api.SamostatnyNalezXmlImportView._verify_content_digest.digest_mismatch")

        return None

    @classmethod
    def _validate_declared_schema_version(cls, doc: etree._ElementTree) -> str | None:
        """
        Ověří, že XML deklaruje podporovanou verzi AMČR schématu.

        :param doc: Naparsovaný XML dokument.

        :return: Chybová zpráva nebo ``None``, pokud deklarace odpovídá podporované verzi.
        """
        root = doc.getroot()
        amcr_namespace = root.nsmap.get("amcr")
        if amcr_namespace != AMCR_NAMESPACE_URL:
            return _("pas.api.SamostatnyNalezXmlImportView._validate_declared_schema_version.unsupported_namespace")

        schema_location = root.get(f"{{{cls._XSI_NS}}}schemaLocation")
        if not schema_location:
            return _("pas.api.SamostatnyNalezXmlImportView._validate_declared_schema_version.missing_schema_location")

        schema_parts = schema_location.split()
        if len(schema_parts) % 2 != 0:
            return _("pas.api.SamostatnyNalezXmlImportView._validate_declared_schema_version.invalid_schema_location")

        schema_mapping = dict(zip(schema_parts[0::2], schema_parts[1::2]))
        declared_amcr_xsd = schema_mapping.get(amcr_namespace)
        if declared_amcr_xsd != AMCR_XSD_URL:
            return _(
                "pas.api.SamostatnyNalezXmlImportView._validate_declared_schema_version.unsupported_schema_location"
            )

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
        cached = cls._amcr_schema_cache.get(schema_url)
        if cached is not None and now - cached[1] < _AMCR_SCHEMA_CACHE_TTL:
            return cached[0]

        with _AMCR_SCHEMA_LOCK:
            cached = cls._amcr_schema_cache.get(schema_url)
            if cached is not None and time.time() - cached[1] < _AMCR_SCHEMA_CACHE_TTL:
                return cached[0]

            class _LocalResolver(etree.Resolver):
                """Resolver nahrazující vzdálené W3C URL lokálním souborem xml.xsd."""

                def __init__(self):
                    super().__init__()
                    self.blocked_exception: ImportValidationException | None = None

                def resolve(self, url, id, context):
                    """
                    Přeloží URL na lokální cestu pro xml.xsd.

                    :param url: URL požadovaného zdroje.
                    :param id: Identifikátor kontextu parseru.
                    :param context: Kontext resolveru.

                    :return: Vrací lokální soubor pro xml.xsd, jinak None.
                    """
                    allowed_urls = (
                        "http://www.w3.org/2001/xml.xsd",
                        "https://www.w3.org/2001/xml.xsd",
                        "http://www.w3.org/2001/03/xml.xsd",
                        "https://www.w3.org/2001/03/xml.xsd",
                    )
                    if url in allowed_urls:
                        return self.resolve_filename("xml_generator/definitions/xml.xsd", context)
                    if any(pattern.match(url) for pattern in _ALLOWED_SCHEMA_URL_PATTERNS):
                        try:
                            response = urllib.request.urlopen(url, timeout=_AMCR_SCHEMA_FETCH_TIMEOUT)  # noqa: S310
                        except (urllib.error.URLError, TimeoutError) as exc:
                            logger.error("Nepodařilo se načíst XSD schéma z URL %s: %s", url, exc)
                            self.blocked_exception = ImportValidationException(
                                ImportValidationIssue(
                                    line=None,
                                    column=None,
                                    message=_(
                                        "pas.api.SamostatnyNalezXmlImportView._get_amcr_schema.schema_not_available"
                                    )
                                    % {"url": url},
                                    error_type=ImportErrorType.INVALID_DATA,
                                )
                            )
                            self.blocked_exception.__cause__ = exc
                            return None
                        return self.resolve_file(response, context, base_url=url)
                    # Disallowed URL — store the exception for re-raising after XMLSchema()
                    # because lxml swallows Python exceptions raised inside resolver callbacks.
                    self.blocked_exception = ImportValidationException(
                        ImportValidationIssue(
                            line=None,
                            column=None,
                            message=_("pas.api.SamostatnyNalezXmlImportView._get_amcr_schema.disallowed_schema_url")
                            % {"url": url},
                            error_type=ImportErrorType.INVALID_DATA,
                        )
                    )
                    return None

            parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
            resolver = _LocalResolver()
            parser.resolvers.add(resolver)
            try:
                response = urllib.request.urlopen(schema_url, timeout=_AMCR_SCHEMA_FETCH_TIMEOUT)  # noqa: S310
            except (urllib.error.URLError, TimeoutError) as exc:
                logger.error("Nepodařilo se načíst XSD schéma z URL %s: %s", schema_url, exc)
                raise ImportValidationException(
                    ImportValidationIssue(
                        line=None,
                        column=None,
                        message=_("pas.api.SamostatnyNalezXmlImportView._get_amcr_schema.schema_not_available")
                        % {"url": schema_url},
                        error_type=ImportErrorType.INVALID_DATA,
                    )
                ) from exc
            with response:
                schema_doc = etree.parse(response, parser)
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
                    message=_("pas.api.SamostatnyNalezXmlImportView._get_amcr_schema.disallowed_schema_url")
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
                    _("pas.api.SamostatnyNalezXmlImportView.post.ignored_lang_attribute")
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

    @classmethod
    def _parse_nalezce(cls, elem: etree._Element, user) -> tuple[str | None, Osoba | None]:
        """
        Zpracuje element ``nalezce`` a vrátí ``ident_cely`` osoby pro import.

        Pokud má element atribut ``id=":tba"``, vytvoří se nová osoba z textu
        ve formátu ``"Příjmení, Jméno"``. Nová osoba se zde pouze připraví,
        ale uloží se až v transakci společně s ``SamostatnyNalez``.

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
                message = _("pas.api.SamostatnyNalezXmlImportView._parse_nalezce.incorrect_format_missing_separator")
            elif len(casti) < 2 or not casti[0]:
                message = _("pas.api.SamostatnyNalezXmlImportView._parse_nalezce.incorrect_format_missing_surname")
            elif not casti[1]:
                message = _("pas.api.SamostatnyNalezXmlImportView._parse_nalezce.incorrect_format_missing_name")
            else:
                message = _("pas.api.SamostatnyNalezXmlImportView._parse_nalezce.incorrect_format")
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

        if not check_permissions(Permissions.actionChoices.model_edit, user):
            raise ImportValidationException(
                ImportValidationIssue(
                    line=nalezce_elem.sourceline if nalezce_elem is not None else elem.sourceline,
                    column=None,
                    message="nalezce: "
                    + _("pas.api.SamostatnyNalezXmlImportView._parse_nalezce.missing_edit_osoba_permission"),
                    error_type=ImportErrorType.PERMISSION_ERROR,
                )
            )

        prijmeni, jmeno = casti
        jmeno = " ".join(jmeno.split())
        osoba = Osoba(
            prijmeni=prijmeni,
            jmeno=jmeno,
            vypis=build_osoba_vypis(prijmeni, jmeno),
            vypis_cely=f"{prijmeni}, {jmeno}",
        )
        return None, osoba

    @classmethod
    def _parse_nalez_element(cls, elem: etree._Element, user) -> tuple[dict, Osoba | None]:
        """
        Převede element ``amcr:samostatny_nalez`` na slovník pro deserializaci.

        Elementy typu ``refType`` a ``vocabType`` se mapují pomocí atributu ``id``,
        který nese ``ident_cely`` odkazovaného záznamu. Geometrie jsou předány
        jako WKT řetězce z elementů ``geom_wkt`` a ``geom_sjtsk_wkt``.

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
                    + _("pas.api.SamostatnyNalezXmlImportView._parse_nalez_element.missing_projekt"),
                    error_type=ImportErrorType.INVALID_DATA,
                )
            )

        def parse_ruian_katastr_kod(katastr_elem: etree._Element | None) -> int | None:
            """
            Převede atribut ``id`` ve formátu ``ruian-{kod}`` na číselný kód katastru.

            :param katastr_elem: XML element ``katastr``.

            :return: Kód katastru nebo ``None``, pokud element neexistuje.

            :raises ImportValidationException: Pokud je atribut ``id`` v nevalidním formátu.
            """
            if katastr_elem is None:
                return None

            katastr_id = katastr_elem.get("id")
            if not katastr_id:
                return None
            if not katastr_id.startswith("ruian-"):
                raise ImportValidationException(
                    ImportValidationIssue(
                        line=katastr_elem.sourceline,
                        column=None,
                        message=f"katastr: {_('pas.api.SamostatnyNalezXmlImportView._parse_nalez_element.invalid_katastr_id')}",
                        error_type=ImportErrorType.INVALID_DATA,
                    )
                )

            try:
                return int(katastr_id.split("-", 1)[1])
            except (IndexError, ValueError):
                raise ImportValidationException(
                    ImportValidationIssue(
                        line=katastr_elem.sourceline,
                        column=None,
                        message=f"katastr: {_('pas.api.SamostatnyNalezXmlImportView._parse_nalez_element.invalid_katastr_id')}",
                        error_type=ImportErrorType.INVALID_DATA,
                    )
                )

        data = {
            "ident_cely": None if cls._text(elem, "ident_cely") == ":tba" else cls._text(elem, "ident_cely"),
            "projekt": projekt_ident,
            "evidencni_cislo": cls._text(elem, "evidencni_cislo"),
            "igsn": cls._text(elem, "igsn"),
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
            "stav": SN_ZAPSANY,
            "predano": cls._parse_bool(cls._text(elem, "predano")),
            "predano_organizace": cls._id_attr(elem, "predano_organizace"),
            "geom_system": cls._text(elem, "geom_system"),
            "pristupnost": cls._id_attr(elem, "pristupnost"),
        }

        if chranene is not None:
            data["katastr"] = parse_ruian_katastr_kod(chranene.find(cls._ns("katastr")))
            data["lokalizace"] = cls._text(chranene, "lokalizace")
            geom_wkt_elem = chranene.find(cls._ns("geom_wkt"))
            if geom_wkt_elem is not None and geom_wkt_elem.text:
                data["geom"] = geom_wkt_elem.text.strip()
            geom_sjtsk_elem = chranene.find(cls._ns("geom_sjtsk_wkt"))
            if geom_sjtsk_elem is not None and geom_sjtsk_elem.text:
                data["geom_sjtsk"] = geom_sjtsk_elem.text.strip()

        return {k: v for k, v in data.items() if v is not None}, nova_osoba
