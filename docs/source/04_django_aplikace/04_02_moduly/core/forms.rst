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

      :param attrs: Kolekce ``attrs`` zpracovávaná touto funkcí.
      :param choices: Parametr ``choices`` se předává do volání ``__init__()``.


.. py:class:: TwoLevelSelectField

   Potrebná úprava metód pro Charfield ve formuláři, pokud se používa widget se zobrazením dvou-stupňového seznamu.

   **Metody:**

   .. py:method:: to_python()

      Konvertuje vybranou hodnotu na Python objekt Heslar.

      :param selected_value: ID vybraného hesláře.
      :return: Instance Heslar objektu nebo None.

   .. py:method:: has_changed()

      Určí, zda changed.

      :param initial: Stavová nebo časová hodnota `initial` používaná při rozhodování logiky.
      :param data: Kolekce ``data`` zpracovávaná touto funkcí.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: HeslarChoiceFieldField

   Potrebná úprava metód pro ChoiceField ve formuláři, pro správně zobrazení a spracováni predmetu specifikace.

   **Metody:**

   .. py:method:: clean()

      Vrátí instanci Heslar objektu nebo spustí standardní vyčištění pole.

      :param selected_value: ID vybraného hesláře.
      :return: Instance Heslar objektu nebo výsledek ```super().clean()``.

   .. py:method:: to_python()

      Konvertuje vybranou hodnotu na Python objekt Heslar.

      :param selected_value: ID vybraného hesláře.
      :return: Instance Heslar objektu nebo None.

   .. py:method:: has_changed()

      Určí, zda changed.

      :param initial: Stavová nebo časová hodnota `initial` používaná při rozhodování logiky.
      :param data: Kolekce ``data`` zpracovávaná touto funkcí.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: CheckStavNotChangedForm

   Formulář pro kontrolu jestli se stav záznamu nezmenil mezi jeho načtením a odeslánim zmeny.

   Celá logika je v clean metóde.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param db_stav: Stavová hodnota načtená z databáze.
      :param require_confirmation: Parametr ``require_confirmation`` ovlivňuje větvení podmínek.
      :param dokument_warnings: Parametr ``dokument_warnings`` předává se do volání ``append()``, ``HTML()``, ovlivňuje větvení podmínek.
      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: clean()

      Ověří, že se stav záznamu nezměnil mezi načtením a odesláním.

      :return: Ověřená data.
      :raises forms.ValidationError: Vyvolá se s textem "State_changed" pokud se stav změnil.


.. py:class:: VratitForm

   Formulář pro vrácení záznamu. Obsahuje jen text pole pro zdůvodnění vrácení.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: VratitFormDokument

   Implementuje komponentu ``VratitFormDokument`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: VratitFormAZ

   Formulář pro vrácení záznamu Akce nebo Lokality. Obsahuje text pole pro zdůvodnění vrácení a výběr dokumentů pro vrácení.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param az: Parametr ``az`` se předává do volání ``filter()``, pracuje se s atributy ``stav``, ``ident_cely``, ovlivňuje větvení podmínek.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: DecimalTextWidget

   Třida pro formátování hodnoty velikosti souboru na 3 desetiná místa.

   **Metody:**

   .. py:method:: format_value()

      Zformátuje hodnotu na 3 desetinná místa.

      :param value: Hodnota k zformátování.
      :return: Zformátovaná hodnota nebo None.


.. py:class:: OdstavkaSystemuForm

   Formulář pro nastavení a úpravu odstávky.

   Vrámci načítáni formuláře se doplní načítají hodnoty z template odstávky.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


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

      :param args: Parametry předané do nadřazeného ``__init__``.
      :param kwargs: Klíčové parametry předané do nadřazeného ``__init__``.

   .. py:method:: _get_lock_fields()

      Vrací seznam názvů polí formuláře zahrnutých do kontroly souběžných změn.

      Zahrnuje DB modelová pole i pole z :attr:`optimistic_lock_instance_fields`.

      :return: Seznam názvů polí, která jsou sledována a nejsou vyloučena.

   .. py:method:: _serialize_instance_for_lock()

      Serializuje hodnoty polí instance modelu do JSON řetězce.

      :param instance: Instance modelu, jehož hodnoty se serializují.
      :return: JSON řetězec s hodnotami polí pro pozdější porovnání.

   .. py:method:: get_conflicting_fields()

      Porovná původní stav polí se stavem v databázi a vrátí seznam konfliktních polí.

      Načte čerstvý stav záznamu z databáze a porovná ho s hodnotami uloženými
      při renderování formuláře v poli :attr:`optimistic_lock_field_name`.

      :return: Seznam názvů polí, která byla mezitím změněna jinou úpravou.

   .. py:method:: add_secondary_lock()

      Přidá skryté pole se snapshotem stavu jiné instance modelu (secondary lock).

      Použití: formulář pro vytvoření PIANu chrání i editaci souvisejícího DJ.
      Lze volat opakovaně s různými ``field_name`` a uzamknout tak formulář
      proti více souvisejícím modelům najednou.

      :param instance: Instance modelu, jejíž stav má být sledován.
      :param field_name: Unikátní název skrytého pole pro snapshot.
      :param lock_fields: Seznam DB polí instance pro porovnání (FK se serializují přes ``*_id``).

   .. py:method:: _serialize_fields_for_lock()

      Serializuje vybraná DB pole instance modelu do JSON řetězce.

      Pole, která nejsou DB pole modelu, jsou ignorována. M2M pole se ukládají jako
      seřazený seznam PK, FK jako ``*_id`` hodnota, datetime přes ``isoformat()``.

      :param instance: Instance modelu, jehož pole se serializují.
      :param lock_fields: Seznam DB polí, která se mají serializovat.
      :return: JSON řetězec s hodnotami polí pro pozdější porovnání.

   .. py:method:: get_secondary_conflicting_fields()

      Vrátí seznam polí instance pod daným secondary lockem, která byla v DB mezitím změněna.

      :param field_name: Název skrytého pole použitý při :meth:`add_secondary_lock`.
      :return: Seznam názvů polí, která byla mezitím změněna jinou úpravou.


.. py:class:: BaseFilterForm

   Implementuje komponentu ``BaseFilterForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: clean()

      Validuje rozmezí datumů v historii — startovní datum musí být dříve než koncové.

      :return: Slovník s očistěnými daty formuláře.
      :raises forms.ValidationError: Pokud je startovní datum pozdější než koncové.


.. py:class:: TranslationImportForm

   Implementuje komponentu ``TranslationImportForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: clean()

      Validuje nahraný PO soubor — kontroluje velikost a formát.

      :return: Slovník s očistěnými daty formuláře.
      :raises forms.ValidationError: Pokud je soubor příliš malý (< 1000 B) nebo nemá příponu ``.po``.


.. py:class:: ImportDataAdminForm

   Implementuje komponentu ``ImportDataAdminForm`` v rámci aplikace.

