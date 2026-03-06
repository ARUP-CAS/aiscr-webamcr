XML_GENERATOR generator
=======================

Modul generator.

Třídy
------

.. py:class:: AsText

   Implementuje komponentu ``AsText`` v rámci aplikace.


.. py:class:: ParsedComment

   Implementuje komponentu ``ParsedComment`` v rámci aplikace.


.. py:class:: DocumentGenerator

   Implementuje komponentu ``DocumentGenerator`` v rámci aplikace.

   **Metody:**

   .. py:method:: _get_schema_dict()

      Vrací schema dict.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_schema_name()

      Vrací schema name.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _create_xpath_query()

      Vytvoří xpath query.

      :param model_name: Název modelu používaný pro cílení operace.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: get_path_to_schema()

      Vrací path to schema.

   .. py:method:: _parse_schema()

      Zpracuje schema.

      :param model_name: Název modelu používaný pro cílení operace.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _get_prefix()

      Vrací prefix.

      :param comment_text: Číselná hodnota ``comment_text`` použitá při výpočtu nebo transformaci.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _parse_comment()

      Zpracuje comment.

      :param comment_text: Číselná hodnota ``comment_text`` použitá při výpočtu nebo transformaci.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _get_attribute_of_record()

      Vrací attribute of record.

      :param attribute_name: Textový název nebo klíč ``attribute_name`` používaný v rámci operace.
      :param record: Záznam, který funkce čte nebo upravuje.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_attribute_of_record_unbounded()

      Vrací attribute of record unbounded.

      :param record: Záznam, který funkce čte nebo upravuje.
      :param parsed_comment: Číselná nebo geometrická hodnota `parsed_comment` použitá při výpočtu nebo transformaci.
      :param schema_element: Cesta, URL nebo název zdroje ``schema_element``, ze kterého funkce čte nebo kam zapisuje.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _create_element()

      Vytvoří element.

      :param schema_element: Cesta, URL nebo název zdroje ``schema_element``, ze kterého funkce čte nebo kam zapisuje.
      :param parent_element: Záznam/objekt ``parent_element``, který funkce čte, validuje nebo upravuje.
      :param parsed_comment: Číselná nebo geometrická hodnota `parsed_comment` použitá při výpočtu nebo transformaci.
      :param document_object: Záznam/objekt ``document_object``, který funkce čte, validuje nebo upravuje.
      :param id_field_prefix: Záznam/objekt ``id_field_prefix``, který funkce čte, validuje nebo upravuje.
      :param ref_type: Název nebo typ ``ref_type`` používaný pro volbu cílové logiky.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _create_many_to_many_ref_elements()

      Vytvoří many to many ref elements.

      :param schema_element: Cesta, URL nebo název zdroje ``schema_element``, ze kterého funkce čte nebo kam zapisuje.
      :param parent_element: Záznam/objekt ``parent_element``, který funkce čte, validuje nebo upravuje.
      :param related_records: Záznam/objekt ``related_records``, který funkce čte, validuje nebo upravuje.
      :param parsed_comment: Číselná nebo geometrická hodnota `parsed_comment` použitá při výpočtu nebo transformaci.
      :param prefix: Číselná hodnota ``prefix`` použitá při výpočtu nebo transformaci.
      :param ref_type: Název nebo typ ``ref_type`` používaný pro volbu cílové logiky.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _parse_scheme_create_element()

      Zpracuje scheme create element.

      :param schema_element: Cesta, URL nebo název zdroje ``schema_element``, ze kterého funkce čte nebo kam zapisuje.
      :param parent_element: Záznam/objekt ``parent_element``, který funkce čte, validuje nebo upravuje.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _iterate_unbound_records()

      Provádí operaci iterate unbound records.

      :param related_records: Záznam/objekt ``related_records``, který funkce čte, validuje nebo upravuje.
      :param schema_element: Cesta, URL nebo název zdroje ``schema_element``, ze kterého funkce čte nebo kam zapisuje.
      :param parent_element: Záznam/objekt ``parent_element``, který funkce čte, validuje nebo upravuje.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _parse_scheme_create_nested_element()

      Zpracuje scheme create nested element.

      :param schema_element: Cesta, URL nebo název zdroje ``schema_element``, ze kterého funkce čte nebo kam zapisuje.
      :param parent_element: Záznam/objekt ``parent_element``, který funkce čte, validuje nebo upravuje.
      :param document_object: Záznam/objekt ``document_object``, který funkce čte, validuje nebo upravuje.
      :param child_parent_element_name: Textový název nebo klíč ``child_parent_element_name`` používaný v rámci operace.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_ref_type_attribute_name()

      Vrací ref type attribute name.

      :param type_name: Název nebo typ ``type_name`` používaný pro volbu cílové logiky.

   .. py:method:: _replace_redundant_namespaces()

      Provádí operaci replace redundant namespaces.

      :param xml_string: Cesta, URL nebo název zdroje ``xml_string``, ze kterého funkce čte nebo kam zapisuje.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: generate_document()

      Vygeneruje document. v aplikaci.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param document_object: Záznam/objekt ``document_object``, který funkce čte, validuje nebo upravuje.

