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

      :param missing_columns: Vstupní hodnota ``missing_columns`` pro danou operaci.
      :param excess_columns: Vstupní hodnota ``excess_columns`` pro danou operaci.


.. py:class:: ImportDataIncorrectStructureContentObjectError

   Výjimka vyvolaná při nesouladu struktury obsahu importovaných dat s očekávanou strukturou (neplatná kombinace sloupců).

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param columns: Vstupní hodnota ``columns`` pro danou operaci.
      :param expected_colummns_options: Dodatečné poziční argumenty předané voláním.


.. py:class:: ImportDataMissingReferencedValueError

   Výjimka vyvolaná při chybějící hodnotě referencovaného záznamu — buď v databázi, nebo v importovaných datech.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param missing_value_id: Identifikátor objektu ``missing_value``.
      :param missing_model_name: Vstupní hodnota ``missing_model_name`` pro danou operaci.


.. py:class:: ImportDataIntegrityError

   Výjimka vyvolaná ve dvou případech:

   při insertu — pokud záznam se stejným primárním klíčem již v databázi existuje,
   při updatu — pokud záznam se zadaným primárním klíčem v databázi neexistuje.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record_id: Identifikátor objektu ``record``.
      :param model_name: Vstupní hodnota ``model_name`` pro danou operaci.
      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.


.. py:class:: ImportDataLimitChoicesError

   Výjimka vyvolaná při hodnotě cizího klíče, která nesplňuje omezení limit_choices_to.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record_id: Identifikátor objektu ``record``.
      :param limit_choices_to: Vstupní hodnota ``limit_choices_to`` pro danou operaci.


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

      :param file_name: Vstupní hodnota ``file_name`` pro danou operaci.


.. py:class:: ImportDataUnsupportedFilesError

   Výjimka vyvolaná při výskytu jednoho nebo více nepodporovaných názvů souborů v importovaném archivu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param file_names: Vstupní hodnota ``file_names`` pro danou operaci.


.. py:class:: ImportDataIncorrectPrimaryKeyFormatError

   Výjimka vyvolaná při nesouladu hodnoty primárního klíče s očekávaným formátem.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param primary_key_value: Vstupní hodnota ``primary_key_value`` pro danou operaci.


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

      :param value: Vstupní hodnota ``value`` pro danou operaci.

   .. py:method:: is_null()

      Určí, zda null.

   .. py:method:: instance_value()

      Provádí operaci instance value.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: IntegerImportField

   Importní pole pro hodnoty datového typu integer.

   **Metody:**

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: PositiveIntegerImportField

   Importní pole pro kladné celočíselné hodnoty. Záporná čísla způsobí vyvolání ImportDataError.

   **Metody:**

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: DecimalImportField

   Importní pole pro desetinná čísla (float).

   **Metody:**

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: BooleanImportField

   Importní pole pro hodnoty datového typu boolean.

   **Metody:**

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: DateImportField

   Importní pole pro hodnoty datového typu date.

   **Metody:**

   .. py:method:: value()

      Provádí operaci value.

   .. py:method:: value()

      Provádí operaci value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: DateTimeImportField

   Importní pole pro hodnoty datového typu datetime.

   Podporovaný formát: "YYYY-MM-DD HH:MM:SS".

   **Metody:**

   .. py:method:: value()

      Provádí operaci value.

   .. py:method:: value()

      Provádí operaci value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: DateRangeImportField

   Importní pole pro hodnoty datového typu date range.

   **Metody:**

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: LookupImportField

   Importní pole pro hodnoty odkazující na instanci jiného modelu (cizí klíč).

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param lookup_model_classes: Vstupní hodnota ``lookup_model_classes`` pro danou operaci.
      :param lookup_field_name: Vstupní hodnota ``lookup_field_name`` pro danou operaci.
      :param limit_choices_to: Vstupní hodnota ``limit_choices_to`` pro danou operaci.

   .. py:method:: instance_value()

      Provádí operaci instance value.

   .. py:method:: _check_limit_choices_to()

      Ověří limit choices to.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: RuianLookupImportField

   Rozšíření LookupImportField pro import dat z RUIAN. Odstraní prefix "ruian-" a převede hodnotu na integer.

   **Metody:**

   .. py:method:: value()

      Provádí operaci value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.


.. py:class:: VazbaLookupImportField

   Importní pole pro referencované modely přes vazbu (relaci). Relace je 1:1 místo 1:N.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param lookup_model_classes: Vstupní hodnota ``lookup_model_classes`` pro danou operaci.
      :param lookup_field_name: Vstupní hodnota ``lookup_field_name`` pro danou operaci.
      :param read_field_name: Vstupní hodnota ``read_field_name`` pro danou operaci.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: GeomImportField

   Importní pole pro geometrické hodnoty.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param srid: Vstupní hodnota ``srid`` pro danou operaci.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: GenericForeignKeyImportField

   Importní pole pro generický cizí klíč.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param lookup_model_classes: Vstupní hodnota ``lookup_model_classes`` pro danou operaci.
      :param lookup_field_name: Vstupní hodnota ``lookup_field_name`` pro danou operaci.
      :param serialized_attribute: Vstupní hodnota ``serialized_attribute`` pro danou operaci.

   .. py:method:: serialized_value()

      Provádí operaci serialized value.

   .. py:method:: _process_value()

      Provádí operaci process value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: ImportModelMapper

   Základní třída pro hromadný import dat. Načítá data z importovaného souboru,

   předzpracovává hodnoty podle cílového pole a vytváří záznamy.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param value_dict: Vstupní hodnota ``value_dict`` pro danou operaci.

   .. py:method:: get_import_data_mapper_dict()

      Vrátí slovník mapující názvy importních souborů na příslušné třídy mapperů.

   .. py:method:: get_import_data_mapper()

      Vrátí třídu mapperu odpovídající zadanému názvu souboru (bez přípony).

      :param file_name: Popis parametru ``file_name``.

   .. py:method:: get_mapping()

      Vrátí slovník mapování polí pomocí metody map_field.

      :param include_primary_key: Popis parametru ``include_primary_key``.
      :return: Vrací výsledek operace.

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrátí slovník s názvem (názvy) a hodnotou (hodnotami) primárního klíče pro filtrování.

   .. py:method:: _parse_primary_key()

      Zpracuje primary key.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _parse_primary_key_custom_prefix()

      Zpracuje primary key custom prefix.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :param prefix: Vstupní hodnota ``prefix`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: map_field()

      Namapuje pole modelu na odpovídající instanci BaseImportField nebo její podtřídy.

      :param field_name: Popis parametru ``field_name``.

   .. py:method:: is_field_required()

      Určí, zda field required.

      :param field_name: Vstupní hodnota ``field_name`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: import_validation()

      Provede validaci na základě primárního klíče. Při insertu záznam nesmí existovat,

      při updatu musí existovat. Vrátí slovník s primárními klíči, nebo vyvolá ImportDataIntegrityError.

      :param performed_action: Popis parametru ``performed_action``.
      :return: Vrací výsledek operace.

   .. py:method:: _check_column_structure()

      Ověří column structure.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: map()

      Nejprve ověří strukturu sloupců souboru — při nesouladu vyvolá ImportDataIncorrectStructureError.

      Poté vrátí slovník s názvy polí jako klíči a instancemi BaseImportField s načtenými hodnotami jako hodnotami.

      :param performed_action: Popis parametru ``performed_action``.
      :param instance_values: Popis parametru ``instance_values``.
      :param serialize: Popis parametru ``serialize``.
      :param include_primary_key: Popis parametru ``include_primary_key``.
      :return: Vrací výsledek operace.

   .. py:method:: check_required_fields()

      Ověří required fields.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.

   .. py:method:: map_column_name_to_field_name()

      Provádí operaci map column name to field name.

      :param column_name: Vstupní hodnota ``column_name`` pro danou operaci.

   .. py:method:: create_relations()

      Vytvoří relations. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.

   .. py:method:: record_postprocessing()

      Provádí operaci record postprocessing.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
      :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.


.. py:class:: GeometryTransformMixin

   Mixin pro mappery s geometrickými poli. Při insertu zajišťuje konverzi mezi souřadnicovými systémy:

   WGS84 (SRID 4326) → S-JTSK (SRID 5514) a naopak.

   **Metody:**

   .. py:method:: transform_geometries()

      Transformuje geometries. v aplikaci.

      :param mapping_dict: Vstupní hodnota ``mapping_dict`` pro danou operaci.
      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.


.. py:class:: MultipleClassImportModelMapper

   Základní třída pro mappery importující data do více modelů najednou.

   **Metody:**

   .. py:method:: import_validation()

      Načte validation. v aplikaci.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrací filter kwargs primary key.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: is_field_required()

      Určí, zda field required.

      :param field_name: Vstupní hodnota ``field_name`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: HeslarMapper

   Mapovač pro model Heslar.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: HeslarDataceMapper

   Mapovač pro model HeslarDatace.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: HeslarDokumentTypMaterialRadaMapper

   Mapovač pro model HeslarDokumentTypMaterialRada.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: HeslarHierarchieMapper

   Mapovač pro model HeslarHierarchie.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: HeslarOdkazMapper

   Mapovač pro model HeslarOdkaz.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: OrganizaceMapper

   Mapovač pro model Organizace.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: OsobaMapper

   Mapovač pro model Osoba.


.. py:class:: ProjektMapper

   Mapovač pro model Projekt.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
      :param instance_values: Vstupní hodnota ``instance_values`` pro danou operaci.
      :param serialize: Vstupní hodnota ``serialize`` pro danou operaci.
      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: ProjektKatastrMapper

   Mapovač pro model ProjektKatastr.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: ProjektOznamovatelMapper

   Mapovač pro model Oznamovatel.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: SamostatnyNalezMapper

   Mapovač pro model SamostatnyNalez.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
      :param instance_values: Vstupní hodnota ``instance_values`` pro danou operaci.
      :param serialize: Vstupní hodnota ``serialize`` pro danou operaci.
      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: ArcheologickyZaznamAkceMapper

   Mapovač pro modely ArcheologickyZaznam a Akce.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.

   .. py:method:: map_field()

      Provádí operaci map field.

      :param field_name: Vstupní hodnota ``field_name`` pro danou operaci.

   .. py:method:: record_postprocessing()

      Provádí operaci record postprocessing.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
      :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.


.. py:class:: LokalitaMapper

   Mapovač pro modely ArcheologickyZaznam a Lokalita.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.

   .. py:method:: map_field()

      Provádí operaci map field.

      :param field_name: Vstupní hodnota ``field_name`` pro danou operaci.


.. py:class:: AkceVedouciMapper

   Mapovač pro model AkceVedouci.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: ArcheologickyZaznamKatastrMapper

   Mapovač pro model ArcheologickyZaznamKatastr.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: PianMapper

   Mapovač pro model Pian.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
      :param instance_values: Vstupní hodnota ``instance_values`` pro danou operaci.
      :param serialize: Vstupní hodnota ``serialize`` pro danou operaci.
      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: DokumentacniJednotkaMapper

   Mapovač pro model DokumentacniJednotka.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.

   .. py:method:: record_postprocessing()

      Provádí operaci record postprocessing.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
      :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.


.. py:class:: AdbMapper

   Mapovač pro model Adb.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: AdbVyskovyBod

   Mapovač pro model VyskovyBod.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: DokumentLetMapper

   Mapovač pro model Let.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: DokumentMapper

   Mapovač pro modely Dokument a DokumentExtraData.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.

   .. py:method:: map_field()

      Provádí operaci map field.

      :param field_name: Vstupní hodnota ``field_name`` pro danou operaci.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
      :param instance_values: Vstupní hodnota ``instance_values`` pro danou operaci.
      :param serialize: Vstupní hodnota ``serialize`` pro danou operaci.
      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: DokumentAutorMapper

   Mapovač pro model DokumentAutor.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: DokumentJazykMapper

   Mapovač pro model DokumentJazyk.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: DokumentOsobaMapper

   Mapovač pro model DokumentOsoba.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: DokumentPosudekMapper

   Mapovač pro model DokumentPosudek.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: TvarMapper

   Mapovač pro model Tvar.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: DokumentCastMapper

   Mapovač pro model DokumentCast.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: NeidentAkceMapper

   Mapovač pro model NeidentAkce.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: NeidentAkceVedouciMapper

   Mapovač pro model NeidentAkceVedouci.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: KomponentaMapper

   Mapovač pro model Komponenta.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: KomponentaAktivitaMapper

   Mapovač pro model KomponentaAktivita.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: NalezMapper

   Základní mapper pro nálezy.


.. py:class:: NalezObjektMapper

   Mapovač pro model NalezObjekt.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: NalezPredmetMapper

   Mapovač pro model NalezPredmet.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: ExterniZdrojMapper

   Mapovač pro model ExterniZdroj.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: ExterniZdrojAutorMapper

   Mapovač pro model ExterniZdrojAutor.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: ExterniZdrojEditorMapper

   Mapovač pro model ExterniZdrojEditor.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: ExterniOdkazMapper

   Mapovač pro model ExterniOdkaz.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: UzivatelMapper

   Mapovač pro model User.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: UzivatelNotifikaceProjektMapper

   Mapovač pro model Pes (notifikace uživatele vázané na projekt či územní jednotku RUIAN).

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrací filter kwargs primary key.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: map_field()

      Provádí operaci map field.

      :param field_name: Vstupní hodnota ``field_name`` pro danou operaci.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _check_column_structure()

      Ověří column structure.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: map()

      Provádí operaci map.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
      :param instance_values: Vstupní hodnota ``instance_values`` pro danou operaci.
      :param serialize: Vstupní hodnota ``serialize`` pro danou operaci.
      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: UzivatelSpolupraceMapper

   Mapovač pro model UzivatelSpoluprace.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: UzivatelOpravneniMapper

   Mapovač pro přiřazení skupinových oprávnění uživateli (model User).

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrací filter kwargs primary key.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.

   .. py:method:: import_validation()

      Načte validation. v aplikaci.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.


.. py:class:: SouborMapper

   Mapovač pro model Soubor.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.


.. py:class:: UzivatelNotifikaceMapper

   Mapovač pro přiřazení typů notifikací uživateli (model User).

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrací filter kwargs primary key.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: create_records()

      Vytvoří records. v aplikaci.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.

   .. py:method:: import_validation()

      Načte validation. v aplikaci.

      :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.


.. py:class:: HistorieMapper

   Mapovač pro model Historie.

   **Metody:**

   .. py:method:: get_mapping()

      Vrací mapping. v aplikaci.

      :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.

