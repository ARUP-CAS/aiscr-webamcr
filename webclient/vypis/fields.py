from datetime import date
from decimal import Decimal

from adb.models import VyskovyBod
from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
from core.constants import ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID
from core.models import Soubor
from dj.models import DokumentacniJednotka
from django.db import connection, transaction
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from dokument.models import Dokument, DokumentCast, Tvar
from ez.models import ExterniZdroj
from historie.models import Historie
from komponenta.models import Komponenta
from nalez.models import NalezObjekt, NalezPredmet
from neidentakce.models import NeidentAkce
from pas.models import SamostatnyNalez
from projekt.models import Projekt
from projekt.views import get_show_oznamovatel


def get_model(name):
    """Zajišťuje logiku funkce ``get_model``.
    
    :param name: Vstupní hodnota parametru ``name`` použitého při zpracování.
    :return: Návratová hodnota funkce po zpracování vstupních dat.
    """
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
    """Zajišťuje logiku funkce ``get_gml``.
    
    :param geom: Vstupní hodnota parametru ``geom`` použitého při zpracování.
    :return: Návratová hodnota funkce po zpracování vstupních dat.
    """
    try:
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("SELECT ST_AsGML(%s)", [geom.wkt])
            row = cursor.fetchone()
        return row[0]
    except Exception:
        return None


def get_wkt(geom):
    """Zajišťuje logiku funkce ``get_wkt``.
    
    :param geom: Vstupní hodnota parametru ``geom`` použitého při zpracování.
    :return: Návratová hodnota funkce po zpracování vstupních dat.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT ST_AsText(ST_GeomFromText(%s))", [geom.wkt])
        row = cursor.fetchone()
        cursor.close()
        return row[0]


class SimpleSectionTemplateName:
    """Zapouzdřuje chování třídy ``SimpleSectionTemplateName`` pro modul ``webclient.vypis.fields``."""
    def __init__(self, name):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param name: Vstupní hodnota parametru ``name`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.name = name

    def __str__(self):
        """Zajišťuje logiku funkce ``__str__``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return self.name

    def get_name(self, instance):
        """Zajišťuje logiku funkce ``get_name``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return self.name

    def get_permission(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_permission``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return True


class SectionNameWithAccessor(SimpleSectionTemplateName):
    """Zapouzdřuje chování třídy ``SectionNameWithAccessor`` pro modul ``webclient.vypis.fields``."""
    def __init__(self, name, accessor, foreign_key=None):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param name: Vstupní hodnota parametru ``name`` použitého při zpracování.
        :param accessor: Vstupní hodnota parametru ``accessor`` použitého při zpracování.
        :param foreign_key: Vstupní hodnota parametru ``foreign_key`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super().__init__(name)
        self.accessor = accessor
        self.foreign_key = foreign_key

    def get_name(self, instance):
        """Zajišťuje logiku funkce ``get_name``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        if self.foreign_key:
            if getattr(instance, self.foreign_key):
                return f"{self.name}&nbsp;{getattr(getattr(instance, self.foreign_key), self.accessor)}"
            else:
                return None
        return f"{self.name}&nbsp;{getattr(instance, self.accessor)}"


class PianSectionNameWithAccessor(SectionNameWithAccessor):
    """Zapouzdřuje chování třídy ``PianSectionNameWithAccessor`` pro modul ``webclient.vypis.fields``."""
    def get_name(self, instance):
        """Zajišťuje logiku funkce ``get_name``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        if getattr(instance, self.foreign_key):
            pian = getattr(instance, self.foreign_key)
            stav = getattr(pian, self.accessor[1])()
            return f"{self.name}&nbsp;{getattr(pian, self.accessor[0])}&nbsp;({stav})&nbsp;-&nbsp;{getattr(pian, self.accessor[2])}&nbsp;({getattr(pian, self.accessor[3])})"
        else:
            return None


class OznamovatelSectionNameWithAccessor(SectionNameWithAccessor):
    """Zapouzdřuje chování třídy ``OznamovatelSectionNameWithAccessor`` pro modul ``webclient.vypis.fields``."""
    def get_permission(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_permission``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return get_show_oznamovatel(instance, user)


class Field:
    """Zapouzdřuje chování třídy ``Field`` pro modul ``webclient.vypis.fields``."""
    def __init__(self, label, accessor):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param label: Vstupní hodnota parametru ``label`` použitého při zpracování.
        :param accessor: Vstupní hodnota parametru ``accessor`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.label = label
        self.accessor = accessor

    def __repr__(self):
        """Zajišťuje logiku funkce ``__repr__``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return f"Field(label={self.label}, accessor={self.accessor})"

    def __str__(self):
        """Zajišťuje logiku funkce ``__str__``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return self.label

    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        value = getattr(instance, self.accessor)
        if isinstance(value, date) and value:
            return value.strftime("%-d.%-m.%Y")
        if isinstance(value, Decimal) and value:
            return f"{value:.3f}"
        return getattr(instance, self.accessor)

    def get_label(self):
        """Zajišťuje logiku funkce ``get_label``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return self.label


class SouborField(Field):
    """Zapouzdřuje chování třídy ``SouborField`` pro modul ``webclient.vypis.fields``."""
    def __init__(self, label, accessor, key_name):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param label: Vstupní hodnota parametru ``label`` použitého při zpracování.
        :param accessor: Vstupní hodnota parametru ``accessor`` použitého při zpracování.
        :param key_name: Vstupní hodnota parametru ``key_name`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super().__init__(label, accessor)
        self.key_name = key_name

    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
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
    """Zapouzdřuje chování třídy ``SouborDownloadField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        accessor = getattr(instance, self.accessor)
        if accessor:
            return {
                "value": accessor,
                "download": reverse(
                    "core:download_file",
                    args=(
                        self.key_name,
                        instance.vazba.navazany_objekt.ident_cely,
                        instance.id,
                    ),
                ),
            }
        return None


class Model3dKomponentaField(Field):
    """Zapouzdřuje chování třídy ``Model3dKomponentaField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return getattr(instance.casti.first().komponenty.komponenty.first(), self.accessor)


class Model3dKomponentaAktivityField(Model3dKomponentaField):
    """Zapouzdřuje chování třídy ``Model3dKomponentaAktivityField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        related_manager = super().get_value(instance, user)
        return "; ".join([str(v) for v in related_manager.all()])


class ChooseField(Field):
    """Zapouzdřuje chování třídy ``ChooseField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        for accessor in self.accessor:
            value = getattr(instance, accessor)
            if value:
                return mark_safe(value.get_ident_cely_link)
        return None


class StatusField(Field):
    """Zapouzdřuje chování třídy ``StatusField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return getattr(instance, self.accessor)()


class ZjisteniField(Field):
    """Zapouzdřuje chování třídy ``ZjisteniField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        if getattr(instance, self.accessor) is not None:
            if getattr(instance, self.accessor):
                return _("vypis.vypis_config.dj.zjisteni.Ano")
            else:
                return _("vypis.vypis_config.dj.zjisteni.Ne")
        return getattr(instance, self.accessor)()


class ForeignField(Field):
    """Zapouzdřuje chování třídy ``ForeignField`` pro modul ``webclient.vypis.fields``."""
    def __init__(self, name, accessor, foreign_key):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param name: Vstupní hodnota parametru ``name`` použitého při zpracování.
        :param accessor: Vstupní hodnota parametru ``accessor`` použitého při zpracování.
        :param foreign_key: Vstupní hodnota parametru ``foreign_key`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super().__init__(name, accessor)
        self.foreign_key = foreign_key

    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        accessors = self.accessor.split("__")
        new_instance = ""
        try:
            if getattr(instance, self.foreign_key):
                new_instance = getattr(instance, self.foreign_key)
                for key in accessors:
                    if getattr(new_instance, key, False) or getattr(new_instance, key) == 0:
                        new_instance = getattr(new_instance, key)
                    else:
                        new_instance = ""
                        break
        except Dokument.extra_data.RelatedObjectDoesNotExist:
            new_instance = ""
        return mark_safe(new_instance)


class GeomGmlField(Field):
    """Zapouzdřuje chování třídy ``GeomGmlField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        geom = getattr(instance, self.accessor)
        if geom:
            return get_gml(geom)
        return None


class GeomWktField(Field):
    """Zapouzdřuje chování třídy ``GeomWktField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        geom = getattr(instance, self.accessor)
        if geom:
            return get_wkt(geom)
        return None


class ForeignGeomGmlField(ForeignField):
    """Zapouzdřuje chování třídy ``ForeignGeomGmlField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        try:
            geom = getattr(getattr(instance, self.foreign_key), self.accessor)
            if geom:
                return get_gml(geom)
        except Dokument.extra_data.RelatedObjectDoesNotExist:
            return None
        return None


class ForeignGeomWktField(ForeignField):
    """Zapouzdřuje chování třídy ``ForeignGeomWktField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        try:
            geom = getattr(getattr(instance, self.foreign_key), self.accessor)
            if geom:
                return get_wkt(geom)
        except Dokument.extra_data.RelatedObjectDoesNotExist:
            return None
        return None


class ManyToManyField(Field):
    """Zapouzdřuje chování třídy ``ManyToManyField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        related_manager = getattr(instance, self.accessor)
        return "; ".join([str(v) for v in related_manager.all()])


class ForeignManyToManyField(ForeignField):
    """Zapouzdřuje chování třídy ``ForeignManyToManyField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        if getattr(instance, self.foreign_key, False):
            related_manager = getattr(getattr(instance, self.foreign_key), self.accessor)
            return "; ".join([v.vypis_name() for v in related_manager.all()])
        return None


class DoubleField(Field):
    """Zapouzdřuje chování třídy ``DoubleField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        values = []
        for accessor in self.accessor:
            value = getattr(instance, accessor)
            if value:
                if isinstance(value, date):
                    values.append(value.strftime("%-d.%-m.%Y"))
                else:
                    values.append(str(value))
        if values:
            return " - ".join(values)
        return None


class DoubleFieldNum(Field):
    """Zapouzdřuje chování třídy ``DoubleFieldNum`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        values = []
        for accessor in self.accessor:
            value = getattr(instance, accessor)
            if value:
                values.append(str(value))
        if values:
            return " - ".join(values)
        return None


class ForeignDoubleField(ForeignField):
    """Zapouzdřuje chování třídy ``ForeignDoubleField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        if getattr(instance, self.foreign_key, False):
            values = []
            for accessor in self.accessor:
                value = getattr(getattr(instance, self.foreign_key), accessor)
                if value:
                    values.append(str(value))
            if values:
                return " - ".join(values)
        return None


class ForeignDoubleFieldNum(ForeignField):
    """Zapouzdřuje chování třídy ``ForeignDoubleFieldNum`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        if getattr(instance, self.foreign_key, False):
            values = []
            for accessor in self.accessor:
                value = getattr(getattr(instance, self.foreign_key), accessor)
                if value:
                    values.append(str(value))
            if values:
                return "-".join(values)
        return None


class RepeatableField(ForeignField):
    """Zapouzdřuje chování třídy ``RepeatableField`` pro modul ``webclient.vypis.fields``."""
    def __init__(self, name, accessor, foreign_key, template_name=None, model_name=None):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param name: Vstupní hodnota parametru ``name`` použitého při zpracování.
        :param accessor: Vstupní hodnota parametru ``accessor`` použitého při zpracování.
        :param foreign_key: Vstupní hodnota parametru ``foreign_key`` použitého při zpracování.
        :param template_name: Vstupní hodnota parametru ``template_name`` použitého při zpracování.
        :param model_name: Vstupní hodnota parametru ``model_name`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super().__init__(name, accessor, foreign_key)
        self.template_name = template_name
        self.model_name = model_name

    def get_related_manager(self, instance):
        """Zajišťuje logiku funkce ``get_related_manager``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        if self.model_name:
            return get_model(self.foreign_key).objects.filter(**{self.model_name: instance})
        return get_model(self.foreign_key).objects.filter(**{instance._meta.model_name: instance})

    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
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
    """Zapouzdřuje chování třídy ``VbRepeatableField`` pro modul ``webclient.vypis.fields``."""
    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        related_manager = self.get_related_manager(instance)
        data = {
            "template_name": self.template_name,
            "label": self.label,
        }
        if related_manager.count() > 0:
            data["zaznamy"] = []
            for v in related_manager.all():
                acc3_2 = get_wkt(getattr(v, "geom"))
                acc3_3 = get_gml(getattr(v, "geom"))
                item = {}
                item[self.accessor[0]] = getattr(v, self.accessor[0])
                item[self.accessor[1]] = getattr(v, self.accessor[1])
                item[self.accessor[2]] = f"GML (EPSG:5514): {acc3_3}"
                item[self.accessor[3]] = f"WKT (EPSG:5514): {acc3_2}"
                data["zaznamy"].append(item)
            return data
        return None


class HistorieRepeatableField(RepeatableField):
    """Zapouzdřuje chování třídy ``HistorieRepeatableField`` pro modul ``webclient.vypis.fields``."""
    def get_related_manager(self, instance):
        """Zajišťuje logiku funkce ``get_related_manager``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return Historie.objects.filter(**{"vazba": instance.historie})

    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        related_manager = self.get_related_manager(instance)
        data = {
            "template_name": self.template_name,
        }
        if related_manager.count() > 0:
            data[self.foreign_key] = []
            for v in related_manager.all():
                item = {}
                for accessor in self.accessor:
                    if accessor == "uzivatel_protected":
                        item[accessor] = v.uzivatel_protected(
                            user.hlavni_role.pk not in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)
                        )
                    elif accessor.endswith("display"):
                        item[accessor] = getattr(v, accessor)()
                    else:
                        item[accessor] = getattr(v, accessor)
                data[self.foreign_key].append(item)
            return data
        return None


class RepeatableSectionField(RepeatableField):
    """Zapouzdřuje chování třídy ``RepeatableSectionField`` pro modul ``webclient.vypis.fields``."""
    def get_label(self):
        """Zajišťuje logiku funkce ``get_label``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return super().get_label()

    def get_sections(self, instance):
        """Zajišťuje logiku funkce ``get_sections``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        related_manager = (
            get_model(self.foreign_key).objects.filter(**{instance._meta.model_name: instance}).order_by("ident_cely")
        )
        if related_manager.count() > 0:
            return related_manager
        return None

    def get_value(self, instance, user=None):
        """Zajišťuje logiku funkce ``get_value``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :param user: Vstupní hodnota parametru ``user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
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
    """Zapouzdřuje chování třídy ``SectionField`` pro modul ``webclient.vypis.fields``."""
    def __init__(self, name, accessor, foreign_key):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param name: Vstupní hodnota parametru ``name`` použitého při zpracování.
        :param accessor: Vstupní hodnota parametru ``accessor`` použitého při zpracování.
        :param foreign_key: Vstupní hodnota parametru ``foreign_key`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super().__init__(name, accessor)
        self.foreign_key = foreign_key


class RepeatableSectionNameWithAccessor(SectionNameWithAccessor):
    """Zapouzdřuje chování třídy ``RepeatableSectionNameWithAccessor`` pro modul ``webclient.vypis.fields``."""
    def __init__(self, name, accessor, foreign_key, model_name=None):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param name: Vstupní hodnota parametru ``name`` použitého při zpracování.
        :param accessor: Vstupní hodnota parametru ``accessor`` použitého při zpracování.
        :param foreign_key: Vstupní hodnota parametru ``foreign_key`` použitého při zpracování.
        :param model_name: Vstupní hodnota parametru ``model_name`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super().__init__(name, accessor, foreign_key)
        self.model_name = model_name

    def get_sections(self, instance):
        """Zajišťuje logiku funkce ``get_sections``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        related_manager = (
            get_model(self.foreign_key).objects.filter(**{self.model_name: instance}).order_by("ident_cely")
        )
        if related_manager.count() > 0:
            return related_manager
        return None

    def get_name(self, instance):
        """Zajišťuje logiku funkce ``get_name``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        if len(self.accessor) > 2:
            new_name = f"{self.name}&nbsp;{getattr(instance, self.accessor[0])}&nbsp;-&nbsp;{getattr(instance, self.accessor[1])}"
        else:
            new_name = f"{self.name}&nbsp;{getattr(instance, self.accessor[0])}"
        if getattr(instance, self.accessor[-1]):
            return f"{new_name} ({getattr(instance, self.accessor[-1])})"
        return new_name


class SouboryRepeatableSectionNameWithAccessor(RepeatableSectionNameWithAccessor):
    """Zapouzdřuje chování třídy ``SouboryRepeatableSectionNameWithAccessor`` pro modul ``webclient.vypis.fields``."""
    def get_sections(self, instance):
        """Zajišťuje logiku funkce ``get_sections``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        related_manager = get_model(self.foreign_key).objects.filter(**{"vazba": instance.soubory}).order_by("pk")
        if related_manager.count() > 0:
            return related_manager
        return None

    def get_name(self, instance):
        """Zajišťuje logiku funkce ``get_name``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        new_name = f"{self.name} {getattr(instance, self.accessor[0])}"
        if getattr(instance, self.accessor[-1]):
            return f"{new_name}<div class='mime-type' style='white-space: pre;'> ({getattr(instance, self.accessor[-1])})</div>"
        return new_name


class KomponentaRepeatableSectionNameWithAccessor(RepeatableSectionNameWithAccessor):
    """Zapouzdřuje chování třídy ``KomponentaRepeatableSectionNameWithAccessor`` pro modul ``webclient.vypis.fields``."""
    def get_name(self, instance):
        """Zajišťuje logiku funkce ``get_name``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        obdobi = getattr(instance, self.accessor[1])
        jistota = getattr(instance, self.accessor[2])
        presna_datace = getattr(instance, self.accessor[3])
        areal = getattr(instance, self.accessor[4])
        aktivity = getattr(instance, self.accessor[5]).all()
        second_part = ""
        third_part = ""
        vypis_jistota_translated_ne = _("vypis.vypis_config.komponenta.jistota.Ne")
        vypis_jistota_translated_ano = _("vypis.vypis_config.komponenta.jistota.Ano")
        if jistota is not None:
            if jistota:
                second_part += f"&nbsp;({vypis_jistota_translated_ano}"
            else:
                second_part += f"&nbsp;({vypis_jistota_translated_ne}"
            if presna_datace:
                second_part += f";&nbsp;{presna_datace})"
            else:
                second_part += ")"
        elif presna_datace:
            second_part += f"&nbsp;({presna_datace})"
        if aktivity:
            third_part = f"&nbsp;({';&nbsp;'.join([str(a) for a in aktivity])})"
        return f"{self.name}&nbsp;{getattr(instance, self.accessor[0])}&nbsp;-&nbsp;{obdobi}{second_part}&nbsp;-&nbsp;{areal}{third_part}"


class SubSectionField:
    """Zapouzdřuje chování třídy ``SubSectionField`` pro modul ``webclient.vypis.fields``."""
    def __init__(self, config, foreign_key=None):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param config: Vstupní hodnota parametru ``config`` použitého při zpracování.
        :param foreign_key: Vstupní hodnota parametru ``foreign_key`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.config = config
        self.foreign_key = foreign_key

    def get_config(self):
        """Zajišťuje logiku funkce ``get_config``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return self.config

    def get_instance(self, instance):
        """Zajišťuje logiku funkce ``get_instance``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        if self.foreign_key:
            try:
                return getattr(instance, self.foreign_key)
            except Exception:
                return None
        return instance


class NeidentAkceSubSectionField(SubSectionField):
    """Zapouzdřuje chování třídy ``NeidentAkceSubSectionField`` pro modul ``webclient.vypis.fields``."""
    def get_instance(self, instance):
        """Zajišťuje logiku funkce ``get_instance``.
        
        :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        try:
            neident_akce = NeidentAkce.objects.get(dokument_cast=instance)
            return neident_akce
        except Exception:
            return None


def get_historie_config(label_key):
    """Zajišťuje logiku funkce ``get_historie_config``.
    
    :param label_key: Vstupní hodnota parametru ``label_key`` použitého při zpracování.
    :return: Návratová hodnota funkce po zpracování vstupních dat.
    """
    return {
        "section_name": SimpleSectionTemplateName(label_key),
        "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
        "historie": HistorieRepeatableField(
            label_key,
            ["datum_zmeny", "uzivatel_protected", "get_typ_zmeny_display", "poznamka"],
            "historie",
            "vypis/historie.html",
        ),
    }


class HistorieSubSectionField(SubSectionField):
    """Zapouzdřuje chování třídy ``HistorieSubSectionField`` pro modul ``webclient.vypis.fields``."""
    def __init__(self, foreign_key=None, label_key="vypis.historie.section_name"):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param foreign_key: Vstupní hodnota parametru ``foreign_key`` použitého při zpracování.
        :param label_key: Vstupní hodnota parametru ``label_key`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.label_key = label_key
        self.foreign_key = foreign_key

    def get_config(self):
        """Zajišťuje logiku funkce ``get_config``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return get_historie_config(self.label_key)
