CORE import_data_mappers
========================

Modul import_data_mappers.

Třídy
------

.. py:class:: ImportDataValidationResult

   Popis není k dispozici.


.. py:class:: ImportDataError

   Popis není k dispozici.


.. py:class:: ImportDataIncorrectStructureError

   Exception raised when the structure of the imported data does not match the expected structure.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataIncorrectStructureContentObjectError

   Exception raised when the structure of the imported data does not match the expected structure.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataMissingReferencedValueError

   Exception raised when a referenced value is missing in either database or in the imported data.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataIntegrityError

   Exception raised in two cases.
   During the import action: when a record with the same primary key already exists in the database
   During the update action: when a record with the specified primary key does not exist in the database.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataLimitChoicesError

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataHeslarPresnostLimitChoicesError

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataUnsupportedFileError

   Exception raised when an unsupported file name is included in the imported archive.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataUnsupportedMultipleFilesError

   Exception raised when an unsupported file name is included in the imported archive.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ImportDataIncorrectPrimaryKeyFormatError

   Exception raised when the primary key value does not match the expected format.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: BaseImportField

   Base class for import fields. Does not perform any validation or processing of the value.
   Used mostly for text fields.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: value()

   .. py:method:: value()

   .. py:method:: is_null()

   .. py:method:: instance_value()

   .. py:method:: serialized_value()

   .. py:method:: _process_value()


.. py:class:: IntegerImportField

   Class for import fields that should contain integer values.

   **Metody:**

   .. py:method:: _process_value()

      If the value is not a number, then the method raises ImportDataError. Otherwise it converts value to int.


.. py:class:: PositiveIntegerImportField

   Popis není k dispozici.

   **Metody:**

   .. py:method:: _process_value()


.. py:class:: DecimalImportField

   Popis není k dispozici.

   **Metody:**

   .. py:method:: _process_value()


.. py:class:: BooleanImportField

   Class for import fields that should contain boolean values.

   **Metody:**

   .. py:method:: _process_value()

      Tries to convert string value to bool. If the string value is not "true" or "false", then the exception
      ImportDataError is raised.


.. py:class:: DateImportField

   Class for import fields that should contain date values.

   **Metody:**

   .. py:method:: value()

   .. py:method:: value()

   .. py:method:: serialized_value()

   .. py:method:: _process_value()

      Tries to convert a string value to date. If the string value is not in the format "YYYY-MM-DD" or "DD.MM.YYYY",
      then the exception ImportDataError is raised.


.. py:class:: DateTimeImportField

   Class for import fields that should contain date and time values.

   **Metody:**

   .. py:method:: value()

   .. py:method:: value()

   .. py:method:: serialized_value()

   .. py:method:: _process_value()


.. py:class:: DateRangeImportField

   Class for import fields that should contain date-range values.

   **Metody:**

   .. py:method:: serialized_value()

   .. py:method:: _process_value()

      Tries to convert a string value to date. If the string value is not in the format "YYYY-MM-DD".
      then the exception ImportDataError is raised.


.. py:class:: LookupImportField

   Class for import fields that should contain a reference to another model instance.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: instance_value()

   .. py:method:: _check_limit_choices_to()

   .. py:method:: _process_value()

      Processes the value by checking if it exists in the database or in the imported records. If yes, it returns
      the record. If the referenced record does not exist, it raises ImportDataMissingReferencedValueError.


.. py:class:: RuianLookupImportField

   Based on the LookupImportField, this class is used for importing data from RUIAN data. It strips
   the "ruian-" prefix from the value and converts it to an integer.

   **Metody:**

   .. py:method:: value()


.. py:class:: VazbaLookupImportField

   Class for import field with referenced models for vazba (relation). This relation is 1:1 instead of 1:N
   and these fields manage relation to another model.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: _process_value()


.. py:class:: GeomImportField

   Class for import fields that should contain geometries.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: serialized_value()

   .. py:method:: _process_value()

      Tries to convert string value to geometry.


.. py:class:: GenericForeignKeyImportField

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: serialized_value()

   .. py:method:: _process_value()


.. py:class:: ImportModelMapper

   Base class for data import. The class loads data from the imported file, preprocesses all values based on the
   target field and creates a record.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: get_import_data_mapper_dict()

      Returns a child class based on the import file name.

   .. py:method:: get_import_data_mapper()

      Returns a child mapper class based on the file name, omitting the file extension.

   .. py:method:: get_mapping()

      Map imported values using the map_field method.

   .. py:method:: _get_filter_kwargs_primary_key()

      Returns a dict with primary key field name(s) and field value(s).

   .. py:method:: _parse_primary_key()

   .. py:method:: _parse_primary_key_custom_prefix()

   .. py:method:: map_field()

      Maps value to a specific BaseImportField instance or BaseImportField child instance.

   .. py:method:: is_field_required()

   .. py:method:: create_records()

      Create a record instance or multiple model instances that can be saved to database.

   .. py:method:: import_validation()

      Perform the validation based on the primary key. The record should not exist in databased when the insert action
      is performed. It should exist if the update action is performed. If one of the conditions is valid, the method
      returns a dict with mapped primary key field names and values.  Otherwise, the ImportDataIntegrityError
      error is raised.

   .. py:method:: _check_column_structure()

   .. py:method:: map()

      Checks if the file columns structure is valid as the first step. If not, the ImportDataIncorrectStructureError
      exception is raised. Then it creates a dict with field names as keys and values are instances of
      BaseImportField class or one of its child classes with values loaded from the import file.

   .. py:method:: check_required_fields()

   .. py:method:: map_column_name_to_field_name()

      Map a column name from the import file to the field name of the Django model. Used when the Django field
      name is different from a database column name.

   .. py:method:: create_relations()

      Creates relation fields for Historie, Koimponenty, and Soubory.

   .. py:method:: record_postprocessing()


.. py:class:: GeometryTransformMixin

   Popis není k dispozici.

   **Metody:**

   .. py:method:: transform_geometries()


.. py:class:: MultipleClassImportModelMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: import_validation()

   .. py:method:: _get_filter_kwargs_primary_key()

   .. py:method:: create_records()

   .. py:method:: is_field_required()


.. py:class:: HeslarMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: HeslarDataceMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: HeslarDokumentTypMaterialRadaMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: HeslarHierarchieMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: HeslarOdkazMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: OrganizaceMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: OsobaMapper

   Popis není k dispozici.


.. py:class:: ProjektMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: map()


.. py:class:: ProjektKatastrMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: ProjektOznamovatelMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: SamostatnyNalezMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: map()


.. py:class:: ArcheologickyZaznamAkceMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: map_field()

   .. py:method:: record_postprocessing()


.. py:class:: LokalitaMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: map_field()


.. py:class:: AkceVedouciMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: ArcheologickyZaznamKatastrMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: PianMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: map()


.. py:class:: DokumentacniJednotkaMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: record_postprocessing()


.. py:class:: AdbMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: AdbVyskovyBod

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: DokumentLetMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: DokumentMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: map_field()

   .. py:method:: create_records()

      Creates a Dokument instance and DokumentExtraData instance with relation to Dokument instance.

   .. py:method:: map()


.. py:class:: DokumentAutorMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: DokumentJazykMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: DokumentOsobaMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: DokumentPosudekMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: TvarMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: DokumentCastMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: NeidentAkceMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: NeidentAkceVedouciMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: KomponentaMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: KomponentaAktivitaMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: NalezMapper

   Popis není k dispozici.


.. py:class:: NalezObjektMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: NalezPredmetMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: ExterniZdrojMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: ExterniZdrojAutorMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: ExterniZdrojEditorMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: ExterniOdkazMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: UzivatelMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: UzivatelNotifikaceProjektMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_filter_kwargs_primary_key()

   .. py:method:: map_field()

   .. py:method:: create_records()

   .. py:method:: _check_column_structure()

   .. py:method:: map()


.. py:class:: UzivatelSpolupraceMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: UzivatelOpravneniMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_filter_kwargs_primary_key()

   .. py:method:: create_records()

   .. py:method:: import_validation()


.. py:class:: SouborMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()


.. py:class:: UzivatelNotifikaceMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()

   .. py:method:: _get_filter_kwargs_primary_key()

   .. py:method:: create_records()

   .. py:method:: import_validation()


.. py:class:: HistorieMapper

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_mapping()

