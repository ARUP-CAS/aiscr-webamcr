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

      :param user: Parametr ``user`` pracuje se s atributy ``is_active``, ovlivňuje větvení podmínek.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
      :raises ValidationError: Vyvolá se při splnění podmínky ``user.is_active``.

