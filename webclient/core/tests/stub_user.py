"""Sdílená náhrada uživatele pro jednotkové testy importních view a administrace."""


class _StubUser:
    """Poskytuje identitu a příznaky oprávnění bez přístupu do databáze."""

    def __init__(self, user_id, is_superuser=True):
        """Nastaví aktivního přihlášeného uživatele pro požadavky z RequestFactory.

        :param user_id: Hodnota ``id`` a ``pk`` porovnávaná s vlastníkem importní úlohy.
        :param is_superuser: Zda uživatel splňuje superuživatelskou bránu importních view.
        """
        self.id = user_id
        self.pk = user_id
        self.is_superuser = is_superuser
        self.is_staff = True
        self.is_active = True
        self.is_authenticated = True
