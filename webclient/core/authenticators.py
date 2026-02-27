from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class AMCRAuthUser(ModelBackend):
    """
    Třída pro určení jestli se uživatel múže prihlásit. kontroluje se pole is_active na uživatelovi.
    """

    def user_can_authenticate(self, user):
        """Zajišťuje logiku funkce ``user_can_authenticate``.
        
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        if user.is_active:
            return True
        else:
            raise ValidationError(
                (_("core.authenticators.user_can_authenticate")),
                code="inactive",
            )
