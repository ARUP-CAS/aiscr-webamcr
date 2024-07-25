import datetime
import logging
import os
import re
from dataclasses import dataclass
# import xml.etree.ElementTree as ET
from typing import Union, Optional

from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import AsGML, GeoFunc
from lxml import etree
from lxml import etree as ET

from adb.models import VyskovyBod
from heslar.models import RuianKraj, RuianOkres
from xml_generator.models import ModelWithMetadata

AMCR_NAMESPACE_URL = "https://api.aiscr.cz/schema/amcr/2.0/"
AMCR_XSD_URL = "https://api.aiscr.cz/schema/amcr/2.0/amcr.xsd"
AMCR_XSD_FILENAME = "amcr.xsd"
SCHEMA_LOCATION = "https://api.aiscr.cz/schema/amcr/2.0/ https://api.aiscr.cz/schema/amcr/2.0/amcr.xsd"
logger = logging.getLogger(__name__)


class AsText(GeoFunc):
    output_field = models.TextField()


@dataclass
class ParsedComment:
    value_field_name: str
    attribute_field_names: list = None


class DocumentGenerator:
    _nsmap = {
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "gml": "http://www.opengis.net/gml/3.2",
        "amcr": AMCR_NAMESPACE_URL,
        "xml": "http://www.w3.org/XML/1998/namespace"
    }
    attribute_names = {}
    _simple_element_types = ("xs:string", "xs:date", "xs:integer", "amcr:refType", "xs:dateTime", "amcr:gmlType",
                             "amcr:wktType", "amcr:autorType", "xs:boolean", "amcr:langstringType", "amcr:vocabType",
                             "xs:decimal")

    @classmethod
    def generate_metadata(cls, model_class=None, limit=None, start_with_pk=None):
        logger.debug("xml_generator.generator.generate_metadata.start", extra={"model_class": model_class,
                                                                               "limit": limit})
        if not model_class:
            for current_class in cls._get_schema_dict():
                logger.debug("xml_generator.generator.generate_metadata.loop.strart",
                             extra={"limit": limit, "current_class": str(current_class)})
                if not start_with_pk:
                    queryset = current_class.objects.all().order_by("pk")
                else:
                    queryset = current_class.objects.filter(pk__gte=start_with_pk).order_by("pk")
                if limit is not None:
                    queryset = queryset[:limit]
                for obj in queryset:
                    from uzivatel.models import User
                    from core.repository_connector import FedoraTransaction
                    obj: Union[ModelWithMetadata, User]
                    fedora_transaction = FedoraTransaction()
                    obj.save_metadata(fedora_transaction, close_transaction=True)
                logger.debug("xml_generator.generator.generate_metadata.loop.end",
                             extra={"limit": limit, "current_class": str(current_class)})
        else:
            logger.debug("xml_generator.generator.generate_metadata.loop.strart",
                         extra={"model_class": model_class, "limit": limit})
            from adb.models import Adb
            from arch_z.models import ArcheologickyZaznam
            from dokument.models import Dokument
            from projekt.models import Projekt
            from pas.models import SamostatnyNalez
            from ez.models import ExterniZdroj
            from dokument.models import Let
            from uzivatel.models import User, Organizace, Osoba
            from heslar.models import Heslar, RuianKraj, RuianKatastr, RuianOkres
            from pian.models import Pian
            model_class = {
                "Projekt": Projekt,
                "ArcheologickyZaznam": ArcheologickyZaznam,
                "Let": Let,
                "Adb": Adb,
                "Dokument": Dokument,
                "ExterniZdroj": ExterniZdroj,
                "Pian": Pian,
                "SamostatnyNalez": SamostatnyNalez,
                "User": User,
                "Heslar": Heslar,
                "RuianKraj": RuianKraj,
                "RuianOkres": RuianOkres,
                "RuianKatastr": RuianKatastr,
                "Organizace": Organizace,
                "Osoba": Osoba,
            }.get(model_class)
            if not start_with_pk:
                queryset = model_class.objects.order_by("pk").all()
            else:
                queryset = model_class.objects.filter(pk__gte=start_with_pk).order_by("pk")
            if limit is not None:
                queryset = queryset[:limit]
            for obj in queryset:
                from uzivatel.models import User
                from core.repository_connector import FedoraTransaction
                obj: Union[ModelWithMetadata, User]
                fedora_transaction = FedoraTransaction()
                obj.active_transaction = fedora_transaction
                obj.save_metadata(fedora_transaction, close_transaction=True)
            logger.debug("xml_generator.generator.generate_metadata.loop.end",
                         extra={"model_class": model_class, "limit": limit})
        logger.debug("xml_generator.generator.generate_metadata.end", extra={"model_class": model_class,
                                                                             "limit": limit})

    @classmethod
    def _get_schema_dict(cls):
        from adb.models import Adb
        from arch_z.models import ArcheologickyZaznam
        from dokument.models import Dokument
        from projekt.models import Projekt
        from pas.models import SamostatnyNalez
        from ez.models import ExterniZdroj
        from dokument.models import Let
        from uzivatel.models import User, Organizace, Osoba
        from heslar.models import Heslar, RuianKraj, RuianKatastr, RuianOkres
        from pian.models import Pian

        return {
            Projekt: "projekt",
            ArcheologickyZaznam: "archeologicky_zaznam",
            Let: "let",
            Adb: "adb",
            Dokument: "dokument",
            ExterniZdroj: "ext_zdroj",
            Pian: "pian",
            SamostatnyNalez: "samostatny_nalez",
            User: "uzivatel",
            Heslar: "heslo",
            RuianKraj: "ruian_kraj",
            RuianOkres: "ruian_okres",
            RuianKatastr: "ruian_katastr",
            Organizace: "organizace",
            Osoba: "osoba",
        }

    def _get_schema_name(self):
        type_class_dict = self._get_schema_dict()
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
        if "-" not in comment_text:
            return ""
        if "|" in comment_text:
            comment_text_split = comment_text.split("|")
            comment_text = comment_text_split[0]
        attribute_prefix = comment_text[:comment_text.find("-") + 1]
        attribute_prefix = attribute_prefix.replace("\"", "").replace("{", "").replace("}", "").strip()
        return attribute_prefix

    @staticmethod
    def _parse_comment(comment_text: str) -> Optional[ParsedComment]:
        attribute_list = comment_text.split("|")
        attribute_list = [text.replace("\"", "").replace("{", "").replace("}", "").strip().lower()
                          for text in attribute_list]
        attribute_list = [text[text.find("-") + 1:] if "-" in text else text for text in attribute_list]
        if len(attribute_list) == 2:
            return ParsedComment(attribute_list[1], [attribute_list[0]])
        elif len(attribute_list) == 1:
            return ParsedComment(attribute_list[0])
        elif len(attribute_list) == 3:
            return ParsedComment(attribute_list[-1], attribute_list[:-1])

    def _get_attribute_of_record(self, attribute_name, record=None):
        attribute_value = None
        if record is None:
            record = self.document_object
        if attribute_name.lower() == "self":
            return record
        if "." not in attribute_name and "(" not in attribute_name:
            attribute_value = getattr(record, attribute_name, None)
        elif "st_asgml" in attribute_name.lower() or "st_astext" in attribute_name.lower() \
                or "st_srid" in attribute_name.lower():
            from dokument.models import DokumentExtraData
            from pas.models import SamostatnyNalez
            from projekt.models import Projekt
            from heslar.models import RuianKatastr
            from pian.models import Pian
            if isinstance(record, Projekt) or isinstance(record, DokumentExtraData) \
                    or isinstance(record, VyskovyBod):
                record = record.__class__.objects.annotate(geom_st_asgml=AsGML("geom", nprefix="gml"),
                                                           geom_st_astext=AsText("geom")) \
                    .get(pk=record.pk)
            elif isinstance(record, SamostatnyNalez) or isinstance(record, Pian):
                record = record.__class__.objects.annotate(geom_st_asgml=AsGML("geom", nprefix="gml"),
                                                           geom_st_astext=AsText("geom"),
                                                           geom_sjtsk_st_asgml=AsGML("geom_sjtsk", nprefix="gml"),
                                                           geom_sjtsk_st_astext=AsText("geom_sjtsk")) \
                    .get(pk=record.pk)
            elif isinstance(record, RuianKatastr) or isinstance(record, RuianKraj) or isinstance(record, RuianOkres):
                record = record.__class__.objects.annotate(definicni_bod_st_asgml=AsGML("definicni_bod", nprefix="gml"),
                                                           definicni_bod_st_astext=AsText("definicni_bod"),
                                                           hranice_st_asgml=AsGML("hranice", nprefix="gml"),
                                                           hranice_st_astext=AsText("hranice")) \
                    .get(pk=record.pk)
            if "st_asgml" in attribute_name.lower():
                field_name = attribute_name.lower().replace("st_asgml", "").replace("(", "").replace(")", "")
                attribute_value = getattr(record, f"{field_name}_st_asgml")
            elif "st_astext" in attribute_name.lower():
                field_name = attribute_name.lower().replace("st_astext", "").replace("(", "").replace(")", "")
                attribute_value = getattr(record, f"{field_name}_st_astext")
            elif "st_srid" in attribute_name.lower():
                field_name = attribute_name.lower().replace("st_srid", "").replace("(", "").replace(")", "")
                attribute_value = getattr(record, f"{field_name}").srid
            if attribute_value is not None and "st_asgml" in attribute_name.lower():
                # ET.register_namespace("gml", "http://www.opengis.net/gml/3.2")
                attribute_value = attribute_value.replace(">", ' xmlns:gml="http://www.opengis.net/gml/3.2">', 1)
                attribute_value = ET.fromstring(attribute_value)
        else:
            record_name_split = attribute_name.split(".")
            if len(record_name_split) == 2:
                related_record = getattr(record, record_name_split[0], None)
                attribute_value = getattr(related_record, record_name_split[1], None)
            elif len(record_name_split) == 3:
                related_record = getattr(record, record_name_split[0], None)
                second_related_record = getattr(related_record, record_name_split[1], None)
                attribute_value = getattr(second_related_record, record_name_split[2], None)
            elif len(record_name_split) == 4:
                related_record_1 = getattr(record, record_name_split[0], None)
                related_record_2 = getattr(related_record_1, record_name_split[1], None)
                related_record_3 = getattr(related_record_2, record_name_split[2], None)
                attribute_value = getattr(related_record_3, record_name_split[3], None)
        return attribute_value

    @staticmethod
    def _get_attribute_of_record_unbounded(record, parsed_comment: ParsedComment, schema_element) -> dict:
        attributes_dict = {}
        def get_attribute(record, attribute_name):
            attributes = []
            record_name_split = attribute_name.split(".")
            if len(record_name_split) == 1:
                record_attribute = getattr(record, record_name_split[0])
                if hasattr(record_attribute, "all"):
                    attributes = [x for x in record_attribute.all()]
                else:
                    attributes = [record_attribute]
            elif len(record_name_split) == 2:
                related_record = getattr(record, record_name_split[0])
                if hasattr(related_record, "all"):
                    for item in related_record.all():
                        attributes.append(getattr(item, record_name_split[1], None))
                else:
                    related_record = getattr(record, record_name_split[0], None)
                    related_record = getattr(related_record, record_name_split[1], None)
                    if hasattr(related_record, "all"):
                        attributes = []
                        try:
                            for x in related_record.all():
                                attributes.append(x)
                        except Exception as err:
                            logger.info(
                                "xml_generator.generator._get_attribute_of_record_unbounded.attr.append.error",
                                extra={"err": err}
                            )
            elif len(record_name_split) == 3:
                related_record = getattr(record, record_name_split[0])
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

        attributes_dict["value"] = get_attribute(record, parsed_comment.value_field_name)
        if parsed_comment.attribute_field_names:
            for key in parsed_comment.attribute_field_names:
                attributes_dict[key] = get_attribute(record, key)
        return attributes_dict

    def _create_element(self, schema_element, parent_element, parsed_comment: ParsedComment, document_object=None,
                        id_field_prefix="", ref_type=None):
        if document_object is None:
            document_object = self.document_object
        attribute_value = self._get_attribute_of_record(parsed_comment.value_field_name, document_object)
        if parsed_comment.attribute_field_names is None and id_field_prefix:
            attribute_value = id_field_prefix + str(attribute_value)
        if attribute_value is not None and len(str(attribute_value)) > 0:
            new_sub_element = ET.SubElement(parent_element,
                                            f"{{{AMCR_NAMESPACE_URL}}}{schema_element.attrib['name']}",
                                            nsmap=self._nsmap)
            if attribute_value.__class__.__name__ == "_Element":
                new_sub_element.append(attribute_value)
            elif isinstance(attribute_value, datetime.datetime):
                new_sub_element.text = attribute_value.isoformat()
            else:
                if isinstance(attribute_value, bool):
                    new_sub_element.text = str(attribute_value).lower()
                else:
                    new_sub_element.text = str(attribute_value)
            if "vocabType" in ref_type:
                new_sub_element.attrib[f"{{{self._nsmap['xml']}}}lang"] = "cs"
            if "langstringType" in ref_type:
                new_sub_element.attrib[f"{{{self._nsmap['xml']}}}lang"] = \
                    "en" if parsed_comment.value_field_name.endswith("_en") else "cs"
            if parsed_comment.attribute_field_names is not None:
                for attribute_field_name in parsed_comment.attribute_field_names:
                    attribute_name = self.get_ref_type_attribute_name(ref_type)
                    new_sub_element.attrib[attribute_name] = \
                        f"{id_field_prefix}{self._get_attribute_of_record(attribute_field_name, document_object)}"

    def _create_many_to_many_ref_elements(self, schema_element, parent_element, related_records,
                                          parsed_comment: ParsedComment, prefix="", ref_type=None):
        for i, record in enumerate(related_records["value"]):
            new_sub_element = ET.SubElement(parent_element,
                                            f"{{{AMCR_NAMESPACE_URL}}}" + schema_element.attrib["name"],
                                            nsmap=self._nsmap)
            if record.__class__.__name__ == "_Element":
                new_sub_element.append(record)
            else:
                record_text = str(record)
                if parsed_comment.attribute_field_names is None and prefix:
                    record = prefix + record_text
                if isinstance(record, bool):
                    new_sub_element.text = record_text.lower()
                else:
                    new_sub_element.text = record_text
            if "vocabType" in ref_type:
                new_sub_element.attrib[f"{{{self._nsmap['xml']}}}lang"] = "cs"
                if getattr(record, "ident_cely", None) is not None:
                    new_sub_element.attrib["id"] = record.ident_cely
            if "langstringType" in ref_type:
                if parsed_comment.attribute_field_names is not None:
                    new_sub_element.attrib[f"{{{self._nsmap['xml']}}}lang"] = \
                        "en" if parsed_comment.attribute_field_names[0].endswith("_en") else "cs"
                else:
                    new_sub_element.attrib[f"{{{self._nsmap['xml']}}}lang"] = "cs"
            if parsed_comment.attribute_field_names is not None:
                new_sub_element.attrib["id"] = \
                    f"{prefix}{related_records[parsed_comment.attribute_field_names[0]][i]}"
                if len(parsed_comment.attribute_field_names) == 2:
                    attribute_name = self.get_ref_type_attribute_name(ref_type)
                    new_sub_element.attrib[attribute_name] = \
                        f"{prefix}{related_records[parsed_comment.attribute_field_names[1]][i]}"

    def _parse_scheme_create_element(self, schema_element, parent_element):
        if schema_element.__class__.__name__ == "_Element":
            next_element = schema_element.getnext()
            # The comment should be the very next element
            if next_element.__class__.__name__ == "_Comment":
                parsed_comment: ParsedComment = self._parse_comment(next_element.text)
                prefix = self._get_prefix(next_element.text)
                if "maxOccurs" not in schema_element.attrib or schema_element.attrib["maxOccurs"] == "1":
                    if parsed_comment.value_field_name is not None:
                        if schema_element.attrib["type"] in self._simple_element_types:
                            self._create_element(schema_element, parent_element, parsed_comment,
                                                 id_field_prefix=prefix, ref_type=schema_element.attrib["type"])
                        else:
                            obj = self._get_attribute_of_record(parsed_comment.value_field_name)
                            if obj is not None:
                                child_schema_element = self._parse_schema(schema_element.attrib["type"])
                                self._parse_scheme_create_nested_element(child_schema_element, parent_element, obj,
                                                                         schema_element.attrib["name"])
                elif schema_element.attrib["maxOccurs"] == "unbounded":
                    if parsed_comment.value_field_name is not None:
                        related_records_dict = self._get_attribute_of_record_unbounded(self.document_object,
                                                                                       parsed_comment,
                                                                                       schema_element)
                        if related_records_dict and related_records_dict["value"]:
                            if schema_element.attrib["type"].replace("amcr:", "") \
                                    not in ("refType", "autorType", "wktType", "gmlType", "xs:string",
                                            "langstringType", "vocabType"):
                                self._iterate_unbound_records(related_records_dict, schema_element, parent_element)
                            else:
                                self._create_many_to_many_ref_elements(schema_element, parent_element,
                                                                       related_records_dict,
                                                                       parsed_comment=parsed_comment,
                                                                       prefix=prefix,
                                                                       ref_type=schema_element.attrib["type"])
            elif "choice" in schema_element.tag.lower():
                for child_schema_element in schema_element:
                    self._parse_scheme_create_element(child_schema_element, parent_element)

    def _iterate_unbound_records(self, related_records, schema_element, parent_element):
        child_schema_element = self._parse_schema(schema_element.attrib["type"])
        for obj in related_records["value"]:
            self._parse_scheme_create_nested_element(child_schema_element, parent_element, obj,
                                                     schema_element.attrib["name"])

    def _parse_scheme_create_nested_element(self, schema_element, parent_element, document_object,
                                            child_parent_element_name):
        child_parent_element = ET.SubElement(parent_element, f"{{{AMCR_NAMESPACE_URL}}}{child_parent_element_name}",
                                             nsmap=self._nsmap)
        for child_schema_element in schema_element:
            if child_schema_element.__class__.__name__ == "_Element":
                next_element = child_schema_element.getnext()
                if next_element.__class__.__name__ == "_Comment":
                    parsed_comment: ParsedComment = self._parse_comment(next_element.text)
                    prefix = self._get_prefix(next_element.text)
                    if child_schema_element.attrib["maxOccurs"] == "1":
                        if parsed_comment.value_field_name is not None:
                            if child_schema_element.attrib["type"] in self._simple_element_types:
                                self._create_element(child_schema_element, child_parent_element,
                                                     parsed_comment, document_object, prefix,
                                                     ref_type=child_schema_element.attrib["type"])
                            else:
                                obj = self._get_attribute_of_record(parsed_comment.value_field_name,
                                                                    record=document_object)
                                if obj is not None:
                                    inner_child_schema_element = self._parse_schema(child_schema_element.attrib["type"])
                                    self._parse_scheme_create_nested_element(inner_child_schema_element,
                                                                             child_parent_element, obj,
                                                                             child_schema_element.attrib["name"])
                    else:
                        related_records_dict = self._get_attribute_of_record_unbounded(document_object,
                                                                                  parsed_comment,
                                                                                  child_schema_element)
                        if related_records_dict is not None and len(related_records_dict) > 0:
                            if child_schema_element.attrib["type"].replace("amcr:", "") \
                                    not in ("refType", "autorType", "wktType", "gmlType", "xs:string",
                                            "langstringType", "vocabType"):
                                self._iterate_unbound_records(related_records_dict, child_schema_element,
                                                              child_parent_element)
                            else:
                                self._create_many_to_many_ref_elements(child_schema_element, child_parent_element,
                                                                       related_records_dict, parsed_comment, prefix,
                                                                       child_schema_element.attrib["type"])

    def get_ref_type_attribute_name(self, type_name):
        parser = etree.XMLParser()
        type_name = type_name.replace("amcr:", "")
        if type_name not in self.attribute_names:
            tree = etree.parse(self.get_path_to_schema(), parser)
            xpath_query = f"//*[@name='{type_name}']/*/*/*"
            elements = tree.xpath(xpath_query)
            if "name" in elements[0].attrib:
                self.attribute_names[type_name] = elements[0].attrib["name"]
        return self.attribute_names.get(type_name, "id")

    @staticmethod
    def _replace_redundant_namespaces(xml_string):
        pattern = r'\sxmlns:gml="[^"]*"'
        counter = [0]

        def replace(match):
            if counter[0] > 0:
                return ""
            else:
                counter[0] += 1
                return match.group()

        xml_string = re.sub(pattern, replace, xml_string.decode("utf-8"))
        xml_string = ET.fromstring(xml_string)
        xml_string = ET.tostring(xml_string, encoding='utf-8', xml_declaration=True, pretty_print=True)
        return xml_string

    def generate_document(self):
        self.document_root.attrib[f"{{http://www.w3.org/2001/XMLSchema-instance}}schemaLocation"] = SCHEMA_LOCATION
        parent_element = ET.SubElement(self.document_root, f"{{{AMCR_NAMESPACE_URL}}}{self._get_schema_name()}",
                                       nsmap=self._nsmap)
        for schema_element in self._parse_schema(self._get_schema_name()):
            self._parse_scheme_create_element(schema_element, parent_element)
            children = list(schema_element)
            if len(children) == 1:
                inner_document_element = \
                    ET.SubElement(parent_element, f"{{{AMCR_NAMESPACE_URL}}}{schema_element.attrib['name']}",
                                  nsmap=self._nsmap)
                for child_schema_element in children[0][0]:
                    self._parse_scheme_create_element(child_schema_element, inner_document_element)
        xml_string = ET.tostring(self.document_root)
        xml_string = self._replace_redundant_namespaces(xml_string)
        return xml_string

    def __init__(self, document_object):
        self.document_object = document_object
        ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
        ET.register_namespace("gml", "http://www.opengis.net/gml/3.2")
        ET.register_namespace("amcr", AMCR_NAMESPACE_URL)
        self.document_root = ET.Element(f"{{{AMCR_NAMESPACE_URL}}}amcr", nsmap=self._nsmap)
