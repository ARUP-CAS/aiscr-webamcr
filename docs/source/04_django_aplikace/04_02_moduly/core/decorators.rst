CORE decorators
===============

Modul decorators.

Přehled modulu
--------------

Sdílené dekorátory pro řízení přístupu a režimu odstávky.

Funkce
------

.. py:function:: allowed_user_groups(allowed_groups)

   Omezí přístup k pohledu pouze na vybrané hlavní uživatelské role.

   Na vstupe je list povolených uživatelských skupin.
   Jestli uživatel nemá jesnou z daných skupin jako hlavní tak funkce vráti exception PermissionError a nezobrazí formulár.

   :param allowed_groups: Seznam nebo množina ID povolených hlavních rolí (skupin), jimž je přístup povolen.

       :return: Vrací proměnná ``_method_wrapper``.

.. py:function:: odstavka_in_progress(view_func)

   Při aktivní odstávce vrátí stránku údržby namísto cílového pohledu.

   :param view_func: View funkce obalená dekorátorem nebo middlewarem.

       :return: Vrací proměnná ``wrapper``.
