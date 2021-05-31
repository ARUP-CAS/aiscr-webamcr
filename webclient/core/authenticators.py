from core.constants import ROLE_NEAKTIVNI_UZIVATEL_ID
from django.contrib.auth.backends import ModelBackend


class AMCRAuthUser(ModelBackend):
    def user_can_authenticate(self, user):
        return user.hlavni_role.id != ROLE_NEAKTIVNI_UZIVATEL_ID and user.is_active
