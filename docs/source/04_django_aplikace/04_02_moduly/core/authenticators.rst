CORE authenticators
===================

Modul authenticators.

Třídy
------

.. py:class:: AMCRAuthUser

   Třída pro určení jestli se uživatel múže prihlásit. kontroluje se pole is_active na uživatelovi.

   **Metody:**

   .. py:method:: user_can_authenticate()

      Ověří, zda se uživatel může přihlásit; vrátí True, nebo vyvolá ValidationError, pokud je neaktivní.

      **Parametry:**

      - ``user``: Uživatelský objekt, jehož atribut ``is_active`` se ověřuje.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

      **Výjimky:**

      - ``ValidationError``: Vyvolá se při splnění podmínky ``user.is_active``.


