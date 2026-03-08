CORE import_data_mappers
========================

Modul import_data_mappers.

Třídy
------

.. py:class:: ImportDataValidationResult

   Datová třída, která reprezentuje výsledek validace jednoho záznamu při importu dat.


   **Atributy:**

   - ``item_order``: Pořadové číslo záznamu v importu.
   - ``file_name``: Název CSV souboru, ze kterého záznam pochází.
   - ``primary_key_import``: Primární klíč záznamu v datovém souboru.
   - ``primary_key_table``: Primární klíč záznamu v databázi.
   - ``validation_result``: Textový popis výsledku validace (úspěch nebo chybová zpráva).


.. py:class:: ImportDataError

   Základní výjimka pro chyby při importu dat.


.. py:class:: ImportDataIncorrectStructureError

   Výjimka vyvolaná při nesouladu struktury importovaných dat s očekávanou strukturou (chybějící nebo přebývající sloupce).

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param missing_columns: Parametr ``missing_columns`` se předává do volání ``__init__()``, ``join()``.
      :param excess_columns: Číselná hodnota ``excess_columns`` použitá při výpočtu nebo transformaci.


.. py:class:: ImportDataIncorrectStructureContentObjectError

   Výjimka vyvolaná při nesouladu struktury obsahu importovaných dat s očekávanou strukturou (neplatná kombinace sloupců).

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param columns: Parametr ``columns`` se předává do volání ``__init__()``, ``join()``.
      :param expected_colummns_options: Parametr ``expected_colummns_options`` se předává do volání ``__init__()``, ``join()``.


.. py:class:: ImportDataMissingReferencedValueError

   Výjimka vyvolaná při chybějící hodnotě referencovaného záznamu — buď v databázi, nebo v importovaných datech.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param missing_value_id: Identifikátor objektu ``missing_value``.
      :param missing_model_name: Parametr ``missing_model_name`` předává se do volání ``__init__()``.


.. py:class:: ImportDataIntegrityError

   Výjimka vyvolaná ve dvou případech:

   při insertu — pokud záznam se stejným primárním klíčem již v databázi existuje,
   při updatu — pokud záznam se zadaným primárním klíčem v databázi neexistuje.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record_id: Identifikátor objektu ``record``.
      :param model_name: Název modelu používaný pro cílení operace.
      :param performed_action: Parametr ``performed_action`` předává se do volání ``__init__()``, ``format()``.


.. py:class:: ImportDataLimitChoicesError

   Výjimka vyvolaná při hodnotě cizího klíče, která nesplňuje omezení limit_choices_to.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record_id: Identifikátor objektu ``record``.
      :param limit_choices_to: Parametr ``limit_choices_to`` se předává do volání ``__init__()``, ``format()``, pracuje se s atributy ``items``.


.. py:class:: ImportDataHeslarPresnostLimitChoicesError

   Výjimka vyvolaná při neplatné hodnotě přesnosti v hesláři u importovaného záznamu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record_id: Identifikátor objektu ``record``.


.. py:class:: ImportDataUnsupportedFileError

   Výjimka vyvolaná při výskytu nepodporovaného názvu souboru v importovaném archivu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param file_name: Parametr ``file_name`` se předává do volání ``__init__()``, ``format()``.


.. py:class:: ImportDataUnsupportedFilesError

   Výjimka vyvolaná při výskytu jednoho nebo více nepodporovaných názvů souborů v importovaném archivu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param file_names: Parametr ``file_names`` se předává do volání ``__init__()``, ``format()``.


.. py:class:: ImportDataIncorrectPrimaryKeyFormatError

   Výjimka vyvolaná při nesouladu hodnoty primárního klíče s očekávaným formátem.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param primary_key_value: Textový název nebo klíč ``primary_key_value`` používaný v rámci operace.


.. py:class:: ImportDataActiveUserCannotBeDeleted

   Výjimka vyvolaná při snaze o smazání aktivního uživatele

   **Metody:**

   .. py:method:: __init__()


.. py:class:: BaseImportField

   Základní třída pro importní pole. Neprovádí žádnou validaci ani zpracování hodnoty.

   Používá se především pro textová pole.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

   .. py:method:: value()

      Provádí operaci value.

      :return: Vrací atribut objektu.

   .. py:method:: value()

      Provádí operaci value.

      :param value: Parametr ``value`` předává se do volání ``str()``, ``_process_value()``, pracuje se s atributy ``setter``, ovlivňuje větvení podmínek.

   .. py:method:: is_null()

      Určí, zda null.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: instance_value()

      Provádí operaci instance value.

      :return: Vrací atribut objektu.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

      :return: Vrací atribut objektu.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Parametr ``value`` vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: IntegerImportField

   Importní pole pro hodnoty datového typu integer.

   **Metody:**

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``str()``, pracuje se s atributy ``decode``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

      :raises ImportDataError: Vyvolá se při splnění podmínky ``value``.


.. py:class:: PositiveIntegerImportField

   Importní pole pro kladné celočíselné hodnoty. Záporná čísla způsobí vyvolání ImportDataError.

   **Metody:**

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Parametr ``value`` předává se do volání ``_process_value()``, ``ImportDataError()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

      :raises ImportDataError: Vyvolá se při splnění podmínky ``value is not None and value < 0``.


.. py:class:: DecimalImportField

   Importní pole pro desetinná čísla (float).

   **Metody:**

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``str()``, pracuje se s atributy ``decode``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

      :raises ImportDataError: Vyvolá se při splnění podmínky ``value``.


.. py:class:: BooleanImportField

   Importní pole pro hodnoty datového typu boolean.

   **Metody:**

   .. py:method:: _process_value()

      Provádí operaci process value.

      Převede řetězec na bool. Pokud hodnota není "true"/"1" ani "false"/"0", vyvolá ImportDataError.

      :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``ImportDataError()``, pracuje se s atributy ``lower``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

      :raises ImportDataError: Vyvolá se v konkrétních chybových větvích této funkce.


.. py:class:: DateImportField

   Importní pole pro hodnoty datového typu date.

   **Metody:**

   .. py:method:: value()

      Provádí operaci value.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: value()

      Provádí operaci value.

      :param value: Parametr ``value`` předává se do volání ``_process_value()``, pracuje se s atributy ``setter``.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: _process_value()

      Provádí operaci process value.

      Převede řetězec na datum. Podporované formáty jsou "YYYY-MM-DD" a "DD.MM.YYYY".
      Pokud hodnota neodpovídá žádnému formátu, vyvolá ImportDataError.

      :param value: Parametr ``value`` předává se do volání ``str()``, ``isinstance()``, pracuje se s atributy ``replace``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

      :raises ImportDataError: Vyvolá se v konkrétních chybových větvích této funkce.


.. py:class:: DateTimeImportField

   Importní pole pro hodnoty datového typu datetime.

   Podporovaný formát: "YYYY-MM-DD HH:MM:SS".

   **Metody:**

   .. py:method:: value()

      Provádí operaci value.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: value()

      Provádí operaci value.

      :param value: Parametr ``value`` předává se do volání ``_process_value()``, pracuje se s atributy ``setter``.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Parametr ``value`` předává se do volání ``str()``, ``isinstance()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

      :raises ImportDataError: Vyvolá se v konkrétních chybových větvích této funkce.


.. py:class:: DateRangeImportField

   Importní pole pro hodnoty datového typu date range.

   **Metody:**

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: _process_value()

      Provádí operaci process value.

      Převede řetězec na DateRange ve formátu "[YYYY-MM-DD, YYYY-MM-DD)".
      Pokud hodnota neodpovídá očekávanému formátu, vyvolá ImportDataError.

      :param value: Parametr ``value`` předává se do volání ``str()``, ``isinstance()``, pracuje se s atributy ``strip``, ovlivňuje větvení podmínek.
      :return: Výstup funkce odpovídající implementované logice.

      :raises ImportDataError: Vyvolá se v konkrétních chybových větvích této funkce.


.. py:class:: LookupImportField

   Importní pole pro hodnoty odkazující na instanci jiného modelu (cizí klíč).

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param lookup_model_classes: Parametr ``lookup_model_classes`` předává se do volání ``isinstance()``, ovlivňuje větvení podmínek.
      :param lookup_field_name: Textový název nebo klíč ``lookup_field_name`` používaný v rámci operace.
      :param limit_choices_to: Parametr ``limit_choices_to`` ovlivňuje větvení podmínek.

      :raises ValueError: Vyvolá se s textem "limit_choices_to is only supported for Heslar model".

   .. py:method:: instance_value()

      Provádí operaci instance value.

      :return: Vrací atribut objektu.

   .. py:method:: _check_limit_choices_to()

      Ověří limit choices to.

      :param record: Parametr ``record`` předává se do volání ``all()``, ``getattr()``, ovlivňuje větvení podmínek.
      :return: Vrací výsledek ověření nebo validačního pravidla.

      :raises ImportDataLimitChoicesError: Vyvolá se při splnění podmínky ``not all((getattr(record, k).pk == v for k, v in self.limit_choices_to.items()))``.

   .. py:method:: _process_value()

      Provádí operaci process value.

      Ověří existenci hodnoty v databázi nebo v importovaných záznamech a vrátí odpovídající záznam.
      Pokud referencovaný záznam neexistuje, vyvolá ImportDataMissingReferencedValueError.

      :param value: Parametr ``value`` předává se do volání ``str()``, ``len()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

      :raises ImportDataMissingReferencedValueError: Vyvolá se v konkrétních chybových větvích této funkce.


.. py:class:: RuianLookupImportField

   Rozšíření LookupImportField pro import dat z RUIAN. Odstraní prefix "ruian-" a převede hodnotu na integer.

   **Metody:**

   .. py:method:: value()

      Provádí operaci value.

      :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``match()``, ovlivňuje větvení podmínek.


.. py:class:: VazbaLookupImportField

   Importní pole pro referencované modely přes vazbu (relaci). Relace je 1:1 místo 1:N.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param lookup_model_classes: Parametr ``lookup_model_classes`` předává se do volání ``__init__()``.
      :param lookup_field_name: Textový název nebo klíč ``lookup_field_name`` používaný v rámci operace.
      :param read_field_name: Textový název nebo klíč ``read_field_name`` používaný v rámci operace.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Parametr ``value`` předává se do volání ``get_record_from_ident()``, ``get()``, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

      :raises ImportDataMissingReferencedValueError: Vyvolá se v konkrétních chybových větvích této funkce.


.. py:class:: GeomImportField

   Importní pole pro geometrické hodnoty.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param srid: Parametr ``srid`` slouží jako vstup pro logiku funkce ``__init__``.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

      :return: Vrací výsledek volání ``getattr()``.

   .. py:method:: _process_value()

      Provádí operaci process value.

      Převede řetězec na objekt GEOSGeometry. Pokud převod selže, vyvolá ImportDataError.

      :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``GEOSGeometry()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

      :raises ImportDataError: Vyvolá se v konkrétních chybových větvích této funkce.


.. py:class:: GenericForeignKeyImportField

   Importní pole pro generický cizí klíč.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param lookup_model_classes: Parametr ``lookup_model_classes`` předává se do volání ``__init__()``.
      :param lookup_field_name: Textový název nebo klíč ``lookup_field_name`` používaný v rámci operace.
      :param serialized_attribute: Parametr ``serialized_attribute`` slouží jako vstup pro logiku funkce ``__init__``.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``getattr()``, atribut objektu.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``match()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

      :raises ImportDataMissingReferencedValueError: Vyvolá se v konkrétních chybových větvích této funkce.


.. py:class:: ImportModelMapper

   Základní třída pro hromadný import dat. Načítá data z importovaného souboru,

   předzpracovává hodnoty podle cílového pole a vytváří záznamy.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param value_dict: Kolekce nebo datová struktura `value_dict` zpracovávaná touto funkcí.

   .. py:method:: get_import_data_mapper_dict()

      Vrátí slovník mapující názvy importních souborů na příslušné třídy mapperů.

      :return: Vrací slovník.

   .. py:method:: get_import_data_mapper()

      Vrátí třídu mapperu odpovídající zadanému názvu souboru (bez přípony).

      :param file_name: Parametr ``file_name`` se předává do volání ``get()``, pracuje se s atributy ``split``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: get_file_name_for_mapper()

      Vrátí název souboru odpovídající zadané třídě mapperu.

   .. py:method:: get_mapping()

      Vrátí slovník mapování polí pomocí metody map_field.

      :param include_primary_key: Parametr ``include_primary_key`` ovlivňuje větvení podmínek.
      :return: Vrací výsledek operace.

   .. py:method:: load_record_from_db()

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrátí slovník s názvem (názvy) a hodnotou (hodnotami) primárního klíče pro filtrování.

      :return: Vrací hodnotu typu ``dict | None``; podle větve může jít o: None, slovník, hodnotu podle větve zpracování.

   .. py:method:: _parse_primary_key()

      Zpracuje primary key.

      :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``match()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

      :raises ImportDataIncorrectPrimaryKeyFormatError: Vyvolá se při splnění podmínky ``match``.

   .. py:method:: _parse_primary_key_custom_prefix()

      Zpracuje primary key custom prefix.

      :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``int()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param prefix: Číselná hodnota ``prefix`` použitá při výpočtu nebo transformaci.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: map_field()

      Namapuje pole modelu na odpovídající instanci BaseImportField nebo její podtřídy.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``BaseImportField()``, výsledek volání ``IntegerImportField()``, výsledek volání ``PositiveIntegerImportField()``.
      :raises ImportDataError: Vyvolá se v konkrétních chybových větvích této funkce.

   .. py:method:: is_field_required()

      Určí, zda field required.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: create_records()

      Vytvoří instanci záznamu nebo více instancí modelů připravených k uložení do databáze.

      :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``, ``ImportDataError()``, ovlivňuje větvení podmínek.
      :return: Nově vytvořená hodnota připravená touto funkcí.

      :raises ImportDataError: Vyvolá se při splnění podmínky ``performed_action not in (ImportDataAdminForm.PERFORMED_ACTION_INSERT, ImportDataAdminForm.PERFORMED_ACTION_UPDATE, ImportDataAdminForm.PERFO``.

   .. py:method:: import_validation()

      Provede validaci na základě primárního klíče. Při insertu záznam nesmí existovat,

      při updatu musí existovat. Vrátí slovník s primárními klíči, nebo vyvolá ImportDataIntegrityError.

      :param performed_action: Parametr ``performed_action`` předává se do volání ``ImportDataIntegrityError()``, ovlivňuje větvení podmínek.
      :return: Vrací výsledek operace.

      :raises ImportDataIntegrityError: Vyvolá se při splnění podmínky ``performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT and self.model_class.objects.filter(**self._get_filter_kwargs_primary_key())``; nebo při splnění podmínky ``performed_action in (ImportDataAdminForm.PERFORMED_ACTION_UPDATE, ImportDataAdminForm.PERFORMED_ACTION_DELETE) and (not self.model_class.obj``.

   .. py:method:: _check_column_structure()

      Ověří column structure.

      :param performed_action: Parametr ``performed_action`` ovlivňuje větvení podmínek.
      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``set()``, ``get_mapping()``.
      :return: Vrací výsledek ověření nebo validačního pravidla.

      :raises ImportDataIncorrectStructureError: Vyvolá se při splnění podmínky ``missing_columns or excess_columns``.

   .. py:method:: map()

      Nejprve ověří strukturu sloupců souboru — při nesouladu vyvolá ImportDataIncorrectStructureError.

      Poté vrátí slovník s názvy polí jako klíči a instancemi BaseImportField s načtenými hodnotami jako hodnotami.

      :param performed_action: Parametr ``performed_action`` předává se do volání ``_check_column_structure()``.
      :param instance_values: Parametr ``instance_values`` ovlivňuje větvení podmínek.
      :param serialize: Parametr ``serialize`` slouží jako vstup pro logiku funkce ``map``.
      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``_check_column_structure()``, ``get_mapping()``.
      :return: Vrací výsledek operace.

   .. py:method:: check_required_fields()

      Ověří required fields.

      :param performed_action: Parametr ``performed_action`` slouží jako vstup pro logiku funkce ``check_required_fields``.

      :raises ImportDataError: Vyvolá se při splnění podmínky ``required and (value is None or str(value).lower().strip() in ('nan', '') or pd.isna(value))``.

   .. py:method:: map_column_name_to_field_name()

      Provádí operaci map column name to field name.

      Převede název sloupce z importního souboru na název pole Django modelu.
      Používá se, pokud se název pole liší od názvu databázového sloupce.

      :param column_name: Textový název nebo klíč ``column_name`` používaný v rámci operace.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: create_relations()

      Vytvoří vazební záznamy pro Historie, Komponenty a Soubory, pokud ještě neexistují.

      :param instance: Parametr ``instance`` předává se do volání ``getattr()``, pracuje se s atributy ``historie``, ``soubory``, ovlivňuje větvení podmínek.

   .. py:method:: record_postprocessing()

      Provádí operaci record postprocessing.

      :param record: Parametr ``record`` vstupuje do návratové hodnoty.
      :param performed_action: Parametr ``performed_action`` slouží jako vstup pro logiku funkce ``record_postprocessing``.
      :param fedora_transaction: Parametr ``fedora_transaction`` slouží jako vstup pro logiku funkce ``record_postprocessing``.

      :return: Vrací proměnná ``record``.

   .. py:method:: fedora_update_targets()

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: GeometryTransformMixin

   Mixin pro mappery s geometrickými poli. Při insertu zajišťuje konverzi mezi souřadnicovými systémy:

   WGS84 (SRID 4326) → S-JTSK (SRID 5514) a naopak.

   **Metody:**

   .. py:method:: transform_geometries()

      Transformuje geometries. v aplikaci.

      :param mapping_dict: Parametr ``mapping_dict`` předává se do volání ``transform_geom_to_sjtsk()``, ``transform_geom_to_wgs84()``, pracuje se s atributy ``get``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param performed_action: Parametr ``performed_action`` ovlivňuje větvení podmínek.

      :return: Vrací proměnná ``mapping_dict``.


.. py:class:: MultipleClassImportModelMapper

   Základní třída pro mappery importující data do více modelů najednou.

   **Metody:**

   .. py:method:: import_validation()

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrací filter kwargs primary key.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``, ovlivňuje větvení podmínek.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: is_field_required()

      Určí, zda field required.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: HeslarMapper

   Mapovač pro model Heslar.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.


.. py:class:: HeslarDataceMapper

   Mapovač pro model HeslarDatace.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: HeslarDokumentTypMaterialRadaMapper

   Mapovač pro model HeslarDokumentTypMaterialRada.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: HeslarHierarchieMapper

   Mapovač pro model HeslarHierarchie.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: HeslarOdkazMapper

   Mapovač pro model HeslarOdkaz.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: OrganizaceMapper

   Mapovač pro model Organizace.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: OsobaMapper

   Mapovač pro model Osoba.


.. py:class:: ProjektMapper

   Mapovač pro model Projekt.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``, ``transform_geometries()``, vstupuje do návratové hodnoty.
      :param instance_values: Parametr ``instance_values`` předává se do volání ``map()``.
      :param serialize: Parametr ``serialize`` předává se do volání ``map()``.
      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``map()``.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_record_history()


.. py:class:: ProjektKatastrMapper

   Mapovač pro model ProjektKatastr.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: ProjektOznamovatelMapper

   Mapovač pro model Oznamovatel.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: SamostatnyNalezMapper

   Mapovač pro model SamostatnyNalez.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``, ``transform_geometries()``, vstupuje do návratové hodnoty.
      :param instance_values: Parametr ``instance_values`` předává se do volání ``map()``.
      :param serialize: Parametr ``serialize`` předává se do volání ``map()``.
      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``map()``.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: ArcheologickyZaznamAkceMapper

   Mapovač pro modely ArcheologickyZaznam a Akce.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` slouží jako vstup pro logiku funkce ``get_mapping``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: map_field()

      Provádí operaci map field.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: record_postprocessing()

      Provádí operaci record postprocessing.

      :param record: Parametr ``record`` předává se do volání ``isinstance()``, ``record_postprocessing()``, pracuje se s atributy ``typ_zaznamu``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param performed_action: Parametr ``performed_action`` předává se do volání ``record_postprocessing()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``record_postprocessing()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``record_postprocessing()``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: LokalitaMapper

   Mapovač pro modely ArcheologickyZaznam a Lokalita.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` slouží jako vstup pro logiku funkce ``get_mapping``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: map_field()

      Provádí operaci map field.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: get_record_history()


.. py:class:: AkceVedouciMapper

   Mapovač pro model AkceVedouci.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: get_record_history()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: ArcheologickyZaznamKatastrMapper

   Mapovač pro model ArcheologickyZaznamKatastr.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: PianMapper

   Mapovač pro model Pian.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``, ``transform_geometries()``, vstupuje do návratové hodnoty.
      :param instance_values: Parametr ``instance_values`` předává se do volání ``map()``.
      :param serialize: Parametr ``serialize`` předává se do volání ``map()``.
      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``map()``.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_record_history()


.. py:class:: DokumentacniJednotkaMapper

   Mapovač pro model DokumentacniJednotka.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: record_postprocessing()

      Provádí operaci record postprocessing.

      :param record: Parametr ``record`` předává se do volání ``vytvor_pian()``, pracuje se s atributy ``archeologicky_zaznam``, ``pian``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param performed_action: Parametr ``performed_action`` slouží jako vstup pro logiku funkce ``record_postprocessing``.
      :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``vytvor_pian()``.

      :return: Vrací proměnná ``record``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: AdbMapper

   Mapovač pro model Adb.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: AdbVyskovyBod

   Mapovač pro model VyskovyBod.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: DokumentLetMapper

   Mapovač pro model Let.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.


.. py:class:: DokumentMapper

   Mapovač pro modely Dokument a DokumentExtraData.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` slouží jako vstup pro logiku funkce ``get_mapping``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: map_field()

      Provádí operaci map field.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: create_records()

      Vytvoří instanci Dokument a DokumentExtraData s vazbou na Dokument.

      :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``, ovlivňuje větvení podmínek.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``, ``transform_geometries()``, vstupuje do návratové hodnoty.
      :param instance_values: Parametr ``instance_values`` předává se do volání ``map()``.
      :param serialize: Parametr ``serialize`` předává se do volání ``map()``.
      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``map()``.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_record_history()


.. py:class:: DokumentAutorMapper

   Mapovač pro model DokumentAutor.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: DokumentJazykMapper

   Mapovač pro model DokumentJazyk.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: DokumentOsobaMapper

   Mapovač pro model DokumentOsoba.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: DokumentPosudekMapper

   Mapovač pro model DokumentPosudek.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: TvarMapper

   Mapovač pro model Tvar.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: DokumentCastMapper

   Mapovač pro model DokumentCast.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: NeidentAkceMapper

   Mapovač pro model NeidentAkce.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: NeidentAkceVedouciMapper

   Mapovač pro model NeidentAkceVedouci.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: KomponentaMapper

   Mapovač pro model Komponenta.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: KomponentaAktivitaMapper

   Mapovač pro model KomponentaAktivita.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: NalezMapper

   Základní mapper pro nálezy.

   **Metody:**

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: NalezObjektMapper

   Mapovač pro model NalezObjekt.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.


.. py:class:: NalezPredmetMapper

   Mapovač pro model NalezPredmet.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.


.. py:class:: ExterniZdrojMapper

   Mapovač pro model ExterniZdroj.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: get_record_history()


.. py:class:: ExterniZdrojAutorMapper

   Mapovač pro model ExterniZdrojAutor.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: ExterniZdrojEditorMapper

   Mapovač pro model ExterniZdrojEditor.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: ExterniOdkazMapper

   Mapovač pro model ExterniOdkaz.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: UzivatelMapper

   Mapovač pro model User.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: get_record_history()

   .. py:method:: import_validation()


.. py:class:: UzivatelNotifikaceProjektMapper

   Mapovač pro model Pes (notifikace uživatele vázané na projekt či územní jednotku RUIAN).

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` slouží jako vstup pro logiku funkce ``get_mapping``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrací filter kwargs primary key.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: map_field()

      Provádí operaci map field.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.

      :return: Vrací výsledek volání ``map_field()``.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _check_column_structure()

      Ověří column structure.

      :param performed_action: Parametr ``performed_action`` slouží jako vstup pro logiku funkce ``_check_column_structure``.
      :param include_primary_key: Parametr ``include_primary_key`` slouží jako vstup pro logiku funkce ``_check_column_structure``.
      :return: Vrací výsledek ověření nebo validačního pravidla.

      :raises ImportDataIncorrectStructureContentObjectError: Vyvolá se při splnění podmínky ``mapping_column_set != expected_column_set_import and mapping_column_set != expected_column_set_job``.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``.
      :param instance_values: Parametr ``instance_values`` předává se do volání ``map()``.
      :param serialize: Parametr ``serialize`` předává se do volání ``map()``.
      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``map()``.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: UzivatelSpolupraceMapper

   Mapovač pro model UzivatelSpoluprace.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: UzivatelOpravneniMapper

   Mapovač pro přiřazení skupinových oprávnění uživateli (model User).

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` slouží jako vstup pro logiku funkce ``get_mapping``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrací filter kwargs primary key.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Parametr ``performed_action`` slouží jako vstup pro logiku funkce ``create_records``.

      :return: Vrací seznam.

   .. py:method:: import_validation()

   .. py:method:: get_record_history()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: SouborMapper

   Mapovač pro model Soubor.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

   .. py:method:: get_record_history()


.. py:class:: UzivatelNotifikaceMapper

   Mapovač pro přiřazení typů notifikací uživateli (model User).

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` slouží jako vstup pro logiku funkce ``get_mapping``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrací filter kwargs primary key.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Parametr ``performed_action`` slouží jako vstup pro logiku funkce ``create_records``.

      :return: Vrací seznam.

   .. py:method:: import_validation()

   .. py:method:: get_record_history()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: HistorieMapper

   Mapovač pro model Historie.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

      :return: Vrací proměnná ``field_mapping``.

   .. py:method:: _get_updated_ident_cely_record_list()

