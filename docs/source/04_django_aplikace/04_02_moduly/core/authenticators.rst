CORE authenticators
===================

Modul authenticators.

Třídy
------

.. py:class:: AMCRAuthUser

   Třída pro určení jestli se uživatel múže prihlásit. kontroluje se pole is_active na uživatelovi.

   **Metody:**

   .. py:method:: user_can_authenticate()

      Vrací vždy True. Validace na is_active byla přesunuta do formuláře na login a do middleware pro přihlášeného uživatele.

      :param user: Uživatelský objekt.
      :return: Vždy vrací True, aby bylo umožněno ověření všem uživatelům.

