CORE import_maintenance
=======================

Modul import_maintenance.

Přehled modulu
--------------

Ochrana probíhající odstávky před ukončením během hromadného importu.

Třídy
------

.. py:class:: MaintenanceImportConflict

   Odmítnutí změny odstávky, která by zpřístupnila aplikaci během importu.


Funkce
------

.. py:function:: lock_maintenance_configuration()

   Zamkne konfiguraci odstávky do konce transakce volajícího.

   :return: Aktuální řádky odstávky; stejný zámek používá upload i administrace odstávky.

.. py:function:: maintenance_is_active(maintenance)

   Vyhodnotí řádek odstávky bez cache podle stávajících pravidel aplikace.

   :param maintenance: Uložená nebo navrhovaná konfigurace odstávky.
   :return: Zda je odstávka zapnutá, zveřejněná a její začátek již nastal.

.. py:function:: import_is_protected()

   Zjistí, zda Redis eviduje aktivní nebo nedokončený import.

   :return: ``True``, pokud import drží lock nebo jeho aktivní ukazatel není v terminální fázi.
   :raises MaintenanceImportConflict: Stav importu nelze bezpečně ověřit.

.. py:function:: ensure_maintenance_change_allowed(current, replacement, import_protected)

   Odmítne ukončení aktivní odstávky, pokud import ještě drží ochranu.

   Volající musí držet zámek konfigurace až do uložení nebo smazání odstávky.

   :param current: Aktuální zamčený řádek odstávky.
   :param replacement: Navrhovaná konfigurace; ``None`` znamená smazání.
   :param import_protected: Předem načtený stav ochrany importu; bez hodnoty se načte z Redis.
   :raises MaintenanceImportConflict: Import běží nebo nelze jeho stav bezpečně ověřit.

.. py:function:: acquire_import_lock_during_maintenance(connection, token, ttl_seconds)

   Ověří odstávku a získá importní lock atomicky vůči změnám její konfigurace.

   :param connection: Dekódující Redis spojení importního formuláře.
   :param token: Vlastnický token nového importu.
   :param ttl_seconds: Doba platnosti importního locku.
   :return: ``True`` při získání locku, ``False`` při obsazeném slotu, ``None`` bez odstávky.
