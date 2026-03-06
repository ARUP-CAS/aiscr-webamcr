CORE decorators
===============

Modul decorators.

Funkce
------

.. py:function:: allowed_user_groups(allowed_groups)

   Omezí přístup k pohledu pouze na vybrané hlavní uživatelské role.

   :param allowed_groups: Typová nebo konfigurační hodnota `allowed_groups` určující cílovou logiku.

.. py:function:: odstavka_in_progress(view_func)

   Při aktivní odstávce vrátí stránku údržby namísto cílového pohledu.

   :param view_func: View funkce obalená dekorátorem nebo middlewarem.
