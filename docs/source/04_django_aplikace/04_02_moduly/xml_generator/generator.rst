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

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_schema_name()

      Vrací schema name.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _create_xpath_query()

      Vytvoří xpath query.

      **Parametry:**

      - ``model_name``: Název modelu používaný pro cílení operace.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: get_path_to_schema()

      Vrací path to schema.

      **Návratová hodnota:**

      Vrací výsledek volání ``join()``.


   .. py:method:: _parse_schema()

      Zpracuje schema.

      **Parametry:**

      - ``model_name``: Název modelu používaný pro cílení operace.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _get_prefix()

      Vrací prefix.

      **Parametry:**

      - ``comment_text``: Číselná hodnota ``comment_text`` použitá při výpočtu nebo transformaci.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _parse_comment()

      Zpracuje comment.

      **Parametry:**

      - ``comment_text``: Číselná hodnota ``comment_text`` použitá při výpočtu nebo transformaci.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _get_attribute_of_record()

      Vrací attribute of record.

      **Parametry:**

      - ``attribute_name``: Textový název nebo klíč ``attribute_name`` používaný v rámci operace.
      - ``record``: Parametr ``record`` předává se do volání ``getattr()``, ``isinstance()``, pracuje se s atributy ``__class__``, ``pk``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_attribute_of_record_unbounded()

      Vrací attribute of record unbounded.

      **Parametry:**

      - ``record``: Parametr ``record`` předává se do volání ``get_attribute()``.
      - ``parsed_comment``: Parametr ``parsed_comment`` se předává do volání ``get_attribute()``, pracuje se s atributy ``value_field_name``, ``attribute_field_names``, ovlivňuje větvení podmínek.
      - ``schema_element``: Parametr ``schema_element`` slouží jako vstup pro logiku funkce ``_get_attribute_of_record_unbounded``.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _create_element()

      Vytvoří element.

      **Parametry:**

      - ``schema_element``: Parametr ``schema_element`` se předává do volání ``SubElement()``, pracuje se s atributy ``attrib``.
      - ``parent_element``: Parametr ``parent_element`` předává se do volání ``SubElement()``.
      - ``parsed_comment``: Parametr ``parsed_comment`` se předává do volání ``_get_attribute_of_record()``, pracuje se s atributy ``value_field_name``, ``attribute_field_names``, ovlivňuje větvení podmínek.
      - ``document_object``: Parametr ``document_object`` předává se do volání ``_get_attribute_of_record()``, ovlivňuje větvení podmínek.
      - ``id_field_prefix``: Parametr ``id_field_prefix`` ovlivňuje větvení podmínek.
      - ``ref_type``: Parametr ``ref_type`` předává se do volání ``get_ref_type_attribute_name()``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: _create_many_to_many_ref_elements()

      Vytvoří many to many ref elements.

      **Parametry:**

      - ``schema_element``: Parametr ``schema_element`` se předává do volání ``SubElement()``, pracuje se s atributy ``attrib``.
      - ``parent_element``: Parametr ``parent_element`` předává se do volání ``SubElement()``.
      - ``related_records``: Parametr ``related_records`` předává se do volání ``enumerate()``.
      - ``parsed_comment``: Parametr ``parsed_comment`` se předává do volání ``len()``, pracuje se s atributy ``attribute_field_names``, ovlivňuje větvení podmínek.
      - ``prefix``: Číselná hodnota ``prefix`` použitá při výpočtu nebo transformaci.
      - ``ref_type``: Parametr ``ref_type`` předává se do volání ``get_ref_type_attribute_name()``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: _parse_scheme_create_element()

      Zpracuje scheme create element.

      **Parametry:**

      - ``schema_element``: Parametr ``schema_element`` se předává do volání ``_create_element()``, ``_parse_schema()``, pracuje se s atributy ``__class__``, ``getnext``, ovlivňuje větvení podmínek.
      - ``parent_element``: Parametr ``parent_element`` předává se do volání ``_create_element()``, ``_parse_scheme_create_nested_element()``.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _iterate_unbound_records()

      Provádí operaci iterate unbound records.

      **Parametry:**

      - ``related_records``: Parametr ``related_records`` slouží jako vstup pro logiku funkce ``_iterate_unbound_records``.
      - ``schema_element``: Parametr ``schema_element`` se předává do volání ``_parse_schema()``, ``_parse_scheme_create_nested_element()``, pracuje se s atributy ``attrib``.
      - ``parent_element``: Parametr ``parent_element`` předává se do volání ``_parse_scheme_create_nested_element()``.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _parse_scheme_create_nested_element()

      Zpracuje scheme create nested element.

      **Parametry:**

      - ``schema_element``: Parametr ``schema_element`` slouží jako vstup pro logiku funkce ``_parse_scheme_create_nested_element``.
      - ``parent_element``: Parametr ``parent_element`` předává se do volání ``SubElement()``.
      - ``document_object``: Parametr ``document_object`` předává se do volání ``_create_element()``, ``_get_attribute_of_record()``.
      - ``child_parent_element_name``: Textový název nebo klíč ``child_parent_element_name`` používaný v rámci operace.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: get_ref_type_attribute_name()

      Vrací ref type attribute name.

      **Parametry:**

      - ``type_name``: Parametr ``type_name`` předává se do volání ``get()``, pracuje se s atributy ``replace``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``get()``.


   .. py:method:: _replace_redundant_namespaces()

      Provádí operaci replace redundant namespaces.

      **Parametry:**

      - ``xml_string``: Parametr ``xml_string`` se předává do volání ``sub()``, ``fromstring()``, pracuje se s atributy ``decode``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: generate_document()

      Vygeneruje document. v aplikaci.

      **Návratová hodnota:**

      Vrací proměnná ``xml_string``.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``document_object``: Parametr ``document_object`` slouží jako vstup pro logiku funkce ``__init__``.


