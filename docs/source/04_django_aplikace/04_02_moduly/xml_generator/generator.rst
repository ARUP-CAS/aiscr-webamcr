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

      :return: Vrací výsledek volání ``join()``.

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
      :param record: Parametr ``record`` předává se do volání ``getattr()``, ``isinstance()``, pracuje se s atributy ``__class__``, ``pk``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_attribute_of_record_unbounded()

      Vrací attribute of record unbounded.

      :param record: Parametr ``record`` předává se do volání ``get_attribute()``.
      :param parsed_comment: Parametr ``parsed_comment`` se předává do volání ``get_attribute()``, pracuje se s atributy ``value_field_name``, ``attribute_field_names``, ovlivňuje větvení podmínek.
      :param schema_element: Parametr ``schema_element`` slouží jako vstup pro logiku funkce ``_get_attribute_of_record_unbounded``.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _create_element()

      Vytvoří element.

      :param schema_element: Parametr ``schema_element`` se předává do volání ``SubElement()``, pracuje se s atributy ``attrib``.
      :param parent_element: Parametr ``parent_element`` předává se do volání ``SubElement()``.
      :param parsed_comment: Parametr ``parsed_comment`` se předává do volání ``_get_attribute_of_record()``, pracuje se s atributy ``value_field_name``, ``attribute_field_names``, ovlivňuje větvení podmínek.
      :param document_object: Parametr ``document_object`` předává se do volání ``_get_attribute_of_record()``, ovlivňuje větvení podmínek.
      :param id_field_prefix: Parametr ``id_field_prefix`` ovlivňuje větvení podmínek.
      :param ref_type: Parametr ``ref_type`` předává se do volání ``get_ref_type_attribute_name()``, ovlivňuje větvení podmínek.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _create_many_to_many_ref_elements()

      Vytvoří many to many ref elements.

      :param schema_element: Parametr ``schema_element`` se předává do volání ``SubElement()``, pracuje se s atributy ``attrib``.
      :param parent_element: Parametr ``parent_element`` předává se do volání ``SubElement()``.
      :param related_records: Parametr ``related_records`` předává se do volání ``enumerate()``.
      :param parsed_comment: Parametr ``parsed_comment`` se předává do volání ``len()``, pracuje se s atributy ``attribute_field_names``, ovlivňuje větvení podmínek.
      :param prefix: Číselná hodnota ``prefix`` použitá při výpočtu nebo transformaci.
      :param ref_type: Parametr ``ref_type`` předává se do volání ``get_ref_type_attribute_name()``, ovlivňuje větvení podmínek.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _parse_scheme_create_element()

             Zpracuje scheme create element.

             :param schema_element: Parametr ``schema_element`` se předává do volání ``_create_element()``, ``_parse_schema()``, pracuje se s atributy ``__class__``, ``getnext``, ovlivňuje větvení podmínek.
             :param parent_element: Parametr ``parent_element`` předává se do volání ``_create_element()``, ``_parse_scheme_create_nested_element()``.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _iterate_unbound_records()

             Provádí operaci iterate unbound records.

             :param related_records: Parametr ``related_records`` slouží jako vstup pro logiku funkce ``_iterate_unbound_records``.
             :param schema_element: Parametr ``schema_element`` se předává do volání ``_parse_schema()``, ``_parse_scheme_create_nested_element()``, pracuje se s atributy ``attrib``.
             :param parent_element: Parametr ``parent_element`` předává se do volání ``_parse_scheme_create_nested_element()``.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _parse_scheme_create_nested_element()

             Zpracuje scheme create nested element.

             :param schema_element: Parametr ``schema_element`` slouží jako vstup pro logiku funkce ``_parse_scheme_create_nested_element``.
             :param parent_element: Parametr ``parent_element`` předává se do volání ``SubElement()``.
             :param document_object: Parametr ``document_object`` předává se do volání ``_create_element()``, ``_get_attribute_of_record()``.
             :param child_parent_element_name: Textový název nebo klíč ``child_parent_element_name`` používaný v rámci operace.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_ref_type_attribute_name()

      Vrací ref type attribute name.

      :param type_name: Parametr ``type_name`` předává se do volání ``get()``, pracuje se s atributy ``replace``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``get()``.

   .. py:method:: _replace_redundant_namespaces()

             Provádí operaci replace redundant namespaces.

             :param xml_string: Parametr ``xml_string`` se předává do volání ``sub()``, ``fromstring()``, pracuje se s atributy ``decode``, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: generate_document()

      Vygeneruje document. v aplikaci.

      :return: Vrací proměnná ``xml_string``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param document_object: Parametr ``document_object`` slouží jako vstup pro logiku funkce ``__init__``.

