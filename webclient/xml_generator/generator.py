import datetime
import os

import xml.etree.ElementTree as ET

from django.contrib.gis.db.models.functions import AsGML, AsWKT
from lxml import etree

from arch_z.models import ArcheologickyZaznam
from projekt.models import Projekt

AMCR_NAMESPACE_URL = "https://api.aiscr.cz/schema/amcr/2.0/"
AMCR_XSD_URL = "https://api.aiscr.cz/schema/amcr/2.0/amcr.xsd"
AMCR_XSD_FILENAME = "amcr_230531.xsd"
SCHEMA_LOCATION = "https://api.aiscr.cz/schema/amcr/2.0/ https://api.aiscr.cz/schema/amcr/2.0/amcr.xsd " \
                  "http://www.opengis.net/gml/3.2 http://schemas.opengis.net/gml/3.2.1/gml.xsd"

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

    @staticmethod
    def get_path_to_schema():
        return os.path.join("xml_generator/definitions/", AMCR_XSD_FILENAME)

    def _parse_schema(self, model_name):
        parser = etree.XMLParser()
        tree = etree.parse(self.get_path_to_schema(), parser)
        return tree.xpath(self._create_xpath_query(model_name))

    @staticmethod
    def _get_prefix(comment_text: str) -> str:
        if ":" not in comment_text:
            return ""
        comment_text_split = comment_text.split("|")
        comment_text = comment_text_split[0]
        attribute_prefix = comment_text[:comment_text.find(":") + 1]
        attribute_prefix = attribute_prefix.replace("\"", "").replace("{", "").replace("}", "").strip()
        return attribute_prefix

    @staticmethod
    def _parse_comment(comment_text: str) -> list:
        attribute_list = comment_text.split("|")
        attribute_list = [text.replace("\"", "").replace("{", "").replace("}", "").strip().lower()
                          for text in attribute_list]
        attribute_list = [text[text.find(":") + 1:] if ":" in text else text for text in attribute_list]
        if len(attribute_list) == 2:
            return attribute_list
        elif len(attribute_list) == 1:
            return [None] + attribute_list
        else:
            return [None, None]

    def _get_attribute_of_record(self, attribute_name, record=None):
        attribute_value = None
        if record is None:
            record = self.document_object
        if attribute_name == "self":
            return self.document_object
        if "." not in attribute_name and "(" not in attribute_name:
            attribute_value = getattr(record, attribute_name, None)
        elif "st_asgml" in attribute_name.lower() or "st_srid" in attribute_name.lower():
            if "st_asgml" in attribute_name.lower():
                field_name = attribute_name.lower().replace("st_asgml", "").replace("(", "").replace(")", "")
                attribute_value = getattr(record, f"{field_name}_st_asgml")
            elif "st_srid" in attribute_name.lower():
                field_name = attribute_name.lower().replace("st_srid", "").replace("(", "").replace(")", "")
                attribute_value = getattr(record, f"{field_name}_st_wkt")
            else:
                return None
            parser = ET.XMLParser()
            attribute_value = attribute_value.replace(">", ' xmlns:gml="http://www.opengis.net/gml/3.2">', 1)
            # attribute_value = ET.fromstring(attribute_value, parser)
        else:
            record_name_split = attribute_name.split(".")
            if len(record_name_split) == 2:
                related_record = getattr(record, record_name_split[0], None)
                attribute_value = getattr(related_record, record_name_split[1], None)
            elif len(record_name_split) == 3:
                related_record = getattr(record, record_name_split[0], None)
                second_related_record = getattr(related_record, record_name_split[1], None)
                attribute_value = getattr(second_related_record, record_name_split[2], None)
        return attribute_value

    @staticmethod
    def _get_attribute_of_record_unbounded(record, attribute_name, schema_element) -> list:
        attributes = []
        record_name_split = attribute_name.split(".")
        if len(record_name_split) == 1:
            record_attribute = getattr(record, record_name_split[0], None)
            if hasattr(record_attribute, "all"):
                attributes = [x for x in record_attribute.all()]
        elif len(record_name_split) == 2:
            related_record = getattr(record, record_name_split[0], None)
            if hasattr(related_record, "all"):
                attributes = [getattr(x, record_name_split[1], None) for x in related_record.all()]
            else:
                related_record = getattr(record, record_name_split[0], None)
                related_record = getattr(related_record, record_name_split[1], None)
                if hasattr(related_record, "all"):
                    attributes = [x for x in related_record.all()]
        elif len(record_name_split) == 3:
            related_record = getattr(record, record_name_split[0], None)
            if hasattr(related_record, "all"):
                for record in related_record.all():
                    first_related = getattr(record, record_name_split[1], None)
                    if first_related is not None:
                        second_related = getattr(first_related, record_name_split[2], None)
                        attributes.append(second_related)
            else:
                related_record = getattr(related_record, record_name_split[1], None)
                if hasattr(related_record, "all"):
                    attributes = [x for x in related_record.all()]
        if schema_element.attrib["type"] == "xs:date":
            attributes = [x.date() for x in attributes]
        return attributes

    def _create_element(self, schema_element, parent_element, field_name, id_field_name=None, document_object=None,
                        id_field_prefix=""):
        if document_object is None:
            document_object = self.document_object
        attribute_value = self._get_attribute_of_record(field_name, document_object)
        if attribute_value is not None and len(str(attribute_value)) > 0:
            new_sub_element = ET.SubElement(parent_element,
                                            f"{{{AMCR_NAMESPACE_URL}}}{schema_element.attrib['name']}")
            print("_create_element", attribute_value, attribute_value.__class__.__name__)
            if attribute_value.__class__.__name__ == "Element":
                new_sub_element.append(attribute_value)
            elif isinstance(attribute_value, datetime.datetime):
                new_sub_element.text = attribute_value.isoformat()
            else:
                if isinstance(attribute_value, bool):
                    new_sub_element.text = str(attribute_value).lower()
                else:
                    new_sub_element.text = str(attribute_value)
            if id_field_name is not None:
                new_sub_element.attrib["id"] = \
                    f"{id_field_prefix}{self._get_attribute_of_record(id_field_name, document_object)}"
        else:
            print("Unknown field", field_name, attribute_value, document_object)

    @staticmethod
    def _create_many_to_many_ref_elements(schema_element, parent_element, related_records, id_field_name=None,
                                          prefix=""):
        for record in related_records:
            new_sub_element = ET.SubElement(parent_element,
                                            f"{{{AMCR_NAMESPACE_URL}}}" + schema_element.attrib["name"])
            if record.__class__.__name__ == "_Element":
                new_sub_element.append(record)
            else:
                if isinstance(record, bool):
                    new_sub_element.text = str(record).lower()
                else:
                    new_sub_element.text = str(record)
            if id_field_name is not None:
                new_sub_element.attrib[f"{prefix}id"] = str(record)

    def _parse_scheme_create_element(self, schema_element, parent_element):
        if schema_element.__class__.__name__ == "_Element":
            next_element = schema_element.getnext()
            # The comment should be the very next element
            if next_element.__class__.__name__ == "_Comment":
                id_field_name, field_name = self._parse_comment(next_element.text)
                prefix = self._get_prefix(next_element.text)
                if schema_element.attrib["maxOccurs"] == "1":
                    if field_name is not None:
                        if schema_element.attrib["type"] in ("xs:string", "xs:date", "xs:integer", "amcr:refType",
                                                             "xs:dateTime"):
                            self._create_element(schema_element, parent_element, field_name, id_field_name,
                                                 id_field_prefix=prefix)
                        else:
                            obj = self._get_attribute_of_record(field_name)
                            if obj is not None:
                                child_schema_element = self._parse_schema(schema_element.attrib["type"])
                                self._parse_scheme_create_nested_element(child_schema_element, parent_element, obj,
                                                                         schema_element.attrib["name"])
                elif schema_element.attrib["maxOccurs"] == "unbounded":
                    if field_name is not None:
                        related_records = self._get_attribute_of_record_unbounded(self.document_object, field_name,
                                                                                  schema_element)
                        if related_records is not None:
                            if schema_element.attrib["type"] != "amcr:refType":
                                self._iterate_unbound_records(related_records, schema_element, parent_element)
                            else:
                                self._create_many_to_many_ref_elements(schema_element, parent_element, related_records,
                                                                       id_field_name if id_field_name else None,
                                                                       prefix)
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
        child_parent_element = ET.SubElement(parent_element, f"{{{AMCR_NAMESPACE_URL}}}{child_parent_element_name}")
        for child_schema_element in schema_element:
            if child_schema_element.__class__.__name__ == "_Element":
                next_element = child_schema_element.getnext()
                if next_element.__class__.__name__ == "_Comment":
                    id_field_name, field_name = self._parse_comment(next_element.text)
                    prefix = self._get_prefix(next_element.text)
                    if child_schema_element.attrib["maxOccurs"] == "1":
                        if field_name is not None:
                            self._create_element(child_schema_element, child_parent_element, field_name, id_field_name,
                                                 document_object, prefix)
                    else:
                        related_records = self._get_attribute_of_record_unbounded(document_object, field_name,
                                                                                  child_schema_element)
                        if related_records is not None and len(related_records) > 0:
                            self._iterate_unbound_records(related_records, child_schema_element, child_parent_element)

    def generate_document(self):
        ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
        ET.register_namespace("gml", "https://www.opengis.net/gml/3.2")
        ET.register_namespace("amcr", AMCR_NAMESPACE_URL)
        self.document_root.attrib[f"{{http://www.w3.org/2001/XMLSchema-instance}}schemaLocation"] = SCHEMA_LOCATION
        parent_element = ET.SubElement(self.document_root, f"{{{AMCR_NAMESPACE_URL}}}{self._get_schema_name()}")
        for schema_element in self._parse_schema(self._get_schema_name()):
            self._parse_scheme_create_element(schema_element, parent_element)
            children = list(schema_element)
            if len(children) == 1:
                inner_document_element = \
                    ET.SubElement(parent_element, f"{{{AMCR_NAMESPACE_URL}}}{schema_element.attrib['name']}")
                for child_schema_element in children[0][0]:
                    self._parse_scheme_create_element(child_schema_element, inner_document_element)
        return ET.tostring(self.document_root, encoding='utf8', method='xml')

    def __init__(self, document_object):
        self.document_object = document_object
        self.document_root = ET.Element(f"{{{AMCR_NAMESPACE_URL}}}amcr")
