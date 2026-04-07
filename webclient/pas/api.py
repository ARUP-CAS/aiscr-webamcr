import base64
import hashlib
import ipaddress
import json
import logging
import time
from dataclasses import asdict, dataclass
from enum import Enum

from core.constants import ODESLANI_SN, POTVRZENI_SN, SN_ZAPSANY, ZAPSANI_SN
from core.ident_cely import get_sn_ident
from core.models import Permissions, check_permissions
from core.repository_connector import FedoraRepositoryConnector, FedoraTransaction
from core.setting_models import CustomAdminSettings
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.http import HttpResponse
from django.utils.translation import gettext as _
from heslar.hesla import (
    HESLAR_NALEZOVE_OKOLNOSTI,
    HESLAR_OBDOBI,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_SPECIFIKACE,
    HESLAR_PRISTUPNOST,
)
from heslar.models import Heslar, RuianKatastr
from historie.models import Historie
from lxml import etree
from projekt.models import Projekt
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import BaseThrottle
from rest_framework.views import APIView
from uzivatel.models import Organizace, Osoba
from uzivatel.views import TokenAuthenticationBearer
from xml_generator.generator import AMCR_NAMESPACE_URL, AMCR_XSD_URL, DocumentGenerator

from .models import SamostatnyNalez

logger = logging.getLogger(__name__)

_CACHE_KEY_ACCESS_RULES = "pas_api_access_rules"
_CACHE_KEY_RATE_LIMITS = "pas_api_rate_limits"
_CACHE_TTL = 30  # sekund

_PAS_API_GROUP = "pas_api"
_ACCESS_RULES_ID = "access_rules"
_RATE_LIMITS_ID = "rate_limits"

TYPE_IP_BLACKLIST = "ip_blacklist"
TYPE_IP_WHITELIST = "ip_whitelist"
TYPE_USER_BLACKLIST = "user_blacklist"
TYPE_USER_WHITELIST = "user_whitelist"
SCOPE_USER = "user"
SCOPE_IP = "ip"


def _load_json_setting(item_id: str) -> list:
    """
    Načte JSON seznam z ``CustomAdminSettings`` pro skupinu ``pas_api``.

    Nastavení se konfiguruje v Django administraci přes model ``CustomAdminSettings``
    (skupina ``pas_api``). Každý záznam musí mít pole ``value`` obsahující platný JSON seznam.

    Podporované záznamy:

    ``access_rules`` (``item_id="access_rules"``)
        Seznam pravidel přístupu. Každé pravidlo je objekt s klíči:

        - ``rule_type`` *(povinný)* — typ pravidla; povolené hodnoty:
          ``"ip_blacklist"``, ``"ip_whitelist"``, ``"user_blacklist"``, ``"user_whitelist"``
        - ``value`` *(povinný)* — IP adresa, CIDR rozsah (např. ``"192.168.1.0/24"``)
          nebo uživatelské jméno podle ``rule_type``
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
        - ``value`` *(povinný)* — uživatelské jméno nebo IP adresa/CIDR rozsah
        - ``rate`` *(povinný)* — limit ve formátu ``"počet/jednotka"``;
          jednotky: ``s`` (sekunda), ``m`` (minuta), ``h`` (hodina), ``d`` (den);
          např. ``"10/m"``, ``"100/h"``, ``"1000/d"``
        - ``active`` *(volitelný, výchozí* ``true``*)* — ``false`` limit dočasně deaktivuje

        Příklad::

            [
              {"scope": "user", "value": "jan.novak", "rate": "10/m"},
              {"scope": "ip", "value": "203.0.113.0/24", "rate": "50/h"}
            ]

    Změny v administraci se projeví do ``30`` sekund (TTL cache).

    :param item_id: Identifikátor záznamu — ``"access_rules"`` nebo ``"rate_limits"``.

    :return: Naparsovaný seznam nebo prázdný seznam při chybě či absenci záznamu.
    """
    try:
        obj = CustomAdminSettings.objects.get(item_group=_PAS_API_GROUP, item_id=item_id)
        return json.loads(obj.value)
    except CustomAdminSettings.DoesNotExist:
        return []
    except (json.JSONDecodeError, TypeError):
        logger.error("pas.api._load_json_setting.invalid_json", extra={"item_id": item_id})
        return []


def _get_access_rules() -> list[dict]:
    """
    Vrátí přístupová pravidla API z cache nebo ``CustomAdminSettings``.

    Každé pravidlo je slovník s klíči ``rule_type``, ``value`` a volitelně ``active`` (výchozí ``True``).

    :return: Seznam aktivních pravidel.
    """
    rules = cache.get(_CACHE_KEY_ACCESS_RULES)
    if rules is None:
        rules = [r for r in _load_json_setting(_ACCESS_RULES_ID) if r.get("active", True)]
        cache.set(_CACHE_KEY_ACCESS_RULES, rules, _CACHE_TTL)
    return rules


def _get_rate_limits() -> list[dict]:
    """
    Vrátí limity počtu požadavků z cache nebo ``CustomAdminSettings``.

    Každý limit je slovník s klíči ``scope``, ``value``, ``rate`` a volitelně ``active`` (výchozí ``True``).

    :return: Seznam aktivních limitů.
    """
    limits = cache.get(_CACHE_KEY_RATE_LIMITS)
    if limits is None:
        limits = [r for r in _load_json_setting(_RATE_LIMITS_ID) if r.get("active", True)]
        cache.set(_CACHE_KEY_RATE_LIMITS, limits, _CACHE_TTL)
    return limits


@receiver(post_save, sender=CustomAdminSettings)
@receiver(post_delete, sender=CustomAdminSettings)
def _invalidate_api_cache(sender, instance=None, **kwargs):
    """Vymaže cache pravidel API po změně záznamu ``CustomAdminSettings`` skupiny ``pas_api``."""
    if instance and instance.item_group == _PAS_API_GROUP:
        cache.delete(_CACHE_KEY_ACCESS_RULES)
        cache.delete(_CACHE_KEY_RATE_LIMITS)


def _get_client_ip(request) -> str:
    """
    Vrátí IP adresu klienta z požadavku s ohledem na proxy hlavičky.

    :param request: HTTP požadavek.

    :return: IP adresa klienta jako řetězec.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _get_user_identifier(user) -> str | None:
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


def _ip_matches(client_ip: str, pattern: str) -> bool:
    """
    Porovná IP adresu klienta s konkrétní adresou nebo CIDR rozsahem.

    :param client_ip: IP adresa klienta.
    :param pattern: IP adresa nebo CIDR rozsah (např. ``192.168.1.0/24``).

    :return: ``True`` pokud adresa odpovídá vzoru.
    """
    try:
        if "/" in pattern:
            return ipaddress.ip_address(client_ip) in ipaddress.ip_network(pattern, strict=False)
        return client_ip == pattern
    except ValueError:
        return False


class IpBlacklistPermission(BasePermission):
    """Zamítne přístup IP adresám uvedeným v blacklistu ``CustomAdminSettings`` (``pas_api/access_rules``)."""

    def has_permission(self, request, view) -> bool:
        """
        Ověří, zda IP adresa klienta není na blacklistu.

        :param request: HTTP požadavek.
        :param view: Pohled zpracovávající požadavek.

        :return: ``False`` pokud je IP na blacklistu, jinak ``True``.
        """
        client_ip = _get_client_ip(request)
        rules = _get_access_rules()
        for rule in rules:
            if rule["rule_type"] == TYPE_IP_BLACKLIST and _ip_matches(client_ip, rule["value"]):
                logger.warning(
                    "pas.api.IpBlacklistPermission.denied",
                    extra={"ip": client_ip, "rule": rule["value"]},
                )
                return False
        return True


class IpWhitelistPermission(BasePermission):
    """
    Povolí přístup pouze IP adresám uvedeným ve whitelistu ``CustomAdminSettings`` (``pas_api/access_rules``).

    Pokud žádné aktivní whitelist pravidlo neexistuje, propustí všechny požadavky.
    """

    def has_permission(self, request, view) -> bool:
        """
        Ověří, zda IP adresa klienta je na whitelistu (pokud je whitelist definován).

        :param request: HTTP požadavek.
        :param view: Pohled zpracovávající požadavek.

        :return: ``True`` pokud whitelist není definován nebo IP na něm je, jinak ``False``.
        """
        rules = _get_access_rules()
        whitelist = [r for r in rules if r["rule_type"] == TYPE_IP_WHITELIST]
        if not whitelist:
            return True
        client_ip = _get_client_ip(request)
        for rule in whitelist:
            if _ip_matches(client_ip, rule["value"]):
                return True
        logger.warning(
            "pas.api.IpWhitelistPermission.denied",
            extra={"ip": client_ip},
        )
        return False


class UserBlacklistPermission(BasePermission):
    """Zamítne přístup uživatelům uvedeným v blacklistu ``CustomAdminSettings`` (``pas_api/access_rules``)."""

    def has_permission(self, request, view) -> bool:
        """
        Ověří, zda přihlášený uživatel není na blacklistu.

        :param request: HTTP požadavek.
        :param view: Pohled zpracovávající požadavek.

        :return: ``False`` pokud je uživatel na blacklistu, jinak ``True``.
        """
        if not request.user or not request.user.is_authenticated:
            return True
        user_identifier = _get_user_identifier(request.user)
        rules = _get_access_rules()
        for rule in rules:
            if rule["rule_type"] == TYPE_USER_BLACKLIST and rule["value"] == user_identifier:
                logger.warning(
                    "pas.api.UserBlacklistPermission.denied",
                    extra={"user": user_identifier},
                )
                return False
        return True


class UserWhitelistPermission(BasePermission):
    """
    Povolí přístup pouze uživatelům uvedeným ve whitelistu ``CustomAdminSettings`` (``pas_api/access_rules``).

    Pokud žádné aktivní whitelist pravidlo neexistuje, propustí všechny požadavky.
    """

    def has_permission(self, request, view) -> bool:
        """
        Ověří, zda přihlášený uživatel je na whitelistu (pokud je whitelist definován).

        :param request: HTTP požadavek.
        :param view: Pohled zpracovávající požadavek.

        :return: ``True`` pokud whitelist není definován nebo uživatel na něm je, jinak ``False``.
        """
        rules = _get_access_rules()
        whitelist = [r for r in rules if r["rule_type"] == TYPE_USER_WHITELIST]
        if not whitelist:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        user_identifier = _get_user_identifier(request.user)
        for rule in whitelist:
            if rule["value"] == user_identifier:
                return True
        logger.warning(
            "pas.api.UserWhitelistPermission.denied",
            extra={"user": user_identifier},
        )
        return False


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


class ApiImportThrottle(BaseThrottle):
    """
    Throttle pro API import samostatného nálezu řízený záznamy ``CustomAdminSettings`` (``pas_api/rate_limits``).

    Pravidla jsou načítána z databáze (s cache) a aplikována v pořadí:
    nejdříve pravidlo pro konkrétního uživatele, pak pro IP adresu.
    Pokud žádné pravidlo neexistuje, požadavek je povolen.
    """

    def allow_request(self, request, view) -> bool:
        """
        Rozhodne, zda je požadavek povolen na základě nakonfigurovaných limitů.

        :param request: HTTP požadavek.
        :param view: Pohled zpracovávající požadavek.

        :return: ``True`` pokud limit nebyl překročen nebo neexistuje, jinak ``False``.
        """
        limits = _get_rate_limits()
        client_ip = _get_client_ip(request)
        user_identifier = _get_user_identifier(request.user)

        for limit in limits:
            if limit["scope"] == SCOPE_USER and limit["value"] == user_identifier:
                return self._check_limit(f"throttle_user_{user_identifier}", limit["rate"], request)
            if limit["scope"] == SCOPE_IP and _ip_matches(client_ip, limit["value"]):
                return self._check_limit(f"throttle_ip_{client_ip}", limit["rate"], request)
        return True

    def _check_limit(self, cache_key: str, rate: str, request) -> bool:
        """
        Zkontroluje a aktualizuje počítadlo požadavků v cache pro daný klíč a rate.

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
        history = cache.get(cache_key, [])
        history = [t for t in history if now - t < window]
        if len(history) >= max_requests:
            self.wait_seconds = window - (now - history[0]) if history else 1
            logger.warning(
                "pas.api.ApiImportThrottle.throttled",
                extra={"cache_key": cache_key, "rate": rate},
            )
            return False
        history.append(now)
        cache.set(cache_key, history, window)
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
        queryset=Projekt.objects.all(),
    )
    katastr = serializers.SlugRelatedField(
        slug_field="nazev",
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


class SamostatnyNalezXmlImportView(APIView):
    """Pohled pro import záznamu samostatného nálezu z XML souboru přes POST požadavek."""

    authentication_classes = [TokenAuthenticationBearer]
    permission_classes = [
        IsAuthenticated,
        IpBlacklistPermission,
        IpWhitelistPermission,
        UserBlacklistPermission,
        UserWhitelistPermission,
    ]
    throttle_classes = [ApiImportThrottle]
    parser_classes = [MultiPartParser]
    http_method_names = ["post"]

    HTTP_200_OK = 200
    HTTP_400_BAD_REQUEST = 400
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_422_UNPROCESSABLE_ENTITY = 422

    _AMCR_NS = "https://api.aiscr.cz/schema/amcr/2.2/"
    _XML_NS = "http://www.w3.org/XML/1998/namespace"
    _XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
    _IMPORT_HISTORY_NOTE = _("pas.api.SamostatnyNalezXmlImportView.import_history_note")
    _amcr_schema: etree.XMLSchema | None = None

    def post(self, request, format=None):
        """
        Importuje nový záznam samostatného nálezu z XML souboru.

        Přijímá soubor v parametru ``file`` (multipart/form-data). XML musí odpovídat
        schématu AMČR 2.2 (https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd).
        Každý element ``amcr:samostatny_nalez`` v dokumentu je importován jako
        samostatný záznam. Celá operace je atomická — při jakékoli chybě se
        neuloží nic.

        :param request: HTTP požadavek obsahující XML soubor v poli ``file``.
        :param format: Formát odpovědi.

        :return: Vrací ``Response`` se seznamem vytvořených ``ident_cely`` (HTTP 200),
                 nebo chybou syntaxe volání (HTTP 400), chybějícím projektem (HTTP 404),
                 nevalidním XML či datovými chybami (HTTP 422).
        """
        xml_file = request.FILES.get("file")
        if xml_file is None:
            return Response(
                {"detail": _("pas.api.SamostatnyNalezXmlImportView.post.missing_file")},
                status=self.HTTP_400_BAD_REQUEST,
            )

        digest_error = self._verify_content_digest(request, xml_file)
        if digest_error:
            return Response({"detail": digest_error}, status=self.HTTP_400_BAD_REQUEST)
        xml_file.seek(0)

        try:
            parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
            doc = etree.parse(xml_file, parser=parser)
        except etree.XMLSyntaxError as exc:
            logger.warning(
                "pas.api.SamostatnyNalezXmlImportView.post.xml_syntax_error",
                extra={"error": str(exc), "user": request.user.pk},
            )
            return Response(
                {"detail": _("pas.api.SamostatnyNalezXmlImportView.post.invalid_xml_syntax")},
                status=self.HTTP_400_BAD_REQUEST,
            )

        version_error = self._validate_declared_schema_version(doc)
        if version_error:
            return Response({"detail": version_error}, status=self.HTTP_422_UNPROCESSABLE_ENTITY)

        schema = self._get_amcr_schema()
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
            logger.warning(
                "pas.api.SamostatnyNalezXmlImportView.post.schema_invalid",
                extra={"errors": [error.to_dict() for error in errors], "user": request.user.pk},
            )
            return Response(
                {"schema_errors": [error.to_dict() for error in errors]}, status=self.HTTP_422_UNPROCESSABLE_ENTITY
            )

        root = doc.getroot()
        root_children = list(root)
        nalez_elements = [child for child in root_children if child.tag == self._ns("samostatny_nalez")]
        if not root_children:
            return Response(
                {"detail": _("pas.api.SamostatnyNalezXmlImportView.post.missing_samostatny_nalez")},
                status=self.HTTP_400_BAD_REQUEST,
            )
        if len(nalez_elements) > 1:
            return Response(
                {"detail": _("pas.api.SamostatnyNalezXmlImportView.post.multiple_samostatny_nalez")},
                status=self.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if len(root_children) != 1 or len(nalez_elements) != 1:
            return Response(
                {"detail": _("pas.api.SamostatnyNalezXmlImportView.post.invalid_root_content")},
                status=self.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        elem = nalez_elements[0]
        notes = self._get_ignored_lang_notes(elem)
        try:
            self._validate_disallowed_elements(elem)
            data, fedora_transaction = self._parse_nalez_element(elem, request.user)
        except ImportValidationException as exc:
            return self._validation_error_response(exc.import_errors, request.user)

        if not self._has_import_permissions(request.user, data):
            logger.warning(
                "pas.api.SamostatnyNalezXmlImportView.post.permission_denied",
                extra={"user": request.user.pk, "projekt": data.get("projekt")},
            )
            return Response(
                {"detail": _("pas.api.SamostatnyNalezXmlImportView.post.permission_denied")},
                status=self.HTTP_403_FORBIDDEN,
            )

        try:
            serializer = SamostatnyNalezXmlImportSerializer(data=data)
            if not serializer.is_valid():
                raise ImportValidationException.from_serializer_errors(serializer.errors, line=elem.sourceline)
            self._validate_heslar_value_matches(serializer.validated_data, elem)
        except ImportValidationException as exc:
            return self._validation_error_response(exc.import_errors, request.user)

        instance = SamostatnyNalez(**serializer.validated_data)
        if not instance.ident_cely:
            instance.ident_cely = get_sn_ident(instance.projekt)
        fedora_transaction = fedora_transaction or FedoraTransaction(instance, request.user)
        instance.active_transaction = fedora_transaction
        with transaction.atomic():
            instance.save()
            self._create_import_history_records(instance, request.user)

        fedora_transaction.mark_transaction_as_closed()
        metadata = FedoraRepositoryConnector(instance).get_metadata(update=False)

        logger.info(
            "pas.api.SamostatnyNalezXmlImportView.post.created",
            extra={"ident_cely": instance.ident_cely, "user": request.user.pk},
        )
        if notes:
            logger.info(
                "pas.api.SamostatnyNalezXmlImportView.post.ignored_lang_notes",
                extra={"ident_cely": instance.ident_cely, "notes": notes, "user": request.user.pk},
            )
        return HttpResponse(metadata, content_type="application/xml", status=self.HTTP_200_OK)

    @staticmethod
    def _has_import_permissions(user, data: dict) -> bool:
        """
        Ověří oprávnění potřebná pro import samostatného nálezu.

        :param user: Uživatel provádějící import.
        :param data: Data jednoho importovaného záznamu.

        :return: Vrací ``True`` pokud má uživatel obě vyžadovaná oprávnění.
        """
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

    def _validation_error_response(self, errors: list[ImportValidationIssue], user) -> Response:
        """
        Vytvoří HTTP odpověď pro validační chyby importu.

        :param errors: Seznam validačních chyb importu.
        :param user: Uživatel provádějící import.

        :return: HTTP odpověď se serializovanými chybami.
        """
        serialized_errors = [error.to_dict() for error in errors]
        logger.warning(
            "pas.api.SamostatnyNalezXmlImportView.post.validation_errors",
            extra={"errors": serialized_errors, "user": user.pk},
        )
        if any(error.error_type == ImportErrorType.PERMISSION_ERROR for error in errors):
            return Response({"validation_errors": serialized_errors}, status=self.HTTP_403_FORBIDDEN)
        if any(error.error_type == ImportErrorType.RECORD_DOES_NOT_EXIST for error in errors):
            return Response({"validation_errors": serialized_errors}, status=self.HTTP_404_NOT_FOUND)
        return Response({"validation_errors": serialized_errors}, status=self.HTTP_422_UNPROCESSABLE_ENTITY)

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

        def strip_namespace(tag: str) -> str:
            """
            Vrátí název XML tagu bez namespace prefixu pro účely schema-validace.

            :param tag: XML tag včetně namespace.

            :return: Název tagu bez namespace.
            """
            if "}" in tag:
                return tag.split("}", 1)[1]
            return tag

        validation_doc = etree.ElementTree(etree.fromstring(etree.tostring(doc.getroot())))
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
                if strip_namespace(child.tag) in insert_before_tags:
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
    def _get_amcr_schema(cls) -> etree.XMLSchema:
        """
        Vrátí zkompilované XSD schéma AMČR (singleton, načte se jednou).

        :return: Vrací instanci ``etree.XMLSchema`` pro validaci importovaných XML dokumentů.
        """
        if cls._amcr_schema is None:

            class _LocalResolver(etree.Resolver):
                """Resolver nahrazující vzdálené W3C URL lokálním souborem xml.xsd."""

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
                    )
                    if url in allowed_urls:
                        return self.resolve_filename("xml_generator/definitions/xml.xsd", context)
                    return None

            parser = etree.XMLParser()
            parser.resolvers.add(_LocalResolver())
            with open(DocumentGenerator.get_path_to_schema(), "rb") as f:
                schema_doc = etree.parse(f, parser)
            cls._amcr_schema = etree.XMLSchema(schema_doc)
        return cls._amcr_schema

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

        def strip_namespace(tag: str) -> str:
            """
            Vrátí název XML tagu bez namespace prefixu.

            :param tag: XML tag včetně namespace.

            :return: Název tagu bez namespace.
            """
            if "}" in tag:
                return tag.split("}", 1)[1]
            return tag

        notes = []
        lang_attr = f"{{{cls._XML_NS}}}lang"
        for child in elem.iter():
            lang_value = child.get(lang_attr)
            if lang_value and lang_value.lower() != "cs":
                notes.append(
                    _("pas.api.SamostatnyNalezXmlImportView.post.ignored_lang_attribute")
                    % {"element": strip_namespace(child.tag), "lang": lang_value}
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
    def _parse_nalezce(cls, elem: etree._Element, user) -> tuple[str | None, FedoraTransaction | None]:
        """
        Zpracuje element ``nalezce`` a vrátí ``ident_cely`` osoby pro import.

        Pokud má element atribut ``id=":tba"``, vytvoří se nová osoba z textu
        ve formátu ``"Příjmení, Jméno"``.

        :param elem: Element ``amcr:samostatny_nalez``.
        :param user: Uživatel provádějící import.

        :return: Dvojice ``(ident_cely_osoby, fedora_transaction)``.
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
        fedora_transaction = FedoraTransaction(transaction_user=user)
        osoba = Osoba(
            prijmeni=prijmeni,
            jmeno=jmeno,
            vypis=build_osoba_vypis(prijmeni, jmeno),
            vypis_cely=f"{prijmeni}, {jmeno}",
        )
        osoba.active_transaction = fedora_transaction
        osoba.save()
        return osoba.ident_cely, fedora_transaction

    @classmethod
    def _parse_nalez_element(cls, elem: etree._Element, user) -> tuple[dict, FedoraTransaction | None]:
        """
        Převede element ``amcr:samostatny_nalez`` na slovník pro deserializaci.

        Elementy typu ``refType`` a ``vocabType`` se mapují pomocí atributu ``id``,
        který nese ``ident_cely`` odkazovaného záznamu. Geometrie jsou předány
        jako WKT řetězce z elementů ``geom_wkt`` a ``geom_sjtsk_wkt``.

        :param elem: Element ``amcr:samostatny_nalez`` z importovaného XML dokumentu.
        :param user: Uživatel provádějící import.

        :return: Dvojice ``(data, fedora_transaction)`` připravená pro import.
        """
        chranene = elem.find(cls._ns("chranene_udaje"))
        nalezce_ident, fedora_transaction = cls._parse_nalezce(elem, user)

        data = {
            "ident_cely": None if cls._text(elem, "ident_cely") == ":tba" else cls._text(elem, "ident_cely"),
            "projekt": cls._id_attr(elem, "projekt"),
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
            data["lokalizace"] = cls._text(chranene, "lokalizace")
            geom_wkt_elem = chranene.find(cls._ns("geom_wkt"))
            if geom_wkt_elem is not None and geom_wkt_elem.text:
                data["geom"] = geom_wkt_elem.text.strip()
            geom_sjtsk_elem = chranene.find(cls._ns("geom_sjtsk_wkt"))
            if geom_sjtsk_elem is not None and geom_sjtsk_elem.text:
                data["geom_sjtsk"] = geom_sjtsk_elem.text.strip()

        return {k: v for k, v in data.items() if v is not None}, fedora_transaction
