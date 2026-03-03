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


.. py:class:: ImportDataIncorrectStructureContentObjectError

   Výjimka vyvolaná při nesouladu struktury obsahu importovaných dat s očekávanou strukturou (neplatná kombinace sloupců).

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataMissingReferencedValueError

   Výjimka vyvolaná při chybějící hodnotě referencovaného záznamu — buď v databázi, nebo v importovaných datech.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataIntegrityError

   Výjimka vyvolaná ve dvou případech:
   při insertu — pokud záznam se stejným primárním klíčem již v databázi existuje,
   při updatu — pokud záznam se zadaným primárním klíčem v databázi neexistuje.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataLimitChoicesError

   Výjimka vyvolaná při hodnotě cizího klíče, která nesplňuje omezení limit_choices_to.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataHeslarPresnostLimitChoicesError

   Výjimka vyvolaná při neplatné hodnotě přesnosti v hesláři u importovaného záznamu.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataUnsupportedFileError

   Výjimka vyvolaná při výskytu nepodporovaného názvu souboru v importovaném archivu.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataUnsupportedFilesError

   Výjimka vyvolaná při výskytu jednoho nebo více nepodporovaných názvů souborů v importovaném archivu.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataIncorrectPrimaryKeyFormatError

   Výjimka vyvolaná při nesouladu hodnoty primárního klíče s očekávaným formátem.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: BaseImportField

   Základní třída pro importní pole. Neprovádí žádnou validaci ani zpracování hodnoty.
   Používá se především pro textová pole.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: value()

   .. py:method:: value()

   .. py:method:: is_null()

   .. py:method:: instance_value()

   .. py:method:: serialized_value()

   .. py:method:: _process_value()


.. py:class:: IntegerImportField

   Importní pole pro hodnoty datového typu integer.

   **Metody:**

   .. py:method:: _process_value()

      Převede hodnotu na int. Pokud hodnota není číslo, vyvolá ImportDataError.


.. py:class:: PositiveIntegerImportField

   Importní pole pro kladné celočíselné hodnoty. Záporná čísla způsobí vyvolání ImportDataError.

   **Metody:**

   .. py:method:: _process_value()


.. py:class:: DecimalImportField

   Importní pole pro desetinná čísla (float).

   **Metody:**

   .. py:method:: _process_value()


.. py:class:: BooleanImportField

   Importní pole pro hodnoty datového typu boolean.

   **Metody:**

   .. py:method:: _process_value()

      Převede řetězec na bool. Pokud hodnota není "true"/"1" ani "false"/"0", vyvolá ImportDataError.


.. py:class:: DateImportField

   Importní pole pro hodnoty datového typu date.

   **Metody:**

   .. py:method:: value()

   .. py:method:: value()

   .. py:method:: serialized_value()

   .. py:method:: _process_value()

      Převede řetězec na datum. Podporované formáty jsou "YYYY-MM-DD" a "DD.MM.YYYY".
      Pokud hodnota neodpovídá žádnému formátu, vyvolá ImportDataError.


.. py:class:: DateTimeImportField

   Importní pole pro hodnoty datového typu datetime.
   Podporovaný formát: "YYYY-MM-DD HH:MM:SS".

   **Metody:**

   .. py:method:: value()

   .. py:method:: value()

   .. py:method:: serialized_value()

   .. py:method:: _process_value()


.. py:class:: DateRangeImportField

   Importní pole pro hodnoty datového typu date range.

   **Metody:**

   .. py:method:: serialized_value()

   .. py:method:: _process_value()

      Převede řetězec na DateRange ve formátu "[YYYY-MM-DD, YYYY-MM-DD)".
      Pokud hodnota neodpovídá očekávanému formátu, vyvolá ImportDataError.


.. py:class:: LookupImportField

   Importní pole pro hodnoty odkazující na instanci jiného modelu (cizí klíč).

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: instance_value()

   .. py:method:: _check_limit_choices_to()

   .. py:method:: _process_value()

      Ověří existenci hodnoty v databázi nebo v importovaných záznamech a vrátí odpovídající záznam.
      Pokud referencovaný záznam neexistuje, vyvolá ImportDataMissingReferencedValueError.


.. py:class:: RuianLookupImportField

   Rozšíření LookupImportField pro import dat z RUIAN. Odstraní prefix "ruian-" a převede hodnotu na integer.

   **Metody:**

   .. py:method:: value()


.. py:class:: VazbaLookupImportField

   Importní pole pro referencované modely přes vazbu (relaci). Relace je 1:1 místo 1:N.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: _process_value()


.. py:class:: GeomImportField

   Importní pole pro geometrické hodnoty.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: serialized_value()

   .. py:method:: _process_value()

      Převede řetězec na objekt GEOSGeometry. Pokud převod selže, vyvolá ImportDataError.


.. py:class:: GenericForeignKeyImportField

   Importní pole pro generický cizí klíč.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: serialized_value()

   .. py:method:: _process_value()


.. py:class:: ImportModelMapper

   Základní třída pro hromadný import dat. Načítá data z importovaného souboru,
   předzpracovává hodnoty podle cílového pole a vytváří záznamy.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: get_import_data_mapper_dict()

      Vrátí slovník mapující názvy importních souborů na příslušné třídy mapperů.

   .. py:method:: get_import_data_mapper()

      Vrátí třídu mapperu odpovídající zadanému názvu souboru (bez přípony).

   .. py:method:: get_mapping()

      Vrátí slovník mapování polí pomocí metody map_field.

   .. py:method:: _get_filter_kwargs_primary_key()

      Vrátí slovník s názvem (názvy) a hodnotou (hodnotami) primárního klíče pro filtrování.

   .. py:method:: _parse_primary_key()

   .. py:method:: _parse_primary_key_custom_prefix()

   .. py:method:: map_field()

      Namapuje pole modelu na odpovídající instanci BaseImportField nebo její podtřídy.

   .. py:method:: is_field_required()

   .. py:method:: create_records()

      Vytvoří instanci záznamu nebo více instancí modelů připravených k uložení do databáze.

   .. py:method:: import_validation()

      Provede validaci na základě primárního klíče. Při insertu záznam nesmí existovat,
      při updatu musí existovat. Vrátí slovník s primárními klíči, nebo vyvolá ImportDataIntegrityError.

   .. py:method:: _check_column_structure()

   .. py:method:: map()

      Nejprve ověří strukturu sloupců souboru — při nesouladu vyvolá ImportDataIncorrectStructureError.
      Poté vrátí slovník s názvy polí jako klíči a instancemi BaseImportField s načtenými hodnotami jako hodnotami.

   .. py:method:: check_required_fields()

   .. py:method:: map_column_name_to_field_name()

      Převede název sloupce z importního souboru na název pole Django modelu.
      Používá se, pokud se název pole liší od názvu databázového sloupce.

   .. py:method:: create_relations()

      Vytvoří vazební záznamy pro Historie, Komponenty a Soubory, pokud ještě neexistují.

   .. py:method:: record_postprocessing()

   .. py:method:: updated_ident_cely_set()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: GeometryTransformMixin

   Mixin pro mappery s geometrickými poli. Při insertu zajišťuje konverzi mezi souřadnicovými systémy:
   WGS84 (SRID 4326) → S-JTSK (SRID 5514) a naopak.

   **Metody:**

   .. py:method:: transform_geometries()


.. py:class:: MultipleClassImportModelMapper

   Základní třída pro mappery importující data do více modelů najednou.

   **Metody:**

   .. py:method:: import_validation()

   .. py:method:: _get_filter_kwargs_primary_key()

   .. py:method:: create_records()

   .. py:method:: is_field_required()


.. py:class:: HeslarMapper

   Mapper pro model Heslar.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: HeslarDataceMapper

   Mapper pro model HeslarDatace.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: HeslarDokumentTypMaterialRadaMapper

   Mapper pro model HeslarDokumentTypMaterialRada.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: HeslarHierarchieMapper

   Mapper pro model HeslarHierarchie.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: HeslarOdkazMapper

   Mapper pro model HeslarOdkaz.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: OrganizaceMapper

   Mapper pro model Organizace.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: OsobaMapper

   Mapper pro model Osoba.


.. py:class:: ProjektMapper

   Mapper pro model Projekt.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: map()


.. py:class:: ProjektKatastrMapper

   Mapper pro model ProjektKatastr.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: ProjektOznamovatelMapper

   Mapper pro model Oznamovatel.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: SamostatnyNalezMapper

   Mapper pro model SamostatnyNalez.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: map()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: ArcheologickyZaznamAkceMapper

   Mapper pro modely ArcheologickyZaznam a Akce.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: map_field()

   .. py:method:: record_postprocessing()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: LokalitaMapper

   Mapper pro modely ArcheologickyZaznam a Lokalita.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: map_field()


.. py:class:: AkceVedouciMapper

   Mapper pro model AkceVedouci.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: ArcheologickyZaznamKatastrMapper

   Mapper pro model ArcheologickyZaznamKatastr.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: PianMapper

   Mapper pro model Pian.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: map()


.. py:class:: DokumentacniJednotkaMapper

   Mapper pro model DokumentacniJednotka.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: record_postprocessing()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: AdbMapper

   Mapper pro model Adb.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: AdbVyskovyBod

   Mapper pro model VyskovyBod.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: DokumentLetMapper

   Mapper pro model Let.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: DokumentMapper

   Mapper pro modely Dokument a DokumentExtraData.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: map_field()

   .. py:method:: create_records()

      Vytvoří instanci Dokument a DokumentExtraData s vazbou na Dokument.

   .. py:method:: map()


.. py:class:: DokumentAutorMapper

   Mapper pro model DokumentAutor.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: DokumentJazykMapper

   Mapper pro model DokumentJazyk.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: DokumentOsobaMapper

   Mapper pro model DokumentOsoba.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: DokumentPosudekMapper

   Mapper pro model DokumentPosudek.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: TvarMapper

   Mapper pro model Tvar.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: DokumentCastMapper

   Mapper pro model DokumentCast.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: NeidentAkceMapper

   Mapper pro model NeidentAkce.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: NeidentAkceVedouciMapper

   Mapper pro model NeidentAkceVedouci.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: KomponentaMapper

   Mapper pro model Komponenta.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: KomponentaAktivitaMapper

   Mapper pro model KomponentaAktivita.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: NalezMapper

   Základní mapper pro nálezy.

   **Metody:**

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: NalezObjektMapper

   Mapper pro model NalezObjekt.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: NalezPredmetMapper

   Mapper pro model NalezPredmet.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: ExterniZdrojMapper

   Mapper pro model ExterniZdroj.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: ExterniZdrojAutorMapper

   Mapper pro model ExterniZdrojAutor.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: ExterniZdrojEditorMapper

   Mapper pro model ExterniZdrojEditor.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: ExterniOdkazMapper

   Mapper pro model ExterniOdkaz.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: UzivatelMapper

   Mapper pro model User.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: UzivatelNotifikaceProjektMapper

   Mapper pro model Pes (notifikace uživatele vázané na projekt či územní jednotku RUIAN).

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_filter_kwargs_primary_key()

   .. py:method:: map_field()

   .. py:method:: create_records()

   .. py:method:: _check_column_structure()

   .. py:method:: map()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: UzivatelSpolupraceMapper

   Mapper pro model UzivatelSpoluprace.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: UzivatelOpravneniMapper

   Mapper pro přiřazení skupinových oprávnění uživateli (model User).

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_filter_kwargs_primary_key()

   .. py:method:: create_records()

   .. py:method:: import_validation()


.. py:class:: SouborMapper

   Mapper pro model Soubor.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()


.. py:class:: UzivatelNotifikaceMapper

   Mapper pro přiřazení typů notifikací uživateli (model User).

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_filter_kwargs_primary_key()

   .. py:method:: create_records()

   .. py:method:: import_validation()


.. py:class:: HistorieMapper

   Mapper pro model Historie.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_updated_ident_cely_record_list()

