CORE services
=============

Modul services.

Přehled modulu
--------------

Import zdrojové matice uživatelských oprávnění.

Třídy
------

.. py:class:: PermissionService

   Načte, ověří a atomicky nahradí matici oprávnění.

   **Metody:**

   .. py:method:: run()

      Ověří soubor před nahrazením záznamů a zachová původní kompakci.

      :param docfile: Nahraný CSV nebo XLSX soubor s úplnou maticí oprávnění.
      :return: Přehled zpracovaných řádků a prázdný seznam chybějících URL.
      :raises PermissionPolicyError: Při neplatné matici nebo neúspěšném importu.

   .. py:method:: _compact_unrestricted_permissions()

      Odstraní stejné neomezené záznamy jako původní import.

