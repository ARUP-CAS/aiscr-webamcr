CORE decorators
===============

Modul decorators.

Funkce
------

.. py:function:: allowed_user_groups(allowed_groups)

   Dekorátor funkce použitý nad pohledem, na kontrolu práv uživatele na daný pohled.
   Na vstupe je list povolených uživatelských skupin.
   Jestli uživatel nemá jesnou z daných skupin jako hlavní tak funkce vráti exception PermissionError a nezobrazí formulár.

.. py:function:: odstavka_in_progress(view_func)

   Dekorátor funkce použitý nad pohledem, na zobrazení stránky o odstávke místo stránky oznámení a prihlášení pokud je nastavená odstívka.
