from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class AMCRAuthUser(ModelBackend):
    """
    Třída pro určení jestli se uživatel múže prihlásit. kontroluje se pole is_active na uživatelovi.
    """

    def user_can_authenticate(self, user):
        """Zpracuje volání ``AMCRAuthUser.user_can_authenticate`` v rámci modulu ``webclient.core.authenticators``."""
        if user.is_active:
            return True
        else:
            raise ValidationError(
                (_("core.authenticators.user_can_authenticate")),
                code="inactive",
            )
