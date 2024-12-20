import logging

from adb.models import VyskovyBod
from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
from core.models import Soubor
from dj.models import DokumentacniJednotka
from django.db import connection, transaction
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from dokument.models import Dokument, DokumentCast, Tvar
from ez.models import ExterniZdroj
from historie.models import Historie
from komponenta.models import Komponenta
from nalez.models import NalezObjekt, NalezPredmet
from pas.models import SamostatnyNalez
from projekt.models import Projekt
from projekt.views import get_show_oznamovatel

logger = logging.getLogger(__name__)


def get_model(name):
    models = {
        "tvary": Tvar,
        "dokument": Dokument,
        "dokument_casti": DokumentCast,
        "komponenty": Komponenta,
        "objekty": NalezObjekt,
        "predmety": NalezPredmet,
        "historie": Historie,
        "soubory": Soubor,
        "projekt": Projekt,
        "archeologicky_zaznam": ArcheologickyZaznam,
        "samostatny_nalez": SamostatnyNalez,
        "akce": ArcheologickyZaznam,
        "dokumentacni_jednotka": DokumentacniJednotka,
        "vb": VyskovyBod,
        "ext_odkaz": ExterniOdkaz,
        "lokalita": ArcheologickyZaznam,
        "pas": SamostatnyNalez,
        "model": Dokument,
        "ez": ExterniZdroj,
    }
    return models.get(name)


def get_gml(geom):
    try:
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("SELECT ST_AsGML(%s)", [geom.wkt])
            row = cursor.fetchone()
        return row[0]
    except Exception as e:
        logger.error(f"Error executing SQL: {e}")
        return None


def get_wkt(geom):
    with connection.cursor() as cursor:
        cursor.execute("SELECT ST_AsText(ST_GeomFromText(%s))", [geom.wkt])
        row = cursor.fetchone()
        cursor.close()
        return row[0]


class SimpleSectionTemplateName:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def get_name(self, instance):
        return self.name

    def get_permission(self, instance, user=None):
        return True


class SectionNameWithAccessor(SimpleSectionTemplateName):
    def __init__(self, name, accessor, foreign_key=None):
        super().__init__(name)
        self.accessor = accessor
        self.foreign_key = foreign_key

    def get_name(self, instance):
        if self.foreign_key:
            if getattr(instance, self.foreign_key):
                return f"{self.name} {getattr(getattr(instance, self.foreign_key), self.accessor)}"
            else:
                return None
        return f"{self.name} {getattr(instance, self.accessor)}"


class PianSectionNameWithAccessor(SectionNameWithAccessor):
    def get_name(self, instance):
        if getattr(instance, self.foreign_key):
            pian = getattr(instance, self.foreign_key)
            stav = getattr(pian, self.accessor[1])()
            return f"{self.name} {getattr(pian, self.accessor[0])} ({stav}) - {getattr(pian, self.accessor[2])} ({getattr(pian, self.accessor[3])})"
        else:
            return None


class OznamovatelSectionNameWithAccessor(SectionNameWithAccessor):
    def get_permission(self, instance, user=None):
        return get_show_oznamovatel(instance, user)


class Field:
    def __init__(self, label, accessor):
        self.label = label
        self.accessor = accessor

    def __repr__(self):
        return f"Field(label={self.label}, accessor={self.accessor})"

    def __str__(self):
        return self.label

    def get_value(self, instance):
        return getattr(instance, self.accessor)

    def get_label(self):
        return self.label


class SouborField(Field):
    def __init__(self, label, accessor, key_name):
        super().__init__(label, accessor)
        self.key_name = key_name

    def get_value(self, instance):
        soubor = getattr(instance, self.accessor)
        if soubor:
            return reverse(
                "core:download_thumbnail",
                args=(
                    self.key_name,
                    instance.vazba.navazany_objekt.ident_cely,
                    instance.id,
                ),
            )
        return None


class SouborDownloadField(SouborField):
    def get_value(self, instance):
        accessor = getattr(instance, self.accessor)
        if accessor:
            return {
                "value": accessor,
                "download": reverse(
                    "core:download_thumbnail",
                    args=(
                        self.key_name,
                        instance.vazba.navazany_objekt.ident_cely,
                        instance.id,
                    ),
                ),
            }
        return None


class Model3dKomponentaField(Field):
    def get_value(self, instance):
        return getattr(instance.casti.first().komponenty.komponenty.first(), self.accessor)


class ChooseField(Field):
    def get_value(self, instance):
        for accessor in self.accessor:
            value = getattr(instance, accessor)
            if value:
                return str(value)
        return None


class StatusField(Field):
    def get_value(self, instance):
        return getattr(instance, self.accessor)()


class ForeignField(Field):
    def __init__(self, name, accessor, foreign_key):
        super().__init__(name, accessor)
        self.foreign_key = foreign_key

    def get_value(self, instance):
        if getattr(instance, self.foreign_key, False):
            return getattr(getattr(instance, self.foreign_key), self.accessor)
        return None


class GeomGmlField(Field):
    def get_value(self, instance):
        geom = getattr(instance, self.accessor)
        if geom:
            return get_gml(geom)
        return None


class GeomWktField(Field):
    def get_value(self, instance):
        geom = getattr(instance, self.accessor)
        if geom:
            epsg = get_wkt(geom)
            wkt = geom.srid
            return f"EPSG: {epsg}, {wkt}"
        return None


class ForeignGeomGmlField(ForeignField):
    def get_value(self, instance):
        geom = getattr(getattr(instance, self.foreign_key), self.accessor)
        if geom:
            return get_gml(geom)
        return None


class ForeignGeomWktField(ForeignField):
    def get_value(self, instance):
        geom = getattr(getattr(instance, self.foreign_key), self.accessor)
        if geom:
            epsg = get_wkt(geom)
            wkt = geom.srid
            return f"EPSG: {epsg}, {wkt}"
        return None


class ManyToManyField(Field):
    def get_value(self, instance):
        related_manager = getattr(instance, self.accessor)
        return ", ".join([str(v) for v in related_manager.all()])


class ForeignManyToManyField(ForeignField):
    def get_value(self, instance):
        if getattr(instance, self.foreign_key, False):
            related_manager = getattr(getattr(instance, self.foreign_key), self.accessor)
            return ", ".join([str(v) for v in related_manager.all()])
        return None


class DoubleField(Field):
    def get_value(self, instance):
        values = []
        for accessor in self.accessor:
            value = getattr(instance, accessor)
            if value:
                values.append(str(value))
        if values:
            return " - ".join(values)
        return None


class ForeignDoubleField(ForeignField):
    def get_value(self, instance):
        if getattr(instance, self.foreign_key, False):
            values = []
            for accessor in self.accessor:
                value = getattr(getattr(instance, self.foreign_key), accessor)
                if value:
                    values.append(str(value))
            if values:
                return " - ".join(values)
        return None


class RepeatableField(ForeignField):
    def __init__(self, name, accessor, foreign_key, template_name=None, model_name=None):
        super().__init__(name, accessor, foreign_key)
        self.template_name = template_name
        self.model_name = model_name

    def get_related_manager(self, instance):
        if self.model_name:
            return get_model(self.foreign_key).objects.filter(**{self.model_name: instance})
        return get_model(self.foreign_key).objects.filter(**{instance._meta.model_name: instance})

    def get_value(self, instance):
        related_manager = self.get_related_manager(instance)
        data = {
            "template_name": self.template_name,
        }
        if related_manager.count() > 0:
            data["zaznamy"] = []
            for v in related_manager.all():
                item = {}
                for accessor in self.accessor:
                    accessors = accessor.split("__")
                    new_v = v
                    for a in accessors:
                        new_v = getattr(new_v, a)
                    item[accessors[-1]] = new_v
                data["zaznamy"].append(item)
            return data
        return None


class VbRepeatableField(RepeatableField):
    def get_value(self, instance):
        related_manager = self.get_related_manager(instance)
        data = {
            "template_name": self.template_name,
        }
        if related_manager.count() > 0:
            data["zaznamy"] = []
            for v in related_manager.all():
                acc3_1 = getattr(v, "geom").srid
                acc3_2 = get_wkt(getattr(v, "geom"))
                item = {}
                item[self.accessor[0]] = getattr(v, self.accessor[0])
                item[self.accessor[1]] = getattr(v, self.accessor[1])
                item[self.accessor[2]] = get_gml(getattr(v, "geom"))
                item[self.accessor[3]] = f"EPSG:{acc3_1}, {acc3_2}"
                data["zaznamy"].append(item)
            return data
        return None


class HistorieRepeatableField(RepeatableField):
    def get_related_manager(self, instance):
        return Historie.objects.filter(**{"vazba": instance.historie})

    def get_value(self, instance):
        related_manager = self.get_related_manager(instance)
        data = {
            "template_name": self.template_name,
        }
        if related_manager.count() > 0:
            data[self.foreign_key] = []
            for v in related_manager.all():
                item = {}
                logger.debug(v)
                for accessor in self.accessor:
                    if accessor.endswith("display"):
                        item[accessor] = getattr(v, accessor)()
                    else:
                        item[accessor] = getattr(v, accessor)
                data[self.foreign_key].append(item)
            return data
        return None


class RepeatableSectionField(RepeatableField):
    def get_label(self):
        return super().get_label()

    def get_sections(self, instance):
        related_manager = get_model(self.foreign_key).objects.filter(**{instance._meta.model_name: instance})
        if related_manager.count() > 0:
            return related_manager
        return None

    def get_value(self, instance):
        related_manager = get_model(self.foreign_key).objects.filter(**{instance._meta.model_name: instance})
        data = {
            "template_name": self.template_name,
        }
        if related_manager.count() > 0:
            data[self.foreign_key] = []
            for v in related_manager.all():
                item = {}
                for accessor in self.accessor:
                    item[accessor] = getattr(v, accessor)
                data[self.foreign_key].append(item)
            return data
        return None


class SectionField(Field):
    def __init__(self, name, accessor, foreign_key):
        super().__init__(name, accessor)
        self.foreign_key = foreign_key


class RepeatableSectionNameWithAccessor(SectionNameWithAccessor):
    def __init__(self, name, accessor, foreign_key, model_name=None):
        super().__init__(name, accessor, foreign_key)
        self.model_name = model_name

    def get_sections(self, instance):
        related_manager = get_model(self.foreign_key).objects.filter(**{self.model_name: instance})
        if related_manager.count() > 0:
            return related_manager
        return None

    def get_name(self, instance):
        if len(self.accessor) > 2:
            new_name = f"{self.name} {getattr(instance, self.accessor[0])} - {getattr(instance, self.accessor[1])}"
        else:
            new_name = f"{self.name} {getattr(instance, self.accessor[0])}"
        if getattr(instance, self.accessor[-1]):
            return f"{new_name} ({getattr(instance, self.accessor[-1])})"
        return new_name


class SouboryRepeatableSectionNameWithAccessor(RepeatableSectionNameWithAccessor):
    def get_sections(self, instance):
        related_manager = get_model(self.foreign_key).objects.filter(**{"vazba": instance.soubory})
        if related_manager.count() > 0:
            return related_manager
        return None


class KomponentaRepeatableSectionNameWithAccessor(RepeatableSectionNameWithAccessor):
    def get_name(self, instance):
        obdobi = getattr(instance, self.accessor[1])
        jistota = getattr(instance, self.accessor[2])
        presna_datace = getattr(instance, self.accessor[3])
        areal = getattr(instance, self.accessor[4])
        aktivity = getattr(instance, self.accessor[5]).all()
        second_part = ""
        vypis_jistota_translated = (
            _("vypis.vyppis_config.KomponentaRepeatableSectionNameWithAccessor.jistota.Ano")
            if jistota
            else _("vypis.vyppis_config.KomponentaRepeatableSectionNameWithAccessor.jistota.Ne")
        )
        if obdobi:
            second_part = f" - {obdobi}"
            second_part += f" ({vypis_jistota_translated}"
            if presna_datace:
                second_part += f"; {presna_datace})"
            else:
                second_part += ")"
        else:
            second_part = f" - ({vypis_jistota_translated}"
            if presna_datace:
                second_part += f"; {presna_datace})"
            else:
                second_part += ")"
        third_part = ""
        if areal:
            third_part = f" - {areal}"
            if aktivity:
                third_part += f" ({', '.join([str(a) for a in aktivity])})"
        elif aktivity:
            third_part = f" - ({', '.join([str(a) for a in aktivity])})"
        return f"{self.name} {getattr(instance, self.accessor[0])}{second_part}{third_part}"


class SubSectionField:
    def __init__(self, config, foreign_key=None):
        self.config = config
        self.foreign_key = foreign_key

    def get_config(self):
        return self.config

    def get_instance(self, instance):
        if self.foreign_key:
            try:
                return getattr(instance, self.foreign_key)
            except Exception:
                return None
        return instance


def get_historie_config(label_key):
    logger.debug(f"Getting historie config for {label_key}")
    return {
        "section_name": SimpleSectionTemplateName(label_key),
        "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
        "historie": HistorieRepeatableField(
            label_key,
            ["datum_zmeny", "uzivatel", "get_typ_zmeny_display", "poznamka"],
            "historie",
            "vypis/historie.html",
        ),
    }


class HistorieSubSectionField(SubSectionField):
    def __init__(self, foreign_key=None, label_key="vypis.historie.section_name"):
        self.label_key = label_key
        self.foreign_key = foreign_key

    def get_config(self):
        logger.debug(f"historie config {get_historie_config(self.label_key)}")
        return get_historie_config(self.label_key)
