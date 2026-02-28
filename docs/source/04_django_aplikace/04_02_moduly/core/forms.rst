CORE formuláře
==============

Definice formulářů.

Třídy
------

.. py:class:: SelectMultipleSeparator

   Override nad widgetom na zobrazení multi selectu stejně v každém formuláři.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param attrs: Vstupní hodnota ``attrs`` pro danou operaci.
      :param choices: Vstupní hodnota ``choices`` pro danou operaci.


.. py:class:: TwoLevelSelectField

   Potrebná úprava metód pro Charfield ve formuláři, pokud se používa widget se zobrazením dvou-stupňového seznamu.

   **Metody:**

   .. py:method:: to_python()

      Provádí operaci to python.

      :param selected_value: Vstupní hodnota ``selected_value`` pro danou operaci.

   .. py:method:: has_changed()

      Určí, zda changed.

      :param initial: Vstupní hodnota ``initial`` pro danou operaci.
      :param data: Vstupní hodnota ``data`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: HeslarChoiceFieldField

   Potrebná úprava metód pro ChoiceField ve formuláři, pro správně zobrazení a spracováni predmetu specifikace.

   **Metody:**

   .. py:method:: clean()

      Provádí operaci clean.

      :param selected_value: Vstupní hodnota ``selected_value`` pro danou operaci.

   .. py:method:: to_python()

      Provádí operaci to python.

      :param selected_value: Vstupní hodnota ``selected_value`` pro danou operaci.

   .. py:method:: has_changed()

      Určí, zda changed.

      :param initial: Vstupní hodnota ``initial`` pro danou operaci.
      :param data: Vstupní hodnota ``data`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: CheckStavNotChangedForm

   Formulář pro kontrolu jestli se stav záznamu nezmenil mezi jeho načtením a odeslánim zmeny.

   Celá logika je v clean metóde.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param db_stav: Vstupní hodnota ``db_stav`` pro danou operaci.
      :param require_confirmation: Vstupní hodnota ``require_confirmation`` pro danou operaci.
      :param dokument_warnings: Vstupní hodnota ``dokument_warnings`` pro danou operaci.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: clean()

      Provádí operaci clean.


.. py:class:: VratitForm

   Formulář pro vrácení záznamu. Obsahuje jen text pole pro zdůvodnění vrácení.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: VratitFormDokument

   Implementuje komponentu ``VratitFormDokument`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: VratitFormAZ

   Formulář pro vrácení záznamu Akce nebo Lokality. Obsahuje text pole pro zdůvodnění vrácení a výběr dokumentů pro vrácení.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param az: Vstupní hodnota ``az`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DecimalTextWideget

   Třida pro formátování hodnoty velikosti souboru na 3 desetiná místa.

   **Metody:**

   .. py:method:: format_value()

      Provádí operaci format value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.


.. py:class:: OdstavkaSystemuForm

   Formulář pro nastavení a úpravu odstávky.

   Vrámci načítáni formuláře se doplní načítají hodnoty z template odstávky.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: PermissionImportForm

   Implementuje komponentu ``PermissionImportForm`` v rámci aplikace.


.. py:class:: PermissionSkipImportForm

   Implementuje komponentu ``PermissionSkipImportForm`` v rámci aplikace.


.. py:class:: BaseFilterForm

   Implementuje komponentu ``BaseFilterForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: clean()

      Provádí operaci clean.


.. py:class:: TransaltionImportForm

   Implementuje komponentu ``TransaltionImportForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: clean()

      Provádí operaci clean.


.. py:class:: ImportDataAdminForm

   Implementuje komponentu ``ImportDataAdminForm`` v rámci aplikace.

