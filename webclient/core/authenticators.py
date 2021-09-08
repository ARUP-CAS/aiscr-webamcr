from core.constants import ROLE_NEAKTIVNI_UZIVATEL_ID
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError


class AMCRAuthUser(ModelBackend):
    def user_can_authenticate(self, user):
        if user.hlavni_role.id != ROLE_NEAKTIVNI_UZIVATEL_ID and user.is_active:
            return True
        else:
            raise ValidationError(
                (
                    "Účet ješte nebyl aktivován. Pokud ste ho už aktivoval přes link v emailu, vyčkejte prosím na potvrzovací email od admina."
                ),
                code="inactive",
            )
