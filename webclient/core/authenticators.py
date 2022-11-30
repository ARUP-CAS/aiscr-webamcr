from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError


class AMCRAuthUser(ModelBackend):
    def user_can_authenticate(self, user):
        if user.is_active:
            return True
        else:
            raise ValidationError(
                (
                    "Účet ješte nebyl aktivován. Pokud ste ho už aktivoval přes link v emailu, vyčkejte prosím na potvrzovací email od admina."
                ),
                code="inactive",
            )
