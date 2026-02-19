CORE decorators
===============

Modul decorators.

Funkce
------

.. py:function:: allowed_user_groups(allowed_groups)

   Omezí přístup k pohledu pouze na vybrané hlavní uživatelské role.


   **Argumenty:**

   - ``allowed_groups``: Seznam ID rolí, které mohou pohled vykonat.

.. py:function:: odstavka_in_progress(view_func)

   Při aktivní odstávce vrátí stránku údržby namísto cílového pohledu.
