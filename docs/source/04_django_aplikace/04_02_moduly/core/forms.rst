CORE formuláře
==============

Definice formulářů.

Třídy
------

.. py:class:: SelectMultipleSeparator

   Override nad widgetom na zobrazení multi selectu stejně v každém formuláři.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: TwoLevelSelectField

   Potrebná úprava metód pro Charfield ve formuláři, pokud se používa widget se zobrazením dvou-stupňového seznamu.

   **Metody:**

   .. py:method:: to_python()

   .. py:method:: has_changed()


.. py:class:: HeslarChoiceFieldField

   Potrebná úprava metód pro ChoiceField ve formuláři, pro správně zobrazení a spracováni predmetu specifikace.

   **Metody:**

   .. py:method:: clean()

   .. py:method:: to_python()

   .. py:method:: has_changed()


.. py:class:: CheckStavNotChangedForm

   Formulář pro kontrolu jestli se stav záznamu nezmenil mezi jeho načtením a odeslánim zmeny.
Celá logika je v clean metóde.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: clean()


.. py:class:: VratitForm

   Formulář pro vrácení záznamu. Obsahuje jen text pole pro zdůvodnění vrácení.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: VratitFormDokument

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: VratitFormAZ

   Formulář pro vrácení záznamu Akce nebo Lokality. Obsahuje text pole pro zdůvodnění vrácení a výběr dokumentů pro vrácení.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: DecimalTextWideget

   Třida pro formátování hodnoty velikosti souboru na 3 desetiná místa.

   **Metody:**

   .. py:method:: format_value()


.. py:class:: OdstavkaSystemuForm

   Formulář pro nastavení a úpravu odstávky.
Vrámci načítáni formuláře se doplní načítají hodnoty z template odstávky.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: PermissionImportForm

   Popis není k dispozici.


.. py:class:: PermissionSkipImportForm

   Popis není k dispozici.


.. py:class:: BaseFilterForm

   Popis není k dispozici.

   **Metody:**

   .. py:method:: clean()


.. py:class:: TransaltionImportForm

   Popis není k dispozici.

   **Metody:**

   .. py:method:: clean()


.. py:class:: ImportDataAdminForm

   Popis není k dispozici.

