import datetime
import logging
import os
import re
import threading
from dataclasses import dataclass
from typing import Optional

from adb.models import VyskovyBod
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import AsGML, GeoFunc
from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist
from heslar.models import Heslar, RuianKraj, RuianOkres
from lxml import etree
from lxml import etree as ET

AMCR_NAMESPACE_URL = "https://api.aiscr.cz/schema/amcr/2.2/"
AMCR_XSD_URL = "https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd"
AMCR_XSD_FILENAME = "amcr.xsd"
SCHEMA_LOCATION = "https://api.aiscr.cz/schema/amcr/2.2/ https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd"
logger = logging.getLogger(__name__)

#: Per-vláknová cache naparsovaného XSD stromu (viz ``DocumentGenerator._get_schema_tree``).
#: XSD se během běhu procesu nemění, ale `lxml` `_ElementTree`/`xpath()` není bezpečné
#: sdílet mezi vlákny (konkurentní XPath nad jedním sdíleným dokumentem je v `lxml`
#: dlouhodobě zdroj hlášených pádů) - a `generate_metadata_fast --workers N` volá
#: generování dokumentů z mnoha paralelních vláken. Proto per-vlákno, ne
#: ``functools.lru_cache`` sdílený přes všechna vlákna - cena je pár desítek ms
#: parsování navíc na vlákno (místo jednou celkem), riziko pádu je nula.
_schema_tree_local = threading.local()


class AsText(GeoFunc):
    """Implementuje komponentu ``AsText`` v rámci aplikace."""

    output_field = models.TextField()


@dataclass
class ParsedComment:
    """Implementuje komponentu ``ParsedComment`` v rámci aplikace."""

    value_field_name: str
    attribute_field_names: list = None


class DocumentGenerator:
    """Implementuje komponentu ``DocumentGenerator`` v rámci aplikace."""

    _nsmap = {
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "gml": "http://www.opengis.net/gml/3.2",
        "amcr": AMCR_NAMESPACE_URL,
        "xml": "http://www.w3.org/XML/1998/namespace",
    }
    attribute_names = {}
    _simple_element_types = (
        "xs:string",
        "xs:date",
        "xs:integer",
        "amcr:refType",
        "xs:dateTime",
        "amcr:gmlType",
        "amcr:wktType",
        "amcr:autorType",
        "xs:boolean",
        "amcr:langstringType",
        "amcr:vocabType",
        "xs:decimal",
        "xs:anyURI",
    )

    @classmethod
    def _get_schema_dict(cls):
        """
        Vrací schema dict.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        from adb.models import Adb
        from arch_z.models import ArcheologickyZaznam
        from dokument.models import Dokument, Let
        from ez.models import ExterniZdroj
        from heslar.models import Heslar, RuianKatastr, RuianKraj, RuianOkres
        from pas.models import SamostatnyNalez
        from pian.models import Pian
        from projekt.models import Projekt
        from uzivatel.models import Organizace, Osoba, User

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
        """
        Vrací schema name.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        type_class_dict = self._get_schema_dict()
        object_class = self.document_object.__class__
        name = type_class_dict.get(object_class)
        return name

    @staticmethod
    def _create_xpath_query(model_name):
        """
        Vytvoří xpath query.

        :param model_name: Název modelu používaný pro cílení operace.
        :return: Nově vytvořená hodnota připravená touto funkcí.
        """
        if model_name.lower().endswith("type"):
            model_name = model_name.replace("amcr:", "")
            query_attribute_selection = f"[local-name()='complexType' and @name='{model_name}']"
        else:
            query_attribute_selection = f"[local-name()='complexType' and @name='{model_name}Type']"
        query = f"//*{query_attribute_selection}/*/*|//*{query_attribute_selection}/*/comment()"
        return query

    @staticmethod
    def get_path_to_schema():
        """
        Vrací path to schema.

        :return: Vrací výsledek volání ``join()``.
        """
        return os.path.join("xml_generator/definitions/", AMCR_XSD_FILENAME)

    @staticmethod
    def _get_schema_tree(schema_path):
        """
        Načte a naparsuje XSD schema; výsledek je cachovaný po dobu běhu vlákna.

        XSD soubor se během běhu nemění, opakované ``etree.parse()`` při každém
        volání :func:`_parse_schema`/:func:`get_ref_type_attribute_name` bylo
        zbytečné čtení a parsování ze disku (desítky ms na volání). Cache je
        per-vlákno (viz ``_schema_tree_local``), ne sdílená přes všechna vlákna -
        a klíčovaná podle ``schema_path``, ne jen jedna hodnota na vlákno, aby
        metoda respektovala svůj vlastní argument (kdyby o stejného vlákna žádal
        strom pro jinou cestu, dostal by mylně strom z první cesty).

        :param schema_path: Cesta k XSD schema souboru.
        :return: Naparsovaný ``lxml.etree._ElementTree``.
        """
        trees = getattr(_schema_tree_local, "trees", None)
        if trees is None:
            trees = {}
            _schema_tree_local.trees = trees
        tree = trees.get(schema_path)
        if tree is None:
            tree = etree.parse(schema_path, etree.XMLParser())
            trees[schema_path] = tree
        return tree

    def _parse_schema(self, model_name):
        """
               Zpracuje schema.

               :param model_name: Název modelu používaný pro cílení operace.
        :return: Výstup funkce odpovídající implementované logice.
        """
        tree = self._get_schema_tree(self.get_path_to_schema())
        return tree.xpath(self._create_xpath_query(model_name))

    @staticmethod
    def _get_prefix(comment_text: str) -> str:
        """
        Vrací prefix.

        :param comment_text: Číselná hodnota ``comment_text`` použitá při výpočtu nebo transformaci.
        :return: Načtená data odpovídající zadaným vstupům.
        """
        if "-" not in comment_text:
            return ""
        if "|" in comment_text:
            comment_text_split = comment_text.split("|")
            comment_text = comment_text_split[0]
        attribute_prefix = comment_text[: comment_text.find("-") + 1]
        attribute_prefix = attribute_prefix.replace('"', "").replace("{", "").replace("}", "").strip()
        return attribute_prefix

    @staticmethod
    def _parse_comment(comment_text: str) -> Optional[ParsedComment]:
        """
               Zpracuje comment.

               :param comment_text: Číselná hodnota ``comment_text`` použitá při výpočtu nebo transformaci.
        :return: Výstup funkce odpovídající implementované logice.
        """
        attribute_list = comment_text.split("|")
        attribute_list = [
            text.replace('"', "").replace("{", "").replace("}", "").strip().lower() for text in attribute_list
        ]
        attribute_list = [text[text.find("-") + 1 :] if "-" in text else text for text in attribute_list]
        if len(attribute_list) == 2:
            return ParsedComment(attribute_list[1], [attribute_list[0]])
        elif len(attribute_list) == 1:
            return ParsedComment(attribute_list[0])
        elif len(attribute_list) == 3:
            return ParsedComment(attribute_list[-1], attribute_list[:-1])

    _MISSING = object()

    def _get_cached_related(self, record, attr_name, default=_MISSING):
        """
        Ekvivalent ``getattr(record, attr_name[, default])``, ale pro ForeignKey na
        ``Heslar`` použije cache v rámci životnosti tohoto ``DocumentGenerator``.

        Stejný heslářový kód se v rámci jednoho dokumentu často vyskytuje vícekrát
        (různé prvky schématu odkazují na stejnou klasifikaci) - bez cache se
        zbytečně opakovaně dotazuje ta samá řádka `heslar` (viz profiling issue #3967:
        ~34 % dotazů na `heslar` uvnitř jednoho záznamu byly duplicity). Cache nikdy
        nepřežije jeden dokument, takže nehrozí zastaralá data napříč záznamy.

        :param record: Instance modelu (nebo ``None``), ze které se atribut čte.
        :param attr_name: Název atributu/pole.
        :param default: Výchozí hodnota při chybějícím atributu; není-li zadána,
            chová se jako ``getattr`` bez výchozí hodnoty (vyhodí ``AttributeError``).
        :return: Hodnota atributu.
        """
        field = None
        if record is not None:
            try:
                field = record._meta.get_field(attr_name)
            except FieldDoesNotExist:
                field = None
        if field is not None and getattr(field, "many_to_one", False) and field.related_model is Heslar:
            if field.is_cached(record):
                # Instance už hodnotu má (Django ji nacachoval dřív, např. eagerní
                # čtení v __init__ některých modelů) - použij ji, ať se nedotazuje
                # znovu cestou přes _heslar_cache zbytečně navíc.
                return field.get_cached_value(record)
            fk_id = getattr(record, field.attname, None)
            if fk_id is None:
                return None
            if fk_id not in self._heslar_cache:
                # `.get()`, ne `.filter().first()` - nerozbitá FK musí vyhodit
                # `Heslar.DoesNotExist` stejně jako by to udělal obyčejný FK
                # descriptor přes `getattr()` (chování před zavedením cache).
                # Negativní výsledek se neukládá do cache, ať se chyba neschová
                # jen proto, že šlo o druhé volání pro stejné `fk_id`.
                self._heslar_cache[fk_id] = Heslar.objects.get(pk=fk_id)
            return self._heslar_cache[fk_id]
        if default is self._MISSING:
            return getattr(record, attr_name)
        return getattr(record, attr_name, default)

    def _get_attribute_of_record(self, attribute_name, record=None):
        """
        Vrací attribute of record.

        :param attribute_name: Textový název nebo klíč ``attribute_name`` používaný v rámci operace.
        :param record: Parametr ``record`` předává se do volání ``getattr()``, ``isinstance()``, pracuje se s atributy ``__class__``, ``pk``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :return: Načtená data odpovídající zadaným vstupům.
        """
        attribute_value = None
        if record is None:
            record = self.document_object
        if attribute_name.lower() == "self":
            return record
        if "." not in attribute_name and "(" not in attribute_name:
            attribute_value = self._get_cached_related(record, attribute_name, None)
        elif (
            "st_asgml" in attribute_name.lower()
            or "st_astext" in attribute_name.lower()
            or "st_srid" in attribute_name.lower()
        ):
            from dokument.models import DokumentExtraData
            from heslar.models import RuianKatastr
            from pas.models import SamostatnyNalez
            from pian.models import Pian
            from projekt.models import Projekt

            # Stejný záznam (`record.pk` v rámci jedné třídy) se v rámci jednoho
            # dokumentu často žádá o víc geometrických atributů (st_asgml/st_astext/
            # st_srid) - bez cache by se pro každý z nich zbytečně opakoval stejný
            # anotovaný dotaz. Cache nikdy nepřežije jeden dokument (viz __init__).
            cache_key = (record.__class__, record.pk)
            if cache_key in self._geom_annotation_cache:
                record = self._geom_annotation_cache[cache_key]
            else:
                if isinstance(record, Projekt):
                    record = record.__class__.objects.annotate(
                        geom_st_asgml=AsGML("geom", nprefix="gml"),
                        geom_st_astext=AsText("geom"),
                        geom_sjtsk_st_asgml=AsGML("geom_sjtsk", nprefix="gml"),
                        geom_sjtsk_st_astext=AsText("geom_sjtsk"),
                    ).get(pk=record.pk)
                elif isinstance(record, DokumentExtraData):
                    try:
                        record = record.__class__.objects.annotate(
                            geom_st_asgml=AsGML("geom", nprefix="gml"),
                            geom_st_astext=AsText("geom"),
                            geom_sjtsk_st_asgml=AsGML("geom_sjtsk", nprefix="gml"),
                            geom_sjtsk_st_astext=AsText("geom_sjtsk"),
                        ).get(pk=record.pk)
                    except ObjectDoesNotExist:
                        record = DokumentExtraData()
                        setattr(record, "geom_st_asgml", None)
                        setattr(record, "geom_st_astext", None)
                        setattr(record, "geom_sjtsk_st_asgml", None)
                        setattr(record, "geom_sjtsk_st_astext", None)
                elif isinstance(record, VyskovyBod):
                    record = record.__class__.objects.annotate(
                        geom_st_asgml=AsGML("geom", nprefix="gml"),
                        geom_st_astext=AsText("geom"),
                    ).get(pk=record.pk)
                elif isinstance(record, SamostatnyNalez) or isinstance(record, Pian):
                    record = record.__class__.objects.annotate(
                        geom_st_asgml=AsGML("geom", nprefix="gml"),
                        geom_st_astext=AsText("geom"),
                        geom_sjtsk_st_asgml=AsGML("geom_sjtsk", nprefix="gml"),
                        geom_sjtsk_st_astext=AsText("geom_sjtsk"),
                    ).get(pk=record.pk)
                elif (
                    isinstance(record, RuianKatastr) or isinstance(record, RuianKraj) or isinstance(record, RuianOkres)
                ):
                    record = record.__class__.objects.annotate(
                        definicni_bod_st_asgml=AsGML("definicni_bod", nprefix="gml"),
                        definicni_bod_st_astext=AsText("definicni_bod"),
                        hranice_st_asgml=AsGML("hranice", nprefix="gml"),
                        hranice_st_astext=AsText("hranice"),
                    ).get(pk=record.pk)
                self._geom_annotation_cache[cache_key] = record
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
                attribute_value = attribute_value.replace(">", ' xmlns:gml="http://www.opengis.net/gml/3.2">', 1)
                attribute_value = ET.fromstring(attribute_value)
        else:
            record_name_split = attribute_name.split(".")
            if len(record_name_split) == 2:
                related_record = self._get_cached_related(record, record_name_split[0], None)
                attribute_value = self._get_cached_related(related_record, record_name_split[1], None)
            elif len(record_name_split) == 3:
                related_record = self._get_cached_related(record, record_name_split[0], None)
                second_related_record = self._get_cached_related(related_record, record_name_split[1], None)
                attribute_value = self._get_cached_related(second_related_record, record_name_split[2], None)
            elif len(record_name_split) == 4:
                related_record_1 = self._get_cached_related(record, record_name_split[0], None)
                related_record_2 = self._get_cached_related(related_record_1, record_name_split[1], None)
                related_record_3 = self._get_cached_related(related_record_2, record_name_split[2], None)
                attribute_value = self._get_cached_related(related_record_3, record_name_split[3], None)
        return attribute_value

    def _get_attribute_of_record_unbounded(self, record, parsed_comment: ParsedComment, schema_element) -> dict:
        """
        Vrací attribute of record unbounded.

        :param record: Parametr ``record`` předává se do volání ``get_attribute()``.
        :param parsed_comment: Parametr ``parsed_comment`` se předává do volání ``get_attribute()``, pracuje se s atributy ``value_field_name``, ``attribute_field_names``, ovlivňuje větvení podmínek.
        :param schema_element: Parametr ``schema_element`` slouží jako vstup pro logiku funkce ``_get_attribute_of_record_unbounded``.
        :return: Načtená data odpovídající zadaným vstupům.
        """
        attributes_dict = {}

        def get_attribute(record, attribute_name):
            """
            Vrací attribute. v aplikaci.

            :param record: Parametr ``record`` předává se do volání ``getattr()``, ``isinstance()``, ovlivňuje větvení podmínek.
            :param attribute_name: Textový název nebo klíč ``attribute_name`` používaný v rámci operace.

                :return: Vrací proměnná ``attributes``.
            """
            attributes = []
            record_name_split = attribute_name.split(".")
            if len(record_name_split) == 1:
                record_attribute = self._get_cached_related(record, record_name_split[0])
                if hasattr(record_attribute, "all"):
                    attributes = [x for x in record_attribute.all()]
                else:
                    attributes = [record_attribute]
            elif len(record_name_split) == 2:
                try:
                    related_record = self._get_cached_related(record, record_name_split[0])
                except ObjectDoesNotExist:
                    related_record = None
                    from uzivatel.models import User

                    # Známý problém: smazání uživatele selže, pokud má nastavenou notifikaci.
                    if not (isinstance(record, User) and record_name_split[0] == "history_vazba"):
                        logger.warning(
                            "xml_generator.generator.DocumentGenerator."
                            "_get_attribute_of_record_unbounded.object_does_not_exist",
                            extra={
                                "ident_cely": getattr(record, "ident_cely", None),
                                "record": record_name_split[0],
                            },
                        )
                if related_record and hasattr(related_record, "all"):
                    for item in related_record.all():
                        attributes.append(self._get_cached_related(item, record_name_split[1], None))
                elif related_record:
                    related_record = self._get_cached_related(record, record_name_split[0], None)
                    related_record = self._get_cached_related(related_record, record_name_split[1], None)
                    if hasattr(related_record, "all"):
                        attributes = []
                        try:
                            for x in related_record.all():
                                attributes.append(x)
                        except Exception as err:
                            logger.info(
                                "xml_generator.generator._get_attribute_of_record_unbounded.attr.append.error",
                                extra={"error": err},
                            )
            elif len(record_name_split) == 3:
                related_record = self._get_cached_related(record, record_name_split[0])
                if hasattr(related_record, "all"):
                    for record in related_record.all():
                        first_related = self._get_cached_related(record, record_name_split[1], None)
                        if first_related is not None:
                            second_related = self._get_cached_related(first_related, record_name_split[2], None)
                            attributes.append(second_related)
                else:
                    related_record = self._get_cached_related(related_record, record_name_split[1], None)
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

    def _create_element(
        self,
        schema_element,
        parent_element,
        parsed_comment: ParsedComment,
        document_object=None,
        id_field_prefix="",
        ref_type=None,
    ):
        """
        Vytvoří element.

        :param schema_element: Parametr ``schema_element`` se předává do volání ``SubElement()``, pracuje se s atributy ``attrib``.
        :param parent_element: Parametr ``parent_element`` předává se do volání ``SubElement()``.
        :param parsed_comment: Parametr ``parsed_comment`` se předává do volání ``_get_attribute_of_record()``, pracuje se s atributy ``value_field_name``, ``attribute_field_names``, ovlivňuje větvení podmínek.
        :param document_object: Parametr ``document_object`` předává se do volání ``_get_attribute_of_record()``, ovlivňuje větvení podmínek.
        :param id_field_prefix: Parametr ``id_field_prefix`` ovlivňuje větvení podmínek.
        :param ref_type: Parametr ``ref_type`` předává se do volání ``get_ref_type_attribute_name()``, ovlivňuje větvení podmínek.
        :return: Nově vytvořená hodnota připravená touto funkcí.
        """
        if document_object is None:
            document_object = self.document_object
        attribute_value = self._get_attribute_of_record(parsed_comment.value_field_name, document_object)
        if parsed_comment.attribute_field_names is None and id_field_prefix:
            attribute_value = id_field_prefix + str(attribute_value)
        if attribute_value is not None and len(str(attribute_value)) > 0:
            new_sub_element = ET.SubElement(
                parent_element, f"{{{AMCR_NAMESPACE_URL}}}{schema_element.attrib['name']}", nsmap=self._nsmap
            )
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
                new_sub_element.attrib[f"{{{self._nsmap['xml']}}}lang"] = (
                    "en" if parsed_comment.value_field_name.endswith("_en") else "cs"
                )
            if parsed_comment.attribute_field_names is not None:
                for attribute_field_name in parsed_comment.attribute_field_names:
                    attribute_name = self.get_ref_type_attribute_name(ref_type)
                    new_sub_element.attrib[attribute_name] = (
                        f"{id_field_prefix}{self._get_attribute_of_record(attribute_field_name, document_object)}"
                    )

    def _create_many_to_many_ref_elements(
        self, schema_element, parent_element, related_records, parsed_comment: ParsedComment, prefix="", ref_type=None
    ):
        """
        Vytvoří many to many ref elements.

        :param schema_element: Parametr ``schema_element`` se předává do volání ``SubElement()``, pracuje se s atributy ``attrib``.
        :param parent_element: Parametr ``parent_element`` předává se do volání ``SubElement()``.
        :param related_records: Parametr ``related_records`` předává se do volání ``enumerate()``.
        :param parsed_comment: Parametr ``parsed_comment`` se předává do volání ``len()``, pracuje se s atributy ``attribute_field_names``, ovlivňuje větvení podmínek.
        :param prefix: Číselná hodnota ``prefix`` použitá při výpočtu nebo transformaci.
        :param ref_type: Parametr ``ref_type`` předává se do volání ``get_ref_type_attribute_name()``, ovlivňuje větvení podmínek.
        :return: Nově vytvořená hodnota připravená touto funkcí.
        """
        for i, record in enumerate(related_records["value"]):
            new_sub_element = ET.SubElement(
                parent_element, f"{{{AMCR_NAMESPACE_URL}}}" + schema_element.attrib["name"], nsmap=self._nsmap
            )
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
                    new_sub_element.attrib[f"{{{self._nsmap['xml']}}}lang"] = (
                        "en" if parsed_comment.attribute_field_names[0].endswith("_en") else "cs"
                    )
                else:
                    new_sub_element.attrib[f"{{{self._nsmap['xml']}}}lang"] = "cs"
            if parsed_comment.attribute_field_names is not None:
                new_sub_element.attrib["id"] = f"{prefix}{related_records[parsed_comment.attribute_field_names[0]][i]}"
                if len(parsed_comment.attribute_field_names) == 2:
                    attribute_name = self.get_ref_type_attribute_name(ref_type)
                    new_sub_element.attrib[attribute_name] = (
                        f"{prefix}{related_records[parsed_comment.attribute_field_names[1]][i]}"
                    )

    def _parse_scheme_create_element(self, schema_element, parent_element):
        """
               Zpracuje scheme create element.

               :param schema_element: Parametr ``schema_element`` se předává do volání ``_create_element()``, ``_parse_schema()``, pracuje se s atributy ``__class__``, ``getnext``, ovlivňuje větvení podmínek.
               :param parent_element: Parametr ``parent_element`` předává se do volání ``_create_element()``, ``_parse_scheme_create_nested_element()``.
        :return: Výstup funkce odpovídající implementované logice.
        """
        if schema_element.__class__.__name__ == "_Element":
            next_element = schema_element.getnext()
            # Komentář by měl být bezprostředně následující element.
            if next_element.__class__.__name__ == "_Comment":
                parsed_comment: ParsedComment = self._parse_comment(next_element.text)
                prefix = self._get_prefix(next_element.text)
                if "maxOccurs" not in schema_element.attrib or schema_element.attrib["maxOccurs"] == "1":
                    if parsed_comment.value_field_name is not None:
                        if schema_element.attrib["type"] in self._simple_element_types:
                            self._create_element(
                                schema_element,
                                parent_element,
                                parsed_comment,
                                id_field_prefix=prefix,
                                ref_type=schema_element.attrib["type"],
                            )
                        else:
                            obj = self._get_attribute_of_record(parsed_comment.value_field_name)
                            if obj is not None:
                                child_schema_element = self._parse_schema(schema_element.attrib["type"])
                                self._parse_scheme_create_nested_element(
                                    child_schema_element, parent_element, obj, schema_element.attrib["name"]
                                )
                elif schema_element.attrib["maxOccurs"] == "unbounded":
                    if parsed_comment.value_field_name is not None:
                        related_records_dict = self._get_attribute_of_record_unbounded(
                            self.document_object, parsed_comment, schema_element
                        )
                        if related_records_dict and related_records_dict["value"]:
                            if schema_element.attrib["type"].replace("amcr:", "") not in (
                                "refType",
                                "autorType",
                                "wktType",
                                "gmlType",
                                "xs:string",
                                "langstringType",
                                "vocabType",
                                "xs:anyURI",
                            ):
                                self._iterate_unbound_records(related_records_dict, schema_element, parent_element)
                            else:
                                self._create_many_to_many_ref_elements(
                                    schema_element,
                                    parent_element,
                                    related_records_dict,
                                    parsed_comment=parsed_comment,
                                    prefix=prefix,
                                    ref_type=schema_element.attrib["type"],
                                )
            elif "choice" in schema_element.tag.lower():
                for child_schema_element in schema_element:
                    self._parse_scheme_create_element(child_schema_element, parent_element)

    def _iterate_unbound_records(self, related_records, schema_element, parent_element):
        """
               Provádí operaci iterate unbound records.

               :param related_records: Parametr ``related_records`` slouží jako vstup pro logiku funkce ``_iterate_unbound_records``.
               :param schema_element: Parametr ``schema_element`` se předává do volání ``_parse_schema()``, ``_parse_scheme_create_nested_element()``, pracuje se s atributy ``attrib``.
               :param parent_element: Parametr ``parent_element`` předává se do volání ``_parse_scheme_create_nested_element()``.
        :return: Výstup funkce odpovídající implementované logice.
        """
        child_schema_element = self._parse_schema(schema_element.attrib["type"])
        for obj in related_records["value"]:
            self._parse_scheme_create_nested_element(
                child_schema_element, parent_element, obj, schema_element.attrib["name"]
            )

    def _parse_scheme_create_nested_element(
        self, schema_element, parent_element, document_object, child_parent_element_name
    ):
        """
               Zpracuje scheme create nested element.

               :param schema_element: Parametr ``schema_element`` slouží jako vstup pro logiku funkce ``_parse_scheme_create_nested_element``.
               :param parent_element: Parametr ``parent_element`` předává se do volání ``SubElement()``.
               :param document_object: Parametr ``document_object`` předává se do volání ``_create_element()``, ``_get_attribute_of_record()``.
               :param child_parent_element_name: Textový název nebo klíč ``child_parent_element_name`` používaný v rámci operace.
        :return: Výstup funkce odpovídající implementované logice.
        """
        child_parent_element = ET.SubElement(
            parent_element, f"{{{AMCR_NAMESPACE_URL}}}{child_parent_element_name}", nsmap=self._nsmap
        )
        for child_schema_element in schema_element:
            if child_schema_element.__class__.__name__ == "_Element":
                next_element = child_schema_element.getnext()
                if next_element.__class__.__name__ == "_Comment":
                    parsed_comment: ParsedComment = self._parse_comment(next_element.text)
                    prefix = self._get_prefix(next_element.text)
                    if child_schema_element.attrib["maxOccurs"] == "1":
                        if parsed_comment.value_field_name is not None:
                            if child_schema_element.attrib["type"] in self._simple_element_types:
                                self._create_element(
                                    child_schema_element,
                                    child_parent_element,
                                    parsed_comment,
                                    document_object,
                                    prefix,
                                    ref_type=child_schema_element.attrib["type"],
                                )
                            else:
                                obj = self._get_attribute_of_record(
                                    parsed_comment.value_field_name, record=document_object
                                )
                                if obj is not None:
                                    inner_child_schema_element = self._parse_schema(child_schema_element.attrib["type"])
                                    self._parse_scheme_create_nested_element(
                                        inner_child_schema_element,
                                        child_parent_element,
                                        obj,
                                        child_schema_element.attrib["name"],
                                    )
                    else:
                        related_records_dict = self._get_attribute_of_record_unbounded(
                            document_object, parsed_comment, child_schema_element
                        )
                        if related_records_dict is not None and len(related_records_dict) > 0:
                            if child_schema_element.attrib["type"].replace("amcr:", "") not in (
                                "refType",
                                "autorType",
                                "wktType",
                                "gmlType",
                                "xs:string",
                                "langstringType",
                                "vocabType",
                                "xs:anyURI",
                            ):
                                self._iterate_unbound_records(
                                    related_records_dict, child_schema_element, child_parent_element
                                )
                            else:
                                self._create_many_to_many_ref_elements(
                                    child_schema_element,
                                    child_parent_element,
                                    related_records_dict,
                                    parsed_comment,
                                    prefix,
                                    child_schema_element.attrib["type"],
                                )

    def get_ref_type_attribute_name(self, type_name):
        """
        Vrací ref type attribute name.

        :param type_name: Parametr ``type_name`` předává se do volání ``get()``, pracuje se s atributy ``replace``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``get()``.
        """
        type_name = type_name.replace("amcr:", "")
        if type_name not in self.attribute_names:
            tree = self._get_schema_tree(self.get_path_to_schema())
            xpath_query = f"//*[@name='{type_name}']/*/*/*"
            elements = tree.xpath(xpath_query)
            if "name" in elements[0].attrib:
                self.attribute_names[type_name] = elements[0].attrib["name"]
        return self.attribute_names.get(type_name, "id")

    @staticmethod
    def _replace_redundant_namespaces(xml_string):
        """
               Provádí operaci replace redundant namespaces.

               :param xml_string: Parametr ``xml_string`` se předává do volání ``sub()``, ``fromstring()``, pracuje se s atributy ``decode``, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.
        """
        pattern = r'\sxmlns:gml="[^"]*"'
        counter = [0]

        def replace(match):
            """
            Provádí operaci replace.

            :param match: Parametr ``match`` pracuje se s atributy ``group``, vstupuje do návratové hodnoty.

                :return: Vrací hodnotu podle větve zpracování, typicky: str, výsledek volání ``group()``.
            """
            if counter[0] > 0:
                return ""
            else:
                counter[0] += 1
                return match.group()

        xml_string = re.sub(pattern, replace, xml_string.decode("utf-8"))
        xml_string = ET.fromstring(xml_string)
        xml_string = ET.tostring(xml_string, encoding="utf-8", xml_declaration=True, pretty_print=True)
        return xml_string

    def generate_document(self):
        """
        Vygeneruje document. v aplikaci.

        :return: Vrací proměnná ``xml_string``.
        """
        self.document_root.attrib["{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"] = SCHEMA_LOCATION
        parent_element = ET.SubElement(
            self.document_root, f"{{{AMCR_NAMESPACE_URL}}}{self._get_schema_name()}", nsmap=self._nsmap
        )
        for schema_element in self._parse_schema(self._get_schema_name()):
            self._parse_scheme_create_element(schema_element, parent_element)
            children = list(schema_element)
            if len(children) == 1:
                inner_document_element = ET.SubElement(
                    parent_element, f"{{{AMCR_NAMESPACE_URL}}}{schema_element.attrib['name']}", nsmap=self._nsmap
                )
                for child_schema_element in children[0][0]:
                    self._parse_scheme_create_element(child_schema_element, inner_document_element)
        xml_string = ET.tostring(self.document_root)
        xml_string = self._replace_redundant_namespaces(xml_string)
        return xml_string

    def __init__(self, document_object):
        """
        Inicializuje instanci třídy.

        :param document_object: Parametr ``document_object`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        self.document_object = document_object
        self._heslar_cache = {}
        self._geom_annotation_cache = {}
        ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
        ET.register_namespace("gml", "http://www.opengis.net/gml/3.2")
        ET.register_namespace("amcr", AMCR_NAMESPACE_URL)
        self.document_root = ET.Element(f"{{{AMCR_NAMESPACE_URL}}}amcr", nsmap=self._nsmap)
