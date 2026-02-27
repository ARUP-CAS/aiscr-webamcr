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
    """Funkce `get_model` v modulu `webclient.vypis.fields`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param name: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
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
    """Funkce `get_gml` v modulu `webclient.vypis.fields`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param geom: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    try:
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("SELECT ST_AsGML(%s)", [geom.wkt])
            row = cursor.fetchone()
        return row[0]
    except Exception:
        return None


def get_wkt(geom):
    """Funkce `get_wkt` v modulu `webclient.vypis.fields`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param geom: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT ST_AsText(ST_GeomFromText(%s))", [geom.wkt])
        row = cursor.fetchone()
        cursor.close()
        return row[0]


class SimpleSectionTemplateName:
    """Třída `SimpleSectionTemplateName` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, name):
        """Funkce `SimpleSectionTemplateName.__init__` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param name: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.name = name

    def __str__(self):
        """Funkce `SimpleSectionTemplateName.__str__` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        return self.name

    def get_name(self, instance):
        """Funkce `SimpleSectionTemplateName.get_name` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return self.name

    def get_permission(self, instance, user=None):
        """Funkce `SimpleSectionTemplateName.get_permission` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return True


class SectionNameWithAccessor(SimpleSectionTemplateName):
    """Třída `SectionNameWithAccessor` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, name, accessor, foreign_key=None):
        """Funkce `SectionNameWithAccessor.__init__` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param name: Vstupní hodnota používaná při zpracování.
        :param accessor: Vstupní hodnota používaná při zpracování.
        :param foreign_key: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        super().__init__(name)
        self.accessor = accessor
        self.foreign_key = foreign_key

    def get_name(self, instance):
        """Funkce `SectionNameWithAccessor.get_name` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if self.foreign_key:
            if getattr(instance, self.foreign_key):
                return f"{self.name}&nbsp;{getattr(getattr(instance, self.foreign_key), self.accessor)}"
            else:
                return None
        return f"{self.name}&nbsp;{getattr(instance, self.accessor)}"


class PianSectionNameWithAccessor(SectionNameWithAccessor):
    """Třída `PianSectionNameWithAccessor` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_name(self, instance):
        """Funkce `PianSectionNameWithAccessor.get_name` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if getattr(instance, self.foreign_key):
            pian = getattr(instance, self.foreign_key)
            stav = getattr(pian, self.accessor[1])()
            return f"{self.name}&nbsp;{getattr(pian, self.accessor[0])}&nbsp;({stav})&nbsp;-&nbsp;{getattr(pian, self.accessor[2])}&nbsp;({getattr(pian, self.accessor[3])})"
        else:
            return None


class OznamovatelSectionNameWithAccessor(SectionNameWithAccessor):
    """Třída `OznamovatelSectionNameWithAccessor` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_permission(self, instance, user=None):
        """Funkce `OznamovatelSectionNameWithAccessor.get_permission` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return get_show_oznamovatel(instance, user)


class Field:
    """Třída `Field` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, label, accessor):
        """Funkce `Field.__init__` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param label: Vstupní hodnota používaná při zpracování.
        :param accessor: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.label = label
        self.accessor = accessor

    def __repr__(self):
        """Funkce `Field.__repr__` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        return f"Field(label={self.label}, accessor={self.accessor})"

    def __str__(self):
        """Funkce `Field.__str__` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        return self.label

    def get_value(self, instance, user=None):
        """Funkce `Field.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        value = getattr(instance, self.accessor)
        if isinstance(value, date) and value:
            return value.strftime("%-d.%-m.%Y")
        if isinstance(value, Decimal) and value:
            return f"{value:.3f}"
        return getattr(instance, self.accessor)

    def get_label(self):
        """Funkce `Field.get_label` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        return self.label


class SouborField(Field):
    """Třída `SouborField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, label, accessor, key_name):
        """Funkce `SouborField.__init__` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param label: Vstupní hodnota používaná při zpracování.
        :param accessor: Vstupní hodnota používaná při zpracování.
        :param key_name: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        super().__init__(label, accessor)
        self.key_name = key_name

    def get_value(self, instance, user=None):
        """Funkce `SouborField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
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
    """Třída `SouborDownloadField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `SouborDownloadField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
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
    """Třída `Model3dKomponentaField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `Model3dKomponentaField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return getattr(instance.casti.first().komponenty.komponenty.first(), self.accessor)


class Model3dKomponentaAktivityField(Model3dKomponentaField):
    """Třída `Model3dKomponentaAktivityField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `Model3dKomponentaAktivityField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        related_manager = super().get_value(instance, user)
        return "; ".join([str(v) for v in related_manager.all()])


class ChooseField(Field):
    """Třída `ChooseField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `ChooseField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        for accessor in self.accessor:
            value = getattr(instance, accessor)
            if value:
                return mark_safe(value.get_ident_cely_link)
        return None


class StatusField(Field):
    """Třída `StatusField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `StatusField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return getattr(instance, self.accessor)()


class ZjisteniField(Field):
    """Třída `ZjisteniField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `ZjisteniField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if getattr(instance, self.accessor) is not None:
            if getattr(instance, self.accessor):
                return _("vypis.vypis_config.dj.zjisteni.Ano")
            else:
                return _("vypis.vypis_config.dj.zjisteni.Ne")
        return getattr(instance, self.accessor)()


class ForeignField(Field):
    """Třída `ForeignField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, name, accessor, foreign_key):
        """Funkce `ForeignField.__init__` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param name: Vstupní hodnota používaná při zpracování.
        :param accessor: Vstupní hodnota používaná při zpracování.
        :param foreign_key: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        super().__init__(name, accessor)
        self.foreign_key = foreign_key

    def get_value(self, instance, user=None):
        """Funkce `ForeignField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
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
    """Třída `GeomGmlField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `GeomGmlField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        geom = getattr(instance, self.accessor)
        if geom:
            return get_gml(geom)
        return None


class GeomWktField(Field):
    """Třída `GeomWktField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `GeomWktField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        geom = getattr(instance, self.accessor)
        if geom:
            return get_wkt(geom)
        return None


class ForeignGeomGmlField(ForeignField):
    """Třída `ForeignGeomGmlField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `ForeignGeomGmlField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        try:
            geom = getattr(getattr(instance, self.foreign_key), self.accessor)
            if geom:
                return get_gml(geom)
        except Dokument.extra_data.RelatedObjectDoesNotExist:
            return None
        return None


class ForeignGeomWktField(ForeignField):
    """Třída `ForeignGeomWktField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `ForeignGeomWktField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        try:
            geom = getattr(getattr(instance, self.foreign_key), self.accessor)
            if geom:
                return get_wkt(geom)
        except Dokument.extra_data.RelatedObjectDoesNotExist:
            return None
        return None


class ManyToManyField(Field):
    """Třída `ManyToManyField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `ManyToManyField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        related_manager = getattr(instance, self.accessor)
        return "; ".join([str(v) for v in related_manager.all()])


class ForeignManyToManyField(ForeignField):
    """Třída `ForeignManyToManyField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `ForeignManyToManyField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if getattr(instance, self.foreign_key, False):
            related_manager = getattr(getattr(instance, self.foreign_key), self.accessor)
            return "; ".join([v.vypis_name() for v in related_manager.all()])
        return None


class DoubleField(Field):
    """Třída `DoubleField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `DoubleField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
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
    """Třída `DoubleFieldNum` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `DoubleFieldNum.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
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
    """Třída `ForeignDoubleField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `ForeignDoubleField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
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
    """Třída `ForeignDoubleFieldNum` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `ForeignDoubleFieldNum.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
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
    """Třída `RepeatableField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, name, accessor, foreign_key, template_name=None, model_name=None):
        """Funkce `RepeatableField.__init__` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param name: Vstupní hodnota používaná při zpracování.
        :param accessor: Vstupní hodnota používaná při zpracování.
        :param foreign_key: Vstupní hodnota používaná při zpracování.
        :param template_name: Vstupní hodnota používaná při zpracování.
        :param model_name: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        super().__init__(name, accessor, foreign_key)
        self.template_name = template_name
        self.model_name = model_name

    def get_related_manager(self, instance):
        """Funkce `RepeatableField.get_related_manager` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if self.model_name:
            return get_model(self.foreign_key).objects.filter(**{self.model_name: instance})
        return get_model(self.foreign_key).objects.filter(**{instance._meta.model_name: instance})

    def get_value(self, instance, user=None):
        """Funkce `RepeatableField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
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
    """Třída `VbRepeatableField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_value(self, instance, user=None):
        """Funkce `VbRepeatableField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
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
    """Třída `HistorieRepeatableField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_related_manager(self, instance):
        """Funkce `HistorieRepeatableField.get_related_manager` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return Historie.objects.filter(**{"vazba": instance.historie})

    def get_value(self, instance, user=None):
        """Funkce `HistorieRepeatableField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
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
    """Třída `RepeatableSectionField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_label(self):
        """Funkce `RepeatableSectionField.get_label` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        return super().get_label()

    def get_sections(self, instance):
        """Funkce `RepeatableSectionField.get_sections` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        related_manager = (
            get_model(self.foreign_key).objects.filter(**{instance._meta.model_name: instance}).order_by("ident_cely")
        )
        if related_manager.count() > 0:
            return related_manager
        return None

    def get_value(self, instance, user=None):
        """Funkce `RepeatableSectionField.get_value` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :param user: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
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
    """Třída `SectionField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, name, accessor, foreign_key):
        """Funkce `SectionField.__init__` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param name: Vstupní hodnota používaná při zpracování.
        :param accessor: Vstupní hodnota používaná při zpracování.
        :param foreign_key: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        super().__init__(name, accessor)
        self.foreign_key = foreign_key


class RepeatableSectionNameWithAccessor(SectionNameWithAccessor):
    """Třída `RepeatableSectionNameWithAccessor` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, name, accessor, foreign_key, model_name=None):
        """Funkce `RepeatableSectionNameWithAccessor.__init__` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param name: Vstupní hodnota používaná při zpracování.
        :param accessor: Vstupní hodnota používaná při zpracování.
        :param foreign_key: Vstupní hodnota používaná při zpracování.
        :param model_name: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        super().__init__(name, accessor, foreign_key)
        self.model_name = model_name

    def get_sections(self, instance):
        """Funkce `RepeatableSectionNameWithAccessor.get_sections` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        related_manager = (
            get_model(self.foreign_key).objects.filter(**{self.model_name: instance}).order_by("ident_cely")
        )
        if related_manager.count() > 0:
            return related_manager
        return None

    def get_name(self, instance):
        """Funkce `RepeatableSectionNameWithAccessor.get_name` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if len(self.accessor) > 2:
            new_name = f"{self.name}&nbsp;{getattr(instance, self.accessor[0])}&nbsp;-&nbsp;{getattr(instance, self.accessor[1])}"
        else:
            new_name = f"{self.name}&nbsp;{getattr(instance, self.accessor[0])}"
        if getattr(instance, self.accessor[-1]):
            return f"{new_name} ({getattr(instance, self.accessor[-1])})"
        return new_name


class SouboryRepeatableSectionNameWithAccessor(RepeatableSectionNameWithAccessor):
    """Třída `SouboryRepeatableSectionNameWithAccessor` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_sections(self, instance):
        """Funkce `SouboryRepeatableSectionNameWithAccessor.get_sections` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        related_manager = get_model(self.foreign_key).objects.filter(**{"vazba": instance.soubory}).order_by("pk")
        if related_manager.count() > 0:
            return related_manager
        return None

    def get_name(self, instance):
        """Funkce `SouboryRepeatableSectionNameWithAccessor.get_name` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        new_name = f"{self.name} {getattr(instance, self.accessor[0])}"
        if getattr(instance, self.accessor[-1]):
            return f"{new_name}<div class='mime-type' style='white-space: pre;'> ({getattr(instance, self.accessor[-1])})</div>"
        return new_name


class KomponentaRepeatableSectionNameWithAccessor(RepeatableSectionNameWithAccessor):
    """Třída `KomponentaRepeatableSectionNameWithAccessor` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_name(self, instance):
        """Funkce `KomponentaRepeatableSectionNameWithAccessor.get_name` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
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
    """Třída `SubSectionField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, config, foreign_key=None):
        """Funkce `SubSectionField.__init__` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param config: Vstupní hodnota používaná při zpracování.
        :param foreign_key: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.config = config
        self.foreign_key = foreign_key

    def get_config(self):
        """Funkce `SubSectionField.get_config` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        return self.config

    def get_instance(self, instance):
        """Funkce `SubSectionField.get_instance` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if self.foreign_key:
            try:
                return getattr(instance, self.foreign_key)
            except Exception:
                return None
        return instance


class NeidentAkceSubSectionField(SubSectionField):
    """Třída `NeidentAkceSubSectionField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def get_instance(self, instance):
        """Funkce `NeidentAkceSubSectionField.get_instance` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param instance: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        try:
            neident_akce = NeidentAkce.objects.get(dokument_cast=instance)
            return neident_akce
        except Exception:
            return None


def get_historie_config(label_key):
    """Funkce `get_historie_config` v modulu `webclient.vypis.fields`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param label_key: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
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
    """Třída `HistorieSubSectionField` v modulu `webclient.vypis.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, foreign_key=None, label_key="vypis.historie.section_name"):
        """Funkce `HistorieSubSectionField.__init__` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param foreign_key: Vstupní hodnota používaná při zpracování.
        :param label_key: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.label_key = label_key
        self.foreign_key = foreign_key

    def get_config(self):
        """Funkce `HistorieSubSectionField.get_config` v modulu `webclient.vypis.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        return get_historie_config(self.label_key)
