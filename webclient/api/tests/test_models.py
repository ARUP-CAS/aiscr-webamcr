"""
Testy modelu ``ApiRequestLog`` — zejména ``pre_save`` validace pro PAS cíle.

Validátor ``validate_pas_request_target_fields`` (``api/signals.py``) musí:

* propustit záznamy s ne-PAS ``request_target`` bez ohledu na ostatní pole,
* propustit záznamy ve stavech ``received`` / ``processing`` / ``failure``
  i bez ``ident_cely`` a ``samostatny_nalez`` (failure cíleně netriggeruje
  kontrolu, viz docstring v ``signals.py``),
* vyhodit ``ValidationError`` pro PAS cíl ve stavu ``success``,
  pokud chybí ``ident_cely`` nebo ``samostatny_nalez``,
* propustit PAS cíl ve stavu ``success``, jsou-li obě pole vyplněna.

Validátor se volá přímo jako funkce, aby testy nemusely vytvářet skutečné
``SamostatnyNalez`` (FK na řadu dalších modelů) a aby nezávisely na DB.
"""

from api.models import ApiRequestLog
from api.signals import validate_pas_request_target_fields
from core.constants import (
    API_REQUEST_LOG_STATUS_FAILURE,
    API_REQUEST_LOG_STATUS_PROCESSING,
    API_REQUEST_LOG_STATUS_RECEIVED,
    API_REQUEST_LOG_STATUS_SUCCESS,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_EVIDENCNI_CISLO_PATCH,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_FOTOGRAFIE_UPLOAD,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_XML_IMPORT,
)
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase


def _make_log(**overrides) -> ApiRequestLog:
    """Sestaví in-memory instanci ``ApiRequestLog`` pro test (bez DB)."""
    defaults = {
        "client_ip": "127.0.0.1",
        "request_target": API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_XML_IMPORT,
        "status": API_REQUEST_LOG_STATUS_RECEIVED,
        "ident_cely": None,
    }
    defaults.update(overrides)
    log = ApiRequestLog(**defaults)
    # Obejít FK validaci nastavením jen ID; samotný objekt SamostatnyNalez neexistuje,
    # což je v pořádku, protože voláme signal handler přímo bez .save().
    log.samostatny_nalez_id = overrides.get("samostatny_nalez_id")
    return log


def _call_validator(log: ApiRequestLog) -> None:
    """Spustí pre_save validátor přímo, bez Django save() / DB."""
    validate_pas_request_target_fields(ApiRequestLog, log)


class ValidatePasRequestTargetFieldsTests(SimpleTestCase):
    """Pokrytí signál handleru ``validate_pas_request_target_fields``."""

    PAS_TARGETS = [
        API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_XML_IMPORT,
        API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_EVIDENCNI_CISLO_PATCH,
        API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_FOTOGRAFIE_UPLOAD,
    ]
    NON_TRIGGERING_STATUSES = [
        API_REQUEST_LOG_STATUS_RECEIVED,
        API_REQUEST_LOG_STATUS_PROCESSING,
        API_REQUEST_LOG_STATUS_FAILURE,
    ]

    def test_non_pas_target_passes_even_when_fields_missing(self):
        """Ne-PAS ``request_target`` neaktivuje kontrolu."""
        log = _make_log(
            request_target="other_universal_target",
            status=API_REQUEST_LOG_STATUS_SUCCESS,
            ident_cely=None,
            samostatny_nalez_id=None,
        )
        _call_validator(log)  # nesmí vyhodit

    def test_non_triggering_statuses_pass_for_pas_target_without_fields(self):
        """Stavy ``received``, ``processing`` a ``failure`` netriggerují kontrolu ani pro PAS cíl."""
        for target in self.PAS_TARGETS:
            for status_value in self.NON_TRIGGERING_STATUSES:
                with self.subTest(target=target, status=status_value):
                    log = _make_log(
                        request_target=target,
                        status=status_value,
                        ident_cely=None,
                        samostatny_nalez_id=None,
                    )
                    _call_validator(log)  # nesmí vyhodit

    def test_success_pas_target_missing_both_fields_raises(self):
        """PAS cíl + ``success`` + obě chybějící pole → ``ValidationError`` s oběma klíči."""
        for target in self.PAS_TARGETS:
            with self.subTest(target=target):
                log = _make_log(
                    request_target=target,
                    status=API_REQUEST_LOG_STATUS_SUCCESS,
                    ident_cely=None,
                    samostatny_nalez_id=None,
                )
                with self.assertRaises(ValidationError) as ctx:
                    _call_validator(log)
                self.assertIn("ident_cely", ctx.exception.message_dict)
                self.assertIn("samostatny_nalez", ctx.exception.message_dict)

    def test_success_pas_target_missing_only_ident_cely_raises(self):
        """Chybí pouze ``ident_cely`` → ``ValidationError`` jen pro ``ident_cely``."""
        log = _make_log(
            request_target=API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_EVIDENCNI_CISLO_PATCH,
            status=API_REQUEST_LOG_STATUS_SUCCESS,
            ident_cely=None,
            samostatny_nalez_id=42,
        )
        with self.assertRaises(ValidationError) as ctx:
            _call_validator(log)
        self.assertIn("ident_cely", ctx.exception.message_dict)
        self.assertNotIn("samostatny_nalez", ctx.exception.message_dict)

    def test_success_pas_target_missing_only_samostatny_nalez_raises(self):
        """Chybí pouze ``samostatny_nalez`` → ``ValidationError`` jen pro ten klíč."""
        log = _make_log(
            request_target=API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_FOTOGRAFIE_UPLOAD,
            status=API_REQUEST_LOG_STATUS_SUCCESS,
            ident_cely="M-202400001-N00001",
            samostatny_nalez_id=None,
        )
        with self.assertRaises(ValidationError) as ctx:
            _call_validator(log)
        self.assertIn("samostatny_nalez", ctx.exception.message_dict)
        self.assertNotIn("ident_cely", ctx.exception.message_dict)

    def test_success_pas_target_with_both_fields_passes(self):
        """PAS cíl + ``success`` + obě pole vyplněná → validace projde."""
        for target in self.PAS_TARGETS:
            with self.subTest(target=target):
                log = _make_log(
                    request_target=target,
                    status=API_REQUEST_LOG_STATUS_SUCCESS,
                    ident_cely="M-202400001-N00001",
                    samostatny_nalez_id=7,
                )
                _call_validator(log)  # nesmí vyhodit

    def test_failure_pas_target_missing_fields_passes(self):
        """PAS cíl + ``failure`` + chybějící pole → validace cíleně projde (early-abort flow)."""
        for target in self.PAS_TARGETS:
            with self.subTest(target=target):
                log = _make_log(
                    request_target=target,
                    status=API_REQUEST_LOG_STATUS_FAILURE,
                    ident_cely=None,
                    samostatny_nalez_id=None,
                )
                _call_validator(log)  # nesmí vyhodit

    def test_empty_string_ident_cely_treated_as_missing(self):
        """Prázdný řetězec ``ident_cely`` je rovnocenný ``None`` (falsy hodnota)."""
        log = _make_log(
            request_target=API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_XML_IMPORT,
            status=API_REQUEST_LOG_STATUS_SUCCESS,
            ident_cely="",
            samostatny_nalez_id=1,
        )
        with self.assertRaises(ValidationError) as ctx:
            _call_validator(log)
        self.assertIn("ident_cely", ctx.exception.message_dict)
