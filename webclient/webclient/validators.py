import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_phone_number(number):
    number = number.replace(" ", "")
    SVK = '+421'
    CZE = '+420'
    is_valid = False
    r = re.compile('[0-9]+')
    # With country code
    if number.startswith(SVK) or number.startswith(CZE):
        rest = number[4:]  # Without the country code
        if len(rest) == 9 and r.match(rest):
            # +421 907 452 325 or +420 722 803 058
            is_valid = True
        # 0907 452 325 or 722 803 058
    # Without country code
    elif len(number) == 10 or len(number) == 9 and r.match(number):
        is_valid = True

    if not is_valid:
        raise ValidationError(
            _('%(value)s nesprávný formát čísla. Musí být: +420xxxxxxxxx'),
            params={'value': number},
        )
