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

      **Parametry:**

      - ``attrs``: Kolekce ``attrs`` zpracovávaná touto funkcí.
      - ``choices``: Parametr ``choices`` se předává do volání ``__init__()``.



.. py:class:: TwoLevelSelectField

   Potrebná úprava metód pro Charfield ve formuláři, pokud se používa widget se zobrazením dvou-stupňového seznamu.

   **Metody:**

   .. py:method:: to_python()

      Konvertuje vybranou hodnotu na Python objekt Heslar.

      **Parametry:**

      - ``selected_value``: ID vybraného hesláře.

      **Návratová hodnota:**

      Instance Heslar objektu nebo None.


   .. py:method:: has_changed()

      Určí, zda changed.

      **Parametry:**

      - ``initial``: Stavová nebo časová hodnota `initial` používaná při rozhodování logiky.
      - ``data``: Kolekce ``data`` zpracovávaná touto funkcí.

      **Návratová hodnota:**

      Vrací výsledek ověření nebo validačního pravidla.



.. py:class:: HeslarChoiceFieldField

   Potrebná úprava metód pro ChoiceField ve formuláři, pro správně zobrazení a spracováni predmetu specifikace.

   **Metody:**

   .. py:method:: clean()

      Vrátí instanci Heslar objektu nebo spustí standardní vyčištění pole.

      **Parametry:**

      - ``selected_value``: ID vybraného hesláře.

      **Návratová hodnota:**

      Instance Heslar objektu nebo výsledek ```super().clean()``.


   .. py:method:: to_python()

      Konvertuje vybranou hodnotu na Python objekt Heslar.

      **Parametry:**

      - ``selected_value``: ID vybraného hesláře.

      **Návratová hodnota:**

      Instance Heslar objektu nebo None.


   .. py:method:: has_changed()

      Určí, zda changed.

      **Parametry:**

      - ``initial``: Stavová nebo časová hodnota `initial` používaná při rozhodování logiky.
      - ``data``: Kolekce ``data`` zpracovávaná touto funkcí.

      **Návratová hodnota:**

      Vrací výsledek ověření nebo validačního pravidla.



.. py:class:: CheckStavNotChangedForm

   Formulář pro kontrolu jestli se stav záznamu nezmenil mezi jeho načtením a odeslánim zmeny.

   Celá logika je v clean metóde.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``db_stav``: Stavová hodnota načtená z databáze.
      - ``require_confirmation``: Parametr ``require_confirmation`` ovlivňuje větvení podmínek.
      - ``dokument_warnings``: Parametr ``dokument_warnings`` předává se do volání ``append()``, ``HTML()``, ovlivňuje větvení podmínek.
      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: clean()

      Ověří, že se stav záznamu nezměnil mezi načtením a odesláním.

      **Návratová hodnota:**

      Ověřená data.

      **Výjimky:**

      - ``forms.ValidationError``: Vyvolá se s textem "State_changed" pokud se stav změnil.



.. py:class:: VratitForm

   Formulář pro vrácení záznamu. Obsahuje jen text pole pro zdůvodnění vrácení.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: VratitFormDokument

   Implementuje komponentu ``VratitFormDokument`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: VratitFormAZ

   Formulář pro vrácení záznamu Akce nebo Lokality. Obsahuje text pole pro zdůvodnění vrácení a výběr dokumentů pro vrácení.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``az``: Parametr ``az`` se předává do volání ``filter()``, pracuje se s atributy ``stav``, ``ident_cely``, ovlivňuje větvení podmínek.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: DecimalTextWideget

   Třida pro formátování hodnoty velikosti souboru na 3 desetiná místa.

   **Metody:**

   .. py:method:: format_value()

      Zformátuje hodnotu na 3 desetinná místa.

      **Parametry:**

      - ``value``: Hodnota k zformátování.

      **Návratová hodnota:**

      Zformátovaná hodnota nebo None.



.. py:class:: OdstavkaSystemuForm

   Formulář pro nastavení a úpravu odstávky.

   Vrámci načítáni formuláře se doplní načítají hodnoty z template odstávky.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: PermissionImportForm

   Implementuje komponentu ``PermissionImportForm`` v rámci aplikace.


.. py:class:: PermissionSkipImportForm

   Implementuje komponentu ``PermissionSkipImportForm`` v rámci aplikace.


.. py:class:: OptimisticLockingMixin

   Mixin pro detekci souběžných úprav záznamu (optimistické zamykání).

   Při inicializaci formuláře s existující instancí uloží aktuální hodnoty polí modelu
   do skrytého pole (výchozí název ``optimistic_lock_data``, lze přepsat atributem
   :attr:`optimistic_lock_field_name`). Při odeslání formuláře lze pomocí metody
   :meth:`get_conflicting_fields` zjistit, která pole byla mezitím změněna v databázi.

   Pokud je na jedné stránce více formulářů sdílejících jeden POST, je nutné v každé
   podtřídě nastavit unikátní :attr:`optimistic_lock_field_name`, aby nedošlo ke kolizi.

   Podtřída by měla skryté pole zahrnout do layoutu formuláře nebo ho vykreslit ručně v šabloně.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje mixin a přidá skryté pole pro optimistické zamykání.

      **Parametry:**

      - ``args``: Parametry předané do nadřazeného ``__init__``.
      - ``kwargs``: Klíčové parametry předané do nadřazeného ``__init__``.


   .. py:method:: _get_lock_fields()

      Vrací seznam názvů polí formuláře zahrnutých do kontroly souběžných změn.

      Zahrnuje DB modelová pole i pole z :attr:`optimistic_lock_instance_fields`.

      **Návratová hodnota:**

      Seznam názvů polí, která jsou sledována a nejsou vyloučena.


   .. py:method:: _serialize_instance_for_lock()

      Serializuje hodnoty polí instance modelu do JSON řetězce.

      **Parametry:**

      - ``instance``: Instance modelu, jehož hodnoty se serializují.

      **Návratová hodnota:**

      JSON řetězec s hodnotami polí pro pozdější porovnání.


   .. py:method:: get_conflicting_fields()

      Porovná původní stav polí se stavem v databázi a vrátí seznam konfliktních polí.

      Načte čerstvý stav záznamu z databáze a porovná ho s hodnotami uloženými
      při renderování formuláře v poli :attr:`optimistic_lock_field_name`.

      **Návratová hodnota:**

      Seznam názvů polí, která byla mezitím změněna jinou úpravou.



.. py:class:: BaseFilterForm

   Implementuje komponentu ``BaseFilterForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: clean()

      Validuje rozmezí datumů v historii — startovní datum musí být dříve než koncové.

      **Návratová hodnota:**

      Slovník s očistěnými daty formuláře.

      **Výjimky:**

      - ``forms.ValidationError``: Pokud je startovní datum pozdější než koncové.



.. py:class:: TransaltionImportForm

   Implementuje komponentu ``TransaltionImportForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: clean()

      Validuje nahraný PO soubor — kontroluje velikost a formát.

      **Návratová hodnota:**

      Slovník s očistěnými daty formuláře.

      **Výjimky:**

      - ``forms.ValidationError``: Pokud je soubor příliš malý (< 1000 B) nebo nemá příponu ``.po``.



.. py:class:: ImportDataAdminForm

   Implementuje komponentu ``ImportDataAdminForm`` v rámci aplikace.

