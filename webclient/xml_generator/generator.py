import xml.etree.ElementTree as ET
from dataclasses import dataclass

from lxml import etree
from projekt.models import Projekt


class DocumentGenerator:
    def _get_name(self):
        type_class_dict = {
            Projekt: "projekt"
        }
        object_class = self.document_object.__class__
        name = type_class_dict.get(object_class)
        return name

    def _create_xpath_query(self):
        model_name = self._get_name()
        query_attribute_selection = f"[local-name()='complexType' and @name='{model_name}Type']"
        query = f"//*{query_attribute_selection}/*/*|//*{query_attribute_selection}/*/comment()"
        return query

    def _parse_schema(self):
        parser = etree.XMLParser()
        tree = etree.parse("xml_generator/definitions/amcr_230522.xsd.xml", parser)
        return tree.xpath(self._create_xpath_query())

    @staticmethod
    def _parse_comment(comment_text):
        attribute_list = comment_text.split("|")
        attribute_list = [text.replace("\"", "").replace("{", "").replace("}", "").replace(".", "__").strip()
                          for text in attribute_list]
        if len(attribute_list) == 2:
            return attribute_list
        elif len(attribute_list) == 1:
            return [None] + attribute_list
        else:
            return None, None

    def _create_element(self, schema_element, parent_element, field_name, id_field_name=None):
        if hasattr(self.document_object, field_name) and getattr(self.document_object, field_name) is not None:
            new_sub_element = ET.SubElement(parent_element,
                                           r"{https://api.aiscr.cz/schema/amcr/2.0/}" + schema_element.attrib["name"])
            new_sub_element.text = str(getattr(self.document_object, field_name))
            if id_field_name is not None and hasattr(self.document_object, field_name):
                new_sub_element.attrib["id"] = str(getattr(self.document_object, id_field_name))

    def _parse_scheme_create_element(self, schema_element, parent_element):
        if schema_element.__class__.__name__ == "_Element":
            next_element = schema_element.getnext()
            if next_element.__class__.__name__ == "_Comment":
                id_field_name, field_name = self._parse_comment(next_element.text)
                if field_name is not None and hasattr(self.document_object, field_name):
                    self._create_element(schema_element, parent_element, field_name, id_field_name)

    def generate_document(self):
        ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
        ET.register_namespace("amcr", "https://api.aiscr.cz/schema/amcr/2.0/")
        ET.register_namespace("gml", "https://www.opengis.net/gml/3.2")
        ET.register_namespace("schemaLocation",
                              "https://api.aiscr.cz/schema/amcr/2.0/ "
                              "https://api.aiscr.cz/schema/amcr/2.0/amcr.xsd "
                              "https://www.opengis.net/gml/3.2 https://schemas.opengis.net/gml/3.2.1/gml.xsd")
        parent_element = ET.SubElement(self.document_root, r"{https://api.aiscr.cz/schema/amcr/2.0/}projekt")

        for schema_element in self._parse_schema():
            self._parse_scheme_create_element(schema_element, parent_element)
            children = list(schema_element)
            if len(children) == 1:
                inner_document_element = \
                    ET.SubElement(parent_element, "{https://api.aiscr.cz/schema/amcr/2.0/}"
                                  + schema_element.attrib["name"])
                for child_schema_element in children[0][0]:
                    self._parse_scheme_create_element(child_schema_element, inner_document_element)
        with open('data.xml', 'w') as f:
            tree = ET.ElementTree(self.document_root)
            print(ET.dump(self.document_root))
            tree.write(f, encoding='unicode')

    def __init__(self, document_object):
        self.document_object = document_object
        self.document_root = ET.Element("xmlns")


objekt = Projekt.objects.first()
generator = DocumentGenerator(objekt)
generator.generate_document()
