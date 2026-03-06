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

      Provádí operaci to python.

      :param selected_value: Kolekce nebo datová struktura `selected_value` zpracovávaná touto funkcí.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get()``, None.

   .. py:method:: has_changed()

      Určí, zda changed.

      :param initial: Stavová nebo časová hodnota `initial` používaná při rozhodování logiky.
      :param data: Kolekce ``data`` zpracovávaná touto funkcí.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: HeslarChoiceFieldField

   Potrebná úprava metód pro ChoiceField ve formuláři, pro správně zobrazení a spracováni predmetu specifikace.

   **Metody:**

   .. py:method:: clean()

      Provádí operaci clean.

      :param selected_value: Kolekce nebo datová struktura `selected_value` zpracovávaná touto funkcí.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get()``, výsledek volání ``clean()``.

   .. py:method:: to_python()

      Provádí operaci to python.

      :param selected_value: Kolekce nebo datová struktura `selected_value` zpracovávaná touto funkcí.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get()``, None.

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

      Provádí operaci clean.

      :return: Vrací proměnná ``cleaned_data``.
      :raises forms.ValidationError: Vyvolá se s textem "State_changed".


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


.. py:class:: DecimalTextWideget

   Třida pro formátování hodnoty velikosti souboru na 3 desetiná místa.

   **Metody:**

   .. py:method:: format_value()

      Provádí operaci format value.

      :param value: Parametr ``value`` předává se do volání ``localize_input()``, ``str()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: None, výsledek volání ``localize_input()``, výsledek volání ``str()``.


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


.. py:class:: BaseFilterForm

   Implementuje komponentu ``BaseFilterForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: clean()

      Provádí operaci clean.

      :return: Vrací proměnná ``cleaned_data``.
      :raises forms.ValidationError: Vyvolá se při splnění podmínky ``error_list``.


.. py:class:: TransaltionImportForm

   Implementuje komponentu ``TransaltionImportForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: clean()

      Provádí operaci clean.

      :return: Vrací proměnná ``cleaned_data``.
      :raises forms.ValidationError: Vyvolá se při splnění podmínky ``file.size < 1000``; nebo při splnění podmínky ``file.name.split('.')[-1] != 'po'``.


.. py:class:: ImportDataAdminForm

   Implementuje komponentu ``ImportDataAdminForm`` v rámci aplikace.

