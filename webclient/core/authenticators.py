from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class AMCRAuthUser(ModelBackend):
    """
    Třída pro určení jestli se uživatel múže prihlásit. kontroluje se pole is_active na uživatelovi.
    """

    def user_can_authenticate(self, user):
        """
        Ověří, zda se uživatel může přihlásit; vrátí True, nebo vyvolá ValidationError, pokud je neaktivní.

        :param user: Uživatelský objekt, jehož atribut ``is_active`` se ověřuje.

            :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
            :raises ValidationError: Vyvolá se při splnění podmínky ``user.is_active``.
        """
        if user.is_active:
            return True
        else:
            raise ValidationError(
                (_("core.authenticators.user_can_authenticate")),
                code="inactive",
            )
