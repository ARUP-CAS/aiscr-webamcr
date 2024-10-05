import logging
import re

import phonenumbers
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def validate_phone_number(number):
    """
    Validátor pro ověření telefonního čísla na správny formát.
    """
    regex_tel = re.compile(r"[\s\d\+\-\(+\)]+")
    if not regex_tel.fullmatch(number):
        logger.info("Phone provided contains not allowed characters", extra={"phone number": number})
        raise ValidationError(_("core.validators.validate_phone_number.not_valid.symbols"))
    try:
        parsed_tel = phonenumbers.parse(number, "CZ")
    except Exception as e:
        logger.info("Phone provided is not valid telephone number", extra={"exception": e})
        raise ValidationError(_("core.validators.validate_phone_number.not_valid.number"))
    if not phonenumbers.is_valid_number(parsed_tel):
        logger.info("Phone provided is not valid telephone number", extra={"parsed tel:": parsed_tel})
        raise ValidationError(_("core.validators.validate_phone_number.not_valid.number"))
