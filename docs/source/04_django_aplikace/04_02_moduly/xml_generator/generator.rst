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

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_schema_name()

      Vrací schema name.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _create_xpath_query()

      Vytvoří xpath query.

      :param model_name: Vstupní hodnota ``model_name`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: get_path_to_schema()

      Vrací path to schema.

   .. py:method:: _parse_schema()

      Zpracuje schema.

      :param model_name: Vstupní hodnota ``model_name`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _get_prefix()

      Vrací prefix.

      :param comment_text: Vstupní hodnota ``comment_text`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _parse_comment()

      Zpracuje comment.

      :param comment_text: Vstupní hodnota ``comment_text`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _get_attribute_of_record()

      Vrací attribute of record.

      :param attribute_name: Vstupní hodnota ``attribute_name`` pro danou operaci.
      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_attribute_of_record_unbounded()

      Vrací attribute of record unbounded.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :param parsed_comment: Vstupní hodnota ``parsed_comment`` pro danou operaci.
      :param schema_element: Vstupní hodnota ``schema_element`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _create_element()

      Vytvoří element.

      :param schema_element: Vstupní hodnota ``schema_element`` pro danou operaci.
      :param parent_element: Vstupní hodnota ``parent_element`` pro danou operaci.
      :param parsed_comment: Vstupní hodnota ``parsed_comment`` pro danou operaci.
      :param document_object: Vstupní hodnota ``document_object`` pro danou operaci.
      :param id_field_prefix: Vstupní hodnota ``id_field_prefix`` pro danou operaci.
      :param ref_type: Vstupní hodnota ``ref_type`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _create_many_to_many_ref_elements()

      Vytvoří many to many ref elements.

      :param schema_element: Vstupní hodnota ``schema_element`` pro danou operaci.
      :param parent_element: Vstupní hodnota ``parent_element`` pro danou operaci.
      :param related_records: Vstupní hodnota ``related_records`` pro danou operaci.
      :param parsed_comment: Vstupní hodnota ``parsed_comment`` pro danou operaci.
      :param prefix: Vstupní hodnota ``prefix`` pro danou operaci.
      :param ref_type: Vstupní hodnota ``ref_type`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _parse_scheme_create_element()

      Zpracuje scheme create element.

      :param schema_element: Vstupní hodnota ``schema_element`` pro danou operaci.
      :param parent_element: Vstupní hodnota ``parent_element`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _iterate_unbound_records()

      Provádí operaci iterate unbound records.

      :param related_records: Vstupní hodnota ``related_records`` pro danou operaci.
      :param schema_element: Vstupní hodnota ``schema_element`` pro danou operaci.
      :param parent_element: Vstupní hodnota ``parent_element`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _parse_scheme_create_nested_element()

      Zpracuje scheme create nested element.

      :param schema_element: Vstupní hodnota ``schema_element`` pro danou operaci.
      :param parent_element: Vstupní hodnota ``parent_element`` pro danou operaci.
      :param document_object: Vstupní hodnota ``document_object`` pro danou operaci.
      :param child_parent_element_name: Vstupní hodnota ``child_parent_element_name`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_ref_type_attribute_name()

      Vrací ref type attribute name.

      :param type_name: Vstupní hodnota ``type_name`` pro danou operaci.

   .. py:method:: _replace_redundant_namespaces()

      Provádí operaci replace redundant namespaces.

      :param xml_string: Vstupní hodnota ``xml_string`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: generate_document()

      Vygeneruje document. v aplikaci.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param document_object: Vstupní hodnota ``document_object`` pro danou operaci.

