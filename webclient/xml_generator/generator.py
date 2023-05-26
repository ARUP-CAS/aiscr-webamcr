import xml.etree.ElementTree as ET

from lxml import etree
from projekt.models import Projekt


AMCR_NAMESPACE_URL = "https://api.aiscr.cz/schema/amcr/2.0/"
AMCR_XSD_URL = "https://api.aiscr.cz/schema/amcr/2.0/amcr.xsd"


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
        attribute_list = [text.replace("\"", "").replace("{", "").replace("}", "").strip().lower()
                          for text in attribute_list]
        attribute_list = [text[text.find(":") + 1:] if ":" in text else text for text in attribute_list]
        if len(attribute_list) == 2:
            return attribute_list
        elif len(attribute_list) == 1:
            return [None] + attribute_list
        else:
            return None, None

    @staticmethod
    def _get_attribute_of_record(record, attribute_name):
        if "." not in attribute_name and "(" not in attribute_name:
            attribute_value = getattr(record, attribute_name)
            return attribute_value
        else:
            record_name_split = attribute_name.split(".")
            if len(record_name_split) == 2:
                related_record = getattr(record, record_name_split[0], "")
                return getattr(related_record, record_name_split[1], "")
            if len(record_name_split) == 3:
                related_record = getattr(record, record_name_split[0], "")
                second_related_record = getattr(related_record, record_name_split[1], "")
                return getattr(second_related_record, record_name_split[2], "")
        print("Attribute not found", record, attribute_name)

    def _create_element(self, schema_element, parent_element, field_name, id_field_name=None):
        if self._get_attribute_of_record(self.document_object, field_name) is not None:
            new_sub_element = ET.SubElement(parent_element,
                                            f"{{{AMCR_NAMESPACE_URL}}}" + schema_element.attrib["name"])
            new_sub_element.text = str(self._get_attribute_of_record(self.document_object, field_name))
            if id_field_name is not None:
                new_sub_element.attrib["id"] = str(self._get_attribute_of_record(self.document_object, id_field_name))
        else:
            print(f"Unknown field: {field_name}")

    def _create_many_to_many_elements(self, schema_element, parent_element, related_records, field_name,
                                      id_field_name=None):
        for record in related_records:
            new_sub_element = ET.SubElement(parent_element,
                                            f"{{{AMCR_NAMESPACE_URL}}}" + schema_element.attrib["name"])
            new_sub_element.text = str(self._get_attribute_of_record(record, field_name))
            if id_field_name is not None:
                new_sub_element.attrib["id"] = str(self._get_attribute_of_record(record, id_field_name))

    def _parse_scheme_create_element(self, schema_element, parent_element):
        if schema_element.__class__.__name__ == "_Element":
            next_element = schema_element.getnext()
            if next_element.__class__.__name__ == "_Comment":
                id_field_name, field_name = self._parse_comment(next_element.text)
                if schema_element.attrib["maxOccurs"] == "1":
                    if field_name is not None:
                        self._create_element(schema_element, parent_element, field_name, id_field_name)
                elif schema_element.attrib["maxOccurs"] == "unbounded":
                    id_field_name, field_name = self._parse_comment(next_element.text)
                    split_name = field_name.split(".")
                    if id_field_name is not None:
                        id_field_name = id_field_name.split(".")
                        if len(id_field_name) == 2:
                            _, id_field_name = id_field_name
                    if len(split_name) >= 2:
                        if field_name is not None:
                            related_records = self._get_attribute_of_record(self.document_object,
                                                                            ".".join(split_name[:-1]))
                            print("Related records", field_name, related_records)
                            if related_records is not None:
                                self._create_many_to_many_elements(schema_element, parent_element,
                                                                   related_records.all(), split_name[-1],
                                                                   id_field_name)

    def generate_document(self):
        ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
        ET.register_namespace("amcr", AMCR_NAMESPACE_URL)
        ET.register_namespace("gml", "https://www.opengis.net/gml/3.2")
        ET.register_namespace("schemaLocation",
                              f"{AMCR_NAMESPACE_URL} {AMCR_XSD_URL} "
                              "https://www.opengis.net/gml/3.2 https://schemas.opengis.net/gml/3.2.1/gml.xsd")
        parent_element = ET.SubElement(self.document_root, f"{{{AMCR_NAMESPACE_URL}}}projekt")

        for schema_element in self._parse_schema():
            self._parse_scheme_create_element(schema_element, parent_element)
            children = list(schema_element)
            if len(children) == 1:
                inner_document_element = \
                    ET.SubElement(parent_element, f"{{{AMCR_NAMESPACE_URL}}}{schema_element.attrib['name']}")
                for child_schema_element in children[0][0]:
                    self._parse_scheme_create_element(child_schema_element, inner_document_element)
        with open('data.xml', 'w') as f:
            tree = ET.ElementTree(self.document_root)
            tree.write(f, encoding='unicode')

    def __init__(self, document_object):
        self.document_object = document_object
        self.document_root = ET.Element("xmlns")


objekt = Projekt.objects.get(ident_cely="C-201668331")
generator = DocumentGenerator(objekt)
generator.generate_document()
