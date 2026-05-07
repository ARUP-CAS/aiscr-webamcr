"""Jednotkové testy permission tříd používaných v PAS XML API."""

import json
from types import SimpleNamespace
from unittest.mock import patch

from core.setting_models import CustomAdminSettings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase
from pas.api import (
    ACCESS_MODE_CLOSED,
    ACCESS_MODE_OPEN,
    ACCESS_MODE_WHITELIST_ONLY,
    ApiAccessModePermission,
    ApiImportThrottle,
    IpBlacklistPermission,
    IpWhitelistPermission,
    PasApiPermissionMixin,
    UserBlacklistPermission,
    UserWhitelistPermission,
)


class PasApiPermissionTests(TestCase):
    """Testy permission tříd pro konfigurovatelný přístup do PAS XML API."""

    def setUp(self):
        """Před každým testem vyčistí per-test PAS API nastavení."""
        super().setUp()
        self._clear_pas_api_settings()

    def tearDown(self):
        """Po každém testu znovu vyčistí PAS API nastavení."""
        self._clear_pas_api_settings()
        super().tearDown()

    @staticmethod
    def _build_request(ip: str = "127.0.0.1", user=None):
        """
        Vytvoří minimální request objekt pro permission testy.

        :param ip: IP adresa klienta.
        :param user: Uživatelský objekt; pokud není zadán, použije se anonymní uživatel.

        :return: Objekt s atributy ``META`` a ``user``.
        """
        if user is None:
            user = SimpleNamespace(is_authenticated=False, email=None, username=None)
        return SimpleNamespace(META={"REMOTE_ADDR": ip}, user=user)

    @staticmethod
    def _build_user(email: str, username: str | None = None):
        """
        Vytvoří minimální autentizovaný uživatelský objekt pro permission testy.

        :param email: Email uživatele.
        :param username: Volitelný fallback username.

        :return: Objekt s atributy kompatibilními s permission helpery.
        """
        return SimpleNamespace(
            is_authenticated=True,
            email=email,
            username=username or email.split("@", 1)[0],
        )

    def _clear_pas_api_settings(self) -> None:
        """Vyčistí testovací ``CustomAdminSettings`` a odpovídající cache."""
        CustomAdminSettings.objects.filter(item_group="pas_api").delete()
        cache.clear()

    def _set_pas_api_setting(self, item_id: str, value) -> None:
        """
        Uloží JSON hodnotu do ``CustomAdminSettings`` pro skupinu ``pas_api``.

        :param item_id: Identifikátor položky nastavení.
        :param value: Hodnota serializovatelná do JSON.
        """
        CustomAdminSettings.objects.update_or_create(
            item_group="pas_api",
            item_id=item_id,
            defaults={"value": json.dumps(value)},
        )

    def test_api_access_mode_permission_has_permission_short_circuits_for_closed_mode(self):
        """V režimu `closed` `ApiAccessModePermission.has_permission()` nenatahuje access-rules."""
        permission = ApiAccessModePermission()
        request = self._build_request()

        with patch.object(
            ApiAccessModePermission, "get_access_mode", return_value=ACCESS_MODE_CLOSED
        ) as get_access_mode:
            with patch.object(ApiAccessModePermission, "get_access_rules") as get_access_rules:
                self.assertFalse(permission.has_permission(request))

        get_access_mode.assert_called_once_with()
        get_access_rules.assert_not_called()
        self.assertEqual(str(permission.message), "pas.api.ApiAccessModePermission.closed")

    def test_api_access_mode_permission_returns_false_for_closed_mode(self):
        """Režim ``closed`` odmítne přístup."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_CLOSED)
        permission = ApiAccessModePermission()

        self.assertFalse(permission.has_permission(self._build_request()))

    def test_api_access_mode_permission_returns_false_for_whitelist_only_without_whitelist_rule(self):
        """Režim ``whitelist_only`` bez whitelist pravidel odmítne přístup."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_WHITELIST_ONLY)
        permission = ApiAccessModePermission()

        self.assertFalse(permission.has_permission(self._build_request()))

    def test_api_access_mode_permission_returns_true_by_default(self):
        """Bez nastaveného ``access_mode`` se použije výchozí režim ``open``."""
        permission = ApiAccessModePermission()

        self.assertTrue(permission.has_permission(self._build_request()))

    def test_api_access_mode_permission_returns_true_for_open_mode(self):
        """Režim ``open`` povolí přístup."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_OPEN)
        permission = ApiAccessModePermission()

        self.assertTrue(permission.has_permission(self._build_request()))

    def test_api_access_mode_permission_returns_true_for_whitelist_only_with_whitelist_rule(self):
        """Režim ``whitelist_only`` je aktivní, pokud existuje alespoň jedno whitelist pravidlo."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_WHITELIST_ONLY)
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_whitelist", "value": "203.0.113.10", "active": True}],
        )
        permission = ApiAccessModePermission()

        self.assertTrue(permission.has_permission(self._build_request()))

    def test_api_import_throttle_applies_to_ip_in_range(self):
        """IP limit se aplikuje i na klienta spadajícího do explicitního IP rozsahu."""
        self._set_pas_api_setting(
            "rate_limits",
            [{"scope": "ip", "value": "192.168.1.1-192.168.1.5", "rate": "1/m", "active": True}],
        )
        throttle = ApiImportThrottle()
        request = self._build_request(ip="192.168.1.3")

        with patch("pas.api.time.time", return_value=1000.0):
            self.assertTrue(throttle.allow_request(request))
            self.assertFalse(throttle.allow_request(request))

    def test_api_import_throttle_does_not_apply_to_ip_outside_range(self):
        """IP limit se neuplatní na klienta mimo explicitní IP rozsah."""
        self._set_pas_api_setting(
            "rate_limits",
            [{"scope": "ip", "value": "192.168.1.1-192.168.1.5", "rate": "1/m", "active": True}],
        )
        throttle = ApiImportThrottle()
        request = self._build_request(ip="192.168.1.6")

        self.assertTrue(throttle.allow_request(request))
        self.assertTrue(throttle.allow_request(request))

    def test_api_import_throttle_uses_atomic_fixed_window_counter(self):
        """Throttle používá atomický čítač ve fixním okně a nastaví wait čas při překročení limitu."""
        throttle = ApiImportThrottle()
        request = self._build_request(ip="203.0.113.10")

        with patch("pas.api.time.time", return_value=1000.0):
            self.assertTrue(throttle._check_limit("throttle_ip_203.0.113.10", "2/m", request))
            self.assertTrue(throttle._check_limit("throttle_ip_203.0.113.10", "2/m", request))
            self.assertFalse(throttle._check_limit("throttle_ip_203.0.113.10", "2/m", request))

        self.assertEqual(throttle.wait_seconds, 60)

    def test_custom_admin_setting_full_clean_allows_valid_access_rules(self):
        """Validní `access_rules` projdou `full_clean()` a lze je uložit."""
        instance = CustomAdminSettings(
            item_group="pas_api",
            item_id="access_rules",
            value=json.dumps([{"rule_type": "ip_blacklist", "value": "203.0.113.10", "active": True}]),
        )

        instance.full_clean()
        instance.save()

        self.assertTrue(
            CustomAdminSettings.objects.filter(
                item_group="pas_api",
                item_id="access_rules",
                value=instance.value,
            ).exists()
        )

    def test_custom_admin_setting_full_clean_raises_for_invalid_access_mode(self):
        """`full_clean()` odmítne nevalidní `access_mode`."""
        instance = CustomAdminSettings(
            item_group="pas_api",
            item_id="access_mode",
            value=json.dumps("bad_mode"),
        )

        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_access_mode.invalid_value",
        ):
            instance.full_clean()

    def test_custom_admin_setting_full_clean_raises_for_invalid_access_rules(self):
        """`full_clean()` odmítne nevalidní `access_rules` jako validační chybu modelu."""
        instance = CustomAdminSettings(
            item_group="pas_api",
            item_id="access_rules",
            value=json.dumps([{"rule_type": "ip_blacklist", "value": "999.999.999.999", "active": True}]),
        )

        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_access_rules.invalid_ip_value",
        ):
            instance.full_clean()

    def test_custom_admin_setting_full_clean_raises_for_invalid_access_rules_json(self):
        """Nevalidní JSON v `access_rules` je odmítnut při `full_clean()`."""
        instance = CustomAdminSettings(
            item_group="pas_api",
            item_id="access_rules",
            value="{not valid json",
        )

        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_custom_admin_setting.invalid_json",
        ):
            instance.full_clean()

    def test_custom_admin_setting_full_clean_raises_for_invalid_item_id(self):
        """Skupina `pas_api` nepovoluje neznámý `item_id`."""
        instance = CustomAdminSettings(
            item_group="pas_api",
            item_id="unknown_setting",
            value=json.dumps({}),
        )

        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_custom_admin_setting.invalid_item_id",
        ):
            instance.full_clean()

    def test_custom_admin_setting_full_clean_raises_for_invalid_rate_limits(self):
        """`full_clean()` odmítne nevalidní `rate_limits`."""
        instance = CustomAdminSettings(
            item_group="pas_api",
            item_id="rate_limits",
            value=json.dumps([{"scope": "ip", "value": "999.999.999.999", "rate": "1/m", "active": True}]),
        )

        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_rate_limits.invalid_ip_value",
        ):
            instance.full_clean()

    def test_get_access_rules_raises_for_invalid_ip_value(self):
        """IP pravidlo musí mít syntakticky validní IP adresu, CIDR nebo rozsah."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_access_rules.invalid_ip_value",
        ):
            IpBlacklistPermission.validate_access_rules(
                [{"rule_type": "ip_blacklist", "value": "999.999.999.999", "active": True}]
            )

    def test_get_access_rules_raises_for_missing_required_keys(self):
        """Položka `access_rules` musí obsahovat `rule_type` i `value`."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_access_rules.missing_required_keys",
        ):
            IpBlacklistPermission.validate_access_rules([{"rule_type": "ip_blacklist"}])

    def test_get_access_rules_raises_for_non_bool_active(self):
        """Klíč `active` musí být bool nebo null."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_access_rules.invalid_active",
        ):
            IpBlacklistPermission.validate_access_rules(
                [{"rule_type": "ip_blacklist", "value": "203.0.113.10", "active": "yes"}]
            )

    def test_get_access_rules_raises_for_non_dict_item(self):
        """Položka `access_rules` musí být slovník."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_access_rules.item_not_a_dict",
        ):
            IpBlacklistPermission.validate_access_rules(["203.0.113.10"])

    def test_get_access_rules_raises_for_non_list_setting(self):
        """`access_rules` musí být seznam slovníků."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_access_rules.not_a_list",
        ):
            IpBlacklistPermission.validate_access_rules({"rule_type": "ip_blacklist", "value": "203.0.113.10"})

    def test_get_access_rules_raises_for_unsupported_rule_type(self):
        """`rule_type` musí být jedním z podporovaných typů pravidel."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_access_rules.unsupported_rule_type",
        ):
            IpBlacklistPermission.validate_access_rules(
                [{"rule_type": "unsupported_rule", "value": "203.0.113.10", "active": True}]
            )

    def test_ip_blacklist_permission_has_permission_uses_only_ip_blacklist_rules(self):
        """`IpBlacklistPermission.has_permission()` ignoruje ne-IP-blacklist pravidla."""
        permission = IpBlacklistPermission()
        request = self._build_request(ip="203.0.113.10")

        with patch.object(IpBlacklistPermission, "get_client_ip", return_value="203.0.113.10") as get_client_ip:
            with patch.object(
                IpBlacklistPermission,
                "get_access_rules",
                return_value=[
                    {"rule_type": "user_blacklist", "value": "blocked@example.com", "active": True},
                    {"rule_type": "ip_whitelist", "value": "203.0.113.10", "active": True},
                ],
            ) as get_access_rules:
                with patch.object(IpBlacklistPermission, "ip_matches") as ip_matches:
                    self.assertTrue(permission.has_permission(request))

        get_client_ip.assert_called_once_with(request)
        get_access_rules.assert_called_once_with()
        ip_matches.assert_not_called()

    def test_ip_blacklist_permission_returns_false_for_blocked_ip(self):
        """IP adresa uvedená na blacklistu je odmítnuta."""
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_blacklist", "value": "203.0.113.10", "active": True}],
        )
        permission = IpBlacklistPermission()

        self.assertFalse(permission.has_permission(self._build_request(ip="203.0.113.10")))

    def test_ip_blacklist_permission_returns_false_for_ip_in_blocked_range(self):
        """IP adresa spadající do explicitního rozsahu na blacklistu je odmítnuta."""
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_blacklist", "value": "192.168.1.1-192.168.1.5", "active": True}],
        )
        permission = IpBlacklistPermission()

        self.assertFalse(permission.has_permission(self._build_request(ip="192.168.1.3")))

    def test_ip_blacklist_permission_returns_true_for_ip_outside_blocked_range(self):
        """IP adresa mimo explicitní rozsah na blacklistu je povolena."""
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_blacklist", "value": "192.168.1.1-192.168.1.5", "active": True}],
        )
        permission = IpBlacklistPermission()

        self.assertTrue(permission.has_permission(self._build_request(ip="192.168.1.6")))

    def test_ip_blacklist_permission_returns_true_for_non_blocked_ip(self):
        """IP adresa mimo blacklist je povolena."""
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_blacklist", "value": "203.0.113.10", "active": True}],
        )
        permission = IpBlacklistPermission()

        self.assertTrue(permission.has_permission(self._build_request(ip="203.0.113.11")))

    def test_ip_blacklist_permission_returns_true_when_no_rules_defined(self):
        """Bez access-rules IP blacklist nic neblokuje."""
        permission = IpBlacklistPermission()

        self.assertTrue(permission.has_permission(self._build_request(ip="203.0.113.10")))

    def test_ip_whitelist_permission_has_permission_short_circuits_outside_whitelist_only(self):
        """Mimo `whitelist_only` `IpWhitelistPermission.has_permission()` nečte whitelist pravidla."""
        permission = IpWhitelistPermission()
        request = self._build_request(ip="203.0.113.10")

        with patch.object(IpWhitelistPermission, "get_access_mode", return_value=ACCESS_MODE_OPEN) as get_access_mode:
            with patch.object(IpWhitelistPermission, "get_access_rules") as get_access_rules:
                with patch.object(IpWhitelistPermission, "get_client_ip") as get_client_ip:
                    self.assertTrue(permission.has_permission(request))

        get_access_mode.assert_called_once_with()
        get_access_rules.assert_not_called()
        get_client_ip.assert_not_called()

    def test_ip_whitelist_permission_returns_false_for_ip_outside_whitelisted_range_in_whitelist_only(self):
        """V režimu ``whitelist_only`` je IP mimo explicitní whitelist rozsah odmítnuta."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_WHITELIST_ONLY)
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_whitelist", "value": "192.168.1.1-192.168.1.5", "active": True}],
        )
        permission = IpWhitelistPermission()

        self.assertFalse(permission.has_permission(self._build_request(ip="192.168.1.6")))

    def test_ip_whitelist_permission_returns_false_for_non_whitelisted_ip_in_whitelist_only(self):
        """V režimu ``whitelist_only`` je ne-whitelisted IP odmítnuta."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_WHITELIST_ONLY)
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_whitelist", "value": "203.0.113.10", "active": True}],
        )
        permission = IpWhitelistPermission()

        self.assertFalse(permission.has_permission(self._build_request(ip="203.0.113.11")))

    def test_ip_whitelist_permission_returns_true_for_ip_in_whitelisted_range_in_whitelist_only(self):
        """V režimu ``whitelist_only`` je IP z explicitního whitelist rozsahu povolena."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_WHITELIST_ONLY)
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_whitelist", "value": "192.168.1.1-192.168.1.5", "active": True}],
        )
        permission = IpWhitelistPermission()

        self.assertTrue(permission.has_permission(self._build_request(ip="192.168.1.4")))

    def test_ip_whitelist_permission_returns_true_for_whitelisted_and_non_whitelisted_ips_outside_whitelist_only(self):
        """Mimo režim ``whitelist_only`` se IP whitelist neuplatní."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_OPEN)
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_whitelist", "value": "203.0.113.10", "active": True}],
        )
        permission = IpWhitelistPermission()

        self.assertTrue(permission.has_permission(self._build_request(ip="203.0.113.10")))
        self.assertTrue(permission.has_permission(self._build_request(ip="203.0.113.11")))

    def test_ip_whitelist_permission_returns_true_for_whitelisted_ip_in_whitelist_only(self):
        """V režimu ``whitelist_only`` je whitelisted IP povolena."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_WHITELIST_ONLY)
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_whitelist", "value": "203.0.113.10", "active": True}],
        )
        permission = IpWhitelistPermission()

        self.assertTrue(permission.has_permission(self._build_request(ip="203.0.113.10")))

    def test_ip_whitelist_permission_returns_true_without_ip_whitelist_rules_in_whitelist_only(self):
        """Samotný ``IpWhitelistPermission`` bez IP whitelist pravidel nikoho neblokuje."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_WHITELIST_ONLY)
        permission = IpWhitelistPermission()

        self.assertTrue(permission.has_permission(self._build_request(ip="203.0.113.11")))

    def test_permission_stack_blacklisted_user_is_denied_even_if_whitelisted(self):
        """Blacklisted uživatel je v permission stacku odmítnut i když je současně na whitelistu."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_WHITELIST_ONLY)
        self._set_pas_api_setting(
            "access_rules",
            [
                {"rule_type": "user_whitelist", "value": "blocked@example.com", "active": True},
                {"rule_type": "user_blacklist", "value": "blocked@example.com", "active": True},
            ],
        )
        request = self._build_request(user=self._build_user("blocked@example.com"))

        self.assertTrue(ApiAccessModePermission().has_permission(request))
        self.assertFalse(UserBlacklistPermission().has_permission(request))
        self.assertTrue(UserWhitelistPermission().has_permission(request))

    def test_user_blacklist_permission_has_permission_short_circuits_for_anonymous_user(self):
        """`UserBlacklistPermission.has_permission()` pro anonymního uživatele nečte pravidla ani identifikátor."""
        permission = UserBlacklistPermission()
        request = self._build_request()

        with patch.object(UserBlacklistPermission, "get_user_identifier") as get_user_identifier:
            with patch.object(UserBlacklistPermission, "get_access_rules") as get_access_rules:
                self.assertTrue(permission.has_permission(request))

        get_user_identifier.assert_not_called()
        get_access_rules.assert_not_called()

    def test_user_blacklist_permission_returns_false_for_blacklisted_user(self):
        """Uživatel uvedený na blacklistu je odmítnut."""
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "user_blacklist", "value": "blocked@example.com", "active": True}],
        )
        permission = UserBlacklistPermission()

        self.assertFalse(permission.has_permission(self._build_request(user=self._build_user("blocked@example.com"))))

    def test_user_blacklist_permission_returns_true_for_anonymous_user(self):
        """Neautentizovaný uživatel není user-blacklistem blokován."""
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "user_blacklist", "value": "blocked@example.com", "active": True}],
        )
        permission = UserBlacklistPermission()

        self.assertTrue(permission.has_permission(self._build_request()))

    def test_user_blacklist_permission_returns_true_for_non_blacklisted_user(self):
        """Uživatel mimo blacklist je povolen."""
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "user_blacklist", "value": "blocked@example.com", "active": True}],
        )
        permission = UserBlacklistPermission()

        self.assertTrue(permission.has_permission(self._build_request(user=self._build_user("allowed@example.com"))))

    def test_user_whitelist_permission_returns_false_for_anonymous_user_in_whitelist_only(self):
        """V režimu ``whitelist_only`` anonymní požadavek s user whitelist pravidly neprojde."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_WHITELIST_ONLY)
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "user_whitelist", "value": "whitelisted@example.com", "active": True}],
        )
        permission = UserWhitelistPermission()

        self.assertFalse(permission.has_permission(self._build_request()))

    def test_user_whitelist_permission_returns_false_for_non_whitelisted_user_in_whitelist_only(self):
        """V režimu ``whitelist_only`` je ne-whitelisted uživatel odmítnut."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_WHITELIST_ONLY)
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "user_whitelist", "value": "whitelisted@example.com", "active": True}],
        )
        permission = UserWhitelistPermission()

        self.assertFalse(permission.has_permission(self._build_request(user=self._build_user("other@example.com"))))

    def test_user_whitelist_permission_returns_true_for_whitelisted_and_non_whitelisted_users_outside_whitelist_only(
        self,
    ):
        """Mimo režim ``whitelist_only`` se user whitelist neuplatní."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_OPEN)
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "user_whitelist", "value": "whitelisted@example.com", "active": True}],
        )
        permission = UserWhitelistPermission()

        self.assertTrue(
            permission.has_permission(self._build_request(user=self._build_user("whitelisted@example.com")))
        )
        self.assertTrue(permission.has_permission(self._build_request(user=self._build_user("other@example.com"))))

    def test_user_whitelist_permission_returns_true_for_whitelisted_user_in_whitelist_only(self):
        """V režimu ``whitelist_only`` je whitelisted uživatel povolen."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_WHITELIST_ONLY)
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "user_whitelist", "value": "whitelisted@example.com", "active": True}],
        )
        permission = UserWhitelistPermission()

        self.assertTrue(
            permission.has_permission(self._build_request(user=self._build_user("whitelisted@example.com")))
        )

    def test_validate_access_mode_allows_open_value(self):
        """Podporovaná hodnota `access_mode` projde validací."""
        self.assertTrue(IpBlacklistPermission.validate_access_mode("open"))

    def test_validate_access_mode_raises_for_invalid_value(self):
        """`access_mode` musí být jednou z podporovaných hodnot."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_access_mode.invalid_value",
        ):
            IpBlacklistPermission.validate_access_mode("invalid_mode")

    def test_validate_custom_admin_setting_returns_true_for_non_access_rules_item(self):
        """Validní `pas_api/access_mode` validace propustí bez výjimky."""
        instance = CustomAdminSettings(
            item_group="pas_api",
            item_id="access_mode",
            value=json.dumps("open"),
        )

        self.assertTrue(IpBlacklistPermission.validate_custom_admin_setting(instance))

    def test_validate_rate_limits_raises_for_invalid_ip_value(self):
        """IP limit musí mít syntakticky validní IP adresu, CIDR nebo rozsah."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_rate_limits.invalid_ip_value",
        ):
            IpBlacklistPermission.validate_rate_limits(
                [{"scope": "ip", "value": "999.999.999.999", "rate": "1/m", "active": True}]
            )

    def test_validate_rate_limits_raises_for_invalid_rate(self):
        """`rate` v `rate_limits` musí mít podporovaný formát."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_rate_limits.invalid_rate",
        ):
            IpBlacklistPermission.validate_rate_limits(
                [{"scope": "ip", "value": "203.0.113.10", "rate": "abc", "active": True}]
            )

    def test_validate_rate_limits_raises_for_missing_required_keys(self):
        """Položka `rate_limits` musí obsahovat `scope`, `value` a `rate`."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_rate_limits.missing_required_keys",
        ):
            IpBlacklistPermission.validate_rate_limits([{"scope": "ip", "value": "203.0.113.10"}])

    def test_validate_rate_limits_raises_for_non_bool_active(self):
        """Klíč `active` v `rate_limits` musí být bool nebo null."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_rate_limits.invalid_active",
        ):
            IpBlacklistPermission.validate_rate_limits(
                [{"scope": "ip", "value": "203.0.113.10", "rate": "1/m", "active": "yes"}]
            )

    def test_validate_rate_limits_raises_for_non_dict_item(self):
        """Položka `rate_limits` musí být slovník."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_rate_limits.item_not_a_dict",
        ):
            IpBlacklistPermission.validate_rate_limits(["203.0.113.10"])

    def test_validate_rate_limits_raises_for_non_list_setting(self):
        """`rate_limits` musí být seznam slovníků."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_rate_limits.not_a_list",
        ):
            IpBlacklistPermission.validate_rate_limits({"scope": "ip", "value": "203.0.113.10", "rate": "1/m"})

    def test_validate_rate_limits_raises_for_unsupported_scope(self):
        """`scope` v `rate_limits` musí být `user` nebo `ip`."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_rate_limits.unsupported_scope",
        ):
            IpBlacklistPermission.validate_rate_limits(
                [{"scope": "group", "value": "203.0.113.10", "rate": "1/m", "active": True}]
            )

    # --- IPv6 ---

    def test_validate_access_rules_accepts_ipv6_address(self):
        """IP pravidlo s IPv6 adresou projde validací."""
        self.assertTrue(
            IpBlacklistPermission.validate_access_rules(
                [{"rule_type": "ip_blacklist", "value": "2001:db8::1", "active": True}]
            )
        )

    def test_validate_access_rules_accepts_ipv6_cidr(self):
        """IP pravidlo s IPv6 CIDR prefixem projde validací."""
        self.assertTrue(
            IpBlacklistPermission.validate_access_rules(
                [{"rule_type": "ip_whitelist", "value": "2001:db8::/32", "active": True}]
            )
        )

    def test_validate_rate_limits_accepts_ipv6_address(self):
        """IP rate limit s IPv6 adresou projde validací."""
        self.assertTrue(
            IpBlacklistPermission.validate_rate_limits(
                [{"scope": "ip", "value": "2001:db8::1", "rate": "10/m", "active": True}]
            )
        )

    def test_validate_rate_limits_accepts_ipv6_cidr(self):
        """IP rate limit s IPv6 CIDR prefixem projde validací."""
        self.assertTrue(
            IpBlacklistPermission.validate_rate_limits(
                [{"scope": "ip", "value": "2001:db8::/32", "rate": "10/m", "active": True}]
            )
        )

    def test_ip_blacklist_permission_blocks_ipv6_address(self):
        """IPv6 adresa uvedená na blacklistu je odmítnuta."""
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_blacklist", "value": "2001:db8::1", "active": True}],
        )
        permission = IpBlacklistPermission()

        self.assertFalse(permission.has_permission(self._build_request(ip="2001:db8::1")))

    def test_ip_blacklist_permission_blocks_ipv6_cidr(self):
        """IPv6 adresa spadající do CIDR rozsahu na blacklistu je odmítnuta."""
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_blacklist", "value": "2001:db8::/32", "active": True}],
        )
        permission = IpBlacklistPermission()

        self.assertFalse(permission.has_permission(self._build_request(ip="2001:db8::cafe")))

    def test_ip_blacklist_permission_allows_ipv6_outside_cidr(self):
        """IPv6 adresa mimo CIDR rozsah na blacklistu je povolena."""
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_blacklist", "value": "2001:db8::/32", "active": True}],
        )
        permission = IpBlacklistPermission()

        self.assertTrue(permission.has_permission(self._build_request(ip="2001:db9::1")))

    def test_ip_whitelist_permission_allows_ipv6_in_whitelist_only(self):
        """V režimu ``whitelist_only`` je whitelisted IPv6 adresa povolena."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_WHITELIST_ONLY)
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_whitelist", "value": "2001:db8::/32", "active": True}],
        )
        permission = IpWhitelistPermission()

        self.assertTrue(permission.has_permission(self._build_request(ip="2001:db8::1")))

    def test_ip_whitelist_permission_blocks_ipv6_outside_whitelist_in_whitelist_only(self):
        """V režimu ``whitelist_only`` je IPv6 adresa mimo whitelist CIDR odmítnuta."""
        self._set_pas_api_setting("access_mode", ACCESS_MODE_WHITELIST_ONLY)
        self._set_pas_api_setting(
            "access_rules",
            [{"rule_type": "ip_whitelist", "value": "2001:db8::/32", "active": True}],
        )
        permission = IpWhitelistPermission()

        self.assertFalse(permission.has_permission(self._build_request(ip="2001:db9::1")))

    def test_api_import_throttle_applies_to_ipv6_cidr(self):
        """IP rate limit se aplikuje i na IPv6 klienta spadajícího do CIDR rozsahu."""
        self._set_pas_api_setting(
            "rate_limits",
            [{"scope": "ip", "value": "2001:db8::/32", "rate": "1/m", "active": True}],
        )
        throttle = ApiImportThrottle()
        request = self._build_request(ip="2001:db8::1")

        with patch("pas.api.time.time", return_value=1000.0):
            self.assertTrue(throttle.allow_request(request))
            self.assertFalse(throttle.allow_request(request))


class GetClientIpTests(TestCase):
    """Testy metody ``PasApiPermissionMixin.get_client_ip``."""

    def setUp(self):
        """Před každým testem vyčistí PAS API nastavení a DNS resolve cache."""
        super().setUp()
        CustomAdminSettings.objects.filter(item_group="pas_api").delete()
        cache.clear()
        PasApiPermissionMixin._trusted_proxy_resolve_cache.clear()

    def tearDown(self):
        """Po každém testu vyčistí PAS API nastavení a DNS resolve cache."""
        CustomAdminSettings.objects.filter(item_group="pas_api").delete()
        cache.clear()
        PasApiPermissionMixin._trusted_proxy_resolve_cache.clear()
        super().tearDown()

    @staticmethod
    def _build_request(remote_addr: str = "10.0.1.1", x_forwarded_for: str | None = None):
        """
        Vytvoří minimální request objekt pro testy ``get_client_ip``.

        :param remote_addr: Hodnota ``REMOTE_ADDR`` (přímý spojovatel — typicky proxy).
        :param x_forwarded_for: Hodnota hlavičky ``X-Forwarded-For``; ``None`` znamená chybějící hlavičku.

        :return: Objekt s atributem ``META``.
        """
        meta = {"REMOTE_ADDR": remote_addr}
        if x_forwarded_for is not None:
            meta["HTTP_X_FORWARDED_FOR"] = x_forwarded_for
        return SimpleNamespace(META=meta)

    def _set_trusted_proxies(self, entries: list) -> None:
        """
        Uloží seznam důvěryhodných proxy do ``CustomAdminSettings``.

        :param entries: Seznam CIDR řetězců, IP adres nebo DNS názvů.
        """
        CustomAdminSettings.objects.update_or_create(
            item_group="pas_api",
            item_id="trusted_proxies",
            defaults={"value": json.dumps(entries)},
        )

    def test_returns_remote_addr_when_no_xff_header(self):
        """Bez hlavičky ``X-Forwarded-For`` se vrátí ``REMOTE_ADDR``."""
        self._set_trusted_proxies(["10.0.1.0/24"])
        request = self._build_request(remote_addr="10.0.1.1")

        self.assertEqual(PasApiPermissionMixin.get_client_ip(request), "10.0.1.1")

    def test_returns_remote_addr_when_no_trusted_proxies_configured(self):
        """Bez nastavení ``trusted_proxies`` se ``X-Forwarded-For`` ignoruje a vrátí se ``REMOTE_ADDR``."""
        request = self._build_request(remote_addr="10.0.1.1", x_forwarded_for="203.0.113.5")

        self.assertEqual(PasApiPermissionMixin.get_client_ip(request), "10.0.1.1")

    def test_returns_client_ip_from_xff_skipping_trusted_proxy(self):
        """Poslední nedůvěryhodná IP v XFF řetězu je identifikována jako klientská IP."""
        self._set_trusted_proxies(["10.0.1.0/24"])
        # XFF: klient → proxy mimo naši síť → naše proxy (10.0.1.1)
        request = self._build_request(remote_addr="10.0.1.1", x_forwarded_for="203.0.113.5, 10.0.1.2")

        self.assertEqual(PasApiPermissionMixin.get_client_ip(request), "203.0.113.5")

    def test_xff_spoofing_is_ignored(self):
        """Injektovaná IP na začátku XFF řetězu nemůže předstírat identitu klienta."""
        self._set_trusted_proxies(["10.0.1.0/24"])
        # Útočník přidá falešnou IP na začátek; naše proxy přidá skutečnou klientskou IP za ní.
        request = self._build_request(
            remote_addr="10.0.1.1",
            x_forwarded_for="1.2.3.4, 203.0.113.5, 10.0.1.2",
        )

        self.assertEqual(PasApiPermissionMixin.get_client_ip(request), "203.0.113.5")

    def test_returns_remote_addr_when_all_xff_ips_are_trusted(self):
        """Pokud jsou všechny IP v XFF řetězu důvěryhodné, vrátí se ``REMOTE_ADDR``."""
        self._set_trusted_proxies(["10.0.1.0/24"])
        request = self._build_request(remote_addr="10.0.1.1", x_forwarded_for="10.0.1.2, 10.0.1.3")

        self.assertEqual(PasApiPermissionMixin.get_client_ip(request), "10.0.1.1")

    def test_single_trusted_proxy_cidr_exact_match(self):
        """Přesná IP adresa v CIDR rozsahu důvěryhodných proxy je přeskočena."""
        self._set_trusted_proxies(["172.16.0.1/32"])
        request = self._build_request(remote_addr="172.16.0.1", x_forwarded_for="203.0.113.99")

        self.assertEqual(PasApiPermissionMixin.get_client_ip(request), "203.0.113.99")

    def test_untrusted_remote_addr_without_xff_is_returned_directly(self):
        """``REMOTE_ADDR`` mimo důvěryhodný rozsah bez XFF hlavičky je vráceno jako klientská IP."""
        self._set_trusted_proxies(["10.0.1.0/24"])
        request = self._build_request(remote_addr="203.0.113.5")

        self.assertEqual(PasApiPermissionMixin.get_client_ip(request), "203.0.113.5")

    def test_validate_trusted_proxies_accepts_valid_list(self):
        """Validní seznam CIDR rozsahů projde validací."""
        self.assertTrue(PasApiPermissionMixin.validate_trusted_proxies(["10.0.1.0/24", "192.168.0.1"]))

    def test_validate_trusted_proxies_accepts_hostname(self):
        """DNS název (bez lomítka a bez čistě číselného tvaru) je přijat bez DNS lookup."""
        self.assertTrue(PasApiPermissionMixin.validate_trusted_proxies(["proxy"]))

    def test_validate_trusted_proxies_raises_for_non_list(self):
        """``trusted_proxies`` musí být seznam."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_trusted_proxies.not_a_list",
        ):
            PasApiPermissionMixin.validate_trusted_proxies("10.0.1.0/24")

    def test_validate_trusted_proxies_raises_for_empty_string_entry(self):
        """Prázdný řetězec v seznamu ``trusted_proxies`` je odmítnut."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_trusted_proxies.invalid_entry",
        ):
            PasApiPermissionMixin.validate_trusted_proxies([""])

    def test_validate_trusted_proxies_raises_for_invalid_cidr(self):
        """Neplatný CIDR řetězec v ``trusted_proxies`` je odmítnut."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_trusted_proxies.invalid_cidr",
        ):
            PasApiPermissionMixin.validate_trusted_proxies(["999.999.999.999/24"])

    def test_custom_admin_setting_full_clean_allows_valid_trusted_proxies(self):
        """Validní ``trusted_proxies`` projdou ``full_clean()`` a lze je uložit."""
        instance = CustomAdminSettings(
            item_group="pas_api",
            item_id="trusted_proxies",
            value=json.dumps(["10.0.1.0/24", "proxy"]),
        )

        instance.full_clean()
        instance.save()

        self.assertTrue(
            CustomAdminSettings.objects.filter(
                item_group="pas_api",
                item_id="trusted_proxies",
            ).exists()
        )

    def test_custom_admin_setting_full_clean_raises_for_invalid_trusted_proxies(self):
        """``full_clean()`` odmítne nevalidní ``trusted_proxies``."""
        instance = CustomAdminSettings(
            item_group="pas_api",
            item_id="trusted_proxies",
            value=json.dumps(["999.999.999.999/24"]),
        )

        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_trusted_proxies.invalid_cidr",
        ):
            instance.full_clean()

    def test_get_trusted_proxies_returns_default_when_not_configured(self):
        """Bez nastavení ``trusted_proxies`` se vrátí výchozí prázdný seznam."""
        self.assertEqual(PasApiPermissionMixin.get_trusted_proxies(), [])

    def test_get_trusted_proxies_returns_configured_value(self):
        """Nastavená hodnota ``trusted_proxies`` je vrácena z cache nebo databáze."""
        self._set_trusted_proxies(["192.168.0.0/16"])

        self.assertEqual(PasApiPermissionMixin.get_trusted_proxies(), ["192.168.0.0/16"])

    def test_resolve_trusted_networks_dns_failure_is_logged_and_skipped(self):
        """Neúspěšný DNS lookup je zalogován a daná položka je přeskočena."""
        with patch("pas.api.socket.getaddrinfo", side_effect=OSError("DNS failure")):
            with self.assertLogs("pas.api", level="WARNING") as log_ctx:
                networks = PasApiPermissionMixin._resolve_trusted_networks(["nonexistent.internal"])

        self.assertEqual(networks, [])
        self.assertTrue(
            any("pas.api.PasApiPermissionMixin._resolve_trusted_networks.dns_failed" in line for line in log_ctx.output)
        )

    # --- IPv6 ---

    def test_validate_trusted_proxies_accepts_ipv6_cidr(self):
        """IPv6 CIDR prefix projde validací ``trusted_proxies``."""
        self.assertTrue(PasApiPermissionMixin.validate_trusted_proxies(["2001:db8::/32"]))

    def test_validate_trusted_proxies_accepts_ipv6_address(self):
        """Jednotlivá IPv6 adresa projde validací ``trusted_proxies``."""
        self.assertTrue(PasApiPermissionMixin.validate_trusted_proxies(["::1"]))

    def test_validate_trusted_proxies_raises_for_invalid_ipv6_cidr(self):
        """Neplatný IPv6 CIDR prefix v ``trusted_proxies`` je odmítnut."""
        with self.assertRaisesRegex(
            ValidationError,
            "pas.api.PasApiPermissionMixin.validate_trusted_proxies.invalid_cidr",
        ):
            PasApiPermissionMixin.validate_trusted_proxies(["2001:db8::/200"])

    def test_get_client_ip_skips_ipv6_trusted_proxy(self):
        """IPv6 proxy v ``trusted_proxies`` je přeskočena a vrátí se klientská IP z XFF."""
        self._set_trusted_proxies(["::1"])
        request = self._build_request(remote_addr="::1", x_forwarded_for="2001:db8::cafe")

        self.assertEqual(PasApiPermissionMixin.get_client_ip(request), "2001:db8::cafe")
