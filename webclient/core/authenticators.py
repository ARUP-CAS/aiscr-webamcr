from django.contrib.auth.backends import ModelBackend


class AMCRAuthUser(ModelBackend):
    """
    Třída pro určení jestli se uživatel múže prihlásit. kontroluje se pole is_active na uživatelovi.
    """

    def user_can_authenticate(self, user):
        """
        Vrací vždy True. Validace na is_active byla přesunuta do formuláře na login a do middleware pro přihlášeného uživatele.

        :param user: Uživatelský objekt.
        :return: Vždy vrací True, aby bylo umožněno ověření všem uživatelům.
        """
        return True
