CORE authenticators
===================

Modul authenticators.

Třídy
------

.. py:class:: AMCRAuthUser

   Třída pro určení jestli se uživatel múže prihlásit. kontroluje se pole is_active na uživatelovi.

   **Metody:**

   .. py:method:: authenticate()

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

