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

      :param missing_columns: Číselná nebo geometrická hodnota `missing_columns` použitá při výpočtu nebo transformaci.
      :param excess_columns: Číselná hodnota ``excess_columns`` použitá při výpočtu nebo transformaci.


.. py:class:: ImportDataIncorrectStructureContentObjectError

   Výjimka vyvolaná při nesouladu struktury obsahu importovaných dat s očekávanou strukturou (neplatná kombinace sloupců).

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param columns: Číselná nebo geometrická hodnota `columns` použitá při výpočtu nebo transformaci.
      :param expected_colummns_options: Dodatečné poziční argumenty předané voláním.


.. py:class:: ImportDataMissingReferencedValueError

   Výjimka vyvolaná při chybějící hodnotě referencovaného záznamu — buď v databázi, nebo v importovaných datech.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param missing_value_id: Identifikátor objektu ``missing_value``.
      :param missing_model_name: Název nebo typ ``missing_model_name`` používaný pro volbu cílové logiky.


.. py:class:: ImportDataIntegrityError

   Výjimka vyvolaná ve dvou případech:

   při insertu — pokud záznam se stejným primárním klíčem již v databázi existuje,
   při updatu — pokud záznam se zadaným primárním klíčem v databázi neexistuje.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record_id: Identifikátor objektu ``record``.
      :param model_name: Název modelu používaný pro cílení operace.
      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.


.. py:class:: ImportDataLimitChoicesError

   Výjimka vyvolaná při hodnotě cizího klíče, která nesplňuje omezení limit_choices_to.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record_id: Identifikátor objektu ``record``.
      :param limit_choices_to: Číselná nebo geometrická hodnota `limit_choices_to` použitá při výpočtu nebo transformaci.


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

      :param file_name: Cesta, URL nebo název zdroje ``file_name``, ze kterého funkce čte nebo kam zapisuje.


.. py:class:: ImportDataUnsupportedFilesError

   Výjimka vyvolaná při výskytu jednoho nebo více nepodporovaných názvů souborů v importovaném archivu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param file_names: Cesta, URL nebo název zdroje ``file_names``, ze kterého funkce čte nebo kam zapisuje.


.. py:class:: ImportDataIncorrectPrimaryKeyFormatError

   Výjimka vyvolaná při nesouladu hodnoty primárního klíče s očekávaným formátem.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param primary_key_value: Textový název nebo klíč ``primary_key_value`` používaný v rámci operace.


.. py:class:: BaseImportField

   Základní třída pro importní pole. Neprovádí žádnou validaci ani zpracování hodnoty.

   Používá se především pro textová pole.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

   .. py:method:: value()

      Provádí operaci value.

   .. py:method:: value()

      Provádí operaci value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: is_null()

      Určí, zda null.

   .. py:method:: instance_value()

      Provádí operaci instance value.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: IntegerImportField

   Importní pole pro hodnoty datového typu integer.

   **Metody:**

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: PositiveIntegerImportField

   Importní pole pro kladné celočíselné hodnoty. Záporná čísla způsobí vyvolání ImportDataError.

   **Metody:**

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: DecimalImportField

   Importní pole pro desetinná čísla (float).

   **Metody:**

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: BooleanImportField

   Importní pole pro hodnoty datového typu boolean.

   **Metody:**

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: DateImportField

   Importní pole pro hodnoty datového typu date.

   **Metody:**

   .. py:method:: value()

      Provádí operaci value.

   .. py:method:: value()

      Provádí operaci value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: DateTimeImportField

   Importní pole pro hodnoty datového typu datetime.

   Podporovaný formát: "YYYY-MM-DD HH:MM:SS".

   **Metody:**

   .. py:method:: value()

      Provádí operaci value.

   .. py:method:: value()

      Provádí operaci value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: DateRangeImportField

   Importní pole pro hodnoty datového typu date range.

   **Metody:**

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: LookupImportField

   Importní pole pro hodnoty odkazující na instanci jiného modelu (cizí klíč).

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param lookup_model_classes: Název nebo typ ``lookup_model_classes`` používaný pro volbu cílové logiky.
      :param lookup_field_name: Textový název nebo klíč ``lookup_field_name`` používaný v rámci operace.
      :param limit_choices_to: Číselná nebo geometrická hodnota `limit_choices_to` použitá při výpočtu nebo transformaci.

   .. py:method:: instance_value()

      Provádí operaci instance value.

   .. py:method:: _check_limit_choices_to()

      Ověří limit choices to.

      :param record: Záznam, který funkce čte nebo upravuje.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: RuianLookupImportField

   Rozšíření LookupImportField pro import dat z RUIAN. Odstraní prefix "ruian-" a převede hodnotu na integer.

   **Metody:**

   .. py:method:: value()

      Provádí operaci value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.


.. py:class:: VazbaLookupImportField

   Importní pole pro referencované modely přes vazbu (relaci). Relace je 1:1 místo 1:N.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param lookup_model_classes: Název nebo typ ``lookup_model_classes`` používaný pro volbu cílové logiky.
      :param lookup_field_name: Textový název nebo klíč ``lookup_field_name`` používaný v rámci operace.
      :param read_field_name: Textový název nebo klíč ``read_field_name`` používaný v rámci operace.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: GeomImportField

   Importní pole pro geometrické hodnoty.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param srid: Číselná nebo geometrická hodnota `srid` použitá při výpočtu nebo transformaci.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: GenericForeignKeyImportField

   Importní pole pro generický cizí klíč.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param lookup_model_classes: Název nebo typ ``lookup_model_classes`` používaný pro volbu cílové logiky.
      :param lookup_field_name: Textový název nebo klíč ``lookup_field_name`` používaný v rámci operace.
      :param serialized_attribute: Příznak ``serialized_attribute`` určující průběh nebo rozsah zpracování.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: ImportModelMapper

   Základní třída pro hromadný import dat. Načítá data z importovaného souboru,

   předzpracovává hodnoty podle cílového pole a vytváří záznamy.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param value_dict: Kolekce nebo datová struktura `value_dict` zpracovávaná touto funkcí.

   .. py:method:: get_import_data_mapper_dict()

      Vrátí slovník mapující názvy importních souborů na příslušné třídy mapperů.

   .. py:method:: get_import_data_mapper()

      Vrátí třídu mapperu odpovídající zadanému názvu souboru (bez přípony).

      :param file_name: Cesta, URL nebo název zdroje ``file_name``, ze kterého funkce čte nebo kam zapisuje.

   .. py:method:: get_mapping()

      Vrátí slovník mapování polí pomocí metody map_field.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.
      :return: Vrací výsledek operace.

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrátí slovník s názvem (názvy) a hodnotou (hodnotami) primárního klíče pro filtrování.

   .. py:method:: _parse_primary_key()

      Zpracuje primary key.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _parse_primary_key_custom_prefix()

      Zpracuje primary key custom prefix.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :param prefix: Číselná hodnota ``prefix`` použitá při výpočtu nebo transformaci.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: map_field()

      Namapuje pole modelu na odpovídající instanci BaseImportField nebo její podtřídy.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.

   .. py:method:: is_field_required()

      Určí, zda field required.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: import_validation()

      Provede validaci na základě primárního klíče. Při insertu záznam nesmí existovat,

      při updatu musí existovat. Vrátí slovník s primárními klíči, nebo vyvolá ImportDataIntegrityError.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :return: Vrací výsledek operace.

   .. py:method:: _check_column_structure()

      Ověří column structure.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: map()

      Nejprve ověří strukturu sloupců souboru — při nesouladu vyvolá ImportDataIncorrectStructureError.

      Poté vrátí slovník s názvy polí jako klíči a instancemi BaseImportField s načtenými hodnotami jako hodnotami.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :param instance_values: Záznam/objekt ``instance_values``, který funkce čte, validuje nebo upravuje.
      :param serialize: Příznak ``serialize`` určující průběh nebo rozsah zpracování.
      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.
      :return: Vrací výsledek operace.

   .. py:method:: check_required_fields()

      Ověří required fields.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.

   .. py:method:: map_column_name_to_field_name()

      Provádí operaci map column name to field name.

      :param column_name: Textový název nebo klíč ``column_name`` používaný v rámci operace.

   .. py:method:: create_relations()

      Vytvoří relations. v aplikaci.

      :param instance: Instance modelu, které se operace týká.

   .. py:method:: record_postprocessing()

      Provádí operaci record postprocessing.

      :param record: Záznam, který funkce čte nebo upravuje.
      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.


.. py:class:: GeometryTransformMixin

   Mixin pro mappery s geometrickými poli. Při insertu zajišťuje konverzi mezi souřadnicovými systémy:

   WGS84 (SRID 4326) → S-JTSK (SRID 5514) a naopak.

   **Metody:**

   .. py:method:: transform_geometries()

      Transformuje geometries. v aplikaci.

      :param mapping_dict: Název nebo typ ``mapping_dict`` používaný pro volbu cílové logiky.
      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.


.. py:class:: MultipleClassImportModelMapper

   Základní třída pro mappery importující data do více modelů najednou.

   **Metody:**

   .. py:method:: import_validation()

      Načte validation. v aplikaci.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrací filter kwargs primary key.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
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

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: HeslarDataceMapper

   Mapovač pro model HeslarDatace.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: HeslarDokumentTypMaterialRadaMapper

   Mapovač pro model HeslarDokumentTypMaterialRada.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: HeslarHierarchieMapper

   Mapovač pro model HeslarHierarchie.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: HeslarOdkazMapper

   Mapovač pro model HeslarOdkaz.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: OrganizaceMapper

   Mapovač pro model Organizace.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: OsobaMapper

   Mapovač pro model Osoba.


.. py:class:: ProjektMapper

   Mapovač pro model Projekt.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :param instance_values: Záznam/objekt ``instance_values``, který funkce čte, validuje nebo upravuje.
      :param serialize: Příznak ``serialize`` určující průběh nebo rozsah zpracování.
      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: ProjektKatastrMapper

   Mapovač pro model ProjektKatastr.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: ProjektOznamovatelMapper

   Mapovač pro model Oznamovatel.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: SamostatnyNalezMapper

   Mapovač pro model SamostatnyNalez.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :param instance_values: Záznam/objekt ``instance_values``, který funkce čte, validuje nebo upravuje.
      :param serialize: Příznak ``serialize`` určující průběh nebo rozsah zpracování.
      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: ArcheologickyZaznamAkceMapper

   Mapovač pro modely ArcheologickyZaznam a Akce.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.

   .. py:method:: map_field()

      Provádí operaci map field.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.

   .. py:method:: record_postprocessing()

      Provádí operaci record postprocessing.

      :param record: Záznam, který funkce čte nebo upravuje.
      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.


.. py:class:: LokalitaMapper

   Mapovač pro modely ArcheologickyZaznam a Lokalita.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.

   .. py:method:: map_field()

      Provádí operaci map field.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.


.. py:class:: AkceVedouciMapper

   Mapovač pro model AkceVedouci.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: ArcheologickyZaznamKatastrMapper

   Mapovač pro model ArcheologickyZaznamKatastr.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: PianMapper

   Mapovač pro model Pian.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :param instance_values: Záznam/objekt ``instance_values``, který funkce čte, validuje nebo upravuje.
      :param serialize: Příznak ``serialize`` určující průběh nebo rozsah zpracování.
      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: DokumentacniJednotkaMapper

   Mapovač pro model DokumentacniJednotka.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.

   .. py:method:: record_postprocessing()

      Provádí operaci record postprocessing.

      :param record: Záznam, který funkce čte nebo upravuje.
      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.


.. py:class:: AdbMapper

   Mapovač pro model Adb.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: AdbVyskovyBod

   Mapovač pro model VyskovyBod.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: DokumentLetMapper

   Mapovač pro model Let.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: DokumentMapper

   Mapovač pro modely Dokument a DokumentExtraData.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.

   .. py:method:: map_field()

      Provádí operaci map field.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :param instance_values: Záznam/objekt ``instance_values``, který funkce čte, validuje nebo upravuje.
      :param serialize: Příznak ``serialize`` určující průběh nebo rozsah zpracování.
      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: DokumentAutorMapper

   Mapovač pro model DokumentAutor.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: DokumentJazykMapper

   Mapovač pro model DokumentJazyk.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: DokumentOsobaMapper

   Mapovač pro model DokumentOsoba.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: DokumentPosudekMapper

   Mapovač pro model DokumentPosudek.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: TvarMapper

   Mapovač pro model Tvar.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: DokumentCastMapper

   Mapovač pro model DokumentCast.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: NeidentAkceMapper

   Mapovač pro model NeidentAkce.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: NeidentAkceVedouciMapper

   Mapovač pro model NeidentAkceVedouci.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: KomponentaMapper

   Mapovač pro model Komponenta.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: KomponentaAktivitaMapper

   Mapovač pro model KomponentaAktivita.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: NalezMapper

   Základní mapper pro nálezy.


.. py:class:: NalezObjektMapper

   Mapovač pro model NalezObjekt.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: NalezPredmetMapper

   Mapovač pro model NalezPredmet.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: ExterniZdrojMapper

   Mapovač pro model ExterniZdroj.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: ExterniZdrojAutorMapper

   Mapovač pro model ExterniZdrojAutor.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: ExterniZdrojEditorMapper

   Mapovač pro model ExterniZdrojEditor.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: ExterniOdkazMapper

   Mapovač pro model ExterniOdkaz.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: UzivatelMapper

   Mapovač pro model User.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: UzivatelNotifikaceProjektMapper

   Mapovač pro model Pes (notifikace uživatele vázané na projekt či územní jednotku RUIAN).

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrací filter kwargs primary key.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: map_field()

      Provádí operaci map field.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _check_column_structure()

      Ověří column structure.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.
      :param instance_values: Záznam/objekt ``instance_values``, který funkce čte, validuje nebo upravuje.
      :param serialize: Příznak ``serialize`` určující průběh nebo rozsah zpracování.
      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: UzivatelSpolupraceMapper

   Mapovač pro model UzivatelSpoluprace.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: UzivatelOpravneniMapper

   Mapovač pro přiřazení skupinových oprávnění uživateli (model User).

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrací filter kwargs primary key.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.

   .. py:method:: import_validation()

      Načte validation. v aplikaci.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.


.. py:class:: SouborMapper

   Mapovač pro model Soubor.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.


.. py:class:: UzivatelNotifikaceMapper

   Mapovač pro přiřazení typů notifikací uživateli (model User).

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrací filter kwargs primary key.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.

   .. py:method:: import_validation()

      Načte validation. v aplikaci.

      :param performed_action: Záznam/objekt ``performed_action``, který funkce čte, validuje nebo upravuje.


.. py:class:: HistorieMapper

   Mapovač pro model Historie.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Příznak ``include_primary_key`` určující průběh nebo rozsah zpracování.

