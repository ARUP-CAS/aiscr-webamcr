CORE setting_models
===================

Modul setting_models.

Třídy
------

.. py:class:: CustomAdminSettings

   Implementuje komponentu ``CustomAdminSettings`` v rámci aplikace.

   **Metody:**

   .. py:method:: clean()

      Ověří konzistenci hodnoty nastavení před validací formuláře a uložením.

      Pro skupinu ``pas_api`` deleguje validaci na helper v aplikaci PAS, aby se stejná
      pravidla používala v administraci i za běhu API.

      :raises ValidationError: Pokud hodnota nastavení neodpovídá očekávanému formátu.

