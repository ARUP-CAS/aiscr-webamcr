import os

import xml.etree.ElementTree as ET

from lxml import etree

from arch_z.models import ArcheologickyZaznam
from projekt.models import Projekt

AMCR_NAMESPACE_URL = "https://api.aiscr.cz/schema/amcr/2.0/"
AMCR_XSD_URL = "https://api.aiscr.cz/schema/amcr/2.0/amcr.xsd"
AMCR_XSD_FILENAME = "amcr_230531.xsd"


class DocumentGenerator:
    def _get_schema_name(self):
        type_class_dict = {
            Projekt: "projekt",
            ArcheologickyZaznam: "archeologicky_zaznam"
        }
        object_class = self.document_object.__class__
        name = type_class_dict.get(object_class)
        return name

    @staticmethod
    def _create_xpath_query(model_name):
        if model_name.lower().endswith("type"):
            model_name = model_name.replace("amcr:", "")
            query_attribute_selection = f"[local-name()='complexType' and @name='{model_name}']"
        else:
            query_attribute_selection = f"[local-name()='complexType' and @name='{model_name}Type']"
        query = f"//*{query_attribute_selection}/*/*|//*{query_attribute_selection}/*/comment()"
        return query

    def _parse_schema(self, model_name):
        parser = etree.XMLParser()
        tree = etree.parse(os.path.join("xml_generator/definitions/", AMCR_XSD_FILENAME), parser)
        return tree.xpath(self._create_xpath_query(model_name))

    @staticmethod
    def _parse_comment(comment_text: str):
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

    def _get_attribute_of_record(self, record, attribute_name):
        if attribute_name == "self":
            return self.document_object
        if "." not in attribute_name and "(" not in attribute_name:
            attribute_value = getattr(record, attribute_name, None)
            return attribute_value
        else:
            record_name_split = attribute_name.split(".")
            if len(record_name_split) == 2:
                related_record = getattr(record, record_name_split[0], None)
                return getattr(related_record, record_name_split[1], None)
            if len(record_name_split) == 3:
                related_record = getattr(record, record_name_split[0], None)
                second_related_record = getattr(related_record, record_name_split[1], None)
                return getattr(second_related_record, record_name_split[2], None)
        print("Attribute not found", record, attribute_name)

    @staticmethod
    def _get_attribute_of_record_unbounded(record, attribute_name):
        record_name_split = attribute_name.split(".")
        if len(record_name_split) == 1:
            record_attribute = getattr(record, record_name_split[0], None)
            if hasattr(record_attribute, "all"):
                return [x for x in record_attribute.all()]
            else:
                print("_get_attribute_of_record_unbounded", record_name_split)
        elif len(record_name_split) == 2:
            related_record = getattr(record, record_name_split[0], None)
            if hasattr(related_record, "all"):
                attributes = [getattr(x, record_name_split[1], None) for x in related_record.all()]
                return attributes
            related_record = getattr(record, record_name_split[0], None)
            related_record = getattr(related_record, record_name_split[1], None)
            if hasattr(related_record, "all"):
                return [x for x in related_record.all()]
        elif len(record_name_split) == 3:
            related_record = getattr(record, record_name_split[0], None)
            if hasattr(related_record, "all"):
                attributes = []
                for record in related_record.all():
                    first_related = getattr(record, record_name_split[1], None)
                    if first_related is not None:
                        second_related = getattr(first_related, record_name_split[2], None)
                        attributes.append(second_related)
                return attributes
            related_record = getattr(record, record_name_split[0], None)
            related_record = getattr(related_record, record_name_split[1], None)
            if hasattr(related_record, "all"):
                return [x for x in related_record.all()]
        print("Attribute not found", record, attribute_name)

    def _create_element(self, schema_element, parent_element, field_name, id_field_name=None, document_object=None):
        if document_object is None:
            document_object = self.document_object
        attribute_value = self._get_attribute_of_record(document_object, field_name)
        if attribute_value is not None and len(str(attribute_value)) > 0:
            new_sub_element = ET.SubElement(parent_element,
                                            f"{{{AMCR_NAMESPACE_URL}}}{schema_element.attrib['name']}")
            new_sub_element.text = str(attribute_value)
            if id_field_name is not None:
                new_sub_element.attrib["id"] = str(self._get_attribute_of_record(document_object, id_field_name))
        else:
            print(f"Unknown field: {field_name}")

    def _create_many_to_many_ref_elements(self, schema_element, parent_element, related_records, id_field_name=None):
        for record in related_records:
            new_sub_element = ET.SubElement(parent_element,
                                            f"{{{AMCR_NAMESPACE_URL}}}" + schema_element.attrib["name"])
            new_sub_element.text = str(record)
            if id_field_name is not None:
                new_sub_element.attrib["id"] = str(record)

    def _parse_scheme_create_element(self, schema_element, parent_element):
        if schema_element.__class__.__name__ == "_Element":
            next_element = schema_element.getnext()
            # The comment should be the very next element
            if next_element.__class__.__name__ == "_Comment":
                id_field_name, field_name = self._parse_comment(next_element.text)
                if schema_element.attrib["maxOccurs"] == "1":
                    if field_name is not None:
                        if schema_element.attrib["type"] in ("xs:string", "xs:date", "xs:integer", "amcr:refType"):
                            self._create_element(schema_element, parent_element, field_name, id_field_name)
                        else:
                            obj = self._get_attribute_of_record(self.document_object, field_name)
                            if obj is not None:
                                child_schema_element = self._parse_schema(schema_element.attrib["type"])
                                self._parse_scheme_create_nested_element(child_schema_element, parent_element, obj,
                                                                         schema_element.attrib["name"])
                elif schema_element.attrib["maxOccurs"] == "unbounded":
                    id_field_names, field_names = self._parse_comment(next_element.text)
                    if field_name is not None:
                        related_records = self._get_attribute_of_record_unbounded(self.document_object, field_names)
                        if related_records is not None:
                            if schema_element.attrib["type"] != "amcr:refType":
                                self._iterate_unbound_records(related_records, schema_element, parent_element)
                                # child_schema_element = self._parse_schema(schema_element.attrib["type"])
                                # for obj in related_records:
                                #     self._parse_scheme_create_nested_element(child_schema_element, parent_element, obj,
                                #                                              schema_element.attrib["name"])
                            else:
                                self._create_many_to_many_ref_elements(schema_element, parent_element, related_records,
                                                                       id_field_names if id_field_names else None)
                    else:
                        print("Unknown field", "next_element.text")
            else:
                print("Element without comment", schema_element.attrib["name"])

    def _iterate_unbound_records(self, related_records, schema_element, parent_element):
        child_schema_element = self._parse_schema(schema_element.attrib["type"])
        for obj in related_records:
            self._parse_scheme_create_nested_element(child_schema_element, parent_element, obj,
                                                     schema_element.attrib["name"])

    def _parse_scheme_create_nested_element(self, schema_element, parent_element, document_object,
                                            child_parent_element_name):
        print("_parse_scheme_create_nested_element", document_object)
        child_parent_element = ET.SubElement(parent_element, f"{{{AMCR_NAMESPACE_URL}}}{child_parent_element_name}")
        for child_schema_element in schema_element:
            if child_schema_element.__class__.__name__ == "_Element":
                next_element = child_schema_element.getnext()
                if next_element.__class__.__name__ == "_Comment":
                    id_field_name, field_name = self._parse_comment(next_element.text)
                    if child_schema_element.attrib["maxOccurs"] == "1":
                        if field_name is not None:
                            self._create_element(child_schema_element, child_parent_element, field_name, id_field_name,
                                                 document_object)
                    else:
                        related_records = self._get_attribute_of_record_unbounded(document_object, field_name)
                        if related_records is not None:
                            self._iterate_unbound_records(related_records, child_schema_element, child_parent_element)
                        else:
                            print("_parse_scheme_create_nested_element_unbounded", field_name)

    def generate_document(self):
        ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
        ET.register_namespace("amcr", AMCR_NAMESPACE_URL)
        ET.register_namespace("gml", "https://www.opengis.net/gml/3.2")
        ET.register_namespace("schemaLocation",
                              f"{AMCR_NAMESPACE_URL} {AMCR_XSD_URL} "
                              "https://www.opengis.net/gml/3.2 https://schemas.opengis.net/gml/3.2.1/gml.xsd")
        parent_element = ET.SubElement(self.document_root, f"{{{AMCR_NAMESPACE_URL}}}{self._get_schema_name()}")
        for schema_element in self._parse_schema(self._get_schema_name()):
            self._parse_scheme_create_element(schema_element, parent_element)
            children = list(schema_element)
            if len(children) == 1:
                inner_document_element = \
                    ET.SubElement(parent_element, f"{{{AMCR_NAMESPACE_URL}}}{schema_element.attrib['name']}")
                for child_schema_element in children[0][0]:
                    self._parse_scheme_create_element(child_schema_element, inner_document_element)
        with open('data.xml', 'w') as f:
            tree = ET.ElementTree(self.document_root)
            ET.indent(tree, space="\t", level=0)
            tree.write(f, encoding='unicode')

    def __init__(self, document_object):
        self.document_object = document_object
        self.document_root = ET.Element("xmlns")


objekt = ArcheologickyZaznam.objects.get(ident_cely="C-201901234A")
# objekt = Projekt.objects.get(ident_cely="C-201705778")
generator = DocumentGenerator(objekt)
generator.generate_document()
