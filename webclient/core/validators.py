import logging
import re
from datetime import datetime

import phonenumbers
from django.core.exceptions import ValidationError
from django.db.backends.postgresql.psycopg_any import DateRange
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


orcid_pattern = re.compile(r"\d{4}-\d{4}-\d{4}-\d{4}")


def validate_phone_number(number):
    """
    Validátor pro ověření telefonního čísla na správny formát.
    """
    regex_tel = re.compile(r"[\s\d\+\-\(+\)]+")
    if not regex_tel.fullmatch(number):
        logger.info("Phone provided contains not allowed characters", extra={"value": number})
        raise ValidationError(_("core.validators.validate_phone_number.not_valid.symbols"))
    try:
        parsed_tel = phonenumbers.parse(number, "CZ")
    except Exception as e:
        logger.info("Phone provided is not valid telephone number", extra={"exception": e})
        raise ValidationError(_("core.validators.validate_phone_number.not_valid.number"))
    if not phonenumbers.is_valid_number(parsed_tel):
        logger.info("Phone provided is not valid telephone number", extra={"value": parsed_tel})
        raise ValidationError(_("core.validators.validate_phone_number.not_valid.number"))


def validate_date_min_1600(value):
    """Funkce `validate_date_min_1600` v modulu `webclient.core.validators`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param value: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    min_date = datetime(1600, 1, 1).date()
    if isinstance(value, DateRange):
        if value.lower <= min_date:
            raise ValidationError(_("core.validators.validate_date_min_1600.not_valid_lower"))
        elif value.upper <= min_date:
            raise ValidationError(_("core.validators.validate_date_min_1600.not_valid_upper"))
    elif value and value <= min_date:
        raise ValidationError(_("core.validators.validate_date_min_1600.not_valid"))
