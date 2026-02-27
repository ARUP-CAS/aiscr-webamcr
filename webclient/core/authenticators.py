from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class AMCRAuthUser(ModelBackend):
    """
    Třída pro určení jestli se uživatel múže prihlásit. kontroluje se pole is_active na uživatelovi.
    """

    def user_can_authenticate(self, user):
        """Provádí operaci user can authenticate.

        :param user: Vstupní hodnota ``user`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if user.is_active:
            return True
        else:
            raise ValidationError(
                (_("core.authenticators.user_can_authenticate")),
                code="inactive",
            )
