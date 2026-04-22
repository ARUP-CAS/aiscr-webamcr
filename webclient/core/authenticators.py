from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class AMCRAuthUser(ModelBackend):
    """
    Třída pro určení jestli se uživatel múže prihlásit. kontroluje se pole is_active na uživatelovi.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Ověří přihlašovací údaje uživatele.

        Pokud jsou přihlašovací údaje správné, ale účet není aktivní, vyvolá
        ``ValidationError`` s kódem ``inactive``, aby bylo možné zobrazit
        srozumitelnou chybovou zprávu v přihlašovacím formuláři.

        :param request: HTTP požadavek.
        :param username: Přihlašovací jméno uživatele.
        :param password: Heslo uživatele.
        :param kwargs: Dodatečné argumenty; může obsahovat ``USERNAME_FIELD`` jako klíč.
        :return: Instance uživatele při úspěšném ověření, jinak ``None``.
        :raises ValidationError: Vyvolá se pokud jsou přihlašovací údaje správné,
                                 ale účet není aktivní.
        """
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            # Spustit hashování hesla jednou, aby se snížil časový rozdíl
            # mezi existujícím a neexistujícím uživatelem.
            UserModel().set_password(password)
            return None
        if not user.check_password(password):
            return None
        if not user.is_active:
            raise ValidationError(
                _("core.authenticators.user_can_authenticate"),
                code="inactive",
            )
        return user
