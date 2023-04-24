import logging
import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger('python-logstash-logger')


def validate_phone_number(number):
    number = number.replace(" ", "")
    is_valid = False
    r = re.compile("[0-9]+")
    number_range = range(5, 15)
    # With country code
    if number.startswith("+") or number.startswith("00"):
        if number.startswith("+"):
            rest = number[1:]  # Without + mark
        else:
            rest = number[2:]  # Without + mark
        if len(rest) in number_range and r.match(rest):
            # +12345 to +123451234512345
            is_valid = True
        # 0907 452 325 or 722 803 058
    # Without country code
    elif len(number) in number_range and r.match(number):
        is_valid = True

    if not is_valid:
        logger.debug(f"core.validators.validate_phone_number.not_valid", extra={"number": number})
        raise ValidationError(
            _("%(value)s nesprávný formát čísla. Musí být: +420xxxxxxxxx"),
            params={"value": number},
        )
    else:
        logger.debug(f"core.validators.validate_phone_number.valid", extra={"number": number})
