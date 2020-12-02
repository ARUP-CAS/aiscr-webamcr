from django.core.exceptions import ValidationError
from django.test import TestCase

from .validators import validate_phone_number


class ValidatorTestCase(TestCase):

    def test_validate_phone_number(self):
        # Valid phone numbers
        valid_numbers = ['+420 777 777 777', '+421098789876', '777000000', '1234567890']
        invalid_numbers = ['a12312312', '+420', '', '00420777888111']
        try:
            for number in valid_numbers:
                validate_phone_number(number)
        except ValidationError:
            self.fail("Valid numbers should not raise exceptions")

        for number in invalid_numbers:
            print(number)
            self.assertRaises(ValidationError, validate_phone_number, number)
