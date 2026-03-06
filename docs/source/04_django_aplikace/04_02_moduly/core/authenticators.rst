CORE authenticators
===================

Modul authenticators.

Třídy
------

.. py:class:: AMCRAuthUser

   Třída pro určení jestli se uživatel múže prihlásit. kontroluje se pole is_active na uživatelovi.

   **Metody:**

   .. py:method:: user_can_authenticate()

      Provádí operaci user can authenticate.

      :param user: Uživatel, v jehož kontextu se operace provádí.

